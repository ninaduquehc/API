import asyncio
import aiohttp
import time
import requests
import pandas as pd
from database.connection import get_connection

BASE_URL         = "https://dadosabertos.camara.leg.br/api/v2"
ANOS             = [2023, 2024, 2025]
TIPOS_ALVO       = ["PL", "PDC", "PEC"]
ITENS_POR_PAGINA = 100
MAX_CONCORRENCIA = 20
TIMEOUT_SEGUNDOS = 30


# ──────────────────────────────────────────────
# 1. BUSCA DEPUTADOS DO BANCO
# ──────────────────────────────────────────────
def buscar_deputados_do_banco():
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nome FROM deputados ORDER BY nome")
    deputados = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"  ✅ {len(deputados)} deputados encontrados no banco")
    return deputados


# ──────────────────────────────────────────────
# 2. TEMAS — SÍNCRONO (endpoint simples)
# ──────────────────────────────────────────────
def coletar_temas():
    print("  📡 Buscando temas da API...")
    try:
        res = requests.get(
            f"{BASE_URL}/referencias/proposicoes/codTema",
            timeout=15
        )
        res.raise_for_status()
        dados = res.json().get("dados", [])
        print(f"  ✅ {len(dados)} temas encontrados")
        return dados
    except Exception as e:
        print(f"  ❌ Erro ao buscar temas: {e}")
        return []


def tratar_temas(brutos):
    if not brutos:
        return pd.DataFrame()

    df = pd.DataFrame(brutos)

    for col in ["cod", "nome"]:
        if col not in df.columns:
            df[col] = None

    df = df[["cod", "nome"]].copy()

    df = df.dropna(subset=["cod", "nome"])
    df = df.drop_duplicates(subset=["cod"], keep="last")

    df["cod"]  = df["cod"].astype(str).str.strip()
    df["nome"] = df["nome"].astype(str).str.strip()

    print(f"   → {len(df)} temas prontos para carga")
    return df


def salvar_temas(df):
    if df.empty:
        print("  ⚠️  Nenhum tema para salvar.")
        return False

    try:
        conn   = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"  ❌ Erro ao conectar no banco: {e}")
        return False

    registros = list(df[["cod", "nome"]].itertuples(index=False, name=None))

    sql = """
        INSERT INTO temas (cod, nome)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            nome = VALUES(nome)
    """

    try:
        cursor.executemany(sql, registros)
        conn.commit()
        print(f"  ✅ {len(registros)} temas salvos no banco")
        return True
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Erro ao salvar temas: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# 3. TEMAS POR PROPOSIÇÃO — ASSÍNCRONO
# ──────────────────────────────────────────────
async def fetch_temas_proposicao(session, semaforo, id_proposicao):
    url = f"{BASE_URL}/proposicoes/{id_proposicao}/temas"

    async with semaforo:
        for tentativa in range(3):
            try:
                async with session.get(url) as res:
                    if res.status == 429:
                        await asyncio.sleep(2 ** tentativa)
                        continue
                    if res.status != 200:
                        return []
                    data  = await res.json(content_type=None)
                    dados = data.get("dados", [])
                    for d in dados:
                        d["_id_proposicao"] = id_proposicao
                    return dados
            except Exception:
                await asyncio.sleep(1)
        return []


async def coletar_temas_proposicoes(ids_proposicoes):
    timeout  = aiohttp.ClientTimeout(total=TIMEOUT_SEGUNDOS)
    semaforo = asyncio.Semaphore(MAX_CONCORRENCIA)
    total    = len(ids_proposicoes)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tarefas    = [fetch_temas_proposicao(session, semaforo, pid) for pid in ids_proposicoes]
        todas      = []
        concluidos = 0

        for coro in asyncio.as_completed(tarefas):
            lote = await coro
            todas.extend(lote)
            concluidos += 1
            if concluidos % 100 == 0 or concluidos == total:
                print(f"    [{concluidos}/{total}] proposições consultadas — {len(todas)} vínculos coletados")

    return todas


def tratar_proposicoes_temas(brutos):
    if not brutos:
        return pd.DataFrame()

    df = pd.DataFrame(brutos)

    for col in ["_id_proposicao", "cod", "nome"]:
        if col not in df.columns:
            df[col] = None

    df = df[["_id_proposicao", "cod", "nome"]].copy()
    df = df.rename(columns={"_id_proposicao": "id_proposicao"})

    df = df.dropna(subset=["id_proposicao", "cod"])
    df = df.drop_duplicates(subset=["id_proposicao", "cod"], keep="last")

    df["id_proposicao"] = df["id_proposicao"].astype(int)
    df["cod"]           = df["cod"].astype(str).str.strip()
    df["nome"]          = df["nome"].fillna("").astype(str).str.strip()

    print(f"   → {len(df)} vínculos proposição×tema prontos para carga")
    return df


