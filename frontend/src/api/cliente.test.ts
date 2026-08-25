import { afterEach, describe, expect, it, vi } from 'vitest'

import { ErroDaApi, chamarApi } from './cliente'

function responderCom(status: number, corpo: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => corpo,
  } as Response
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('chamarApi', () => {
  it('devolve o corpo quando a resposta é bem-sucedida', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(responderCom(200, { total_conteudos: 3 })),
    )

    const resultado = await chamarApi<{ total_conteudos: number }>(
      '/painel',
    )

    expect(resultado.total_conteudos).toBe(3)
  })

  it('envia o token no cabeçalho de autorização', async () => {
    const requisicao = vi
      .fn()
      .mockResolvedValue(responderCom(200, {}))

    vi.stubGlobal('fetch', requisicao)

    await chamarApi('/painel', { token: 'meu-token' })

    const opcoes = requisicao.mock.calls[0][1]

    expect(opcoes.headers.Authorization).toBe('Bearer meu-token')
  })

  it('usa a mensagem de detail quando o backend manda texto', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        responderCom(401, { detail: 'E-mail ou senha inválidos.' }),
      ),
    )

    await expect(chamarApi('/auth/login')).rejects.toThrow(
      'E-mail ou senha inválidos.',
    )
  })

  it('junta as mensagens quando o 422 devolve lista de erros', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        responderCom(422, {
          detail: [
            { loc: ['body', 'senha'], msg: 'Senha muito curta' },
            { loc: ['body', 'email'], msg: 'E-mail inválido' },
          ],
        }),
      ),
    )

    await expect(chamarApi('/auth/register')).rejects.toThrow(
      'Senha muito curta. E-mail inválido',
    )
  })

  it('preserva o status no erro lançado', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(responderCom(409, { detail: 'Já existe.' })),
    )

    await expect(chamarApi('/auth/register')).rejects.toMatchObject({
      status: 409,
    })
  })

  it('avisa quando o servidor está inacessível', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new TypeError('Failed to fetch')),
    )

    await expect(chamarApi('/painel')).rejects.toBeInstanceOf(ErroDaApi)
    await expect(chamarApi('/painel')).rejects.toThrow(
      'Não foi possível falar com o servidor.',
    )
  })
})
