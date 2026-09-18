import { afterEach, describe, expect, it, vi } from 'vitest'

import { responderCom } from '../testes/respostaHttp'
import { ErroDaApi, chamarApi, registrarPerdaDeSessao } from './cliente'

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

  it('desiste quando a resposta demora além do prazo', async () => {
    const estourou = new Error('The operation was aborted due to timeout')
    estourou.name = 'TimeoutError'

    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(estourou))

    // Sem prazo, a promessa fica pendente para sempre e todo botão da
    // tela continua desabilitado esperando por ela.
    await expect(chamarApi('/painel')).rejects.toThrow(
      'O servidor demorou demais para responder.',
    )
  })

  it('manda um prazo junto de toda requisição', async () => {
    const requisicao = vi.fn().mockResolvedValue(responderCom(200, {}))

    vi.stubGlobal('fetch', requisicao)

    await chamarApi('/painel')

    expect(requisicao.mock.calls[0][1].signal).toBeInstanceOf(AbortSignal)
  })

  it('prazo estourado no meio do corpo não vira erro de endereço', async () => {
    const estourou = new Error('The operation was aborted due to timeout')
    estourou.name = 'TimeoutError'

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => {
          throw estourou
        },
      } as unknown as Response),
    )

    // O prazo do AbortSignal também corta o corpo. Como o fetch já
    // resolveu, quem rejeita é o json(), e isso saía como "confira o
    // endereço da API" para quem só estava numa rede ruim.
    await expect(chamarApi('/painel')).rejects.toThrow(
      'O servidor demorou demais para responder.',
    )
  })

  it('rede caída no meio do corpo é falha de rede', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => {
          throw new TypeError('network error')
        },
      } as unknown as Response),
    )

    await expect(chamarApi('/painel')).rejects.toThrow(
      'Não foi possível falar com o servidor.',
    )
  })

  it('devolve vazio no 204 sem tentar ler o corpo', async () => {
    const corpo = vi.fn()

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 204,
        json: corpo,
      } as unknown as Response),
    )

    // É o que toda exclusão devolve. Sem o curto-circuito, o json()
    // estoura no corpo vazio e a tela acusa endereço errado ao excluir.
    await expect(
      chamarApi('/conteudos/7', { metodo: 'DELETE' }),
    ).resolves.toBeUndefined()

    expect(corpo).not.toHaveBeenCalled()
  })

  it('tem mensagem de último recurso quando o erro não traz detail', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(responderCom(502, { erro: 'bad gateway' })),
    )

    // Um proxy no caminho responde sem o formato do FastAPI. Sem esta
    // saída, a tela mostraria "undefined" ao usuário.
    await expect(chamarApi('/painel')).rejects.toThrow(
      'Erro inesperado do servidor (502).',
    )
  })

  it('recusa um 200 que não traz JSON', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => {
          throw new SyntaxError('Unexpected token <')
        },
      } as unknown as Response),
    )

    // É o index.html chegando no lugar da API. Virando nulo em silêncio,
    // a tela ficava em "Carregando…" sem nunca sair de lá.
    await expect(chamarApi('/conteudos')).rejects.toThrow(
      /não é a resposta esperada/,
    )
  })
})

describe('perda de sessão', () => {
  afterEach(() => {
    registrarPerdaDeSessao(null)
  })

  it('avisa quando uma rota autenticada devolve 401', async () => {
    const aoPerder = vi.fn()
    registrarPerdaDeSessao(aoPerder)

    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(responderCom(401, { detail: 'Não autenticado.' })),
    )

    await expect(
      chamarApi('/painel', { token: 'token-da-requisicao' }),
    ).rejects.toThrow()

    // O aviso leva o token usado, para quem controla a sessão saber se o
    // 401 é da sessão atual ou de uma requisição atrasada de antes.
    expect(aoPerder).toHaveBeenCalledTimes(1)
    expect(aoPerder).toHaveBeenCalledWith('token-da-requisicao')
  })

  it('não derruba a sessão quando o 401 vem do login', async () => {
    const aoPerder = vi.fn()
    registrarPerdaDeSessao(aoPerder)

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        responderCom(401, { detail: 'E-mail ou senha inválidos.' }),
      ),
    )

    await expect(chamarApi('/auth/login')).rejects.toThrow()

    expect(aoPerder).not.toHaveBeenCalled()
  })

  it('não confunde outros erros com sessão perdida', async () => {
    const aoPerder = vi.fn()
    registrarPerdaDeSessao(aoPerder)

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(responderCom(404, { detail: 'Sumiu.' })),
    )

    await expect(chamarApi('/conteudos/9')).rejects.toThrow()

    expect(aoPerder).not.toHaveBeenCalled()
  })
})
