import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { BarreiraDeErro } from './BarreiraDeErro'

function Quebrada(): never {
  throw new Error('localStorage bloqueado')
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('BarreiraDeErro', () => {
  it('deixa passar o que renderiza sem erro', () => {
    render(
      <BarreiraDeErro>
        <p>Painel</p>
      </BarreiraDeErro>,
    )

    expect(screen.getByText('Painel')).toBeInTheDocument()
  })

  it('explica a falha em vez de deixar a tela em branco', () => {
    // O React escreve o erro no console mesmo capturado, e o ruído
    // atrapalha a leitura da saída dos testes.
    vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <BarreiraDeErro>
        <Quebrada />
      </BarreiraDeErro>,
    )

    expect(
      screen.getByRole('heading', { name: /Algo deu errado nesta tela/ }),
    ).toBeInTheDocument()

    // Quem vai relatar o problema precisa da mensagem técnica; quem só
    // quer voltar a usar o sistema não precisa vê-la aberta.
    expect(screen.getByText('localStorage bloqueado')).toBeInTheDocument()

    expect(
      screen.getByRole('button', { name: 'Recarregar a página' }),
    ).toBeInTheDocument()
  })
})
