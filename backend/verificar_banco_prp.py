import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'colaboradores_prp.db')
print(f"Verificando banco: {db_path}")
print(f"Banco existe: {os.path.exists(db_path)}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Listar todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTabelas no banco: {tables}")
    
    if tables:
        for table in tables:
            table_name = table[0]
            print(f"\n--- Estrutura da tabela '{table_name}' ---")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  Coluna: {col[1]} | Tipo: {col[2]}")
            
            # Mostrar primeiros 5 registros
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            print(f"\nPrimeiros 5 registros:")
            for row in rows:
                print(f"  {row}")
    else:
        print("\n⚠️  Banco vazio! Nenhuma tabela encontrada.")
        print("\nCriando tabela 'colaboradores'...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS colaboradores (
                MATRICULA TEXT PRIMARY KEY,
                NOME TEXT NOT NULL,
                TURNO TEXT
            )
        ''')
        conn.commit()
        print("✅ Tabela criada!")
    
    conn.close()
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
