import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { FormEvent } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { dataDeHoje } from '../../formatacao'
import { FormularioDaMedicao } from './FormularioDaMedicao'
import type { DadosDaMedicao } from './FormularioDaMedicao'

const vazio: DadosDaMedicao = {
  visualizacoes: '',
  curtidas: '',
  comentarios: '',
  compartilhamentos: '',
  alcance: '',
  data_referencia: '',
}

// Campo obrigatório vazio barra o envio na validação do navegador, antes
// do evento chegar na página. O teste de envio precisa do formulário
// preenchido.
const preenchido: DadosDaMedicao = {
  visualizacoes: '3200',
  curtidas: '110',
  comentarios: '14',
  compartilhamentos: '22',
  alcance: '1450',
  data_referencia: '2026-09-02',
}

function renderizar(opcoes: {
  dados?: DadosDaMedicao
  enviando?: boolean
}) {
  const aoAlterar =
    vi.fn<(campo: keyof DadosDaMedicao, valor: string) => void>()
  const aoEnviar = vi.fn<(evento: FormEvent) => void>()
  const aoCancelar = vi.fn<() => void>()

  render(
    <FormularioDaMedicao
      dados={opcoes.dados ?? vazio}
      enviando={opcoes.enviando ?? false}
      dataDaPublicacao="2026-08-21"
      aoAlterar={aoAlterar}
      aoEnviar={aoEnviar}
      aoCancelar={aoCancelar}
    />,
  )

  return { aoAlterar, aoEnviar, aoCancelar }
}

afterEach(() => {
  vi.clearAllMocks()
})

describe('FormularioDaMedicao', () => {
  it('prende a data de referência entre a publicação e hoje', () => {
    renderizar({})

    const campo = screen.getByLabelText('Data de referência')

    // Antes da publicação o conteúdo não existia, depois de hoje ainda
    // não aconteceu. O navegador barra as duas pontas.
    expect(campo).toHaveAttribute('min', '2026-08-21')
    expect(campo).toHaveAttribute('max', dataDeHoje())
  })

  it('cada campo reporta a alteração com a própria chave', async () => {
    const usuario = userEvent.setup()

    // Um valor distinto por campo desmascara chave trocada entre dois
    // campos, que com valores iguais passaria sem ninguém notar.
    const { aoAlterar } = renderizar({})

    await usuario.type(screen.getByLabelText('Visualizações'), '1')
    await usuario.type(screen.getByLabelText('Alcance'), '2')
    await usuario.type(screen.getByLabelText('Curtidas'), '3')
    await usuario.type(screen.getByLabelText('Comentários'), '4')
    await usuario.type(screen.getByLabelText('Compartilhamentos'), '5')

    // Campo de data não aceita digitação letra a letra no jsdom, o valor
    // entra pelo evento de mudança direto.
    fireEvent.change(screen.getByLabelText('Data de referência'), {
      target: { value: '2026-09-02' },
    })

    expect(aoAlterar).toHaveBeenCalledWith('visualizacoes', '1')
    expect(aoAlterar).toHaveBeenCalledWith('alcance', '2')
    expect(aoAlterar).toHaveBeenCalledWith('curtidas', '3')
    expect(aoAlterar).toHaveBeenCalledWith('comentarios', '4')
    expect(aoAlterar).toHaveBeenCalledWith('compartilhamentos', '5')
    expect(aoAlterar).toHaveBeenCalledWith(
      'data_referencia',
      '2026-09-02',
    )
  })

  it('entrega o envio para a página', async () => {
    const usuario = userEvent.setup()

    const { aoEnviar, aoCancelar } = renderizar({ dados: preenchido })

    await usuario.click(
      screen.getByRole('button', { name: 'Salvar medição' }),
    )

    expect(aoEnviar).toHaveBeenCalledOnce()
    expect(aoCancelar).not.toHaveBeenCalled()
  })

  it('cancelar desiste sem enviar nada', async () => {
    const usuario = userEvent.setup()

    const { aoEnviar, aoCancelar } = renderizar({})

    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(aoCancelar).toHaveBeenCalledOnce()
    expect(aoEnviar).not.toHaveBeenCalled()
  })

  it('trava o botão enquanto a gravação está no ar', () => {
    renderizar({ enviando: true })

    // O segundo clique criaria medição duplicada na mesma data.
    expect(
      screen.getByRole('button', { name: 'Salvando…' }),
    ).toBeDisabled()
  })
})
