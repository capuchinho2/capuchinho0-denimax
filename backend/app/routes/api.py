from flask import Blueprint, jsonify, request, send_file
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
import pyodbc
import requests
from io import BytesIO
from ..utils.db_utils import get_db_connection
from ..utils.logic import processar_het, processar_hom, processar_pedidos_x7, clear_cache, cache_store, cache_timestamps, obter_status_prep, cache_with_timeout
from ..utils.parte_coleta import coletar_registros, registros_para_checklists

api_bp = Blueprint('api', __name__)

TELEGRAM_API_URL = "https://api.telegram.org"


def carregar_configuracao_telegram():
    arquivo_env = Path(__file__).resolve().parent.parent / "utils" / ".env"
    if not arquivo_env.exists():
        return
    for linha in arquivo_env.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        valor = valor.strip().strip('"').strip("'")
        os.environ.setdefault(chave.strip(), valor)


carregar_configuracao_telegram()


def enviar_mensagem_telegram(mensagem, chat_id=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    destino = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado.")
    if not destino:
        raise RuntimeError("TELEGRAM_CHAT_ID não configurado.")

    blocos = mensagem.split("\n\n")
    partes = []
    parte_atual = ""
    for bloco in blocos:
        candidato = f"{parte_atual}\n\n{bloco}" if parte_atual else bloco
        if len(candidato) <= 4096:
            parte_atual = candidato
        else:
            if parte_atual:
                partes.append(parte_atual)
            while len(bloco) > 4096:
                partes.append(bloco[:4096])
                bloco = bloco[4096:]
            parte_atual = bloco
    if parte_atual:
        partes.append(parte_atual)

    resultados = []
    for parte in partes:
        resposta = requests.post(
            f"{TELEGRAM_API_URL}/bot{token}/sendMessage",
            json={"chat_id": destino, "text": parte},
            timeout=15,
        )
        try:
            resultado = resposta.json()
        except ValueError:
            resultado = {}
        if not resposta.ok or not resultado.get("ok"):
            descricao = resultado.get("description", resposta.text or "Erro sem descrição")
            raise RuntimeError(f"Telegram recusou a mensagem: {descricao}")
        resultados.append(resultado.get("result", {}))
    return resultados


@api_bp.route('/api/checklist/coletar', methods=['GET'])
def coletar_checklists_api():
    try:
        hoje = datetime.now().strftime('%d/%m/%Y')
        data_inicial = request.args.get('data_inicial', hoje)
        data_final = request.args.get('data_final', hoje)
        status = request.args.get('status', 'Todos')
        registros = coletar_registros(
            status_escolhido=status,
            data_inicial=data_inicial,
            data_final=data_final,
        )
        return jsonify({
            "success": True,
            "total": len(registros),
            "dados": registros_para_checklists(registros),
        })
    except Exception as erro:
        return jsonify({"success": False, "error": str(erro)}), 502


@api_bp.route('/api/checklist/coletar-auto', methods=['GET'])
def coletar_checklists_auto_api():
    try:
        agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
        ontem = (agora - timedelta(days=1)).strftime('%d/%m/%Y')
        hoje = agora.strftime('%d/%m/%Y')
        registros = coletar_registros(
            status_escolhido="Todos",
            data_inicial=ontem,
            data_final=hoje,
        )
        dados = registros_para_checklists(registros)
        pendentes = [
            item for item in dados
            if str(item.get('status', '')).strip().lower() in {'criado', 'em andamento'}
        ]
        return jsonify({
            "success": True,
            "total": len(pendentes),
            "periodo": {"data_inicial": ontem, "data_final": hoje},
            "dados": pendentes,
        })
    except Exception as erro:
        return jsonify({"success": False, "error": str(erro)}), 502


@api_bp.route('/api/checklist/enviar-telegram', methods=['POST'])
def enviar_checklists_telegram_api():
    try:
        dados = request.get_json(silent=True) or {}
        checklists = dados.get('checklists', [])
        if not checklists:
            return jsonify({"success": False, "error": "Nenhum checklist informado."}), 400

        responsavel = dados.get('responsavel', 'Daniel Capuchinho')
        linhas = [
            f"Olá, {responsavel}!",
            "Existem checklists pendentes:",
            "",
        ]
        for checklist in checklists:
            linhas.append(
                "------------------------------\n"
                f"Nome: {checklist.get('responsavel', '') or 'Não informado'}\n"
                f"Checklist: {checklist.get('checklist', 'Checklist')}\n"
                f"N° Equip: {checklist.get('informacoes', '') or 'Não informado'}\n"
                f"Status: {checklist.get('status', '') or 'Não informado'}\n"
                f"Data: {checklist.get('data_hora', '') or 'Não informado'}\n"
                "------------------------------"
            )
        linhas.extend(["", "Por favor, verifique e finalize os checklists."])
        mensagem = "\n".join(linhas)
        telegram = enviar_mensagem_telegram(mensagem, dados.get('chat_id'))
        return jsonify({
            "success": True,
            "responsavel": responsavel,
            "mensagem": mensagem,
            "telegram": telegram,
        })
    except Exception as erro:
        return jsonify({"success": False, "error": str(erro)}), 503

@api_bp.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "API está funcionando"})

