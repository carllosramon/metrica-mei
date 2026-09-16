import { describe, expect, it } from 'vitest'

import { inteiroDigitado, urlOuNulo } from './formularios'

describe('inteiroDigitado', () => {
  it.each([
    ['1450', 1450],
    ['0', 0],
    ['  42  ', 42],
  ])('%s é medida direta', (digitado, esperado) => {
    expect(inteiroDigitado(digitado)).toBe(esperado)
  })

  it.each([
    ['1.000', 1000],
    ['12.000', 12000],
    ['12.345', 12345],
    ['1.234.567', 1234567],
  ])('%s é milhar brasileiro', (digitado, esperado) => {
    // É assim que o Instagram mostra o número, e é assim que o usuário
    // copia. Antes disso, "12.000" virava 12.
    expect(inteiroDigitado(digitado)).toBe(esperado)
  })

  it.each(['1.5', '12.34', '1,5', '12,000', '1e3', '-1', '', '   ', 'abc'])(
    '%s não é medida válida',
    (digitado) => {
      // Os grupos de três dígitos são o que permite recusar o decimal
      // sem depender da validação de passo do navegador.
      expect(inteiroDigitado(digitado)).toBeNull()
    },
  )
})

describe('urlOuNulo', () => {
  it('campo em branco significa remover a URL', () => {
    expect(urlOuNulo('   ')).toBeNull()
  })

  it('endereço preenchido segue como está', () => {
    expect(urlOuNulo('https://instagram.com/p/abc')).toBe(
      'https://instagram.com/p/abc',
    )
  })
})
