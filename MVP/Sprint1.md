

# 📌 MVP - Radar Cidadão

## 🎯 Objetivo do MVP
O propósito deste MVP é validar a viabilidade de uma plataforma centralizada que simplifica a análise de dados públicos de parlamentares.
- **Qual problema resolve?** A dificuldade de acesso e compreensão de dados complexos sobre o desempenho de deputados federais.
- **Qual hipótese será validada?** Eleitores utilizam ferramentas visuais e neutras para fundamentar sua decisão de voto quando a informação é apresentada de forma clara e comparativa.
- **Qual valor será entregue ao usuário final?** Transparência e agilidade na avaliação de candidatos à reeleição para as eleições de outubro de 2026.

---

## 📝 Descrição da Solução
Desenvolvimento de uma ferramenta de análise que permite a consulta rápida e visual do histórico de deputados federais.
- **Funcionalidades principais incluídas:** Busca por filtros (estado, partido, nome), listagem paginada e perfil detalhado com indicadores de desempenho (presença, gastos, projetos e coerência).
- **Limitações conhecidas:** Nesta etapa, os dados serão focados exclusivamente em deputados candidatos à reeleição.
- **Escopo reduzido:** Foco total na visualização de dados e usabilidade de filtros, sem funcionalidades de interação social ou comentários nesta fase.

---

## 👥 Personas / Usuários-Alvo
- **Persona 1: O Eleitor Consciente.** Cidadão que deseja renovar seu voto ou confirmar a reeleição de seu candidato, mas não tem tempo para buscar dados brutos em portais governamentais. Busca agilidade e clareza.
- **Persona 2: O Educador/Estudante.** Profissionais ou acadêmicos que precisam de fontes neutras e baseadas em fatos para fomentar discussões sobre política e cidadania.

---

## 🔑 User Stories (Backlog do MVP)
| ID  | User Story | Prioridade | Estimativa |
|-----|------------|------------|------------|
| US1 | Como eleitor, quero filtrar deputados por estado, partido ou nome, para encontrar rapidamente o candidato de minha preferência. | Alta/Meta | 8 pontos |
| US2 | Como eleitor, quero visualizar uma lista paginada dos candidatos do meu estado, para conhecer as opções de voto. | Alta | 8 pontos |
| US3 | Como eleitor, quero visualizar uma síntese do deputado (foto, partido, desempenho e gráficos de barras), para decidir meu voto com agilidade. | Alta | 13 pontos |
| US4 | Como eleitor, quero visualizar o percentual de presença do deputado comparado à média, para avaliar seu comprometimento. | Baixa | 8 pontos |

---

## 📅 Sprint(s) Relacionadas
| Sprint | Entregas Principais | Status |
|--------|---------------------|--------|
| 01 | Sistema de filtros, listagem de candidatos e visualização do perfil com gráficos. | Em andamento |

---

## 📊 Critérios de Aceitação
- O sistema deve permitir que o usuário encontre qualquer deputado da base de dados em menos de 3 comandos ou cliques através dos filtros.
- O sistema deve renderizar corretamente os gráficos de barras horizontais com dados reais extraídos via Python.
- O perfil deve exibir de forma clara a classificação de desempenho do parlamentar.

---

## 🚀 Próximos Passos
- **Desenvolvimento de uma página WEB responsiva.**
- Histórico de votações em temas específicos de interesse público.
- Expansão da base de dados para outros cargos legislativos e futuras janelas partidárias.

---

## 📂 Anexos / Evidências
- **Tecnologias:** Python (Processamento de Dados/Google Colab).
- **Repositório:** [GitHub - Radar Cidadão](https://github.com/ninaduquehc/API/tree/main)