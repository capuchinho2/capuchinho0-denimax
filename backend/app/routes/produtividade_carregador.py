from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
import pyodbc
import pandas as pd
import sqlite3
import os

produtividade_carregador_bp = Blueprint('produtividade_carregador', __name__)

@produtividade_carregador_bp.route('/produtividade-carregador')
def produtividade_carregador():
    return render_template('produtividade_carregador.html')

@produtividade_carregador_bp.route('/api/produtividade-carregador/dados', methods=['GET'])
def api_produtividade_carregador():
    """
    Endpoint para obter dados de produtividade dos carregadores
    Parâmetros opcionais:
    - data_inicio: Data inicial (formato YYYY-MM-DD)
    - data_fim: Data final (formato YYYY-MM-DD)
    """
    try:
        # Obter parâmetros da requisição
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Se não fornecido, usar últimos 7 dias
        if not data_inicio:
            data_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = datetime.now().strftime('%Y-%m-%d')
        
        # Conexão com o banco
        conn_str = (
            "DRIVER={iSeries Access ODBC Driver};"
            "SYSTEM=FGE5006CDP;"
            "UID=CDP174176G;"
            "PWD=CDP1753;"
        )
        conn = pyodbc.connect(conn_str)
        
        # Query para obter dados da ONDADET
        query_ondadet = f"""
        SELECT VIAGEM, PALETE, DATA, MIS_OPER, MIS_DONE 
        FROM DANALLCDP.ONDADET
        WHERE DATA >= '{data_inicio}' AND DATA <= '{data_fim}'
        """
        
        # Executar query
        df_ondadet = pd.read_sql(query_ondadet, conn)
        conn.close()
        
        if df_ondadet.empty:
            return jsonify({
                "success": True, 
                "mensagem": "Nenhum dado encontrado para o período selecionado",
                "total_paletes": 0,
                "total_operadores": 0,
                "produtividade": []
            })
        
        # Análise de produtividade por operador
        df_bipados = df_ondadet[df_ondadet['MIS_DONE'] == 'Y']
        
        if df_bipados.empty:
            return jsonify({
                "success": True,
                "mensagem": "Nenhum palete bipado encontrado para o período selecionado",
                "total_paletes": 0,
                "total_operadores": 0,
                "produtividade": []
            })
        
        # Agrupar por operador
        produtividade = df_bipados.groupby('MIS_OPER').size().reset_index(name='PALETES_BIPADOS')
        produtividade = produtividade.sort_values('PALETES_BIPADOS', ascending=False)
        
        # Buscar nomes e turnos no banco colaboradores
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'colaboradores.db')
        conn_sqlite = sqlite3.connect(db_path)
        cursor = conn_sqlite.cursor()
        
        # Adicionar NOME e TURNO
        dados_produtividade = []
        for _, row in produtividade.iterrows():
            matricula = str(row['MIS_OPER']).strip()
            cursor.execute('SELECT NOME, TURNO FROM colaboradores WHERE MATRICULA = ?', (matricula,))
            resultado = cursor.fetchone()
            
            dados_produtividade.append({
                'MIS_OPER': row['MIS_OPER'],
                'NOME': resultado[0] if resultado else 'N/A',
                'TURNO': resultado[1] if resultado else 'N/A',
                'PALETES_BIPADOS': int(row['PALETES_BIPADOS'])
            })
        
        conn_sqlite.close()
        
        # Estatísticas gerais
        total_paletes = int(produtividade['PALETES_BIPADOS'].sum())
        total_operadores = len(produtividade)
        media_paletes = round(total_paletes / total_operadores, 2) if total_operadores > 0 else 0
        
        return jsonify({
            "success": True,
            "total_paletes": total_paletes,
            "total_operadores": total_operadores,
            "media_paletes": media_paletes,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "produtividade": dados_produtividade
        })
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": str(e),
            "total_paletes": 0,
            "total_operadores": 0,
            "produtividade": []
        }), 500
