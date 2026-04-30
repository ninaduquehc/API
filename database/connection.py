from mysql.connector.pooling import MySQLConnectionPool

_pool = MySQLConnectionPool(
    pool_name="camara_pool",
    pool_size=10,
    host="localhost",
    user="root",
<<<<<<< HEAD
    password="fatec",
=======
    password="123456",
>>>>>>> atualizacao-projeto-29-04
    database="camara_db",
    autocommit=False,
)


def get_connection():
    return _pool.get_connection()