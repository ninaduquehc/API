import requests
import pandas as pd

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
LIMITE_DEPUTADOS = 5
TIMEOUT = 10


def formatar_brl(valor: float) -> str:
    s = f"{valor:,.2f}"  # 1,234,567.89
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")  # 1.234.567,89
    return f"R$ {s}"


def buscar_json(url: str):
    try:
        resposta = requests.get(url, timeout=TIMEOUT)
        resposta.raise_for_status()
        return resposta.json()
    except requests.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return None


def buscar_deputados(limite: int = 5):
    payload = buscar_json(f"{BASE_URL}/deputados")
    if not payload or "dados" not in payload:
        return []
    return payload["dados"][:limite]


def buscar_total_despesas(id_deputado: int) -> float:
    payload = buscar_json(f"{BASE_URL}/deputados/{id_deputado}/despesas")
    if not payload or "dados" not in payload:
        return 0.0

    despesas = payload["dados"]
    total = sum(float(item.get("valorLiquido") or 0) for item in despesas)
    return round(total, 2)


def montar_registros(deputados):
    registros = []

    for deputado in deputados:
        id_deputado = deputado["id"]
        nome = deputado["nome"]
        email = deputado.get("email")
        sigla_uf = deputado.get("siglaUf")

        total_despesa = buscar_total_despesas(id_deputado)

        print(f"Nome: {nome}")
        print(f"Total gasto: {formatar_brl(total_despesa)}")
        print("=" * 40)

        registros.append(
            {
                "id": id_deputado,
                "nome": nome,
                "email": email,
                "siglaUf": sigla_uf,
                "despesa": total_despesa,  # mantém número para ordenar/calcular
            }
        )

    return registros


def limpar_dados(registros):
    df = pd.DataFrame(registros)
    if df.empty:
        return df

    df = df.copy()
    df = df[df["email"].notna() & (df["email"] != "")]
    df["despesa"] = pd.to_numeric(df["despesa"], errors="coerce")
    df = df[df["despesa"].notna()]
    df = df.drop_duplicates(subset="id")
    df["siglaUf"] = df["siglaUf"].fillna("").str.upper()

    return df


def main():
    deputados = buscar_deputados(LIMITE_DEPUTADOS)
    registros = montar_registros(deputados)
    df = limpar_dados(registros)

    print("\nRanking de gastos:")
    df_rank = df.sort_values(by="despesa", ascending=False).copy()
    df_rank["despesa_formatada"] = df_rank["despesa"].apply(formatar_brl)
    print(df_rank[["nome", "siglaUf", "email", "despesa_formatada"]])


if __name__ == "__main__":
    main()
