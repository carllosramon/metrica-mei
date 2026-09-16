# MetricaMEI

Sistema web para análise de métricas de conteúdos digitais em microempreendimentos, desenvolvido com arquitetura em camadas e testes automatizados.

Projeto desenvolvido como Trabalho de Conclusão de Curso do curso de Ciência da Computação do Instituto Federal de Santa Catarina (IFSC) — Câmpus Lages.

## Integrantes

- Carlos Ramon Moreira
- Joao Pedro Ribeiro Biazzin

## Orientadores

- Orlando Santos
- Alexandre Perin de Souza

## Sobre o projeto

O MetricaMEI tem como objetivo desenvolver um sistema web para centralizar o registro e a análise de métricas de conteúdos digitais utilizados por microempreendedores.

A aplicação permite organizar conteúdos publicados em diferentes plataformas e registrar métricas associadas a esses conteúdos ao longo do tempo.

Além das funcionalidades do sistema, o trabalho possui como foco técnico a utilização de uma arquitetura em camadas e de testes automatizados para favorecer organização, manutenção, testabilidade e evolução do software.

## Arquitetura

O backend segue a arquitetura:

```text
Controller
    ↓
Service
    ↓
Repository
    ↓
Persistência
```

### Controller

Responsável pela camada HTTP: recebe requisições, valida schemas de entrada, utiliza autenticação e delega os casos de uso ao Service.

A conversão de exceções em respostas HTTP saiu daqui. Cada rota repetia o mesmo bloco de `try/except`, e bastava esquecer um para a falha virar `500`. Hoje os manipuladores ficam registrados na aplicação, em `app/erros.py`, e valem para toda rota por definição.

### Service

Concentra as regras de negócio e os casos de uso da aplicação. Essa camada não depende diretamente de FastAPI ou SQLAlchemy.

### Repository

Abstrai o acesso aos dados. Os Services dependem de contratos de Repository, permitindo utilizar diferentes implementações de persistência sem alterar as regras de negócio.

A aplicação usa as implementações com SQLAlchemy. Os testes unitários usam dublês em memória, que vivem em `tests/dubles` e respondem com a mesma semântica dos reais, incluindo posse, unicidade e exclusão em cascata. Onde o dublê fosse mais permissivo, o teste aprovaria comportamento que a aplicação não tem.

### Tradução de erros

Os erros de domínio viram resposta HTTP num registro único, em `app/erros.py`, e não em cada endpoint. Assim um endpoint novo não precisa lembrar de traduzir, e cada erro tem uma resposta só.

## Tecnologias

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- PyJWT
- Argon2
- Pytest

### Banco de dados

Atualmente são utilizados:

- SQLite no desenvolvimento local e na suíte principal de testes;
- PostgreSQL 16 na integração contínua para validar as migrations e o schema;
- SQLAlchemy como camada de acesso aos dados;
- Alembic para versionamento do schema.

A arquitetura permite utilizar PostgreSQL sem alterar as regras de negócio da aplicação. A cadeia completa de migrations é validada automaticamente em uma instância PostgreSQL real na integração contínua.

### Frontend

React com Vite e TypeScript, roteamento com React Router e estilo em CSS Modules. Testes com Vitest e Testing Library.

## Estrutura do backend

```text
backend/
├── alembic/
│   └── versions/
├── app/
│   ├── controllers/
│   ├── database/
│   ├── domain/
│   ├── repositories/
│   ├── schemas/
│   ├── security/
│   ├── services/
│   ├── config.py
│   ├── dependencies.py
│   ├── erros.py
│   └── main.py
├── tests/
│   ├── dubles/
│   ├── integration/
│   └── unit/
├── alembic.ini
├── requirements.txt
└── .env.example
```

## Funcionalidades implementadas

### Autenticação

O sistema possui cadastro de usuários, login, autenticação utilizando JWT, recuperação do usuário autenticado e hash de senhas utilizando Argon2.

Endpoints disponíveis:

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

### Conteúdos

