import pyodbc
from typing import List, Dict, Any

class DB2Connection:
    def __init__(self, system: str, uid: str, pwd: str, driver: str = "iSeries Access ODBC Driver"):
        self.system = system
        self.uid = uid
        self.pwd = pwd
        self.driver = driver
        self.conn = None
        
    def connect(self):
        """Conecta ao DB2 via ODBC"""
        conn_str = (
            f"DRIVER={{{self.driver}}};"
            f"SYSTEM={self.system};"
            f"UID={self.uid};"
            f"PWD={self.pwd};"
        )
        try:
            self.conn = pyodbc.connect(conn_str)
            print(f"✓ Conectado ao DB2: {self.system}")
            return True
        except Exception as e:
            print(f"✗ Erro ao conectar DB2: {e}")
            return False
    
    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Executa query e retorna lista de dicionários"""
        if not self.conn:
            self.connect()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            
            # Pega nomes das colunas
            columns = [column[0] for column in cursor.description]
            
            # Converte para lista de dicionários
            result = []
            for row in cursor.fetchall():
                result.append(dict(zip(columns, row)))
            
            cursor.close()
            print(f"✓ Query executada: {len(result)} registros")
            return result
        except Exception as e:
            print(f"✗ Erro na query: {e}")
            return []
    
    def close(self):
        """Fecha conexão"""
        if self.conn:
            self.conn.close()
            print("✓ Conexão DB2 fechada")


class MySQLConnection:
    def __init__(self, host: str, user: str, password: str, database: str):
        import mysql.connector
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        
    def connect(self):
        """Conecta ao MySQL"""
        try:
            import mysql.connector
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print(f"✓ Conectado ao MySQL: {self.database}")
            return True
        except Exception as e:
            print(f"✗ Erro ao conectar MySQL: {e}")
            return False
    
    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Executa query e retorna lista de dicionários"""
        if not self.conn:
            self.connect()
        
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            print(f"✓ Query executada: {len(result)} registros")
            return result
        except Exception as e:
            print(f"✗ Erro na query: {e}")
            return []
    
    def close(self):
        """Fecha conexão"""
        if self.conn:
            self.conn.close()
            print("✓ Conexão MySQL fechada")
