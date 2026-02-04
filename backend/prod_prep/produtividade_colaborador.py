"""
Produtividade por Colaborador - Preparadores
Replica funcionalidade de produtividade_colaborador.php
"""

from datetime import datetime
from db_connection import DB2Connection, MySQLConnection
from config import DB2_CONFIG, MYSQL_CONFIG
from utils import left_join_arrays, calc_subtraction, calc_percentage, print_table


def get_produtividade_colaborador(data_inicio: str, data_fim: str, cod_preparador: str):
    """
    Busca produtividade de um colaborador específico por período
    
    Args:
        data_inicio: Data inicial formato YYYY-MM-DD
        data_fim: Data final formato YYYY-MM-DD
        cod_preparador: Código do preparador
    """
    print(f"\n🔍 Buscando produtividade do preparador {cod_preparador}")
    print(f"📅 Período: {data_inicio} até {data_fim}")
    
    # Query principal - Produtividade por dia
    sql_produtividade = f"""
    SELECT PRODUTIVIDADE.DATA, PRODUTIVIDADE.PREP AS PREPARADOR, FINVUSR.DES,
    SUM(PRODUTIVIDADE.QTD_USADA) AS QTD_USADA, SUM(PRODUTIVIDADE.QTD_TOTAL) AS QTD_TOTAL, 
    COUNT(PRODUTIVIDADE.PESO) AS GUIAS,
    SUM(PRODUTIVIDADE.PESO)/1000 AS TONS
    FROM(
        SELECT SUM(DANALLCDP.RASTLOG.QTD_USADA) AS QTD_USADA, 
        SUM(DANALLCDP.RASTLOG.QTD_TOTAL) AS QTD_TOTAL,
        DANALLCDP.RASTLOG.VIAGEM||DANALLCDP.RASTLOG.PALETE AS CHAVE,
        SUM(DANALLCDP.RASTLOG.QTD_USADA*FGE5006CDP.GEPRO.PDBCOL) AS PESO, 
        YEAR(DANALLCDP.RASTLOG.DATAHORA)||'-'||
        REPEAT('0',2-CHAR_LENGTH(MONTH(DANALLCDP.RASTLOG.DATAHORA)))||MONTH(DANALLCDP.RASTLOG.DATAHORA)||'-'||
        REPEAT('0',2-CHAR_LENGTH(DAY(DANALLCDP.RASTLOG.DATAHORA)))||DAY(DANALLCDP.RASTLOG.DATAHORA) AS DATA, 
        DANALLCDP.RASTLOG.USUARIO AS PREP
        FROM DANALLCDP.RASTLOG
        LEFT JOIN FGE5006CDP.GEPRO ON FGE5006CDP.GEPRO.CODPRO='000000000'||DANALLCDP.RASTLOG.CODPRO
        WHERE DATAHORA BETWEEN '{data_inicio} 00:00:00' AND '{data_fim} 23:59:59'
        GROUP BY DANALLCDP.RASTLOG.VIAGEM||DANALLCDP.RASTLOG.PALETE, 
        YEAR(DANALLCDP.RASTLOG.DATAHORA)||'-'||
        REPEAT('0',2-CHAR_LENGTH(MONTH(DANALLCDP.RASTLOG.DATAHORA)))||MONTH(DANALLCDP.RASTLOG.DATAHORA)||'-'||
        REPEAT('0',2-CHAR_LENGTH(DAY(DANALLCDP.RASTLOG.DATAHORA)))||DAY(DANALLCDP.RASTLOG.DATAHORA), 
        DANALLCDP.RASTLOG.USUARIO
    ) AS PRODUTIVIDADE
    LEFT JOIN (SELECT CODPRP AS USR, NOMPRP AS DES FROM FGE5006CDP.GEZPRP) AS FINVUSR 
    ON PRODUTIVIDADE.PREP=FINVUSR.USR
    WHERE FINVUSR.USR='{cod_preparador}'
    GROUP BY PRODUTIVIDADE.PREP, FINVUSR.DES, PRODUTIVIDADE.DATA
    ORDER BY PRODUTIVIDADE.DATA ASC
    """
    
    # Conecta DB2 e executa query de produtividade
    print("\n📊 Executando query de produtividade...")
    db2 = DB2Connection(**DB2_CONFIG)
    db2.connect()
    arr_produtividade = db2.execute_query(sql_produtividade)
    db2.close()
    
    if not arr_produtividade:
        print("\n⚠️  Nenhum dado encontrado para este preparador no período!")
        return []
    
    # Calcula percentual para gráfico
    print("\n📈 Calculando percentuais...")
    arr_final = calc_percentage(arr_produtividade, 'TONS', 'GRAFICO')
    
    # Exibe resultados
    print_table(arr_final, f"PRODUTIVIDADE COLABORADOR {cod_preparador} - {data_inicio} a {data_fim}")
    
    return arr_final


def listar_preparadores():
    """Lista todos os preparadores disponíveis"""
    print("\n👥 Listando preparadores...")
    
    sql = "SELECT CODPRP, NOMPRP FROM FGE5006CDP.GEZPRP ORDER BY NOMPRP ASC"
    
    db2 = DB2Connection(**DB2_CONFIG)
    db2.connect()
    preparadores = db2.execute_query(sql)
    db2.close()
    
    print_table(preparadores, "PREPARADORES DISPONÍVEIS")
    
    return preparadores


if __name__ == "__main__":
    # Lista preparadores disponíveis
    preparadores = listar_preparadores()
    
    # Teste com um preparador (ajustar código)
    if preparadores:
        cod_prep = preparadores[0]['CODPRP']  # Pega o primeiro
        print(f"\n📌 Usando preparador: {cod_prep}")
        
        data_inicio = "2026-01-01"
        data_fim = datetime.now().strftime("%Y-%m-%d")
        
        resultado = get_produtividade_colaborador(data_inicio, data_fim, cod_prep)
        
    print(f"\n✅ Processamento concluído!")
