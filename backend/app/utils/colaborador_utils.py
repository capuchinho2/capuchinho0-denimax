import sqlite3
import os

def buscar_nome_colaborador_por_codigo(codigo_prep):
    """
    Busca o nome do colaborador pelo código do preparador na base colaboradores_prp.db
    """
    db_path = os.path.join(os.path.dirname(__file__), '../../colaboradores_prp.db')
    print(f"[DEBUG colaborador_utils] DB Path: {db_path}")
    print(f"[DEBUG colaborador_utils] Executando query: SELECT NOMES FROM colaboradores WHERE MATRICULA = '{codigo_prep.strip()}'")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT NOMES FROM colaboradores WHERE MATRICULA = ?', (codigo_prep.strip(),))
        row = cursor.fetchone()
        conn.close()
        print(f"[DEBUG colaborador_utils] Resultado: {row}")
        if row:
            return row[0]
        return None
    except Exception as e:
        print(f"[ERROR colaborador_utils] Erro ao buscar nome do colaborador: {e}")
        import traceback
        traceback.print_exc()
        return None
