import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { chamarApi } from '../api/cliente'
import type { Usuario } from '../api/tipos'
import { responderCom } from '../testes/respostaHttp'
import { ProvedorAutenticacao } from './ProvedorAutenticacao'
import { useAutenticacao } from './useAutenticacao'

// Nada aqui é simulado além do fetch. O provedor, o cliente HTTP e os
// módulos de api rodam de verdade, então o 401 que dispara o aviso de
// sessão vencida atravessa o mesmo caminho que atravessa no navegador.

const CHAVE_DO_TOKEN = 'metricamei.token'

const carlos: Usuario = {
  id: 1,
  nome: 'Carlos',
  email: 'carlos@email.com',
  criado_em: '2026-08-01T00:00:00',
}

type Resposta = {
  metodo?: string
  caminho: string
  status?: number
  corpo: unknown
}

// Um servidor de mentira que responde por método e fim do caminho. O que
// não estiver na lista estoura, para o teste não passar por acaso.
function servidorCom(...respostas: Resposta[]) {
  const requisicao = vi.fn(
    async (endereco: string, opcoes?: RequestInit) => {
      const metodo = opcoes?.method ?? 'GET'

      const resposta = respostas.find(
        (candidata) =>
          (candidata.metodo ?? 'GET') === metodo &&
          endereco.endsWith(candidata.caminho),
      )

      if (resposta === undefined) {
        throw new Error(`Sem resposta para ${metodo} ${endereco}`)
      }

      return responderCom(resposta.status ?? 200, resposta.corpo)
    },
  )

  vi.stubGlobal('fetch', requisicao)

  return requisicao
}

// Mostra na tela o que o contexto expõe, que é a única forma de observar o
// provedor de fora sem espiar o estado por dentro.
function Espelho() {
  const {
    token,
    usuario,
    verificando,
    sessaoExpirada,
    criarConta,
    entrarNaConta,
    sair,
  } = useAutenticacao()

  return (
    <div>
      <p data-testid="token">{token ?? 'nenhum'}</p>
      <p data-testid="usuario">{usuario?.nome ?? 'nenhum'}</p>
      <p data-testid="verificando">{verificando ? 'sim' : 'não'}</p>
      <p data-testid="expirada">{sessaoExpirada ? 'sim' : 'não'}</p>

      <button
        onClick={() => {
          void entrarNaConta('carlos@email.com', 'minhasenha')
        }}
      >
        Entrar
      </button>
      <button
        onClick={() => {
          void criarConta('Carlos', 'carlos@email.com', 'minhasenha')
        }}
      >
        Criar conta
      </button>
      <button onClick={sair}>Sair</button>
    </div>
  )
}

function renderizar() {
  return render(
    <ProvedorAutenticacao>
      <Espelho />
    </ProvedorAutenticacao>,
  )
}

async function comSessaoAberta() {
  localStorage.setItem(CHAVE_DO_TOKEN, 'token-guardado')
  servidorCom({ caminho: '/auth/me', corpo: carlos })

  renderizar()

  await waitFor(() => {
    expect(screen.getByTestId('usuario')).toHaveTextContent('Carlos')
  })
}

// Dispara, pelo cliente real, uma requisição que volta 401 com o token
// dado. É assim que a tela descobre que a sessão caiu no meio do uso.
async function requisicaoRecusadaCom(token: string) {
  servidorCom({
    caminho: '/painel',
    status: 401,
    corpo: { detail: 'Não autenticado.' },
  })

  await act(async () => {
    await expect(chamarApi('/painel', { token })).rejects.toThrow()
  })
}

beforeEach(() => {
  localStorage.clear()
})

afterEach(() => {
  vi.unstubAllGlobals()
  // Os testes de armazenamento bloqueado espionam o Storage.prototype, que
  // é compartilhado entre todos os casos do arquivo.
  vi.restoreAllMocks()
})

