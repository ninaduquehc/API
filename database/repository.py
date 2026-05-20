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


def buscar_todos_deputados():
    """Retorna todos os deputados ordenados por nome (sem limite de paginação)."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, nome, url_foto, sigla_partido, sigla_uf, cargo_partido, email
        FROM deputados
        ORDER BY nome ASC
    """)
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

def buscar_ranking_gastos(uf=None, ordem="desc", partido=None):
    conn   = get_connection()
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
    if partido:
        query += " AND d.sigla_partido = %s"
        params.append(partido)
 
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

def buscar_ranking_presenca(uf=None, ordem="asc", partido=None):
    conn   = get_connection()
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
    if partido:
        query += " AND d.sigla_partido = %s"
        params.append(partido)
 
    query += f" GROUP BY d.id, d.nome, d.sigla_uf, d.sigla_partido, p.percentual_presenca, media_uf.media ORDER BY presenca {direcao}"
 
    cursor.execute(query, params)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados

def contar_ranking(uf=None, criterio="gastos", partido=None):
    conn   = get_connection()
    cursor = conn.cursor()
 
    if criterio == "presenca":
        query = "SELECT COUNT(*) FROM presencas p JOIN deputados d ON d.id = p.id_deputado WHERE 1=1"
    else:
        query = "SELECT COUNT(DISTINCT d.id) FROM deputados d JOIN despesas dep ON dep.id_deputado = d.id WHERE 1=1"
 
    params = []
    if uf:
        query += " AND d.sigla_uf = %s"
        params.append(uf)
    if partido:
        query += " AND d.sigla_partido = %s"
        params.append(partido)
 
    cursor.execute(query, params)
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total

def buscar_dados_ranking_pl(uf=None, partido=None):
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
 
    query = """
        SELECT
            d.id, d.nome, d.sigla_uf, d.sigla_partido, d.url_foto,
            SUM(CASE WHEN p.sigla_tipo = 'PL'  THEN 1 ELSE 0 END) AS total_pl,
            SUM(CASE WHEN p.sigla_tipo = 'PDC' THEN 1 ELSE 0 END) AS total_pdc,
            SUM(CASE WHEN p.sigla_tipo = 'PEC' THEN 1 ELSE 0 END) AS total_pec
        FROM deputados d
        LEFT JOIN proposicoes p ON p.id_deputado = d.id
        WHERE 1=1
    """
    params = []
    if uf:
        query += " AND d.sigla_uf = %s"
        params.append(uf)
    if partido:
        query += " AND d.sigla_partido = %s"
        params.append(partido)
 
    query += " GROUP BY d.id, d.nome, d.sigla_uf, d.sigla_partido, d.url_foto"
 
    cursor.execute(query, params)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados

# ── Proposições ──────────────────────────────────────────────

def buscar_proposicoes_deputado(id_deputado, tipo=None, ano=None, situacao=None):
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    query  = """
        SELECT p.id, p.sigla_tipo, p.numero, p.ano, p.ementa,
               p.keywords, p.situacao, p.url_inteiro_teor
        FROM proposicoes p
        WHERE p.id_deputado = %s
    """
    params = [id_deputado]

    if tipo:
        query += " AND p.sigla_tipo = %s"
        params.append(tipo)
    if ano:
        query += " AND p.ano = %s"
        params.append(ano)
    if situacao:
        query += " AND p.situacao LIKE %s"
        params.append(f"%{situacao}%")

    query += " ORDER BY p.ano DESC, p.numero DESC"

    cursor.execute(query, params)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados


def buscar_top_temas_deputado(id_deputado, limite=5):
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT t.nome, COUNT(*) AS total
        FROM proposicoes_temas pt
        JOIN temas t ON t.cod = pt.cod_tema
        JOIN proposicoes p ON p.id = pt.id_proposicao
        WHERE p.id_deputado = %s
        GROUP BY t.cod, t.nome
        ORDER BY total DESC
        LIMIT %s
    """, (id_deputado, limite))

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados


def buscar_resumo_proposicoes_deputado(id_deputado):
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            sigla_tipo,
            ano,
            COUNT(*) AS total
        FROM proposicoes
        WHERE id_deputado = %s
        GROUP BY sigla_tipo, ano
        ORDER BY ano DESC, sigla_tipo
    """, (id_deputado,))

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados


def buscar_anos_proposicoes_deputado(id_deputado):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT ano FROM proposicoes
        WHERE id_deputado = %s
        ORDER BY ano DESC
    """, (id_deputado,))

    resultados = [row[0] for row in cursor.fetchall() if row[0]]
    cursor.close()
    conn.close()
    return resultados


def buscar_situacoes_proposicoes_deputado(id_deputado):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT situacao FROM proposicoes
        WHERE id_deputado = %s AND situacao != ''
        ORDER BY situacao
    """, (id_deputado,))

    resultados = [row[0] for row in cursor.fetchall() if row[0]]
    cursor.close()
    conn.close()
    return resultados

