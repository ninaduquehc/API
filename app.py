from flask import Flask, render_template, request, abort, redirect, url_for
import requests as http_requests
from datetime import datetime
 
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
    buscar_total_proposicoes_aprovadas_deputado,
    buscar_dados_ranking_pl,
    buscar_resumo_coerencia,
    buscar_todos_deputados,
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
    import random
 
    lista = buscar_todos_deputados()
    if len(lista) >= 2:
        sorteados = random.sample(lista, 2)
        id1, id2 = sorteados[0]["id"], sorteados[1]["id"]
    else:
        id1, id2 = None, None
 
    dados = _gerar_dados_comparacao(id1, id2, "24m")
 
    return render_template(
        "home.html",
        dep1=dados["dep1"],
        dep2=dados["dep2"],
        indicadores=dados["indicadores"],
        sintese1=dados["sintese1"],
        sintese2=dados["sintese2"]
    )
 
 
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
        contar_discursos_ultimo_ano,
        buscar_ultimos_discursos,
        buscar_discursos_por_ano,
        buscar_discursos_por_palavra_chave,
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
    total_aprovadas = buscar_total_proposicoes_aprovadas_deputado(id_deputado)
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
 
    palavra_chave       = request.args.get("q", "").strip()
    total_discursos     = contar_discursos_ultimo_ano(id_deputado)
    ultimos_discursos   = buscar_ultimos_discursos(id_deputado)
    discursos_por_ano   = buscar_discursos_por_ano(id_deputado)
    discursos_filtrados = buscar_discursos_por_palavra_chave(id_deputado, palavra_chave) if palavra_chave else []
 
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
        total_discursos=total_discursos,
        ultimos_discursos=ultimos_discursos,
        discursos_por_ano=discursos_por_ano,
        discursos_filtrados=discursos_filtrados,
        palavra_chave=palavra_chave,
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
 
 
@app.route("/metodologia")
def metodologia():
    return render_template("metodologia.html")
 
 
def _cargo_label(deputado):
    cargo = (deputado or {}).get("cargo_partido") or ""
    cargo = cargo.strip().lower()
    if cargo in {"presidente", "lider", "líder", "vice-lider", "vice-líder"}:
        return cargo.title()
    return "Membro"
 
 
def _formatar_moeda_br(valor):
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")
 
 
def _formatar_numero_br(valor):
    return f"{int(round(valor)):,}".replace(",", ".")
 
 
def _formatar_percentual(valor):
    return f"{valor:.1f}%".replace(".", ",")
 
 
def _filtro_periodo(periodo):
    agora = datetime.now()
    if periodo == "12m":
        return agora.year - 1
    if periodo == "24m":
        return agora.year - 2
    if periodo == "48m":
        return agora.year - 4
    return None
 
 
def _normalizar_indicador(nome, icone, valor1, valor2, melhor_maior=True, formatter=str):
    limite = max(valor1, valor2, 0.0)
    if limite <= 0:
        barra1 = 0.0
        barra2 = 0.0
        melhor = 0
    else:
        barra1 = (valor1 / limite) * 100
        barra2 = (valor2 / limite) * 100
        if valor1 == valor2:
            melhor = 0
        elif melhor_maior:
            melhor = 1 if valor1 > valor2 else 2
        else:
            melhor = 1 if valor1 < valor2 else 2
 
    return {
        "nome": nome,
        "icone": icone,
        "valor1": formatter(valor1),
        "valor2": formatter(valor2),
        "barra1": round(barra1, 1),
        "barra2": round(barra2, 1),
        "melhor": melhor,
        "disponivel": True,
    }
 
 
