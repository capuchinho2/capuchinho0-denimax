import sqlite3
import os

def adicionar_preparador(codprp, nome, turno=''):
    """
    Adiciona um preparador no banco preparador.db
    """
    db_path = os.path.join(os.path.dirname(__file__), 'preparador.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se já existe
        cursor.execute('SELECT NOME, TURNO FROM preparadores WHERE CODPRP = ?', (codprp,))
        existe = cursor.fetchone()
        
        if existe:
            print(f"❌ Preparador {codprp} já existe: {existe[0]} - Turno: {existe[1]}")
            opcao = input("Deseja atualizar? (s/n): ")
            if opcao.lower() == 's':
                cursor.execute('UPDATE preparadores SET NOME = ?, TURNO = ? WHERE CODPRP = ?', (nome, turno, codprp))
                conn.commit()
                print(f"✅ Preparador {codprp} atualizado: {nome} - Turno: {turno}")
            else:
                print("❌ Operação cancelada")
        else:
            cursor.execute('INSERT INTO preparadores (CODPRP, NOME, TURNO) VALUES (?, ?, ?)', (codprp, nome, turno))
            conn.commit()
            print(f"✅ Preparador adicionado: {codprp} - {nome} - Turno: {turno}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao adicionar preparador: {e}")
        import traceback
        traceback.print_exc()

def listar_preparadores():
    """
    Lista todos os preparadores do banco
    """
    db_path = os.path.join(os.path.dirname(__file__), 'preparador.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT CODPRP, NOME, TURNO FROM preparadores ORDER BY NOME')
        rows = cursor.fetchall()
        conn.close()
        
        print("\n" + "="*80)
        print("PREPARADORES CADASTRADOS")
        print("="*80)
        print(f"{'CÓDIGO':<15} {'NOME':<35} {'TURNO':<10}")
        print("-"*80)
        for codprp, nome, turno in rows:
            print(f"{codprp:<15} {nome:<35} {turno or 'N/A':<10}")
        print("="*80)
        print(f"Total: {len(rows)} preparadores\n")
        
    except Exception as e:
        print(f"❌ Erro ao listar preparadores: {e}")

if __name__ == "__main__":
    print("="*80)
    print("GERENCIADOR DE PREPARADORES - preparador.db")
    print("="*80)
    
    while True:
        print("\n1. Adicionar novo preparador")
        print("2. Listar todos os preparadores")
        print("3. Sair")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            codprp = input("\nCódigo do preparador (ex: CDP123): ").strip().upper()
            nome = input("Nome completo: ").strip().upper()
            turno = input("Turno (1º/2º/3º ou deixe vazio): ").strip().upper()
            
            if codprp and nome:
                adicionar_preparador(codprp, nome, turno)
            else:
                print("❌ Código e nome são obrigatórios!")
                
        elif opcao == "2":
            listar_preparadores()
            
        elif opcao == "3":
            print("\n👋 Até logo!")
            break
        else:
            print("❌ Opção inválida!")
