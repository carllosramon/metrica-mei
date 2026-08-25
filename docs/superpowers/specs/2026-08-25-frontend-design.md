# Marco 0.7 — Frontend Design

## 1. Objetivo

O Marco 0.7 entrega a base do frontend em React e fecha o RF05.2: a apresentação dos indicadores consolidados em um painel de análise.

O marco inclui o projeto Vite, a liberação de CORS no backend, o cliente HTTP, o controle de sessão, as telas de cadastro e login, a rota protegida e a tela do painel.

Ficam fora deste marco os CRUDs de conteúdo e de métrica, que serão tratados no Marco 0.8. O usuário ainda cadastra conteúdos e métricas pela API.

## 2. Por que a fatia é esta

O frontend não se fatia por tela isolada. Sem login não há token, e sem token nenhuma rota responde; sem conteúdo e métrica cadastrados o painel aparece vazio. A menor fatia que entrega valor verificável é autenticação mais painel — que é exatamente o que falta para o RF05 fechar.

Os CRUDs ficam para depois porque são repetição de um padrão que este marco estabelece, e não conhecimento novo: mais formulários consumindo o mesmo cliente HTTP e a mesma sessão.

## 3. CORS

O backend não tinha liberação de origem cruzada. O frontend roda em `localhost:5173` e a API em `localhost:8000`, e o navegador bloqueia a requisição antes de ela sair.

`CORSMiddleware` passa a liberar as origens definidas em `CORS_ORIGINS`, com padrão para as duas formas do host local. A lista chega como texto separado por vírgula porque é assim que ela cabe em uma variável de ambiente, tanto no `.env` quanto na hospedagem.

Métodos e cabeçalhos são declarados explicitamente em vez de `*`: só `GET`, `POST`, `PATCH` e `DELETE`, e só `Authorization` e `Content-Type`. A lista explícita documenta a superfície real da API.

`allow_credentials` fica desligado. A sessão é transportada no cabeçalho `Authorization`, não em cookie, e ligar credenciais ampliaria a liberação sem necessidade.

## 4. Linguagem e nomeação

O frontend usa TypeScript. O backend é tipado de ponta a ponta, com `Protocol` nos repositórios e anotações em todas as assinaturas, e os tipos das respostas fazem o contrato virar verificação de build: se um campo mudar no backend, o front quebra ao compilar, e não na tela do usuário.

A nomeação é em **pt-BR**. Esta é a diferença em relação ao backend: lá os identificadores são em inglês por convenção já consolidada, e a skill de padrões manda respeitar o repositório. O frontend não tem convenção anterior, então a regra de nomear em pt-BR se aplica sem conflito.

Permanecem em inglês os termos consagrados e as APIs da plataforma: `token`, `fetch`, `Response`, os nomes de hooks do React.

## 5. Estrutura

```text
frontend/src/
├── api/            contrato com o backend
├── autenticacao/   sessão, contexto e rota protegida
├── componentes/    peças reutilizáveis de interface
├── estilos/        variáveis e reset globais
├── paginas/        uma pasta por tela
└── formatacao.ts   apresentação de números e datas
```

A separação espelha a do backend: `api/` é a borda, `autenticacao/` e `formatacao.ts` são regra, `paginas/` e `componentes/` são apresentação.

## 6. Cliente HTTP

`chamarApi` concentra base da URL, cabeçalhos, injeção do token e tradução de erro. Nenhuma tela chama `fetch` diretamente.

Duas decisões merecem registro:

**Erro de rede vira `ErroDaApi` com status zero.** Uma falha de conexão não tem status HTTP, e sem esse tratamento a tela receberia um `TypeError` cru do `fetch` e mostraria uma mensagem sem sentido para o usuário.

**O 422 do FastAPI recebe tratamento próprio.** Nas demais falhas o backend devolve `detail` como texto, mas na validação devolve uma lista de erros, um por campo. Sem separar os dois casos a tela exibiria `[object Object]`.

## 7. Sessão

