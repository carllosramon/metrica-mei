# RF04 — Índice de engajamento

**Projeto:** MetricaMEI
**Situação:** atendido

## 1. Enunciado

> O sistema deve calcular automaticamente o índice de engajamento de cada métrica.

## 2. Fórmula

```text
(curtidas + comentarios + compartilhamentos)
--------------------------------------------- × 100
                  alcance
```

O resultado é arredondado para duas casas decimais.

O numerador soma as três formas de interação deliberada do público. Visualização fica de fora: ela mede quantos viram, não quantos reagiram, e está no denominador conceitualmente — o alcance é a base sobre a qual a interação é medida.

## 3. Alcance zero

O documento de projeto autoriza duas saídas: *"o sistema deve retornar 0 (zero) ou nulo, tratando a divisão por zero"*.

**Foi escolhido o nulo.**

Zero afirma que houve desempenho e ele foi nenhum. Nulo afirma que o índice não é calculável. São situações diferentes, e a distinção importa: um conteúdo com alcance 500 e nenhuma interação tem engajamento real de 0%, enquanto um conteúdo sem alcance registrado simplesmente não tem base de cálculo.

Retornar zero para os dois casos faria o painel exibir como fracasso um conteúdo que apenas não foi medido — e o usuário poderia descartar um conteúdo que na verdade foi bem.

Na interface, o nulo aparece como travessão acompanhado da explicação, e não como `0%`.

## 4. Decisões e justificativas

### O índice não é persistido

Conforme a observação explícita da modelagem de dados: *"O índice de engajamento não é armazenado na entidade Métrica. Ele é calculado pela camada de serviço."*

A razão técnica sustenta a escolha: o índice depende de quatro colunas que o `PATCH` pode alterar. Gravá-lo criaria uma segunda fonte de verdade, que ficaria errada em qualquer caminho de escrita que não passasse pelo serviço.

### Função pura em módulo próprio

O cálculo vive em `app/services/engagement.py` como função que recebe quatro inteiros e devolve `float | None`. Não conhece `Metric`, HTTP nem banco.

O isolamento permite que o RF05 reaproveite a mesma regra sobre os totais consolidados, sem instanciar o serviço de métricas nem repositórios. Nenhuma fórmula é reimplementada em nenhum ponto do sistema.

### Percentual acima de 100 é preservado

Conteúdo muito compartilhado acumula interações de pessoas fora do alcance medido. Limitar o valor a 100 esconderia justamente o caso de melhor desempenho.

### Valores negativos são impossíveis por construção

O RF03 já recusa métrica que não seja inteiro maior ou igual a zero, então o cálculo não precisa validar de novo.

## 5. Exposição

O campo `engajamento` acompanha todas as respostas de métrica — `POST`, `GET`, `LIST` e `PATCH`. Não é aceito como entrada em nenhum endpoint: é saída derivada, nunca dado informado.

## 6. Critérios de aceite

1. O índice é calculado pela fórmula, com duas casas decimais;
2. alcance zero devolve nulo, e não zero;
3. interações zero com alcance positivo devolve `0.0`, distinto do caso anterior;
4. percentual acima de 100 é preservado;
5. o índice acompanha toda resposta de métrica;
6. o índice não é aceito como entrada;
7. nenhuma coluna de engajamento existe no banco;
8. a correção de uma métrica recalcula o índice na resposta;
9. o cálculo é reaproveitado pelo painel sem reimplementação;
10. a interface exibe travessão explicado quando o índice não é calculável.

## 7. Rastreabilidade

| Critério | Verificado em |
|---|---|
| 1, 2, 3, 4 | `tests/unit/test_engagement.py` |
| 5, 8 | `tests/unit/test_metric_service_engagement.py`, `tests/integration/test_metric_engagement_api.py` |
| 6, 7 | ausência de `engajamento` em `MetricCreateRequest`/`MetricUpdateRequest` e na migration `0003_create_metricas` |
| 9 | `tests/unit/test_dashboard_service.py` |
| 10 | `frontend/src/formatacao.test.ts`, `frontend/src/paginas/Painel.test.tsx` |

Requisitos relacionados: RF03 (valores de origem), RF05 (consolidação), RNF01, RNF02.

O detalhamento técnico está em `docs/superpowers/specs/2026-08-25-engagement-design.md`.
