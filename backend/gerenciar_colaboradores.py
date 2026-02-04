import sqlite3
import os

# Caminho do banco de dados na mesma pasta do script
DB_PATH = os.path.join(os.path.dirname(__file__), 'colaboradores.db')

def listar_colaboradores():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT MATRICULA, NOME, TURNO FROM colaboradores ORDER BY NOME')
    colaboradores = cursor.fetchall()
    
    if not colaboradores:
        print("\n⚠️ Nenhum colaborador cadastrado.")
        conn.close()
        return
    
    print("\n📋 Lista de Colaboradores:\n")
    print(f"{'Matrícula':<15} {'Nome':<30} {'Turno':<10}")
    print("-" * 60)
    for matricula, nome, turno in colaboradores:
        print(f"{matricula:<15} {nome:<30} {turno:<10}")
    
    conn.close()
    return len(colaboradores)

def excluir_colaborador():
    matricula = input("\n🗑️  Digite a matrícula do colaborador a excluir: ").strip()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar se existe
    cursor.execute('SELECT NOME FROM colaboradores WHERE MATRICULA = ?', (matricula,))
    resultado = cursor.fetchone()
    
    if not resultado:
        print(f"\n❌ Matrícula '{matricula}' não encontrada!")
        conn.close()
        return
    
    nome = resultado[0]
    confirmacao = input(f"\n⚠️  Confirma exclusão de '{nome}' (matrícula {matricula})? (s/n): ").strip().lower()
    
    if confirmacao == 's':
        cursor.execute('DELETE FROM colaboradores WHERE MATRICULA = ?', (matricula,))
        conn.commit()
        print(f"\n✅ Colaborador '{nome}' excluído com sucesso!")
    else:
        print("\n❌ Exclusão cancelada.")
    
    conn.close()

def excluir_todos():
    confirmacao = input("\n⚠️  TEM CERTEZA que deseja EXCLUIR TODOS os colaboradores? (s/n): ").strip().lower()
    
    if confirmacao != 's':
        print("\n❌ Operação cancelada.")
        return
    
    confirmacao2 = input("⚠️  Confirme novamente digitando 'EXCLUIR TODOS': ").strip()
    
    if confirmacao2 != 'EXCLUIR TODOS':
        print("\n❌ Operação cancelada.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM colaboradores')
    conn.commit()
    linhas = cursor.rowcount
    conn.close()
    
    print(f"\n✅ {linhas} colaborador(es) excluído(s)!")

# Menu principal
while True:
    print("\n" + "="*60)
    print("🔧 GERENCIAR COLABORADORES")
    print("="*60)
    print("\n1. 📋 Listar todos")
    print("2. 🗑️  Excluir um colaborador")
    print("3. ⚠️  Excluir TODOS os colaboradores")
    print("4. 🚪 Sair")
    
    opcao = input("\nEscolha uma opção: ").strip()
    
    if opcao == '1':
        total = listar_colaboradores()
        if total:
            print(f"\nTotal: {total} colaborador(es)")
    elif opcao == '2':
        listar_colaboradores()
        excluir_colaborador()
    elif opcao == '3':
        listar_colaboradores()
        excluir_todos()
    elif opcao == '4':
        print("\n👋 Até logo!")
        break
    else:
        print("\n❌ Opção inválida!")
