import asyncio
import os
from dataclasses import dataclass
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from parte_coleta import coletar_registros, registros_para_checklists


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
TELEGRAM_API_URL = "https://api.telegram.org"
RESPONSAVEL_POR_TURNO = {
	"TURNO 2": "DJAIR ALMEIDA",
}


@dataclass
class ChecklistPendente:
	codigo: str
	nome: str
	data_hora: str
	turno: str


class TesteTurnoMensagem(BaseModel):
	chat_id: int | None = None
	checklists: list[ChecklistPendente] = Field(min_length=1)


def montar_mensagem(
	nome_responsavel: str,
	checklists: list[ChecklistPendente],
) -> str:
	linhas = [
		f"Olá, {nome_responsavel}!",
		"Existem checklists pendentes:",
		"",
	]
	for checklist in checklists:
		linhas.append(
			f"- Checklist #{checklist.codigo} | {checklist.nome} "
			f"| {checklist.data_hora} | {checklist.turno}"
		)
	linhas.extend(["", "Por favor, verifique e finalize os checklists."])
	return "\n".join(linhas)


def normalizar_turno(turno: str) -> str:
	return turno.strip().upper()


def montar_mensagem_do_turno(
	turno: str,
	checklists: list[ChecklistPendente],
) -> tuple[str, str]:
	turno_normalizado = normalizar_turno(turno)
	responsavel = RESPONSAVEL_POR_TURNO.get(turno_normalizado)
	if responsavel is None:
		raise ValueError(f"Nenhum responsável configurado para {turno}")
	return responsavel, montar_mensagem(responsavel, checklists)


def converter_checklists(checklists: list[ChecklistPendente | dict]) -> list[ChecklistPendente]:
	itens: list[ChecklistPendente] = []
	for checklist in checklists:
		if isinstance(checklist, dict):
			itens.append(ChecklistPendente(**checklist))
		else:
			itens.append(checklist)
	return itens


async def chamar_telegram(metodo: str, dados: dict | None = None) -> dict:
	if not TELEGRAM_BOT_TOKEN:
		raise RuntimeError("Configure TELEGRAM_BOT_TOKEN para usar o bot.")

	url = f"{TELEGRAM_API_URL}/bot{TELEGRAM_BOT_TOKEN}/{metodo}"
	try:
		async with httpx.AsyncClient(timeout=15) as cliente:
			resposta = await cliente.post(url, json=dados or {})
	except httpx.HTTPError as erro:
		raise RuntimeError("Não foi possível conectar à API do Telegram.") from erro
	if resposta.status_code == 401:
		raise RuntimeError("Token do Telegram inválido ou revogado.")
	resposta.raise_for_status()
	retorno = resposta.json()
	if not retorno.get("ok"):
		raise RuntimeError(retorno.get("description", "Erro retornado pelo Telegram"))
	return retorno["result"]


async def enviar_mensagem(chat_id: int | None, mensagem: str) -> dict:
	destino = chat_id if chat_id is not None else TELEGRAM_CHAT_ID
	if destino == 0:
		raise RuntimeError("Configure TELEGRAM_CHAT_ID para usar o destinatário fixo.")
	return await chamar_telegram(
		"sendMessage",
		{"chat_id": destino, "text": mensagem},
	)


def turno_agora() -> str:
	hora = datetime.now().time()
	if datetime.strptime("06:10", "%H:%M").time() <= hora <= datetime.strptime("14:39", "%H:%M").time():
		return "TURNO 1"
	if datetime.strptime("14:40", "%H:%M").time() <= hora <= datetime.strptime("23:10", "%H:%M").time():
		return "TURNO 2"
	return "TURNO 3"


async def enviar_agora_manual(
	checklists: list[ChecklistPendente],
	chat_id: int | None = None,
) -> dict:
	responsavel = "DJAIR ALMEIDA"
	mensagem = montar_mensagem(responsavel, checklists)
	retorno = await enviar_mensagem(chat_id, mensagem)
	return {"responsavel": responsavel, "mensagem": mensagem, "telegram": retorno}


async def monitorar_turno_automatico(
	checklists: list[ChecklistPendente],
	intervalo_segundos: int = 60,
	chat_id: int | None = None,
) -> None:
	ultimo_turno_enviado: str | None = None
	while True:
		await asyncio.sleep(intervalo_segundos)
		turno = turno_agora()
		if turno == ultimo_turno_enviado:
			continue
		try:
			_, mensagem = montar_mensagem_do_turno(turno, checklists)
			await enviar_mensagem(chat_id, mensagem)
			ultimo_turno_enviado = turno
		except (ValueError, RuntimeError, httpx.HTTPError):
			continue


app = FastAPI(title="Bot Telegram de Checklists")


@app.get("/health")
def health() -> dict[str, str]:
	return {"status": "ok"}


@app.get("/telegram/atualizacoes")
async def atualizacoes_telegram() -> dict:
	"""Retorna mensagens recebidas para localizar o chat_id após /start."""
	try:
		return {"atualizacoes": await chamar_telegram("getUpdates")}
	except (RuntimeError, httpx.HTTPError) as erro:
		raise HTTPException(status_code=503, detail=str(erro)) from erro


@app.post("/telegram/testar-turno-2")
async def testar_turno_2(dados: TesteTurnoMensagem) -> dict:
	checklists = converter_checklists(dados.checklists)
	try:
		responsavel, mensagem = montar_mensagem_do_turno("TURNO 2", checklists)
	except ValueError as erro:
		raise HTTPException(status_code=400, detail=str(erro)) from erro
	try:
		retorno = await enviar_mensagem(dados.chat_id, mensagem)
	except (RuntimeError, httpx.HTTPError) as erro:
		raise HTTPException(status_code=503, detail=str(erro)) from erro
	return {"responsavel": responsavel, "mensagem": mensagem, "telegram": retorno}


@app.post("/telegram/enviar-agora")
async def enviar_agora(dados: TesteTurnoMensagem) -> dict:
	checklists = converter_checklists(dados.checklists)
	try:
		return await enviar_agora_manual(checklists, dados.chat_id)
	except (RuntimeError, httpx.HTTPError, ValueError) as erro:
		raise HTTPException(status_code=503, detail=str(erro)) from erro


@app.post("/telegram/enviar-coleta")
async def enviar_coleta() -> dict:
	registros = coletar_registros(status_escolhido="Todos")
	checklists = converter_checklists(registros_para_checklists(registros))
	try:
		return await enviar_agora_manual(checklists)
	except (RuntimeError, httpx.HTTPError, ValueError) as erro:
		raise HTTPException(status_code=503, detail=str(erro)) from erro