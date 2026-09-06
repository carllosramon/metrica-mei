import { afterEach, describe, expect, it, vi } from 'vitest'

import { simularApi } from '../testes/respostaHttp'
import { buscarPainel } from './painel'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api do painel', () => {
  it('buscarPainel consulta o consolidado com o token', async () => {
    const requisicao = simularApi({ total_conteudos: 3 })

    const painel = await buscarPainel('meu-token')

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe('http://localhost:8000/painel')
    expect(opcoes.method).toBe('GET')
    expect(opcoes.headers.Authorization).toBe('Bearer meu-token')
    expect(painel.total_conteudos).toBe(3)
  })
})
