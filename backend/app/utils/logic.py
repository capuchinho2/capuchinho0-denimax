# Funções e variáveis utilitárias stubs para funcionamento do backend
# Substitua por implementações reais conforme necessário
import pandas as pd

def processar_het(data_inicial, data_final, conn=None):
    """
    Processa dados HET da tabela GELIVE e ONDAITM
    Args:
        data_inicial: string no formato YYYYMMDD
        data_final: string no formato YYYYMMDD
        conn: conexão com banco (opcional)
    Returns:
        dict com preparado e pendente em kg
    """
    try:
        from .db_utils import get_db_connection
        import pandas as pd
        from datetime import datetime, timedelta
        
        fechar_conn = False
        if conn is None:
            conn = get_db_connection()
            fechar_conn = True
        
        # Converter para formato YYYY-MM-DD para cálculos
        data_inicial_fmt = f"{data_inicial[:4]}-{data_inicial[4:6]}-{data_inicial[6:]}"
        data_final_fmt = f"{data_final[:4]}-{data_final[4:6]}-{data_final[6:]}"
        
        data_inicial_dt = datetime.strptime(data_inicial_fmt, "%Y-%m-%d")
        data_final_dt = datetime.strptime(data_final_fmt, "%Y-%m-%d")
        
        # Range amplo (±2 dias)
        data_ondaitm_inicial = (data_inicial_dt - timedelta(days=2)).strftime('%Y-%m-%d')
        data_ondaitm_final = (data_final_dt + timedelta(days=2)).strftime('%Y-%m-%d')
        
        # Query GELIVE para HET
        query_gelive_het = f"""
        SELECT *
        FROM FGE5006CDP.GELIVE
        WHERE MAJCRE >= {data_inicial}
            AND MAJCRE <= {data_final}
            AND (HEUEXC >= 140000 OR HEUEXC <= 010000)
            AND (REFLIV LIKE '2414%' OR REFLIV LIKE '2401%')
            AND CODTLI = 'STD'
        """
        
        cursor = conn.cursor()
        cursor.execute(query_gelive_het)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        df_gelive_het = pd.DataFrame.from_records(rows, columns=columns)
        cursor.close()
        
        if df_gelive_het.empty:
            if fechar_conn:
                conn.close()
            return {"preparado": 0, "pendente": 0}
        
        # Processar GELIVE
        df_gelive_het['REFLIV'] = df_gelive_het['REFLIV'].astype(str).str.split('.').str[0].str.strip()
        df_gelive_het['VIAGEM'] = df_gelive_het['REFLIV'].str[4:-2].str.extract(r'(\d+)')[0].fillna(0).astype(int)
        
        viagens_het = df_gelive_het['VIAGEM'].unique().tolist()
        
        if len(viagens_het) == 0:
            if fechar_conn:
                conn.close()
            return {"preparado": 0, "pendente": 0}
        
        # Query ONDAITM para HET
        viagens_str_het = ','.join([str(v) for v in viagens_het])
        query_ondaitm_het = f"""
        SELECT NUMVAG, PALETE, PREP, VIAGEM, CODTLI, STATUS, DONE, DATA, RCAIXAS, QTDLIDA, PESO
        FROM DANALLCDP.ONDAITM
        WHERE VIAGEM IN ({viagens_str_het})
            AND DATA >= '{data_ondaitm_inicial} 00:00:00'
            AND DATA <= '{data_ondaitm_final} 23:59:59'
            AND (CODTLI IS NULL OR TRIM(CODTLI) = '' OR CODTLI NOT LIKE '%HOM%')
        """
        
        cursor = conn.cursor()
        cursor.execute(query_ondaitm_het)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        df_ondaitm_het = pd.DataFrame.from_records(rows, columns=columns)
        cursor.close()
        
        if fechar_conn:
            conn.close()
        
        if df_ondaitm_het.empty:
            return {"preparado": 0, "pendente": 0}
        
        # Verificar status
        def verificar_status(row):
            try:
                rcaixas = float(str(row['RCAIXAS']).replace(',', '.'))
                qtdlida = float(str(row['QTDLIDA']).replace(',', '.'))
                if rcaixas == qtdlida:
                    return 'PREPARADO'
                else:
                    return 'INCOMPLETO'
            except Exception:
                return 'ERRO'
        
        df_ondaitm_het['STATUS_PREPARACAO'] = df_ondaitm_het.apply(verificar_status, axis=1)
        
        # Calcular totais
        tons_preparados = df_ondaitm_het[df_ondaitm_het['STATUS_PREPARACAO'] == 'PREPARADO']['PESO'].sum()
        tons_pendentes = df_ondaitm_het[df_ondaitm_het['STATUS_PREPARACAO'] == 'INCOMPLETO']['PESO'].sum()
        
        return {
            "preparado": float(tons_preparados) / 1000,  # Converter para toneladas
            "pendente": float(tons_pendentes) / 1000
        }
        
    except Exception as e:
        print(f"Erro ao processar HET: {e}")
        import traceback
        traceback.print_exc()
        return {"preparado": 0, "pendente": 0}

