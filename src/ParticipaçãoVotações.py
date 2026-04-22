import requests
import time

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
data_inicio = "2023-02-01"


# 🔹 Função segura para requisições (evita erro JSON)
def get_json_seguro(url, params=None):
    try:
        resp = requests.get(url, params=params)

        if resp.status_code != 200:
            return None

        if not resp.text.strip():
            return None

        return resp.json()

    except:
        return None


# 🔹 Buscar deputados
def buscar_deputados():
    resp = get_json_seguro(f"{BASE_URL}/deputados")
    return resp.get("dados", []) if resp else []


# 🔹 Buscar todas votações
def buscar_votacoes(data_inicio):
    pagina = 1
    todas = []

    while True:
        resp = get_json_seguro(
            f"{BASE_URL}/votacoes",
            params={
                "dataInicio": data_inicio,
                "itens": 100,
                "pagina": pagina
            }
        )

        dados = resp.get("dados", []) if resp else []

        if not dados:
            break

        todas.extend(dados)
        pagina += 1

    return todas


# 🔹 Contar presença de UM deputado
def contar_presencas_deputado(deputado_id, votacoes):
    presencas = 0

    for votacao in votacoes:
        votos_resp = get_json_seguro(
            f"{BASE_URL}/votacoes/{votacao['id']}/votos"
        )

        if not votos_resp:
            continue

        votos = votos_resp.get("dados", [])

        for voto in votos:
            if voto["deputado_"]["id"] == deputado_id:
                presencas += 1
                break

        time.sleep(0.1)  # 🔹 evita sobrecarga da API

    return presencas


# 🔹 Entrada
nome_busca = input("Digite o nome do deputado: ").lower()

deputados = buscar_deputados()

id_alvo = None
nome_encontrado = None
uf_alvo = None

for dep in deputados:
    if nome_busca in dep["nome"].lower():
        id_alvo = dep["id"]
        nome_encontrado = dep["nome"]
        uf_alvo = dep["siglaUf"]
        break

if not id_alvo:
    print("❌ Deputado não encontrado")
    exit()

print(f"\n✅ Encontrado: {nome_encontrado} ({uf_alvo})")


# 🔹 Deputados do mesmo estado
deps_estado = [d for d in deputados if d["siglaUf"] == uf_alvo]


# 🔹 Buscar votações
print("\n⏳ Buscando votações...")
votacoes = buscar_votacoes(data_inicio)
total_votacoes = len(votacoes)


# 🔹 Calcular participação
print("⏳ Calculando participação dos deputados do estado...")

participacoes = []
participacao_alvo = 0

for dep in deps_estado:
    pres = contar_presencas_deputado(dep["id"], votacoes)

    perc = (pres / total_votacoes) * 100 if total_votacoes > 0 else 0
    participacoes.append(perc)

    if dep["id"] == id_alvo:
        participacao_alvo = perc


# 🔹 Média do estado
media_estado = sum(participacoes) / len(participacoes) if participacoes else 0


# 🔹 Resultado
print("\n" + "="*50)
print("📊 RELATÓRIO DE ENGAJAMENTO (US06)")
print("="*50)

print(f"🔹 Deputados no estado ({uf_alvo}): {len(deps_estado)}")
print(f"🔹 Total de votações analisadas: {total_votacoes}")

print(f"\n📈 Participação de {nome_encontrado}: {participacao_alvo:.1f}%")
print(f"📊 Média do estado: {media_estado:.1f}%")

if participacao_alvo >= media_estado:
    print("\n✅ Acima da média estadual.")
else:
    print("\n⚠️ Abaixo da média estadual.")