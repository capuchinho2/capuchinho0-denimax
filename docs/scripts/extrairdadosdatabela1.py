import re
import requests
from bs4 import BeautifulSoup
import time
import os
from colorama import init, Fore, Style
import hashlib

# Inicializa o Colorama
init(autoreset=True)

# 🔹 URL onde buscamos os dados
url_viagem = "http://172.19.0.44:8001/status_ring/index.php"
sessao = requests.Session()
dados_login = {"login": "CDP174176", "senha": "099475", "entrar": "Entrar"}
url_login = "http://172.19.0.44:8001/verifica_login.php"
sessao.post(url_login, data=dados_login)
print("✅ Login 1 OK")

def buscar_dados_viagem(viagem):
    payload = {"local": "linha.php", "viagem": str(viagem)}
    response = sessao.post(url_viagem, data=payload)
    if response.status_code != 200:
        print(f"❌ Erro ao buscar dados da viagem {viagem}. Status: {response.status_code}")
        return None
    return response.text

def extrair_tabela(html):
    soup = BeautifulSoup(html, "html.parser")
    div_viagem = soup.find("div", {"id": "rel_viagem"})
    if not div_viagem:
        print("❌ Div rel_viagem não encontrada!")
        return []

    tabela = div_viagem.find("table", {"class": "table table-hover"})
    if not tabela:
        print("❌ Nenhuma tabela encontrada dentro da div rel_viagem!")
        return []

    dados = []
    paletes_vistos = set()

    for row in tabela.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 10:
            continue

        palete_raw = cols[2].text.strip()
        palete = palete_raw.split("/")[0].zfill(2)
        tipo = cols[4].text.strip()

        if tipo == "HET" and palete not in paletes_vistos:
            paletes_vistos.add(palete)
            dados.append({"PALETE": palete, "TIPO": tipo})

    return dados

# 🔹 Segunda URL e sessão para acessar suporte
BASE_URL = "http://172.19.0.44:8002"
LOGIN_URL = f"{BASE_URL}/verifica_login.php"
SUPORTE_URL = f"{BASE_URL}/index.php"

session = requests.Session()
CREDENCIAIS = {"login": "CDP174176", "senha": "099475"}

def fazer_login():
    print("\n🔄 Realizando login...")
    res = session.post(LOGIN_URL, data=CREDENCIAIS)
    if res.status_code == 200 and "Usuário não tem acesso!" not in res.text:
        print("✅ Login 2 OK")
        return True
    print("❌ Erro no login 2")
    return False

def acessar_suporte(suporte_id):
    payload = {"suporte": suporte_id, "button_viagem": "Ok"}
    res = session.post(SUPORTE_URL, data=payload)
    if res.status_code == 200:
        return res.text
    return None

def cache_path(suporte_id):
    # Cria um nome de arquivo único para cada suporte_id
    nome = hashlib.md5(suporte_id.encode()).hexdigest()
    return os.path.join("cache_paletes", f"{nome}.html")

def acessar_suporte_com_cache(suporte_id, forcar_atualizacao=False):
    caminho = cache_path(suporte_id)
    # Se forçar atualização (palete pendente), busca do site e sobrescreve o cache
    if forcar_atualizacao or not os.path.exists(caminho):
        html = acessar_suporte(suporte_id)
        if html:
            os.makedirs("cache_paletes", exist_ok=True)
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(html)
            return html
        # Se não conseguiu buscar, tenta ler do cache antigo
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                return f.read()
        return None
    # Se não forçar atualização e existe cache, lê do disco
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()

# Troque acessar_suporte por acessar_suporte_com_cache no seu loop principal:
# Exemplo:
# html_suporte = acessar_suporte_com_cache(suporte_id)

