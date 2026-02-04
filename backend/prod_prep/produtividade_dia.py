"""
Produtividade por Período - Preparadores
Replica funcionalidade de produtividade_dia.php
"""

from datetime import datetime
from db_connection import DB2Connection, MySQLConnection
from config import DB2_CONFIG, MYSQL_CONFIG
from utils import left_join_arrays, calc_subtraction, calc_percentage, print_table


def get_produtividade_periodo(data_inicio: str, data_fim: str):
    """
    Busca produtividade dos preparadores por período
    
    Args:
        data_inicio: Data inicial formato YYYY-MM-DD
        data_fim: Data final formato YYYY-MM-DD
    """
    print(f"\n🔍 Buscando produtividade de {data_inicio} até {data_fim}")
    
    # Converte datas para formato timestamp
    dhini = f"{data_inicio} 00:00:00"
    dhfim = f"{data_fim} 23:59:59"
    
    # Query principal - Produtividade dos preparadores
    sql_produtividade = f"""
    SELECT PREPARADOR, NOME, SUM(CAIXAS) AS CAIXAS, CAST(SUM(PESO) AS DECIMAL(16,3)) AS PESO, COUNT(GUIA) AS GUIAS
    FROM (
        SELECT 
            O.PREP AS PREPARADOR, 
            G.NOMPRP AS NOME, 
            SUM(QTDLIDA) AS CAIXAS, 
            FLOAT(SUM(PESO/1000)) AS PESO,
            VIAGEM||PALETE AS GUIA
        FROM 
            DANALLCDP.ONDAITM AS O
        LEFT JOIN 
            FGE5006CDP.GEZPRP AS G 
        ON 
            G.CODPRP=O.PREP
        WHERE 
            DATA BETWEEN '{dhini}' AND '{dhfim}' 
            AND CODTLI!='HOM'
        GROUP BY 
            O.PREP, G.NOMPRP, VIAGEM||PALETE
    )
    GROUP BY PREPARADOR, NOME
    ORDER BY PESO DESC
    """
    
    # Conecta DB2 e executa query de produtividade
    print("\n📊 Executando query de produtividade...")
    db2 = DB2Connection(**DB2_CONFIG)
    db2.connect()
    arr_produtividade = db2.execute_query(sql_produtividade)
    db2.close()
    
    # Calcula percentual para gráfico
    print("\n📈 Calculando percentuais...")
    arr_final = calc_percentage(arr_produtividade, 'PESO', 'GRAFICO')
    
    # Exibe resultados
    print_table(arr_final, f"PRODUTIVIDADE POR PERÍODO - {data_inicio} a {data_fim}")
    
    return arr_final


if __name__ == "__main__":
    # Teste com data de hoje
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    # Pode alterar as datas aqui
    data_inicio = "2026-01-01"
    data_fim = hoje
    
    resultado = get_produtividade_periodo(data_inicio, data_fim)
    
    print(f"\n✅ Processamento concluído!")
