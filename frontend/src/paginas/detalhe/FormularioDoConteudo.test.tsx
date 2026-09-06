import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { dataDeHoje } from '../../formatacao'
import { FormularioDoConteudo } from './FormularioDoConteudo'
import type { DadosEditaveis } from './FormularioDoConteudo'

const preenchido: DadosEditaveis = {
  titulo: 'Reels sobre preço',
  plataforma: 'Instagram',
  tipo: 'Reels',
  data_publicacao: '2026-08-21',
  url_publicacao: 'https://instagram.com/p/abc',
}

const vazio: DadosEditaveis = {
  titulo: '',
  plataforma: '',
  tipo: '',
  data_publicacao: '',
  url_publicacao: '',
}

function renderizar(
  dados: DadosEditaveis,
  aoAlterar = vi.fn(),
  aoEnviar = vi.fn(),
) {
  render(
    <FormularioDoConteudo
      dados={dados}
      enviando={false}
      aoAlterar={aoAlterar}
      aoEnviar={aoEnviar}
    />,
  )

  return { aoAlterar, aoEnviar }
}

afterEach(() => {
  vi.clearAllMocks()
})

describe('FormularioDoConteudo', () => {
  it('mostra os dados do conteúdo nos campos', () => {
    renderizar(preenchido)

    expect(screen.getByLabelText('Título')).toHaveValue(
      'Reels sobre preço',
    )
    expect(screen.getByLabelText('Plataforma')).toHaveValue('Instagram')
    expect(screen.getByLabelText('Data de publicação')).toHaveValue(
      '2026-08-21',
    )
    expect(screen.getByLabelText('URL da publicação')).toHaveValue(
      'https://instagram.com/p/abc',
    )
  })

  it('reporta cada alteração para quem controla o estado', async () => {
    const usuario = userEvent.setup()

    // O formulário é controlado de fora, o valor só muda se o dono do
    // estado aplicar. Digitar uma letra basta para provar o repasse.
    const { aoAlterar } = renderizar(vazio)

    await usuario.type(screen.getByLabelText('Título'), 'R')

    expect(aoAlterar).toHaveBeenCalledWith('titulo', 'R')
  })

  it('entrega o envio para a página', async () => {
    const usuario = userEvent.setup()

    const { aoEnviar } = renderizar(preenchido)

    await usuario.click(
      screen.getByRole('button', { name: 'Salvar alterações' }),
    )

    expect(aoEnviar).toHaveBeenCalledOnce()
  })

  it('não aceita publicação no futuro', () => {
    renderizar(preenchido)

    // Não se cadastra desempenho de conteúdo que ainda não foi ao ar.
    expect(screen.getByLabelText('Data de publicação')).toHaveAttribute(
      'max',
      dataDeHoje(),
    )
  })
})
