export type Adiado<T> = {
  promessa: Promise<T>
  resolver: (valor: T) => void
}

// Uma promessa que o teste resolve quando quiser, para reproduzir resposta
// que chega fora de ordem.
export function adiar<T>(): Adiado<T> {
  let resolver: (valor: T) => void = () => {}

  const promessa = new Promise<T>((cumprir) => {
    resolver = cumprir
  })

  return { promessa, resolver }
}
