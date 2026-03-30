import requests
import pandas as pd
import matplotlib.pyplot as plt


# DEPUTADOS
dados = requests.get(
    "https://dadosabertos.camara.leg.br/api/v2/deputados"
)

deputados = dados.json()["dados"]

df_dep = pd.DataFrame(deputados)


# EVENTOS
eventos_req = requests.get(
    "https://dadosabertos.camara.leg.br/api/v2/eventos?itens=50"
)

eventos = eventos_req.json()["dados"]

participacoes = []


# PEGAR DEPUTADOS EM CADA EVENTO
for evento in eventos:

    id_evento = evento["id"]

    dep_evento = requests.get(
        f"https://dadosabertos.camara.leg.br/api/v2/eventos/{id_evento}/deputados"
    )

    deputados_evento = dep_evento.json()["dados"]

    for d in deputados_evento:

        participacoes.append(d["id"])


# DATAFRAME
df_pres = pd.DataFrame(participacoes, columns=["idDeputado"])

ranking = df_pres.value_counts().reset_index()
ranking.columns = ["idDeputado", "presencas"]

# juntar com nomes

ranking = ranking.merge(
    df_dep[["id", "nome"]],
    left_on="idDeputado",
    right_on="id"
)


# TOP E BOTTOM
top = ranking.sort_values("presencas", ascending=False).head(10)
bottom = ranking.sort_values("presencas", ascending=True).head(10)


# GRAFICO TOP
plt.figure(figsize=(12,6))

plt.bar(top["nome"], top["presencas"])

plt.xticks(rotation=45, ha="right")

for i, v in enumerate(top["presencas"]):
    plt.text(i, v + 0.5, str(v), ha="center")

plt.title("Deputados com MAIS presenças em eventos")
plt.ylabel("Número de presenças")

plt.tight_layout()
plt.show()


# GRAFICO BOTTOM
plt.figure(figsize=(12,6))

plt.bar(bottom["nome"], bottom["presencas"])

plt.xticks(rotation=45, ha="right")

for i, v in enumerate(bottom["presencas"]):
    plt.text(i, v + 0.5, str(v), ha="center")

plt.title("Deputados com MENOS presenças em eventos")
plt.ylabel("Número de presenças")

plt.tight_layout()
plt.show()