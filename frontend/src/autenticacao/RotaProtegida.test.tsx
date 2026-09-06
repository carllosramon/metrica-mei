import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { ContextoAutenticacao } from './contexto'
import type { ValorDaAutenticacao } from './contexto'
import { RotaProtegida } from './RotaProtegida'

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
      <MemoryRouter initialEntries={['/painel']}>
        <Routes>
          <Route
            path="/painel"
            element={
              <RotaProtegida>
                <h1>Conteúdo protegido</h1>
              </RotaProtegida>
            }
          />
          <Route path="/entrar" element={<h1>Login falso</h1>} />
        </Routes>
      </MemoryRouter>
    </ContextoAutenticacao.Provider>,
  )
}

describe('RotaProtegida', () => {
  it('mostra o conteúdo para quem tem sessão', () => {
    renderizar(autenticacaoCom({ token: 'token-valido' }))

    expect(
      screen.getByRole('heading', { name: 'Conteúdo protegido' }),
    ).toBeInTheDocument()
  })

  it('devolve para o login quem não tem sessão', () => {
    renderizar(autenticacaoCom({ token: null }))

    expect(
      screen.getByRole('heading', { name: 'Login falso' }),
    ).toBeInTheDocument()
  })

  it('segura a decisão enquanto o token guardado é validado', () => {
    renderizar(
      autenticacaoCom({ token: 'token-guardado', verificando: true }),
    )

    // Redirecionar agora mandaria para o login todo usuário que
    // recarregasse a página com sessão válida.
    expect(screen.getByText('Carregando…')).toBeInTheDocument()
    expect(
      screen.queryByRole('heading', { name: 'Login falso' }),
    ).not.toBeInTheDocument()
  })
})