O usuário autenticado pode cadastrar conteúdos, listar seus conteúdos, consultar um conteúdo, atualizar parcialmente um conteúdo e excluir um conteúdo.

Os dados de um conteúdo são:

```text
titulo
plataforma
tipo
data_publicacao
url_publicacao
```

A URL de publicação é opcional e pode ser removida enviando `null` no `PATCH`.

A regra não é mais "começa com `http://` ou `https://`". Conferir o prefixo deixava passar `https://` sozinho, sem endereço nenhum, e recusava `HTTPS://`, que é válido porque o esquema não distingue caixa. Hoje o endereço é decomposto: o esquema precisa ser `http` ou `https`, comparado sem caixa, e precisa haver um destino depois dele. O limite é de 500 caracteres.

Endpoints disponíveis:

```text
POST   /conteudos
GET    /conteudos
GET    /conteudos/{content_id}
PATCH  /conteudos/{content_id}
DELETE /conteudos/{content_id}
```

A listagem traz, em cada item, `ultima_medicao`: a data de referência da medição mais recente do conteúdo, ou `null` quando ele nunca foi medido. É o que responde "o que eu ainda não anotei" sem abrir um conteúdo por vez, que é a rotina que o sistema se propõe a apoiar. O campo não aparece na consulta individual, onde seria sempre nulo.

O sistema aplica ownership por usuário: um usuário não pode consultar, alterar ou excluir conteúdos pertencentes a outro usuário.

### Métricas

O módulo de métricas possui implementação das camadas de domínio, negócio, persistência e HTTP.

Cada métrica é um snapshot cumulativo de um conteúdo em uma determinada data de referência.

Os dados registrados são:

```text
visualizacoes
curtidas
comentarios
compartilhamentos
alcance
data_referencia
```

O módulo atualmente possui:

- entidade de domínio `Metric`;
- contrato `MetricRepository`;
- `SQLAlchemyMetricRepository`, a implementação que a aplicação usa;
- `InMemoryMetricRepository`, dublê de teste em `tests/dubles`, fora do
  pacote da aplicação;
- `MetricService`;
- operações de criação, listagem, consulta, atualização e exclusão;
- validação de valores inteiros não negativos;
- validação da data de referência;
- verificação de ownership através do conteúdo;
- prevenção de métricas duplicadas;
- tratamento de conflitos de persistência;
- rollback da sessão em conflitos do banco;
- ordenação por data de referência e identificador.

A combinação abaixo é única:

```text
conteudo_id + data_referencia
```

Isso impede que um mesmo conteúdo possua dois snapshots para a mesma data.

A integração do módulo de métricas com a camada HTTP está concluída.

Endpoints disponíveis:

```text
POST   /conteudos/{content_id}/metricas
GET    /conteudos/{content_id}/metricas
GET    /conteudos/{content_id}/metricas/{metric_id}
PATCH  /conteudos/{content_id}/metricas/{metric_id}
DELETE /conteudos/{content_id}/metricas/{metric_id}
```

Todas as rotas exigem autenticação JWT e respeitam o ownership através do conteúdo.

### Índice de engajamento

Toda resposta de métrica traz o campo `engajamento`, calculado por:

```text
(curtidas + comentarios + compartilhamentos)
--------------------------------------------- × 100
                  alcance
```

O valor é arredondado para duas casas decimais e não é persistido: ele é calculado na camada de serviço a cada leitura, evitando uma segunda fonte de verdade que ficaria desatualizada a cada `PATCH`.

Quando o alcance é zero, o campo retorna `null`. Alcance zero não significa desempenho nulo, e sim que o índice não é calculável — o que é diferente de um engajamento realmente zero.

A fórmula vive isolada em `app/services/engagement.py`, como função pura, para que o painel de análise possa reaproveitá-la sem depender do serviço de métricas.

### Painel de análise

Um único endpoint devolve os números consolidados da conta do usuário
autenticado:

```text
GET /painel
```

A resposta traz:

```text
total_conteudos
conteudos_com_metricas
total_visualizacoes
total_curtidas
total_comentarios
total_compartilhamentos
total_alcance
engajamento_geral
desempenho_por_plataforma
maiores_alcances
```

