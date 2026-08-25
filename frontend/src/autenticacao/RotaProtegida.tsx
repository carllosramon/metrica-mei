import { Navigate } from 'react-router-dom'
import type { ReactNode } from 'react'

import { usarAutenticacao } from './usarAutenticacao'

type Props = {
  children: ReactNode
}

export function RotaProtegida({ children }: Props) {
  const { token, verificando } = usarAutenticacao()

  // Redirecionar durante a verificação mandaria para o login todo usuário
  // que recarregasse a página com sessão válida.
  if (verificando) {
    return <p>Carregando…</p>
  }

  if (token === null) {
    return <Navigate to="/entrar" replace />
  }

  return <>{children}</>
}