def salvar_proposicoes_temas(df, tamanho_lote=500):
    if df.empty:
        print("  ⚠️  Nenhum vínculo para salvar.")
        return False

    try:
        conn   = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"  ❌ Erro ao conectar no banco: {e}")
        return False

    registros = list(df[["id_proposicao", "cod"]].itertuples(index=False, name=None))

    sql = """
        INSERT IGNORE INTO proposicoes_temas (id_proposicao, cod_tema)
        VALUES (%s, %s)
    """

    total_salvos = 0
    try:
        for i in range(0, len(registros), tamanho_lote):
            lote = registros[i:i + tamanho_lote]
            cursor.executemany(sql, lote)
            conn.commit()
            total_salvos += len(lote)
            print(f"    💾 {total_salvos}/{len(registros)} vínculos salvos…")

        print(f"  ✅ {total_salvos} vínculos proposição×tema salvos")
        return True
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Erro ao salvar vínculos: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def buscar_ids_proposicoes_do_banco():
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM proposicoes")
    ids = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    print(f"  ✅ {len(ids)} proposições encontradas no banco")
    return ids


# ──────────────────────────────────────────────
# 4. COLETA ASSÍNCRONA DE PROPOSIÇÕES
# ──────────────────────────────────────────────
async def fetch_pagina(session, semaforo, id_deputado, tipo, ano, pagina):
    url    = f"{BASE_URL}/proposicoes"
    params = {
        "siglaTipo":       tipo,
        "ano":             ano,
        "idDeputadoAutor": id_deputado,
        "itens":           ITENS_POR_PAGINA,
        "pagina":          pagina,
        "ordenarPor":      "id",
        "ordem":           "DESC",
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
                    return dados
            except Exception as e:
                print(f"    ⚠️  Erro ({id_deputado}/{tipo}/{ano}/p{pagina}): {e}")
                await asyncio.sleep(1)
        return []


async def fetch_detalhe(session, semaforo, id_proposicao):
    url = f"{BASE_URL}/proposicoes/{id_proposicao}"

    async with semaforo:
        for tentativa in range(3):
            try:
                async with session.get(url) as res:
                    if res.status == 429:
                        await asyncio.sleep(2 ** tentativa)
                        continue
                    if res.status != 200:
                        return {}
                    data = await res.json(content_type=None)
                    return data.get("dados", {})
            except Exception:
                await asyncio.sleep(1)
        return {}


async def fetch_proposicoes_deputado(session, semaforo, id_deputado):
    todas = []

    for tipo in TIPOS_ALVO:
        for ano in ANOS:
            primeira = await fetch_pagina(session, semaforo, id_deputado, tipo, ano, 1)
            todas.extend(primeira)

            if len(primeira) < ITENS_POR_PAGINA:
                continue

            tarefas    = [
                fetch_pagina(session, semaforo, id_deputado, tipo, ano, p)
                for p in range(2, 21)
            ]
            resultados = await asyncio.gather(*tarefas)

            for lote in resultados:
                todas.extend(lote)
                if len(lote) < ITENS_POR_PAGINA:
                    break

    return todas


async def enriquecer_detalhes(session, semaforo, proposicoes):
    ids     = [p["id"] for p in proposicoes]
    tarefas = [fetch_detalhe(session, semaforo, pid) for pid in ids]

    detalhes = await asyncio.gather(*tarefas)
    mapa     = {d["id"]: d for d in detalhes if d.get("id")}

    for p in proposicoes:
        det = mapa.get(p["id"], {})
        p["keywords"]       = det.get("keywords", "")
        p["situacao"]       = det.get("statusProposicao", {}).get("descricaoSituacao", "")
        p["urlInteiroTeor"] = det.get("urlInteiroTeor", "")

    return proposicoes


async def coletar_todas_proposicoes(deputados):
    timeout  = aiohttp.ClientTimeout(total=TIMEOUT_SEGUNDOS)
    semaforo = asyncio.Semaphore(MAX_CONCORRENCIA)
    total    = len(deputados)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        tarefas    = [
            fetch_proposicoes_deputado(session, semaforo, d["id"])
            for d in deputados
        ]
        todas      = []
        concluidos = 0

        for coro in asyncio.as_completed(tarefas):
            lote = await coro
            todas.extend(lote)
            concluidos += 1
            if concluidos % 20 == 0 or concluidos == total:
                print(f"    [{concluidos}/{total}] deputados processados — {len(todas)} proposições coletadas")

        if not todas:
            return []

        print(f"\n  🔍 Enriquecendo {len(todas)} proposições com detalhes…")
        todas = await enriquecer_detalhes(session, semaforo, todas)

    return todas


# ──────────────────────────────────────────────
# 5. TRANSFORMAÇÃO DE PROPOSIÇÕES
# ──────────────────────────────────────────────
def tratar_proposicoes(brutos):
    if not brutos:
        return pd.DataFrame()

    df = pd.DataFrame(brutos)

    for col in ["id", "siglaTipo", "numero", "ano", "ementa",
                "keywords", "situacao", "urlInteiroTeor", "_id_deputado"]:
        if col not in df.columns:
            df[col] = None

    df = df[[
        "id", "_id_deputado", "siglaTipo", "numero", "ano",
        "ementa", "keywords", "situacao", "urlInteiroTeor"
    ]].copy()

    df = df.rename(columns={
        "_id_deputado":   "id_deputado",
        "siglaTipo":      "sigla_tipo",
        "urlInteiroTeor": "url_inteiro_teor",
    })

    antes = len(df)
    df    = df.dropna(subset=["id", "id_deputado"])
    df    = df.drop_duplicates(subset=["id"], keep="last")

    for col in ["sigla_tipo", "ementa", "keywords", "situacao", "url_inteiro_teor"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["id"]          = df["id"].astype(int)
    df["id_deputado"] = df["id_deputado"].astype(int)
    df["numero"]      = pd.to_numeric(df["numero"], errors="coerce").fillna(0).astype(int)
    df["ano"]         = pd.to_numeric(df["ano"],    errors="coerce").fillna(0).astype(int)
    df                = df[df["sigla_tipo"].isin(TIPOS_ALVO)]

    print(f"   → {antes - len(df)} registros removidos (duplicados/inválidos)")
    print(f"   → {len(df)} proposições prontas para carga")
    return df


# ──────────────────────────────────────────────
# 6. CARGA DE PROPOSIÇÕES EM LOTES
# ──────────────────────────────────────────────
def salvar_proposicoes(df, tamanho_lote=500):
    if df.empty:
        print("  ⚠️  Nenhuma proposição para salvar.")
        return False

    try:
        conn   = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"  ❌ Erro ao conectar no banco: {e}")
        return False

    registros = list(df[[
        "id", "id_deputado", "sigla_tipo", "numero", "ano",
        "ementa", "keywords", "situacao", "url_inteiro_teor"
    ]].itertuples(index=False, name=None))

    sql = """
        INSERT INTO proposicoes (
            id, id_deputado, sigla_tipo, numero, ano,
            ementa, keywords, situacao, url_inteiro_teor
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            sigla_tipo       = VALUES(sigla_tipo),
            numero           = VALUES(numero),
            ano              = VALUES(ano),
            ementa           = VALUES(ementa),
            keywords         = VALUES(keywords),
            situacao         = VALUES(situacao),
            url_inteiro_teor = VALUES(url_inteiro_teor)
    """

    total_salvos = 0
    try:
        for i in range(0, len(registros), tamanho_lote):
            lote = registros[i:i + tamanho_lote]
            cursor.executemany(sql, lote)
            conn.commit()
            total_salvos += len(lote)
            print(f"    💾 {total_salvos}/{len(registros)} proposições salvas…")

        print(f"  ✅ {total_salvos} proposições salvas no banco")
        return True
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Erro ao salvar: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# 7. MAIN
# ──────────────────────────────────────────────
def main():
    print("🚀 Iniciando carga de proposições e temas...\n")
    t0 = time.perf_counter()

    # ── Temas de referência
    print("=" * 55)
    print("  ETAPA 1 — Temas de referência")
    print("=" * 55)
    brutos_temas = coletar_temas()
    df_temas     = tratar_temas(brutos_temas)
    salvar_temas(df_temas)

    # ── Proposições
    print("\n" + "=" * 55)
    print("  ETAPA 2 — Proposições dos deputados")
    print("=" * 55)
    deputados = buscar_deputados_do_banco()
    if not deputados:
        print("❌ Nenhum deputado no banco. Rode o ETL de deputados primeiro.")
        return

    print(f"\n📡 Coletando proposições de {len(deputados)} deputados — tipos: {TIPOS_ALVO} | anos: {ANOS}...")
    brutos_props = asyncio.run(coletar_todas_proposicoes(deputados))
    print(f"   → {len(brutos_props)} registros brutos coletados")

    if not brutos_props:
        print("❌ Nenhuma proposição coletada. Abortando.")
        return

    print(f"\n🧠 Tratando proposições...")
    df_props = tratar_proposicoes(brutos_props)

    print(f"\n💾 Salvando proposições...")
    sucesso_props = salvar_proposicoes(df_props)

    if not sucesso_props:
        print("❌ Falha ao salvar proposições. Abortando etapa de temas.")
        return

    # ── Vínculos proposição × tema
    print("\n" + "=" * 55)
    print("  ETAPA 3 — Vínculos proposição × tema")
    print("=" * 55)
    ids_proposicoes = buscar_ids_proposicoes_do_banco()

    print(f"\n📡 Coletando temas de {len(ids_proposicoes)} proposições...")
    brutos_vinculos = asyncio.run(coletar_temas_proposicoes(ids_proposicoes))
    print(f"   → {len(brutos_vinculos)} vínculos brutos coletados")

    print(f"\n🧠 Tratando vínculos...")
    df_vinculos = tratar_proposicoes_temas(brutos_vinculos)

    print(f"\n💾 Salvando vínculos...")
    salvar_proposicoes_temas(df_vinculos)

    elapsed = time.perf_counter() - t0
    print(f"\n✅ Tudo concluído em {elapsed:.1f}s")


if __name__ == "__main__":
    main()