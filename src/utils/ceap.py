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

# Valor da cesta básica por estado (capital de referência) — referência março 2026
# Fontes: DIEESE/Conab; estados sem série usam média nacional (~R$ 730)
CESTA_BASICA_UF = {
    "AC": 641.15,
    "AL": 621.74,
    "AM": 620.42,
    "AP": 730.00,
    "BA": 623.85,
    "CE": 700.00,
    "DF": 750.00,
    "ES": 730.00,
    "GO": 730.00,
    "MA": 634.26,
    "MG": 730.00,
    "MS": 838.40,
    "MT": 838.40,
    "PA": 730.00,
    "PB": 636.16,
    "PE": 730.00,
    "PI": 730.00,
    "PR": 730.00,
    "RJ": 867.97,
    "RN": 636.95,
    "RO": 623.42,
    "RR": 652.14,
    "RS": 831.37,
    "SC": 824.35,
    "SE": 598.45,
    "SP": 883.94,
    "TO": 730.00,
}

CESTA_BASICA_MEDIA_NACIONAL = 730.00
LIMITE_CEAP_FALLBACK = 35000.00


def valor_cesta_basica_uf(sigla_uf):
    uf = (sigla_uf or "").strip().upper()
    return CESTA_BASICA_UF.get(uf, CESTA_BASICA_MEDIA_NACIONAL)


def cestas_equivalentes(gasto, sigla_uf):
    valor_cesta = valor_cesta_basica_uf(sigla_uf)
    if valor_cesta <= 0:
        return 0.0
    return gasto / valor_cesta


def limite_ceap_uf(sigla_uf):
    uf = (sigla_uf or "").strip().upper()
    return LIMITES_CEAP.get(uf, LIMITE_CEAP_FALLBACK)


def resumo_ceap_deputado(gasto, sigla_uf, filtro_ano, filtro_mes):
    """
    Calcula limite, % de uso e cestas equivalentes a partir do gasto já filtrado
    (ex.: resultado de buscar_despesas_deputado), alinhado à UF do deputado.

    - Com ano e mês: % sobre o limite mensal da CEAP da UF.
    - Só ano ou sem filtro: % sobre o limite anual de referência (12 × mensal).
    """
    limite_mensal = limite_ceap_uf(sigla_uf)
    limite_anual = limite_mensal * 12
    valor_cesta = valor_cesta_basica_uf(sigla_uf)
    cestas = cestas_equivalentes(gasto, sigla_uf)

    if filtro_ano and filtro_mes:
        denominador = limite_mensal
        modo_referencia = "mensal"
    else:
        denominador = limite_anual
        modo_referencia = "anual"

    uso_pct = (gasto / denominador * 100) if denominador > 0 else 0.0

    return {
        "limite_mensal": limite_mensal,
        "limite_anual": limite_anual,
        "valor_cesta_basica_uf": valor_cesta,
        "cestas_equivalentes": cestas,
        "uso_pct": uso_pct,
        "modo_referencia": modo_referencia,
    }


def _fmt_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(valor):
    return f"{valor:.2f}".replace(".", ",")


def _fmt_cestas(valor):
    """Ex.: 8575.3 → '8.575,3' (uma casa se necessário)."""
    if valor >= 100:
        s = f"{valor:,.1f}"
    else:
        s = f"{valor:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_resumo_ceap_exibicao(resumo):
    """Strings prontas para o template Jinja."""
    pct_barra = min(max(resumo["uso_pct"], 0.0), 100.0)
    return {
        **resumo,
        "limite_mensal_fmt": _fmt_brl(resumo["limite_mensal"]),
        "limite_anual_fmt": _fmt_brl(resumo["limite_anual"]),
        "valor_cesta_basica_fmt": _fmt_brl(resumo["valor_cesta_basica_uf"]),
        "cestas_equivalentes_fmt": _fmt_cestas(resumo["cestas_equivalentes"]),
        "uso_pct_fmt": _fmt_pct(resumo["uso_pct"]),
        "uso_pct_barra": pct_barra,
        "label_referencia_cota": (
            "Limite mensal da CEAP (UF)"
            if resumo["modo_referencia"] == "mensal"
            else "Limite anual de referência (12× mensal da UF)"
        ),
    }