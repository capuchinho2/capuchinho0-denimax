import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.colaborador_utils import buscar_nome_colaborador_por_codigo

# Testar com alguns códigos
codigos_teste = ['CDP152599', 'CDP168016', 'CDP158316', 'CDP129333']

print("=" * 50)
print("TESTE DE BUSCA DE NOMES")
print("=" * 50)

for codigo in codigos_teste:
    print(f"\nTestando código: '{codigo}'")
    nome = buscar_nome_colaborador_por_codigo(codigo)
    print(f"Resultado: {nome}")
    print("-" * 50)

# Agora vamos testar com dados reais da API
print("\n" + "=" * 50)
print("TESTANDO COM DADOS REAIS DA API")
print("=" * 50)

from app.utils.logic import obter_status_prep
from datetime import datetime

data_hoje = datetime.now().strftime('%Y%m%d')
print(f"\nBuscando viagens para data: {data_hoje}")

resultado = obter_status_prep(data_hoje, data_hoje, '')

if resultado.get('success') and resultado.get('viagens_pendentes'):
    print(f"\nEncontradas {len(resultado['viagens_pendentes'])} viagens pendentes")
    print("\nPrimeiras 5 viagens:")
    for i, viagem in enumerate(resultado['viagens_pendentes'][:5]):
        codigo = viagem.get('prep', '').strip()
        print(f"\nViagem {i+1}:")
        print(f"  Código prep original: '{viagem.get('prep')}'")
        print(f"  Código prep stripped: '{codigo}'")
        nome = buscar_nome_colaborador_por_codigo(codigo) if codigo else None
        print(f"  Nome encontrado: {nome}")
else:
    print("\nNenhuma viagem pendente encontrada ou erro na API")
    print(f"Resultado: {resultado}")
