# Marco 0.5 — Engagement Design

## 1. Objetivo

O Marco 0.5 implementa o RF04 do MetricaMEI: o índice de engajamento de cada snapshot de métricas. O marco também alinha a entidade `Conteudo` à modelagem de dados da especificação, adicionando o campo `url_publicacao`, que constava no documento mas não existia no domínio, no schema, no model nem na tabela.

Ficam fora deste marco: painel de análise (RF05), agregações, médias, rankings, comparações entre snapshots, gráficos, filtros por período, paginação, integração com APIs externas e frontend. O painel será tratado no Marco 0.6 e consumirá o cálculo desenhado aqui.

## 2. Fórmula

```text
(curtidas + comentarios + compartilhamentos)
--------------------------------------------- × 100
                  alcance
```

O resultado é arredondado para duas casas decimais.

Valores negativos são impossíveis por construção: `MetricService._validate_metric_values` já rejeita qualquer campo de métrica que não seja inteiro maior ou igual a zero.

Percentuais acima de 100 são válidos e não são truncados. Um conteúdo muito compartilhado acumula interações de pessoas fora do alcance medido, e limitar o valor esconderia justamente o caso de melhor desempenho.

## 3. Comportamento para alcance zero

`alcance = 0` retorna `None`, exposto na API como `null`.

Zero no denominador não significa desempenho nulo: significa que o índice não é calculável. Retornar `0.0` faria o painel exibir um conteúdo sem dados de alcance como se ele tivesse fracassado. `null` distingue "não calculável" de "engajamento realmente zero", que é o valor retornado quando há alcance e nenhuma interação.

## 4. Não persistência

O engajamento é derivado e não é gravado no banco. A tabela `metricas` não muda neste marco.

A justificativa é a consistência: o índice depende de quatro colunas que o `PATCH` pode alterar. Persistir o valor criaria uma segunda fonte de verdade, que precisaria ser recalculada em cada escrita e que ficaria errada em qualquer caminho que atualizasse a linha sem passar pelo serviço.

## 5. Arquitetura

O cálculo vive em `app/services/engagement.py`, como a função pura `calculate_engagement(curtidas, comentarios, compartilhamentos, alcance)`.

Módulo isolado, e não método privado de `MetricService`, porque o painel do Marco 0.6 precisará da mesma regra sem depender do serviço de métricas nem instanciar repositórios.

A função não conhece `Metric`, HTTP ou banco: recebe quatro inteiros e devolve `float | None`.

## 6. Modelo de leitura

`app/domain/metric.py` ganha o dataclass `MetricWithEngagement`, com os mesmos campos de `Metric` mais `engajamento: float | None`.

`Metric` permanece intacto. O domínio persistido não carrega dado calculado, e o controller continua devolvendo o objeto do serviço direto para `response_model=MetricResponse` com `from_attributes=True` — o que exige que o atributo exista no objeto retornado.

`MetricService` passa a expor:

- `_with_engagement(metric) -> MetricWithEngagement`, que converte a entidade e chama `calculate_engagement`;
- `_get_metric_entity(...) -> Metric`, a busca crua usada internamente;
- `get(...) -> MetricWithEngagement`, que apenas envolve `_get_metric_entity`.

A separação é necessária porque `update` e `delete` consomem o resultado da busca em `dataclasses.replace(metric, **changes)` e `repository.delete(metric)`, que exigem a entidade persistida.

`create`, `get` e `update` devolvem `MetricWithEngagement`; `list` devolve `list[MetricWithEngagement]`, calculando por item e preservando a ordenação `data_referencia DESC, id DESC`.

## 7. Exposição na API

`MetricResponse` ganha `engajamento: float | None`, presente em `POST`, `GET`, `LIST` e `PATCH`.

`MetricCreateRequest` e `MetricUpdateRequest` não mudam: engajamento é saída, nunca entrada. Nenhum endpoint novo é criado e `MetricController` não muda — o `response_model` cuida da serialização.

## 8. url_publicacao