def processar_hom(data_inicial, data_final, conn=None):
    """
    Processa dados HOM da tabela GESUPE e ONDAITM
    Args:
        data_inicial: string no formato YYYYMMDD
        data_final: string no formato YYYYMMDD
        conn: conexão com banco (opcional)
    Returns:
        dict com preparado e pendente em kg
    """
    try:
        from .db_utils import get_db_connection
        import pandas as pd
        from datetime import datetime, timedelta
        
        fechar_conn = False
        if conn is None:
            conn = get_db_connection()
            fechar_conn = True
        
        # Converter para formato YYYY-MM-DD
        data_inicial_fmt = f"{data_inicial[:4]}-{data_inicial[4:6]}-{data_inicial[6:]}"
        data_final_fmt = f"{data_final[:4]}-{data_final[4:6]}-{data_final[6:]}"
        
        data_inicial_dt = datetime.strptime(data_inicial_fmt, "%Y-%m-%d")
        data_final_dt = datetime.strptime(data_final_fmt, "%Y-%m-%d")
        
        # Range amplo (±2 dias)
        data_ondaitm_inicial = (data_inicial_dt - timedelta(days=2)).strftime('%Y-%m-%d')
        data_ondaitm_final = (data_final_dt + timedelta(days=2)).strftime('%Y-%m-%d')
        data_gesupe_inicial = int((data_inicial_dt - timedelta(days=2)).strftime('%Y%m%d'))
        data_gesupe_final = int((data_final_dt + timedelta(days=2)).strftime('%Y%m%d'))
        
        # Query GELIVE para pegar viagens STD
        query_gelive_hom = f"""
        SELECT *
        FROM FGE5006CDP.GELIVE
        WHERE MAJCRE >= {data_inicial}
            AND MAJCRE <= {data_final}
            AND (HEUEXC >= 140000 OR HEUEXC <= 010000)
            AND (REFLIV LIKE '2414%' OR REFLIV LIKE '2401%')
            AND CODTLI = 'STD'
        """
        
        cursor = conn.cursor()
        cursor.execute(query_gelive_hom)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        df_gelive_hom = pd.DataFrame.from_records(rows, columns=columns)
        cursor.close()
        
        if df_gelive_hom.empty:
            if fechar_conn:
                conn.close()
            return {"preparado": 0, "pendente": 0}
        
        # Processar GELIVE
        df_gelive_hom['REFLIV'] = df_gelive_hom['REFLIV'].astype(str).str.split('.').str[0].str.strip()
        df_gelive_hom['VIAGEM'] = df_gelive_hom['REFLIV'].str[4:-2].str.extract(r'(\d+)')[0].fillna(0).astype(int)
        df_gelive_hom['CODTLI'] = df_gelive_hom['CODTLI'].astype(str).str.strip().str.upper()
        df_gelive_hom_unique = df_gelive_hom.drop_duplicates(subset=['VIAGEM'], keep='first')
        
        # Query GESUPE
        query_gesupe = f"""
        SELECT NUMSUP, TYPSUP, REFLIV, CARDES, MAJDAT, MAJCRE, MAJHMS
        FROM FGE5006CDP.GESUPE
        WHERE MAJCRE >= {data_gesupe_inicial}
            AND MAJCRE <= {data_gesupe_final}
            AND TYPSUP = 2
            AND (REFLIV LIKE '2414%' OR REFLIV LIKE '2401%')
        """
        
        cursor = conn.cursor()
        cursor.execute(query_gesupe)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        df_gesupe = pd.DataFrame.from_records(rows, columns=columns)
        cursor.close()
        
        if df_gesupe.empty:
            if fechar_conn:
                conn.close()
            return {"preparado": 0, "pendente": 0}
        
        # Processar GESUPE
        df_gesupe['VIAGEM'] = df_gesupe['REFLIV'].astype(str).str.strip().str[4:-2]
        df_gesupe['STATUS'] = df_gesupe['CARDES'].apply(
            lambda x: 'PREPARADO' if pd.notna(x) and str(x).strip() != '' else 'PENDENTE'
        )
        
        # Merge com GELIVE para trazer CODTLI
        df_gelive_hom_clean = df_gelive_hom_unique.copy()
        df_gelive_hom_clean['VIAGEM'] = df_gelive_hom_clean['VIAGEM'].astype(str).str.strip()
        
        df_gesupe_final = pd.merge(
            df_gesupe,
            df_gelive_hom_clean[['VIAGEM', 'CODTLI']],
            on='VIAGEM',
            how='inner'
        )
        
        # Filtrar apenas STD
        df_gesupe_hom = df_gesupe_final[df_gesupe_final['CODTLI'] == 'STD'].copy()
        
        if df_gesupe_hom.empty:
            if fechar_conn:
                conn.close()
            return {"preparado": 0, "pendente": 0}
        
        # Query ONDAITM para pegar pesos
        query_ondaitm_hom = f"""
        SELECT NUMSUP, PESO, VIAGEM
        FROM DANALLCDP.ONDAITM
        WHERE DATA >= '{data_ondaitm_inicial} 00:00:00'
            AND DATA <= '{data_ondaitm_final} 23:59:59'
        """
        
        cursor = conn.cursor()
        cursor.execute(query_ondaitm_hom)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        df_ondaitm_hom = pd.DataFrame.from_records(rows, columns=columns)
        cursor.close()
        
        if fechar_conn:
            conn.close()
        
        if df_ondaitm_hom.empty:
            return {"preparado": 0, "pendente": 0}
        
        df_ondaitm_peso = df_ondaitm_hom[['NUMSUP', 'PESO']].drop_duplicates(subset=['NUMSUP'])
        
        # Merge para trazer pesos
        df_merge_hom = pd.merge(df_gesupe_hom, df_ondaitm_peso, on='NUMSUP', how='left')
        df_com_peso_hom = df_merge_hom[df_merge_hom['PESO'].notna()]
        
        # Calcular totais
        peso_preparado = df_com_peso_hom[df_com_peso_hom['STATUS'] == 'PREPARADO']['PESO'].sum()
        peso_pendente = df_com_peso_hom[df_com_peso_hom['STATUS'] == 'PENDENTE']['PESO'].sum()
        
        return {
            "preparado": float(peso_preparado) / 1000,  # Converter para toneladas
            "pendente": float(peso_pendente) / 1000
        }
        
    except Exception as e:
        print(f"Erro ao processar HOM: {e}")
        import traceback
        traceback.print_exc()
        return {"preparado": 0, "pendente": 0}

