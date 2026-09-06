import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ErroDaApi } from '../api/cliente'
import { ContextoAutenticacao } from '../autenticacao/contexto'
import type { ValorDaAutenticacao } from '../autenticacao/contexto'
import { Cadastrar } from './Cadastrar'

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

function renderizar(autenticacao: ValorDaAutenticacao) {
  return render(
    <ContextoAutenticacao.Provider value={autenticacao}>
      <MemoryRouter initialEntries={['/cadastrar']}>
        <Routes>
          <Route path="/cadastrar" element={<Cadastrar />} />
          <Route path="/painel" element={<h1>Painel falso</h1>} />
        </Routes>
      </MemoryRouter>
    </ContextoAutenticacao.Provider>,
  )
}

async function preencherEEnviar() {
  const usuario = userEvent.setup()

  await usuario.type(screen.getByLabelText('Nome'), 'Joao')
  await usuario.type(screen.getByLabelText('E-mail'), 'joao@email.com')
  await usuario.type(screen.getByLabelText('Senha'), 'minhasenha')
  await usuario.click(screen.getByRole('button', { name: 'Criar conta' }))
}

afterEach(() => {
  vi.clearAllMocks()
})

describe('Cadastrar', () => {
  it('cria a conta e segue direto para o painel', async () => {
    const criarConta = vi.fn().mockResolvedValue(undefined)

    renderizar(autenticacaoCom({ criarConta }))

    await preencherEEnviar()

    expect(criarConta).toHaveBeenCalledWith(
      'Joao',
      'joao@email.com',
      'minhasenha',
    )
    expect(
      await screen.findByRole('heading', { name: 'Painel falso' }),
    ).toBeInTheDocument()
  })

  it('mostra a recusa do backend, como e-mail já usado', async () => {
    const criarConta = vi
      .fn()
      .mockRejectedValue(new ErroDaApi(409, 'E-mail já cadastrado.'))

    renderizar(autenticacaoCom({ criarConta }))

    await preencherEEnviar()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'E-mail já cadastrado.',
    )
    expect(
      screen.getByRole('button', { name: 'Criar conta' }),
    ).toBeEnabled()
  })

  it('cai na mensagem genérica quando a falha não veio da api', async () => {
    const criarConta = vi.fn().mockRejectedValue(new Error('estourou'))

    renderizar(autenticacaoCom({ criarConta }))

    await preencherEEnviar()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Não foi possível criar a conta.',
    )
  })

  it('exige senha com o mínimo que o backend aceita', () => {
    renderizar(autenticacaoCom({}))

    // O aviso local poupa uma ida ao servidor para descobrir a regra.
    expect(screen.getByLabelText('Senha')).toHaveAttribute(
      'minlength',
      '8',
    )
  })
})