A entidade `Conteudo` ganha `url_publicacao: str | None`, nullable no banco.

Nullable porque a coluna nasce em uma tabela que já tem registros e a especificação não a declara obrigatória para publicar um conteúdo.

No domínio, o campo entra como último atributo com default `None`: `criado_em` não tem default, e um dataclass não aceita campo sem default depois de um campo com default. O default também preserva as chamadas existentes de `ContentService.create`.

A migration `0004_add_url_publicacao_conteudos` faz `add_column` com `String(500)` nullable; o `downgrade` faz `drop_column`.

### Validação

A validação fica em `ContentService._normalize_url`, no mesmo estilo de `_normalize_text`, e não em `HttpUrl` do Pydantic. A regra é de negócio e precisa ficar fora da camada de contrato (RNF01), com o erro traduzido para 422 pelo controller como nos demais campos.

Regras:

- `None` é aceito e devolvido como `None` — é assim que o `PATCH` remove a URL de um conteúdo que já a tinha;
- valor não textual é inválido;
- espaços em volta são removidos;
- precisa começar com `http://` ou `https://`;
- no máximo 500 caracteres.

### PATCH

`update` recebe `url_publicacao: object = _UNSET` e entra na condição de "nenhum campo informado", seguindo o padrão dos demais campos.

Como o controller usa `model_dump(exclude_unset=True)`, campo ausente significa "manter" e `null` explícito significa "limpar". Esse é o único campo de conteúdo em que `null` é aceito no `PATCH`, justamente porque ele é o único opcional.

## 9. Estratégia de testes

### Unitários

- `test_engagement.py`: a função pura, isolada — caso típico, arredondamento, `alcance = 0`, interações zero com alcance positivo e percentual acima de 100.
- `test_metric_service_engagement.py`: `create`, `get`, `list` e `update` devolvendo o índice, cálculo por item preservando a ordenação e `None` para alcance zero.
- `test_content_service_url_publicacao.py`: criação com e sem URL, remoção de espaços, esquema ausente, tamanho acima do limite e o ciclo definir/alterar/limpar/manter no `PATCH`.

### HTTP

- `test_metric_engagement_api.py`: `engajamento` presente em `POST`, `GET` e `LIST`, `null` para alcance zero e recálculo no `PATCH`.
- `test_content_api.py`: round-trip de `url_publicacao` em `POST`, `GET` e `PATCH`, incluindo 422 para URL sem esquema.

### Persistência

- `test_content_url_migration.py`: a migration cria `url_publicacao` como `VARCHAR(500)` nullable.
- `test_content_migration.py` e `test_content_model.py`: conjunto de colunas esperado atualizado.

## 10. Critérios de aceite

O Marco 0.5 estará concluído quando:

- o índice for calculado por uma função pura reaproveitável, sem depender do serviço de métricas;
- `POST`, `GET`, `LIST` e `PATCH` de métricas devolverem `engajamento`;
- alcance zero devolver `null`;
- nenhuma coluna de engajamento existir no banco;
- `url_publicacao` existir no domínio, no schema, no model e na tabela, com validação no serviço;
- a migration terminar em `0004_add_url_publicacao_conteudos`, com `downgrade` funcional;
- os testes anteriores permanecerem verdes.

## 11. Fora de escopo

Não entram neste marco: painel de análise, agregações, médias, rankings, comparações entre snapshots, gráficos, filtros por período, paginação, APIs externas e frontend.

## 12. Próximo marco

O Marco 0.6 tratará do RF05, o painel de análise. Ele consumirá `calculate_engagement` para os indicadores agregados, sem reimplementar a fórmula.

## 13. Definition of Done

O Marco 0.5 estará concluído quando um usuário autenticado puder ler o índice de engajamento de qualquer snapshot dos seus conteúdos em todas as respostas de métricas, com `null` onde o índice não for calculável, sem que o valor seja persistido, e quando a entidade `Conteudo` aceitar, devolver e remover a URL de publicação com validação de domínio e cobertura automatizada unitária, de persistência e de HTTP.