def _gerar_dados_comparacao(id1, id2, periodo):
    dep1 = buscar_deputado_por_id(id1) if id1 else None
    dep2 = buscar_deputado_por_id(id2) if id2 else None
 
    indicadores = []
    sintese1 = "Selecione o deputado para gerar a síntese."
    sintese2 = "Selecione o deputado para gerar a síntese."
 
    if dep1:
        dep1["cargo_label"] = _cargo_label(dep1)
    if dep2:
        dep2["cargo_label"] = _cargo_label(dep2)
 
    if dep1 and dep2:
        ano_minimo = _filtro_periodo(periodo)
 
        despesas1 = buscar_despesas_deputado(dep1["id"])
        despesas2 = buscar_despesas_deputado(dep2["id"])
 
        if ano_minimo is not None:
            despesas1 = [d for d in despesas1 if (d.get("ano") or 0) >= ano_minimo]
            despesas2 = [d for d in despesas2 if (d.get("ano") or 0) >= ano_minimo]
 
        gasto1 = sum(float(d.get("valorDocumento") or 0) for d in despesas1)
        gasto2 = sum(float(d.get("valorDocumento") or 0) for d in despesas2)
 
        presenca1 = buscar_presenca_deputado(dep1["id"]) or {}
        presenca2 = buscar_presenca_deputado(dep2["id"]) or {}
        pct_presenca1 = float(presenca1.get("percentual_presenca") or 0.0)
        pct_presenca2 = float(presenca2.get("percentual_presenca") or 0.0)
 
        aprovadas1 = float(buscar_total_proposicoes_aprovadas_deputado(dep1["id"], ano_minimo))
        aprovadas2 = float(buscar_total_proposicoes_aprovadas_deputado(dep2["id"], ano_minimo))
 
        coerencia1 = buscar_resumo_coerencia(dep1["id"], anos=3)
        coerencia2 = buscar_resumo_coerencia(dep2["id"], anos=3)
        indice1 = float(coerencia1.get("indice_medio") or 0.0)
        indice2 = float(coerencia2.get("indice_medio") or 0.0)
        temas1 = float(coerencia1.get("total_temas") or 0.0)
        temas2 = float(coerencia2.get("total_temas") or 0.0)
 
        indicadores = [
            _normalizar_indicador("Presença em plenário", "✅", pct_presenca1, pct_presenca2, True, _formatar_percentual),
            _normalizar_indicador("Projetos aprovados", "📜", aprovadas1, aprovadas2, True, _formatar_numero_br),
            _normalizar_indicador("Índice de coerência", "🎯", indice1, indice2, True, _formatar_percentual),
            _normalizar_indicador("Temas com atuação", "🧭", temas1, temas2, True, _formatar_numero_br),
            _normalizar_indicador("Gasto declarado", "💸", gasto1, gasto2, False, _formatar_moeda_br),
        ]
 
        sintese1 = (
            f"{dep1['nome'].split()[0]} registra {_formatar_percentual(pct_presenca1)} de presença, "
            f"{_formatar_numero_br(aprovadas1)} projetos aprovados e {_formatar_moeda_br(gasto1)} "
            "de gasto declarado no período selecionado."
        )
        sintese2 = (
            f"{dep2['nome'].split()[0]} registra {_formatar_percentual(pct_presenca2)} de presença, "
            f"{_formatar_numero_br(aprovadas2)} projetos aprovados e {_formatar_moeda_br(gasto2)} "
            "de gasto declarado no período selecionado."
        )
 
    return {
        "dep1": dep1,
        "dep2": dep2,
        "indicadores": indicadores,
        "sintese1": sintese1,
        "sintese2": sintese2,
    }
 
 
@app.route("/comparacao")
def comparacao():
    lista_deputados = buscar_todos_deputados()
    id1 = request.args.get("id1", type=int)
    id2 = request.args.get("id2", type=int)
    periodo = request.args.get("periodo", "24m")
 
    periodos = [
        {"valor": "12m", "rotulo": "Últimos 12 meses"},
        {"valor": "24m", "rotulo": "Últimos 24 meses"},
        {"valor": "48m", "rotulo": "Últimos 48 meses"},
        {"valor": "todo", "rotulo": "Histórico completo"},
    ]
    valores_periodo = {p["valor"] for p in periodos}
    if periodo not in valores_periodo:
        periodo = "24m"
 
    dados = _gerar_dados_comparacao(id1, id2, periodo)
 
    return render_template(
        "comparacao.html",
        lista_deputados=lista_deputados,
        dep1=dados["dep1"],
        dep2=dados["dep2"],
        periodo=periodo,
        periodos=periodos,
        indicadores=dados["indicadores"],
        sintese1=dados["sintese1"],
        sintese2=dados["sintese2"],
    )
 
 
NAVBAR_ITEM = """
          <li class="nav-item">
            <a class="nav-link" href="{{ url_for('metodologia') }}">
              <i class="bi bi-calculator-fill me-1"></i>Metodologia
            </a>
          </li>
"""
 
 
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
    else:
        ranking_full = buscar_ranking_gastos(uf or None, ordem, partido or None)
 
    total         = contar_ranking(uf or None, criterio, partido or None)
    total_paginas = max(1, (total + POR_PAGINA - 1) // POR_PAGINA)
    ranking_pag   = ranking_full[offset : offset + POR_PAGINA]
 
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