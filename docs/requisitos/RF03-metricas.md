# RF03 — Registro de métricas

**Projeto:** MetricaMEI
**Situação:** atendido

## 1. Enunciado

> O sistema deve permitir o registro de métricas vinculadas a um conteúdo.

## 2. Escopo

```text
POST   /conteudos/{id}/metricas              registro
GET    /conteudos/{id}/metricas              histórico
GET    /conteudos/{id}/metricas/{metrica}    consulta
PATCH  /conteudos/{id}/metricas/{metrica}    correção
DELETE /conteudos/{id}/metricas/{metrica}    exclusão
```

O caminho aninhado é deliberado: métrica não existe fora de um conteúdo, e a rota aninhada torna o vínculo impossível de burlar.

Os dados registrados são os cinco previstos na modelagem — `visualizacoes`, `curtidas`, `comentarios`, `compartilhamentos` e `alcance` — mais a `data_referencia` da medição.

## 3. Cada métrica é um snapshot cumulativo

**Esta é a decisão mais consequente do requisito.**

Cada registro representa o total observado na plataforma até aquela data de referência, e não o incremento do dia. É como as redes sociais apresentam os números: um post com mil visualizações continua com mil no dia seguinte, mais o que ganhar.

A consequência aparece no RF05: somar todo o histórico de um conteúdo multiplicaria seus números. Qualquer consolidação precisa usar apenas a medição mais recente de cada conteúdo.

O sistema **não exige crescimento** entre medições. Plataformas corrigem e recalculam números, e recusar um valor menor que o anterior impediria o usuário de registrar o dado real.

## 4. Decisões e justificativas

### Valores inteiros e não negativos

Não existe meia curtida nem alcance negativo. A validação recusa qualquer outro tipo, inclusive booleano, que em Python passaria por inteiro sem verificação explícita.

### Uma medição por conteúdo e data

A combinação `conteudo_id + data_referencia` é única, garantida por constraint no banco e não apenas por verificação no serviço. Duas medições do mesmo dia seriam registros contraditórios do mesmo fato, e a consolidação não teria como escolher entre elas.

A tentativa de repetir a data responde `409`. Na interface, a mensagem orienta a editar a medição existente ou escolher outra data — o erro genérico diria o que houve, mas não o que fazer.

### Data de referência entre a publicação e hoje

Não se mede desempenho antes de publicar nem no futuro. Os dois limites são verificados no serviço e declarados também nos campos do formulário.

### O ownership vem do conteúdo

A métrica não guarda `usuario_id`. A cadeia é `Usuario → Conteudo → Metrica`, e duplicar o dono na métrica criaria a possibilidade de os dois divergirem.

## 5. Critérios de aceite

1. O registro cria a medição vinculada ao conteúdo e devolve `201`;
2. valores não inteiros ou negativos são recusados com `422`;
3. data anterior à publicação ou futura é recusada com `422`;
4. segunda medição na mesma data do mesmo conteúdo é recusada com `409`;
5. o conflito é barrado também no banco, não só no serviço;
6. o histórico é devolvido da medição mais recente para a mais antiga;
7. a correção parcial altera apenas os campos enviados;
8. a exclusão remove somente a medição indicada;
9. conteúdo ou métrica de outro usuário responde `404`;
10. a interface permite registrar, corrigir e excluir sem uso da API direta.

## 6. Rastreabilidade

| Critério | Verificado em |
|---|---|
| 1, 2, 3 | `tests/unit/test_metric_service_create.py`, `tests/integration/test_metric_api.py` |
| 4 | `tests/unit/test_metric_service_create.py`, `tests/unit/test_in_memory_metric_repository.py` |
| 5 | `tests/integration/test_metric_migration.py`, `tests/integration/test_sqlalchemy_metric_repository.py` |
| 6, 7, 8 | `tests/unit/test_metric_service_crud.py` |
| 9 | `tests/integration/test_metric_api.py` |
| 10 | `frontend/src/paginas/ConteudoDetalhe.test.tsx`, `frontend/e2e/jornada.spec.ts` |

Requisitos relacionados: RF02 (conteúdo que a métrica referencia), RF04 (índice derivado destes valores), RF05 (consolidação), RF06 (isolamento), RNF01, RNF02.
