import { afterEach, describe, expect, it, vi } from 'vitest'

import { simularApi } from '../testes/respostaHttp'
import { buscarUsuarioAtual, cadastrar, entrar } from './autenticacao'

// Estes testes atravessam o chamarApi de verdade, com o fetch simulado na
// ponta. As telas simulam este módulo inteiro, então sem isto os endereços
// de autenticação nunca executariam e um caminho digitado errado passaria
// batido até a jornada.

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api de autenticação', () => {
  it('cadastrar envia nome, e-mail e senha para o registro', async () => {
    const requisicao = simularApi()

    await cadastrar('Joao', 'joao@email.com', 'minhasenha')

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe('http://localhost:8000/auth/register')
    expect(opcoes.method).toBe('POST')
    expect(JSON.parse(opcoes.body)).toEqual({
      nome: 'Joao',
      email: 'joao@email.com',
      senha: 'minhasenha',
    })
  })

  it('entrar envia as credenciais para o login', async () => {
    const requisicao = simularApi({
      access_token: 'abc',
      token_type: 'bearer',
    })

    const token = await entrar('joao@email.com', 'minhasenha')

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe('http://localhost:8000/auth/login')
    expect(opcoes.method).toBe('POST')
    expect(JSON.parse(opcoes.body)).toEqual({
      email: 'joao@email.com',
      senha: 'minhasenha',
    })
    expect(token.access_token).toBe('abc')
  })

  it('buscarUsuarioAtual consulta /auth/me com o token', async () => {
    const requisicao = simularApi({ id: 1, nome: 'Joao' })

    await buscarUsuarioAtual('token-guardado')

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe('http://localhost:8000/auth/me')
    expect(opcoes.method).toBe('GET')
    expect(opcoes.headers.Authorization).toBe('Bearer token-guardado')
  })
})
