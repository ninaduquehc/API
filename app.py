from flask import Flask, render_template, request
import sys
import os

# Ensure the app can find the src.py folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.py.consdep import get_deputados, calculate_dashboard_metrics,get_deputado_por_id,get_despesas_deputado,ranking_presenca,calcular_media_estado,calcular_presenca,get_deputados_completo

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    page = request.args.get("page", 1, type=int)
    
    uf = request.form.get("uf") or request.args.get("uf") or ""
    uf = uf.strip().upper()
    
    partido = request.form.get("partido") or request.args.get("partido") or ""
    partido = partido.strip().upper()
    
    nome = request.form.get("nome") or request.args.get("nome") or ""
    nome = nome.strip()

    # 🔥 JÁ VEM LIMPO E PAGINADO
    deputados = get_deputados(
        uf_filtro=uf,
        partido_filtro=partido,
        nome_filtro=nome,
        pagina=page,
        itens=12
    )

    # 🔥 cálculo normal
    metrics = calculate_dashboard_metrics(deputados)
    ranking = ranking_presenca(deputados)

    return render_template(
        "index.html", 
        deputados=deputados, 
        metrics=metrics, 
        current_page=page,
        uf=uf,
        partido=partido,
        nome=nome,
        ranking_presenca=ranking
    )

@app.route("/deputado/<int:id>")
def detalhe_deputado(id):
    deputado = get_deputado_por_id(id)

    uf = deputado["ultimoStatus"]["siglaUf"]

    gasto = get_despesas_deputado(id)

    presenca = calcular_presenca(id)
    media_estado = calcular_media_estado(uf)

    deputados_estado = get_deputados(uf_filtro=uf, itens=100)
    ranking = ranking_presenca(deputados_estado)

    posicao = "-"
    total = len(ranking)

    origem = request.args.get("origem", "dashboard")
    for i, dep in enumerate(ranking):
        if dep["id"] == id:
            posicao = i + 1
            break
            
    return render_template(
        "deputado.html",
        deputado=deputado,
        gasto=gasto,
        presenca=round(presenca, 2),
        media=round(media_estado, 2),
        posicao=posicao,
        total=total,
        origem=origem
    )

@app.route("/ranking")
def ranking():
    uf = request.args.get("uf", "").upper()
    page = request.args.get("page", 1, type=int)

    deputados = get_deputados_completo(uf_filtro=uf)

    ranking_lista = ranking_presenca(deputados)

    itens = 15
    inicio = (page - 1) * itens
    fim = inicio + itens

    ranking_pagina = ranking_lista[inicio:fim]

    tem_proxima = len(ranking_lista) > page * itens

    return render_template(
        "ranking.html",
        ranking=ranking_pagina,
        uf=uf,
        current_page=page,
        tem_proxima=tem_proxima
    )



if __name__ == "__main__":
    app.run(debug=True)
