# RF05 — Painel de análise

**Projeto:** MetricaMEI
**Situação:** atendido

## 1. Enunciado

> O sistema deve apresentar indicadores consolidados em um painel de análise.

A seção 7 do documento de projeto detalha o que o painel deve conter:

> - Totais gerais (soma de visualizações, curtidas, etc.)
> - Desempenho por plataforma
> - Ranking dos conteúdos de maior alcance

## 2. O que o enunciado não resolve

O enunciado isolado não é verificável: não diz sobre quais dados os indicadores são calculados nem em que recorte de tempo. Duas implementações com resultados divergentes em centenas por cento atenderiam ao mesmo texto.

A lista da seção 7 fecha o *quê*. As decisões abaixo fecham o *como*, e cada uma está registrada com a sua justificativa.

## 3. Regra de consolidação

**Cada conteúdo entra nos totais uma única vez, pela sua medição mais recente.**

Esta é a decisão mais importante do requisito, e não decorre do RF05: decorre do RF03. As métricas são snapshots cumulativos, em que cada registro contém o total observado até a sua data de referência.

Somar todo o histórico contaria repetidamente o mesmo desempenho. Um conteúdo com cinco medições apareceria com aproximadamente cinco vezes as visualizações reais, e o erro cresceria conforme o usuário registrasse mais medições — ou seja, o painel ficaria progressivamente mais errado justamente para os usuários mais assíduos.

O critério de "mais recente" é a maior `data_referencia`, com desempate pelo maior identificador.

## 4. Totais gerais

```text
total_conteudos           quantidade de conteúdos do usuário
conteudos_com_metricas    quantos deles já têm ao menos uma medição
total_visualizacoes       soma das medições mais recentes
total_curtidas            soma das medições mais recentes
total_comentarios         soma das medições mais recentes
total_compartilhamentos   soma das medições mais recentes
total_alcance             soma das medições mais recentes
engajamento_geral         índice consolidado da conta
```

`conteudos_com_metricas` não estava na lista da seção 7 e foi acrescentado porque `total_conteudos` sozinho induz a erro de leitura: um usuário com doze conteúdos e dois medidos veria totais baixos e concluiria mau desempenho, quando a base de medição é que é pequena.

### Engajamento geral

Calculado sobre os totais, reaproveitando a fórmula do RF04:

```text
(total_curtidas + total_comentarios + total_compartilhamentos)
--------------------------------------------------------------- × 100
                       total_alcance
```

E **não** como média aritmética dos índices individuais. A média trata todos os conteúdos como equivalentes: um conteúdo visto por dez pessoas e curtido por uma teria 10% e pesaria o mesmo que um visto por cinquenta mil. Conteúdos de alcance minúsculo, que são estatisticamente ruidosos, dominariam o indicador da conta.

O campo se chama `engajamento_geral`, e não `engajamento_medio`, porque o valor não é uma média.

Alcance total zero devolve nulo, pela mesma razão do RF04.

## 5. Desempenho por plataforma

Para cada rede, os mesmos cinco totais mais a quantidade de conteúdos medidos e o índice consolidado daquela plataforma.

Ordenado por alcance total decrescente: a rede onde o usuário alcança mais pessoas é a informação que ele procura primeiro.

### Agrupamento ignora maiúsculas

`plataforma` é texto livre digitado pelo usuário (RF02). Agrupar pela string exata partiria "Instagram" e "instagram" em duas linhas da mesma rede, o que o usuário leria como defeito.

Entre grafias concorrentes prevalece a do conteúdo cadastrado primeiro. É uma regra determinística: sem ela, o rótulo mudaria conforme a ordenação da listagem.

## 6. Ranking dos conteúdos de maior alcance

No máximo cinco conteúdos, ordenados por alcance decrescente, com desempate por data de referência e identificador.

Cada item traz identificador, título, plataforma, alcance, índice de engajamento e data da medição.

O índice aparece ao lado do alcance de propósito. Sem ele, a leitura natural do ranking seria que o conteúdo mais alcançado é também o de melhor desempenho — e frequentemente não é.

Entram no ranking **todos** os conteúdos com medição, inclusive os de alcance zero, que ocupam a última posição. Alcance zero é medição real e ordenável; o que fica sem valor nesse caso é apenas o índice de engajamento.