Como cada métrica é um snapshot cumulativo, o painel usa **apenas a medição
mais recente de cada conteúdo**. Somar todo o histórico multiplicaria os
números, porque cada snapshot já contém o total acumulado até a sua data.

O `engajamento_geral` é calculado sobre os totais, e não como média dos
engajamentos individuais — na média, um conteúdo de alcance 10 pesaria o mesmo
que um de alcance 50.000. Entram nesses totais apenas as medições com alcance
maior que zero: medição sem alcance não tem base de cálculo, e deixá-la somar
interações ao numerador cobrava as curtidas de um conteúdo do alcance de outro,
chegando a devolver um índice de conta acima do de qualquer conteúdo dela. Os
números brutos continuam somando todas as medições, e a medição sem alcance
continua no ranking, apenas sem índice. Quando nenhuma medição tem alcance, o
campo vem `null`.

O `desempenho_por_plataforma` agrupa as medições por rede, ignorando diferença
de maiúsculas — `plataforma` é texto livre, e `Instagram` e `instagram` são a
mesma rede. Cada rede traz os dois contadores da seção anterior,
`total_conteudos` com todos os conteúdos dela e `conteudos_com_metricas` com os
que já têm medição. Uma rede onde o usuário publicou e ainda não mediu aparece
zerada, e não omitida, porque a ausência de medição é justamente o que ele
precisa ver.

As duas seções vêm acompanhadas de visualização gráfica: barras comparando o
alcance das plataformas e, na tela de um conteúdo, uma linha com a evolução do
engajamento ao longo das medições. Os gráficos acompanham as tabelas em vez de
substituí-las — a tabela continua sendo a leitura exata dos mesmos números.

O `maiores_alcances` traz até cinco conteúdos ordenados por alcance decrescente,
com o índice de engajamento ao lado para não induzir à leitura de que o mais
alcançado é o de melhor desempenho. Conteúdos sem medição ficam de fora; os de
alcance zero entram na última posição, apenas sem índice.

Uma conta sem conteúdo nenhum recebe `200` com o painel zerado. Ausência de
dado é a primeira tela de todo usuário novo, não uma falha.

A especificação completa do requisito, com a justificativa de cada decisão e
os critérios de aceite, está em `docs/requisitos/RF05-painel-de-analise.md`.

## Requisitos

Cada requisito funcional tem um documento próprio em `docs/requisitos/`, com o
enunciado da especificação, as decisões de projeto justificadas, os critérios
de aceite numerados e a rastreabilidade para os testes que os verificam.

```text
RF01-autenticacao.md      cadastro e autenticação
RF02-conteudos.md         gerenciamento de conteúdos
RF03-metricas.md          registro de métricas
RF04-engajamento.md       índice de engajamento
RF05-painel-de-analise.md painel de análise
RF06-isolamento.md        acesso restrito aos próprios dados
```

## Frontend

Aplicação em React com Vite e TypeScript, no diretório `frontend/`.

```text
frontend/src/
├── api/            contrato com o backend
├── autenticacao/   sessão, contexto e rota protegida
├── componentes/    peças reutilizáveis de interface
├── estilos/        variáveis e reset globais
├── paginas/        uma tela por arquivo
└── formatacao.ts   apresentação de números e datas
```

Telas disponíveis:

```text
/cadastrar          criação de conta
/entrar             login
/painel             painel de análise
/conteudos          lista e cadastro de conteúdos
/conteudos/:id      edição do conteúdo e histórico de medições
```

Todas as telas exceto cadastro e login exigem sessão.

A sessão guarda o token em `localStorage` e o valida contra `GET /auth/me` ao
abrir a aplicação, porque o JWT expira em trinta minutos e o valor guardado
pode estar vencido. Se o token vencer com a tela aberta, qualquer resposta
`401` encerra a sessão e devolve o usuário ao login com aviso, em vez de
deixá-lo numa tela que não carrega.