@api_bp.route('/api/volumes', methods=['POST'])
def get_volumes():
    try:
        data = request.get_json()
        data_inicial = data.get('data_inicial')
        data_final = data.get('data_final')
        if not data_inicial or not data_final:
            return jsonify({"error": "data_inicial e data_final são obrigatórios"}), 400
        if len(data_inicial) != 8 or len(data_final) != 8:
            return jsonify({"error": "Datas devem estar no formato AAAAMMDD"}), 400
        dados_het = processar_het(data_inicial, data_final)
        dados_hom = processar_hom(data_inicial, data_final)
        dados_pedidos_x7 = processar_pedidos_x7(data_inicial)
        total_preparado = dados_het['preparado'] + dados_hom['preparado']
        total_pendente = dados_het['pendente'] + dados_hom['pendente']
        total_geral = total_preparado + total_pendente
        return jsonify({
            "success": True,
            "data": {
                "het": dados_het,
                "hom": dados_hom,
                "pedidos_x7": dados_pedidos_x7,
                "consolidado": {
                    "preparado": round(total_preparado, 4),
                    "pendente": round(total_pendente, 4),
                    "total": round(total_geral, 4)
                }
            }
        })
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Erro ao processar dados: {str(e)}"}), 500

@api_bp.route('/api/volumes/hoje', methods=['GET'])
def get_volumes_hoje():
    try:
        hoje = datetime.now().strftime('%Y%m%d')
        dados_het = processar_het(hoje, hoje)
        dados_hom = processar_hom(hoje, hoje)
        dados_pedidos_x7 = processar_pedidos_x7(hoje)
        total_preparado = dados_het['preparado'] + dados_hom['preparado']
        total_pendente = dados_het['pendente'] + dados_hom['pendente']
        total_geral = total_preparado + total_pendente
        resultado = {
            "success": True,
            "data": {
                "data": hoje,
                "het": dados_het,
                "hom": dados_hom,
                "pedidos_x7": dados_pedidos_x7,
                "consolidado": {
                    "preparado": round(total_preparado, 4),
                    "pendente": round(total_pendente, 4),
                    "total": round(total_geral, 4)
                }
            }
        }
        return jsonify(resultado)
    except pyodbc.Error as db_error:
        error_msg = f"Erro de banco de dados: {str(db_error)}"
        return jsonify({"success": False, "error": error_msg}), 500
    except Exception as e:
        error_msg = f"Erro ao processar dados: {str(e)}"
        return jsonify({"success": False, "error": error_msg}), 500

