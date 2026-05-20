import asyncio
import aiohttp
import time
import requests
import pandas as pd
from database.connection import get_connection

BASE_URL         = "https://dadosabertos.camara.leg.br/api/v2"
ANOS             = [2023, 2024, 2025]
ITENS_POR_PAGINA = 100
MAX_CONCORRENCIA = 20
TIMEOUT_SEGUNDOS = 30

# Campos retornados pelo endpoint GET /deputados/{id}/discursos
COLUNAS = {
    "dataHoraInicio": "data_hora_inicio",
    "dataHoraFim":    "data_hora_fim",
    "tipoDiscurso":   "tipo_discurso",
    "sumario":        "sumario",
    "keywords":       "keywords",
    "faseEvento":     "fase_evento",
    "transcricao":    "transcricao",
    "uriEvento":      "uri_evento",
}


# ──────────────────────────────────────────────
# 1. TEMAS — SÍNCRONO (reutiliza tabela já populada pelo etl_proposicoes)
# ──────────────────────────────────────────────

def buscar_temas_do_banco() -> list[dict]:
    """
    Lê os temas já salvos pelo etl_proposicoes.
    Retorna lista de dicts com 'cod' (str) e 'nome' (str, minúsculo para match).
    """
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cod, nome FROM temas ORDER BY cod")
    temas = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"  ✅ {len(temas)} temas encontrados no banco")
    return temas


# ──────────────────────────────────────────────
# 2. DEPUTADOS
# ──────────────────────────────────────────────

def buscar_deputados_do_banco() -> list[dict]:
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nome FROM deputados ORDER BY nome")
    deputados = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"  ✅ {len(deputados)} deputados encontrados no banco")
    return deputados


# ──────────────────────────────────────────────
# 3. COLETA ASSÍNCRONA DE DISCURSOS
# ──────────────────────────────────────────────

async def fetch_pagina(session, semaforo, id_deputado, ano, pagina):
    url    = f"{BASE_URL}/deputados/{id_deputado}/discursos"
    params = {
        "dataInicio": f"{ano}-01-01",
        "dataFim":    f"{ano}-12-31",
        "itens":      ITENS_POR_PAGINA,
        "pagina":     pagina,
        "ordenarPor": "dataHoraInicio",
        "ordem":      "ASC",
    }

    async with semaforo:
        for tentativa in range(3):
            try:
                async with session.get(url, params=params) as res:
                    if res.status == 429:
                        await asyncio.sleep(2 ** tentativa)
                        continue
                    if res.status != 200:
                        return []
                    data  = await res.json(content_type=None)
                    dados = data.get("dados", [])
                    for d in dados:
                        d["_id_deputado"] = id_deputado
                        d["_ano"]         = ano
                    return dados
            except Exception as e:
                print(f"    ⚠️  Erro ({id_deputado}/ano {ano}/p{pagina}): {e}")
                await asyncio.sleep(1)
        return []


async def fetch_discursos_deputado(session, semaforo, id_deputado):
    todos = []

    for ano in ANOS:
        primeira = await fetch_pagina(session, semaforo, id_deputado, ano, 1)
        todos.extend(primeira)

        if len(primeira) < ITENS_POR_PAGINA:
            continue

        tarefas    = [
            fetch_pagina(session, semaforo, id_deputado, ano, p)
            for p in range(2, 21)
        ]
        resultados = await asyncio.gather(*tarefas)

        for lote in resultados:
            todos.extend(lote)
            if len(lote) < ITENS_POR_PAGINA:
                break

    return todos


async def coletar_todos_discursos(deputados) -> list[dict]:
    timeout  = aiohttp.ClientTimeout(total=TIMEOUT_SEGUNDOS)
    semaforo = asyncio.Semaphore(MAX_CONCORRENCIA)
    total    = len(deputados)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tarefas    = [
            fetch_discursos_deputado(session, semaforo, d["id"])
            for d in deputados
        ]
        todos      = []
        concluidos = 0

        for coro in asyncio.as_completed(tarefas):
            lote = await coro
            todos.extend(lote)
            concluidos += 1
            if concluidos % 20 == 0 or concluidos == total:
                print(f"    [{concluidos}/{total}] deputados processados — {len(todos)} discursos coletados")

    return todos


