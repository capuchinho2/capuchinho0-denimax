import sqlite3
import os

def criar_banco_operador():
    """
    Cria o banco de dados operador.db com a tabela de operadores
    """
    db_path = os.path.join(os.path.dirname(__file__), 'operador.db')
    
    # Verificar se o banco já existe
    if os.path.exists(db_path):
        resposta = input(f"⚠️  O banco '{db_path}' já existe. Deseja recriá-lo? (s/n): ")
        if resposta.lower() != 's':
            print("❌ Operação cancelada.")
            return
        os.remove(db_path)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Criar tabela de operadores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operadores (
                MATRICULA TEXT PRIMARY KEY,
                NOME TEXT NOT NULL,
                TURNO TEXT
            )
        ''')
        
        conn.commit()
        print(f"✅ Banco de dados '{db_path}' criado com sucesso!")
        print("📋 Estrutura da tabela 'operadores':")
        print("   - MATRICULA (TEXT, PRIMARY KEY)")
        print("   - NOME (TEXT, NOT NULL)")
        print("   - TURNO (TEXT)")
        
        # Mostrar informações
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = cursor.fetchall()
        print(f"\n📊 Tabelas no banco: {[t[0] for t in tabelas]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao criar banco: {e}")
        import traceback
        traceback.print_exc()

def adicionar_operador(matricula, nome, turno=''):
    """
    Adiciona um operador no banco operador.db
    """
    db_path = os.path.join(os.path.dirname(__file__), 'operador.db')
    
    if not os.path.exists(db_path):
        print("❌ Banco operador.db não existe. Execute criar_banco_operador() primeiro.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se já existe
        cursor.execute('SELECT NOME FROM operadores WHERE MATRICULA = ?', (matricula,))
        existe = cursor.fetchone()
        
        if existe:
            print(f"⚠️  Operador {matricula} já existe: {existe[0]}")
            opcao = input("Deseja atualizar? (s/n): ")
            if opcao.lower() == 's':
                cursor.execute('UPDATE operadores SET NOME = ?, TURNO = ? WHERE MATRICULA = ?', 
                             (nome, turno, matricula))
                conn.commit()
                print(f"✅ Operador atualizado: {matricula} - {nome} - Turno: {turno}")
            else:
                print("❌ Operação cancelada")
        else:
            cursor.execute('INSERT INTO operadores (MATRICULA, NOME, TURNO) VALUES (?, ?, ?)', 
                         (matricula, nome, turno))
            conn.commit()
            print(f"✅ Operador adicionado: {matricula} - {nome} - Turno: {turno}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao adicionar operador: {e}")
        import traceback
        traceback.print_exc()

def listar_operadores():
    """
    Lista todos os operadores do banco
    """
    db_path = os.path.join(os.path.dirname(__file__), 'operador.db')
    
    if not os.path.exists(db_path):
        print("❌ Banco operador.db não existe.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT MATRICULA, NOME, TURNO FROM operadores ORDER BY NOME')
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print("📭 Nenhum operador cadastrado.")
            return
        
        print(f"\n📋 Total de operadores: {len(rows)}\n")
        print(f"{'Matrícula':<15} {'Nome':<40} {'Turno':<10}")
        print("-" * 70)
        for matricula, nome, turno in rows:
            print(f"{matricula:<15} {nome:<40} {turno or 'N/A':<10}")
        
    except Exception as e:
        print(f"❌ Erro ao listar operadores: {e}")

def menu():
    """
    Menu interativo para gerenciar operadores
    """
    while True:
        print("\n" + "="*50)
        print("🔧 GERENCIADOR DE OPERADORES")
        print("="*50)
        print("1. Criar banco operador.db")
        print("2. Adicionar operador")
        print("3. Listar operadores")
        print("4. Sair")
        print("="*50)
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == '1':
            criar_banco_operador()
        elif opcao == '2':
            matricula = input("Matrícula: ").strip()
            nome = input("Nome: ").strip()
            turno = input("Turno (opcional): ").strip()
            adicionar_operador(matricula, nome, turno)
        elif opcao == '3':
            listar_operadores()
        elif opcao == '4':
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida!")

if __name__ == '__main__':
    menu()
