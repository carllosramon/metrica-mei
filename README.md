# MetricaMEI

Sistema web para análise de métricas de conteúdos digitais em microempreendimentos.

Este projeto está sendo desenvolvido como Trabalho de Conclusão de Curso em Ciência da Computação.

## Backend

O backend utiliza:

- Python

- FastAPI

- SQLAlchemy

- SQLite no ambiente de desenvolvimento

- Alembic para migrations

- Argon2 para hash de senhas

- JWT para autenticação

- Pytest para testes automatizados

## Arquitetura

A aplicação segue uma arquitetura em camadas:

```text

Controller

    ↓

Service

    ↓

Repository

    ↓

Persistência

```

Os Controllers tratam requisições HTTP.

Os Services concentram as regras de negócio.

Os Repositories abstraem o acesso aos dados.

O objetivo é manter as regras de negócio desacopladas da camada HTTP e do mecanismo de persistência.

## Configuração do ambiente

Entre na pasta do backend:

```powershell

cd backend

```

Crie o ambiente virtual:

```powershell

python -m venv .venv

```

Ative o ambiente:

```powershell

.\\.venv\\Scripts\\Activate.ps1

```

Instale as dependências:

```powershell

python -m pip install -r requirements.txt

```

Crie o arquivo local de configuração a partir do exemplo:

```powershell

Copy-Item .env.example .env

```

Abra o arquivo `.env` e substitua:

```text

JWT_SECRET=replace-with-a-local-secret

```

por um segredo local seguro.

Uma forma de gerar o segredo é:

```powershell

python -c "import secrets; print(secrets.token_urlsafe(48))"

```

O arquivo `.env` não deve ser versionado.

## Banco de dados

O ambiente de desenvolvimento utiliza SQLite.

Para criar ou atualizar a estrutura do banco:

```powershell

python -m alembic upgrade head

```

As migrations atuais criam as tabelas:

```text
usuarios
conteudos
```

A tabela `conteudos` referencia `usuarios.id` por `usuario_id`.

O banco local é armazenado em:

```text

backend/data/metrica_mei.db

```

Esse arquivo não é versionado.

## Executando a API

Dentro de `backend` e com o ambiente virtual ativo:

```powershell

python -m uvicorn app.main:app --reload

```

A documentação interativa da API pode ser acessada em:

```text

http://127.0.0.1:8000/docs

```

## Endpoints atuais

### GET /health

Verifica se a API está em execução.

Resposta:

```json

{

  "status": "ok"

}

```

### POST /auth/register

Cadastra um usuário.

Exemplo:

```json

{

  "nome": "Carlos Ramon",

  "email": "carlos@email.com",

  "senha": "minhasenha"

}

```

O cadastro armazena apenas o hash da senha.

### POST /auth/login

Autentica o usuário.

Exemplo:

```json

{

  "email": "carlos@email.com",

  "senha": "minhasenha"

}

```

Em caso de sucesso retorna:

```json

{

  "access_token": "...",

  "token_type": "bearer"

}

```

### GET /auth/me

Retorna os dados públicos do usuário autenticado.

Requer o header:

```text

Authorization: Bearer <token>

```

### POST /conteudos

Cria um conteúdo para o usuário autenticado.

Requer:

```text
Authorization: Bearer <token>
```

Exemplo:

```json
{
  "titulo": "Resultados do mês",
  "plataforma": "Instagram",
  "tipo": "Carrossel",
  "data_publicacao": "2026-08-20"
}
```

### GET /conteudos

Lista somente os conteúdos do usuário autenticado, ordenados por data de publicação mais recente e, em caso de empate, pelo maior `id`.

### GET /conteudos/{id}

Retorna um conteúdo do usuário autenticado.

Conteúdo inexistente ou pertencente a outro usuário retorna `404`.

### PATCH /conteudos/{id}

Atualiza parcialmente `titulo`, `plataforma`, `tipo` e/ou `data_publicacao`.

Payload vazio é inválido.

### DELETE /conteudos/{id}

Exclui definitivamente um conteúdo do usuário autenticado.

Em caso de sucesso retorna `204 No Content`.

## Testes automatizados

Para executar toda a suíte:

```powershell

python -m pytest -v

```

Os testes estão divididos em:

```text

tests/

├── unit/

└── integration/

```

Os testes unitários verificam regras de negócio utilizando um Repository em memória.

Os testes de integração percorrem as camadas da aplicação utilizando SQLite isolado do banco de desenvolvimento.

## Segurança

As senhas são protegidas com Argon2.

A autenticação utiliza JWT HS256 com access token de 30 minutos.

Segredos são carregados através de variáveis de ambiente e não devem ser armazenados no repositório.

## Estado atual

O Marco 0.3 implementa:

```text
cadastro/login
      ↓
     JWT
      ↓
usuário autenticado
      ↓
CRUD de conteúdos
      ↓
ownership por usuário
```

O backend possui autenticação e gerenciamento de conteúdos com arquitetura Controller–Service–Repository, testes unitários com Repository em memória e testes de integração com SQLite isolado.

Métricas, cálculo de engajamento, dashboard e frontend fazem parte dos próximos marcos.