# ──────────────────────────────────────────────
# 4. TRANSFORMAÇÃO DE DISCURSOS
# ──────────────────────────────────────────────

def tratar_discursos(brutos: list[dict]) -> pd.DataFrame:
    if not brutos:
        return pd.DataFrame()

    df = pd.DataFrame(brutos)

    for col in list(COLUNAS.keys()) + ["_id_deputado", "_ano"]:
        if col not in df.columns:
            df[col] = None

    df = df[list(COLUNAS.keys()) + ["_id_deputado", "_ano"]].copy()
    df = df.rename(columns=COLUNAS)
    df = df.rename(columns={"_id_deputado": "id_deputado", "_ano": "ano"})

    antes = len(df)

    df = df[df["data_hora_inicio"].notna() & (df["data_hora_inicio"] != "")]
    df = df.drop_duplicates(subset=["id_deputado", "data_hora_inicio"], keep="last")

    df["data_hora_inicio"] = pd.to_datetime(df["data_hora_inicio"], errors="coerce")
    df["data_hora_fim"]    = pd.to_datetime(df["data_hora_fim"],    errors="coerce")
    df["id_deputado"]      = df["id_deputado"].astype(int)
    df["ano"]              = df["ano"].astype(int)

    for col in ["tipo_discurso", "sumario", "keywords", "fase_evento", "transcricao", "uri_evento"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    print(f"   → {antes - len(df)} registros removidos (duplicados/inválidos)")
    print(f"   → {len(df)} discursos prontos para carga")
    return df


# ──────────────────────────────────────────────
# 5. CARGA DE DISCURSOS
# ──────────────────────────────────────────────

def salvar_discursos(df: pd.DataFrame, tamanho_lote=500) -> bool:
    if df.empty:
        print("  ⚠️  Nenhum discurso para salvar.")
        return False

    try:
        conn   = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"  ❌ Erro ao conectar no banco: {e}")
        return False

    registros = list(df[[
        "id_deputado", "ano", "data_hora_inicio", "data_hora_fim",
        "tipo_discurso", "sumario", "keywords",
        "fase_evento", "transcricao", "uri_evento",
    ]].itertuples(index=False, name=None))

    sql = """
        INSERT INTO discursos (
            id_deputado, ano, data_hora_inicio, data_hora_fim,
            tipo_discurso, sumario, keywords,
            fase_evento, transcricao, uri_evento
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            data_hora_fim = VALUES(data_hora_fim),
            sumario       = VALUES(sumario),
            keywords      = VALUES(keywords),
            transcricao   = VALUES(transcricao)
    """

    total_salvos = 0
    try:
        for i in range(0, len(registros), tamanho_lote):
            lote = registros[i:i + tamanho_lote]
            cursor.executemany(sql, lote)
            conn.commit()
            total_salvos += len(lote)
            print(f"    💾 {total_salvos}/{len(registros)} discursos salvos...")

        print(f"  ✅ {total_salvos} discursos salvos no banco")
        return True

    except Exception as e:
        conn.rollback()
        print(f"  ❌ Erro ao salvar discursos: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# 6. VÍNCULOS DISCURSO × TEMA (via keywords)
#
# Estratégia: a API não expõe /discursos/{id}/temas.
# Fazemos matching entre as keywords do discurso e o nome do tema.
# Ex: keywords "educação; ensino médio" → tema "Educação" (cod 46)
#
# O match é case-insensitive e verifica se o nome do tema aparece
# em qualquer parte da string de keywords ou do sumário.
# ──────────────────────────────────────────────

def buscar_ids_discursos_do_banco() -> list[dict]:
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, keywords, sumario FROM discursos")
    discursos = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"  ✅ {len(discursos)} discursos encontrados no banco")
    return discursos


