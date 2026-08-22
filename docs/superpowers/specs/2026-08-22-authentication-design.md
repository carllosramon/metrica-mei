\# Marco 0.2 — Autenticação e Persistência de Usuários



Data: 2026-08-22



\## 1. Objetivo



Implementar o primeiro fluxo de negócio real do MetricaMEI: cadastro e autenticação de usuários.



O marco introduz:



\- arquitetura Controller → Service → Repository;

\- persistência com SQLAlchemy;

\- SQLite no ambiente de desenvolvimento;

\- migrations com Alembic;

\- hashing de senhas com Argon2;

\- autenticação por JWT;

\- testes unitários e de integração;

\- endpoint protegido para identificação do usuário autenticado.



Ficam fora deste marco:



\- conteúdos;

\- métricas;

\- dashboard;

\- frontend React;

\- refresh token;

\- PostgreSQL em produção.



---



\## 2. Entidade Usuario



A entidade de domínio terá:



\- `id`

\- `nome`

\- `email`

\- `senha\_hash`

\- `criado\_em`



A API nunca deverá retornar `senha` ou `senha\_hash`.



\### Regras



\#### Nome



\- obrigatório;

\- remover espaços externos;

\- mínimo de 2 caracteres;

\- máximo de 100 caracteres.



\#### E-mail



\- obrigatório;

\- formato válido;

\- remover espaços externos;

\- armazenar em letras minúsculas;

\- único no sistema.



\#### Senha



\- obrigatória;

\- mínimo de 8 caracteres;

\- máximo de 128 caracteres;

\- nunca armazenada em texto puro;

\- hash gerado com Argon2.



---



\## 3. Arquitetura



O fluxo principal será:



HTTP

→ Controller

→ Service

→ Repository

→ Persistência



\### Controller



Responsável por:



\- receber requisições HTTP;

\- validar schemas de entrada;

\- chamar o Service;

\- transformar exceções de negócio em respostas HTTP.



Não deverá conter regras de negócio.



\### Service



Responsável por:



\- regras de cadastro;

\- normalização de dados;

\- verificação de e-mail duplicado;

\- hashing de senha;

\- autenticação;

\- validação de credenciais;

\- geração de JWT.



O Service não conhecerá detalhes de SQLAlchemy ou SQLite.



\### Repository



Será a abstração responsável pelo acesso aos usuários.



Haverá duas implementações:



1\. `SQLAlchemyUserRepository`

&nbsp;  - usada pela aplicação real;

&nbsp;  - persiste em SQLite durante o desenvolvimento.



2\. `InMemoryUserRepository`

&nbsp;  - usada em testes unitários;

&nbsp;  - não depende de banco de dados.



---



\## 4. Estrutura prevista



```text

backend/

├── app/

│   ├── main.py

│   ├── controllers/

│   │   └── auth\_controller.py

│   ├── services/

│   │   └── auth\_service.py

│   ├── repositories/

│   │   ├── user\_repository.py

│   │   ├── sqlalchemy\_user\_repository.py

│   │   └── in\_memory\_user\_repository.py

│   ├── domain/

│   │   └── user.py

│   ├── schemas/

│   │   └── auth.py

│   ├── database/

│   │   ├── connection.py

│   │   └── models.py

│   ├── security/

│   │   ├── password.py

│   │   └── jwt.py

│   └── dependencies.py

├── tests/

│   ├── unit/

│   └── integration/

├── alembic/

│   └── versions/

├── alembic.ini

└── data/

