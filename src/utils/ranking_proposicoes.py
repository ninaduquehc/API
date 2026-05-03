PESOS = {"PEC": 3, "PDC": 2, "PL": 1}


def calcular_score(total_pl: int, total_pdc: int, total_pec: int) -> float:
    return (
        int(total_pl)  * PESOS["PL"]  +
        int(total_pdc) * PESOS["PDC"] +
        int(total_pec) * PESOS["PEC"]
    )


def montar_ranking_pl(rows: list[dict]) -> list[dict]:
    if not rows:
        return []

    for r in rows:
        r["total_pl"]  = int(r.get("total_pl",  0) or 0)
        r["total_pdc"] = int(r.get("total_pdc", 0) or 0)
        r["total_pec"] = int(r.get("total_pec", 0) or 0)
        r["score"]     = float(calcular_score(r["total_pl"], r["total_pdc"], r["total_pec"]))
        r["total_geral"] = r["total_pl"] + r["total_pdc"] + r["total_pec"]

    media_por_uf: dict[str, float] = {}
    contagem_uf:  dict[str, int]   = {}
    for r in rows:
        uf = r["sigla_uf"]
        media_por_uf[uf] = media_por_uf.get(uf, 0.0) + r["score"]
        contagem_uf[uf]  = contagem_uf.get(uf, 0) + 1

    for uf in media_por_uf:
        media_por_uf[uf] = round(media_por_uf[uf] / contagem_uf[uf], 2)

    for r in rows:
        r["media_uf_score"] = media_por_uf[r["sigla_uf"]]
        r["diff_score"]     = round(r["score"] - r["media_uf_score"], 2)

    rows.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(rows):
        r["posicao"] = i + 1

    return rows