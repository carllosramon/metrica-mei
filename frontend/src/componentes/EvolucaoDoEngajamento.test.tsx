import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { Metrica } from '../api/tipos'
import { EvolucaoDoEngajamento } from './EvolucaoDoEngajamento'

function medicao(
  id: number,
  data_referencia: string,
  engajamento: number | null,
): Metrica {
  return {
    id,
    visualizacoes: 100,
    curtidas: 10,
    comentarios: 0,
    compartilhamentos: 0,
    alcance: engajamento === null ? 0 : 100,
    data_referencia,
    criado_em: `${data_referencia}T10:00:00`,
    engajamento,
  }
}

// A API devolve da medição mais recente para a mais antiga.
const MAIS_RECENTE_PRIMEIRO = [
  medicao(3, '2026-08-22', 30),
  medicao(2, '2026-08-21', 20),
  medicao(1, '2026-08-20', 10),
]

describe('EvolucaoDoEngajamento', () => {
  it('desenha uma linha única quando todas as medições têm índice', () => {
    const { container } = render(
      <EvolucaoDoEngajamento metricas={MAIS_RECENTE_PRIMEIRO} />,
    )

    expect(container.querySelectorAll('polyline')).toHaveLength(1)
    expect(container.querySelectorAll('circle')).toHaveLength(3)
  })

  it('interrompe a linha na medição sem alcance', () => {
    const comBuraco = [
      medicao(4, '2026-08-23', 40),
      medicao(3, '2026-08-22', null),
      medicao(2, '2026-08-21', 20),
      medicao(1, '2026-08-20', 10),
    ]

    const { container } = render(
      <EvolucaoDoEngajamento metricas={comBuraco} />,
    )

    // Dois trechos: as duas primeiras medições de um lado do buraco, e a
    // última sozinha do outro — que vira ponto, não linha.
    expect(container.querySelectorAll('polyline')).toHaveLength(1)
    expect(container.querySelectorAll('circle')).toHaveLength(3)
  })

  it('separa em dois trechos quando há pontos dos dois lados do buraco', () => {
    const comBuraco = [
      medicao(5, '2026-08-24', 50),
      medicao(4, '2026-08-23', 40),
      medicao(3, '2026-08-22', null),
      medicao(2, '2026-08-21', 20),
      medicao(1, '2026-08-20', 10),
    ]

    const { container } = render(
      <EvolucaoDoEngajamento metricas={comBuraco} />,
    )

    expect(container.querySelectorAll('polyline')).toHaveLength(2)
    expect(container.querySelectorAll('circle')).toHaveLength(4)
  })

  it('descreve o gráfico para quem não o enxerga', () => {
    render(<EvolucaoDoEngajamento metricas={MAIS_RECENTE_PRIMEIRO} />)

    expect(
      screen.getByRole('img', {
        name: 'Evolução do engajamento em 3 medições, de 10,00% a 30,00%.',
      }),
    ).toBeInTheDocument()
  })

  it('explica a ausência quando nenhuma medição tem índice', () => {
    const { container } = render(
      <EvolucaoDoEngajamento
        metricas={[medicao(1, '2026-08-20', null)]}
      />,
    )

    expect(
      screen.getByText(/Nenhuma medição tem engajamento calculável/),
    ).toBeInTheDocument()
    expect(container.querySelector('svg')).toBeNull()
  })
})
