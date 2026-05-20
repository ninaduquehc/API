import asyncio
import aiohttp
import time
import pandas as pd
from database.connection import get_connection

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
ANOS = [2023, 2024, 2025]
ITENS_POR_PAGINA = 100
MAX_CONCORRENCIA = 20
TIMEOUT_SEGUNDOS = 30

COLUNAS = {
    "codDocumento":      "id_documento",
    "ano":               "ano",
    "mes":               "mes",
    "tipoDespesa":       "tipo_despesa",
    "valorDocumento":    "valor",
    "nomeFornecedor":    "nome_fornecedor",
    "cnpjCpfFornecedor": "cnpj_cpf_fornecedor",
    "dataDocumento":     "data_documento",
    "numDocumento":      "num_documento",
    "urlDocumento":      "url_documento",
}


def buscar_deputados_do_banco():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nome FROM deputados ORDER BY nome")
    deputados = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"  ✅ {len(deputados)} deputados encontrados no banco")
    return deputados


async def fetch_pagina(session, semaforo, id_deputado, ano, pagina):
    url = f"{BASE_URL}/deputados/{id_deputado}/despesas"
    params = {"ano": ano, "itens": ITENS_POR_PAGINA, "pagina": pagina}

    async with semaforo:
        for tentativa in range(3):
            try:
                async with session.get(url, params=params) as res:
                    if res.status == 429:
                        await asyncio.sleep(2 ** tentativa)
                        continue
                    if res.status != 200:
                        return []
                    data = await res.json(content_type=None)
                    dados = data.get("dados", [])
                    for d in dados:
                        d["_id_deputado"] = id_deputado
                    return dados
            except Exception as e:
                print(f"    ⚠️  Erro ({id_deputado}/ano {ano}/p{pagina}): {e}")
                await asyncio.sleep(1)
        return []


async def fetch_despesas_deputado(session, semaforo, id_deputado, nome):
    todas = []

    for ano in ANOS:
        primeira = await fetch_pagina(session, semaforo, id_deputado, ano, 1)
        todas.extend(primeira)

        if len(primeira) < ITENS_POR_PAGINA:
            continue

        tarefas = [
            fetch_pagina(session, semaforo, id_deputado, ano, p)
            for p in range(2, 21)
        ]
        resultados = await asyncio.gather(*tarefas)

        for lote in resultados:
            todas.extend(lote)
            if len(lote) < ITENS_POR_PAGINA:
                break

    return todas


async def coletar_todas_despesas(deputados):
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SEGUNDOS)
    semaforo = asyncio.Semaphore(MAX_CONCORRENCIA)
    total = len(deputados)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tarefas = [
            fetch_despesas_deputado(session, semaforo, d["id"], d["nome"])
            for d in deputados
        ]

        todas = []
        concluidos = 0

        for coro in asyncio.as_completed(tarefas):
            lote = await coro
            todas.extend(lote)
            concluidos += 1
            if concluidos % 20 == 0 or concluidos == total:
                print(f"    [{concluidos}/{total}] deputados processados — {len(todas)} despesas coletadas")

    return todas


def tratar_despesas(brutos):
    if not brutos:
        return pd.DataFrame()

    df = pd.DataFrame(brutos)

    for col in list(COLUNAS.keys()) + ["_id_deputado"]:
        if col not in df.columns:
            df[col] = None

    df = df[list(COLUNAS.keys()) + ["_id_deputado"]].copy()
    df = df.rename(columns=COLUNAS)
    df = df.rename(columns={"_id_deputado": "id_deputado"})

    antes = len(df)

    mask_com_id = df["id_documento"].notna() & (df["id_documento"] != 0) & (df["id_documento"] != "")
    df_com_id = df[mask_com_id].drop_duplicates(subset=["id_documento"], keep="last")
    df_sem_id = df[~mask_com_id]
    df = pd.concat([df_com_id, df_sem_id], ignore_index=True)

    df = df[df["valor"].notna() & (df["valor"] != 0)]

    df["data_documento"] = pd.to_datetime(df["data_documento"], errors="coerce").dt.date

    for col in ["tipo_despesa", "nome_fornecedor", "cnpj_cpf_fornecedor", "num_documento", "url_documento"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["id_documento"] = df["id_documento"].apply(
        lambda x: str(x).strip() if pd.notna(x) and str(x).strip() != "" else None
    )

    print(f"   → {antes - len(df)} registros removidos (duplicados/inválidos)")
    print(f"   → {len(df)} despesas prontas para carga")
    return df


def salvar_despesas(df, tamanho_lote=500):
    if df.empty:
        print("  ⚠️  Nenhuma despesa para salvar.")
        return False

    try:
        conn = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"  ❌ Erro ao conectar no banco: {e}")
        return False

    registros = list(df[[
        "id_deputado", "ano", "mes", "tipo_despesa", "valor",
        "nome_fornecedor", "cnpj_cpf_fornecedor", "data_documento",
        "num_documento", "url_documento", "id_documento"
    ]].itertuples(index=False, name=None))

    sql = """
        INSERT INTO despesas (
            id_deputado, ano, mes, tipo_despesa, valor,
            nome_fornecedor, cnpj_cpf_fornecedor, data_documento,
            num_documento, url_documento, id_documento
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            valor               = VALUES(valor),
            nome_fornecedor     = VALUES(nome_fornecedor),
            cnpj_cpf_fornecedor = VALUES(cnpj_cpf_fornecedor),
            data_documento      = VALUES(data_documento),
            url_documento       = VALUES(url_documento)
    """

    total_salvos = 0
    try:
        for i in range(0, len(registros), tamanho_lote):
            lote = registros[i:i + tamanho_lote]
            cursor.executemany(sql, lote)
            conn.commit()
            total_salvos += len(lote)
            print(f"    💾 {total_salvos}/{len(registros)} despesas salvas...")

        print(f"  ✅ {total_salvos} despesas salvas no banco")
        return True

    except Exception as e:
        conn.rollback()
        print(f"  ❌ Erro ao salvar: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


def main():
    print("🚀 Iniciando carga de despesas...\n")
    t0 = time.perf_counter()

    print("🗄️  Buscando deputados no banco...")
    deputados = buscar_deputados_do_banco()
    if not deputados:
        print("❌ Nenhum deputado no banco. Rode o ETL de deputados primeiro.")
        return

    print(f"\n📡 Coletando despesas de {len(deputados)} deputados ({ANOS})...")
    brutos = asyncio.run(coletar_todas_despesas(deputados))
    print(f"   → {len(brutos)} registros brutos coletados")

    if not brutos:
        print("❌ Nenhuma despesa coletada. Abortando.")
        return

    print(f"\n🧠 Tratando dados...")
    df = tratar_despesas(brutos)

    print(f"\n💾 Salvando no banco em lotes...")
    sucesso = salvar_despesas(df)

    elapsed = time.perf_counter() - t0
    if sucesso:
        print(f"\n✅ Concluído em {elapsed:.1f}s")
    else:
        print(f"\n❌ Carga falhou. Verifique os erros acima.")


if __name__ == "__main__":
    main()