def processar_pedidos_x7(data_busca):
    """
    Processa pedidos X7 da tabela GELIVE
    Args:
        data_busca: string no formato YYYYMMDD
    Returns:
        dict com total_registros, total_peso, lista de dados
    """
    try:
        from .db_utils import get_db_connection
        import pandas as pd
        
        conn = get_db_connection()
        
        # Consulta SQL baseada no script PEDIDO_X7.py
        query = f"""
        SELECT 
            MAJCRE, MAJDAT, HEUEXC, MAJHMS, 
            REFLIV, NUMVAG, ETALIV, CODTLI, 
            CUMPRD, CUMLIG, CUMPOI
        FROM FGE5006CDP.GELIVE
        WHERE MAJCRE = {data_busca}
          AND (REFLIV LIKE '2414%' OR REFLIV LIKE '2401%')
          AND CODTLI = 'STD'
          AND INT(SUBSTR(DIGITS(HEUEXC),1,2)) BETWEEN 14 AND 23
        """
        
        # Executar query usando cursor
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Obter nomes das colunas
        columns = [column[0] for column in cursor.description]
        
        # Buscar todos os resultados
        rows = cursor.fetchall()
        
        # Criar DataFrame manualmente
        df = pd.DataFrame.from_records(rows, columns=columns)
        
        cursor.close()
        conn.close()
        
        if df.empty:
            return {
                "success": True,
                "total_registros": 0,
                "total_peso": 0,
                "dados": []
            }
        
        # Processar dados conforme script original
        # Limpar REFLIV
        df['REFLIV'] = df['REFLIV'].astype(str).str.split('.').str[0].str.strip()
        
        # VIAGEM: do 5º caractere até os dois últimos
        df['VIAGEM'] = df['REFLIV'].str[4:-2].str.extract(r'(\d+)').fillna(0).astype(int)
        
        # PALETE: dois últimos dígitos
        df['PALETE'] = df['REFLIV'].str[-2:].str.extract(r'(\d+)').fillna(0).astype(int)
        
        # Converter HEUEXC para HH:MM:SS
        df['HEUEXC'] = pd.to_datetime(
            df['HEUEXC'].astype(str).str.split('.').str[0].str.zfill(6),
            format='%H%M%S', errors='coerce'
        ).dt.strftime('%H:%M:%S')
        
        # Converter MAJHMS para HH:MM:SS
        df['MAJHMS'] = df['MAJHMS'].astype(str).str.split('.').str[0].str.zfill(6)
        df['MAJHMS'] = df['MAJHMS'].str.replace(r'(\d{2})(\d{2})(\d{2})', r'\1:\2:\3', regex=True)
        
        # Renomear colunas
        df = df[[
            "MAJCRE", "MAJDAT", "HEUEXC", "MAJHMS",
            "REFLIV", "VIAGEM", "PALETE",
            "NUMVAG", "ETALIV", "CODTLI",
            "CUMPRD", "CUMLIG", "CUMPOI"
        ]]
        
        df.columns = [
            "DATA_PED", "DATA_X7", "HORA_X7", "HORA304",
            "REFLIV", "VIAGEM", "PALETE",
            "NRO_OND", "ETALIV", "CODTLI",
            "CAIXA01", "CAIXA05", "PESO_201"
        ]
        
        # Calcular total de peso
        total_peso = pd.to_numeric(df['PESO_201'], errors='coerce').sum()
        
        return {
            "success": True,
            "total_registros": len(df),
            "total_peso": round(total_peso, 2),
            "dados": df.to_dict('records')
        }
        
    except Exception as e:
        print(f"Erro ao processar pedidos X7: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "total_registros": 0,
            "total_peso": 0,
            "dados": []
        }

