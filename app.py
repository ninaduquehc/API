from flask import Flask, render_template, request, abort, redirect, url_for
import requests as http_requests

from database.repository import (
    buscar_deputados,
    contar_deputados,
    buscar_despesas_por_deputados,
    buscar_deputado_por_id,
    buscar_despesas_deputado,
    buscar_tipos_despesa_deputado,
    buscar_anos_despesa_deputado,
    buscar_ranking_gastos,
    buscar_ranking_presenca,
    buscar_presenca_deputado,
    media_presenca_estado,
    contar_ranking,
    buscar_ranking_proposicoes_deputado,
    buscar_dados_ranking_pl,
    buscar_resumo_coerencia,
)
from src.utils.data_processor import processar_metricas_pandas, gasto_total_numerico
from src.utils.ceap import resumo_ceap_deputado, formatar_resumo_ceap_exibicao
from src.utils.ranking_proposicoes import montar_ranking_pl

app = Flask(__name__)

# Substitua pela sua chave em https://newsapi.org/register
# Em produção use: import os; NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
NEWS_API_KEY = ""


# ── / → redireciona para /home ────────────────────────────────
@app.route("/")
def root():
    return redirect(url_for("home"))


# ── Home / Landing page ───────────────────────────────────────
@app.route("/home")
def home():
    return render_template("home.html", news_api_key=NEWS_API_KEY)


# ── Listagem de deputados ─────────────────────────────────────
@app.route("/listagem", methods=["GET"])
def listagem():
    page    = request.args.get("page", 1, type=int)
    uf      = request.args.get("uf", "").upper().strip()
    partido = request.args.get("partido", "").upper().strip()
    nome    = request.args.get("nome", "").strip()

    limit  = 12
    offset = (page - 1) * limit

    deputados     = buscar_deputados(uf, partido, nome, limit, offset)
    total         = contar_deputados(uf, partido, nome)
    total_paginas = max(1, (total + limit - 1) // limit)
    tem_proxima   = (offset + limit) < total

    if page > total_paginas:
        page = total_paginas

    ids      = [d["id"] for d in deputados]
    despesas = buscar_despesas_por_deputados(ids)
    metrics  = processar_metricas_pandas(despesas, len(deputados))

    return render_template(
        "index.html",
        deputados=deputados,
        metrics=metrics,
        current_page=page,
        total_paginas=total_paginas,
        tem_proxima=tem_proxima,
        uf=uf,
        partido=partido,
        nome=nome,
    )


# ── Detalhe do deputado ───────────────────────────────────────
@app.route("/deputado/<int:id_deputado>")
def deputado_detalhe(id_deputado):
    from database.repository import (
        buscar_proposicoes_deputado,
        buscar_top_temas_deputado,
        buscar_resumo_proposicoes_deputado,
        buscar_anos_proposicoes_deputado,
        buscar_situacoes_proposicoes_deputado,
    )

    deputado = buscar_deputado_por_id(id_deputado)
    if not deputado:
        abort(404)

    filtro_ano    = request.args.get("ano",  "").strip()
    filtro_mes    = request.args.get("mes",  "").strip()
    filtro_tipo   = request.args.get("tipo", "").strip()
    prop_tipo     = request.args.get("prop_tipo",     "").strip()
    prop_ano      = request.args.get("prop_ano",      "").strip()
    prop_situacao = request.args.get("prop_situacao", "").strip()

    detalhes_api = {}
    try:
        res = http_requests.get(
            f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_deputado}",
            timeout=10,
        )
        if res.status_code == 200:
            detalhes_api = res.json().get("dados", {})
    except Exception:
        pass

    despesas = buscar_despesas_deputado(
        id_deputado,
        ano=int(filtro_ano) if filtro_ano else None,
        mes=int(filtro_mes) if filtro_mes else None,
        tipo=filtro_tipo    if filtro_tipo else None,
    )

    tipos_despesa = buscar_tipos_despesa_deputado(id_deputado)
    anos_despesa  = buscar_anos_despesa_deputado(id_deputado)
    metrics       = processar_metricas_pandas(despesas, 1)
    coerencia     = buscar_resumo_coerencia(id_deputado, anos=3)

    gasto_total = gasto_total_numerico(despesas)
    ceap_bruto  = resumo_ceap_deputado(
        gasto_total,
        deputado.get("sigla_uf") or "",
        filtro_ano,
        filtro_mes,
    )
    ceap = formatar_resumo_ceap_exibicao(ceap_bruto)

    presenca        = buscar_presenca_deputado(id_deputado)
    media_estado    = media_presenca_estado(deputado["sigla_uf"])
    ranking_prop    = buscar_ranking_proposicoes_deputado(id_deputado)
    posicao_prop    = ranking_prop["posicao"]         if ranking_prop else None
    total_aprovadas = ranking_prop["total_aprovadas"] if ranking_prop else 0
    valor_presenca  = float(presenca["percentual_presenca"]) if presenca else 0.0
    cargo_partido   = deputado.get("cargo_partido") or "Membro"

    proposicoes = buscar_proposicoes_deputado(
        id_deputado,
        tipo=prop_tipo         if prop_tipo     else None,
        ano=int(prop_ano)      if prop_ano      else None,
        situacao=prop_situacao if prop_situacao else None,
    )
    top_temas          = buscar_top_temas_deputado(id_deputado, limite=5)
    resumo_proposicoes = buscar_resumo_proposicoes_deputado(id_deputado)
    anos_proposicoes   = buscar_anos_proposicoes_deputado(id_deputado)
    situacoes_prop     = buscar_situacoes_proposicoes_deputado(id_deputado)

    totais_tipo = {}
    for row in resumo_proposicoes:
        t = row["sigla_tipo"]
        totais_tipo[t] = totais_tipo.get(t, 0) + row["total"]

    return render_template(
        "deputado.html",
        deputado=deputado,
        detalhes=detalhes_api,
        despesas=despesas,
        metrics=metrics,
        ceap=ceap,
        tipos_despesa=tipos_despesa,
        anos_despesa=anos_despesa,
        filtro_ano=filtro_ano,
        filtro_mes=filtro_mes,
        filtro_tipo=filtro_tipo,
        presenca=valor_presenca,
        media=media_estado,
        cargo_partido=cargo_partido,
        proposicoes=proposicoes,
        top_temas=top_temas,
        totais_tipo=totais_tipo,
        anos_proposicoes=anos_proposicoes,
        situacoes_prop=situacoes_prop,
        prop_tipo=prop_tipo,
        prop_ano=prop_ano,
        prop_situacao=prop_situacao,
        posicao_prop=posicao_prop,
        total_aprovadas=total_aprovadas,
        coerencia=coerencia,
    )


