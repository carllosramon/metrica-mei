# RF05 — Painel de análise

**Projeto:** MetricaMEI
**Data:** 2026-08-25
**Situação:** especificado e implementado no backend

## 1. Enunciado original

> O sistema deve apresentar indicadores consolidados em um painel de análise.

## 2. Por que o enunciado precisou ser refinado

O enunciado não é verificável na forma em que está. Ele não diz **quais** indicadores, **sobre quais dados** eles são calculados, nem **em que recorte de tempo**. Duas implementações radicalmente diferentes — uma somando todo o histórico, outra usando só a última medição — atenderiam igualmente ao texto, produzindo números que divergem em centenas por cento.

Como não existe protótipo de tela nem definição de período no documento de requisitos, as lacunas foram fechadas por decisão de projeto. Cada decisão está registrada abaixo com a sua justificativa, para que a escolha possa ser auditada e, se necessário, revista.

## 3. Decomposição do requisito

O verbo do enunciado é **apresentar**. Apresentar é responsabilidade da interface, não do backend, que apenas disponibiliza os dados. O requisito foi decomposto em duas partes com entregas distintas:

| Parte | Descrição | Entrega |
|---|---|---|
| RF05.1 | O sistema deve disponibilizar os indicadores consolidados do usuário autenticado | Marco 0.6 — concluída |
| RF05.2 | O sistema deve apresentar esses indicadores em um painel de análise | Marco 0.7 — frontend |

A decomposição evita declarar o requisito como concluído enquanto não houver tela, e ao mesmo tempo permite verificar a parte de dados de forma independente e automatizada.

## 4. Indicadores especificados

O painel disponibiliza nove indicadores, obtidos em uma única requisição a `GET /painel`:

| Indicador | Descrição |
|---|---|
| `total_conteudos` | Quantidade de conteúdos cadastrados pelo usuário |
| `conteudos_com_metricas` | Quantos desses conteúdos possuem ao menos uma medição |
| `total_visualizacoes` | Soma das visualizações |
| `total_curtidas` | Soma das curtidas |
| `total_comentarios` | Soma dos comentários |
| `total_compartilhamentos` | Soma dos compartilhamentos |
| `total_alcance` | Soma do alcance |
| `engajamento_geral` | Índice de engajamento consolidado da conta |
| `melhores_conteudos` | Ranking dos conteúdos de melhor desempenho |

### Justificativa da escolha

Os cinco totais são os mesmos campos que o RF03 já obriga o usuário a registrar. Consolidar exatamente o que é coletado mantém o painel rastreável: todo número exibido tem origem verificável em um registro que o próprio usuário inseriu, sem estimativa ou dado derivado de fonte externa.

`engajamento_geral` é o único indicador calculado, e reaproveita a fórmula já definida pelo RF04. O painel não introduz nenhuma regra de cálculo nova.

`conteudos_com_metricas` foi incluído porque `total_conteudos` isolado induz a erro de leitura: um usuário com doze conteúdos e dois medidos veria totais baixos e concluiria que teve mau desempenho, quando na verdade a base de medição é pequena. O par de contadores torna a cobertura dos dados explícita.

`melhores_conteudos` responde à pergunta que motiva o sistema — qual conteúdo dá mais retorno — que nenhum total agregado consegue responder.

## 5. Regra de consolidação

**Cada conteúdo entra nos totais uma única vez, pela sua medição mais recente.**

Esta é a regra mais importante da especificação, e não decorre do enunciado do RF05: decorre do RF03. As métricas são snapshots cumulativos, em que cada registro contém o total observado na plataforma até a sua data de referência, e não o incremento do dia.

Somar todo o histórico contaria repetidamente o mesmo desempenho. Um conteúdo com cinco medições apareceria com aproximadamente cinco vezes as visualizações que realmente teve, e o erro cresceria à medida que o usuário registrasse mais medições — ou seja, o painel ficaria progressivamente mais errado justamente para os usuários mais assíduos.

O critério de "mais recente" é a maior `data_referencia`, com desempate pelo maior identificador.

## 6. Consolidação do engajamento

O índice da conta é calculado sobre os totais:

```text
(total_curtidas + total_comentarios + total_compartilhamentos)
--------------------------------------------------------------- × 100
                       total_alcance
```

E **não** como média aritmética dos engajamentos individuais.

### Justificativa

A média das médias trata todos os conteúdos como equivalentes, independentemente da audiência que alcançaram. Um conteúdo visto por dez pessoas e curtido por uma tem engajamento de 10%, e na média pesaria o mesmo que um conteúdo visto por cinquenta mil.

O efeito prático é perverso: conteúdos de alcance minúsculo, que são estatisticamente ruidosos, dominariam o indicador da conta. O índice consolidado pondera naturalmente pela audiência e responde à pergunta correta — qual o engajamento da conta como um todo.

Por isso o campo se chama `engajamento_geral`, e não `engajamento_medio`: o valor não é uma média, e nomeá-lo assim descreveria errado o que a conta faz.

