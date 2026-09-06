import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { Metrica } from '../../api/tipos'
import { TabelaDeMedicoes } from './TabelaDeMedicoes'

const medicao: Metrica = {
  id: 3,
  visualizacoes: 3200,
  curtidas: 110,
  comentarios: 14,
  compartilhamentos: 22,
  alcance: 1450,
  data_referencia: '2026-09-02',
  criado_em: '2026-09-02T10:00:00',
  engajamento: 10.07,
}

function renderizar(
  metricaConfirmada: number | null = null,
  aoEditar = vi.fn(),
  aoExcluir = vi.fn(),
) {
  render(
    <TabelaDeMedicoes
      metricas={[medicao]}
      metricaConfirmada={metricaConfirmada}
      aoEditar={aoEditar}
      aoExcluir={aoExcluir}
    />,
  )

  return { aoEditar, aoExcluir }
}

afterEach(() => {
  vi.clearAllMocks()
})

describe('TabelaDeMedicoes', () => {
  it('mostra a medição formatada para leitura', () => {
    renderizar()

    expect(
      screen.getByRole('cell', { name: '02/09/2026' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('cell', { name: '3.200' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('cell', { name: '10,07%' }),
    ).toBeInTheDocument()
  })

  it('editar entrega a medição inteira para a página', async () => {
    const usuario = userEvent.setup()

    const { aoEditar } = renderizar()

    await usuario.click(screen.getByRole('button', { name: 'Editar' }))

    expect(aoEditar).toHaveBeenCalledWith(medicao)
  })

  it('o primeiro clique em excluir só pede confirmação', async () => {
    const usuario = userEvent.setup()

    const { aoExcluir } = renderizar()

    await usuario.click(screen.getByRole('button', { name: 'Excluir' }))

    // Quem decide se a linha fica armada é a página. A tabela só avisa
    // qual id foi clicado.
    expect(aoExcluir).toHaveBeenCalledWith(3)
  })

  it('a linha armada troca o rótulo para confirmar', () => {
    renderizar(3)

    expect(
      screen.getByRole('button', { name: 'Confirmar' }),
    ).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Excluir' }),
    ).not.toBeInTheDocument()
  })
})
