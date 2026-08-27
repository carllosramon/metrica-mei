import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { DesempenhoDaPlataforma } from '../api/tipos'
import { BarrasPorPlataforma } from './BarrasPorPlataforma'

function plataforma(
  nome: string,
  total_alcance: number,
): DesempenhoDaPlataforma {
  return {
    plataforma: nome,
    total_conteudos: 1,
    total_visualizacoes: total_alcance * 2,
    total_curtidas: 10,
    total_comentarios: 0,
    total_compartilhamentos: 0,
    total_alcance,
    engajamento: 1,
  }
}

describe('BarrasPorPlataforma', () => {
  it('desenha uma barra por plataforma, proporcional à maior', () => {
    const { container } = render(
      <BarrasPorPlataforma
        plataformas={[plataforma('Instagram', 1000), plataforma('TikTok', 250)]}
      />,
    )

    const barras = container.querySelectorAll('[class*="barra"]')

    expect(barras).toHaveLength(2)
    expect((barras[0] as HTMLElement).style.width).toBe('100%')
    expect((barras[1] as HTMLElement).style.width).toBe('25%')
  })

  it('não quebra quando todas as plataformas têm alcance zero', () => {
    const { container } = render(
      <BarrasPorPlataforma
        plataformas={[plataforma('Instagram', 0), plataforma('TikTok', 0)]}
      />,
    )

    const barras = container.querySelectorAll('[class*="barra"]')

    // Sem o piso de 1 no divisor isto seria 0/0, e a largura sairia NaN%.
    expect((barras[0] as HTMLElement).style.width).toBe('0%')
  })

  it('mostra o alcance de cada plataforma em números', () => {
    render(
      <BarrasPorPlataforma plataformas={[plataforma('Instagram', 48200)]} />,
    )

    expect(screen.getByText('48.200')).toBeInTheDocument()
  })

  it('descreve o gráfico para quem não o enxerga', () => {
    render(
      <BarrasPorPlataforma
        plataformas={[plataforma('Instagram', 1000), plataforma('TikTok', 250)]}
      />,
    )

    expect(
      screen.getByRole('img', {
        name: 'Alcance por plataforma, em 2 redes, da maior para a menor.',
      }),
    ).toBeInTheDocument()
  })
})
