# RF01 — Cadastro e autenticação

**Projeto:** MetricaMEI
**Situação:** atendido

## 1. Enunciado

> O sistema deve permitir que o usuário se cadastre e se autentique.

## 2. Escopo

O requisito cobre três operações:

```text
POST /auth/register   criação de conta
POST /auth/login      obtenção do token
GET  /auth/me         identificação do usuário autenticado
```

Na interface, correspondem às telas `/cadastrar` e `/entrar`, e à validação de sessão feita quando a aplicação abre.

## 3. Decisões e justificativas

### Senha armazenada com Argon2

A senha nunca é gravada em texto. O hash usa Argon2, vencedor da Password Hashing Competition e recomendado atualmente sobre alternativas mais antigas, por resistir a ataques com hardware dedicado através do custo de memória — algo que funções apenas iterativas não oferecem.

O documento de projeto exige senha "armazenada de forma criptografada"; hash com Argon2 atende de forma mais forte que cifragem reversível, que teria de guardar a chave em algum lugar.

### Autenticação stateless por JWT

Conforme o RNF03. O token carrega o identificador do usuário e expira em trinta minutos.

**Não há refresh token.** Ele foi excluído desde o Marco 0.2 e nenhum requisito o menciona. A consequência é assumida: após trinta minutos o usuário precisa entrar de novo, e a interface trata isso encerrando a sessão e explicando o motivo, em vez de deixar a tela em erro.

### E-mail único, comparado sem diferenciar maiúsculas

`Joao@email.com` e `joao@email.com` são a mesma conta. Sem isso, o mesmo endereço geraria contas distintas e o usuário não entenderia por que seus dados sumiram.

### Falha de login não revela qual campo errou

E-mail inexistente e senha errada devolvem a mesma resposta `401` com o mesmo texto. Distinguir os dois casos transformaria a tela de login em um verificador de quais e-mails têm conta no sistema.

### O cadastro não devolve token

`POST /auth/register` responde com o usuário criado, não com uma sessão. A interface encadeia o login logo em seguida para não pedir as credenciais duas vezes, mas a separação mantém cada endpoint com uma responsabilidade.

## 4. Critérios de aceite

1. O cadastro cria a conta e devolve os dados públicos do usuário com `201`;
2. a senha é gravada como hash, nunca em texto;
3. e-mail repetido é recusado com `409`, ignorando diferença de maiúsculas;
4. nome com menos de dois caracteres e senha com menos de oito são recusados com `422`;
5. o login devolve um token para credenciais válidas;
6. credenciais inválidas recebem `401` com a mesma mensagem, seja o erro no e-mail ou na senha;
7. `GET /auth/me` identifica o portador de um token válido;
8. token ausente, inválido ou expirado recebe `401`;
9. a interface permite criar conta e entrar sem uso da API direta.

## 5. Rastreabilidade

| Critério | Verificado em |
|---|---|
| 1, 2, 3, 4 | `tests/unit/test_auth_service_registration.py`, `tests/integration/test_auth_register.py` |
| 5, 6 | `tests/unit/test_auth_service_login.py`, `tests/integration/test_auth_login.py` |
| 7, 8 | `tests/unit/test_auth_service_current_user.py`, `tests/integration/test_auth_me.py` |
| 9 | `frontend/e2e/jornada.spec.ts` |

Requisitos relacionados: RNF01 (camadas), RNF02 (testes), RNF03 (JWT), RF06 (isolamento, que depende da identidade estabelecida aqui).