O token fica em `localStorage`, sob a chave `metricamei.token`.

A alternativa seria cookie `HttpOnly`, que resiste a roubo por script injetado. Ela foi descartada porque exigiria o backend emitindo e validando cookie, proteção contra CSRF e `allow_credentials` ligado — uma reestruturação da autenticação inteira, que o Marco 0.2 já entregou e nenhum requisito pede para revisar.

O token guardado é validado contra `GET /auth/me` na montagem da aplicação. O JWT expira em trinta minutos, então o valor em `localStorage` pode estar vencido, e só o backend sabe dizer. Sem essa verificação a aplicação abriria o painel para quem já perdeu a sessão, e o erro só apareceria na primeira requisição.

Enquanto a verificação corre, o contexto expõe `verificando`. A rota protegida espera esse sinal antes de decidir: redirecionar durante a verificação mandaria para o login todo usuário que recarregasse a página com sessão válida.

O cadastro faz login logo em seguida, porque `POST /auth/register` devolve o usuário e não um token. Encadear os dois poupa o usuário de digitar as mesmas credenciais duas vezes.

## 8. Apresentação dos dados

`engajamento_geral` nulo aparece como travessão, com a observação "sem alcance registrado para calcular". Mostrar `0%` diria que o desempenho foi nulo, quando o que houve foi ausência de base de cálculo — a mesma distinção que o backend faz ao devolver `null`.

Datas vêm do backend como `AAAA-MM-DD` e são convertidas separando os campos do texto, sem passar por `new Date`. O construtor interpreta a data pura como meia-noite UTC, o que no fuso do Brasil volta um dia: `2026-01-01` viraria 31/12/2025 na tela.

Números usam separador de milhar brasileiro, e percentuais têm duas casas fixas.

O ranking vazio não some da tela: exibe uma orientação explicando que é preciso registrar métricas com alcance maior que zero. Uma área em branco não diz ao usuário o que fazer.

## 9. Estilo

CSS Modules, sem dependência nova. O escopo por componente vem do próprio Vite, e o projeto mantém a característica de só carregar dependências essenciais — o backend tem trinta e nove pacotes, todos com função clara.

As cores ficam em variáveis CSS num arquivo global, para que o Marco 0.8 acrescente telas sem redefinir a paleta.

## 10. Estratégia de testes

Vitest com Testing Library, cobrindo o que tem risco real de quebrar:

- `cliente.test.ts` — injeção do token, `detail` como texto, `detail` como lista de validação, status preservado no erro e falha de rede;
- `formatacao.test.ts` — percentual nulo contra percentual zero, e a data que voltaria um dia pelo fuso;
- `Painel.test.tsx` — indicadores renderizados, travessão com a explicação, orientação de ranking vazio, linha do ranking com data brasileira e mensagem de erro na falha da busca.

Formulários controlados e marcação não são testados: o retorno não paga o custo, e uma quebra ali aparece na primeira execução da tela.

No backend, `test_cors.py` cobre o preflight, a liberação de `Authorization` e a recusa de origem desconhecida.

## 11. Critérios de aceite

O Marco 0.7 estará concluído quando:

- o backend liberar as origens configuradas e recusar as demais;
- o usuário puder criar conta e entrar pela interface;
- a sessão sobreviver a recarga de página e expirar sem deixar a aplicação em estado quebrado;
- a rota do painel redirecionar para o login sem sessão;
- o painel exibir os nove indicadores e o ranking;
- índice não calculável aparecer como travessão explicado, e não como zero;
- `npm run build` e `npm test` passarem;
- a suíte do backend permanecer verde.

## 12. Fora de escopo

CRUD de conteúdos, CRUD de métricas, edição de perfil, recuperação de senha, tema escuro, internacionalização e responsividade além do essencial.

## 13. Próximo marco

O Marco 0.8 acrescenta as telas de conteúdo e métrica, reaproveitando o cliente HTTP, a sessão e a paleta estabelecidos aqui.
