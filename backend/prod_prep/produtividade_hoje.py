"""
Produtividade Hoje - Preparadores
Replica funcionalidade de produtividade_hoje.php
"""

import argparse
from datetime import datetime, timedelta
from db_connection import DB2Connection, MySQLConnection
from config import DB2_CONFIG, MYSQL_CONFIG
from utils import left_join_arrays, calc_subtraction, calc_percentage, print_table


def get_produtividade_hoje(data: str = None):
    """
    Busca produtividade dos preparadores de um dia específico
    
    Args:
        data: Data no formato YYYY-MM-DD (opcional, default = hoje)
    """
    # Se não passou data, usa hoje
    if not data:
        data_inicio = datetime.now().strftime("%Y-%m-%d")
    else:
        data_inicio = data
    
    data_fim = (datetime.strptime(data_inicio, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"\n🔍 Buscando produtividade de HOJE: {data_inicio}")
    
    # Query principal - Produtividade do dia
    sql_produtividade = f"""
    SELECT PRODUTIVIDADE.PREP AS PREPARADOR, NOMPRP AS DES,
    SUM(PRODUTIVIDADE.QTD_USADA) AS QTD_USADA, SUM(PRODUTIVIDADE.QTD_TOTAL2) AS QTD_TOTAL,
    SUM(PRODUTIVIDADE.PESO) AS PESO, COUNT(PRODUTIVIDADE.PESO) AS GUIAS
    FROM(
        SELECT FUNC.PREP, PRODUCAO.QTD_USADA, PRODUCAO.QTD_TOTAL, FUNC.QTD_TOTAL2, PRODUCAO.PESO
        FROM(
            SELECT SUM(RASTLOG.QTD_USADA) AS QTD_USADA, SUM(RASTLOG.QTD_TOTAL) AS QTD_TOTAL, 
            RASTLOG.VIAGEM||RASTLOG.PALETE AS CHAVE, 
            SUM(RASTLOG.QTD_USADA*GEPRO.PDBCOL) AS PESO
            FROM DANALLCDP.RASTLOG AS RASTLOG
            LEFT JOIN FGE5006CDP.GEPRO AS GEPRO 
            ON REPEAT('0',17-CHAR_LENGTH(RASTLOG.CODPRO))||RASTLOG.CODPRO=GEPRO.CODPRO
            WHERE DATAHORA BETWEEN '{data_inicio} 00:00:00' AND '{data_fim} 23:59:59'
            GROUP BY RASTLOG.VIAGEM||RASTLOG.PALETE
        ) AS PRODUCAO
        LEFT OUTER JOIN (
            SELECT SUM(DANALLCDP.ONDAITM.RCAIXAS) AS QTD_TOTAL2, DANALLCDP.ONDAITM.PREP,
            DANALLCDP.ONDAITM.VIAGEM||DANALLCDP.ONDAITM.PALETE AS CHAVE
            FROM DANALLCDP.ONDAITM
            GROUP BY DANALLCDP.ONDAITM.PREP, DANALLCDP.ONDAITM.VIAGEM||DANALLCDP.ONDAITM.PALETE
        ) AS FUNC ON FUNC.CHAVE=PRODUCAO.CHAVE
    ) AS PRODUTIVIDADE
    LEFT JOIN FGE5006CDP.GEZPRP AS GEZPRP ON PRODUTIVIDADE.PREP=GEZPRP.CODPRP
    GROUP BY PRODUTIVIDADE.PREP, NOMPRP
    ORDER BY SUM(PRODUTIVIDADE.PESO) DESC
    """
    
    # Conecta DB2 e executa query de produtividade
    print("\n📊 Executando query de produtividade...")
    db2 = DB2Connection(**DB2_CONFIG)
    db2.connect()
    arr_produtividade = db2.execute_query(sql_produtividade)
    db2.close()
    
    # Converte PESO de gramas para toneladas
    print("\n🧮 Calculando peso em toneladas...")
    for item in arr_produtividade:
        item['PESO_TON'] = round(float(item.get('PESO', 0) or 0) / 1000, 3)
    
    # Calcula percentual para gráfico
    print("\n📈 Calculando percentuais...")
    arr_final = calc_percentage(arr_produtividade, 'PESO_TON', 'GRAFICO')
    
    # Exibe resultados
    print_table(arr_final, f"PRODUTIVIDADE HOJE - {data_inicio}")
    
    return arr_final


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Produtividade dos Preparadores')
    parser.add_argument(
        '--data', 
        type=str, 
        help='Data para consulta no formato YYYY-MM-DD (ex: 2026-01-18). Se não informado, usa hoje.'
    )
    
    args = parser.parse_args()
    
    # Valida data se foi informada
    if args.data:
        try:
            datetime.strptime(args.data, "%Y-%m-%d")
        except ValueError:
            print("❌ Erro: Data deve estar no formato YYYY-MM-DD (ex: 2026-01-18)")
            exit(1)
    
    resultado = get_produtividade_hoje(args.data)
    print(f"\n✅ Processamento concluído!")
