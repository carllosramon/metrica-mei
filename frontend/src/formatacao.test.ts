import { describe, expect, it, vi } from 'vitest'

import {
  dataDeHoje,
  formatarData,
  formatarNumero,
  formatarPercentual,
} from './formatacao'

describe('formatarNumero', () => {
  it('separa milhares no padrão brasileiro', () => {
    expect(formatarNumero(48200)).toBe('48.200')
  })
})

describe('formatarPercentual', () => {
  it('mostra duas casas decimais com vírgula', () => {
    expect(formatarPercentual(10.07)).toBe('10,07%')
  })

  it('completa as casas decimais de um valor redondo', () => {
    expect(formatarPercentual(8)).toBe('8,00%')
  })

  it('mostra traço quando o índice não é calculável', () => {
    expect(formatarPercentual(null)).toBe('—')
  })

  it('distingue índice ausente de engajamento zero', () => {
    expect(formatarPercentual(0)).toBe('0,00%')
    expect(formatarPercentual(0)).not.toBe(formatarPercentual(null))
  })
})

describe('formatarData', () => {
  it('converte a data ISO para o formato brasileiro', () => {
    expect(formatarData('2026-08-25')).toBe('25/08/2026')
  })

  it('não volta um dia por causa do fuso horário', () => {
    // new Date('2026-01-01') vira 31/12/2025 no horário de Brasília.
    expect(formatarData('2026-01-01')).toBe('01/01/2026')
  })
})

describe('dataDeHoje', () => {
  it('usa o calendário local, e não o UTC', () => {
    // Fim da tarde no Brasil já é o dia seguinte em UTC, e o formulário
    // passaria a aceitar data futura se usasse toISOString.
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-08-25T23:30:00-03:00'))

    expect(dataDeHoje()).toBe('2026-08-25')

    vi.useRealTimers()
  })
})