describe('ProvedorAutenticacao', () => {
  it('sem token guardado não pergunta nada ao servidor', () => {
    const requisicao = servidorCom()

    renderizar()

    expect(screen.getByTestId('token')).toHaveTextContent('nenhum')
    expect(screen.getByTestId('verificando')).toHaveTextContent('não')
    expect(requisicao).not.toHaveBeenCalled()
  })

  it('segue verificando enquanto o servidor não responde', () => {
    localStorage.setItem(CHAVE_DO_TOKEN, 'token-guardado')

    // Sem esse estado a aplicação decidiria que ninguém está autenticado e
    // piscaria a tela de login a cada recarga de página.
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))

    renderizar()

    expect(screen.getByTestId('verificando')).toHaveTextContent('sim')
    expect(screen.getByTestId('usuario')).toHaveTextContent('nenhum')
  })

  it('token guardado válido devolve a sessão sem novo login', async () => {
    localStorage.setItem(CHAVE_DO_TOKEN, 'token-guardado')
    const requisicao = servidorCom({ caminho: '/auth/me', corpo: carlos })

    renderizar()

    await waitFor(() => {
      expect(screen.getByTestId('usuario')).toHaveTextContent('Carlos')
    })

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe('http://localhost:8000/auth/me')
    expect(opcoes?.headers).toMatchObject({
      Authorization: 'Bearer token-guardado',
    })
    expect(screen.getByTestId('verificando')).toHaveTextContent('não')
  })

  it('token guardado vencido é descartado e a tela de login explica', async () => {
    localStorage.setItem(CHAVE_DO_TOKEN, 'token-vencido')
    servidorCom({
      caminho: '/auth/me',
      status: 401,
      corpo: { detail: 'Não autenticado.' },
    })

    renderizar()

    await waitFor(() => {
      expect(screen.getByTestId('token')).toHaveTextContent('nenhum')
    })

    expect(localStorage.getItem(CHAVE_DO_TOKEN)).toBeNull()
    expect(screen.getByTestId('verificando')).toHaveTextContent('não')

    // Quem volta dias depois com o token vencido precisa entrar de novo, e
    // saber o motivo é informação, não ruído.
    expect(screen.getByTestId('expirada')).toHaveTextContent('sim')
  })

  it('falha de rede na verificação não apaga o token', async () => {
    localStorage.setItem(CHAVE_DO_TOKEN, 'token-guardado')
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))),
    )

    renderizar()

    await waitFor(() => {
      expect(screen.getByTestId('verificando')).toHaveTextContent('não')
    })

    // O backend fora do ar por um instante não é prova de que o token
    // venceu. Ele fica para a próxima tentativa.
    expect(localStorage.getItem(CHAVE_DO_TOKEN)).toBe('token-guardado')
    expect(screen.getByTestId('token')).toHaveTextContent('token-guardado')
    expect(screen.getByTestId('expirada')).toHaveTextContent('não')
  })

  it('401 durante o uso encerra a sessão e acusa expiração', async () => {
    await comSessaoAberta()

    await requisicaoRecusadaCom('token-guardado')

    expect(screen.getByTestId('expirada')).toHaveTextContent('sim')
    expect(screen.getByTestId('token')).toHaveTextContent('nenhum')
    expect(screen.getByTestId('usuario')).toHaveTextContent('nenhum')
    expect(localStorage.getItem(CHAVE_DO_TOKEN)).toBeNull()
  })

  it('401 atrasado de um token antigo não derruba a sessão nova', async () => {
    await comSessaoAberta()

    // Uma requisição lenta feita antes de sair e entrar de novo volta 401
    // com o token de antes. A sessão que vale agora não tem nada com isso.
    await requisicaoRecusadaCom('token-antigo')

    expect(screen.getByTestId('expirada')).toHaveTextContent('não')
    expect(screen.getByTestId('token')).toHaveTextContent('token-guardado')
    expect(screen.getByTestId('usuario')).toHaveTextContent('Carlos')
  })

  it('sair encerra a sessão sem acusar expiração', async () => {
    const usuario = userEvent.setup()

    await comSessaoAberta()

    await usuario.click(screen.getByRole('button', { name: 'Sair' }))

    expect(screen.getByTestId('token')).toHaveTextContent('nenhum')
    expect(screen.getByTestId('usuario')).toHaveTextContent('nenhum')

    // Saída deliberada não é sessão vencida, e a tela de login não deve
    // acusar expiração para quem clicou em "Sair".
    expect(screen.getByTestId('expirada')).toHaveTextContent('não')
  })

  it('entrar guarda o token para a próxima abertura', async () => {
    const usuario = userEvent.setup()

    const requisicao = servidorCom(
      {
        metodo: 'POST',
        caminho: '/auth/login',
        corpo: { access_token: 'token-novo', token_type: 'bearer' },
      },
      { caminho: '/auth/me', corpo: carlos },
    )

    renderizar()

    await usuario.click(screen.getByRole('button', { name: 'Entrar' }))

    await waitFor(() => {
      expect(screen.getByTestId('usuario')).toHaveTextContent('Carlos')
    })

    const [, opcoesDoLogin] = requisicao.mock.calls[0]

    expect(JSON.parse(String(opcoesDoLogin?.body))).toEqual({
      email: 'carlos@email.com',
      senha: 'minhasenha',
    })
    expect(localStorage.getItem(CHAVE_DO_TOKEN)).toBe('token-novo')
  })

  it('criar conta encadeia o login e já começa a sessão', async () => {
    const usuario = userEvent.setup()

    const requisicao = servidorCom(
      { metodo: 'POST', caminho: '/auth/register', status: 201, corpo: carlos },
      {
        metodo: 'POST',
        caminho: '/auth/login',
        corpo: { access_token: 'token-da-conta-nova', token_type: 'bearer' },
      },
      { caminho: '/auth/me', corpo: carlos },
    )

    renderizar()

    await usuario.click(screen.getByRole('button', { name: 'Criar conta' }))

    await waitFor(() => {
      expect(screen.getByTestId('usuario')).toHaveTextContent('Carlos')
    })

    // O cadastro não devolve token, então sem o login em seguida o usuário
    // teria de digitar tudo de novo na tela ao lado.
    const caminhos = requisicao.mock.calls.map(([endereco]) =>
      String(endereco).replace('http://localhost:8000', ''),
    )

    expect(caminhos).toEqual(['/auth/register', '/auth/login', '/auth/me'])
    expect(localStorage.getItem(CHAVE_DO_TOKEN)).toBe('token-da-conta-nova')
  })
})