def clear_cache():
    global cache_store, cache_timestamps
    cache_store = {}
    cache_timestamps = {}

cache_store = {}
cache_timestamps = {}

def obter_status_prep(data_inicial, data_final, nome_preparador):
    """
    Obtém o status de preparação dos produtos
    Args:
        data_inicial: string no formato YYYY-MM-DD
        data_final: string no formato YYYY-MM-DD
        nome_preparador: string com nome ou código do preparador (opcional)
    """
    try:
        from .db_utils import get_db_connection
        import pandas as pd
        
        conn = get_db_connection()
        
        # Consulta ONDAITM com filtro de intervalo de datas
        query = f"""
        SELECT NUMVAG, PALETE, PREP, VIAGEM, CODTLI, STATUS, DONE, DATA, RCAIXAS, QTDLIDA
        FROM DANALLCDP.ONDAITM
        WHERE DATA >= '{data_inicial} 00:00:00' AND DATA <= '{data_final} 23:59:59'
          AND (CODTLI IS NULL OR TRIM(CODTLI) = '')
        """
        
        # Se preparador foi especificado, adiciona filtro
        if nome_preparador:
            query += f" AND UPPER(TRIM(PREP)) LIKE '%{nome_preparador.upper()}%'"
        
        # Executar query usando cursor para evitar problemas de compatibilidade com pandas
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Obter nomes das colunas
        columns = [column[0] for column in cursor.description]
        
        # Buscar todos os resultados
        rows = cursor.fetchall()
        
        # Criar DataFrame manualmente
        df_ondaitm = pd.DataFrame.from_records(rows, columns=columns)
        
        cursor.close()
        conn.close()
        
        if df_ondaitm.empty:
            return {
                "success": True,
                "total": 0,
                "preparados": 0,
                "incompletos": 0,
                "erro": 0,
                "dados": [],
                "viagens_pendentes": []
            }
        
        # Filtra apenas linhas onde CODTLI está vazia ou nula
        df_filtrado = df_ondaitm[(df_ondaitm['CODTLI'].isna()) | (df_ondaitm['CODTLI'].astype(str).str.strip() == '')]
        df_filtrado = df_filtrado.dropna(how='all')
        
        # Função para verificar status
        def verificar_status(row):
            try:
                rcaixas = float(str(row['RCAIXAS']).replace(',', '.'))
                qtdlida = float(str(row['QTDLIDA']).replace(',', '.'))
                if rcaixas == qtdlida:
                    return 'PREPARADO'
                else:
                    return 'INCOMPLETO'
            except Exception:
                return 'ERRO'
        
        df_filtrado['STATUS_PREPARACAO'] = df_filtrado.apply(verificar_status, axis=1)
        
        # Agrupar por VIAGEM+PALETE e verificar o status de cada palete
        def status_palete(grupo):
            if all(grupo == 'PREPARADO'):
                return 'PREPARADO'
            elif any(grupo == 'ERRO'):
                return 'ERRO'
            else:
                return 'INCOMPLETO'
        
        paletes_status = df_filtrado.groupby(['VIAGEM', 'PALETE'])['STATUS_PREPARACAO'].apply(status_palete)
        
        # Contar paletes por status
        paletes_preparados = int((paletes_status == 'PREPARADO').sum())
        paletes_incompletos = int((paletes_status == 'INCOMPLETO').sum())
        paletes_erro = int((paletes_status == 'ERRO').sum())
        
        # Agrupar todas as linhas por VIAGEM+PALETE e somar QTDLIDA (igual ao PHP)
        paletes_dict = {}
        for _, row in df_filtrado.iterrows():
            chave = (str(row['VIAGEM']), str(row['PALETE']))
            
            if chave not in paletes_dict:
                paletes_dict[chave] = {
                    'viagem': str(row['VIAGEM']),
                    'palete': str(row['PALETE']),
                    'prep': str(row['PREP']) if pd.notna(row['PREP']) else '',
                    'lido': 0,
                    'total': 0,
                    'status': None
                }
            
            # Somar QTDLIDA e RCAIXAS de todas as linhas
            try:
                qtd = float(str(row['QTDLIDA']).replace(',', '.')) if pd.notna(row['QTDLIDA']) else 0
                paletes_dict[chave]['lido'] += int(qtd)
            except:
                pass
            
            try:
                rcx = float(str(row['RCAIXAS']).replace(',', '.')) if pd.notna(row['RCAIXAS']) else 0
                paletes_dict[chave]['total'] += int(rcx)
            except:
                pass
            
            # Guardar status do palete (se pelo menos uma linha é INCOMPLETO, palete fica INCOMPLETO)
            if row['STATUS_PREPARACAO'] == 'INCOMPLETO':
                paletes_dict[chave]['status'] = 'INCOMPLETO'
            elif paletes_dict[chave]['status'] != 'INCOMPLETO' and row['STATUS_PREPARACAO'] == 'PREPARADO':
                paletes_dict[chave]['status'] = 'PREPARADO'
        
        # Filtrar apenas paletes incompletos para a lista
        lista_viagens_pendentes = [p for p in paletes_dict.values() if p['status'] == 'INCOMPLETO']
        # Remover campo status antes de enviar
        for p in lista_viagens_pendentes:
            del p['status']
        
        # Paletes preparados (status PREPARADO) - agrupados por viagem, palete e prep
        viagens_preparadas_df = df_filtrado[df_filtrado['STATUS_PREPARACAO'] == 'PREPARADO']
        lista_paletes_preparados = []
        if not viagens_preparadas_df.empty:
            agrupado = viagens_preparadas_df.groupby(['VIAGEM', 'PALETE', 'PREP'], as_index=False).first()
            for _, row in agrupado.iterrows():
                lista_paletes_preparados.append({
                    'viagem': str(row['VIAGEM']),
                    'palete': str(row['PALETE']),
                    'prep': str(row['PREP']) if pd.notna(row['PREP']) else ''
                })

        return {
            "success": True,
            "total": len(df_filtrado),
            "preparados": paletes_preparados,
            "incompletos": paletes_incompletos,
            "erro": paletes_erro,
            "dados": df_filtrado.to_dict('records'),
            "viagens_pendentes": lista_viagens_pendentes,
            "viagens_preparadas": lista_paletes_preparados
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total": 0,
            "preparados": 0,
            "incompletos": 0,
            "erro": 0,
            "dados": [],
            "viagens_pendentes": []
        }

