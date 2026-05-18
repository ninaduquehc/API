from flask import Flask, render_template, request, abort
from functools import lru_cache
import requests as http_requests

from database.repository import (
    buscar_deputados,
    buscar_todos_deputados,
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
    buscar_top_temas_deputado,
    buscar_proposicoes_deputado,
)
from src.utils.data_processor import processar_metricas_pandas, gasto_total_numerico
from src.utils.ceap import resumo_ceap_deputado, formatar_resumo_ceap_exibicao
from src.utils.ranking_proposicoes import montar_ranking_pl

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    page    = request.args.get("page", 1, type=int)
    uf      = request.args.get("uf", "").upper().strip()
    partido = request.args.get("partido", "").upper().strip()
    nome    = request.args.get("nome", "").strip()

    limit  = 12
    offset = (page - 1) * limit

    deputados   = buscar_deputados(uf, partido, nome, limit, offset)
    total       = contar_deputados(uf, partido, nome)
    tem_proxima = (offset + limit) < total

    ids      = [d["id"] for d in deputados]
    despesas = buscar_despesas_por_deputados(ids)
    metrics  = processar_metricas_pandas(despesas, len(deputados))

    return render_template(
        "index.html",
        deputados=deputados,
        metrics=metrics,
        current_page=page,
        tem_proxima=tem_proxima,
        uf=uf,
        partido=partido,
        nome=nome,
    )


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
    )


@app.route("/ranking")
def ranking():
    uf       = request.args.get("uf", "").upper().strip()
    page     = request.args.get("page", 1, type=int)
    criterio = request.args.get("criterio", "gastos")
    ordem    = request.args.get("ordem", "")

    if criterio == "proposicoes":
        if not ordem:
            ordem = "desc"
        por_pagina   = 15
        rows         = buscar_dados_ranking_pl(uf if uf else None)
        ranking_full = montar_ranking_pl(rows)

        if ordem == "asc":
            ranking_full = list(reversed(ranking_full))

        total         = len(ranking_full)
        total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
        offset        = (page - 1) * por_pagina
        ranking_pag   = ranking_full[offset:offset + por_pagina]

        for i, r in enumerate(ranking_pag):
            r["posicao_display"] = offset + i + 1

        return render_template(
            "ranking.html",
            ranking=ranking_pag,
            uf=uf,
            page=page,
            total_paginas=total_paginas,
            criterio=criterio,
            ordem=ordem,
            total=total,
        )

    if not ordem:
        ordem = "asc" if criterio == "presenca" else "desc"

    por_pagina = 15
    offset     = (page - 1) * por_pagina

    if criterio == "presenca":
        ranking_paginado = buscar_ranking_presenca(uf, ordem)
    else:
        ranking_paginado = buscar_ranking_gastos(uf, ordem)

    total         = contar_ranking(uf, criterio)
    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
    ranking_paginado = ranking_paginado[offset:offset + por_pagina]

    return render_template(
        "ranking.html",
        ranking=ranking_paginado,
        uf=uf,
        page=page,
        total_paginas=total_paginas,
        criterio=criterio,
        ordem=ordem,
        total=total,
    )

def _cargo_label(deputado):
    cargo = (deputado or {}).get("cargo_partido") or ""
    if cargo and cargo not in ("Membro", ""):
        return cargo
    sexo = (deputado or {}).get("sexo", "")
    return "Deputada" if sexo == "F" else "Deputado"


@lru_cache(maxsize=512)
def _sintese_deputado(id_deputado):
    temas = buscar_top_temas_deputado(id_deputado, limite=3)
    if not temas:
        return (
            "Perfil parlamentar com atuação diversificada no período analisado. "
            "Consulte o perfil individual para mais detalhes sobre proposições e temas."
        )
    lista = ", ".join(t["nome"] for t in temas)
    return (
        f"Atuação com ênfase em temas como {lista}, "
        "refletindo as principais áreas de proposições no período."
    )


def _meses_no_periodo(ano, despesas):
    if ano:
        return 12
    meses_unicos = {
        str(d.get("dataDocumento") or d.get("ano", ""))[:7]
        for d in despesas
        if d.get("dataDocumento") or d.get("ano")
    }
    return max(1, len(meses_unicos))


def _gastos_deputado(id_deputado, ano=None):
    despesas = buscar_despesas_deputado(
        id_deputado,
        ano=int(ano) if ano else None,
    )
    total   = gasto_total_numerico(despesas)
    metrics = processar_metricas_pandas(despesas, 1)
    return total, metrics.get("gasto_medio", "R$ 0,00"), despesas


