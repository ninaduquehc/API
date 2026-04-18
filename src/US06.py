import requests
from datetime import datetime

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
data_inicio = "2023-02-01" 

nome_busca = input("Digite o nome do deputado: ").lower()

deps_resp = requests.get(f"{BASE_URL}/deputados")
if deps_resp.status_code != 200:
    exit()

deputados = deps_resp.json()["dados"]

id_alvo = None
nome_encontrado = None
sigla_uf_alvo = None

for dep in deputados:
    if nome_busca in dep["nome"].lower():
        id_alvo = dep["id"]
        nome_encontrado = dep["nome"]
        sigla_uf_alvo = dep["siglaUf"]
        break

if not id_alvo:
    print("❌ Deputado não encontrado")
    exit()

print(f"\n✅ Encontrado: {nome_encontrado} ({sigla_uf_alvo})")

votos_resp = requests.get(
    f"{BASE_URL}/deputados/{id_alvo}/votos", 
    params={
        "dataInicio": data_inicio, 
        "ordem": "DESC",
        "itens": 100
    }
)
votos_deputado = votos_resp.json().get("dados", [])

votacoes_estado_resp = requests.get(
    f"{BASE_URL}/votacoes", 
    params={
        "dataInicio": data_inicio, 
        "siglaUf": sigla_uf_alvo,
        "itens": 100
    }
)
total_votacoes_estado = len(votacoes_estado_resp.json().get("dados", []))

print(f"\n📊 Histórico de votos (Desde {data_inicio})\n")

if not votos_deputado:
    print("⚠️ Nenhum voto NOMINAL registrado no lote consultado.")
else:
    for v in votos_deputado[:10]: 
        print(f"🗳️ Tema: {v.get('proposicaoObjeto', 'Sem descrição')[:80]}...")
        print(f"👉 Voto: {v.get('tipoVoto')} | 📅 Data: {v.get('dataRegistroVoto')}")
        print("-" * 50)
    
    if len(votos_deputado) > 10:
        print(f"... e mais {len(votos_deputado) - 10} votos listados.")

    print("\n" + "="*50)
    print(f"📊 RELATÓRIO DE ENGAJAMENTO (US06)")
    print("="*50)

    presencas = len(votos_deputado)
    if total_votacoes_estado > 0:
        perc_participacao = (presencas / total_votacoes_estado) * 100
        print(f"🔹 Amostra de sessões do estado ({sigla_uf_alvo}): {total_votacoes_estado}")
        print(f"🔹 Presenças registradas: {presencas}")
        print(f"📈 Taxa de participação: {perc_participacao:.1f}%")
        
        if perc_participacao >= 70:
            print("\n✅ Engajamento satisfatório.")
        else:
            print("\n⚠️ Engajamento abaixo da média das sessões nominais.")
    else:
        print("❌ Não foi possível realizar a comparação estatística.")
