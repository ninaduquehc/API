import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt

uf_filtro = input("Digite a UF (ou deixe vazio): ").strip().upper()
partido_filtro = input("Digite o partido (ou deixe vazio): ").strip().upper()
nome_filtro = input("Digite parte do nome (ou deixe vazio): ").strip().lower()


dados = requests.get("https://dadosabertos.camara.leg.br/api/v2/deputados")
respostas = dados.json()
deputados = respostas["dados"]


deputados_filtrados = []

for d in deputados:


    if d["idLegislatura"] != 57:
        continue

    if uf_filtro and d["siglaUf"] != uf_filtro:
        continue

    if partido_filtro and d["siglaPartido"] != partido_filtro:
        continue

    if nome_filtro and nome_filtro not in d["nome"].lower():
        continue

    deputados_filtrados.append(d)

if not deputados_filtrados:
    print("Nenhum deputado encontrado com esses filtros.")
else:
    print(f"\nTotal encontrados: {len(deputados_filtrados)}\n")

    for deputado in deputados_filtrados:

        print(" ========================================================= ")
        print("Nome:", deputado["nome"])
        print("Email:", deputado["email"])
        print("UF:", deputado["siglaUf"])
        print("Partido:", deputado["siglaPartido"])

        img_url = deputado["urlFoto"]
        resposta_img = requests.get(img_url)
        img = Image.open(BytesIO(resposta_img.content))

        plt.imshow(img)
        plt.axis("off")
        plt.show()