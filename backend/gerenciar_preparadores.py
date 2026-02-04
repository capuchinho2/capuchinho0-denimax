"""
Script de Gerenciamento de Preparadores
Gerencia os preparadores no banco preparador.db
"""
import sqlite3
import os

def criar_banco_se_nao_existe():
    """Cria o banco se não existir"""
    db_path = os.path.join(os.path.dirname(__file__), 'preparador.db')
    
    if not os.path.exists(db_path):
        print("\n⚠️  Banco de dados não encontrado. Criando...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preparadores (
                CODPRP TEXT PRIMARY KEY,
                NOME TEXT NOT NULL,
                TURNO TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Banco de dados criado com sucesso!")

def adicionar_preparador(codprp, nome, turno=''):
    """Adiciona ou atualiza um preparador"""
    db_path = os.path.join(os.path.dirname(__file__), 'preparador.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT NOME, TURNO FROM preparadores WHERE CODPRP = ?', (codprp,))
    existe = cursor.fetchone()
    
    if existe:
        print(f"\n⚠️  Preparador {codprp} já existe: {existe[0]} - Turno: {existe[1]}")
        opcao = input("Deseja atualizar? (s/n): ")
        if opcao.lower() == 's':
            cursor.execute('UPDATE preparadores SET NOME = ?, TURNO = ? WHERE CODPRP = ?', (nome, turno, codprp))
            conn.commit()
            print(f"✅ Preparador {codprp} atualizado!")
        else:
            print("❌ Operação cancelada")
    else:
        cursor.execute('INSERT INTO preparadores (CODPRP, NOME, TURNO) VALUES (?, ?, ?)', (codprp, nome, turno))
        conn.commit()
        print(f"✅ Preparador {codprp} adicionado com sucesso!")
    
    conn.close()

def listar_preparadores():
    """Lista todos os preparadores"""
    db_path = os.path.join(os.path.dirname(__file__), 'preparador.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT CODPRP, NOME, TURNO FROM preparadores ORDER BY NOME')
    rows = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*80)
    print("PREPARADORES CADASTRADOS")
    print("="*80)
    print(f"{'CÓDIGO':<15} {'NOME':<40} {'TURNO':<10}")
    print("-"*80)
    for codprp, nome, turno in rows:
        print(f"{codprp:<15} {nome:<40} {turno or 'N/A':<10}")
    print("="*80)
    print(f"Total: {len(rows)} preparadores\n")

def remover_preparador(codprp):
    """Remove um preparador"""
    db_path = os.path.join(os.path.dirname(__file__), 'preparador.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT NOME FROM preparadores WHERE CODPRP = ?', (codprp,))
    existe = cursor.fetchone()
    
    if existe:
        print(f"\n⚠️  Preparador: {codprp} - {existe[0]}")
        opcao = input("Confirma remoção? (s/n): ")
        if opcao.lower() == 's':
            cursor.execute('DELETE FROM preparadores WHERE CODPRP = ?', (codprp,))
            conn.commit()
            print(f"✅ Preparador {codprp} removido!")
        else:
            print("❌ Operação cancelada")
    else:
        print(f"\n❌ Preparador {codprp} não encontrado!")
    
    conn.close()

def buscar_preparador(termo):
    """Busca preparadores por código ou nome"""
    db_path = os.path.join(os.path.dirname(__file__), 'preparador.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT CODPRP, NOME, TURNO FROM preparadores 
        WHERE CODPRP LIKE ? OR NOME LIKE ?
        ORDER BY NOME
    ''', (f'%{termo}%', f'%{termo}%'))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        print("\n" + "="*80)
        print(f"RESULTADOS DA BUSCA: '{termo}'")
        print("="*80)
        print(f"{'CÓDIGO':<15} {'NOME':<40} {'TURNO':<10}")
        print("-"*80)
        for codprp, nome, turno in rows:
            print(f"{codprp:<15} {nome:<40} {turno or 'N/A':<10}")
        print("="*80)
        print(f"Total: {len(rows)} preparador(es) encontrado(s)\n")
    else:
        print(f"\n❌ Nenhum preparador encontrado com '{termo}'")

if __name__ == "__main__":
    print("="*80)
    print(" "*20 + "GERENCIADOR DE PREPARADORES")
    print("="*80)
    
    criar_banco_se_nao_existe()
    
    while True:
        print("\n📋 MENU:")
        print("1. Adicionar preparador")
        print("2. Listar todos")
        print("3. Buscar preparador")
        print("4. Remover preparador")
        print("5. Sair")
        
        opcao = input("\n➜ Escolha uma opção: ").strip()
        
        if opcao == "1":
            print("\n" + "-"*50)
            codprp = input("Código do preparador: ").strip().upper()
            nome = input("Nome completo: ").strip().upper()
            turno = input("Turno (1º/2º/3º): ").strip().upper()
            
            if codprp and nome:
                adicionar_preparador(codprp, nome, turno)
            else:
                print("❌ Código e nome são obrigatórios!")
                
        elif opcao == "2":
            listar_preparadores()
            
        elif opcao == "3":
            termo = input("\n🔍 Buscar por código ou nome: ").strip().upper()
            if termo:
                buscar_preparador(termo)
            else:
                print("❌ Digite algo para buscar!")
                
        elif opcao == "4":
            codprp = input("\n🗑️  Código do preparador a remover: ").strip().upper()
            if codprp:
                remover_preparador(codprp)
            else:
                print("❌ Código é obrigatório!")
                
        elif opcao == "5":
            print("\n👋 Até logo!\n")
            break
        else:
            print("\n❌ Opção inválida!")
