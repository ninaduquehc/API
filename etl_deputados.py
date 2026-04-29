import requests
import time
import pandas as pd
from database.connection import get_connection

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

    finally:
        cursor.close()
        conn.close()


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


if __name__ == "__main__":
    main()