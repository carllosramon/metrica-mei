# MetricaMEI — frontend

Interface web do MetricaMEI, em React com Vite e TypeScript.

A documentação completa do projeto, incluindo o backend, está no
[README principal](../README.md).

## Rodando

```bash
npm install
npm run dev
```

O endereço da API vem de `VITE_API_URL`, com padrão `http://localhost:8000`.
Copie o `.env.example` para `.env` se precisar apontar para outro lugar.

O backend precisa estar no ar, e as origens do frontend precisam constar em
`CORS_ORIGINS` no backend — o padrão já cobre `localhost:5173`.

## Estrutura

```text
src/
├── api/            contrato com o backend
├── autenticacao/   sessão, contexto e rota protegida
├── componentes/    peças reutilizáveis de interface
├── estilos/        variáveis e reset globais
├── paginas/        uma tela por arquivo
├── testes/         preparação do ambiente de teste
└── formatacao.ts   apresentação de números e datas
```

A nomeação do código é em português, diferente do backend, que segue a
convenção em inglês já consolidada lá.

## Testes

```bash
npm test          # unidade, com a API simulada
npm run test:e2e  # jornada completa em navegador real
```

O teste de ponta a ponta sobe backend e frontend de verdade. Ele espera
`python` no PATH; se não estiver, aponte `PYTHON_BIN` para o interpretador.

## Build

```bash
npm run build     # verifica os tipos e empacota em dist/
npm run preview   # serve o que foi empacotado
```
