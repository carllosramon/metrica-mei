// Campo em branco significa remover a URL, e o backend recusa texto vazio.
// Null é como ele entende a remoção.
export function urlOuNulo(endereco: string): string | null {
  return endereco.trim() === '' ? null : endereco
}

const SO_DIGITOS = /^\d+$/

// Milhar no padrão brasileiro, em grupos de exatamente três dígitos.
// A exigência dos três é o que separa "12.000" de "1.5": sem ela, tirar
// os pontos de qualquer coisa transformaria um decimal em inteiro.
const MILHAR_BRASILEIRO = /^\d{1,3}(\.\d{3})+$/

// O campo type="number" considera "12.000" um número válido, e Number()
// lê isso como 12. Quem copiava doze mil do Instagram gravava doze, sem
// aviso nenhum, e o alcance errado contaminava o painel inteiro.
export function inteiroDigitado(valor: string): number | null {
  const limpo = valor.trim()

  if (SO_DIGITOS.test(limpo)) {
    return Number(limpo)
  }

  if (MILHAR_BRASILEIRO.test(limpo)) {
    return Number(limpo.replaceAll('.', ''))
  }

  return null
}
