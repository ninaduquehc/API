import requests
import pandas as pd

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
TIMEOUT  = 15

# Limite mensal da cota CEAP por estado (referência 2024/2025)
LIMITES_CEAP = {
    "AC": 56241.52, "AL": 49525.18, "AM": 56402.77, "AP": 54407.24,
    "BA": 48718.06, "CE": 51528.64, "DF": 41603.80, "ES": 45419.10,
    "GO": 41745.03, "MA": 52124.53, "MG": 43513.67, "MS": 47169.45,
    "MT": 48337.92, "PA": 52880.51, "PB": 50812.08, "PE": 50316.21,
    "PI": 51364.59, "PR": 45922.66, "RJ": 44825.93, "RN": 51050.47,
    "RO": 47788.14, "RR": 57382.10, "RS": 47017.86, "SC": 46574.18,
    "SE": 49208.09, "SP": 44401.23, "TO": 46220.16,
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
    payload = buscar_json(
        f"{BASE_URL}/deputados/{id_deputado}/despesas",
        params={"ano": ano, "mes": mes, "itens": 100}
    )
    if not payload or "dados" not in payload:
        return 0.0
    return sum(float(item.get("valorLiquido") or 0) for item in payload["dados"])


def montar_tabela(uf, ano, mes):
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
            continue  # pula quem não teve gasto no período

        registros.append({
            "nome":        d["nome"],
            "uf":          uf,
            "gasto":       gasto,
            "limite_ceap": limite,
            "uso_pct":     (gasto / limite) * 100,
        })

    if not registros:
        print("Nenhum gasto encontrado para este período.")
        return None

    df = pd.DataFrame(registros)

    # Ranking: posição do deputado no estado (1º = maior gasto)
    df["rank_uf"] = df["gasto"].rank(method="min", ascending=False).astype(int)
    df = df.sort_values("rank_uf")

    return df

def exibir_relatorio(df, uf, ano, mes):
    total_dep    = len(df)
    acima_limite = len(df[df["uso_pct"] > 100])

    df_rel = df.copy()
    df_rel["Despesa"]        = df_rel["gasto"].apply(
        lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    df_rel["Uso da Cota"]    = df_rel["uso_pct"].apply(lambda x: f"{x:.1f}%")
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
            if 2019 <= ano <= 2025:
                return ano
            print("  Ano fora do intervalo. Use entre 2019 e 2025.")
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


UF  = pedir_uf()
ANO = pedir_ano()
MES = pedir_mes()

df = montar_tabela(UF, ANO, MES)

if df is not None:
    exibir_relatorio(df, UF, ANO, MES)
