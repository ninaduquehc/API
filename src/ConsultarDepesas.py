import requests
import pandas as pd

# pega deputados
dados = requests.get("https://dadosabertos.camara.leg.br/api/v2/deputados")
respostas = dados.json()
deputados = respostas["dados"]

lista_dados = []

# pega deputados
for deputado in deputados[:5]:

    idDeputado = deputado["id"]
    nome = deputado["nome"]
    email = deputado.get("email")
    uf = deputado.get("siglaUf")

    print("Nome:", nome)

    # consulta despesas
    despesas_req = requests.get(
        f"https://dadosabertos.camara.leg.br/api/v2/deputados/{idDeputado}/despesas"
    )

    despesas = despesas_req.json()["dados"]

    total = 0

    for despesa in despesas:
        valor = despesa["valorLiquido"] or 0
        total += float(valor)

    total = round(total, 2)

    print("Total gasto:", total)
    print("=" * 40)

    # salva os dados
    lista_dados.append({
        "id": idDeputado,
        "nome": nome,
        "email": email,
        "siglaUf": uf,
        "despesa": total
    })


# ===============================
# LIMPEZA DE DADOS COM PANDAS
# ===============================

df = pd.DataFrame(lista_dados)

# remover emails vazios
df = df[df['email'].notna() & (df['email'] != "")]

# converter despesa para número
df['despesa'] = pd.to_numeric(df['despesa'], errors='coerce')

# remover valores inválidos
df = df[df['despesa'].notna()]

# remover duplicados
df = df.drop_duplicates(subset='id')

# padronizar UF
df['siglaUf'] = df['siglaUf'].str.upper()

# estatísticas
print("\nEstatísticas das despesas:")
print(df['despesa'].describe())

# ranking
print("\nRanking de gastos:")
print(df.sort_values(by="despesa", ascending=False))