O estilo usa CSS Modules, sem dependência adicional.

A nomeação do frontend é toda em português. No backend a fronteira é outra: o
que é contrato com o mundo fica em português, porque é o vocabulário do
usuário e o que aparece na API, e a estrutura interna segue o inglês. Um
`Content` tem `titulo` e `data_publicacao`; um `ContentService` levanta
`InvalidContentError` com mensagem em português. Código escrito nos marcos
mais recentes nomeia em português também as variáveis e os métodos privados,
onde o leitor é sempre a dupla.

Para rodar:

```bash
cd frontend
npm install
npm run dev
```

O endereço da API vem de `VITE_API_URL`, com padrão `http://localhost:8000`.
Veja `frontend/.env.example`.

Testes do frontend:

```bash
npm test
```

```text
145 testes passando
```

Com medição de cobertura:

```bash
npm run test:coverage
```

```text
Statements   : 92.59%
Branches     : 85.71%
Functions    : 94.28%
Lines        : 92.51%
```

O piso configurado é o valor medido, arredondado para baixo, e a execução
reprova quando a cobertura cai abaixo dele. Ficam fora da conta o ponto de
entrada, as declarações de tipo e os próprios testes.

Os módulos de `src/api` são exercitados contra o cliente HTTP real, com o
`fetch` simulado na ponta, fixando caminho, método e token de cada operação.
A tela de detalhe tem os caminhos de falha cobertos, salvar, editar e excluir
com o servidor recusando. O que segue sem teste unitário direto são os
componentes de moldura, como layout e navegação, que a jornada de ponta a
ponta atravessa em navegador real.

Jornada de ponta a ponta em navegador real, com backend e frontend no ar:

```bash
npm run test:e2e
```

Ela cobre criar conta, cadastrar conteúdo, registrar medição e conferir o
painel. Requer `PYTHON_BIN` apontando para o interpretador quando `python` não
estiver no PATH.

## Banco de dados

As migrations atuais criam:

```text
usuarios
   ↓
conteudos
   ↓
metricas
```

### usuarios

Armazena os usuários do sistema.

### conteudos

A coluna `url_publicacao` é opcional e armazena o endereço público do conteúdo na plataforma.

Cada conteúdo pertence a um usuário através de:

```text
usuario_id → usuarios.id
```

### metricas

Cada métrica pertence a um conteúdo através de:

```text
conteudo_id → conteudos.id
```

A Foreign Key utiliza:

```text
ON DELETE CASCADE
```

Assim, ao excluir um conteúdo, suas métricas também são excluídas.

No SQLite, o projeto ativa:

```sql
PRAGMA foreign_keys=ON
```

para garantir a aplicação das Foreign Keys.

A migration atual mais recente é:

```text
0004_url_publicacao_conteudos
```

### Trocando o banco de produção

O projeto usa SQLite em desenvolvimento e nos testes, e prevê PostgreSQL em
produção. A troca é apenas a variável de ambiente:

```text
DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/metricamei
```

Depois, `alembic upgrade head` cria o esquema no banco novo.

Nenhuma regra de negócio precisa mudar, conforme o RNF05: os Services conversam
com os contratos de repositório, as migrations usam apenas tipos portáveis, e o
que é específico do SQLite — `check_same_thread` e o `PRAGMA foreign_keys` —
está isolado em `create_engine_from_url`, condicionado ao prefixo da URL.

A jornada de ponta a ponta também roda contra o PostgreSQL na integração
contínua, com o backend apontado para o serviço do job. Localmente ela
continua usando SQLite, salvo se `DATABASE_URL` disser o contrário.

A integração contínua executa `alembic upgrade head` em uma instância
PostgreSQL 16 criada para o job, verifica o schema resultante e **roda a suíte
de testes contra esse mesmo banco**. Assim as consultas reais da aplicação — as
do painel, as de unicidade e as de ownership — são exercitadas no banco de
produção previsto, e não apenas em SQLite.

