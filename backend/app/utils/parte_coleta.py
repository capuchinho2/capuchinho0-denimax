import re
import os
import sys
import threading
import time as time_module
import urllib3
from datetime import datetime, time, timedelta
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


HORARIOS_AUTOMACAO = ((6, 0), (14, 30), (23, 0))
STATUS_PENDENTES = {"CRIADO", "EM ANDAMENTO"}
TELEGRAM_API_URL = "https://api.telegram.org"
_automacao_iniciada = False
FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")


class TabelaChecklists(HTMLParser):
	def __init__(self):
		super().__init__()
		self.linha = None
		self.celula = None
		self.linhas = []

	def handle_starttag(self, tag, attrs):
		if tag == "tr":
			self.linha = []
		elif self.linha is not None and tag in ("td", "th"):
			self.celula = []

	def handle_data(self, data):
		if self.celula is not None:
			texto = " ".join(data.split())
			if texto:
				self.celula.append(texto)

	def handle_endtag(self, tag):
		if tag in ("td", "th") and self.celula is not None:
			self.linha.append(" ".join(self.celula))
			self.celula = None
		elif tag == "tr" and self.linha:
			self.linhas.append(self.linha)
			self.linha = None


def extrair_registros(html):
	parser = TabelaChecklists()
	parser.feed(html)
	return [
		linha for linha in parser.linhas
		if linha and linha[0].isdigit() and len(linha) >= 8
	]


def classificar_turno(data_hora):
	"""Retorna o turno correspondente ao horário de uma data/hora."""
	valor = datetime.strptime(data_hora.strip(), "%d/%m/%Y %H:%M")
	horario = valor.time()
	if time(6, 10) <= horario <= time(14, 39):
		return "TURNO 1"
	if time(14, 40) <= horario <= time(23, 10):
		return "TURNO 2"
	return "TURNO 3"


