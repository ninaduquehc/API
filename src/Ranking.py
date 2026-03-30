import requests
import pandas as pd
from datetime import datetime

def listar_deputados_por_estado(uf):
    url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    params = {'siglaUf': uf, 'ordem': 'ASC', 'ordenarPor': 'nome'}

    response = requests.get(url, params=params)
    dados = response.json().get('dados', [])
    return dados


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


def ranking_estadual(uf, ano=datetime.now().year):
    deputados = listar_deputados_por_estado(uf)

    ranking = []

    print(f"\n🔎 Coletando dados de {len(deputados)} deputados de {uf}...\n")

    for dep in deputados:
        nome = dep['nome']
        id_dep = dep['id']

        percentual = calcular_presenca(id_dep, ano)

        ranking.append({
            'Deputado': nome,
            'Presença (%)': percentual
        })

    df = pd.DataFrame(ranking)

    df = df.sort_values(by='Presença (%)', ascending=False)

    print("\n🏆 RANKING DE PRESENÇA\n")
    print(df.to_string(index=False))


# --- EXECUÇÃO ---
uf = input("Digite a sigla do estado (ex: SP, RJ, MG): ").upper()
ranking_estadual(uf)