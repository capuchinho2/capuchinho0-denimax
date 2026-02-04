# database.py ou config.py
import pyodbc
from contextlib import contextmanager

AS400_CONFIG = {
    'driver': 'iSeries Access ODBC Driver',
    'system': 'FGE5006CDP',
    'user': 'CDP174176G',
    'password': 'CDP1753'
}

@contextmanager
def get_as400_connection():
    """Context manager para AS/400"""
    conn = None
    try:
        conn_string = (
            f"DRIVER={{{AS400_CONFIG['driver']}}};"
            f"SYSTEM={AS400_CONFIG['system']};"
            f"UID={AS400_CONFIG['user']};"
            f"PWD={AS400_CONFIG['password']};"
        )
        conn = pyodbc.connect(conn_string)
        yield conn
    finally:
        if conn:
            conn.close()

# Usar:
def query_as400(sql):
    with get_as400_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results