if __name__ == "__main__":
    viagem = int(input("Digite o número da viagem: "))

    html = buscar_dados_viagem(viagem)
    if not html:
        print("❌ Falha ao buscar viagem.")
        exit()

    dados = extrair_tabela(html)
    print("\n📦 Paletes encontrados:")

    # ADICIONE ESTA LINHA PARA GARANTIR LOGIN NO SISTEMA DE SUPORTE
    if not fazer_login():
        print("❌ Falha no login do sistema de suporte.")
        exit()

    palete_status = {}
    paletes_validos = 0

    for item in dados:
        palete = item["PALETE"]
        suporte_id = f"{viagem}{palete}"

        # Primeiro tenta ler do cache
        html_suporte = acessar_suporte_com_cache(suporte_id)
        if not html_suporte:
            print(f"Palete {palete}: ❌ erro ao acessar suporte")
            continue

        soup = BeautifulSoup(html_suporte, "html.parser")
        tabela = soup.find("table")
        if not tabela:
            print(f"Palete {palete}: ❌ tabela não encontrada")
            continue

        tbody = tabela.find("tbody")
        if not tbody:
            print(f"Palete {palete}: ❌ <tbody> não encontrado")
            continue

        linhas = tbody.find_all("tr")
        if not linhas:
            # Força atualização do cache, pois pode ser lançado depois
            html_suporte = acessar_suporte_com_cache(suporte_id, forcar_atualizacao=True)
            # Reanalisa o HTML atualizado
            soup = BeautifulSoup(html_suporte, "html.parser")
            tabela = soup.find("table")
            if not tabela:
                print(f"Palete {palete}: ❌ tabela não encontrada (após atualização)")
                break
            tbody = tabela.find("tbody")
            if not tbody:
                print(f"Palete {palete}: ❌ <tbody> não encontrado (após atualização)")
                break
            linhas = tbody.find_all("tr")
            if not linhas:
                palete_status[palete] = None
                print(f"Palete {palete}: ⚠️ NÃO LANÇADO PARA CONFERÊNCIA")
                # Aqui, troque continue por break:
                break
        # Se chegou aqui, tem pelo menos um palete válido
        paletes_validos += 1

        total_linhas = len(linhas)
        linhas_gray = sum(1 for row in linhas if "gray" in (row.get("class") or []))
        todas_gray = all("gray" in (row.get("class") or []) for row in linhas)

        if total_linhas > 0:
            porcentagem = (linhas_gray / total_linhas) * 100
        else:
            porcentagem = 0

        if todas_gray:
            palete_status[palete] = True
            print(f"Palete {palete}: ✅ (100%)")
        else:
            # Atualiza o cache, pois pode ter mudado de pendente para conferido
            html_suporte = acessar_suporte_com_cache(suporte_id, forcar_atualizacao=True)
            # Reanalisa o HTML atualizado
            soup = BeautifulSoup(html_suporte, "html.parser")
            tabela = soup.find("table")
            if not tabela:
                print(f"Palete {palete}: ❌ tabela não encontrada (após atualização)")
                continue
            tbody = tabela.find("tbody")
            if not tbody:
                print(f"Palete {palete}: ❌ <tbody> não encontrado (após atualização)")
                continue
            linhas = tbody.find_all("tr")
            total_linhas = len(linhas)
            linhas_gray = sum(1 for row in linhas if "gray" in (row.get("class") or []))
            if total_linhas > 0:
                porcentagem = (linhas_gray / total_linhas) * 100
            else:
                porcentagem = 0
            todas_gray = all("gray" in (row.get("class") or []) for row in linhas)
            if todas_gray:
                palete_status[palete] = True
                print(f"Palete {palete}: ✅ (100%) (atualizado)")
            else:
                palete_status[palete] = False
                print(f"Palete {palete}: ❗ ({porcentagem:.1f}%) pendente")

    print(f"DEBUG: paletes_validos = {paletes_validos}")
    if paletes_validos == 0:
        print("\n⚠️ Nenhum palete lançado para conferência nesta viagem.")
        exit()

    # Se chegou aqui, segue normalmente para o menu de detalhamento
    while True:
        escolha = input("\nDigite o número do palete que deseja detalhar (ou ENTER para sair): ").strip()
        if not escolha:
            break  # Sai do menu de detalhamento

        palete = escolha.zfill(2)
        suporte_id = f"{viagem}{palete}"
        html_suporte = acessar_suporte_com_cache(suporte_id)
        if not html_suporte:
            print("❌ Erro ao acessar suporte.")
            continue  # Permite tentar outro palete

        soup = BeautifulSoup(html_suporte, "html.parser")
        tabela = soup.find("table")
        if not tabela:
            print(f"❌ tabela não encontrada para palete {palete}")
            continue

        tbody = tabela.find("tbody")
        if not tbody:
            print(f"❌ <tbody> não encontrado para palete {palete}")
            continue

        headers = ["CÓDIGO", "DESCRIÇÃO", "QTDE", "STATUS"]
        col_widths = [15, 30, 6, 18]
        print(Fore.CYAN + f"\n🔍 Palete {palete} - Detalhamento:\n")
        print(Fore.CYAN + " | ".join([h.ljust(col_widths[i]) for i, h in enumerate(headers)]))
        print(Fore.CYAN + "-" * (sum(col_widths) + 3 * (len(headers)-1)))

        linhas = tbody.find_all("tr")
        faltam_bipar = 0
        faltam_conferir = 0
        linhas_pendentes = 0
        for idx, row in enumerate(linhas):
            row_class = row.get("class") or []
            if "gray" in row_class:
                continue  # pula linhas já conferidas

            linhas_pendentes += 1
            cols = [td.text.strip() for td in row.find_all("td")]
            codigo = cols[0] if len(cols) > 0 else ""
            descricao = cols[2] if len(cols) > 2 else ""
            qtde = cols[5] if len(cols) > 5 else ""

            if "red" in row_class:
                status = Fore.RED + "❌ FALTA BIPAR"
                faltam_bipar += 1
            elif "white" in row_class:
                status = Fore.YELLOW + "❌ FALTA CONFERIR"
                faltam_conferir += 1
            else:
                status = ""

            print(f"{codigo.ljust(col_widths[0])} | {descricao.ljust(col_widths[1])} | {qtde.ljust(col_widths[2])} | {status.ljust(col_widths[3])}")

        if linhas_pendentes == 0:
            print(Fore.GREEN + "\n✅ Todas as linhas deste palete já foram conferidas!\n")

        print(Fore.CYAN + "-" * (sum(col_widths) + 3 * (len(headers)-1)))
        print(Fore.RED + f"\nResumo: {faltam_bipar} linha(s) faltam bipar, " +
              Fore.YELLOW + f"{faltam_conferir} linha(s) faltam conferir.\n" + Style.RESET_ALL)