Ficam de fora apenas os conteúdos sem nenhuma medição, que não têm alcance a comparar.

O limite de cinco é decisão de projeto: o painel destaca os melhores casos para orientar a próxima publicação, e uma lista longa deixaria de ser destaque para virar a listagem completa, que o RF02 já oferece.

## 7. Recorte temporal

**O painel não tem filtro de período.** Reflete o estado atual da conta, considerando a medição mais recente de cada conteúdo, independentemente de quando foi registrada.

O documento de projeto não define período de análise em nenhum requisito, e adotar um por conta própria criaria comportamento que ninguém pediu e que o usuário não conseguiria desligar.

Há ainda uma razão semântica: filtro de período sobre dado cumulativo é ambíguo. "Painel de agosto" pode significar o estado da conta ao fim de agosto ou o crescimento ocorrido durante agosto — respostas diferentes, e a segunda é análise de evolução, não consolidação. Se um período for exigido no futuro, precisa vir com a definição de qual das duas semânticas se aplica.

## 8. Entrega em duas partes

O verbo do enunciado é **apresentar**, e apresentação é responsabilidade da interface.

| Parte | Descrição | Entrega |
|---|---|---|
| RF05.1 | Disponibilizar os indicadores consolidados em `GET /painel` | Marco 0.6 |
| RF05.2 | Apresentá-los no painel de análise | Marco 0.7 e 0.9 |

Ambas estão concluídas.

## 9. Estado vazio

Conta sem conteúdos recebe `200` com todos os contadores em zero, índice nulo e as duas listas vazias.

Ausência de dados não é erro: é o estado inicial de toda conta recém-criada. Responder `404` obrigaria a interface a tratar como falha aquilo que é a primeira tela do usuário. Cada seção do painel exibe uma orientação do que fazer para preenchê-la, em vez de área em branco.

## 10. Fora do escopo

| Item | Motivo |
|---|---|
| Gráficos | a seção 9 do documento os marca como planejados e não detalhados |
| Crescimento entre medições | exige comparar snapshots; é análise de evolução, não consolidação |
| Filtro por período | ver seção 7 |
| Agrupamento por tipo de conteúdo | a seção 7 pede agrupamento por plataforma, não por tipo |
| Paginação | a resposta tem tamanho limitado por construção |
| Integração com APIs das plataformas | fora do escopo do MVP; os dados são de entrada manual |

## 11. Critérios de aceite

1. `GET /painel` responde `200` com os totais gerais, o desempenho por plataforma e o ranking;
2. cada conteúdo contribui apenas com a sua medição mais recente;
3. conteúdos sem medição são contados em `total_conteudos` e não em `conteudos_com_metricas`;
4. `engajamento_geral` é calculado sobre os totais, com duas casas decimais;
5. `engajamento_geral` é nulo quando o alcance total é zero;
6. o desempenho por plataforma agrupa as redes ignorando diferença de maiúsculas;
7. o desempenho por plataforma é ordenado por alcance decrescente;
8. o ranking é ordenado por alcance decrescente e limitado a cinco itens;
9. o ranking inclui conteúdo com alcance zero e exclui conteúdo sem medição;
10. conteúdos de outros usuários não influenciam nenhum indicador;
11. conta sem conteúdos recebe `200` com o painel zerado;
12. requisição sem token válido recebe `401`;
13. a interface apresenta as três seções, com estado vazio orientado.

## 12. Rastreabilidade

| Critério | Verificado em |
|---|---|
| 1 a 5, 9, 10 | `tests/unit/test_dashboard_service.py` |
| 6, 7 | `tests/unit/test_dashboard_service.py` |
| 8 | `tests/unit/test_dashboard_service.py`, `tests/integration/test_dashboard_api.py` |
| 11, 12 | `tests/integration/test_dashboard_api.py` |
| 13 | `frontend/src/paginas/Painel.test.tsx`, `frontend/e2e/jornada.spec.ts` |

Requisitos relacionados: RF02 e RF03 (dados de origem), RF04 (fórmula reaproveitada), RF06 (isolamento), RNF01, RNF02, RNF03.

O detalhamento técnico está em `docs/superpowers/specs/2026-08-25-dashboard-design.md`.
