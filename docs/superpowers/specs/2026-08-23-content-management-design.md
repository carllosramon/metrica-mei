# Marco 0.3 — Gerenciamento de Conteúdos

**Status:** design aprovado  
**Data:** 2026-08-23  
**Projeto:** MetricaMEI  
**Escopo:** backend — CRUD de conteúdos com autenticação, ownership, persistência e testes automatizados

## 1. Objetivo

Implementar o gerenciamento de conteúdos digitais do usuário autenticado, cobrindo o RF02 e preparando a base para RF03, RF04, RF05 e RF06.

O marco adiciona um novo fluxo completo pela arquitetura Controller–Service–Repository, mantendo o domínio desacoplado de HTTP e da implementação concreta do banco de dados.

O usuário poderá criar, listar, consultar, editar parcialmente e excluir seus próprios conteúdos. Nenhuma operação poderá acessar ou modificar conteúdos pertencentes a outro usuário.

## 2. Escopo

O Marco 0.3 inclui:

- entidade de domínio `Content`;
- schemas HTTP de criação, atualização e resposta;
- `ContentService` com regras de negócio;
- contrato `ContentRepository`;
- implementação SQLAlchemy do repository;
- implementação em memória para testes unitários;
- endpoints protegidos por JWT;
- dependência HTTP compartilhada para resolução do usuário autenticado;
- refatoração de `/auth/me` para reutilizar essa dependência;
- migration `0002_create_conteudos`;
- testes unitários e de integração;
- atualização da documentação do projeto.

Não fazem parte deste marco:

- métricas de conteúdos;
- cálculo de engajamento;
- dashboard;
- paginação;
- filtros de plataforma ou tipo;
- soft delete;
- agendamento de publicações;
- `atualizado_em`;
- enums ou catálogos fechados para plataforma/tipo.

## 3. Arquitetura

O fluxo seguirá a arquitetura já adotada no projeto:

```text
Requisição HTTP + JWT
        ↓
Dependência de autenticação
        ↓
ContentController
        ↓
ContentService
        ↓
ContentRepository
        ↓
SQLAlchemyContentRepository
        ↓
Banco de dados
```

Para testes unitários:

```text
ContentService
        ↓
InMemoryContentRepository
```

### 3.1 Controller

O Controller será responsável por:

- receber e validar a estrutura HTTP por meio dos schemas;
- receber o usuário autenticado da dependência compartilhada;
- chamar os casos de uso do `ContentService`;
- converter exceções de domínio em respostas HTTP;
- definir códigos de status e modelos de resposta.

O Controller não deverá conter regras de negócio nem consultas SQL.

### 3.2 Service

O `ContentService` será responsável por:

- criar conteúdo para um `user_id` já autenticado;
- normalizar campos de texto;
- validar limites de negócio;
- rejeitar `data_publicacao` futura;
- listar somente conteúdos do usuário;
- buscar um conteúdo pelo par `content_id` + `user_id`;
- atualizar parcialmente um conteúdo;
- rejeitar atualização vazia;
- excluir conteúdo pertencente ao usuário;
- lançar exceções independentes de HTTP.

O Service não conhecerá JWT, Bearer, headers HTTP, FastAPI ou SQLAlchemy.

### 3.3 Repository

O `ContentRepository` será a abstração de persistência usada pelo Service.

O contrato deverá oferecer operações equivalentes a:

```text
create(content)
list_by_user(user_id)
get_by_id_and_user(content_id, user_id)
update(content)
delete(content)
```

A implementação SQLAlchemy será usada pela aplicação. A implementação em memória será usada nos testes unitários.

Operações de leitura por identificador deverão considerar também o proprietário. Não haverá busca de conteúdo por `id` isolado para fluxos protegidos por ownership.

## 4. Modelo de domínio

A entidade `Content` terá:

```text
Content
├── id: int | None
├── usuario_id: int
├── titulo: str
├── plataforma: str
├── tipo: str
├── data_publicacao: date
└── criado_em: datetime
```

`criado_em` seguirá o padrão temporal já adotado no projeto: geração em UTC.

### 4.1 Regras dos campos

`titulo`:

- obrigatório;
- remoção de espaços externos;
- mínimo de 1 caractere após normalização;
- máximo de 200 caracteres.

`plataforma`:

- obrigatório;
- texto livre;
- remoção de espaços externos;
- mínimo de 1 caractere após normalização;
- máximo de 50 caracteres;
- capitalização fornecida pelo usuário será preservada.

`tipo`:

- obrigatório;
- texto livre;
- remoção de espaços externos;
- mínimo de 1 caractere após normalização;
- máximo de 50 caracteres;
- capitalização fornecida pelo usuário será preservada.

`data_publicacao`:

- obrigatória;
- armazena apenas data, sem horário;
- aceita hoje ou datas passadas;
- não aceita data futura.

