from flask import Flask, render_template, request, abort
import requests as http_requests

from database.repository import (
    buscar_deputados,
    contar_deputados,
    buscar_despesas_por_deputados,
    buscar_deputado_por_id,
    buscar_despesas_deputado,
    buscar_tipos_despesa_deputado,
    buscar_anos_despesa_deputado,
<<<<<<< HEAD
=======
    buscar_ranking_gastos,
    buscar_ranking_presenca,
    buscar_presenca_deputado,
    media_presenca_estado,
    contar_ranking
>>>>>>> atualizacao-projeto-29-04
)
from src.utils.data_processor import processar_metricas_pandas, gasto_total_numerico
from src.utils.ceap import resumo_ceap_deputado, formatar_resumo_ceap_exibicao

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    page = request.args.get("page", 1, type=int)
    uf = request.args.get("uf", "").upper().strip()
    partido = request.args.get("partido", "").upper().strip()
    nome = request.args.get("nome", "").strip()

    limit = 12
    offset = (page - 1) * limit

    deputados = buscar_deputados(uf, partido, nome, limit, offset)
    total = contar_deputados(uf, partido, nome)
    tem_proxima = (offset + limit) < total

    ids = [d["id"] for d in deputados]
    despesas = buscar_despesas_por_deputados(ids)
    metrics = processar_metricas_pandas(despesas, len(deputados))

    return render_template(
        "index.html",
        deputados=deputados,
        metrics=metrics,
        current_page=page,
        tem_proxima=tem_proxima,
        uf=uf,
        partido=partido,
        nome=nome
    )


@app.route("/deputado/<int:id_deputado>")
def deputado_detalhe(id_deputado):
    deputado = buscar_deputado_por_id(id_deputado)
    if not deputado:
        abort(404)

    filtro_ano = request.args.get("ano", "").strip()
    filtro_mes = request.args.get("mes", "").strip()
    filtro_tipo = request.args.get("tipo", "").strip()

    detalhes_api = {}
    try:
        res = http_requests.get(
            f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_deputado}",
            timeout=10
        )
        if res.status_code == 200:
            detalhes_api = res.json().get("dados", {})
    except Exception:
        pass

    despesas = buscar_despesas_deputado(
        id_deputado,
        ano=int(filtro_ano) if filtro_ano else None,
        mes=int(filtro_mes) if filtro_mes else None,
        tipo=filtro_tipo if filtro_tipo else None,
    )

    tipos_despesa = buscar_tipos_despesa_deputado(id_deputado)
    anos_despesa = buscar_anos_despesa_deputado(id_deputado)
    metrics = processar_metricas_pandas(despesas, 1)
<<<<<<< HEAD
    
=======

    # CEAP — cota parlamentar e equivalência em cestas básicas
>>>>>>> atualizacao-projeto-29-04
    gasto_total = gasto_total_numerico(despesas)
    ceap_bruto = resumo_ceap_deputado(
        gasto_total,
        deputado.get("sigla_uf") or "",
        filtro_ano,
        filtro_mes,
    )
    ceap = formatar_resumo_ceap_exibicao(ceap_bruto)

<<<<<<< HEAD
=======
    # Presença
    presenca = buscar_presenca_deputado(id_deputado)
    media_estado = media_presenca_estado(deputado["sigla_uf"])
    valor_presenca = float(presenca["percentual_presenca"]) if presenca else 0.0

    # Cargo no partido — já vem no dict deputado vindo do banco
    cargo_partido = deputado.get("cargo_partido") or "Membro"

>>>>>>> atualizacao-projeto-29-04
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
<<<<<<< HEAD
=======
        presenca=valor_presenca,
        media=media_estado,
        cargo_partido=cargo_partido,
    )


@app.route("/ranking")
def ranking():
    uf = request.args.get("uf", "").upper().strip()
    page = request.args.get("page", 1, type=int)
    criterio = request.args.get("criterio", "gastos")
    ordem_default = "asc" if criterio == "presenca" else "desc"
    ordem = request.args.get("ordem", ordem_default)

    por_pagina = 15
    offset = (page - 1) * por_pagina

    if criterio == "presenca":
        ranking_paginado = buscar_ranking_presenca(uf, ordem)
    else:
        ranking_paginado = buscar_ranking_gastos(uf, ordem)

    total = contar_ranking(uf, criterio)
    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
    ranking_paginado = ranking_paginado[offset:offset + por_pagina]

    return render_template(
        "ranking.html",
        ranking=ranking_paginado,
        uf=uf,
        page=page,
        total_paginas=total_paginas,
        criterio=criterio,
        ordem=ordem
>>>>>>> atualizacao-projeto-29-04
    )


if __name__ == "__main__":
    app.run(debug=True)