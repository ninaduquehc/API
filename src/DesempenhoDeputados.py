import requests
import pandas as pd

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

def get_json(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


# deputados
resposta = get_json(f"{BASE_URL}/deputados")
deputados = resposta["dados"] if resposta else []

# votações
votacoes_resp = get_json(f"{BASE_URL}/votacoes", params={"itens": 100})
votacoes = votacoes_resp["dados"] if votacoes_resp else []

# votos
lista_votos = {}

for vot in votacoes:
    vot_id = vot.get("id")

    votos_resp = get_json(f"{BASE_URL}/votacoes/{vot_id}/votos")
    if not votos_resp:
        continue

    votos = votos_resp.get("dados", [])

    for v in votos:
        dep_id = (v.get("deputado") or {}).get("id")

        if dep_id is not None:
            lista_votos[dep_id] = lista_votos.get(dep_id, 0) + 1


# análise
dados_analise = []

for deputado in deputados:
    idDeputado = deputado.get("id")
    nome = deputado.get("nome")

    despesas_resp = get_json(f"{BASE_URL}/deputados/{idDeputado}/despesas")
    despesas = despesas_resp.get("dados", []) if despesas_resp else []
    total_gasto = sum(float(d.get("valorLiquido") or 0) for d in despesas)
    total_gasto = round(total_gasto, 2)

    participacoes = lista_votos.get(idDeputado, 0)

    dados_analise.append({
        "nome": nome,
        "total_gasto": total_gasto,
        "participacoes": participacoes
    })


# pandas
df = pd.DataFrame(dados_analise)

df["score"] = (df["total_gasto"] / 1000) + (df["participacoes"] * 10)

df = df.sort_values(by="score", ascending=False)

print("Classificação de desempenho geral:")

for _, row in df.iterrows():
    print(f"{row['nome']} - Score {row['score']:.2f}")