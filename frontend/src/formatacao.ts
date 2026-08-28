const FUSO_DO_NEGOCIO = 'America/Sao_Paulo'

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

export function dataDeHoje(): string {
  // O backend usa o calendário de America/Sao_Paulo para decidir se uma
  // data está no futuro. O formulário precisa usar exatamente o mesmo
  // calendário, independentemente do fuso do navegador ou do servidor.
  const partes = new Intl.DateTimeFormat('pt-BR', {
    timeZone: FUSO_DO_NEGOCIO,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date())

  const valores = Object.fromEntries(
    partes.map((parte) => [parte.type, parte.value]),
  ) as Record<string, string>

  return `${valores.year}-${valores.month}-${valores.day}`
}
