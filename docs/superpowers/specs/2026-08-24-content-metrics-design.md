# Marco 0.4 — Content Metrics Design

## 1. Objetivo

O Marco 0.4 implementa o RF03 do MetricaMEI: registro e gerenciamento de métricas associadas aos conteúdos digitais de usuários autenticados. Este marco implementa somente métricas brutas e histórico de medições.

Ficam fora deste marco: cálculo de engajamento, crescimento entre snapshots, agregações, médias, rankings, dashboard, gráficos, filtros por período, paginação, integração com APIs externas e frontend. O cálculo de engajamento será tratado no Marco 0.5.

## 2. Snapshot de métricas

Cada registro representa um snapshot acumulado do desempenho de um conteúdo em uma data de referência. Os valores representam os totais observados na plataforma naquela data, e não somente o incremento do dia. O sistema não exige crescimento entre snapshots, pois plataformas podem corrigir ou recalcular métricas.

## 3. Modelo de domínio

A entidade `Metric` possui:

- `id: int | None`
- `conteudo_id: int`
- `visualizacoes: int`
- `curtidas: int`
- `comentarios: int`
- `compartilhamentos: int`
- `alcance: int`
- `data_referencia: date`
- `criado_em: datetime`

`Metric` não possui `usuario_id`. O ownership é derivado do conteúdo: `Usuario 1:N Conteudo 1:N Metrica`.

## 4. Estrutura relacional

Será criada a tabela `metricas` com:

- `id INTEGER PRIMARY KEY`
- `conteudo_id INTEGER NOT NULL`
- `visualizacoes INTEGER NOT NULL`
- `curtidas INTEGER NOT NULL`
- `comentarios INTEGER NOT NULL`
- `compartilhamentos INTEGER NOT NULL`
- `alcance INTEGER NOT NULL`
- `data_referencia DATE NOT NULL`
- `criado_em DATETIME NOT NULL`

Restrições:

```text
FOREIGN KEY (conteudo_id)
REFERENCES conteudos(id)
ON DELETE CASCADE

UNIQUE (conteudo_id, data_referencia)
```

Um conteúdo pode possuir várias métricas, mas apenas uma medição por data de referência. Ao excluir um conteúdo, suas métricas são excluídas em cascade.

## 5. Migration e SQLite

Será criada `0003_create_metricas`, após `0002_create_conteudos`, sem alterar migrations anteriores. A migration criará a tabela, a foreign key com `ON DELETE CASCADE` e a constraint única composta.

`create_engine_from_url()` será ajustado para habilitar `PRAGMA foreign_keys = ON` em conexões SQLite. O comportamento será coberto por teste de integração.

## 6. Arquitetura

O módulo seguirá Controller–Service–Repository:

```text
MetricController
       ↓
MetricService
   ↙         ↘
ContentRepository
             MetricRepository
```

O `MetricService` depende diretamente de `ContentRepository` e `MetricRepository`, não de `ContentService`.

### MetricController

Recebe HTTP, obtém o usuário autenticado, recebe schemas, chama o Service e traduz exceções de negócio para HTTP. Não contém regras de negócio.

### MetricService

Valida ownership do conteúdo, valores, datas e duplicidade, e coordena o CRUD. Não depende de FastAPI, SQLAlchemy ou detalhes de banco.

### MetricRepository

Contrato previsto:

```text
create(metric)
list_by_content(content_id)
get_by_id_and_content(metric_id, content_id)
get_by_content_and_reference_date(content_id, data_referencia)
update(metric)
delete(metric)
```

## 7. Ownership e segurança

Toda operação começa verificando se o conteúdo existe e pertence ao usuário autenticado. Conteúdo inexistente ou de outro usuário retorna `404` com `"Conteúdo não encontrado."`.

Depois da validação do conteúdo, métrica inexistente ou que não pertença ao conteúdo informado retorna `404` com `"Métrica não encontrada."`.

## 8. Endpoints

Todos exigem JWT:

```text
POST   /conteudos/{content_id}/metricas
GET    /conteudos/{content_id}/metricas
GET    /conteudos/{content_id}/metricas/{metric_id}
PATCH  /conteudos/{content_id}/metricas/{metric_id}
DELETE /conteudos/{content_id}/metricas/{metric_id}
```

### POST

Payload:

```json
{
  "visualizacoes": 1700,
  "curtidas": 110,
  "comentarios": 14,
  "compartilhamentos": 22,
  "alcance": 1450,
  "data_referencia": "2026-08-24"
}
```

Sucesso: `201 Created`.

### LIST

Retorna todas as métricas do conteúdo, sem paginação, ordenadas por `data_referencia DESC, id DESC`. Sem métricas, retorna `[]`.

### GET

Retorna uma métrica específica.

### PATCH

Campos editáveis: `visualizacoes`, `curtidas`, `comentarios`, `compartilhamentos`, `alcance`, `data_referencia`.

Campos imutáveis: `id`, `conteudo_id`, `criado_em`.

Payload vazio é inválido. `null` explícito é inválido. Zero é válido.

### DELETE

Hard delete com resposta `204 No Content`.

## 9. DTO público

`conteudo_id` não é recebido no payload porque já está na URL. `conteudo_id` e `usuario_id` não são expostos na resposta pública.

Exemplo:

```json
{
  "id": 8,
  "visualizacoes": 1700,
  "curtidas": 110,
  "comentarios": 14,
  "compartilhamentos": 22,
  "alcance": 1450,
  "data_referencia": "2026-08-24",
  "criado_em": "2026-08-24T12:10:00"
}
```

