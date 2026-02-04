import sqlite3
import os

# Caminho do banco de dados na mesma pasta do script
DB_PATH = os.path.join(os.path.dirname(__file__), 'colaboradores.db')

# Conectar ao banco de dados
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("➕ Adicionar novo colaborador\n")

matricula = input("Matrícula: ").strip()
nome = input("Nome: ").strip()
turno = input("Turno (1º, 2º, 3º): ").strip()

try:
    cursor.execute('''
        INSERT INTO colaboradores (MATRICULA, NOME, TURNO)
        VALUES (?, ?, ?)
    ''', (matricula, nome, turno))
    conn.commit()
    print(f"\n✅ Colaborador '{nome}' adicionado com sucesso!")
except sqlite3.IntegrityError:
    print(f"\n⚠️ Matrícula '{matricula}' já existe!")
    
    resposta = input("Deseja atualizar? (s/n): ").strip().lower()
    if resposta == 's':
        cursor.execute('''
            UPDATE colaboradores 
            SET NOME = ?, TURNO = ?
            WHERE MATRICULA = ?
        ''', (nome, turno, matricula))
        conn.commit()
        print(f"✅ Colaborador atualizado!")

conn.close()
