# 🛰️ Radar Cidadão
### Avaliação de Deputados Federais Candidatos à Reeleição

![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)

## 🎯 Objetivo do Projeto
O objetivo central do **Radar Cidadão** é desenvolver uma aplicação que transforme dados públicos complexos em informações claras e compreensíveis para a sociedade. O foco é permitir que eleitores e educadores avaliem o desempenho de parlamentares que buscam a reeleição nas eleições de 2026, utilizando ferramentas simples, neutras e baseadas em fatos.

---

## 📌 Índice
* [Equipe](#-equipe)
* [Tecnologias Utilizadas](#-tecnologias-utilizadas)
* [Padrões de Qualidade (DoR/DoD)](#-padrões-de-qualidade)
* [Product Backlog](#-product-backlog)
* [Registro das Sprints](#-registro-das-sprints)
* [MVPs](#mvps)

---

## 👥 Equipe

| Função | Nome | Social |
| :--- | :--- | :---: |
| **Product Owner** | Guilherme de Lima Leite | [![Linkedin](https://img.shields.io/badge/Linkedin-blue?style=flat-square&logo=Linkedin&logoColor=white)](https://www.linkedin.com/in/guilherme-de-lima-leite-7043282ba/) [![GitHub](https://img.shields.io/badge/GitHub-111217?style=flat-square&logo=github&logoColor=white)](https://github.com/Guilherme-Leite1701) |
| **Scrum Master** | Marina Duque de Holanda Cavalcanti | [![Linkedin](https://img.shields.io/badge/Linkedin-blue?style=flat-square&logo=Linkedin&logoColor=white)](https://www.linkedin.com/in/marina-cavalcanti-53b3503b8/) [![GitHub](https://img.shields.io/badge/GitHub-111217?style=flat-square&logo=github&logoColor=white)](https://github.com/ninaduquehc) |
| Team Member | Guilherme Machado Silva | [![Linkedin](https://img.shields.io/badge/Linkedin-blue?style=flat-square&logo=Linkedin&logoColor=white)](https://www.linkedin.com/in/guilherme-machado-silva-ba2332323/) [![GitHub](https://img.shields.io/badge/GitHub-111217?style=flat-square&logo=github&logoColor=white)](https://github.com/MachadoGuilherme1206) |
| Team Member | Leonardo Vilela Matiusso | [![Linkedin](https://img.shields.io/badge/Linkedin-blue?style=flat-square&logo=Linkedin&logoColor=white)](https://www.linkedin.com/in/leonardo-vilela-matiusso-94b405374/) [![GitHub](https://img.shields.io/badge/GitHub-111217?style=flat-square&logo=github&logoColor=white)](https://github.com/leovmatiusso) |
| Team Member | Murilo Alvarenga de Souza | [![GitHub](https://img.shields.io/badge/GitHub-111217?style=flat-square&logo=github&logoColor=white)](https://github.com/MuriloAlvarenga) |
| Team Member | Nathan Ariel Damasio Leão | [![Linkedin](https://img.shields.io/badge/Linkedin-blue?style=flat-square&logo=Linkedin&logoColor=white)](https://www.linkedin.com/in/nathan-ariel-damasio-le%C3%A3o-7a64522b5/) [![GitHub](https://img.shields.io/badge/GitHub-111217?style=flat-square&logo=github&logoColor=white)](https://github.com/Nathan-ADL) |
| Team Member | Samuel Estevão Pereira Martins | [![Linkedin](https://img.shields.io/badge/Linkedin-blue?style=flat-square&logo=Linkedin&logoColor=white)](https://www.linkedin.com/in/samuel-martins-210s507em) [![GitHub](https://img.shields.io/badge/GitHub-111217?style=flat-square&logo=github&logoColor=white)](https://github.com/SamuelMartins00) |

---

## 🛠 Tecnologias Utilizadas

<div align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5" />
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3" />
  <img src="https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" alt="Bootstrap" />
  <img src="https://img.shields.io/badge/Jira-0052CC?style=for-the-badge&logo=jira&logoColor=white" alt="Jira" />
  <img src="https://img.shields.io/badge/Google%20Colab-F9AB00?style=for-the-badge&logo=googlecolab&logoColor=white" alt="Google Colab" />
</div>

---

## 🎯 Padrões de Qualidade

### 🏁 DoR (Definition of Ready)
Para que uma tarefa seja considerada pronta para desenvolvimento, ela deve:
* Estar escrita no formato: *"Como [persona], quero [ação] para que [objetivo]"*.
* Conter critérios de aceitação definidos.
* Ter subtarefas divididas a partir das User Stories (US).
* Possuir priorização atribuída (Alta, Média, Baixa).
* Possuir estimativas de esforço atribuídas.

### 🏆 DoD (Definition of Done)
Uma entrega é considerada concluída quando:
* O código do projeto estiver finalizado e funcional.
* A documentação da API estiver concluída.

### ⚖️ Critérios de Permanência do Time
* **Report Obrigatório:** Atualização constante do progresso das tarefas.
* **Colaboração Ativa:** Quem concluir suas tarefas antecipadamente deve ajudar os demais.
* **Comportamento Profissional:** Ética e respeito em todas as interações do projeto.

---

## 📋 Product Backlog

| Rank | Prioridade | User Story | Sprint |
|:---:|:---:|:---|:---:|
| 1 | Alta/Meta | Como eleitor, quero filtrar deputados por estado, partido ou nome para busca rápida. | 1 |
| 2 | Alta | Como eleitor, quero visualizar uma lista paginada dos candidatos do meu estado. | 1 |
| 3 | Alta | Como eleitor, quero visualizar uma síntese com foto, gráficos de presença, gastos e coerência. | 1 |
| 4 | Baixa | Como eleitor, quero comparar o percentual de presença com a média estadual. | 1 |
| 5 | Média | **US05:** Como eleitor, quero ver as despesas em R$, % da cota e equivalência em cestas básicas. | 2 |
| 6 | Média | **US06:** Como eleitor, quero ver a participação em votações comparada à média estadual. | 2 |
| 7 | Alta | **US07:** Como eleitor, quero ver as propostas apresentadas por tipo (PL, PDC, PEC) e rankings. | 2 |
| 8 | Alta | **US08:** Como eleitor, quero visualizar as propostas aprovadas para avaliar a efetividade. | 2 |

---

## 🚀 Registro das Sprints

| Sprint | Previsão | Status | Histórico |
|:---:|:---:|:---:|:---|
| 01 | 06/04/2026 | 🟢 Concluído | Implementação dos filtros e visualização básica. |
| 02 | 04/05/2026 | ⚪ Em andamento | Detalhamento de gastos e métricas de efetividade. |

---

## MVPs

### Sprint 1
* 📺 [Clique aqui para assistir o vídeo de demonstração](https://youtu.be/sBF46geoj6Y)
* 📄 [Clique aqui para acessar o arquivo .md do MVP da Sprint](https://github.com/ninaduquehc/API/blob/main/MVP/Sprint1.md)
