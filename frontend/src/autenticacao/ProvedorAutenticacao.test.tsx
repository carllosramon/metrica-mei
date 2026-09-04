import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  buscarUsuarioAtual,
  cadastrar,
  entrar,
} from '../api/autenticacao'
import { registrarPerdaDeSessao } from '../api/cliente'
import type { Usuario } from '../api/tipos'
import { ProvedorAutenticacao } from './ProvedorAutenticacao'
import { useAutenticacao } from './useAutenticacao'

vi.mock('../api/autenticacao', () => ({
  buscarUsuarioAtual: vi.fn(),
  cadastrar: vi.fn(),
  entrar: vi.fn(),
}))

// O provedor avisa o cliente HTTP do que fazer quando alguma requisição volta
// 401. Aqui a simulação apenas guarda esse aviso para que os testes possam
// dispará-lo. Que o 401 de verdade chegue até ele, e que o 401 do próprio
// login não conte, já está verificado em cliente.test.ts.
vi.mock('../api/cliente', () => ({
  registrarPerdaDeSessao: vi.fn(),
}))

const CHAVE_DO_TOKEN = 'metricamei.token'

const carlos: Usuario = {
  id: 1,
  nome: 'Carlos',
  email: 'carlos@email.com',
  criado_em: '2026-08-01T00:00:00',
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
  vi.mocked(buscarUsuarioAtual).mockResolvedValue(carlos)

  renderizar()

  await waitFor(() => {
    expect(screen.getByTestId('usuario')).toHaveTextContent('Carlos')
  })
}

beforeEach(() => {
  localStorage.clear()
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('ProvedorAutenticacao', () => {
  it('sem token guardado não pergunta nada ao servidor', () => {
    renderizar()

    expect(screen.getByTestId('token')).toHaveTextContent('nenhum')
    expect(screen.getByTestId('verificando')).toHaveTextContent('não')
    expect(buscarUsuarioAtual).not.toHaveBeenCalled()
  })

  it('segue verificando enquanto o servidor não responde', () => {
    localStorage.setItem(CHAVE_DO_TOKEN, 'token-guardado')

    // Sem esse estado a aplicação decidiria que ninguém está autenticado e
    // piscaria a tela de login a cada recarga de página.
    vi.mocked(buscarUsuarioAtual).mockReturnValue(new Promise(() => {}))

    renderizar()

    expect(screen.getByTestId('verificando')).toHaveTextContent('sim')
    expect(screen.getByTestId('usuario')).toHaveTextContent('nenhum')
  })

  it('token guardado válido devolve a sessão sem novo login', async () => {
    localStorage.setItem(CHAVE_DO_TOKEN, 'token-guardado')
    vi.mocked(buscarUsuarioAtual).mockResolvedValue(carlos)

    renderizar()

    await waitFor(() => {
      expect(screen.getByTestId('usuario')).toHaveTextContent('Carlos')
    })

    expect(buscarUsuarioAtual).toHaveBeenCalledWith('token-guardado')
    expect(screen.getByTestId('verificando')).toHaveTextContent('não')
  })

  it('token guardado vencido é descartado sem acusar expiração', async () => {
    localStorage.setItem(CHAVE_DO_TOKEN, 'token-vencido')
    vi.mocked(buscarUsuarioAtual).mockRejectedValue(
      new Error('Não autenticado.'),
    )

    renderizar()

    await waitFor(() => {
      expect(screen.getByTestId('token')).toHaveTextContent('nenhum')
    })

    expect(localStorage.getItem(CHAVE_DO_TOKEN)).toBeNull()
    expect(screen.getByTestId('verificando')).toHaveTextContent('não')

    // Quem chega com um token velho no bolso não viu sessão nenhuma cair na
    // frente dele, então a tela de login não tem o que explicar.
    expect(screen.getByTestId('expirada')).toHaveTextContent('não')
  })

  it('401 durante o uso encerra a sessão e acusa expiração', async () => {
    await comSessaoAberta()

    // O aviso que vale é o do último registro. A limpeza entre um teste e
    // outro desmonta o provedor anterior, e a desmontagem registra null.
    const avisarPerdaDeSessao = vi
      .mocked(registrarPerdaDeSessao)
      .mock.calls.at(-1)?.[0]

    expect(avisarPerdaDeSessao).toBeTypeOf('function')

    act(() => {
      avisarPerdaDeSessao?.()
    })

    expect(screen.getByTestId('expirada')).toHaveTextContent('sim')
    expect(screen.getByTestId('token')).toHaveTextContent('nenhum')
    expect(screen.getByTestId('usuario')).toHaveTextContent('nenhum')
    expect(localStorage.getItem(CHAVE_DO_TOKEN)).toBeNull()
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

    vi.mocked(entrar).mockResolvedValue({
      access_token: 'token-novo',
      token_type: 'bearer',
    })
    vi.mocked(buscarUsuarioAtual).mockResolvedValue(carlos)

    renderizar()

    await usuario.click(screen.getByRole('button', { name: 'Entrar' }))

    await waitFor(() => {
      expect(screen.getByTestId('usuario')).toHaveTextContent('Carlos')
    })

    expect(entrar).toHaveBeenCalledWith('carlos@email.com', 'minhasenha')
    expect(localStorage.getItem(CHAVE_DO_TOKEN)).toBe('token-novo')
  })

  it('criar conta encadeia o login e já começa a sessão', async () => {
    const usuario = userEvent.setup()

    vi.mocked(cadastrar).mockResolvedValue(carlos)
    vi.mocked(entrar).mockResolvedValue({
      access_token: 'token-da-conta-nova',
      token_type: 'bearer',
    })
    vi.mocked(buscarUsuarioAtual).mockResolvedValue(carlos)

    renderizar()

    await usuario.click(screen.getByRole('button', { name: 'Criar conta' }))

    await waitFor(() => {
      expect(screen.getByTestId('usuario')).toHaveTextContent('Carlos')
    })

    // O cadastro não devolve token, então sem o login em seguida o usuário
    // teria de digitar tudo de novo na tela ao lado.
    expect(cadastrar).toHaveBeenCalledWith(
      'Carlos',
      'carlos@email.com',
      'minhasenha',
    )
    expect(entrar).toHaveBeenCalledWith('carlos@email.com', 'minhasenha')
    expect(localStorage.getItem(CHAVE_DO_TOKEN)).toBe('token-da-conta-nova')
  })
})
