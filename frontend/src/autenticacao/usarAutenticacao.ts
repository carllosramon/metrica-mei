import { useContext } from 'react'

import { ContextoAutenticacao } from './contexto'
import type { ValorDaAutenticacao } from './contexto'

export function usarAutenticacao(): ValorDaAutenticacao {
  const valor = useContext(ContextoAutenticacao)

  if (valor === null) {
    throw new Error(
      'usarAutenticacao precisa estar dentro de ProvedorAutenticacao.',
    )
  }

  return valor
}