def gerar_vinculos_discursos_temas(
    discursos: list[dict],
    temas: list[dict],
) -> pd.DataFrame:
    """
    Para cada discurso, verifica quais temas têm o nome presente
    nas keywords ou no sumário. Retorna DataFrame com
    (id_discurso, cod_tema).
    """
    if not discursos or not temas:
        return pd.DataFrame()

    # Pré-processa temas: cod como str para bater com temas.cod (VARCHAR 20)
    temas_prep = [(str(t["cod"]).strip(), t["nome"].strip().lower()) for t in temas]

    vinculos = []
    for disc in discursos:
        id_disc = disc["id"]
        texto = " ".join([
            (disc.get("keywords") or ""),
            (disc.get("sumario")  or ""),
        ]).lower()

        if not texto.strip():
            continue

        for cod, nome_tema in temas_prep:
            if not nome_tema:
                continue
            # Aceita se qualquer palavra significativa do tema (>= 4 chars)
            # aparecer no texto — cobre "Educação" dentro de "Educação especial"
            palavras = [p for p in nome_tema.split() if len(p) >= 4]
            if palavras and any(p in texto for p in palavras):
                vinculos.append({"id_discurso": id_disc, "cod_tema": cod})

    df = pd.DataFrame(vinculos) if vinculos else pd.DataFrame(columns=["id_discurso", "cod_tema"])
    df = df.drop_duplicates(subset=["id_discurso", "cod_tema"], keep="last")

    print(f"   → {len(df)} vínculos discurso×tema gerados")
    return df


def salvar_discursos_temas(df: pd.DataFrame, tamanho_lote=500) -> bool:
    if df.empty:
        print("  ⚠️  Nenhum vínculo para salvar.")
        return False

    try:
        conn   = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"  ❌ Erro ao conectar no banco: {e}")
        return False

    registros = list(df[["id_discurso", "cod_tema"]].itertuples(index=False, name=None))

    sql = """
        INSERT IGNORE INTO discursos_temas (id_discurso, cod_tema)
        VALUES (%s, %s)
    """

    total_salvos = 0
    try:
        for i in range(0, len(registros), tamanho_lote):
            lote = registros[i:i + tamanho_lote]
            cursor.executemany(sql, lote)
            conn.commit()
            total_salvos += len(lote)
            print(f"    💾 {total_salvos}/{len(registros)} vínculos salvos...")

        print(f"  ✅ {total_salvos} vínculos discurso×tema salvos")
        return True

    except Exception as e:
        conn.rollback()
        print(f"  ❌ Erro ao salvar vínculos: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# 7. MAIN
# ──────────────────────────────────────────────

def main():
    print("🚀 Iniciando carga de discursos e temas...\n")
    t0 = time.perf_counter()

    # ── Etapa 1 — Discursos
    print("=" * 55)
    print("  ETAPA 1 — Discursos dos deputados")
    print("=" * 55)

    deputados = buscar_deputados_do_banco()
    if not deputados:
        print("❌ Nenhum deputado no banco. Rode o ETL de deputados primeiro.")
        return

    print(f"\n📡 Coletando discursos de {len(deputados)} deputados ({ANOS})...")
    brutos = asyncio.run(coletar_todos_discursos(deputados))
    print(f"   → {len(brutos)} registros brutos coletados")

    if not brutos:
        print("❌ Nenhum discurso coletado. Abortando.")
        return

    print(f"\n🧠 Tratando discursos...")
    df_discursos = tratar_discursos(brutos)

    print(f"\n💾 Salvando discursos...")
    sucesso = salvar_discursos(df_discursos)

    if not sucesso:
        print("❌ Falha ao salvar discursos. Abortando etapa de vínculos.")
        return

    # ── Etapa 2 — Temas (lê do banco, já populado pelo etl_proposicoes)
    print("\n" + "=" * 55)
    print("  ETAPA 2 — Temas de referência (do banco)")
    print("=" * 55)

    temas = buscar_temas_do_banco()
    if not temas:
        print("❌ Nenhum tema no banco. Rode o ETL de proposições primeiro.")
        return

    # ── Etapa 3 — Vínculos discurso × tema
    print("\n" + "=" * 55)
    print("  ETAPA 3 — Vínculos discurso × tema")
    print("=" * 55)

    discursos_banco = buscar_ids_discursos_do_banco()

    print(f"\n🧠 Gerando vínculos por keywords/sumário...")
    df_vinculos = gerar_vinculos_discursos_temas(discursos_banco, temas)

    print(f"\n💾 Salvando vínculos...")
    salvar_discursos_temas(df_vinculos)

    elapsed = time.perf_counter() - t0
    print(f"\n✅ Tudo concluído em {elapsed:.1f}s")


if __name__ == "__main__":
    main()