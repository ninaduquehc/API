import requests
import time
import pandas as pd
from database.connection import get_connection

<<<<<<< HEAD
BASE_URL = "https://dadosabertos.camara.leg.br/api/v2/deputados"
LEGISLATURA_ATUAL = 57
ITENS_POR_PAGINA = 100
TIMEOUT = 20

COLUNAS = {
    "id": "id",
    "nome": "nome",
    "siglaPartido": "sigla_partido",
    "siglaUf": "sigla_uf",
    "urlFoto": "url_foto",
    "email": "email",
}


def coletar_deputados():
    todos, pagina = [], 1

    while True:
        print(f"  Buscando página {pagina}...")
        try:
            res = requests.get(BASE_URL, params={
                "idLegislatura": LEGISLATURA_ATUAL,
                "pagina": pagina,
                "itens": ITENS_POR_PAGINA,
                "ordem": "ASC",
                "ordenarPor": "nome",
            }, timeout=TIMEOUT)
            res.raise_for_status()

        except requests.exceptions.ConnectionError:
            print("  ❌ Sem conexão com a internet.")
            return []
        except requests.exceptions.Timeout:
            print(f"  ⚠️  Timeout na página {pagina}. Tentando em 5s...")
            time.sleep(5)
            continue
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            return []

        data = res.json()
        dados = data.get("dados", [])
        if not dados:
            break

        todos.extend(dados)
        tem_proxima = any(l.get("rel") == "next" for l in data.get("links", []))
        if not tem_proxima:
            break

        pagina += 1
        time.sleep(0.3)

    return todos


def tratar_deputados(brutos):
    df = pd.DataFrame(brutos)[list(COLUNAS.keys())].rename(columns=COLUNAS)

    antes = len(df)
    df = df.dropna(subset=["id", "nome"])
    df = df.drop_duplicates(subset=["id"], keep="last")
    df = df.fillna("")

    print(f"   → {antes - len(df)} registros removidos (inválidos/duplicados)")
    return df


def salvar_deputados(df):
    try:
        conn = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"  ❌ Erro ao conectar no banco: {e}")
        return False

    try:
        cursor.executemany("""
            INSERT INTO deputados (id, nome, sigla_partido, sigla_uf, url_foto, email)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                nome          = VALUES(nome),
                sigla_partido = VALUES(sigla_partido),
                sigla_uf      = VALUES(sigla_uf),
                url_foto      = VALUES(url_foto),
                email         = VALUES(email)
        """, list(df.itertuples(index=False, name=None)))

        conn.commit()
        print(f"  ✅ {len(df)} deputados salvos no banco")
        return True

    except Exception as e:
        conn.rollback()
        print(f"  ❌ Erro ao salvar: {e}")
        return False

=======
BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
LEGISLATURA_ATUAL = 57
TIMEOUT = 20


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_com_retry(url, params=None, tentativas=3):
    for i in range(tentativas):
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            return r
        except requests.exceptions.Timeout:
            print(f"    ⚠️  Timeout ({i+1}/{tentativas}) em {url}")
            time.sleep(3)
        except requests.exceptions.ConnectionError:
            print("    ❌ Sem conexão com a internet.")
            return None
        except Exception as e:
            print(f"    ❌ Erro: {e}")
            return None
    return None


# ── Banco ─────────────────────────────────────────────────────────────────────

def buscar_deputados_sem_cargo() -> list[dict]:
    """
    Retorna apenas deputados cujo cargo_partido é NULL ou 'Membro',
    pois esses são os que precisam ser (re)verificados.
    Líderes e Vice-Líderes já confirmados são ignorados.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nome, sigla_partido
            FROM deputados
            WHERE cargo_partido IS NULL
               OR cargo_partido = ''
               OR cargo_partido = 'Membro'
        """)
        rows = cursor.fetchall()
        print(f"  📋 {len(rows)} deputados elegíveis para atualização de cargo.")
        return rows
    except Exception as e:
        print(f"  ❌ Erro ao buscar deputados: {e}")
        return []
>>>>>>> atualizacao-projeto-29-04
    finally:
        cursor.close()
        conn.close()


<<<<<<< HEAD
def main():
    print("🚀 Iniciando carga de deputados...\n")
    t0 = time.perf_counter()

    print("📡 Coletando da API...")
    brutos = coletar_deputados()
    if not brutos:
        print("❌ Nenhum dado coletado. Abortando.")
        return

    print(f"\n🧠 Tratando {len(brutos)} registros...")
    df = tratar_deputados(brutos)

    print(f"\n💾 Salvando {len(df)} deputados no banco...")
    sucesso = salvar_deputados(df)

    if sucesso:
        print(f"\n✅ Concluído em {time.perf_counter() - t0:.1f}s")
    else:
        print("\n❌ Carga falhou. Verifique os erros acima.")
