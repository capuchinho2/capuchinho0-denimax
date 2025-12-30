
import sqlite3
from datetime import datetime
import os
from pathlib import Path
from config import DB_CONFIG

def get_sqlite_connection():
    db_path = DB_CONFIG["SQLITE_PATH"]
    # Garante que o caminho é relativo à pasta backend
    backend_dir = Path(__file__).parent.parent.parent
    full_path = os.path.join(backend_dir, db_path) if not os.path.isabs(db_path) else db_path
    conn = sqlite3.connect(full_path)
    return conn

def criar_tabela_viagens():
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS viagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                viagem TEXT NOT NULL UNIQUE,
                preparada INTEGER DEFAULT 0,
                conferida INTEGER DEFAULT 0,
                expedida INTEGER DEFAULT 0,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def inserir_viagem(viagem):
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO viagens (viagem) VALUES (?)
    ''', (viagem,))
    conn.commit()
    cursor.close()
    conn.close()

def listar_viagens():
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM viagens ORDER BY id DESC')
    viagens = cursor.fetchall()
    cursor.close()
    conn.close()
    return viagens

def atualizar_status_viagem(viagem_id, campo):
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute(f'UPDATE viagens SET {campo} = 1 WHERE id = ?', (viagem_id,))
    conn.commit()
    cursor.close()
    conn.close()

def excluir_viagem(viagem_id):
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM viagens WHERE id = ?', (viagem_id,))
    conn.commit()
    cursor.close()
    conn.close()