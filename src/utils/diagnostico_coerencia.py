"""
Diagnóstico: encontra deputados que têm proposições E aprovações no banco.
Rode com: python diagnostico_coerencia.py
"""
from database.connection import get_connection


def main():
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    print("=" * 60)
    print("1. DEPUTADOS COM PROPOSIÇÕES APROVADAS")
    print("=" * 60)
    cursor.execute("""
        SELECT d.id, d.nome, d.sigla_partido, d.sigla_uf,
               COUNT(*) AS total_aprovadas
        FROM proposicoes p
        JOIN deputados d ON d.id = p.id_deputado
        WHERE p.situacao LIKE '%Aprovad%'
        GROUP BY d.id, d.nome, d.sigla_partido, d.sigla_uf
        ORDER BY total_aprovadas DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            print(f"  {r['nome']} ({r['sigla_partido']}-{r['sigla_uf']}) — {r['total_aprovadas']} aprovada(s) | id={r['id']}")
    else:
        print("  ❌ Nenhum deputado com proposição aprovada encontrado.")

    print()
    print("=" * 60)
    print("2. DEPUTADOS COM PROPOSIÇÕES (qualquer situação)")
    print("=" * 60)
    cursor.execute("""
        SELECT d.id, d.nome, d.sigla_partido, d.sigla_uf,
               COUNT(*) AS total
        FROM proposicoes p
        JOIN deputados d ON d.id = p.id_deputado
        GROUP BY d.id, d.nome, d.sigla_partido, d.sigla_uf
        ORDER BY total DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            print(f"  {r['nome']} ({r['sigla_partido']}-{r['sigla_uf']}) — {r['total']} proposição(ões) | id={r['id']}")
    else:
        print("  ❌ Nenhum deputado com proposições encontrado.")

    print()
    print("=" * 60)
    print("3. SITUAÇÕES DISTINTAS NA TABELA PROPOSICOES")
    print("   (para verificar o valor exato do campo 'situacao')")
    print("=" * 60)
    cursor.execute("""
        SELECT situacao, COUNT(*) AS total
        FROM proposicoes
        WHERE situacao != ''
        GROUP BY situacao
        ORDER BY total DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            print(f"  [{r['total']:>5}]  {r['situacao']}")
    else:
        print("  ❌ Nenhuma situação encontrada.")

    print()
    print("=" * 60)
    print("4. VÍNCULOS EM PROPOSICOES_TEMAS")
    print("=" * 60)
    cursor.execute("SELECT COUNT(*) AS total FROM proposicoes_temas")
    r = cursor.fetchone()
    print(f"  Total de vínculos proposição×tema: {r['total']}")

    print()
    print("=" * 60)
    print("5. VÍNCULOS EM DISCURSOS_TEMAS")
    print("=" * 60)
    cursor.execute("SELECT COUNT(*) AS total FROM discursos_temas")
    r = cursor.fetchone()
    print(f"  Total de vínculos discurso×tema: {r['total']}")

    print()
    print("=" * 60)
    print("6. AMOSTRA DE KEYWORDS/SUMÁRIO DOS DISCURSOS")
    print("   (para verificar se o matching por texto faz sentido)")
    print("=" * 60)
    cursor.execute("""
        SELECT id, keywords, LEFT(sumario, 80) AS sumario_resumido
        FROM discursos
        WHERE keywords != '' OR sumario != ''
        LIMIT 5
    """)
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            print(f"  id={r['id']}")
            print(f"    keywords : {r['keywords']}")
            print(f"    sumario  : {r['sumario_resumido']}")
    else:
        print("  ❌ Nenhum discurso com keywords ou sumário.")

    cursor.close()
    conn.close()
    print()
    print("✅ Diagnóstico concluído.")


if __name__ == "__main__":
    main()