import pandas as pd

BASE_URL_CSV = "https://dadosabertos.camara.leg.br/arquivos"


def carregar_votos_ano(ano):
    url = f"{BASE_URL_CSV}/votacoesVotos/csv/votacoesVotos-{ano}.csv"
    try:
        df = pd.read_csv(url, sep=';', low_memory=False)
        return df
    except Exception as e:
        print(f"  ⚠️  Erro ao carregar {ano}: {e}")
        return None


def analisar_presenca(nome_busca, anos):
    frames = []

    for ano in anos:
        print(f"📥 Baixando dados de {ano}...")
        df = carregar_votos_ano(ano)
        if df is not None:
            frames.append(df)

    if not frames:
        print("❌ Nenhum dado carregado.")
        return

    print("\n⏳ Consolidando dados...")
    df_total = pd.concat(frames, ignore_index=True)

    # Normaliza nome para busca
    df_total['deputado_nome_lower'] = df_total['deputado_nome'].str.lower()

    # Busca o deputado pelo nome
    matches = df_total[df_total['deputado_nome_lower'].str.contains(nome_busca.lower(), na=False)]

    if matches.empty:
        print("❌ Deputado não encontrado nos dados.")
        return

    # Descobre os candidatos únicos
    candidatos = matches[['deputado_id', 'deputado_nome', 'deputado_siglaUf']].drop_duplicates()

    if len(candidatos) > 1:
        print("⚠️ Múltiplos deputados encontrados:")
        print(candidatos.to_string(index=False))
        return

    dep_id = candidatos.iloc[0]['deputado_id']
    dep_nome = candidatos.iloc[0]['deputado_nome']
    dep_uf = candidatos.iloc[0]['deputado_siglaUf']

    print(f"\n✅ Encontrado: {dep_nome} ({dep_uf})")

    # ── Denominador correto: total de votações únicas no plenário ──────────
    total_votacoes = df_total['idVotacao'].nunique()

    # ── Numerador: votações em que o deputado participou ───────────────────
    presencas_dep = df_total[df_total['deputado_id'] == dep_id]['idVotacao'].nunique()

    # ── Média do estado ────────────────────────────────────────────────────
    df_uf = df_total[df_total['deputado_siglaUf'] == dep_uf]

    presencas_por_dep = (
        df_uf.groupby('deputado_id')['idVotacao']
        .nunique()
        .reset_index(name='presencas')
    )

    media_uf = presencas_por_dep['presencas'].mean()
    n_deps_uf = len(presencas_por_dep)

    # ── Ranking no estado ──────────────────────────────────────────────────
    presencas_por_dep = presencas_por_dep.sort_values('presencas', ascending=False).reset_index(drop=True)
    posicao = presencas_por_dep[presencas_por_dep['deputado_id'] == dep_id].index[0] + 1

    # ── Taxas ──────────────────────────────────────────────────────────────
    taxa_dep = (presencas_dep / total_votacoes) * 100
    taxa_media = (media_uf / total_votacoes) * 100

    # ── Relatório ──────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("📊 RELATÓRIO DE ENGAJAMENTO")
    print("=" * 55)
    print(f"📅 Período analisado:          {min(anos)} – {max(anos)}")
    print(f"🗳️  Total de votações no plenário: {total_votacoes}")
    print(f"🔹 Deputados no estado ({dep_uf}):  {n_deps_uf}")

    print(f"\n📈 {dep_nome}")
    print(f"   Votações participadas:      {presencas_dep} / {total_votacoes}")
    print(f"   Taxa de presença:           {taxa_dep:.1f}%")
    print(f"   Posição no estado ({dep_uf}):  {posicao}º de {n_deps_uf}")

    print(f"\n📊 Média do estado ({dep_uf}):    {taxa_media:.1f}%")

    if taxa_dep >= taxa_media:
        diff = taxa_dep - taxa_media
        print(f"\n✅ Acima da média estadual (+{diff:.1f} p.p.)")
    else:
        diff = taxa_media - taxa_dep
        print(f"\n⚠️  Abaixo da média estadual (-{diff:.1f} p.p.)")

    # ── Salva ranking do estado ────────────────────────────────────────────
    # Enriquece com nomes
    nomes = df_uf[['deputado_id', 'deputado_nome']].drop_duplicates()
    ranking_completo = presencas_por_dep.merge(nomes, on='deputado_id', how='left')
    ranking_completo['taxa_%'] = (ranking_completo['presencas'] / total_votacoes * 100).round(2)
    ranking_completo.index += 1  # posição começa em 1

    arquivo = f"ranking_presenca_{dep_uf}_{min(anos)}_{max(anos)}.csv"
    ranking_completo.to_csv(arquivo)
    print(f"\n💾 Ranking salvo em: {arquivo}")

    return ranking_completo


# ── Entrada ────────────────────────────────────────────────────────────────

nome_busca = input("Digite o nome do deputado: ")
anos = list(range(2023, 2026))   # ajuste o intervalo conforme necessário

analisar_presenca(nome_busca, anos)
