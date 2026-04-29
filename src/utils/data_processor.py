import pandas as pd


def processar_metricas_pandas(dados_despesas, total_deputados):
    if not dados_despesas:
        return {
            "gasto_total": "R$ 0,00",
            "gasto_medio": "R$ 0,00",
            "deputado_mais_gastos": "-"
        }

    df = pd.DataFrame(dados_despesas)

    if "idDocumento" in df.columns:
        mask_valido = df["idDocumento"].notna() & (df["idDocumento"] != 0) & (df["idDocumento"] != "")
        df_com_id = df[mask_valido].drop_duplicates(subset=["idDocumento"])
        df_sem_id = df[~mask_valido]
        df = pd.concat([df_com_id, df_sem_id], ignore_index=True)

    col_valor = "valorDocumento" if "valorDocumento" in df.columns else "valor"
    df[col_valor] = pd.to_numeric(df[col_valor], errors="coerce")

    gasto_total = df[col_valor].sum()

    if total_deputados == 1:
        # Soma por ano → média entre os anos
        if "ano" in df.columns:
            media_por_ano = df.groupby("ano")[col_valor].sum()
            gasto_medio = media_por_ano.mean()
        else:
            gasto_medio = gasto_total
    else:
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