@api_bp.route('/api/viagem/adicionar-tra', methods=['POST'])
@api_bp.route('/api/viagem/adicionar-trn', methods=['POST'])
def adicionar_viagem_trn():
    try:
        data = request.get_json()
        numero_viagem = data.get('numero_viagem', '').strip()
        if not numero_viagem:
            return jsonify({"success": False, "error": "Número da viagem é obrigatório"}), 400
        if not numero_viagem.isdigit():
            return jsonify({"success": False, "error": "Número da viagem deve conter apenas dígitos"}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        query_buscar = f"""
        SELECT REFLIV, MAJCRE, CODTLI
        FROM FGE5006CDP.GELIVE
        WHERE CODTLI = 'TRA'
          AND (REFLIV LIKE '2414%' OR REFLIV LIKE '2401%')
        """
        cursor.execute(query_buscar)
        todos_registros = cursor.fetchall()
        registros_encontrados = []
        for row in todos_registros:
            refliv = str(row[0]).strip()
            if len(refliv) >= 6:
                viagem_extraida = refliv[4:-2] if len(refliv) > 6 else refliv[4:]
                viagem_extraida_num = viagem_extraida.lstrip('0')
                numero_viagem_num = numero_viagem.lstrip('0')
                if viagem_extraida_num == numero_viagem_num or numero_viagem in refliv:
                    registros_encontrados.append(row)
        if not registros_encontrados:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": f"Nenhuma viagem TRA encontrada com o número {numero_viagem}"}), 404
        refliv_list = [row[0].strip() for row in registros_encontrados]
        refliv_conditions = " OR ".join([f"REFLIV = '{ref}'" for ref in refliv_list])
        query_update = f"""
        UPDATE FGE5006CDP.GELIVE
        SET CODTLI = 'STD'
        WHERE ({refliv_conditions}) AND CODTLI = 'TRA'
        """
        cursor.execute(query_update)
        conn.commit()
        registros_atualizados = cursor.rowcount
        cursor.close()
        conn.close()
        clear_cache()
        return jsonify({
            "success": True,
            "message": f"Viagem {numero_viagem} convertida com sucesso",
            "registros_atualizados": registros_atualizados,
            "refliv_list": refliv_list
        })
    except pyodbc.Error as db_error:
        error_msg = f"Erro de banco de dados: {str(db_error)}"
        return jsonify({"success": False, "error": error_msg}), 500
    except Exception as e:
        error_msg = f"Erro ao adicionar viagem: {str(e)}"
        return jsonify({"success": False, "error": error_msg}), 500

@api_bp.route('/api/exportar-viagens', methods=['POST'])
def exportar_viagens():
    try:
        data = request.get_json()
        data_inicial = data.get('data_inicial', '')
        data_final = data.get('data_final', '')
        if not data_inicial or not data_final:
            return jsonify({"success": False, "error": "Datas inicial e final são obrigatórias"}), 400
        conn = get_db_connection()
        data_inicial_fmt = data_inicial.replace("-", "")
        data_final_fmt = data_final.replace("-", "")
        query_todas = f"""
        SELECT 
            MAJCRE as DATA_CRIACAO,
            MAJDAT as DATA_MOVIMENTO,
            HEUEXC as HORA_EXCLUSAO,
            MAJHMS as HORA_MOVIMENTO,
            REFLIV as REFERENCIA,
            NUMVAG as NUMERO_VIAGEM,
            ETALIV as ESTADO,
            CODTLI as TIPO_LIVRAISON,
            CUMPRD as PESO_PRODUTO,
            CUMLIG as PESO_LIGADO,
            CUMPOI as PESO_TOTAL
        FROM FGE5006CDP.GELIVE
        WHERE MAJCRE >= '{data_inicial_fmt}'
          AND MAJCRE <= '{data_final_fmt}'
          AND (REFLIV LIKE '2414%' OR REFLIV LIKE '2401%')
        ORDER BY MAJCRE DESC, HEUEXC DESC
        """
        query_x7 = f"""
        SELECT 
            MAJCRE as DATA_CRIACAO,
            MAJDAT as DATA_MOVIMENTO,
            HEUEXC as HORA_EXCLUSAO,
            MAJHMS as HORA_MOVIMENTO,
            REFLIV as REFERENCIA,
            NUMVAG as NUMERO_VIAGEM,
            ETALIV as ESTADO,
            CODTLI as TIPO_LIVRAISON,
            CUMPRD as PESO_PRODUTO,
            CUMLIG as PESO_LIGADO,
            CUMPOI as PESO_TOTAL
        FROM FGE5006CDP.GELIVE
        WHERE MAJCRE >= '{data_inicial_fmt}'
          AND MAJCRE <= '{data_final_fmt}'
          AND (REFLIV LIKE '2414%' OR REFLIV LIKE '2401%')
          AND CODTLI = 'STD'
          AND INT(SUBSTR(DIGITS(HEUEXC),1,2)) BETWEEN 14 AND 23
        ORDER BY MAJCRE DESC, HEUEXC DESC
        """
        df_todas = pd.read_sql(query_todas, conn)
        df_x7 = pd.read_sql(query_x7, conn)
        conn.close()
        if df_todas.empty:
            return jsonify({"success": False, "error": "Nenhuma viagem encontrada no período"}), 404
        def formatar_dataframe(df):
            df['DATA_CRIACAO'] = pd.to_datetime(df['DATA_CRIACAO'], format='%Y%m%d', errors='coerce').dt.strftime('%d/%m/%Y')
            df['DATA_MOVIMENTO'] = pd.to_datetime(df['DATA_MOVIMENTO'], format='%Y%m%d', errors='coerce').dt.strftime('%d/%m/%Y')
            df['HORA_EXCLUSAO'] = df['HORA_EXCLUSAO'].astype(str).str.zfill(6).apply(lambda x: f"{x[:2]}:{x[2:4]}:{x[4:]}")
            df['HORA_MOVIMENTO'] = df['HORA_MOVIMENTO'].astype(str).str.zfill(6).apply(lambda x: f"{x[:2]}:{x[2:4]}:{x[4:]}")
            df['PESO_PRODUTO_TON'] = (df['PESO_PRODUTO'] / 1000).round(4)
            df['PESO_LIGADO_TON'] = (df['PESO_LIGADO'] / 1000).round(4)
            df['PESO_TOTAL_TON'] = (df['PESO_TOTAL'] / 1000).round(4)
            return df
        df_todas = formatar_dataframe(df_todas)
        df_x7 = formatar_dataframe(df_x7) if not df_x7.empty else df_x7
        df_viagens = df_todas.copy()
        df_viagens['REFERENCIA'] = df_viagens['REFERENCIA'].astype(str).str.strip()
        def extrair_viagem(refliv):
            refliv = str(refliv).strip()
            if len(refliv) >= 6:
                viagem = refliv[4:-2] if len(refliv) > 6 else refliv[4:]
                return viagem
            return ''
        df_viagens['VIAGEM'] = df_viagens['REFERENCIA'].apply(extrair_viagem)
        df_viagens['PALETE'] = df_viagens['REFERENCIA'].str[-2:]
        cols = df_viagens.columns.tolist()
        ref_idx = cols.index('REFERENCIA')
        cols.insert(ref_idx + 1, cols.pop(cols.index('VIAGEM')))
        cols.insert(ref_idx + 2, cols.pop(cols.index('PALETE')))
        df_viagens = df_viagens[cols]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_todas.to_excel(writer, index=False, sheet_name='Todas_Viagens')
            if not df_x7.empty:
                df_x7.to_excel(writer, index=False, sheet_name='PEDIDO_X7')
            df_viagens.to_excel(writer, index=False, sheet_name='VIAGEM')
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                if sheet_name == 'Todas_Viagens':
                    df_ref = df_todas
                elif sheet_name == 'PEDIDO_X7':
                    df_ref = df_x7
                else:
                    df_ref = df_viagens
                for idx, col in enumerate(df_ref.columns):
                    max_length = max(df_ref[col].astype(str).apply(len).max(), len(col)) + 2
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        output.seek(0)
        filename = f"viagens_{data_inicial}_a_{data_final}.xlsx"
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except pyodbc.Error as db_error:
        error_msg = f"Erro de banco de dados: {str(db_error)}"
        return jsonify({"success": False, "error": error_msg}), 500
    except Exception as e:
        error_msg = f"Erro ao exportar viagens: {str(e)}"
        return jsonify({"success": False, "error": error_msg}), 500

@api_bp.route('/api/cache/clear', methods=['POST'])
def limpar_cache_endpoint():
    try:
        clear_cache()
        return jsonify({"success": True, "message": "Cache limpo com sucesso"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/api/cache/status', methods=['GET'])
def status_cache():
    try:
        cache_info = {
            "total_items": len(cache_store),
            "items": []
        }
        current_time = time.time()
        for key in cache_store.keys():
            cached_time = cache_timestamps.get(key, 0)
            age_seconds = int(current_time - cached_time)
            cache_info["items"].append({
                "key": key[:50] + "..." if len(key) > 50 else key,
                "age_seconds": age_seconds
            })
        return jsonify({"success": True, "cache": cache_info})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/api/status-prep', methods=['GET'])
def obter_status_prep_endpoint():
    from ..utils.colaborador_utils import buscar_nome_colaborador_por_codigo
    try:
        data_inicial = request.args.get('dataInicial')
        data_final = request.args.get('dataFinal')
        nome_preparador = request.args.get('preparador', '').strip()
        
        print(f"[DEBUG] Recebendo requisição: dataInicial={data_inicial}, dataFinal={data_final}, preparador={nome_preparador}")
        
        if not data_inicial or not data_final:
            return jsonify({"success": False, "error": "Parâmetros dataInicial e dataFinal são obrigatórios"}), 400
        
        resultado = obter_status_prep(data_inicial, data_final, nome_preparador)
        
        # Adicionar nome do colaborador para cada viagem pendente
        if resultado.get('success') and resultado.get('viagens_pendentes'):
            print(f"[DEBUG] Adicionando nomes para {len(resultado['viagens_pendentes'])} viagens pendentes")
            for viagem in resultado['viagens_pendentes']:
                codigo = viagem.get('prep', '').strip()
                print(f"[DEBUG] Buscando nome para código: '{codigo}'")
                nome = buscar_nome_colaborador_por_codigo(codigo) if codigo else None
                viagem['nome'] = nome
                print(f"[DEBUG] Nome encontrado: {nome}")
        
        print(f"[DEBUG] Resultado obtido: success={resultado.get('success')}, preparados={resultado.get('preparados')}, viagens_preparadas={len(resultado.get('viagens_preparadas', []))}")
        
        if resultado.get('success'):
            return jsonify(resultado)
        else:
            print(f"[ERROR] Erro no resultado: {resultado.get('error')}")
            return jsonify(resultado), 500
    except Exception as e:
        print(f"[ERROR] Exceção no endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/api/conferencia/viagem', methods=['GET'])
def buscar_conferencia():
    from ..utils.logic import buscar_conferencia_viagem
    
    viagem = request.args.get('viagem')
    if not viagem:
        return jsonify({"success": False, "error": "Parâmetro 'viagem' é obrigatório"}), 400
    
    resultado = buscar_conferencia_viagem(viagem)
    return jsonify(resultado)

@api_bp.route('/api/exportar-dashboard-excel', methods=['POST'])
def exportar_dashboard_excel():
    """
    Exporta Excel com duas abas:
    - PEDIDO_X7: Viagens de faturamento do período
    - Volume_HET_e_HOM_Consolidado: Dados consolidados de HET e HOM
    """
    try:
        data = request.get_json()
        data_inicial = data.get('data_inicial', '')
        data_final = data.get('data_final', '')
        
        if not data_inicial or not data_final:
            return jsonify({"success": False, "error": "Datas inicial e final são obrigatórias"}), 400
        
        # Formato YYYYMMDD
        data_inicial_fmt = data_inicial.replace("-", "")
        data_final_fmt = data_final.replace("-", "")
        
        conn = get_db_connection()
        
        # === ABA 1: PEDIDO_X7 ===
        query_pedido_x7 = f"""
        SELECT 
            MAJCRE as DATA_PED,
            MAJDAT as DATA_X7,
            HEUEXC as HORA_X7,
            MAJHMS as HORA304,
            REFLIV,
            NUMVAG as NRO_OND,
            ETALIV,
            CODTLI,
            CUMPRD as CAIXA01,
            CUMLIG as CAIXA05,
            CUMPOI as PESO_201
        FROM FGE5006CDP.GELIVE
        WHERE MAJCRE >= '{data_inicial_fmt}'
          AND MAJCRE <= '{data_final_fmt}'
          AND (REFLIV LIKE '2414%' OR REFLIV LIKE '2401%')
          AND CODTLI = 'STD'
          AND INT(SUBSTR(DIGITS(HEUEXC),1,2)) BETWEEN 14 AND 23
        ORDER BY MAJCRE DESC, HEUEXC DESC
        """
        
        df_pedido_x7 = pd.read_sql(query_pedido_x7, conn)
        
        # Processar PEDIDO_X7
        if not df_pedido_x7.empty:
            df_pedido_x7['REFLIV'] = df_pedido_x7['REFLIV'].astype(str).str.split('.').str[0].str.strip()
            df_pedido_x7['VIAGEM'] = df_pedido_x7['REFLIV'].str[4:-2].str.extract(r'(\d+)')[0].fillna(0).astype(int)
            df_pedido_x7['PALETE'] = df_pedido_x7['REFLIV'].str[-2:].str.extract(r'(\d+)')[0].fillna(0).astype(int)
            
            # Formatar datas e horas
            df_pedido_x7['DATA_PED'] = pd.to_datetime(df_pedido_x7['DATA_PED'], format='%Y%m%d', errors='coerce').dt.strftime('%d/%m/%Y')
            df_pedido_x7['DATA_X7'] = pd.to_datetime(df_pedido_x7['DATA_X7'], format='%Y%m%d', errors='coerce').dt.strftime('%d/%m/%Y')
            df_pedido_x7['HORA_X7'] = df_pedido_x7['HORA_X7'].astype(str).str.zfill(6).apply(lambda x: f"{x[:2]}:{x[2:4]}:{x[4:]}")
            df_pedido_x7['HORA304'] = df_pedido_x7['HORA304'].astype(str).str.zfill(6).apply(lambda x: f"{x[:2]}:{x[2:4]}:{x[4:]}")
            
            # Reordenar colunas
            cols = ['DATA_PED', 'DATA_X7', 'HORA_X7', 'HORA304', 'REFLIV', 'VIAGEM', 'PALETE', 
                    'NRO_OND', 'ETALIV', 'CODTLI', 'CAIXA01', 'CAIXA05', 'PESO_201']
            df_pedido_x7 = df_pedido_x7[cols]
        
        # === ABA 2: Volume_HET_e_HOM_Consolidado ===
        # Obter todas as viagens STD do período para HET e HOM
        query_het_hom = f"""
        SELECT 
            MAJCRE as DATA_CRIACAO,
            MAJDAT as DATA_MOVIMENTO,
            HEUEXC as HORA_EXCLUSAO,
            REFLIV,
            NUMVAG as NUMERO_VIAGEM,
            CODTLI as TIPO,
            CUMPRD as PESO_PRODUTO,
            CUMLIG as PESO_LIGADO,
            CUMPOI as PESO_TOTAL
        FROM FGE5006CDP.GELIVE
        WHERE MAJCRE >= '{data_inicial_fmt}'
          AND MAJCRE <= '{data_final_fmt}'
          AND (REFLIV LIKE '2414%' OR REFLIV LIKE '2401%')
          AND CODTLI = 'STD'
        ORDER BY MAJCRE DESC, HEUEXC DESC
        """
        
        df_het_hom = pd.read_sql(query_het_hom, conn)
        conn.close()
        
        # Processar Volume HET e HOM
        if not df_het_hom.empty:
            df_het_hom['REFLIV'] = df_het_hom['REFLIV'].astype(str).str.split('.').str[0].str.strip()
            df_het_hom['VIAGEM'] = df_het_hom['REFLIV'].str[4:-2].str.extract(r'(\d+)')[0].fillna(0).astype(int)
            df_het_hom['PALETE'] = df_het_hom['REFLIV'].str[-2:].str.extract(r'(\d+)')[0].fillna(0).astype(int)
            
            # Classificar HET ou HOM baseado na hora
            def classificar_tipo(hora):
                try:
                    hora_int = int(str(hora).split('.')[0])
                    hora_formatada = int(str(hora_int).zfill(6)[:2])
                    if 14 <= hora_formatada <= 23:
                        return 'HET'
                    elif 0 <= hora_formatada <= 1:
                        return 'HET'
                    else:
                        return 'HOM'
                except:
                    return 'N/A'
            
            df_het_hom['CLASSIFICACAO'] = df_het_hom['HORA_EXCLUSAO'].apply(classificar_tipo)
            
            # Formatar datas e horas
            df_het_hom['DATA_CRIACAO'] = pd.to_datetime(df_het_hom['DATA_CRIACAO'], format='%Y%m%d', errors='coerce').dt.strftime('%d/%m/%Y')
            df_het_hom['DATA_MOVIMENTO'] = pd.to_datetime(df_het_hom['DATA_MOVIMENTO'], format='%Y%m%d', errors='coerce').dt.strftime('%d/%m/%Y')
            df_het_hom['HORA_EXCLUSAO'] = df_het_hom['HORA_EXCLUSAO'].astype(str).str.zfill(6).apply(lambda x: f"{x[:2]}:{x[2:4]}:{x[4:]}")
            
            # Converter pesos para toneladas
            df_het_hom['PESO_PRODUTO_TON'] = (df_het_hom['PESO_PRODUTO'] / 1000).round(4)
            df_het_hom['PESO_LIGADO_TON'] = (df_het_hom['PESO_LIGADO'] / 1000).round(4)
            df_het_hom['PESO_TOTAL_TON'] = (df_het_hom['PESO_TOTAL'] / 1000).round(4)
            
            # Reordenar colunas
            cols = ['DATA_CRIACAO', 'DATA_MOVIMENTO', 'HORA_EXCLUSAO', 'REFLIV', 'VIAGEM', 'PALETE',
                    'NUMERO_VIAGEM', 'TIPO', 'CLASSIFICACAO', 'PESO_PRODUTO', 'PESO_LIGADO', 'PESO_TOTAL',
                    'PESO_PRODUTO_TON', 'PESO_LIGADO_TON', 'PESO_TOTAL_TON']
            df_het_hom = df_het_hom[cols]
        
        # Criar arquivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if not df_pedido_x7.empty:
                df_pedido_x7.to_excel(writer, index=False, sheet_name='PEDIDO_X7')
            else:
                pd.DataFrame({'Mensagem': ['Nenhum dado encontrado no período']}).to_excel(writer, index=False, sheet_name='PEDIDO_X7')
            
            if not df_het_hom.empty:
                df_het_hom.to_excel(writer, index=False, sheet_name='Volume_HET_e_HOM_Consolidado')
            else:
                pd.DataFrame({'Mensagem': ['Nenhum dado encontrado no período']}).to_excel(writer, index=False, sheet_name='Volume_HET_e_HOM_Consolidado')
            
            # Ajustar largura das colunas e adicionar filtros
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                if sheet_name == 'PEDIDO_X7' and not df_pedido_x7.empty:
                    df_ref = df_pedido_x7
                elif sheet_name == 'Volume_HET_e_HOM_Consolidado' and not df_het_hom.empty:
                    df_ref = df_het_hom
                else:
                    continue
                
                # Ajustar largura das colunas
                for idx, col in enumerate(df_ref.columns):
                    max_length = max(df_ref[col].astype(str).apply(len).max(), len(col)) + 2
                    worksheet.column_dimensions[chr(65 + idx) if idx < 26 else f"{chr(65 + idx // 26 - 1)}{chr(65 + idx % 26)}"].width = min(max_length, 50)
                
                # Adicionar AutoFilter na primeira linha (cabeçalho)
                worksheet.auto_filter.ref = worksheet.dimensions
        
        output.seek(0)
        filename = f"dashboard_{data_inicial}_a_{data_final}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except pyodbc.Error as db_error:
        error_msg = f"Erro de banco de dados: {str(db_error)}"
        return jsonify({"success": False, "error": error_msg}), 500
    except Exception as e:
        error_msg = f"Erro ao exportar dashboard Excel: {str(e)}"
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": error_msg}), 500

@api_bp.route('/api/het-pendentes', methods=['POST'])
def get_het_pendentes():
    """Retorna lista detalhada de itens HET pendentes"""
    try:
        data = request.get_json()
        data_inicial = data.get('data_inicial')
        data_final = data.get('data_final')
        
        if not data_inicial or not data_final:
            return jsonify({"error": "data_inicial e data_final são obrigatórios"}), 400
        
        if len(data_inicial) != 8 or len(data_final) != 8:
            return jsonify({"error": "Datas devem estar no formato AAAAMMDD"}), 400
        
        from datetime import datetime, timedelta
        
        conn = get_db_connection()
        
        # Converter para formato YYYY-MM-DD
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
            conn.close()
            return jsonify({
                "success": True,
                "total": 0,
                "total_toneladas": 0,
                "dados": []
            })
        
        # Processar GELIVE
        df_gelive_het['REFLIV'] = df_gelive_het['REFLIV'].astype(str).str.split('.').str[0].str.strip()
        df_gelive_het['VIAGEM'] = df_gelive_het['REFLIV'].str[4:-2].str.extract(r'(\d+)')[0].fillna(0).astype(int)
        
        viagens_het = df_gelive_het['VIAGEM'].unique().tolist()
        
        if len(viagens_het) == 0:
            conn.close()
            return jsonify({
                "success": True,
                "total": 0,
                "total_toneladas": 0,
                "dados": []
            })
        
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
        conn.close()
        
        if df_ondaitm_het.empty:
            return jsonify({
                "success": True,
                "total": 0,
                "total_toneladas": 0,
                "dados": []
            })
        
        # Verificar status e filtrar apenas incompletos
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
        
        # Filtrar apenas pendentes (incompletos)
        df_pendentes = df_ondaitm_het[df_ondaitm_het['STATUS_PREPARACAO'] == 'INCOMPLETO'].copy()
        
        if df_pendentes.empty:
            return jsonify({
                "success": True,
                "total": 0,
                "total_toneladas": 0,
                "dados": []
            })
        
        # Preparar dados para retorno
        lista_pendentes = []
        for _, row in df_pendentes.iterrows():
            try:
                rcaixas = float(str(row['RCAIXAS']).replace(',', '.'))
                qtdlida = float(str(row['QTDLIDA']).replace(',', '.'))
                peso = float(row['PESO']) / 1000  # Converter para toneladas
                percentual = (qtdlida / rcaixas * 100) if rcaixas > 0 else 0
                
                lista_pendentes.append({
                    'viagem': str(row['VIAGEM']),
                    'palete': str(row['PALETE']),
                    'esperado': int(rcaixas),
                    'lido': int(qtdlida),
                    'percentual': round(percentual, 1),
                    'peso': round(peso, 4),
                    'preparador': str(row['PREP']) if pd.notna(row['PREP']) else ''
                })
            except Exception as e:
                print(f"Erro ao processar linha: {e}")
                continue
        
        total_toneladas = df_pendentes['PESO'].sum() / 1000
        
        return jsonify({
            "success": True,
            "total": len(lista_pendentes),
            "total_toneladas": round(total_toneladas, 4),
            "dados": lista_pendentes
        })
        
    except Exception as e:
        error_msg = f"Erro ao buscar HET pendentes: {str(e)}"
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": error_msg}), 500

@api_bp.route('/api/peso-pendente-extracao', methods=['POST'])
def get_peso_pendente_extracao():
    """Retorna viagens do GELIVE que não foram lançadas para preparar (sem dados na ONDAITM)"""
    try:
        data = request.get_json()
        data_inicial = data.get('data_inicial')
        data_final = data.get('data_final')
        
        if not data_inicial or not data_final:
            return jsonify({"error": "data_inicial e data_final são obrigatórios"}), 400
        
        if len(data_inicial) != 8 or len(data_final) != 8:
            return jsonify({"error": "Datas devem estar no formato AAAAMMDD"}), 400
        
        from datetime import datetime, timedelta
        
        conn = get_db_connection()
        
        # Converter para formato YYYY-MM-DD
        data_inicial_fmt = f"{data_inicial[:4]}-{data_inicial[4:6]}-{data_inicial[6:]}"
        data_final_fmt = f"{data_final[:4]}-{data_final[4:6]}-{data_final[6:]}"
        
        data_inicial_dt = datetime.strptime(data_inicial_fmt, "%Y-%m-%d")
        data_final_dt = datetime.strptime(data_final_fmt, "%Y-%m-%d")
        
        # Range amplo (±2 dias)
        data_ondaitm_inicial = (data_inicial_dt - timedelta(days=2)).strftime('%Y-%m-%d')
        data_ondaitm_final = (data_final_dt + timedelta(days=2)).strftime('%Y-%m-%d')
        
        # Query GELIVE para HET - usar mesma abordagem dos outros endpoints
        query_gelive = f"""
        SELECT *
        FROM FGE5006CDP.GELIVE
        WHERE MAJCRE >= '{data_inicial}'
            AND MAJCRE <= '{data_final}'
            AND (HEUEXC >= 140000 OR HEUEXC <= 010000)
            AND (REFLIV LIKE '2414%' OR REFLIV LIKE '2401%')
            AND CODTLI = 'STD'
        """
        
        df_gelive = pd.read_sql(query_gelive, conn)
        
        if df_gelive.empty:
            conn.close()
            return jsonify({
                "success": True,
                "total": 0,
                "total_toneladas": 0,
                "dados": []
            })
        
        # Processar GELIVE e extrair viagem
        df_gelive['REFLIV'] = df_gelive['REFLIV'].astype(str).str.split('.').str[0].str.strip()
        df_gelive['VIAGEM'] = df_gelive['REFLIV'].str[4:-2].str.extract(r'(\d+)')[0].fillna(0).astype(int)
        df_gelive = df_gelive[df_gelive['VIAGEM'] > 0]
        
        # Converter POICVU para numérico e filtrar > 0
        df_gelive['POICVU'] = pd.to_numeric(df_gelive['POICVU'], errors='coerce').fillna(0)
        df_gelive = df_gelive[df_gelive['POICVU'] > 0]
        
        if df_gelive.empty:
            conn.close()
            return jsonify({
                "success": True,
                "total": 0,
                "total_toneladas": 0,
                "dados": []
            })
        
        # Agrupar por viagem e somar peso
        df_viagens = df_gelive.groupby('VIAGEM', as_index=False).agg({
            'POICVU': 'sum',
            'MAJCRE': 'first'
        })
        
        print(f"DEBUG - Exemplo de POICVU: {df_viagens[['VIAGEM', 'POICVU']].head()}")
        
        viagens_gelive = df_viagens['VIAGEM'].unique().tolist()
        
        if len(viagens_gelive) == 0:
            conn.close()
            return jsonify({
                "success": True,
                "total": 0,
                "total_toneladas": 0,
                "dados": []
            })
        
        # Query ONDAITM - buscar TODAS as viagens sem filtro IN para evitar erro de conversão
        query_ondaitm = f"""
        SELECT DISTINCT VIAGEM
        FROM DANALLCDP.ONDAITM
        WHERE VIAGEM IS NOT NULL
        """
        
        cursor = conn.cursor()
        cursor.execute(query_ondaitm)
        rows = cursor.fetchall()
        
        # Converter viagens para int, ignorando valores inválidos
        viagens_ondaitm = []
        for row in rows:
            try:
                if row[0] is not None:
                    viagem_int = int(row[0])
                    viagens_ondaitm.append(viagem_int)
            except (ValueError, TypeError):
                # Ignorar valores que não são números
                continue
        
        cursor.close()
        conn.close()
        
        print(f"DEBUG - Viagens no GELIVE: {viagens_gelive}")
        print(f"DEBUG - Total viagens na ONDAITM: {len(viagens_ondaitm)}")
        
        # Filtrar viagens que NÃO estão na ONDAITM (não foram lançadas para preparar)
        df_nao_lancadas = df_viagens[~df_viagens['VIAGEM'].isin(viagens_ondaitm)].copy()
        
        if df_nao_lancadas.empty:
            return jsonify({
                "success": True,
                "total": 0,
                "total_toneladas": 0,
                "dados": []
            })
        
        # Preparar dados para retorno
        lista_nao_lancadas = []
        
        for _, row in df_nao_lancadas.iterrows():
            try:
                peso_ton = float(row['POICVU']) if pd.notna(row['POICVU']) else 0  # POICVU já está em toneladas
                data_criacao = str(int(row['MAJCRE'])) if pd.notna(row['MAJCRE']) else ''
                
                if peso_ton > 0:  # Só incluir se tiver peso
                    lista_nao_lancadas.append({
                        'viagem': str(row['VIAGEM']),
                        'peso': round(peso_ton, 4),
                        'data_criacao': data_criacao
                    })
            except Exception as e:
                print(f"Erro ao processar linha: {e}")
                continue
        
        # Calcular total em toneladas (POICVU já está em toneladas)
        total_toneladas = df_nao_lancadas['POICVU'].sum()
        
        return jsonify({
            "success": True,
            "total": len(lista_nao_lancadas),
            "total_toneladas": round(total_toneladas, 4),
            "dados": lista_nao_lancadas
        })
        
    except Exception as e:
        error_msg = f"Erro ao buscar peso pendente de extração: {str(e)}"
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": error_msg}), 500

@api_bp.route('/api/hom-pendentes', methods=['POST'])
def get_hom_pendentes():
    """Retorna lista detalhada de itens HOM pendentes"""
    try:
        data = request.get_json()
        data_inicial = data.get('data_inicial')
        data_final = data.get('data_final')
        
        if not data_inicial or not data_final:
            return jsonify({"error": "data_inicial e data_final são obrigatórios"}), 400
        
        if len(data_inicial) != 8 or len(data_final) != 8:
            return jsonify({"error": "Datas devem estar no formato AAAAMMDD"}), 400
        
        from datetime import datetime, timedelta
        
        conn = get_db_connection()
        
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
            conn.close()
            return jsonify({
                "success": True,
                "total": 0,
                "total_toneladas": 0,
                "dados": []
            })
        
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
            conn.close()
            return jsonify({
                "success": True,
                "total": 0,
                "total_toneladas": 0,
                "dados": []
            })
        
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
        
        # Filtrar apenas STD e PENDENTES
        df_gesupe_hom = df_gesupe_final[
            (df_gesupe_final['CODTLI'] == 'STD') & 
            (df_gesupe_final['STATUS'] == 'PENDENTE')
        ].copy()
        
        if df_gesupe_hom.empty:
            conn.close()
            return jsonify({
                "success": True,
                "total": 0,
                "total_toneladas": 0,
                "dados": []
            })
        
        # Query ONDAITM para pegar pesos e paletes
        query_ondaitm_hom = f"""
        SELECT NUMSUP, PESO, VIAGEM, PALETE
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
        conn.close()
        
        if df_ondaitm_hom.empty:
            return jsonify({
                "success": True,
                "total": 0,
                "total_toneladas": 0,
                "dados": []
            })
        
        # Agrupar por NUMSUP, VIAGEM e PALETE para pegar informações únicas
        df_ondaitm_agrupado = df_ondaitm_hom.groupby(['NUMSUP', 'VIAGEM', 'PALETE']).agg({
            'PESO': 'first'
        }).reset_index()
        
        # Merge para trazer pesos e paletes
        df_merge_hom = pd.merge(df_gesupe_hom, df_ondaitm_agrupado, on='NUMSUP', how='left')
        df_com_peso_hom = df_merge_hom[df_merge_hom['PESO'].notna()]
        
        # Preparar dados para retorno - agrupar por viagem e palete
        lista_pendentes = []
        viagens_paletes = {}
        
        for _, row in df_com_peso_hom.iterrows():
            try:
                viagem = str(row['VIAGEM_y']) if pd.notna(row.get('VIAGEM_y')) else str(row['VIAGEM_x'])
                palete = str(row['PALETE']) if pd.notna(row.get('PALETE')) else 'N/A'
                peso = float(row['PESO']) / 1000  # Converter para toneladas
                
                # Criar chave única viagem-palete
                chave = f"{viagem}-{palete}"
                
                if chave not in viagens_paletes:
                    viagens_paletes[chave] = {
                        'viagem': viagem,
                        'palete': palete,
                        'numsup': str(row['NUMSUP']),
                        'peso': round(peso, 4),
                        'data_criacao': str(row['MAJCRE'])
                    }
                
            except Exception as e:
                print(f"Erro ao processar linha: {e}")
                continue
        
        lista_pendentes = list(viagens_paletes.values())
        total_toneladas = df_com_peso_hom['PESO'].sum() / 1000
        
        return jsonify({
            "success": True,
            "total": len(lista_pendentes),
            "total_toneladas": round(total_toneladas, 4),
            "dados": lista_pendentes
        })
        
    except Exception as e:
        error_msg = f"Erro ao buscar HOM pendentes: {str(e)}"
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": error_msg}), 500
