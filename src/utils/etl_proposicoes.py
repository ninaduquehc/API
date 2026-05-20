"""
Repopula apenas a tabela proposicoes_temas.
Rode com: python etl_proposicoes_temas.py
"""
import asyncio
import aiohttp
import time
from database.connection import get_connection

BASE_URL         = "https://dadosabertos.camara.leg.br/api/v2"
MAX_CONCORRENCIA = 20
TIMEOUT_SEGUNDOS = 30


def buscar_ids_proposicoes_do_banco() -> list[int]:
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM proposicoes ORDER BY id")
    ids = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    print(f"  ✅ {len(ids)} proposições encontradas no banco")
    return ids


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


async def coletar_temas_proposicoes(ids: list[int]) -> list[dict]:
    timeout  = aiohttp.ClientTimeout(total=TIMEOUT_SEGUNDOS)
    semaforo = asyncio.Semaphore(MAX_CONCORRENCIA)
    total    = len(ids)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tarefas    = [fetch_temas_proposicao(session, semaforo, pid) for pid in ids]
        todas      = []
        concluidos = 0

        for coro in asyncio.as_completed(tarefas):
            lote = await coro
            todas.extend(lote)
            concluidos += 1
            if concluidos % 100 == 0 or concluidos == total:
                print(f"    [{concluidos}/{total}] proposições consultadas — {len(todas)} vínculos coletados")

    return todas


def salvar_proposicoes_temas(vinculos: list[dict], tamanho_lote=500) -> bool:
    if not vinculos:
        print("  ⚠️  Nenhum vínculo para salvar.")
        return False

    # Deduplica e normaliza
    vistos = set()
    registros = []
    for v in vinculos:
        id_prop  = v.get("_id_proposicao")
        cod_tema = str(v.get("cod", "")).strip()
        if id_prop and cod_tema and (id_prop, cod_tema) not in vistos:
            vistos.add((id_prop, cod_tema))
            registros.append((id_prop, cod_tema))

    print(f"   → {len(registros)} vínculos únicos prontos para carga")

    try:
        conn   = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"  ❌ Erro ao conectar: {e}")
        return False

    sql = "INSERT IGNORE INTO proposicoes_temas (id_proposicao, cod_tema) VALUES (%s, %s)"

    total_salvos = 0
    try:
        for i in range(0, len(registros), tamanho_lote):
            lote = registros[i:i + tamanho_lote]
            cursor.executemany(sql, lote)
            conn.commit()
            total_salvos += len(lote)
            print(f"    💾 {total_salvos}/{len(registros)} vínculos salvos...")

        print(f"  ✅ {total_salvos} vínculos proposição×tema salvos")
        return True
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Erro ao salvar: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def main():
    print("🚀 Repopulando proposicoes_temas...\n")
    t0 = time.perf_counter()

    ids = buscar_ids_proposicoes_do_banco()
    if not ids:
        print("❌ Nenhuma proposição no banco. Rode o etl_proposicoes.py primeiro.")
        return

    print(f"\n📡 Coletando temas de {len(ids)} proposições...")
    vinculos = asyncio.run(coletar_temas_proposicoes(ids))
    print(f"   → {len(vinculos)} vínculos brutos coletados")

    if not vinculos:
        print("❌ API não retornou nenhum vínculo.")
        print("   Verifique se o endpoint /proposicoes/{id}/temas está acessível.")
        return

    print(f"\n💾 Salvando vínculos...")
    salvar_proposicoes_temas(vinculos)

    elapsed = time.perf_counter() - t0
    print(f"\n✅ Concluído em {elapsed:.1f}s")


if __name__ == "__main__":
    main()