`usuario_id`:

- obrigatório internamente;
- definido a partir do usuário autenticado;
- nunca recebido do JSON da requisição;
- nunca exposto na resposta HTTP.

Títulos duplicados são permitidos. A identidade do conteúdo é seu `id`.

## 5. Persistência

Será criada a tabela `conteudos` por meio de uma nova migration Alembic:

```text
0001_create_usuarios
        ↓
0002_create_conteudos
```

A migration `0001_create_usuarios` não será alterada.

Estrutura conceitual:

```text
conteudos
├── id                PK
├── usuario_id        FK → usuarios.id
├── titulo            VARCHAR(200) NOT NULL
├── plataforma        VARCHAR(50) NOT NULL
├── tipo              VARCHAR(50) NOT NULL
├── data_publicacao   DATE NOT NULL
└── criado_em         DATETIME NOT NULL
```

Será criado índice em `usuario_id`, pois as consultas de conteúdo são escopadas pelo proprietário.

A ordenação padrão da listagem será:

```text
data_publicacao DESC
id DESC
```

O segundo critério garante ordem determinística quando dois conteúdos possuem a mesma data de publicação.

## 6. Schemas HTTP

### 6.1 ContentCreate

Campos:

```text
titulo
plataforma
tipo
data_publicacao
```

Todos são obrigatórios.

### 6.2 ContentUpdate

Campos editáveis:

```text
titulo
plataforma
tipo
data_publicacao
```

Todos são opcionais individualmente para suportar `PATCH`, mas pelo menos um deles deverá ser enviado.

Um payload vazio:

```json
{}
```

será inválido e retornará `422`.

Não poderão ser alterados pela API:

```text
id
usuario_id
criado_em
```

### 6.3 ContentResponse

Campos expostos:

```text
id
titulo
plataforma
tipo
data_publicacao
criado_em
```

`usuario_id` permanecerá interno.

## 7. API

Todos os endpoints de conteúdos exigirão autenticação JWT.

### 7.1 Criar

```http
POST /conteudos
```

Sucesso:

```text
201 Created
```

A propriedade do conteúdo é definida pelo usuário autenticado.

### 7.2 Listar

```http
GET /conteudos
```

Sucesso:

```text
200 OK
```

Retorna todos os conteúdos do usuário autenticado, sem paginação, ordenados por `data_publicacao DESC, id DESC`.

Usuário sem conteúdos recebe:

```json
[]
```

com `200 OK`.

### 7.3 Consultar um conteúdo

```http
GET /conteudos/{id}
```

Resultados:

```text
conteúdo pertence ao usuário → 200 OK
conteúdo não existe           → 404 Not Found
conteúdo pertence a outro     → 404 Not Found
```

### 7.4 Atualizar parcialmente

```http
PATCH /conteudos/{id}
```

Sucesso:

```text
200 OK
```

Somente campos enviados serão alterados. Campos omitidos conservarão os valores existentes.

Conteúdo inexistente ou de outro usuário recebe `404`.

Dados inválidos recebem `422`.

### 7.5 Excluir

```http
DELETE /conteudos/{id}
```

Sucesso:

```text
204 No Content
```

A resposta bem-sucedida não terá corpo.

Conteúdo inexistente ou pertencente a outro usuário recebe `404`.

## 8. Autenticação e ownership

O `usuario_id` usado pelos casos de uso será obtido exclusivamente a partir do JWT válido.

O cliente não poderá determinar o proprietário do conteúdo por payload, query string ou path parameter.

### 8.1 Dependência compartilhada

O arquivo existente `app/dependencies.py` será ampliado com uma dependência compartilhada responsável por:

```text
Authorization: Bearer <token>
        ↓
extrair credencial
        ↓
validar token por meio do AuthService
        ↓
resolver usuário autenticado
        ↓
retornar usuário ao Controller
```

Conceitualmente, essa dependência será `get_current_user`.

A rota existente `GET /auth/me` será refatorada para reutilizar essa dependência, preservando seu comportamento HTTP atual.

A ausência de credenciais ou um token inválido continuará produzindo:

```text
401 Unauthorized
detail: "Não autenticado."
WWW-Authenticate: Bearer
```

### 8.2 Isolamento por usuário

Criação:

```text
JWT → usuário 3 → novo Content(usuario_id=3)
```

Listagem:

```text
repository.list_by_user(3)
```

Busca, edição e exclusão:

```text
content_id = X
AND
usuario_id = 3
```

Para um conteúdo de outro usuário, o sistema produzirá o mesmo comportamento de um conteúdo inexistente.

Isso evita revelar a existência de registros pertencentes a outras contas e implementa o isolamento exigido pelo RF06.

## 9. Tratamento de erros

As exceções de domínio principais serão:

```text
InvalidContentError
ContentNotFoundError
```

