import os
from dotenv import load_dotenv
from mysql.connector.pooling import MySQLConnectionPool

# Carrega as variáveis do arquivo .env
load_dotenv()

_pool = MySQLConnectionPool(
    pool_name="camara_pool",
    pool_size=10,
    host=os.environ.get("DB_HOST", "localhost"),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD", "123456"),
    database=os.environ.get("DB_NAME", "camara_db"),
    autocommit=False,
)


def get_connection():
    return _pool.get_connection()