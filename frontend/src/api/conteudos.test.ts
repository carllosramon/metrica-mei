import { afterEach, describe, expect, it, vi } from 'vitest'

import { simularApi } from '../testes/respostaHttp'
import {
  atualizarConteudo,
  buscarConteudo,
  criarConteudo,
  excluirConteudo,
  listarConteudos,
} from './conteudos'
import type { DadosDoConteudo } from './tipos'

// As páginas simulam este módulo, então só aqui os endereços de conteúdo
// executam de verdade. O que se fixa é o contrato com o backend, caminho,
// método e token de cada operação.

const dados: DadosDoConteudo = {
  titulo: 'Reels sobre preço',
  plataforma: 'Instagram',
  tipo: 'Reels',
  data_publicacao: '2026-08-21',
  url_publicacao: null,
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api de conteúdos', () => {
  it('listarConteudos consulta a coleção com o token', async () => {
    const requisicao = simularApi([])

    await listarConteudos('meu-token')

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe('http://localhost:8000/conteudos')
    expect(opcoes.method).toBe('GET')
    expect(opcoes.headers.Authorization).toBe('Bearer meu-token')
  })

  it('buscarConteudo monta o caminho com o id', async () => {
    const requisicao = simularApi({})

    await buscarConteudo('meu-token', 7)

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe('http://localhost:8000/conteudos/7')
    expect(opcoes.method).toBe('GET')
  })

  it('criarConteudo envia os dados por POST', async () => {
    const requisicao = simularApi({})

    await criarConteudo('meu-token', dados)

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe('http://localhost:8000/conteudos')
    expect(opcoes.method).toBe('POST')
    expect(JSON.parse(opcoes.body)).toEqual(dados)
  })

  it('atualizarConteudo corrige o registro por PATCH', async () => {
    const requisicao = simularApi({})

    await atualizarConteudo('meu-token', 7, dados)

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe('http://localhost:8000/conteudos/7')
    expect(opcoes.method).toBe('PATCH')
    expect(JSON.parse(opcoes.body)).toEqual(dados)
  })

  it('excluirConteudo remove o registro por DELETE', async () => {
    const requisicao = simularApi(undefined)

    await excluirConteudo('meu-token', 7)

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe('http://localhost:8000/conteudos/7')
    expect(opcoes.method).toBe('DELETE')
    expect(opcoes.headers.Authorization).toBe('Bearer meu-token')
  })
})
