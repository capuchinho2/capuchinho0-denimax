import pyodbc

from .settings_config import DB_SETTINGS

def get_db_connection():
    """
    Cria e retorna uma conexão com o banco de dados IBM iSeries.
    """
    try:
        connection_string = (
            f"DRIVER={DB_SETTINGS['DRIVER']};"
            f"SYSTEM={DB_SETTINGS['SYSTEM']};"
            f"UID={DB_SETTINGS['UID']};"
            f"PWD={DB_SETTINGS['PWD']}"
        )
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise
