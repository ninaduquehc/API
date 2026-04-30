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
    buscar_ranking_gastos,
    buscar_ranking_presenca,
    buscar_presenca_deputado,
    media_presenca_estado
)
from src.utils.data_processor import processar_metricas_pandas

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
    presenca = buscar_presenca_deputado(id_deputado)
    media_estado = media_presenca_estado(deputado["sigla_uf"])
    print("PRESENCA:", presenca)
    print("MEDIA:", media_estado)
    valor_presenca = float(presenca["percentual_presenca"]) if presenca else 0
    return render_template(
        "deputado.html",
        deputado=deputado,
        detalhes=detalhes_api,
        despesas=despesas,
        metrics=metrics,
        tipos_despesa=tipos_despesa,
        anos_despesa=anos_despesa,
        filtro_ano=filtro_ano,
        filtro_mes=filtro_mes,
        filtro_tipo=filtro_tipo,
        presenca=valor_presenca,
        media=media_estado, 
    )

@app.route("/ranking")
def ranking():
    uf = request.args.get("uf", "").upper().strip()
    page = request.args.get("page", 1, type=int)
    criterio = request.args.get("criterio", "gastos")

    por_pagina = 15

    if criterio == "presenca":
        ranking_completo = buscar_ranking_presenca(uf)
    else:
        ranking_completo = buscar_ranking_gastos(uf)

    total = len(ranking_completo)
    inicio = (page - 1) * por_pagina
    fim = inicio + por_pagina
    ranking_paginado = ranking_completo[inicio:fim]
    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)

    return render_template(
        "ranking.html",
        ranking=ranking_paginado,
        uf=uf,
        page=page,
        total_paginas=total_paginas,
        criterio=criterio
    )