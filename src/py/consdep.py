import requests
import concurrent.futures
from functools import lru_cache

@lru_cache(maxsize=256)
def get_deputados(uf_filtro=None, partido_filtro=None, nome_filtro=None, pagina=1, itens=12):
    """
    Busca deputados com filtros e aplica paginação correta (sem duplicados).
    """

    url = "https://dadosabertos.camara.leg.br/api/v2/deputados"

    todos = []
    pagina_api = 1

    while True:
        params = {
            "idLegislatura": 57,
            "itens": 100,  # máximo permitido
            "pagina": pagina_api,
            "ordem": "ASC",
            "ordenarPor": "nome"
        }

        if uf_filtro:
            params["siglaUf"] = uf_filtro.upper()
        if partido_filtro:
            params["siglaPartido"] = partido_filtro.upper()
        if nome_filtro:
            params["nome"] = nome_filtro

        try:
            res = requests.get(url, params=params, timeout=10)
            res.raise_for_status()

            dados = res.json().get("dados", [])

            if not dados:
                break

            todos.extend(dados)
            pagina_api += 1

        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar deputados: {e}")
            break

    unicos = {}
    for dep in todos:
        unicos[dep["id"]] = dep

    lista = list(unicos.values())

    inicio = (pagina - 1) * itens
    fim = inicio + itens

    return lista[inicio:fim]

def get_deputados_completo(uf_filtro=None):
    url = "https://dadosabertos.camara.leg.br/api/v2/deputados"

    deputados = []
    pagina = 1

    while True:
        params = {
            "idLegislatura": 57,
            "itens": 100,
            "pagina": pagina
        }

        if uf_filtro:
            params["siglaUf"] = uf_filtro

        try:
            res = requests.get(url, params=params, timeout=10)
            res.raise_for_status()

            dados = res.json().get("dados", [])

            if not dados:
                break

            deputados.extend(dados)
            pagina += 1

        except:
            break

    
    unicos = {}
    for dep in deputados:
        unicos[dep["id"]] = dep

    return list(unicos.values())




def paginar(lista, pagina=1, itens=12):
    inicio = (pagina - 1) * itens
    fim = inicio + itens
    return lista[inicio:fim]


@lru_cache(maxsize=1024)
def get_despesas_deputado(id_deputado, ano=2024):
    """
    Fetches total expenses for a specific deputy.
    """
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_deputado}/despesas"
    try:
        # Limited to max 100 per request, we just take the first page to get an estimate or iterate
        # But for speed, just grab the first page (max 100 itens)
        res = requests.get(url, params={"itens": 100, "ordem": "DESC", "ano": ano})
        if res.status_code == 200:
            despesas = res.json().get("dados", [])
            total = sum([d.get("valorDocumento", 0) for d in despesas])
            return total
        return 0
    except:
        return 0

def calculate_dashboard_metrics(deputados):
    """
    Calculates expenses for the given list of 12 deputies using concurrent requests.
    """
    if not deputados:
        return {
            "gasto_total": 0,
            "gasto_medio": 0,
            "deputado_mais_gastos": "-"
        }

    total_gasto = 0
    mais_gastos_nome = "-"
    mais_gastos_valor = -1

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        future_to_deputado = {executor.submit(get_despesas_deputado, d["id"]): d for d in deputados}
        
        for future in concurrent.futures.as_completed(future_to_deputado):
            d = future_to_deputado[future]
            try:
                gasto = future.result()
                total_gasto += gasto
                
                if gasto > mais_gastos_valor:
                    mais_gastos_valor = gasto
                    mais_gastos_nome = d["nome"]
            except Exception as exc:
                print(f'{d["nome"]} generated an exception: {exc}')

    gasto_medio = total_gasto / len(deputados) if deputados else 0

    return {
        "gasto_total": f"R$ {total_gasto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "gasto_medio": f"R$ {gasto_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "deputado_mais_gastos": mais_gastos_nome
    }

@lru_cache(maxsize=256)
def get_deputado_por_id(id_deputado):
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_deputado}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json().get("dados", {})
    except Exception as e:
        print(f"Erro ao buscar deputado: {e}")
        return {}

def calcular_presenca(id_deputado, ano=2024):
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_deputado}/eventos"

    params = {
        "dataInicio": f"{ano}-01-01",
        "dataFim": f"{ano}-12-31"
    }

    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        eventos = res.json().get("dados", [])

        if not eventos:
            return 0

        total = len(eventos)
        presencas = 0

        for ev in eventos:
            texto = (
                ev.get("descricaoTipo", "") or
                ev.get("descricao", "") or
                ev.get("tipoEvento", "")
            )

            if "Deliberativa" in texto or "Reunião" in texto:
                presencas += 1

        return round((presencas / total) * 100, 2)

    except:
        return 0
    
def ranking_presenca(deputados):
    ranking = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(calcular_presenca, d["id"]): d
            for d in deputados
        }

        for future in concurrent.futures.as_completed(futures):
            dep = futures[future]
            try:
                presenca = future.result()

                ranking.append({
                    "id": dep["id"],  # 🔥 ESSENCIAL
                    "nome": dep["nome"],
                    "partido": dep["siglaPartido"],
                    "uf": dep["siglaUf"],
                    "presenca": presenca,
                    "foto": dep["urlFoto"]
                })
            except:
                pass

    ranking.sort(key=lambda x: x["presenca"], reverse=True)

    return ranking

def calcular_media_estado(uf, ano=2024):
    deputados = get_deputados(uf_filtro=uf, itens=100)

    if not deputados:
        return 0

    total = 0
    count = 0

    for dep in deputados:
        presenca = calcular_presenca(dep["id"], ano)
        total += presenca
        count += 1

    return round(total / count, 2) if count > 0 else 0