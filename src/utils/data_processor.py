import pandas as pd


def _dataframe_despesas_dedup(dados_despesas):
    if not dados_despesas:
        return None
    df = pd.DataFrame(dados_despesas)
    if "idDocumento" in df.columns:
        mask_valido = df["idDocumento"].notna() & (df["idDocumento"] != 0) & (df["idDocumento"] != "")
        df_com_id = df[mask_valido].drop_duplicates(subset=["idDocumento"])
        df_sem_id = df[~mask_valido]
        df = pd.concat([df_com_id, df_sem_id], ignore_index=True)
    return df


def gasto_total_numerico(dados_despesas):
    """Soma dos valores com a mesma deduplicação usada em processar_metricas_pandas."""
    df = _dataframe_despesas_dedup(dados_despesas)
    if df is None or df.empty:
        return 0.0
    col_valor = "valorDocumento" if "valorDocumento" in df.columns else "valor"
    return float(pd.to_numeric(df[col_valor], errors="coerce").sum())


def processar_metricas_pandas(dados_despesas, total_deputados):
    if not dados_despesas:
        return {
            "gasto_total": "R$ 0,00",
            "gasto_medio": "R$ 0,00",
            "deputado_mais_gastos": "-"
        }

    df = _dataframe_despesas_dedup(dados_despesas)

    col_valor = "valorDocumento" if "valorDocumento" in df.columns else "valor"

    gasto_total = pd.to_numeric(df[col_valor], errors="coerce").sum()
    gasto_medio = gasto_total / total_deputados if total_deputados > 0 else 0

    mais_gastador = "-"
    if not df.empty and "nome_deputado" in df.columns:
        gastos_por_nome = df.groupby("nome_deputado")[col_valor].sum()
        mais_gastador = gastos_por_nome.idxmax()

    def fmt(v):
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return {
        "gasto_total": fmt(gasto_total),
        "gasto_medio": fmt(gasto_medio),
        "deputado_mais_gastos": mais_gastador
    }