describe('armazenamento bloqueado pelo navegador', () => {
  // Navegador com dados de site bloqueados levanta no acesso, e não
  // devolve nulo. O jsdom nunca levanta, então sem estas substituições o
  // caminho não existe para a suíte.
  it('sair encerra a sessão mesmo sem conseguir apagar o token', async () => {
    const usuario = userEvent.setup()

    localStorage.setItem(CHAVE_DO_TOKEN, 'token-guardado')

    servidorCom({ caminho: '/auth/me', corpo: carlos })

    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
      throw new DOMException('acesso negado', 'SecurityError')
    })

    renderizar()

    await waitFor(() => {
      expect(screen.getByTestId('usuario')).toHaveTextContent('Carlos')
    })

    await usuario.click(screen.getByRole('button', { name: 'Sair' }))

    // Antes a exceção subia pelo clique antes de limpar o estado, e a
    // pessoa continuava logada numa máquina compartilhada achando que
    // havia saído.
    expect(screen.getByTestId('token')).toHaveTextContent('nenhum')
    expect(screen.getByTestId('usuario')).toHaveTextContent('nenhum')
  })

  it('entrar funciona mesmo sem conseguir guardar o token', async () => {
    const usuario = userEvent.setup()

    servidorCom(
      {
        metodo: 'POST',
        caminho: '/auth/login',
        corpo: { access_token: 'token-novo', token_type: 'bearer' },
      },
      { caminho: '/auth/me', corpo: carlos },
    )

    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('cota esgotada', 'QuotaExceededError')
    })

    renderizar()

    await usuario.click(screen.getByRole('button', { name: 'Entrar' }))

    // O login deu 200 e a credencial estava certa. Antes a tela dizia
    // "Não foi possível entrar." e a pessoa ia trocar a senha.
    await waitFor(() => {
      expect(screen.getByTestId('usuario')).toHaveTextContent('Carlos')
    })
  })
})