Isso importa porque o SQLite é permissivo onde o PostgreSQL não é. O revision
id da migration `0004` passou três marcos com 33 caracteres, acima do limite de
32 da coluna de versão do Alembic: o SQLite não valida tamanho de `VARCHAR` e
aceitou; o PostgreSQL recusou assim que foi executado de verdade.

### Rodando a suíte contra um PostgreSQL local

Sem configuração, cada teste usa o próprio arquivo SQLite temporário. Para
apontar a suíte para um PostgreSQL, crie uma vez o papel e o banco:

```sql
CREATE ROLE metricamei LOGIN PASSWORD 'metricamei';
CREATE DATABASE metricamei_test OWNER metricamei;
```

E execute com a variável apontando para ele:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://metricamei:metricamei@localhost:5432/metricamei_test"
python -m pytest
```

O banco é compartilhado por todos os testes, então o schema é derrubado e
recriado a cada um. Por segurança, `TEST_DATABASE_URL` só aceita bancos cujo
nome declare explicitamente uso de teste, como `test`, `teste`, `*_test` ou
`*_teste`. Isso evita que a suíte execute o reset do schema em um banco de
desenvolvimento ou produção por engano.

Os testes que verificam comportamento específico do SQLite e os da cadeia de
migrations continuam em SQLite, porque é isso que eles verificam.

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
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

Crie o arquivo `.env` local:

```powershell
Copy-Item .env.example .env
```

No `.env`, preencha o `JWT_SECRET`. Ele vem vazio no exemplo de propósito:
um valor de exemplo é um valor que alguém copia sem trocar, e aí quem leu o
repositório sabe assinar token como qualquer usuário. Vazio, a API recusa
subir e diz o motivo.

Gere o seu com:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

O arquivo `.env` não deve ser versionado.

## Preparando o banco

Com o ambiente virtual ativo:

```powershell
python -m alembic upgrade head
```

O banco SQLite local é armazenado em:

```text
backend/data/metrica_mei.db
```

O arquivo do banco não é versionado.

## Executando a API

Dentro de `backend`:

```powershell
python -m uvicorn app.main:app --reload
```

A API estará disponível em:

```text
http://127.0.0.1:8000
```

A documentação automática do FastAPI pode ser acessada em:

```text
http://127.0.0.1:8000/docs
```

## Health check

```text
GET /health
```

Resposta:

```json
{
  "status": "ok"
}
```

## Testes automatizados

O projeto utiliza desenvolvimento orientado a testes em diversas etapas da implementação.

Para executar toda a suíte:

```powershell
python -m pytest -q
```

Ou de forma detalhada:

```powershell
python -m pytest -v
```

Os testes estão separados em:

```text
tests/
├── unit/
└── integration/
```

### Testes unitários

Validam principalmente regras de negócio dos Services utilizando Repositories em memória.

### Testes de integração

Validam a integração entre componentes reais da aplicação, incluindo API, autenticação, SQLAlchemy, SQLite, models, repositories, migrations, constraints e Foreign Keys.

No estado atual do desenvolvimento:

```text
319 testes passando
```

Com medição de cobertura:

```powershell
python -m coverage run -m pytest -q
python -m coverage report
```

```text
995 instruções, 12 sem cobrir, 99%
```

O piso configurado no `.coveragerc` é 99, o valor medido arredondado para
baixo, e o `coverage report` reprova abaixo dele. As doze instruções que
faltam estão espalhadas por seis arquivos, quase todas em ramos de erro de
infraestrutura: escolha de dialeto na conexão, falha de sessão nas
dependências e colisões de escrita que só um banco concorrente produz.

## Integração contínua

Cada push e cada pull request disparam quatro trabalhos paralelos: backend,
frontend, jornada de ponta a ponta e validação em PostgreSQL 16. O job de
PostgreSQL aplica todas as migrations e inspeciona o schema criado. Os jobs de
backend e de frontend rodam as suítes com medição de cobertura, então uma queda
abaixo do piso de qualquer um dos lados reprova a branch. Quando a jornada de navegador falha, o relatório fica anexado
à execução, mostrando em que passo ela parou.

A configuração está em `.github/workflows/testes.yml`.

## Segurança

O projeto atualmente utiliza Argon2 para hash de senhas, JWT com algoritmo HS256, access token com expiração, variáveis de ambiente para segredos e isolamento dos recursos pelo usuário autenticado.

Segredos e arquivos locais de banco de dados não são versionados.

## Implantação

O trabalho prevê PostgreSQL em produção, e a passagem de uma máquina de
desenvolvimento para um servidor tem quatro pontos que já custaram tempo
aqui.

**O segredo.** `JWT_SECRET` precisa ter ao menos 32 caracteres, e a API
recusa subir sem isso, na subida e não no primeiro login. Gere um valor
próprio para o servidor; o da máquina de desenvolvimento não serve, porque
um token assinado num lugar passa a valer no outro.

**O banco.** Troque `DATABASE_URL` para a URL do PostgreSQL e rode as
migrations antes de subir a aplicação:

```bash
alembic upgrade head
```

Se a senha do banco tiver caractere codificado, como `%40` no lugar da
arroba, ela passa pela URL sem problema — o `env.py` escapa o `%` antes de
entregá-la ao Alembic, que de outro modo o leria como interpolação.

**As origens.** `CORS_ORIGINS` recebe os endereços de onde o frontend será
servido, separados por vírgula. A barra final é ignorada, mas o esquema e a
porta contam: `https://app.exemplo.com` e `http://app.exemplo.com` são
origens diferentes para o navegador.

