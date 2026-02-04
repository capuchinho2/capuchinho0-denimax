import pyodbc
import pandas as pd
import os

# Conexão
conn_str = (
    "DRIVER={iSeries Access ODBC Driver};"
    "SYSTEM=FGE5006CDP;"
    "UID=CDP174176G;"
    "PWD=CDP1753;"
)
conn = pyodbc.connect(conn_str)


query_ondadet = """
SELECT VIAGEM, PALETE, DATA, MIS_OPER, MIS_DONE 
FROM DANALLCDP.ONDADET
WHERE DATA >= '2026-01-10'
"""

print("⏳ Carregando ONDADET...")
try:
    df_ondadet = pd.read_sql(query_ondadet, conn)
    print(f"✅ ONDADET carregada: {len(df_ondadet)} linhas")
except Exception as e:
    print(f"❌ Erro ao carregar ONDADET: {e}")
    df_ondadet = pd.DataFrame()


# Verificar se há dados antes de exportar
if df_ondadet.empty:
    print("\n⚠️ Nenhum dado encontrado. Verifique as datas no banco.")
    conn.close()
    exit()

# Análise de produtividade por operador
print("\n📊 Analisando produtividade dos operadores...")
df_bipados = df_ondadet[df_ondadet['MIS_DONE'] == 'Y']
produtividade = df_bipados.groupby('MIS_OPER').size().reset_index(name='PALETES_BIPADOS')
produtividade = produtividade.sort_values('PALETES_BIPADOS', ascending=False)

print("\n🎯 Paletes bipados por operador:")
print(produtividade.to_string(index=False))
print(f"\n📦 Total de paletes bipados: {produtividade['PALETES_BIPADOS'].sum()}")
print(f"👥 Total de operadores: {len(produtividade)}")

# Exporta pro Excel com verificação
arquivo_excel = "dados_filtrados_12-07.xlsx"
print(f"\n📊 Exportando para {arquivo_excel}...")

if os.path.exists(arquivo_excel):
    try:
        os.remove(arquivo_excel)
    except PermissionError:
        print(f"❌ ERRO: Feche o arquivo '{arquivo_excel}' no Excel e tente novamente.")
        conn.close()
        exit()

with pd.ExcelWriter(arquivo_excel, engine='openpyxl') as writer:
    if not df_ondadet.empty:
        df_ondadet.to_excel(writer, sheet_name="ONDADET", index=False)
    if not produtividade.empty:
        produtividade.to_excel(writer, sheet_name="PRODUTIVIDADE", index=False)

print(f"✅ Arquivo '{arquivo_excel}' gerado com sucesso!")
conn.close()