`InvalidContentError` representa violações de regras de negócio do conteúdo.

`ContentNotFoundError` representa tanto:

- conteúdo inexistente;
- conteúdo que não pertence ao usuário autenticado.

A camada HTTP traduzirá essas exceções para os códigos adequados.

Regras estruturais dos schemas podem ser rejeitadas diretamente pelo Pydantic/FastAPI com `422`, mas as regras essenciais também deverão existir no Service para que o domínio permaneça válido fora do fluxo HTTP.

## 10. Estratégia de testes

O desenvolvimento seguirá TDD:

```text
RED
↓
confirmar falha pelo motivo esperado
↓
GREEN
↓
implementar o mínimo necessário
↓
rodar teste específico
↓
rodar suíte completa
↓
refatorar quando necessário
```

### 10.1 Testes unitários

Os testes unitários usarão `ContentService` com `InMemoryContentRepository`.

Devem cobrir, no mínimo:

- criação válida;
- associação correta ao `user_id`;
- normalização de `titulo`;
- normalização de `plataforma`;
- normalização de `tipo`;
- rejeição de título vazio;
- rejeição de título acima de 200 caracteres;
- rejeição de plataforma vazia;
- rejeição de plataforma acima de 50 caracteres;
- rejeição de tipo vazio;
- rejeição de tipo acima de 50 caracteres;
- aceitação de data passada;
- aceitação da data atual;
- rejeição de data futura;
- listagem restrita ao usuário;
- ordenação por data e `id`;
- busca de conteúdo próprio;
- `ContentNotFoundError` para conteúdo inexistente;
- `ContentNotFoundError` para conteúdo de outro usuário;
- PATCH parcial preservando campos omitidos;
- rejeição de PATCH vazio;
- rejeição de valores inválidos no PATCH;
- impossibilidade de editar conteúdo de outro usuário;
- exclusão de conteúdo próprio;
- impossibilidade de excluir conteúdo de outro usuário;
- impossibilidade de buscar conteúdo após exclusão.

### 10.2 Testes de integração

Os testes de integração exercitarão:

```text
HTTP
↓
FastAPI
↓
JWT
↓
Controller
↓
Service
↓
SQLAlchemy Repository
↓
SQLite isolado
```

O banco de desenvolvimento não será usado pelos testes.

Devem existir cenários para:

- registrar usuário e fazer login;
- criar conteúdo com token válido;
- listar conteúdos;
- consultar conteúdo;
- atualizar parcialmente;
- excluir;
- receber `401` sem autenticação;
- receber `401` com token inválido;
- receber `422` para payload inválido;
- receber `404` para conteúdo inexistente;
- validar ownership usando dois usuários.

No cenário de dois usuários:

```text
Usuário A cria conteúdo A
Usuário B cria conteúdo B
```

Com o token de A:

```text
GET conteúdo B    → 404
PATCH conteúdo B  → 404
DELETE conteúdo B → 404
```

Após as tentativas, o conteúdo B deverá continuar existindo e inalterado.

A refatoração de `/auth/me` não poderá quebrar os testes já existentes da autenticação.

## 11. Critérios de conclusão

O Marco 0.3 será considerado concluído quando:

- os cinco endpoints de conteúdos estiverem implementados;
- todos os endpoints estiverem protegidos por JWT;
- `usuario_id` vier exclusivamente do usuário autenticado;
- usuários não conseguirem ler, editar ou excluir conteúdo de outras contas;
- `ContentService` contiver as regras essenciais de negócio;
- existir abstração `ContentRepository`;
- existirem repositories SQLAlchemy e em memória;
- migration `0002_create_conteudos` estiver funcional;
- `alembic upgrade head` levar o banco até `0002_create_conteudos (head)`;
- testes unitários cobrirem as regras de negócio;
- testes de integração cobrirem o fluxo HTTP até o banco isolado;
- toda a suíte anterior continuar passando;
- `python -m pip check` não indicar dependências quebradas;
- documentação relevante for atualizada;
- o trabalho for revisado em PR antes da integração à `main`.

Não será adotada uma meta arbitrária de porcentagem de cobertura. O critério será cobertura dos comportamentos e regras relevantes do marco.

## 12. Relação com os requisitos do TCC

Este marco implementa diretamente:

- **RF02:** cadastro, consulta, edição e exclusão de conteúdos;
- **RF06:** operações restritas aos dados do usuário autenticado;
- **RNF01:** manutenção da arquitetura Controller–Service–Repository;
- **RNF02:** testes unitários e de integração;
- **RNF03:** proteção dos endpoints por JWT;
- **RNF05:** Service desacoplado da implementação concreta do banco;
- **RNF06:** separação de responsabilidades e facilidade de manutenção.

Também prepara o relacionamento necessário para o próximo marco, no qual métricas serão associadas aos conteúdos.