**O endereço da API no pacote.** O frontend embute `VITE_API_URL` no momento
do build, e não lê a variável em tempo de execução. Gerar o pacote sem ela
produz um site que procura a API em `localhost:8000` e só funciona na
máquina de quem o gerou; o build avisa quando isso acontece.

```bash
VITE_API_URL=https://api.exemplo.com npm run build
```

## Estado atual do desenvolvimento

O Marco 0.11 implementa:

```text
Cadastro e login
      ↓
     JWT
      ↓
Usuário autenticado
      ↓
CRUD de conteúdos
      ↓
Histórico de métricas
      ↓
Índice de engajamento
      ↓
Painel consolidado
      ↓
Interface React completa
      ↓
Ownership por conteúdo
```

O backend possui autenticação, gerenciamento de conteúdos, snapshots históricos de métricas, cálculo do índice de engajamento e painel consolidado de análise utilizando arquitetura Controller–Service–Repository.

O RF03 está implementado com criação, listagem, consulta, atualização e exclusão de métricas.

O RF04 está implementado com o índice de engajamento exposto em todas as respostas de métricas, calculado na camada de serviço e não persistido.

O RF05 está concluído nas suas duas partes: a disponibilização dos dados em `GET /painel`, agregando o snapshot mais recente de cada conteúdo sem criar tabelas nem colunas, e a apresentação na tela do painel em React.

A migration mais recente é:

```text
0004_url_publicacao_conteudos
```

O frontend cobre todo o fluxo do sistema: cadastro, login, gestão de conteúdos, registro de medições e painel de análise. Nenhuma operação depende mais de chamar a API diretamente.

## Próximas etapas

As próximas etapas planejadas são:

1. avaliar a qualidade em uso com usuários, conforme a ISO/IEC 25010;
2. ampliar a cobertura de testes conforme a evolução do sistema.

## Fluxo de desenvolvimento

O projeto utiliza Git com desenvolvimento por branches. A branch `main` representa a linha principal do projeto e funcionalidades são desenvolvidas em branches específicas e posteriormente integradas por Pull Request.

Durante a implementação, é utilizado o ciclo:

```text
RED
 ↓
GREEN
 ↓
REFACTOR
```

Primeiro é criado um teste que demonstra o comportamento esperado. Em seguida é implementado o código mínimo necessário para fazê-lo passar e, quando necessário, o código é refatorado mantendo os testes verdes.

---

**MetricaMEI**
Trabalho de Conclusão de Curso — Ciência da Computação
Instituto Federal de Santa Catarina — IFSC, Câmpus Lages
