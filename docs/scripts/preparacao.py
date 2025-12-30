# Simulação da lógica do código 2 em Python
import re

# Simule os dados recebidos (POST/GET)
entrada = {
	'viagem': '2035158',  # exemplo de viagem
	# 'suporte': '1234567XX',  # descomente para simular suporte
}

# Lógica para extrair viagem
if 'viagem' in entrada and entrada['viagem']:
	viagem = entrada['viagem']
elif 'suporte' in entrada and entrada['suporte']:
	viagem = entrada['suporte'][:7]
else:
	viagem = None

ano = mes = dia = 0
if viagem and '-' in viagem:
	partes = viagem.split('-')
	if len(partes) >= 4:
		viagem, ano, mes, dia = partes[:4]

print(f"Viagem: {viagem}")

# Conexão com o banco DB2 usando pyodbc
import pyodbc

conn_str = (
	"DRIVER={iSeries Access ODBC Driver};"
	"SYSTEM=FGE5006CDP;"
	"UID=CDP174176G;"
	"PWD=CDP1753;"
)

sql = f"""
SELECT MAX(DANALLCDP.ONDAITM.NUMVAG) AS ONDA, DANALLCDP.ONDAITM.VIAGEM,
DANALLCDP.ONDAITM.PALETE||'/'||DANALLCDP.ONDAITM.TOT_PALETE AS PALETE,
(CASE DANALLCDP.ONDAITM.TYPSUP WHEN 1 THEN 'HET' ELSE 'HOM' END) AS TIPO,
(CASE DANALLCDP.ONDADET.MIS_DONE WHEN 'Y' THEN '<img src=../images/checked.JPG width=20 height=20 >'
ELSE '<img src=../images/no-checked.JPG width=20 height=20 >' END) AS C,
SUM(DANALLCDP.ONDAITM.PESO) AS PESO, SUM(DANALLCDP.ONDAITM.QTDLIDA) AS QTDLIDA, SUM(DANALLCDP.ONDAITM.RCAIXAS) AS RCAIXAS,
CAST(SUM(DANALLCDP.ONDAITM.QTDLIDA) AS FLOAT) / CAST(SUM(DANALLCDP.ONDAITM.RCAIXAS) AS FLOAT) AS PERC_PREP,
DANALLCDP.ONDADET.MIS_OPER AS CARREGADOR,
(CASE DANALLCDP.ONDAITM.PREP WHEN '          ' THEN OPERADOR.CARDES ELSE DANALLCDP.ONDAITM.PREP END) AS PREPARADOR,
(CASE DANALLCDP.ONDAITM.PREP WHEN '          ' THEN  OPERADOR.NOMUTI ELSE GEZPRP.NOMPRP END ) AS NOME
FROM DANALLCDP.ONDAITM
LEFT JOIN FGE5006CDP.GEZPRP AS GEZPRP ON GEZPRP.CODPRP= DANALLCDP.ONDAITM.PREP
LEFT JOIN DANALLCDP.ONDADET ON
DANALLCDP.ONDADET.VIAGEM||DANALLCDP.ONDADET.PALETE = DANALLCDP.ONDAITM.VIAGEM||DANALLCDP.ONDAITM.PALETE
LEFT JOIN ( SELECT FGE5006CDP.APUTI.CODUTI, FGE5006CDP.APUTI.NOMUTI, FGE5006CDP.GESUPE.NUMSUP,
FGE5006CDP.GESUPE.CARDES
FROM FGE5006CDP.GESUPE
LEFT JOIN FGE5006CDP.APUTI ON FGE5006CDP.APUTI.CODUTI=FGE5006CDP.GESUPE.CARDES
WHERE SUBSTR(FGE5006CDP.GESUPE.REFLIV,5,7)='{viagem}' ) AS OPERADOR
ON OPERADOR.NUMSUP=DANALLCDP.ONDAITM.NUMSUP
WHERE DANALLCDP.ONDAITM.VIAGEM='{viagem}'
GROUP BY DANALLCDP.ONDADET.MIS_OPER, DANALLCDP.ONDAITM.VIAGEM, DANALLCDP.ONDAITM.PALETE, DANALLCDP.ONDAITM.TOT_PALETE,
DANALLCDP.ONDAITM.TYPSUP, DANALLCDP.ONDAITM.USUARIO, DANALLCDP.ONDAITM.PREP, GEZPRP.NOMPRP, DANALLCDP.ONDADET.MIS_DONE,
OPERADOR.CARDES, OPERADOR.NOMUTI
ORDER BY DANALLCDP.ONDAITM.VIAGEM, DANALLCDP.ONDAITM.PALETE ASC 
"""

try:
	conn = pyodbc.connect(conn_str)
	cursor = conn.cursor()
	cursor.execute(sql)
	rows = cursor.fetchall()
	columns = [column[0] for column in cursor.description]
	print("\nResultado da consulta:")
	print(" | ".join(columns))
	print("-" * 80)
	for row in rows:
		print(" | ".join(str(item) for item in row))
	cursor.close()
	conn.close()
except Exception as e:
	print("Erro ao conectar ou executar a consulta:", e)
