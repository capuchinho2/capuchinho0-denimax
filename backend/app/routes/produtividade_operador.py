from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
import pyodbc
import pandas as pd
import sqlite3
import os

produtividade_operador_bp = Blueprint('produtividade_operador', __name__)

@produtividade_operador_bp.route('/produtividade-operador')
def produtividade_operador():
    return render_template('produtividade_operador.html')

@produtividade_operador_bp.route('/api/produtividade-operador/dados', methods=['GET'])
def api_produtividade_operador():
    """
    Endpoint para obter dados de produtividade dos operadores
    Parâmetros:
    - data_inicio: Data inicial (formato YYYY-MM-DD)
    - data_fim: Data final (formato YYYY-MM-DD)
    """
    try:
        # Obter parâmetros da requisição
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        if not data_inicio or not data_fim:
            return jsonify({
                "success": False,
                "error": "Datas de início e fim são obrigatórias"
            }), 400
        
        # Converter para formato YYYYMMDD para a query do AS400
        try:
            inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            fim = datetime.strptime(data_fim, "%Y-%m-%d")
            
            if inicio > fim:
                return jsonify({
                    "success": False,
                    "error": "Data inicial maior que a final"
                }), 400
            
            # Gerar lista de datas no formato YYYYMMDD
            datas = [(inicio + timedelta(days=i)).strftime("%Y%m%d") 
                    for i in range((fim - inicio).days + 1)]
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Formato de data inválido. Use YYYY-MM-DD"
            }), 400
        
        # Buscar operadores cadastrados no banco operador.db (para pegar os nomes)
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'operador.db')
        dict_operadores = {}
        
        if os.path.exists(db_path):
            conn_sqlite = sqlite3.connect(db_path)
            cursor = conn_sqlite.cursor()
            cursor.execute('SELECT MATRICULA, NOME, TURNO FROM operadores ORDER BY NOME')
            operadores = cursor.fetchall()
            conn_sqlite.close()
            
            # Criar dicionário para facilitar busca de nomes
            dict_operadores = {str(col[0]).strip(): {"nome": col[1], "turno": col[2] or "N/A"} 
                              for col in operadores}
        
        # Conectar ao AS400
        conn_str = (
            "DRIVER={iSeries Access ODBC Driver};"
            "SYSTEM=FGE5006CDP;"
            "UID=CDP174176G;"
            "PWD=CDP1753;"
        )
        conn = pyodbc.connect(conn_str)
        dados_brutos = []
        
        # Buscar TODOS os dados do período (sem filtrar por matrícula específica)
        for data in datas:
            query = f"""
            SELECT CODCAR AS MATRICULA, {data} AS DATA, RECMVT, LIVSUP, LIVPIC
            FROM FGE5006CDP.GEHCAR
            WHERE DATHIS = {data}
            """
            df = pd.read_sql(query, conn)
            if not df.empty:
                dados_brutos.append(df)
        
        conn.close()
        
        if not dados_brutos:
            return jsonify({
                "success": True,
                "mensagem": "Nenhum dado encontrado para as datas informadas",
                "total_operadores": 0,
                "dados": []
            })
        
        # Consolidar dados
        df_brutos = pd.concat(dados_brutos, ignore_index=True)
        df_resumo = df_brutos.groupby("MATRICULA")[["RECMVT", "LIVSUP", "LIVPIC"]].sum().reset_index()
        df_resumo["TOTAL"] = df_resumo[["RECMVT", "LIVSUP", "LIVPIC"]].sum(axis=1)
        
        # Adicionar nomes e turnos
        resultado = []
        for _, row in df_resumo.iterrows():
            matricula = str(row['MATRICULA']).strip()
            info_operador = dict_operadores.get(matricula, {"nome": "N/A", "turno": "N/A"})
            
            resultado.append({
                'MATRICULA': matricula,
                'NOME': info_operador['nome'],
                'TURNO': info_operador['turno'],
                'RECMVT': int(row['RECMVT']),
                'LIVSUP': int(row['LIVSUP']),
                'LIVPIC': int(row['LIVPIC']),
                'TOTAL': int(row['TOTAL'])
            })
        
        # Ordenar por total decrescente
        resultado = sorted(resultado, key=lambda x: x['TOTAL'], reverse=True)
        
        return jsonify({
            "success": True,
            "total_operadores": len(resultado),
            "periodo": f"{datas[0]} a {datas[-1]}" if len(datas) > 1 else datas[0],
            "dados": resultado
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