Quando `total_alcance` é zero, o indicador é `null`, e não zero, pela mesma razão já estabelecida no RF04: o índice não é calculável, e zero significaria desempenho nulo.

## 7. Ranking

`melhores_conteudos` contém no máximo **cinco** conteúdos, ordenados por engajamento decrescente, com desempate por data de referência e identificador, ambos decrescentes.

Ficam fora do ranking os conteúdos sem nenhuma medição e os conteúdos cuja medição mais recente tem alcance zero. Nos dois casos não existe índice comparável, e atribuir zero rebaixaria injustamente um conteúdo que não teve desempenho ruim — apenas não teve desempenho medido.

O limite de cinco é uma decisão de projeto: o painel destaca os melhores casos para orientar a próxima publicação, e uma lista longa deixaria de ser destaque para virar a listagem completa, que o RF02 já oferece em `GET /conteudos`.

Cada item do ranking carrega identificador, título, plataforma, engajamento e data de referência, o suficiente para a interface identificar o conteúdo e a data da medição sem uma segunda requisição.

## 8. Recorte temporal

**O painel não tem filtro de período.** Ele reflete o estado atual da conta, considerando a medição mais recente de cada conteúdo, independentemente de quando foi registrada.

### Justificativa

O documento de requisitos não define período de análise, e adotar um por conta própria criaria um comportamento que ninguém pediu e que o usuário não teria como desligar.

Além disso, filtro de período sobre dados cumulativos é semanticamente ambíguo. "Painel de agosto" pode significar o estado da conta ao fim de agosto, ou o crescimento ocorrido durante agosto — duas respostas diferentes, e a segunda exige comparar snapshots, que é análise de crescimento, não consolidação.

Consolidação sem recorte é a leitura mais direta do enunciado e a que não inventa requisito. Se um período for exigido no futuro, ele deve vir acompanhado da definição de qual das duas semânticas se aplica.

## 9. Fora do escopo

Não fazem parte deste requisito, e cada exclusão tem motivo:

| Item | Motivo |
|---|---|
| Gráficos | apresentação visual, pertence ao RF05.2 |
| Crescimento entre medições | exige comparar snapshots; é análise de evolução, não consolidação |
| Agrupamento por plataforma ou tipo | não solicitado; multiplicaria a resposta sem demanda |
| Paginação | a resposta tem tamanho fixo de nove campos |
| Exportação | não solicitado em nenhum requisito |
| Integração com APIs das plataformas | os dados são de entrada manual, conforme o RF03 |

## 10. Regras de acesso

O painel é restrito ao usuário autenticado e considera exclusivamente os conteúdos de sua propriedade, conforme o RF06. Não há caminho pelo qual um conteúdo de outra conta influencie qualquer indicador, porque a consolidação parte da listagem de conteúdos do próprio usuário.

O acesso sem token válido é rejeitado com `401`, como nas demais rotas protegidas.

## 11. Estado vazio

Uma conta sem conteúdos recebe `200` com todos os contadores em zero, `engajamento_geral` nulo e ranking vazio.

Ausência de dados não é erro: é o estado inicial de toda conta recém-criada. Responder `404` obrigaria a interface a tratar como falha aquilo que é a primeira tela do usuário, e a distinguir "painel inexistente" de "erro real" pelo mesmo código de status.

## 12. Critérios de aceite

O RF05.1 é considerado atendido quando, para um usuário autenticado:

1. `GET /painel` responde `200` com os nove indicadores especificados;
2. cada conteúdo contribui para os totais apenas com a sua medição mais recente;
3. conteúdos sem medição são contados em `total_conteudos` e não em `conteudos_com_metricas`;
4. `engajamento_geral` corresponde ao cálculo sobre os totais, com duas casas decimais;
5. `engajamento_geral` é nulo quando o alcance total é zero;
6. o ranking está ordenado por engajamento decrescente e limitado a cinco itens;
7. o ranking exclui conteúdos sem medição e conteúdos com alcance zero;
8. conteúdos de outros usuários não influenciam nenhum indicador;
9. uma conta sem conteúdos recebe `200` com o painel zerado;
10. requisições sem token válido recebem `401`.

## 13. Verificação

Todos os dez critérios são cobertos por testes automatizados:

- `backend/tests/unit/test_dashboard_service.py` — critérios 2 a 8;
- `backend/tests/integration/test_dashboard_api.py` — critérios 1, 8, 9 e 10.

## 14. Rastreabilidade

| Relação | Requisito |
|---|---|
| Consome os dados de | RF02 (conteúdos) e RF03 (métricas) |
| Reaproveita o cálculo de | RF04 (índice de engajamento) |
| Respeita o isolamento de | RF06 (acesso restrito ao próprio usuário) |
| Mantém a arquitetura de | RNF01 (Controller–Service–Repository) |
| É verificado conforme | RNF02 (testes unitários e de integração) |
| É protegido conforme | RNF03 (autenticação por JWT) |

O detalhamento técnico das decisões está em `docs/superpowers/specs/2026-08-25-dashboard-design.md`.
