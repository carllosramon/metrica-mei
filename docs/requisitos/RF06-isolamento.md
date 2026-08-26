# RF06 — Isolamento de dados por usuário

**Projeto:** MetricaMEI
**Situação:** atendido

## 1. Enunciado

> O sistema deve restringir o acesso de cada usuário aos seus próprios dados.

## 2. Alcance do requisito

Este é o único requisito que atravessa todos os outros. Ele não tem endpoint próprio: é uma propriedade que cada operação de conteúdo, métrica e painel precisa preservar.

```text
Usuario (1) → (N) Conteudo (1) → (N) Metrica
```

O dono é sempre derivado dessa cadeia. `Conteudo` guarda `usuario_id`; `Metrica` não guarda dono nenhum, e o seu vínculo passa pelo conteúdo.

## 3. Decisões e justificativas

### O filtro está na consulta, não em verificação posterior

`get_by_id_and_user` e `list_by_user` já incluem o usuário na cláusula da consulta. O registro de outro dono nunca chega a ser carregado.

A alternativa — buscar por identificador e depois comparar o dono — funcionaria, mas deixaria o dado do outro usuário na memória do processo, e bastaria um caminho esquecendo a comparação para vazá-lo.

### Recurso alheio responde 404, não 403

Um `403` confirmaria que o recurso existe e pertence a outra pessoa. O `404` não distingue "não existe" de "não é seu", e por isso não permite descobrir quais identificadores estão ocupados no sistema.

A escolha custa clareza para o dono legítimo que erra um identificador, e ganha em não expor a existência de dados alheios.

### Métrica não duplica o dono

Guardar `usuario_id` na métrica criaria dois lugares afirmando de quem ela é, com a possibilidade de divergirem. O acesso à métrica passa obrigatoriamente pelo conteúdo, que já foi verificado.

### O painel parte da listagem do próprio usuário

A consolidação do RF05 começa em `list_by_user`, então não existe caminho pelo qual um conteúdo de outra conta influencie qualquer indicador. O isolamento não precisa ser reimplementado ali.

### Nenhuma rota de dados é pública

Todas as rotas exceto cadastro, login e verificação de saúde exigem token válido. Sem token, ou com token inválido ou expirado, a resposta é `401`.

## 4. Critérios de aceite

1. A listagem de conteúdos devolve apenas os do usuário autenticado;
2. consultar conteúdo de outro usuário responde `404`;
3. editar conteúdo de outro usuário responde `404` e não altera o registro;
4. excluir conteúdo de outro usuário responde `404` e não remove o registro;
5. as métricas de um conteúdo alheio respondem `404` em todas as operações;
6. o painel de um usuário não reflete conteúdo nem métrica de outro;
7. requisição sem token recebe `401`;
8. requisição com token inválido ou expirado recebe `401`;
9. a interface devolve o usuário ao login quando a sessão deixa de valer.

## 5. Rastreabilidade

| Critério | Verificado em |
|---|---|
| 1, 2, 3, 4 | `tests/unit/test_content_service_crud.py`, `tests/integration/test_content_api.py` |
| 5 | `tests/unit/test_metric_service_crud.py`, `tests/integration/test_metric_api.py` |
| 6 | `tests/unit/test_dashboard_service.py`, `tests/integration/test_dashboard_api.py` |
| 7, 8 | `tests/integration/test_auth_me.py`, `tests/integration/test_dashboard_api.py` |
| 9 | `frontend/src/api/cliente.test.ts`, `frontend/e2e/jornada.spec.ts` |

Requisitos relacionados: RF01 (estabelece a identidade), RF02, RF03 e RF05 (operações que precisam preservar o isolamento), RNF03 (JWT).
