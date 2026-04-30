from database.connection import get_connection


def buscar_deputados(uf="", partido="", nome="", limit=12, offset=0):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM deputados WHERE 1=1"
    params = []

    if uf:
        query += " AND sigla_uf = %s"
        params.append(uf)
    if partido:
        query += " AND sigla_partido = %s"
        params.append(partido)
    if nome:
        query += " AND nome LIKE %s"
        params.append(f"%{nome}%")

    query += " ORDER BY nome ASC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, params)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados


def contar_deputados(uf="", partido="", nome=""):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT COUNT(*) FROM deputados WHERE 1=1"
    params = []

    if uf:
        query += " AND sigla_uf = %s"
        params.append(uf)
    if partido:
        query += " AND sigla_partido = %s"
        params.append(partido)
    if nome:
        query += " AND nome LIKE %s"
        params.append(f"%{nome}%")

    cursor.execute(query, params)
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total


def buscar_despesas_por_deputados(ids):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if not ids:
        return []

    format_strings = ','.join(['%s'] * len(ids))
    query = f"""
        SELECT d.*, d.valor AS valorDocumento, dep.nome as nome_deputado
        FROM despesas d
        JOIN deputados dep ON dep.id = d.id_deputado
        WHERE d.id_deputado IN ({format_strings})
    """

    cursor.execute(query, tuple(ids))
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados


def buscar_deputado_por_id(id_deputado):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM deputados WHERE id = %s", (id_deputado,))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado


def buscar_despesas_deputado(id_deputado, ano=None, mes=None, tipo=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            id_deputado, ano, mes, tipo_despesa,
            valor AS valorDocumento,
            nome_fornecedor, cnpj_cpf_fornecedor,
            data_documento, num_documento, url_documento,
            id_documento AS idDocumento
        FROM despesas
        WHERE id_deputado = %s
    """
    params = [id_deputado]

    if ano:
        query += " AND ano = %s"
        params.append(ano)
    if mes:
        query += " AND mes = %s"
        params.append(mes)
    if tipo:
        query += " AND tipo_despesa LIKE %s"
        params.append(f"%{tipo}%")

    query += " ORDER BY ano DESC, mes DESC, data_documento DESC"

    cursor.execute(query, params)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados


def buscar_tipos_despesa_deputado(id_deputado):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT DISTINCT tipo_despesa FROM despesas WHERE id_deputado = %s ORDER BY tipo_despesa",
        (id_deputado,)
    )
    resultados = [row[0] for row in cursor.fetchall() if row[0]]
    cursor.close()
    conn.close()
    return resultados


def buscar_anos_despesa_deputado(id_deputado):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT DISTINCT ano FROM despesas WHERE id_deputado = %s ORDER BY ano DESC",
        (id_deputado,)
    )
    resultados = [row[0] for row in cursor.fetchall() if row[0]]
    cursor.close()
    conn.close()
    return resultados

def buscar_ranking_gastos(uf=None, ordem="desc"):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    direcao = "ASC" if ordem == "asc" else "DESC"

    query = f"""
        SELECT 
            d.id, d.nome, d.sigla_uf, d.sigla_partido,
            SUM(dep.valor) AS total_gasto,
            COALESCE(p.percentual_presenca, 0) AS presenca,
            COALESCE(media_uf.media, 0) AS media_uf
        FROM deputados d
        JOIN despesas dep ON dep.id_deputado = d.id
        LEFT JOIN presencas p ON p.id_deputado = d.id
        LEFT JOIN (
            SELECT d2.sigla_uf, AVG(p2.percentual_presenca) AS media
            FROM presencas p2
            JOIN deputados d2 ON d2.id = p2.id_deputado
            GROUP BY d2.sigla_uf
        ) media_uf ON media_uf.sigla_uf = d.sigla_uf
        WHERE 1=1
    """

    params = []
    if uf:
        query += " AND d.sigla_uf = %s"
        params.append(uf)

    query += f" GROUP BY d.id, d.nome, d.sigla_uf, d.sigla_partido, p.percentual_presenca, media_uf.media ORDER BY total_gasto {direcao}"

    cursor.execute(query, params)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados

def buscar_presenca_deputado(id_deputado):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT percentual_presenca
        FROM presencas
        WHERE id_deputado = %s
    """, (id_deputado,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()
    return result

def media_presenca_estado(uf):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT AVG(p.percentual_presenca)
        FROM presencas p
        JOIN deputados d ON d.id = p.id_deputado
        WHERE d.sigla_uf = %s
    """, (uf,))

    media = cursor.fetchone()[0]

    cursor.close()
    conn.close()
    return round(media, 2) if media else 0

def buscar_ranking_presenca(uf=None, ordem="asc"):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    direcao = "ASC" if ordem == "asc" else "DESC"

    query = f"""
        SELECT 
            d.id, d.nome, d.sigla_uf, d.sigla_partido,
            p.percentual_presenca AS presenca,
            COALESCE(media_uf.media, 0) AS media_uf,
            COALESCE(SUM(dep.valor), 0) AS total_gasto
        FROM deputados d
        JOIN presencas p ON p.id_deputado = d.id
        LEFT JOIN despesas dep ON dep.id_deputado = d.id
        LEFT JOIN (
            SELECT d2.sigla_uf, AVG(p2.percentual_presenca) AS media
            FROM presencas p2
            JOIN deputados d2 ON d2.id = p2.id_deputado
            GROUP BY d2.sigla_uf
        ) media_uf ON media_uf.sigla_uf = d.sigla_uf
        WHERE 1=1
    """

    params = []
    if uf:
        query += " AND d.sigla_uf = %s"
        params.append(uf)

    query += f" GROUP BY d.id, d.nome, d.sigla_uf, d.sigla_partido, p.percentual_presenca, media_uf.media ORDER BY presenca {direcao}"

    cursor.execute(query, params)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados

def contar_ranking(uf=None, criterio="gastos"):
    conn = get_connection()
    cursor = conn.cursor()
    if criterio == "presenca":
        query = "SELECT COUNT(*) FROM presencas p JOIN deputados d ON d.id = p.id_deputado WHERE 1=1"
    else:
        query = "SELECT COUNT(DISTINCT d.id) FROM deputados d JOIN despesas dep ON dep.id_deputado = d.id WHERE 1=1"
    params = []
    if uf:
        query += " AND d.sigla_uf = %s"
        params.append(uf)
    cursor.execute(query, params)
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total