## 10. Validações

Na criação, os cinco campos quantitativos são obrigatórios e inteiros maiores ou iguais a zero:

```text
visualizacoes >= 0
curtidas >= 0
comentarios >= 0
compartilhamentos >= 0
alcance >= 0
```

Não há validações relacionando esses campos entre si.

A data deve obedecer:

```text
conteudo.data_publicacao <= data_referencia <= date.today()
```

Data igual à publicação é válida; data anterior à publicação ou futura é inválida.

## 11. Unicidade

Só pode existir uma métrica por conteúdo por data de referência. A duplicidade é verificada no Service e garantida também pelo banco com `UNIQUE (conteudo_id, data_referencia)`.

Duplicidade retorna `409 Conflict` com `"Já existe uma métrica para este conteúdo nesta data."`. A regra também vale para PATCH que altere `data_referencia`.

## 12. PATCH e sentinel

O Service usa sentinel interno para diferenciar:

```text
campo não enviado → mantém valor atual
campo = null      → inválido
campo = 0         → válido
```

Alterar `data_referencia` revalida intervalo e unicidade.

## 13. Exceções de negócio

Exceções previstas:

```text
InvalidMetricError
MetricNotFoundError
DuplicateMetricError
MetricContentNotFoundError
```

Mapeamento HTTP:

```text
MetricContentNotFoundError → 404 "Conteúdo não encontrado."
MetricNotFoundError        → 404 "Métrica não encontrada."
DuplicateMetricError       → 409 "Já existe uma métrica para este conteúdo nesta data."
InvalidMetricError         → 422 "Dados da métrica inválidos."
```

Token ausente ou inválido continua retornando `401 Unauthorized`.

## 14. Ordem das validações

CREATE: validar conteúdo/ownership → validar números → validar data → verificar duplicidade → persistir.

LIST: validar conteúdo/ownership → listar métricas.

GET: validar conteúdo/ownership → buscar métrica dentro do conteúdo.

PATCH: validar conteúdo/ownership → localizar métrica → exigir alteração → validar campos → validar data → verificar duplicidade → atualizar.

DELETE: validar conteúdo/ownership → localizar métrica → excluir.

## 15. Conflito de persistência

A constraint única do banco é proteção final contra concorrência. Detalhes do SQLAlchemy não são propagados ao Service.

```text
SQLAlchemy IntegrityError
        ↓
SQLAlchemyMetricRepository
        ↓
erro abstrato de persistência
        ↓
MetricService
        ↓
DuplicateMetricError
        ↓
MetricController
        ↓
409 Conflict
```

## 16. Estratégia de testes

O desenvolvimento seguirá TDD.

### Unitários

`MetricService` usa `InMemoryContentRepository` e `InMemoryMetricRepository`, sem HTTP, FastAPI, SQLAlchemy ou banco real.

Cobertura mínima: criação válida; zero válido; negativos inválidos; data futura inválida; data anterior à publicação inválida; data igual à publicação válida; data de hoje válida; duplicidade; ownership; lista ordenada; lista vazia; GET válido e inválido; PATCH parcial; PATCH vazio; `null` inválido; zero em PATCH; colisão de data; DELETE válido e inexistente.

### Persistência

Cobrir migration `0003`, estrutura da tabela, FK, `ON DELETE CASCADE`, unicidade, create, read, update, delete, ordenação, conflito e cascade. Testes usarão SQLite isolado.

### HTTP

Cobrir POST 201, LIST 200, GET 200, PATCH 200, DELETE 204, sem token 401, token inválido 401, conteúdo alheio 404, métrica inexistente 404, métrica de outro conteúdo 404, dados inválidos 422 e duplicidade 409.

Os 76 testes anteriores devem continuar passando.

## 17. Critérios de aceite

O Marco 0.4 estará concluído quando:

- usuário autenticado puder gerenciar métricas de conteúdo próprio;
- cinco valores quantitativos forem obrigatórios;
- zero for aceito e negativos forem rejeitados;
- datas forem validadas;
- existir somente um snapshot por conteúdo/data;
- duplicidade retornar 409;
- histórico estiver ordenado;
- PATCH parcial funcionar;
- PATCH vazio e `null` forem rejeitados;
- ownership for preservado;
- DELETE retornar 204;
- cascade funcionar;
- endpoints exigirem JWT;
- regras permanecerem no Service;
- persistência permanecer no Repository;
- testes unitários e de integração estiverem verdes;
- testes anteriores permanecerem verdes;
- Alembic terminar em `0003_create_metricas`.

## 18. Fora de escopo

Não entram neste marco: engajamento, crescimento, comparações, agregações, médias, rankings, dashboard, gráficos, filtros de período, paginação, APIs externas e frontend.

## 19. Próximo marco

O Marco 0.5 tratará do cálculo de engajamento:

```text
(curtidas + comentarios + compartilhamentos)
--------------------------------------------- × 100
                  alcance
```

Comportamento para `alcance = 0`, persistência e forma de exposição serão decididos somente no design do Marco 0.5.

## 20. Definition of Done

O Marco 0.4 estará concluído quando um usuário autenticado puder registrar, consultar, editar e excluir snapshots históricos de métricas de seus próprios conteúdos, com validações de domínio, unicidade por data, persistência relacional, proteção de ownership, exclusão em cascade e cobertura automatizada unitária e de integração, sem implementar cálculos analíticos derivados.
