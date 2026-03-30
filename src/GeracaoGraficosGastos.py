import requests
import matplotlib.pyplot as plt
import pandas as pd

dados = requests.get("https://dadosabertos.camara.leg.br/api/v2/deputados")
respostas = dados.json()
deputados = respostas["dados"]

gastos_deputados = {}

for deputado in deputados[:8]:

    idDeputado = deputado["id"]
    nome = deputado["nome"]

    print("Nome:", nome)


    despesas_req = requests.get(
        f"https://dadosabertos.camara.leg.br/api/v2/deputados/{idDeputado}/despesas"
    )

    despesas = despesas_req.json()["dados"]

    total = 0

    for despesa in despesas:
        valor = despesa["valorLiquido"] or 0
        total += float(valor)
        total = round(total, 2)

    gastos_deputados[nome] = total

    print("Total gasto:", total)
    print("=" * 40)

df = pd.DataFrame(list(gastos_deputados.items()), columns=["Deputado", "Gastos"])

df = df.sort_values(by="Gastos", ascending=False)

plt.figure()
plt.bar(df["Deputado"], df["Gastos"])

plt.title("Gastos por Deputado")
plt.xlabel("Deputados")
plt.ylabel("Total gasto (R$)")

plt.xticks(rotation=45)

plt.show()