def buscar_ranking_proposicoes_deputado(id_deputado):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT *
        FROM (
            SELECT 
                d.id,
                d.nome,
                d.sigla_uf,
                COUNT(*) AS total_aprovadas,
                RANK() OVER (
                    PARTITION BY d.sigla_uf 
                    ORDER BY COUNT(*) DESC
                ) AS posicao
            FROM proposicoes p
            JOIN deputados d ON d.id = p.id_deputado
            WHERE p.situacao LIKE '%Aprovad%'
            GROUP BY d.id, d.nome, d.sigla_uf
        ) ranking
        WHERE id = %s
    """

    cursor.execute(query, (id_deputado,))
    resultado = cursor.fetchone()

    cursor.close()
    conn.close()
    return resultado


def contar_ranking_pl(uf=None):
    conn   = get_connection()
    cursor = conn.cursor()

    query  = "SELECT COUNT(*) FROM deputados d WHERE 1=1"
    params = []

    if uf:
        query += " AND d.sigla_uf = %s"
        params.append(uf)

    cursor.execute(query, params)
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total

def buscar_indice_coerencia(id_deputado, anos=3):
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
 
    cursor.execute("""
        WITH base AS (
            SELECT
                t.cod                                    AS cod_tema,
                t.nome                                   AS tema,
                COALESCE(disc.total_discursos,   0)      AS discursos,
                COALESCE(prop.total_proposicoes, 0)      AS proposicoes,
                COALESCE(apro.total_aprovacoes,  0)      AS aprovacoes
            FROM temas t
 
            LEFT JOIN (
                SELECT dt.cod_tema, COUNT(*) AS total_discursos
                FROM discursos d
                JOIN discursos_temas dt ON dt.id_discurso = d.id
                WHERE d.id_deputado = %s
                  AND d.ano >= YEAR(CURDATE()) - %s
                GROUP BY dt.cod_tema
            ) disc ON disc.cod_tema = t.cod
 
            LEFT JOIN (
                SELECT pt.cod_tema, COUNT(DISTINCT p.id) AS total_proposicoes
                FROM proposicoes p
                JOIN proposicoes_temas pt ON pt.id_proposicao = p.id
                WHERE p.id_deputado = %s
                  AND p.ano >= YEAR(CURDATE()) - %s
                GROUP BY pt.cod_tema
            ) prop ON prop.cod_tema = t.cod
 
            LEFT JOIN (
                SELECT pt.cod_tema, COUNT(DISTINCT p.id) AS total_aprovacoes
                FROM proposicoes p
                JOIN proposicoes_temas pt ON pt.id_proposicao = p.id
                WHERE p.id_deputado = %s
                  AND p.ano >= YEAR(CURDATE()) - %s
                  AND p.situacao = 'Transformado em Norma Jurídica'
                GROUP BY pt.cod_tema
            ) apro ON apro.cod_tema = t.cod
 
            WHERE disc.total_discursos   > 0
               OR prop.total_proposicoes > 0
        ),
        maximos AS (
            SELECT
                GREATEST(MAX(discursos),   1) AS max_d,
                GREATEST(MAX(proposicoes), 1) AS max_p,
                GREATEST(MAX(aprovacoes),  1) AS max_a
            FROM base
        )
        SELECT
            b.cod_tema,
            b.tema,
            b.discursos,
            b.proposicoes,
            b.aprovacoes,
            ROUND(
                CASE WHEN b.proposicoes = 0 THEN 0
                ELSE (
                    (b.discursos   / m.max_d) * 0.30 +
                    (b.proposicoes / m.max_p) * 0.40 +
                    (b.aprovacoes  / m.max_a) * 0.30
                ) * 100
                END, 1
            ) AS indice_coerencia
        FROM base b, maximos m
        ORDER BY indice_coerencia DESC, b.tema ASC
    """, (id_deputado, anos, id_deputado, anos, id_deputado, anos))
 
    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado
 
 
def buscar_resumo_coerencia(id_deputado, anos=3):
    dados = buscar_indice_coerencia(id_deputado, anos)
 
    if not dados:
        return {
            "total_temas":       0,
            "total_discursos":   0,
            "total_proposicoes": 0,
            "total_aprovacoes":  0,
            "indice_medio":      0.0,
            "temas":             [],
        }
 
    # Conta direto no banco para evitar dupla contagem por tema
    conn   = get_connection()
    cursor = conn.cursor()
 
    cursor.execute(
        "SELECT COUNT(DISTINCT d.id) FROM discursos d"
        " JOIN discursos_temas dt ON dt.id_discurso = d.id"
        " WHERE d.id_deputado = %s AND d.ano >= YEAR(CURDATE()) - %s",
        (id_deputado, anos)
    )
    total_discursos = cursor.fetchone()[0] or 0
 
    cursor.execute(
        "SELECT COUNT(DISTINCT p.id) FROM proposicoes p"
        " JOIN proposicoes_temas pt ON pt.id_proposicao = p.id"
        " WHERE p.id_deputado = %s AND p.ano >= YEAR(CURDATE()) - %s",
        (id_deputado, anos)
    )
    total_proposicoes = cursor.fetchone()[0] or 0
 
    cursor.execute(
        "SELECT COUNT(DISTINCT p.id) FROM proposicoes p"
        " JOIN proposicoes_temas pt ON pt.id_proposicao = p.id"
        " WHERE p.id_deputado = %s AND p.ano >= YEAR(CURDATE()) - %s"
        " AND p.situacao = 'Transformado em Norma Jur\u00eddica'",
        (id_deputado, anos)
    )
    total_aprovacoes = cursor.fetchone()[0] or 0
 
    cursor.close()
    conn.close()
 
    temas_com_indice = sorted(
        [d["indice_coerencia"] for d in dados if d["indice_coerencia"] > 0]
    )
    n = len(temas_com_indice)
    if n == 0:
        indice_medio = 0.0
    elif n % 2 == 1:
        indice_medio = round(temas_com_indice[n // 2], 1)
    else:
        indice_medio = round((temas_com_indice[n // 2 - 1] + temas_com_indice[n // 2]) / 2, 1)
 
    return {
        "total_temas":       len(dados),
        "total_discursos":   total_discursos,
        "total_proposicoes": total_proposicoes,
        "total_aprovacoes":  total_aprovacoes,
        "indice_medio":      indice_medio,
        "temas":             dados,
    }
