import { fireEvent, render, screen } from '@testing-library/react'
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

  it('cada campo reporta a alteração com a própria chave', async () => {
    const usuario = userEvent.setup()

    // O formulário é controlado de fora, o valor só muda se o dono do
    // estado aplicar. Um valor distinto por campo desmascara chave
    // trocada entre dois campos, que com valores iguais passaria.
    const { aoAlterar } = renderizar(vazio)

    await usuario.type(screen.getByLabelText('Título'), 'T')
    await usuario.type(screen.getByLabelText('Plataforma'), 'P')
    await usuario.type(screen.getByLabelText('Tipo'), 'R')
    await usuario.type(screen.getByLabelText('URL da publicação'), 'h')

    // Campo de data não aceita digitação letra a letra no jsdom, o valor
    // entra pelo evento de mudança direto.
    fireEvent.change(screen.getByLabelText('Data de publicação'), {
      target: { value: '2026-08-21' },
    })

    expect(aoAlterar).toHaveBeenCalledWith('titulo', 'T')
    expect(aoAlterar).toHaveBeenCalledWith('plataforma', 'P')
    expect(aoAlterar).toHaveBeenCalledWith('tipo', 'R')
    expect(aoAlterar).toHaveBeenCalledWith('url_publicacao', 'h')
    expect(aoAlterar).toHaveBeenCalledWith(
      'data_publicacao',
      '2026-08-21',
    )
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
