import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ErroDaApi } from '../api/cliente'
import { ContextoAutenticacao } from '../autenticacao/contexto'
import type { ValorDaAutenticacao } from '../autenticacao/contexto'
import { Entrar } from './Entrar'

function autenticacaoCom(
  parcial: Partial<ValorDaAutenticacao>,
): ValorDaAutenticacao {
  return {
    token: null,
    usuario: null,
    verificando: false,
    sessaoExpirada: false,
    criarConta: vi.fn(),
    entrarNaConta: vi.fn(),
    sair: vi.fn(),
    ...parcial,
  }
}

// A rota do painel existe só para provar que o login navegou. O heading
// falso basta, a tela de verdade não interessa aqui.
function renderizar(autenticacao: ValorDaAutenticacao) {
  return render(
    <ContextoAutenticacao.Provider value={autenticacao}>
      <MemoryRouter initialEntries={['/entrar']}>
        <Routes>
          <Route path="/entrar" element={<Entrar />} />
          <Route path="/painel" element={<h1>Painel falso</h1>} />
        </Routes>
      </MemoryRouter>
    </ContextoAutenticacao.Provider>,
  )
}

async function preencherEEnviar() {
  const usuario = userEvent.setup()

  await usuario.type(screen.getByLabelText('E-mail'), 'joao@email.com')
  await usuario.type(screen.getByLabelText('Senha'), 'minhasenha')
  await usuario.click(screen.getByRole('button', { name: 'Entrar' }))

  return usuario
}

afterEach(() => {
  vi.clearAllMocks()
})

describe('Entrar', () => {
  it('entra com as credenciais digitadas e vai para o painel', async () => {
    const entrarNaConta = vi.fn().mockResolvedValue(undefined)

    renderizar(autenticacaoCom({ entrarNaConta }))

    await preencherEEnviar()

    expect(entrarNaConta).toHaveBeenCalledWith(
      'joao@email.com',
      'minhasenha',
    )
    expect(
      await screen.findByRole('heading', { name: 'Painel falso' }),
    ).toBeInTheDocument()
  })

  it('mostra a mensagem do backend quando a credencial é recusada', async () => {
    const entrarNaConta = vi
      .fn()
      .mockRejectedValue(new ErroDaApi(401, 'E-mail ou senha inválidos.'))

    renderizar(autenticacaoCom({ entrarNaConta }))

    await preencherEEnviar()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'E-mail ou senha inválidos.',
    )

    // A tela continua utilizável para a segunda tentativa.
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeEnabled()
  })

  it('cai na mensagem genérica quando a falha não veio da api', async () => {
    const entrarNaConta = vi
      .fn()
      .mockRejectedValue(new Error('estourou'))

    renderizar(autenticacaoCom({ entrarNaConta }))

    await preencherEEnviar()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Não foi possível entrar.',
    )
  })

  it('avisa quem foi devolvido por sessão vencida', () => {
    renderizar(autenticacaoCom({ sessaoExpirada: true }))

    expect(screen.getByRole('status')).toHaveTextContent(
      'Sua sessão expirou. Entre novamente para continuar.',
    )
  })

  it('o erro da tentativa toma o lugar do aviso de sessão', async () => {
    const entrarNaConta = vi
      .fn()
      .mockRejectedValue(new ErroDaApi(401, 'E-mail ou senha inválidos.'))

    renderizar(
      autenticacaoCom({ sessaoExpirada: true, entrarNaConta }),
    )

    await preencherEEnviar()

    // Dois cartazes ao mesmo tempo disputariam a atenção, e o erro da
    // senha é o que o usuário precisa ler agora.
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
