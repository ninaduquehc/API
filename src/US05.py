import requests
import pandas as pd

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
LIMITE_DEPUTADOS = 5
TIMEOUT = 15

# Lista de limites mensais aproximados da Cota (CEAP) por estado (referência 2024/2025)
LIMITES_CEAP = {
    'DF': 30788.66, 'GO': 39521.13, 'MG': 35742.85, 'SP': 37043.53,
    'RJ': 35761.39, 'PR': 38879.45, 'SC': 39860.26, 'RS': 40875.90,
    'MS': 40542.84, 'MT': 39469.73, 'ES': 37649.92, 'BA': 39010.85,
    'SE': 40139.70, 'AL': 40938.33, 'PE': 41650.88, 'PB': 42171.88,
    'RN': 42232.12, 'CE': 42428.45, 'PI': 40971.77, 'MA': 42147.88,
    'PA': 42253.11, 'AP': 43394.39, 'AM': 43574.76, 'RR': 45612.53,
    'RO': 43632.72, 'AC': 44528.39, 'TO': 39590.86
}

def formatar_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def buscar_json(url: str):
    try:
        resposta = requests.get(url, timeout=TIMEOUT)
        resposta.raise_for_status()
        return resposta.json()
    except:
        return None

def buscar_deputados(limite: int = 5):
    payload = buscar_json(f"{BASE_URL}/deputados")
    return payload["dados"][:limite] if payload else []

def buscar_total_gastos(id_deputado: int) -> float:
    # Busca as despesas do mês atual/último disponível
    payload = buscar_json(f"{BASE_URL}/deputados/{id_deputado}/despesas?ordem=DESC&ordenarPor=ano")
    if not payload or "dados" not in payload:
        return 0.0
    return sum(float(item.get("valorLiquido") or 0) for item in payload["dados"])

def montar_registros(deputados):
    registros = []
    for d in deputados:
        id_dep, nome, uf = d["id"], d["nome"], d.get("siglaUf", "DF")
        print(f"Analisando: {nome}...")
        
        gasto_total = buscar_total_gastos(id_dep)
        limite_uf = LIMITES_CEAP.get(uf, 35000.00) # Valor padrão se não achar UF
        
        # Cálculo do percentual de uso da cota
        percentual_uso = (gasto_total / limite_uf) * 100

        registros.append({
            "nome": nome,
            "uf": uf,
            "despesa_reais": gasto_total,
            "cota_percentual": percentual_uso
        })
    return registros

def main():
    lista_deputados = buscar_deputados(LIMITE_DEPUTADOS)
    dados_processados = montar_registros(lista_deputados)
    
    df = pd.DataFrame(dados_processados)
    
    # Formatação para exibição
    df = df.sort_values(by="despesa_reais", ascending=False)
    df["Total Despesa"] = df["despesa_reais"].apply(formatar_brl)
    df["Uso da Cota (%)"] = df["cota_percentual"].apply(lambda x: f"{x:.2f}%")

    print("\n" + "="*80)
    print(f"{'RELATÓRIO: GASTOS TOTAIS | USO DA COTA':^80}")
    print("="*80)
    print(df[["nome", "uf", "Total Despesa", "Uso da Cota (%)"]].to_string(index=False))
    print("="*80)
    print("* Nota: O % é baseado no limite mensal de cota por estado.")

if __name__ == "__main__":
    main()