@app.route("/deputado/<int:id_deputado>/coerencia")
def coerencia_deputado(id_deputado):
    deputado = buscar_deputado_por_id(id_deputado)
    if not deputado:
        abort(404)

    coerencia = buscar_resumo_coerencia(id_deputado, anos=3)

    return render_template(
        "deputado/coerencia.html",
        deputado=deputado,
        coerencia=coerencia,
    )


# ── Ranking ───────────────────────────────────────────────────
@app.route("/ranking")
def ranking():
    uf       = request.args.get("uf", "").upper().strip()
    partido  = request.args.get("partido", "").upper().strip()
    page     = request.args.get("page", 1, type=int)
    criterio = request.args.get("criterio", "presenca")   # padrão: presença
    ordem    = request.args.get("ordem", "")

    POR_PAGINA = 15

    # ── critério: proposições ──────────────────────────────────
    if criterio == "proposicoes":
        if not ordem:
            ordem = "desc"

        rows         = buscar_dados_ranking_pl(uf or None, partido or None)
        ranking_full = montar_ranking_pl(rows)

        if ordem == "asc":
            ranking_full = list(reversed(ranking_full))

        total         = len(ranking_full)
        total_paginas = max(1, (total + POR_PAGINA - 1) // POR_PAGINA)
        offset        = (page - 1) * POR_PAGINA
        ranking_pag   = ranking_full[offset : offset + POR_PAGINA]

        # injeta posição real (considera a página)
        for i, r in enumerate(ranking_pag):
            r["posicao_display"] = offset + i + 1

        return render_template(
            "ranking.html",
            ranking=ranking_pag,
            uf=uf, partido=partido,
            page=page, total_paginas=total_paginas,
            criterio=criterio, ordem=ordem, total=total,
        )

    # ── critério: presença ou gastos ──────────────────────────
    if not ordem:
        ordem = "desc" if criterio == "gastos" else "asc"

    offset = (page - 1) * POR_PAGINA

    if criterio == "presenca":
        ranking_full = buscar_ranking_presenca(uf or None, ordem, partido or None)
    else:                                  # gastos
        ranking_full = buscar_ranking_gastos(uf or None, ordem, partido or None)

    total         = contar_ranking(uf or None, criterio, partido or None)
    total_paginas = max(1, (total + POR_PAGINA - 1) // POR_PAGINA)
    ranking_pag   = ranking_full[offset : offset + POR_PAGINA]

    # injeta posição real
    for i, r in enumerate(ranking_pag):
        r["posicao_display"] = offset + i + 1

    return render_template(
        "ranking.html",
        ranking=ranking_pag,
        uf=uf, partido=partido,
        page=page, total_paginas=total_paginas,
        criterio=criterio, ordem=ordem, total=total,
    )


if __name__ == "__main__":
    app.run(debug=True)