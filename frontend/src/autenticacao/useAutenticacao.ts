import { useContext } from 'react'

import { ContextoAutenticacao } from './contexto'
import type { ValorDaAutenticacao } from './contexto'

export function useAutenticacao(): ValorDaAutenticacao {
  const valor = useContext(ContextoAutenticacao)

  if (valor === null) {
    throw new Error(
      'useAutenticacao precisa estar dentro de ProvedorAutenticacao.',
    )
  }

  return valor
}
