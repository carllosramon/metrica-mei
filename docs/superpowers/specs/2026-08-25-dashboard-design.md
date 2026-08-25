# Marco 0.6 — Dashboard Design

## 1. Objetivo

O Marco 0.6 implementa o RF05 do MetricaMEI: o painel de análise consolidado do usuário autenticado. Um único endpoint devolve os números gerais da conta, calculados a partir dos conteúdos e dos snapshots de métricas já registrados nos marcos anteriores.

Ficam fora deste marco: gráficos, filtros por período, comparação entre datas, agrupamento por plataforma, paginação, exportação, integração com APIs externas e frontend. O frontend React será tratado no próximo marco e consumirá este endpoint.

## 2. Snapshots são cumulativos

O Marco 0.4 define cada métrica como um snapshot acumulado: os valores representam os totais observados na plataforma naquela data de referência, e não o incremento do dia.

A consequência para o painel é decisiva: **somar todos os snapshots de um conteúdo inflaciona os números**. Um conteúdo com cinco medições apareceria com aproximadamente cinco vezes as visualizações reais, porque cada snapshot já contém tudo o que veio antes.

O painel usa, para cada conteúdo, **somente o snapshot mais recente**. Os totais da conta são a soma desses snapshots mais recentes, um por conteúdo.

O critério de "mais recente" é `data_referencia DESC, id DESC` — a mesma ordenação que `MetricRepository.list_by_content` já aplica, incluindo o desempate por identificador.

## 3. Indicadores

```text
total_conteudos           quantidade de conteúdos do usuário
conteudos_com_metricas    quantos deles já têm ao menos um snapshot
total_visualizacoes       soma dos snapshots mais recentes
total_curtidas            soma dos snapshots mais recentes
total_comentarios         soma dos snapshots mais recentes
total_compartilhamentos   soma dos snapshots mais recentes
total_alcance             soma dos snapshots mais recentes
engajamento_geral         índice consolidado da conta
melhores_conteudos        ranking dos conteúdos por engajamento
```

`conteudos_com_metricas` existe porque `total_conteudos` sozinho engana: um usuário com doze conteúdos e dois medidos veria totais baixos sem entender que a base é pequena, não o desempenho.

## 4. Engajamento geral

O índice da conta é calculado sobre os totais, e não como média dos engajamentos individuais:

```text
(total_curtidas + total_comentarios + total_compartilhamentos)
--------------------------------------------------------------- × 100
                       total_alcance
```

A conta reaproveita `calculate_engagement` de `app/services/engagement.py`, exatamente como o Marco 0.5 previu. Nenhuma fórmula é reimplementada.

A escolha por consolidar em vez de tirar a média das médias evita distorção por escala: um conteúdo com alcance 10 e uma curtida tem engajamento de 10%, e na média aritmética pesaria igual a um conteúdo com alcance 50.000. O índice consolidado responde "qual o engajamento da minha conta", que é a pergunta do painel.

O nome é `engajamento_geral`, e não `engajamento_medio`, porque o valor não é uma média — chamá-lo assim descreveria errado o que a conta faz.

Quando `total_alcance` é zero, o campo vem `null`, pela mesma razão do Marco 0.5: o índice não é calculável, e zero significaria desempenho nulo.

## 5. Ranking

`melhores_conteudos` traz no máximo cinco conteúdos, ordenados por engajamento decrescente, com desempate por `data_referencia DESC` e `conteudo_id DESC`.

Ficam fora do ranking os conteúdos sem nenhum snapshot e os conteúdos cujo snapshot mais recente tem `alcance = 0`. Nos dois casos não existe engajamento comparável, e incluí-los como zero rebaixaria injustamente o conteúdo no ranking.

Cada item carrega `conteudo_id`, `titulo`, `plataforma`, `engajamento` e `data_referencia` — o suficiente para a tabela do painel identificar o conteúdo e a data da medição sem uma segunda requisição.

## 6. Arquitetura

O marco acrescenta uma fatia completa, sem tocar nas existentes:

```text
DashboardController  →  GET /painel
DashboardService     →  agrega, sem persistir
```

`DashboardService` recebe `ContentRepository` e `MetricRepository`, os mesmos contratos já usados por `MetricService`. Nenhum método novo é adicionado a nenhum dos dois Protocols.

