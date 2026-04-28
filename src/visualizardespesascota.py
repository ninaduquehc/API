import requests

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
TIMEOUT = 15

# Limite mensal da cota CEAP por estado (referência 2024/2025)
LIMITES_CEAP = {
    "AC": 56241.52,
    "AL": 49525.18,
    "AM": 56402.77,
    "AP": 54407.24,
    "BA": 48718.06,
    "CE": 51528.64,
    "DF": 41603.80,
    "ES": 45419.10,
    "GO": 41745.03,
    "MA": 52124.53,
    "MG": 43513.67,
    "MS": 47169.45,
    "MT": 48337.92,
    "PA": 52880.51,
    "PB": 50812.08,
    "PE": 50316.21,
    "PI": 51364.59,
    "PR": 45922.66,
    "RJ": 44825.93,
    "RN": 51050.47,
    "RO": 47788.14,
    "RR": 57382.10,
    "RS": 47017.86,
    "SC": 46574.18,
    "SE": 49208.09,
    "SP": 44401.23,
    "TO": 46220.16,
}


def buscar_json(url, params=None):
    try:
        resposta = requests.get(url, params=params, timeout=TIMEOUT)
        resposta.raise_for_status()
        return resposta.json()
    except requests.exceptions.Timeout:
        print(f"  [erro] Tempo esgotado: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"  [erro] HTTP {e.response.status_code}: {url}")
        return None
    except Exception as e:
        print(f"  [erro] {e}")
        return None


def buscar_deputados(uf):
    payload = buscar_json(f"{BASE_URL}/deputados", params={"siglaUf": uf, "itens": 100})
    if not payload:
        return []
    return payload["dados"]


def buscar_gastos(id_deputado, ano, mes):
    """Soma valorLiquido de todas as páginas de despesas do mês (mesmo critério do relatório CLI)."""
    total = 0.0
    pagina = 1
    while True:
        payload = buscar_json(
            f"{BASE_URL}/deputados/{id_deputado}/despesas",
            params={"ano": ano, "mes": mes, "itens": 100, "pagina": pagina},
        )
        if not payload or "dados" not in payload:
            break
        dados = payload["dados"]
        if not dados:
            break
        total += sum(float(item.get("valorLiquido") or 0) for item in dados)
        if len(dados) < 100:
            break
        pagina += 1
    return total


def limite_ceap_uf(sigla_uf):
    uf = (sigla_uf or "").strip().upper()
    return LIMITES_CEAP.get(uf, 35_000.00)


def resumo_ceap_deputado(sigla_uf, id_deputado, ano, mes):
    """
    Retorna gasto no mês, limite CEAP da UF e percentual de uso (baseado em visualizardespesascota).
    """
    gasto = buscar_gastos(id_deputado, ano, mes)
    limite = limite_ceap_uf(sigla_uf)
    uso_pct = (gasto / limite * 100) if limite > 0 else 0.0
    return {
        "gasto": gasto,
        "limite_ceap": limite,
        "uso_pct": uso_pct,
    }


def resumo_e_lista_ceap_mes(sigla_uf, id_deputado, ano, mes):
    """
    Uma única leitura da API de despesas do mês: resumo CEAP + linhas para tabela (evita chamadas duplicadas).
    """
    itens = listar_despesas_mes(id_deputado, ano, mes)
    gasto = sum(float(x.get("valorLiquido") or 0) for x in itens)
    limite = limite_ceap_uf(sigla_uf)
    uso_pct = (gasto / limite * 100) if limite > 0 else 0.0
    resumo = {
        "gasto": gasto,
        "limite_ceap": limite,
        "uso_pct": uso_pct,
    }
    linhas = preparar_linhas_despesas_para_template(itens)
    return resumo, linhas


def listar_despesas_mes(id_deputado, ano, mes):
    """Lista todos os lançamentos do mês para exibição em tabela."""
    itens = []
    pagina = 1
    while True:
        payload = buscar_json(
            f"{BASE_URL}/deputados/{id_deputado}/despesas",
            params={"ano": ano, "mes": mes, "itens": 100, "pagina": pagina},
        )
        if not payload or "dados" not in payload:
            break
        dados = payload["dados"]
        if not dados:
            break
        itens.extend(dados)
        if len(dados) < 100:
            break
        pagina += 1
    return itens


def texto_tipo_despesa(item):
    t = item.get("tipoDespesa")
    if isinstance(t, dict):
        return (t.get("nome") or t.get("descricao") or "").strip() or "—"
    if isinstance(t, str) and t.strip():
        return t.strip()
    return (item.get("descricao") or item.get("titulo") or "—").strip() or "—"


def preparar_linhas_despesas_para_template(itens_api):
    """Normaliza campos da API para o front-end."""
    linhas = []
    for it in itens_api:
        linhas.append(
            {
                "data": (it.get("dataDocumento") or "")[:10],
                "tipo": texto_tipo_despesa(it),
                "fornecedor": (it.get("nomeFornecedor") or "—").strip() or "—",
                "valor": float(it.get("valorLiquido") or 0),
            }
        )
    linhas.sort(key=lambda x: x["data"], reverse=True)
    return linhas


def montar_tabela(uf, ano, mes):
    import pandas as pd

    print(f"\nBuscando deputados de {uf}...")
    deputados = buscar_deputados(uf)

    if not deputados:
        print("Nenhum deputado encontrado.")
        return None

    print(f"{len(deputados)} deputados encontrados. Buscando despesas...\n")

    registros = []
    limite = LIMITES_CEAP.get(uf, 35_000.00)

    for d in deputados:
        print(f"  {d['nome']}...")
        gasto = buscar_gastos(d["id"], ano, mes)

        if gasto == 0:
            continue

        registros.append(
            {
                "nome": d["nome"],
                "uf": uf,
                "gasto": gasto,
                "limite_ceap": limite,
                "uso_pct": (gasto / limite) * 100,
            }
        )

    if not registros:
        print("Nenhum gasto encontrado para este período.")
        return None

    df = pd.DataFrame(registros)

    df["rank_uf"] = df["gasto"].rank(method="min", ascending=False).astype(int)
    df = df.sort_values("rank_uf")

    return df


def exibir_relatorio(df, uf, ano, mes):
    total_dep = len(df)
    acima_limite = len(df[df["uso_pct"] > 100])

    df_rel = df.copy()
    df_rel["Despesa"] = df_rel["gasto"].apply(
        lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    df_rel["Uso da Cota"] = df_rel["uso_pct"].apply(lambda x: f"{x:.1f}%")
    df_rel["Rank no Estado"] = df_rel["rank_uf"].apply(lambda r: f"{r}º de {total_dep}")

    print()
    print("=" * 85)
    print(f"  DESPESAS PARLAMENTARES — {uf} | {mes:02d}/{ano}".center(85))
    print("=" * 85)
    print(df_rel[["nome", "Despesa", "Uso da Cota", "Rank no Estado"]].to_string(index=False))
    print("=" * 85)
    print()
    print("  NOTAS:")
    print("  * O % é calculado sobre o limite mensal da CEAP do estado.")
    print("  * Valores acima de 100% indicam que o deputado ultrapassou o limite")
    print("    mensal da cota. A Câmara não bloqueia o gasto no momento —")
    print("    a auditoria e eventual devolução ocorrem posteriormente.")
    if acima_limite > 0:
        print(f"  * Neste relatório, {acima_limite} deputado(s) ultrapassaram o limite da cota.")
    print("=" * 85)


def pedir_uf():
    while True:
        uf = input("Estado (ex: SP, RJ, MG): ").strip().upper()
        if uf in LIMITES_CEAP:
            return uf
        print(f"  Estado '{uf}' não reconhecido. Tente novamente.")


def pedir_ano():
    while True:
        try:
            ano = int(input("Ano (ex: 2024): ").strip())
            if 2019 <= ano <= 2026:
                return ano
            print("  Ano fora do intervalo. Use entre 2019 e 2026.")
        except ValueError:
            print("  Digite apenas números.")


def pedir_mes():
    while True:
        try:
            mes = int(input("Mês (1 a 12): ").strip())
            if 1 <= mes <= 12:
                return mes
            print("  Mês inválido. Use um número entre 1 e 12.")
        except ValueError:
            print("  Digite apenas números.")


if __name__ == "__main__":
    UF = pedir_uf()
    ANO = pedir_ano()
    MES = pedir_mes()

    df = montar_tabela(UF, ANO, MES)

    if df is not None:
        exibir_relatorio(df, UF, ANO, MES)
