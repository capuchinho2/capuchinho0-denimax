import os
import hashlib
import requests
from bs4 import BeautifulSoup
from datetime import datetime


# Sessões para os dois sistemas
sessao_viagem = requests.Session()
sessao_suporte = requests.Session()

# URLs e credenciais
URL_LOGIN_1 = "http://172.19.0.44:8001/verifica_login.php"
URL_VIAGEM = "http://172.19.0.44:8001/status_ring/index.php"
URL_LOGIN_2 = "http://172.19.0.44:8002/verifica_login.php"
URL_SUPORTE = "http://172.19.0.44:8002/index.php"

CREDENCIAIS = {"login": "CDP174176", "senha": "099475"}

def fazer_login():
    """Faz login nos dois sistemas."""
    r1 = sessao_viagem.post(URL_LOGIN_1, data=CREDENCIAIS)
    r2 = sessao_suporte.post(URL_LOGIN_2, data=CREDENCIAIS)
    return (r1.status_code == 200 and "Usuário não tem acesso" not in r1.text) and \
           (r2.status_code == 200 and "Usuário não tem acesso" not in r2.text)

def buscar_dados_viagem(viagem):
    """Faz o POST e retorna o HTML da viagem."""
    payload = {"local": "linha.php", "viagem": str(viagem)}
    r = sessao_viagem.post(URL_VIAGEM, data=payload)
    return r.text if r.status_code == 200 else None

def extrair_tabela(html):
    """Extrai a tabela principal com os paletes do HTML da viagem."""
    soup = BeautifulSoup(html, "html.parser")
    div_viagem = soup.find("div", {"id": "rel_viagem"})
    if not div_viagem:
        return []

    tabela = div_viagem.find("table", {"class": "table table-hover"})
    if not tabela:
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

def acessar_suporte(suporte_id):
    """Faz POST na tela de suporte e retorna HTML."""
    payload = {"suporte": suporte_id, "button_viagem": "Ok"}
    r = sessao_suporte.post(URL_SUPORTE, data=payload)
    return r.text if r.status_code == 200 else None

def cache_path(suporte_id):
    """Gera o caminho do cache baseado no ID do suporte."""
    nome = hashlib.md5(suporte_id.encode()).hexdigest()
    return os.path.join("cache_paletes", f"{nome}.html")

def acessar_suporte_com_cache(suporte_id, forcar_atualizacao=False):
    """Busca suporte com cache local para melhorar desempenho."""
    caminho = cache_path(suporte_id)

    if forcar_atualizacao or not os.path.exists(caminho):
        html = acessar_suporte(suporte_id)
        if html:
            os.makedirs("cache_paletes", exist_ok=True)
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(html)
            return html
        elif os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                return f.read()
        return None
    else:
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()



# Reutilizar cookies da sessão de login real (sessao_suporte) após login bem-sucedido
def forcar_atualizacao_site(viagem, atualizar_code):
    url = "http://172.19.0.44:8002/index.php"
    payload = {
        'suporte': viagem,
        'atualizar': atualizar_code
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "http://172.19.0.44:8002",
        "Referer": "http://172.19.0.44:8002/index.php",
        "User-Agent": "Mozilla/5.0",
    }

    try:
        log_evento(f"Iniciando atualização - Viagem: {viagem} | Código: {atualizar_code}")
        response = sessao_suporte.post(url, data=payload, headers=headers)

        log_evento(f"Status da resposta: {response.status_code}")
        if response.status_code == 200:
            log_evento("✅ Atualização enviada com sucesso.")
            return True
        else:
            log_evento(f"❌ Erro ao enviar atualização: HTTP {response.status_code}")
            return False
    except Exception as e:
        log_evento(f"❌ Exceção durante atualização: {e}")
        return False



def log_evento(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