O serviço percorre os conteúdos do usuário e, para cada um, pede seus snapshots ao repositório de métricas, tomando o primeiro da lista já ordenada.

Isso significa uma consulta por conteúdo, além da consulta que lista os conteúdos. A alternativa seria um método novo no `MetricRepository` com JOIN em `conteudos`, mas o repositório de métricas hoje conhece apenas a própria tabela, e acoplá-lo a `ContentModel` para servir um único endpoint custa mais do que economiza na escala de um MEI. Se a base crescer a ponto de o painel ficar lento, a troca é local: o serviço passa a chamar um método agregador novo e o resto não muda.

## 7. Domínio

`app/domain/dashboard.py` define dois dataclasses de leitura:

- `DashboardContent`: `conteudo_id`, `titulo`, `plataforma`, `engajamento`, `data_referencia`;
- `Dashboard`: os sete contadores, `engajamento_geral` e `melhores_conteudos`.

Nenhum dos dois é persistido. Assim como `MetricWithEngagement` no Marco 0.5, existem para transportar dado derivado até o `response_model` sem contaminar `Content` nem `Metric`.

`DashboardContent.engajamento` é `float`, não `float | None`: conteúdo sem índice calculável não entra no ranking, então o campo nunca é nulo dentro dele.

## 8. Endpoint

```text
GET /painel
```

Protegido por JWT, como todas as rotas do projeto. Devolve sempre `200`.

Usuário sem conteúdo nenhum recebe um painel zerado, com `engajamento_geral` nulo e `melhores_conteudos` vazio. Ausência de dados não é erro: é o estado inicial de toda conta recém-criada, e um `404` obrigaria o frontend a tratar como falha o que é a primeira tela do usuário.

O painel só enxerga conteúdos do próprio usuário, porque parte de `ContentRepository.list_by_user`. Não existe caminho pelo qual um conteúdo de outra conta entre na soma.

## 9. Estratégia de testes

### Unitários

`test_dashboard_service.py`, com repositórios em memória:

- painel vazio devolve zeros, `engajamento_geral` nulo e ranking vazio;
- conteúdo sem métrica conta em `total_conteudos` mas não em `conteudos_com_metricas`;
- apenas o snapshot mais recente entra na soma, mesmo com vários registrados;
- desempate de "mais recente" por identificador quando a data se repete não se aplica, pois a data é única por conteúdo — o teste cobre a ordenação por data;
- `engajamento_geral` é calculado sobre os totais, não como média das médias;
- `total_alcance` zero devolve `engajamento_geral` nulo;
- ranking ordena por engajamento decrescente e limita a cinco;
- ranking exclui conteúdo sem métrica e conteúdo com alcance zero;
- conteúdo de outro usuário não entra em nenhum indicador.

### HTTP

`test_dashboard_api.py`, com a fixture `client`:

- `200` com o painel consolidado após cadastrar conteúdos e métricas;
- painel zerado para usuário recém-criado;
- `401` sem token e com token inválido;
- painel de um usuário não enxerga conteúdo de outro.

## 10. Critérios de aceite

O Marco 0.6 estará concluído quando:

- `GET /painel` devolver os indicadores consolidados do usuário autenticado;
- apenas o snapshot mais recente de cada conteúdo entrar nas somas;
- `engajamento_geral` reaproveitar `calculate_engagement` sobre os totais;
- alcance total zero devolver `null`;
- o ranking excluir conteúdos sem índice calculável e respeitar o limite;
- nenhuma tabela, coluna ou migration ser criada;
- nenhum método novo entrar nos Protocols de repositório;
- os testes anteriores permanecerem verdes.

## 11. Fora de escopo

Não entram neste marco: gráficos, filtros por período, comparação entre snapshots, crescimento, agrupamento por plataforma, paginação, exportação, APIs externas e frontend.

## 12. Próximo marco

O próximo marco tratará do frontend em React, que consumirá `GET /painel` para os cartões de topo e o ranking.

## 13. Definition of Done

O Marco 0.6 estará concluído quando um usuário autenticado puder consultar, em uma única requisição, os totais consolidados da sua conta, o índice de engajamento geral e o ranking dos seus melhores conteúdos, calculados sobre o snapshot mais recente de cada conteúdo, sem persistir nada e sem alterar as camadas entregues nos marcos anteriores.
