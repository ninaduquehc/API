import requests
import pandas as pd
from datetime import datetime

def listar_deputados_por_estado(uf):
    url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    params = {'siglaUf': uf, 'ordem': 'ASC', 'ordenarPor': 'nome'}

    response = requests.get(url, params=params)
    return response.json().get('dados', [])


def calcular_presenca(deputado_id, ano=datetime.now().year):
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}/eventos"
    params = {
        'dataInicio': f'{ano}-01-01',
        'dataFim': f'{ano}-12-31'
    }

    try:
        response = requests.get(url, params=params)
        eventos = response.json().get('dados', [])

        if not eventos:
            return 0

        df = pd.DataFrame(eventos)

        coluna_filtro = 'descricao' if 'descricao' in df.columns else 'tipoEvento'
        if 'descricaoTipo' in df.columns:
            coluna_filtro = 'descricaoTipo'

        sessoes = df[df[coluna_filtro].str.contains('Deliberativa|Reunião', case=False, na=False)]

        total = len(df)
        presencas = len(sessoes)

        return (presencas / total) * 100 if total > 0 else 0

    except:
        return 0


def calcular_media_estadual(uf, ano=datetime.now().year):
    deputados = listar_deputados_por_estado(uf)

    presencas = []

    print(f"\n📊 Calculando média estadual de {uf}...")

    for dep in deputados:
        percentual = calcular_presenca(dep['id'], ano)
        presencas.append(percentual)

    media = sum(presencas) / len(presencas) if presencas else 0

    return media


def buscar_id_por_nome(nome_busca):
    url_lista = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    params = {'nome': nome_busca}

    response = requests.get(url_lista, params=params)
    dados = response.json().get('dados', [])

    if not dados:
        print("Deputado não encontrado.")
        return None

    return dados[0]['id'], dados[0]['nome'], dados[0]['siglaUf']


def comparar_com_media(nome_deputado, ano=datetime.now().year):
    resultado = buscar_id_por_nome(nome_deputado)

    if not resultado:
        return

    id_dep, nome, uf = resultado

    presenca_dep = calcular_presenca(id_dep, ano)
    media_estado = calcular_media_estadual(uf, ano)

    diferenca = presenca_dep - media_estado

    print("\n" + "="*50)
    print(f"🏛️ DEPUTADO: {nome}")
    print(f"📍 ESTADO: {uf}")
    print(f"📅 ANO: {ano}")
    print("="*50)
    print(f"📊 Presença do deputado: {presenca_dep:.2f}%")
    print(f"📈 Média do estado:      {media_estado:.2f}%")

    if diferenca > 0:
        print(f"✅ Acima da média em {diferenca:.2f} pontos percentuais")
    elif diferenca < 0:
        print(f"❌ Abaixo da média em {abs(diferenca):.2f} pontos percentuais")
    else:
        print("⚖️ Exatamente na média")

    print("="*50)


# --- EXECUÇÃO ---
nome = input("Digite o nome do deputado: ")
comparar_com_media(nome)