=======
def salvar_cargos(cargos: dict[int, str]) -> bool:
    """
    Atualiza cargo_partido apenas para os ids recebidos.
    Nunca sobrescreve quem já tem um cargo diferente de NULL/''/Membro.
    """
    if not cargos:
        print("  ⚠️  Nenhum cargo para salvar.")
        return True

    registros = [(cargo, dep_id) for dep_id, cargo in cargos.items()]

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.executemany("""
            UPDATE deputados
            SET cargo_partido = %s
            WHERE id = %s
              AND (
                cargo_partido IS NULL
                OR cargo_partido = ''
                OR cargo_partido = 'Membro'
              )
        """, registros)
        conn.commit()
        print(f"  ✅ {cursor.rowcount} registros atualizados no banco.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Erro ao salvar cargos: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# ── Coleta ────────────────────────────────────────────────────────────────────

def coletar_cargos_partido(deputados: list[dict]) -> dict[int, str]:
    """
    Recebe lista de deputados com 'id' e 'sigla_partido'.
    Retorna {id_deputado: cargo} onde cargo é o título da API ou 'Membro'.
    Agrupa por partido para minimizar chamadas à API.
    """
    # Mapeia sigla → lista de ids
    por_partido: dict[str, list[int]] = {}
    for d in deputados:
        sigla = d.get("sigla_partido") or d.get("siglaPartido", "")
        if sigla:
            por_partido.setdefault(sigla, []).append(d["id"])

    cargos: dict[int, str] = {}
    total_partidos = len(por_partido)

    for i, (sigla, ids) in enumerate(por_partido.items(), 1):
        print(f"  [{i}/{total_partidos}] Partido {sigla} ({len(ids)} deputado(s))...")

        # 1. Descobrir o ID do partido pela sigla
        r = _get_com_retry(f"{BASE_URL}/partidos", params={
            "sigla": sigla,
            "itens": 1,
            "idLegislatura": LEGISLATURA_ATUAL,
        })
        if not r:
            continue

        dados_partido = r.json().get("dados", [])
        if not dados_partido:
            print(f"    ⚠️  Partido {sigla} não encontrado na API.")
            # Marca todos como Membro para não deixar NULL
            for dep_id in ids:
                cargos.setdefault(dep_id, "Membro")
            continue

        partido_id = dados_partido[0]["id"]

        # 2. Buscar líderes → mapeia id_deputado → título
        lideres_map: dict[int, str] = {}
        r_lid = _get_com_retry(
            f"{BASE_URL}/partidos/{partido_id}/lideres",
            params={"itens": 100},
        )
        if r_lid:
            for lider in r_lid.json().get("dados", []):
                lideres_map[lider["id"]] = lider.get("titulo", "Líder")

        # 3. Buscar membros
        membros_set: set[int] = set()
        r_mem = _get_com_retry(
            f"{BASE_URL}/partidos/{partido_id}/membros",
            params={"itens": 100},
        )
        if r_mem:
            for membro in r_mem.json().get("dados", []):
                membros_set.add(membro["id"])

        # 4. Atribuir cargo a cada deputado do partido
        for dep_id in ids:
            if dep_id in lideres_map:
                cargos[dep_id] = lideres_map[dep_id]
            elif dep_id in membros_set:
                cargos[dep_id] = "Membro"
            else:
                # Não apareceu em nenhum endpoint — assume Membro
                cargos[dep_id] = "Membro"

        lideres_encontrados = sum(1 for dep_id in ids if dep_id in lideres_map)
        if lideres_encontrados:
            print(f"    ✨ {lideres_encontrados} líder(es)/vice(s) encontrado(s).")

        time.sleep(0.5)

    return cargos


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("🚀 Iniciando atualização de cargos por partido...\n")
    t0 = time.perf_counter()

    print("🗄️  Buscando deputados sem cargo definido...")
    deputados = buscar_deputados_sem_cargo()
    if not deputados:
        print("✅ Nenhum deputado precisa de atualização. Banco já está completo.")
        return

    print(f"\n📡 Consultando API para {len(deputados)} deputado(s)...")
    cargos = coletar_cargos_partido(deputados)

    if not cargos:
        print("❌ Nenhum cargo coletado. Verifique a API.")
        return

    print(f"\n💾 Salvando {len(cargos)} cargo(s) no banco...")
    sucesso = salvar_cargos(cargos)

    elapsed = time.perf_counter() - t0
    if sucesso:
        print(f"\n✅ Concluído em {elapsed:.1f}s")
    else:
        print(f"\n❌ Carga falhou. Verifique os erros acima.")
>>>>>>> atualizacao-projeto-29-04


if __name__ == "__main__":
    main()