def turno_do_registro(registro):
	"""Localiza a coluna Data/hora e classifica o registro."""
	for valor in registro:
		if re.fullmatch(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", valor.strip()):
			return classificar_turno(valor)
	return "TURNO NAO IDENTIFICADO"


def gerar_payload_checklist(registro):
	valores = [str(valor).strip() for valor in registro]
	codigo = valores[0] if valores else ""
	data_hora = next(
		(valor for valor in valores if re.fullmatch(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", valor)),
		"",
	)
	turno = turno_do_registro(registro)
	return {
		"codigo": codigo,
		"data_criacao": valores[1] if len(valores) > 1 else "",
		"responsavel": valores[2] if len(valores) > 2 else "",
		"checklist": valores[3] if len(valores) > 3 else "",
		"nome": valores[3] if len(valores) > 3 else "Checklist",
		"formulario": valores[4] if len(valores) > 4 else "",
		"informacoes": valores[5] if len(valores) > 5 else "",
		"percentual": valores[6] if len(valores) > 6 else "",
		"status": valores[7] if len(valores) > 7 else "",
		"data_hora": data_hora,
		"turno": turno,
	}


def registros_para_checklists(registros):
	return [gerar_payload_checklist(registro) for registro in registros]


def coletar_registros(status_escolhido="Todos", data_inicial=None, data_final=None):
	urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
	url = "https://checklist.id-logistics.com.br/"
	usuario = "02133167650"
	senha = "P.!Yg846N8tQ_Ys"
	if data_inicial is None:
		data_inicial = datetime.now().strftime("%d/%m/%Y")
	if data_final is None:
		data_final = datetime.now().strftime("%d/%m/%Y")

	sessao = requests.Session()
	dados_login = {
		"nmlogin": usuario,
		"txsenha": senha,
		"qrcode": "",
		"acao": "A",
	}
	resposta = sessao.post(f"{url}default.php", data=dados_login, verify=False, timeout=10)
	resposta.raise_for_status()

	filtros = {
		"datai": data_inicial,
		"dataf": data_final,
		"fflstatus": "",
		"fidresposta": "",
		"fnmchecklist": "",
		"freferencia": "",
		"acao": "L",
		"ord": "dtcriacao desc",
		"direcao": "",
		"idresposta": "",
	}
	resposta = sessao.post(
		f"{url}preenchimento.php",
		data=filtros,
		headers={"Referer": f"{url}home.php"},
		verify=False,
		timeout=10,
	)
	resposta.raise_for_status()
	registros = extrair_registros(resposta.text)

	paginas = {int(numero) for numero in re.findall(r"tpg\('([0-9]+)'\)", resposta.text)}
	paginas.add(1)
	for pagina in sorted(paginas):
		if pagina == 1:
			continue
		dados_pagina = {**filtros, "paginaatual": str(pagina)}
		resposta_pagina = sessao.post(
			f"{url}preenchimento.php",
			data=dados_pagina,
			headers={"Referer": f"{url}preenchimento.php"},
			verify=False,
			timeout=10,
		)
		resposta_pagina.raise_for_status()
		registros.extend(extrair_registros(resposta_pagina.text))

	registros_por_codigo = {registro[0]: registro for registro in registros}
	registros = list(registros_por_codigo.values())
	if status_escolhido and status_escolhido != "Todos":
		registros = [registro for registro in registros if registro[7] == status_escolhido]
	return registros


def carregar_configuracao_telegram():
	arquivo_env = Path(__file__).resolve().parent / ".env"
	if not arquivo_env.exists():
		return
	for linha in arquivo_env.read_text(encoding="utf-8").splitlines():
		linha = linha.strip()
		if not linha or linha.startswith("#") or "=" not in linha:
			continue
		chave, valor = linha.split("=", 1)
		os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


def proximo_horario_automatico(agora):
	candidatos = [
		agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
		for hora, minuto in HORARIOS_AUTOMACAO
	]
	futuros = [candidato for candidato in candidatos if candidato > agora]
	if futuros:
		return min(futuros)
	amanha = agora + timedelta(days=1)
	return amanha.replace(hour=6, minute=0, second=0, microsecond=0)


def agora_local():
	return datetime.now(FUSO_HORARIO)


def montar_mensagem_automatica(checklists, horario):
	linhas = [
		"Olá, Daniel Capuchinho!",
		f"Resumo automático das {horario.strftime('%H:%M')}.",
		"Checklists pendentes:",
		"",
	]
	for checklist in checklists:
		linhas.extend([
			"------------------------------",
			f"Nome: {checklist.get('responsavel') or 'Não informado'}",
			f"Checklist: {checklist.get('checklist') or 'Não informado'}",
			f"N° Equip: {checklist.get('informacoes') or 'Não informado'}",
			f"Status: {checklist.get('status') or 'Não informado'}",
			f"Data: {checklist.get('data_hora') or 'Não informado'}",
			"------------------------------",
			"",
		])
	linhas.append("Por favor, verifique e finalize os checklists.")
	return "\n".join(linhas)


def enviar_telegram_automatico(mensagem):
	token = os.getenv("TELEGRAM_BOT_TOKEN", "")
	chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
	if not token:
		raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado.")
	if not chat_id:
		raise RuntimeError("TELEGRAM_CHAT_ID não configurado.")

	resposta = requests.post(
		f"{TELEGRAM_API_URL}/bot{token}/sendMessage",
		json={"chat_id": chat_id, "text": mensagem},
		timeout=15,
	)
	try:
		resultado = resposta.json()
	except ValueError:
		resultado = {}
	if not resposta.ok or not resultado.get("ok"):
		descricao = resultado.get("description", resposta.text or "Erro sem descrição")
		raise RuntimeError(f"Telegram recusou a mensagem: {descricao}")


def executar_envio_automatico(horario):
	data = horario.strftime("%d/%m/%Y")
	registros = coletar_registros(
		status_escolhido="Todos",
		data_inicial=data,
		data_final=data,
	)
	checklists = registros_para_checklists(registros)
	pendentes = [
		item for item in checklists
		if str(item.get("status", "")).strip().upper() in STATUS_PENDENTES
	]
	if not pendentes:
		print(f"[{agora_local():%d/%m/%Y %H:%M:%S}] Nenhum checklist pendente.")
		return
	enviar_telegram_automatico(montar_mensagem_automatica(pendentes, horario))
	print(f"[{agora_local():%d/%m/%Y %H:%M:%S}] {len(pendentes)} checklist(s) enviado(s).")


def iniciar_automacao_telegram():
	carregar_configuracao_telegram()
	print("Automação Telegram: 06:00, 14:30 e 23:00.")
	while True:
		agora = agora_local()
		proximo = proximo_horario_automatico(agora)
		print(f"Próximo envio: {proximo:%d/%m/%Y %H:%M}")
		time_module.sleep(max(1, (proximo - agora).total_seconds()))
		try:
			executar_envio_automatico(proximo)
		except Exception as erro:
			print(f"Erro no envio automático: {erro}")


def iniciar_automacao_background():
	global _automacao_iniciada
	if _automacao_iniciada:
		return
	_automacao_iniciada = True
	threading.Thread(
		target=iniciar_automacao_telegram,
		name="automacao-telegram",
		daemon=True,
	).start()


if __name__ == "__main__":
	if "--automacao" in sys.argv:
		iniciar_automacao_telegram()
		sys.exit(0)
	if "--enviar-agora" in sys.argv:
		carregar_configuracao_telegram()
		executar_envio_automatico(agora_local())
		sys.exit(0)
	opcoes_status = {
		"1": "Aprovado",
		"2": "Criado",
		"3": "Em Andamento",
		"4": "Todos",
	}
	print("Escolha o status:")
	for codigo, status in opcoes_status.items():
		print(f"{codigo} - {status}")
	while True:
		escolha = input("Opção [1-4]: ").strip()
		if escolha in opcoes_status:
			break
		print("Opção inválida.")
	status_escolhido = opcoes_status[escolha]
	registros = coletar_registros(status_escolhido=status_escolhido)
	print(f"Total de linhas coletadas: {len(registros)}")
	for registro in registros:
		print(" | ".join([*registro[:8], turno_do_registro(registro)]))
	print(f"TOTAL_LINHAS={len(registros)}")