def cache_with_timeout(timeout_seconds=300):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def buscar_conferencia_viagem(viagem):
    """
    Busca dados de conferência de paletes de uma viagem
    Integração com sistema externo via requests
    """
    import requests
    from bs4 import BeautifulSoup
    
    try:
        # Sistema 1: Status Ring
        url_viagem = "http://172.19.0.44:8001/status_ring/index.php"
        sessao = requests.Session()
        dados_login = {"login": "CDP174176", "senha": "099475", "entrar": "Entrar"}
        url_login = "http://172.19.0.44:8001/verifica_login.php"
        
        # Fazer login
        sessao.post(url_login, data=dados_login)
        
        # Buscar dados da viagem
        payload = {"local": "linha.php", "viagem": str(viagem)}
        response = sessao.post(url_viagem, data=payload)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Erro ao buscar viagem. Status: {response.status_code}"}
        
        # Extrair paletes HET da tabela
        soup = BeautifulSoup(response.text, "html.parser")
        div_viagem = soup.find("div", {"id": "rel_viagem"})
        if not div_viagem:
            return {"success": False, "error": "Dados da viagem não encontrados"}
        
        tabela = div_viagem.find("table", {"class": "table table-hover"})
        if not tabela:
            return {"success": False, "error": "Tabela não encontrada"}
        
        paletes_het = []
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
                paletes_het.append(palete)
        
        if not paletes_het:
            return {"success": False, "error": "Nenhum palete HET encontrado nesta viagem"}
        
        # Sistema 2: Suporte (conferência)
        BASE_URL = "http://172.19.0.44:8002"
        LOGIN_URL = f"{BASE_URL}/verifica_login.php"
        SUPORTE_URL = f"{BASE_URL}/index.php"
        
        session2 = requests.Session()
        CREDENCIAIS = {"login": "CDP174176", "senha": "099475"}
        
        # Login no sistema de suporte
        res = session2.post(LOGIN_URL, data=CREDENCIAIS)
        if res.status_code != 200 or "Usuário não tem acesso!" in res.text:
            return {"success": False, "error": "Erro no login do sistema de conferência"}
        
        # Verificar status de cada palete
        resultado_paletes = []
        paletes_validos = 0
        
        for palete in paletes_het:
            suporte_id = f"{viagem}{palete}"
            payload = {"suporte": suporte_id, "button_viagem": "Ok"}
            res = session2.post(SUPORTE_URL, data=payload)
            
            if res.status_code != 200:
                continue
            
            soup = BeautifulSoup(res.text, "html.parser")
            tabela = soup.find("table")
            if not tabela:
                continue
            
            tbody = tabela.find("tbody")
            if not tbody:
                continue
            
            linhas = tbody.find_all("tr")
            if not linhas:
                # Palete não lançado
                resultado_paletes.append({
                    "palete": palete,
                    "status": "nao_lancado",
                    "porcentagem": 0,
                    "total_linhas": 0,
                    "conferidas": 0
                })
                break  # Para de buscar se encontrou não lançado
            
            paletes_validos += 1
            total_linhas = len(linhas)
            linhas_gray = sum(1 for row in linhas if "gray" in (row.get("class") or []))
            todas_gray = all("gray" in (row.get("class") or []) for row in linhas)
            porcentagem = (linhas_gray / total_linhas * 100) if total_linhas > 0 else 0
            
            if todas_gray:
                status = "completo"
            else:
                status = "pendente"
            
            resultado_paletes.append({
                "palete": palete,
                "status": status,
                "porcentagem": round(porcentagem, 1),
                "total_linhas": total_linhas,
                "conferidas": linhas_gray
            })
        
        if paletes_validos == 0:
            return {"success": False, "error": "Nenhum palete lançado para conferência"}
        
        return {
            "success": True,
            "viagem": viagem,
            "paletes": resultado_paletes,
            "total_paletes": len(resultado_paletes),
            "completos": sum(1 for p in resultado_paletes if p["status"] == "completo"),
            "pendentes": sum(1 for p in resultado_paletes if p["status"] == "pendente")
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
