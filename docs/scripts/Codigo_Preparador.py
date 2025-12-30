import pyodbc
import pandas as pd

# Solicita a data inicial e final ao usuário no formato 20250829
data_inicial = input("Digite a data inicial (AAAAMMDD): ")
data_final = input("Digite a data final (AAAAMMDD): ")

# Converte para o formato YYYY-MM-DD
def formata_data(data):
    if len(data) == 8 and data.isdigit():
        return f"{data[:4]}-{data[4:6]}-{data[6:]}"
    else:
        print("⚠️  Digite a data no formato correto: AAAAMMDD")
        exit()

data_inicial_fmt = formata_data(data_inicial)
data_final_fmt = formata_data(data_final)

# Conexão

conn_str = (
    "DRIVER={iSeries Access ODBC Driver};"
    "SYSTEM=FGE5006CDP;"
    "UID=CDP174176G;"
    "PWD=CDP1753;"
)
conn = pyodbc.connect(conn_str)

# Consulta ONDAITM com filtro de intervalo de datas (comparando como string)
query_ondaitm = f"""
SELECT NUMVAG, PALETE, PREP, VIAGEM, CODTLI, STATUS, DONE, DATA, RCAIXAS, QTDLIDA
FROM DANALLCDP.ONDAITM
WHERE DATA >= '{data_inicial_fmt} 00:00:00' AND DATA <= '{data_final_fmt} 23:59:59'
  AND (CODTLI IS NULL OR TRIM(CODTLI) = '')
"""

print("⏳ Carregando ONDAITM...")
df_ondaitm = pd.read_sql(query_ondaitm, conn)
print("✅ ONDAITM carregada:", len(df_ondaitm), "linhas")

# Diagnóstico: mostra a data mínima e máxima retornada
if 'DATA' in df_ondaitm.columns:
    try:
        datas = pd.to_datetime(df_ondaitm['DATA'], errors='coerce')
        print(f"Data mínima retornada: {datas.min()}")
        print(f"Data máxima retornada: {datas.max()}")
    except Exception as e:
        print(f"Erro ao converter datas: {e}")

# --- Processamento direto dos dados do banco ---
import os
print("⏳ Verificando status de preparação dos produtos...")

# Filtra apenas linhas onde CODTLI está vazia ou nula e remove linhas totalmente em branco
df_filtrado = df_ondaitm[(df_ondaitm['CODTLI'].isna()) | (df_ondaitm['CODTLI'].astype(str).str.strip() == '')]
df_filtrado = df_filtrado.dropna(how='all')

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
output_path = 'dados_status_final.xlsx'
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df_filtrado.to_excel(writer, sheet_name='Dados', index=False)

    # Filtra viagens pendentes (status INCOMPLETO) e salva apenas uma linha por viagem
    viagens_pendentes = df_filtrado[df_filtrado['STATUS_PREPARACAO'] == 'INCOMPLETO']
    viagens_unicas = viagens_pendentes.drop_duplicates(subset=['VIAGEM'])
    viagens_unicas.to_excel(writer, sheet_name='Viagens Pendentes', index=False)

print(f'Arquivo salvo em: {os.path.abspath(output_path)}')

# --- Processamento direto dos dados do banco ---
import os
print("⏳ Verificando status de preparação dos produtos...")

# Filtra apenas linhas onde CODTLI está vazia ou nula e remove linhas totalmente em branco
df_filtrado = df_ondaitm[(df_ondaitm['CODTLI'].isna()) | (df_ondaitm['CODTLI'].astype(str).str.strip() == '')]
df_filtrado = df_filtrado.dropna(how='all')

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
output_path = 'dados_status_final.xlsx'
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df_filtrado.to_excel(writer, sheet_name='Dados', index=False)

    # Filtra viagens pendentes (status INCOMPLETO) e salva apenas uma linha por viagem
    viagens_pendentes = df_filtrado[df_filtrado['STATUS_PREPARACAO'] == 'INCOMPLETO']
    viagens_unicas = viagens_pendentes.drop_duplicates(subset=['VIAGEM'])
    viagens_unicas.to_excel(writer, sheet_name='Viagens Pendentes', index=False)

print(f'Arquivo salvo em: {os.path.abspath(output_path)}')
