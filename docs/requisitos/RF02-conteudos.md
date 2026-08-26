# RF02 — Gerenciamento de conteúdos

**Projeto:** MetricaMEI
**Situação:** atendido

## 1. Enunciado

> O sistema deve permitir o cadastro, edição e exclusão de conteúdos.

## 2. Escopo

Além das três operações do enunciado, o sistema oferece listagem e consulta individual — sem elas o usuário não teria como chegar ao conteúdo que quer editar ou excluir.

```text
POST   /conteudos              cadastro
GET    /conteudos              listagem
GET    /conteudos/{id}         consulta
PATCH  /conteudos/{id}         edição
DELETE /conteudos/{id}         exclusão
```

Na interface, as telas `/conteudos` e `/conteudos/{id}`.

## 3. Atributos

Conforme a modelagem de dados do documento de projeto:

```text
titulo            1 a 200 caracteres
plataforma        1 a 50 caracteres
tipo              1 a 50 caracteres
data_publicacao   não pode ser futura
url_publicacao    opcional
```

`plataforma` e `tipo` são texto livre, e não listas fechadas. O documento cita exemplos ("Instagram, TikTok", "foto, vídeo, carrossel") sem defini-los como conjunto fechado, e uma lista fixa envelheceria a cada rede social nova.

## 4. Decisões e justificativas

### Data de publicação não pode ser futura

Métrica é medição de desempenho já ocorrido. Aceitar publicação futura permitiria registrar desempenho de conteúdo que ainda não existe.

### URL opcional, validada no serviço

O documento lista `url_publicacao` entre os atributos sem marcá-la como obrigatória, e nem todo microempreendedor tem o endereço à mão ao registrar.

A validação exige `http://` ou `https://` e no máximo 500 caracteres, e fica na camada de serviço em vez de no schema do Pydantic. É regra de negócio, e o RNF01 mantém regra fora da camada de contrato.

### `null` no PATCH remove a URL

É o único campo do conteúdo em que `null` não é erro, justamente por ser o único opcional. Nos demais, `null` explícito é recusado com `422`: apagar o título de um conteúdo não é uma operação que faça sentido.

### Atualização parcial

O `PATCH` altera apenas os campos enviados. Campo ausente mantém o valor, o que evita que a interface precise reenviar o registro inteiro e sobrescrever o que não editou.

### Exclusão em cascata

Excluir um conteúdo apaga suas métricas, pela definição da chave estrangeira. Métrica sem conteúdo não tem significado — nem sequer tem dono, já que o vínculo com o usuário passa pelo conteúdo.

## 5. Critérios de aceite

1. O cadastro cria o conteúdo do usuário autenticado e devolve `201`;
2. os campos de texto são normalizados e recusados fora dos limites de tamanho;
3. data de publicação futura é recusada com `422`;
4. a URL é aceita apenas com esquema `http` ou `https`, até 500 caracteres;
5. a listagem devolve apenas os conteúdos do usuário, mais recentes primeiro;
6. a edição parcial altera somente os campos enviados;
7. `null` em `url_publicacao` remove a URL; `null` nos demais campos é recusado;
8. a exclusão remove o conteúdo e suas métricas;
9. conteúdo de outro usuário responde `404` em consulta, edição e exclusão;
10. a interface permite cadastrar, editar e excluir sem uso da API direta.

## 6. Rastreabilidade

| Critério | Verificado em |
|---|---|
| 1, 2, 3 | `tests/unit/test_content_service_create.py`, `tests/integration/test_content_api.py` |
| 4, 7 | `tests/unit/test_content_service_url_publicacao.py` |
| 5, 6, 8 | `tests/unit/test_content_service_crud.py` |
| 8 | `tests/integration/test_sqlalchemy_metric_repository.py` (cascata) |
| 9 | `tests/integration/test_content_api.py` |
| 10 | `frontend/src/paginas/Conteudos.test.tsx`, `frontend/e2e/jornada.spec.ts` |

Requisitos relacionados: RF01 (identidade), RF03 (métricas vinculadas), RF06 (isolamento), RNF01, RNF02.
