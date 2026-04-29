import requests
import time
import concurrent.futures
import pandas as pd
from database.connection import get_connection

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
ANO = 2024


def buscar_deputados():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, nome FROM deputados")
    dados = cursor.fetchall()

    cursor.close()
    conn.close()

    return dados


def calcular_presenca(dep):
    id_dep = dep["id"]

    url = f"{BASE_URL}/deputados/{id_dep}/eventos"

    params = {
        "dataInicio": f"{ANO}-01-01",
        "dataFim": f"{ANO}-12-31"
    }

    try:
        res = requests.get(url, params=params, timeout=20)
        res.raise_for_status()

        eventos = res.json().get("dados", [])

        if not eventos:
            return None

        total = len(eventos)
        presencas = 0

        for ev in eventos:
            texto = (
                ev.get("descricaoTipo", "") or
                ev.get("descricao", "") or
                ev.get("tipoEvento", "")
            )

            if "Deliberativa" in texto or "Reunião" in texto:
                presencas += 1

        faltas = total - presencas

        return {
            "id_deputado": id_dep,
            "ano": ANO,
            "total_eventos": total,
            "presencas": presencas,
            "faltas": faltas,
            "percentual_presenca": round((presencas / total) * 100, 2),
            "percentual_faltas": round((faltas / total) * 100, 2),
        }

    except:
        return None


def coletar_presencas(deputados):
    resultados = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(calcular_presenca, d) for d in deputados]

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            res = future.result()
            if res:
                resultados.append(res)

            if i % 20 == 0:
                print(f"  Processados: {i}")

    return resultados


def salvar(df):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO presencas (
            id_deputado, ano, total_eventos, presencas, faltas,
            percentual_presenca, percentual_faltas
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            total_eventos = VALUES(total_eventos),
            presencas = VALUES(presencas),
            faltas = VALUES(faltas),
            percentual_presenca = VALUES(percentual_presenca),
            percentual_faltas = VALUES(percentual_faltas)
    """

    dados = list(df.itertuples(index=False, name=None))

    cursor.executemany(sql, dados)
    conn.commit()

    cursor.close()
    conn.close()

    print(f"✅ {len(df)} registros salvos")


def main():
    print("🚀 ETL Presenças\n")

    deputados = buscar_deputados()
    print(f"{len(deputados)} deputados encontrados")

    dados = coletar_presencas(deputados)

    df = pd.DataFrame(dados)

    if df.empty:
        print("❌ Nenhum dado")
        return

    salvar(df)


if __name__ == "__main__":
    main()