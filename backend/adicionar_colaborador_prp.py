import sqlite3
import os

def adicionar_colaborador(matricula, nome):
    """
    Adiciona um colaborador no banco colaboradores_prp.db
    """
    db_path = os.path.join(os.path.dirname(__file__), 'colaboradores_prp.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se já existe
        cursor.execute('SELECT NOMES FROM colaboradores WHERE MATRICULA = ?', (matricula,))
        existe = cursor.fetchone()
        
        if existe:
            print(f"❌ Colaborador {matricula} já existe com o nome: {existe[0]}")
            opcao = input("Deseja atualizar? (s/n): ")
            if opcao.lower() == 's':
                cursor.execute('UPDATE colaboradores SET NOMES = ? WHERE MATRICULA = ?', (nome, matricula))
                conn.commit()
                print(f"✅ Colaborador {matricula} atualizado para: {nome}")
            else:
                print("❌ Operação cancelada")
        else:
            cursor.execute('INSERT INTO colaboradores (MATRICULA, NOMES) VALUES (?, ?)', (matricula, nome))
            conn.commit()
            print(f"✅ Colaborador adicionado: {matricula} - {nome}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao adicionar colaborador: {e}")
        import traceback
        traceback.print_exc()

def listar_colaboradores():
    """
    Lista todos os colaboradores do banco
    """
    db_path = os.path.join(os.path.dirname(__file__), 'colaboradores_prp.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT MATRICULA, NOMES FROM colaboradores ORDER BY MATRICULA')
        rows = cursor.fetchall()
        conn.close()
        
        print("\n" + "="*70)
        print("COLABORADORES CADASTRADOS")
        print("="*70)
        for matricula, nome in rows:
            print(f"{matricula:<15} {nome}")
        print("="*70)
        print(f"Total: {len(rows)} colaboradores\n")
        
    except Exception as e:
        print(f"❌ Erro ao listar colaboradores: {e}")

if __name__ == "__main__":
    print("="*70)
    print("GERENCIADOR DE COLABORADORES - colaboradores_prp.db")
    print("="*70)
    
    while True:
        print("\n1. Adicionar novo colaborador")
        print("2. Listar todos os colaboradores")
        print("3. Sair")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            matricula = input("\nMatrícula (ex: CDP123456): ").strip().upper()
            nome = input("Nome completo: ").strip().upper()
            
            if matricula and nome:
                adicionar_colaborador(matricula, nome)
            else:
                print("❌ Matrícula e nome são obrigatórios!")
                
        elif opcao == "2":
            listar_colaboradores()
            
        elif opcao == "3":
            print("\n👋 Até logo!")
            break
        else:
            print("❌ Opção inválida!")
