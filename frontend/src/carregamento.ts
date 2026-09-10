import type { RefObject } from 'react'

// Cada carga reserva um número e recebe uma função que diz se ainda é a
// mais recente. Serve para a carga do efeito e para as disparadas depois
// de salvar ou excluir, que chegavam atrasadas e sobrescreviam a tela com
// dados que já não eram os pedidos.
export function reservarPedido(
  contador: RefObject<number>,
): () => boolean {
  const numero = contador.current + 1

  contador.current = numero

  return () => contador.current === numero
}
