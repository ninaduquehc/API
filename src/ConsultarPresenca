import requests
import pandas as pd
from datetime import datetime

def buscar_id_por_nome(nome_busca):
    url_lista = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    params = {'nome': nome_busca, 'ordem': 'ASC', 'ordenarPor': 'nome'}

    try:
        response = requests.get(url_lista, params=params)
        dados = response.json().get('dados', [])

        if not dados:
            print(f"Nenhum deputado encontrado com o nome '{nome_busca}'.")
            return None

        if len(dados) > 1:
            print(f"\nForam encontrados {len(dados)} deputados. Escolha o número:")
            for i, d in enumerate(dados):
                print(f"{i} - {d['nome']} ({d['siglaPartido']}-{d['siglaUf']})")
            indice = int(input("\nDigite o número do deputado correto: "))
            return dados[indice]['id'], dados[indice]['nome']

        return dados[0]['id'], dados[0]['nome']
    except Exception as e:
        print(f"Erro na busca: {e}")
        return None

def calcular_presenca_detalhada(deputado_id, nome_deputado, ano = datetime.now().year):
    """Busca eventos e calcula o percentual real."""
    url_eventos = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}/eventos"
    params = {
        'dataInicio': f'{ano}-01-01',
        'dataFim': f'{ano}-12-31',
        'ordem': 'ASC'
    }

    response = requests.get(url_eventos, params=params)
    eventos = response.json().get('dados', [])

    if not eventos:
        print(f"Sem registros de sessões para {nome_deputado} em {ano}.")
        return

    df = pd.DataFrame(eventos)

    #
    coluna_filtro = 'descricao' if 'descricao' in df.columns else 'tipoEvento'
    if 'descricaoTipo' in df.columns: coluna_filtro = 'descricaoTipo'

    #
    sessoes_validas = df[df[coluna_filtro].str.contains('Deliberativa|Reunião', case=False, na=False)]

    total_eventos = len(df)
    total_presencas = len(sessoes_validas)

    # Cálculo: (Parte / Todo) * 100
    percentual = (total_presencas / total_eventos) * 100 if total_eventos > 0 else 0

    print("\n" + "="*40)
    print(f"RELATÓRIO: {nome_deputado.upper()}")
    print(f"ANO: {ano}")
    print("="*40)
    print(f"Total de registros na API:  {total_eventos}")
    print(f"Sessões identificadas:      {total_presencas}")
    print(f"PERCENTUAL DE PRESENÇA:     {percentual:.2f}%")
    print("="*40)

print("Iniciando consulta na API da Câmara...")
nome_input = input("Digite o nome do deputado: ")
resultado = buscar_id_por_nome(nome_input)

if resultado:
    id_dep, nome_dep = resultado
    calcular_presenca_detalhada(id_dep, nome_dep)
