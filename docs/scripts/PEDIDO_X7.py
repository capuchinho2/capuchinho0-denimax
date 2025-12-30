import pyodbc
import pandas as pd
from datetime import date

# Conexão ODBC
conn_str = (
    "DRIVER={iSeries Access ODBC Driver};"
    "SYSTEM=FGE5006CDP;"
    "UID=CDP174176G;"
    "PWD=CDP1753;"
)
conn = pyodbc.connect(conn_str)

# Input da data
print("=" * 50)
print("SISTEMA DE BUSCA - GELIVE")
print("=" * 50)
print("Formato da data: AAAAMMDD (ex: 20251116)")
data_input = input("Digite a data (ou deixe vazio para hoje): ").strip()

# Usar data digitada ou data de hoje
if data_input:
    data_busca = data_input
else:
    data_busca = date.today().strftime("%Y%m%d")

# Consulta SQL já com colunas e filtros
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

# Lê do banco
df = pd.read_sql(query, conn)

# ---- Processamento Pandas (vetorizado) ----

# Limpar REFLIV (tirar casas decimais e espaços)
df['REFLIV'] = df['REFLIV'].astype(str).str.split('.').str[0].str.strip()

# VIAGEM: do 5º caractere até os dois últimos
df['VIAGEM'] = df['REFLIV'].str[4:-2].str.extract(r'(\d+)').fillna(0).astype(int)

# PALETE: dois últimos dígitos
df['PALETE'] = df['REFLIV'].str[-2:].str.extract(r'(\d+)').fillna(0).astype(int)

# Converter HEUEXC e MAJHMS para HH:MM:SS
df['HEUEXC'] = pd.to_datetime(
    df['HEUEXC'].astype(str).str.split('.').str[0].str.zfill(6),
    format='%H%M%S', errors='coerce'
).dt.strftime('%H:%M:%S')

df['MAJHMS'] = df['MAJHMS'].astype(str).str.split('.').str[0].str.zfill(6)
df['MAJHMS'] = df['MAJHMS'].str.replace(r'(\d{2})(\d{2})(\d{2})', r'\1:\2:\3', regex=True)

# Reordenar e renomear colunas
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

# Exportar para Excel
nome_arquivo = f"tabelas_GELIVE_{data_busca}.xlsx"
df.to_excel(nome_arquivo, sheet_name="GELIVE", index=False)

# Painel: total de peso
total_peso = pd.to_numeric(df['PESO_201'], errors='coerce').sum()
print(f"\nResultados encontrados: {len(df)}")
print(f"Total de Peso Somado (PESO_201): {total_peso:,.2f}")
print(f"Arquivo gerado: {nome_arquivo}\n")