def _montar_indicador(nome, icone, v1, v2, invert=False, fmt="num", disponivel=True):
    def _num(x):
        if isinstance(x, (int, float)):
            return float(x)
        return 0.0

    n1, n2 = _num(v1), _num(v2)
    max_v  = max(n1, n2, 1e-9)
    barra1 = round((n1 / max_v) * 100, 1)
    barra2 = round((n2 / max_v) * 100, 1)

    if fmt == "pct":
        valor1 = f"{n1:.2f}%".replace(".", ",")
        valor2 = f"{n2:.2f}%".replace(".", ",")
    elif fmt == "money":
        valor1 = f"R$ {n1:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        valor2 = f"R$ {n2:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        valor1 = str(int(n1)) if n1 == int(n1) else f"{n1:.1f}"
        valor2 = str(int(n2)) if n2 == int(n2) else f"{n2:.1f}"

    melhor = 0
    if n1 != n2:
        if invert:
            melhor = 1 if n1 < n2 else 2
        else:
            melhor = 1 if n1 > n2 else 2

    return {
        "nome":       nome,
        "icone":      icone,
        "valor1":     valor1,
        "valor2":     valor2,
        "barra1":     barra1,
        "barra2":     barra2,
        "melhor":     melhor,
        "disponivel": disponivel,
    }


@app.route("/comparacao")
def comparacao():
    id1     = request.args.get("id1", type=int)
    id2     = request.args.get("id2", type=int)
    periodo = request.args.get("periodo", "2023").strip()
    ano     = periodo if periodo.isdigit() else None

    lista_deputados = buscar_todos_deputados()
    ids_na_lista    = {d["id"] for d in lista_deputados}

    dep1 = buscar_deputado_por_id(id1) if id1 else None
    dep2 = buscar_deputado_por_id(id2) if id2 else None

    for dep in (dep1, dep2):
        if dep and dep["id"] not in ids_na_lista:
            lista_deputados.append(dep)
            ids_na_lista.add(dep["id"])
    lista_deputados.sort(key=lambda d: d["nome"])

    if dep1:
        dep1["cargo_label"] = _cargo_label(dep1)
    if dep2:
        dep2["cargo_label"] = _cargo_label(dep2)

    sintese1    = sintese2    = ""
    indicadores = []

    if dep1 and dep2:
        sintese1 = _sintese_deputado(dep1["id"])
        sintese2 = _sintese_deputado(dep2["id"])

        p1    = buscar_presenca_deputado(dep1["id"])
        p2    = buscar_presenca_deputado(dep2["id"])
        pres1 = float(p1["percentual_presenca"]) if p1 else 0.0
        pres2 = float(p2["percentual_presenca"]) if p2 else 0.0

        todas1 = buscar_proposicoes_deputado(dep1["id"], ano=int(ano) if ano else None)
        todas2 = buscar_proposicoes_deputado(dep2["id"], ano=int(ano) if ano else None)

        prop1  = len(todas1)
        prop2  = len(todas2)
        aprov1 = sum(
            1 for p in todas1
            if p.get("situacao") and "aprovad" in p["situacao"].lower()
        )
        aprov2 = sum(
            1 for p in todas2
            if p.get("situacao") and "aprovad" in p["situacao"].lower()
        )

        total1, _, despesas1 = _gastos_deputado(dep1["id"], ano)
        total2, _, despesas2 = _gastos_deputado(dep2["id"], ano)

        meses1   = _meses_no_periodo(ano, despesas1)
        meses2   = _meses_no_periodo(ano, despesas2)
        mensal1  = total1 / meses1
        mensal2  = total2 / meses2

        indicadores = [
            _montar_indicador("Presença nas Sessões",    "📅", pres1,  pres2,  fmt="pct"),
            _montar_indicador("Proposições Apresentadas","📄", prop1,  prop2),
            _montar_indicador("Proposições Aprovadas",   "✅", aprov1, aprov2),
            _montar_indicador(
                "Gasto Total (R$)", "💰",
                total1, total2,
                invert=True, fmt="money",
            ),
            _montar_indicador(
                "Gasto Médio Mensal (R$)", "📊",
                mensal1, mensal2,
                invert=True, fmt="money",
            ),
        ]

    periodos = [
        {"valor": "2023", "rotulo": "01/01/2023 - 31/12/2023"},
        {"valor": "2024", "rotulo": "01/01/2024 - 31/12/2024"},
        {"valor": "2025", "rotulo": "01/01/2025 - 31/12/2025"},
        {"valor": "",     "rotulo": "Todo o período disponível"},
    ]

    return render_template(
        "comparacao.html",
        lista_deputados=lista_deputados,
        dep1=dep1,
        dep2=dep2,
        sintese1=sintese1,
        sintese2=sintese2,
        indicadores=indicadores,
        periodo=periodo,
        periodos=periodos,
    )


if __name__ == "__main__":
    app.run(debug=True)