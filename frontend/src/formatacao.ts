export function formatarNumero(valor: number): string {
  return valor.toLocaleString('pt-BR')
}

export function formatarPercentual(valor: number | null): string {
  // Nulo é ausência de índice calculável, não zero. O traço comunica isso
  // sem inventar um desempenho que o dado não sustenta.
  if (valor === null) {
    return '—'
  }

  return `${valor.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`
}

export function formatarData(isoDaData: string): string {
  // new Date('2026-08-25') é interpretado como meia-noite UTC, o que no
  // fuso do Brasil volta um dia. Separar os campos evita a data errada.
  const [ano, mes, dia] = isoDaData.split('-')

  return `${dia}/${mes}/${ano}`
}
