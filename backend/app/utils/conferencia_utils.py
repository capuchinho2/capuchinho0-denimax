import os
import hashlib
import requests
from bs4 import BeautifulSoup

# Sessões para os dois sistemas
sessao_viagem = requests.Session()
sessao_suporte = requests.Session()

# URLs e credenciais
URL_LOGIN_1 = "http://172.19.0.44:8001/verifica_login.php"
URL_VIAGEM = "http://172.19.0.44:8001/status_ring/index.php"
URL_LOGIN_2 = "http://172.19.0.44:8002/verifica_login.php"
URL_SUPORTE = "http://172.19.0.44:8002/index.php"

CREDENCIAIS = {"login": "CDP174176", "senha": "099475"}

# Cache path
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'cache_paletes')

def fazer_login():
    """Faz login nos dois sistemas."""
    try:
        r1 = sessao_viagem.post(URL_LOGIN_1, data={**CREDENCIAIS, "entrar": "Entrar"})
        r2 = sessao_suporte.post(URL_LOGIN_2, data=CREDENCIAIS)
        return (r1.status_code == 200 and "Usuário não tem acesso" not in r1.text) and \
               (r2.status_code == 200 and "Usuário não tem acesso" not in r2.text)
    except Exception as e:
        print(f"Erro no login: {e}")
        return False

def buscar_dados_viagem(viagem):
    """Faz o POST e retorna o HTML da viagem."""
    try:
        payload = {"local": "linha.php", "viagem": str(viagem)}
        r = sessao_viagem.post(URL_VIAGEM, data=payload)
        return r.text if r.status_code == 200 else None
    except Exception as e:
        print(f"Erro ao buscar viagem: {e}")
        return None

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
    try:
        payload = {"suporte": suporte_id, "button_viagem": "Ok"}
        r = sessao_suporte.post(URL_SUPORTE, data=payload)
        return r.text if r.status_code == 200 else None
    except Exception as e:
        print(f"Erro ao acessar suporte: {e}")
        return None

def cache_path(suporte_id):
    """Gera o caminho do cache baseado no ID do suporte."""
    nome = hashlib.md5(suporte_id.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{nome}.html")

def acessar_suporte_com_cache(suporte_id, forcar_atualizacao=False):
    """Busca suporte com cache local para melhorar desempenho."""
    caminho = cache_path(suporte_id)

    if forcar_atualizacao or not os.path.exists(caminho):
        html = acessar_suporte(suporte_id)
        if html:
            os.makedirs(CACHE_DIR, exist_ok=True)
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

def analisar_palete(viagem, palete, forcar_atualizacao=False):
    """Analisa um palete e retorna seu status e detalhes."""
    suporte_id = f"{viagem}{palete}"
    html_suporte = acessar_suporte_com_cache(suporte_id, forcar_atualizacao=forcar_atualizacao)
    
    if not html_suporte:
        return None
    
    soup = BeautifulSoup(html_suporte, "html.parser")
    tabela = soup.find("table")
    
    if not tabela:
        return None
    
    tbody = tabela.find("tbody")
    if not tbody:
        return None
    
    linhas = tbody.find_all("tr")
    
    # Se não tem linhas, palete não foi lançado
    if not linhas:
        return {
            "numero": palete,
            "tipo": "HET",
            "status": "⚠️ NÃO LANÇADO",
            "percentual": 0,
            "itens": [],
            "nao_lancado": True
        }
    
    total_linhas = len(linhas)
    linhas_gray = sum(1 for row in linhas if "gray" in (row.get("class") or []))
    todas_gray = (linhas_gray == total_linhas and total_linhas > 0)
    
    if total_linhas > 0:
        porcentagem = (linhas_gray / total_linhas) * 100
    else:
        porcentagem = 0
    
    # Extrair detalhes dos itens
    itens = []
    for row in linhas:
        row_class = row.get("class") or []
        cols = [td.text.strip() for td in row.find_all("td")]
        
        if len(cols) >= 6:
            codigo = cols[0]
            descricao = cols[2]
            qtde = cols[5]
            
            if "gray" in row_class:
                status = "CONFERIDO"
            elif "red" in row_class:
                status = "FALTA BIPAR"
            elif "white" in row_class:
                status = "FALTA CONFERIR"
            else:
                status = "PENDENTE"
            
            itens.append({
                "codigo": codigo,
                "descricao": descricao,
                "quantidade": qtde,
                "status": status
            })
    
    return {
        "numero": palete,
        "tipo": "HET",
        "status": "100% Conferido" if todas_gray else f"❗ ({porcentagem:.1f}%) Pendente",
        "percentual": int(porcentagem),
        "itens": itens,
        "nao_lancado": False
    }

def buscar_viagem_completa(viagem):
    """Busca todos os dados da viagem."""
    # Fazer login
    if not fazer_login():
        return {"success": False, "error": "Erro ao fazer login"}
    
    # Buscar dados da viagem
    html = buscar_dados_viagem(viagem)
    if not html:
        return {"success": False, "error": "Falha ao buscar dados da viagem"}
    
    # Extrair paletes
    dados = extrair_tabela(html)
    if not dados:
        return {"success": False, "error": "Nenhum palete HET encontrado"}
    
    # Analisar cada palete
    paletes = []
    completos = 0
    pendentes = 0
    parou_por_nao_lancado = False
    
    for item in dados:
        palete_info = analisar_palete(viagem, item["PALETE"])
        if palete_info:
            # Se palete não foi lançado, para de processar (igual ao seu código)
            if palete_info.get("nao_lancado"):
                paletes.append(palete_info)
                parou_por_nao_lancado = True
                break
            
            # Se não está 100% conferido, força atualização do cache
            if palete_info["percentual"] < 100:
                palete_info_atualizado = analisar_palete(viagem, item["PALETE"], forcar_atualizacao=True)
                if palete_info_atualizado:
                    palete_info = palete_info_atualizado
            
            paletes.append(palete_info)
            if palete_info["percentual"] == 100:
                completos += 1
            else:
                pendentes += 1
    
    return {
        "success": True,
        "viagem": viagem,
        "paletes": paletes,
        "total_paletes": len(paletes),
        "completos": completos,
        "pendentes": pendentes,
        "parou_por_nao_lancado": parou_por_nao_lancado
    }

def forcar_atualizacao_site(viagem, atualizar_code):
    """Força atualização no site usando o código de atualização."""
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
        response = sessao_suporte.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        print(f"Erro ao forçar atualização: {e}")
        return False
