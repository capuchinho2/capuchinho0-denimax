"""
Rotas para Produtividade de Preparadores
Baseado na lógica de produtividade_dia.py
"""
from flask import Blueprint, render_template, jsonify, request
import pyodbc
import sqlite3
from datetime import datetime
import pandas as pd
import os

produtividade_preparador_bp = Blueprint('produtividade_preparador', __name__)

@produtividade_preparador_bp.route('/produtividade-preparador')
def produtividade_preparador():
    """Renderiza a página de produtividade de preparadores"""
    return render_template('produtividade_preparador.html')

@produtividade_preparador_bp.route('/api/produtividade-preparador/dados')
def get_dados_preparador():
    """
    Retorna dados de produtividade dos preparadores por período
    Query baseada em produtividade_dia.py
    """
    try:
        # Pega parâmetros de data
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        if not data_inicio or not data_fim:
            return jsonify({'error': 'Parâmetros data_inicio e data_fim são obrigatórios'}), 400
        
        # Converte para formato timestamp
        dhini = f"{data_inicio} 00:00:00"
        dhfim = f"{data_fim} 23:59:59"
        
        # String de conexão
        conn_str = (
            "DRIVER={iSeries Access ODBC Driver};"
            "SYSTEM=FGE5006CDP;"
            "UID=CDP174176G;"
            "PWD=CDP1753;"
        )
        
        # Query de produtividade dos preparadores - SEM nome, só código
        sql_produtividade = f"""
        SELECT PREPARADOR, SUM(CAIXAS) AS CAIXAS, CAST(SUM(PESO) AS DECIMAL(16,3)) AS PESO, COUNT(GUIA) AS GUIAS
        FROM (
            SELECT 
                O.PREP AS PREPARADOR, 
                SUM(QTDLIDA) AS CAIXAS, 
                FLOAT(SUM(PESO/1000)) AS PESO,
                VIAGEM||PALETE AS GUIA
            FROM 
                DANALLCDP.ONDAITM AS O
            WHERE 
                DATA BETWEEN '{dhini}' AND '{dhfim}' 
                AND CODTLI!='HOM'
                AND O.PREP IS NOT NULL
                AND TRIM(O.PREP) != ''
            GROUP BY 
                O.PREP, VIAGEM||PALETE
        )
        GROUP BY PREPARADOR
        ORDER BY PESO DESC
        """
        
        # Conecta e executa query
        conn = pyodbc.connect(conn_str)
        df = pd.read_sql(sql_produtividade, conn)
        conn.close()
        
        # Buscar banco SQLite local para pegar NOME e TURNO
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'preparador.db')
        
        if not os.path.exists(db_path):
            return jsonify({'error': f'Banco preparador.db não encontrado em {db_path}. Execute criar_banco_preparador.py'}), 500
        
        conn_sqlite = sqlite3.connect(db_path)
        cursor = conn_sqlite.cursor()
        
        # Adicionar NOME e TURNO
        preparadores = []
        for _, row in df.iterrows():
            codprp = str(row['PREPARADOR']).strip()
            cursor.execute('SELECT NOME, TURNO FROM preparadores WHERE CODPRP = ?', (codprp,))
            resultado = cursor.fetchone()
            
            preparadores.append({
                'PREPARADOR': codprp,
                'NOME': resultado[0] if resultado else 'N/A',
                'TURNO': resultado[1] if resultado else 'N/A',
                'CAIXAS': int(row['CAIXAS']),
                'PESO': float(row['PESO']),
                'GUIAS': int(row['GUIAS'])
            })
        
        conn_sqlite.close()
        
        conn_sqlite.close()
        
        # Calcula estatísticas
        total_preparadores = len(preparadores)
        total_caixas = sum(p['CAIXAS'] for p in preparadores)
        total_peso = sum(p['PESO'] for p in preparadores)
        total_guias = sum(p['GUIAS'] for p in preparadores)
        
        return jsonify({
            'preparadores': preparadores,
            'total_preparadores': total_preparadores,
            'total_caixas': total_caixas,
            'total_peso': total_peso,
            'total_guias': total_guias
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
