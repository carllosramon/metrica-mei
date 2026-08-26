import { createContext } from 'react'

import type { Usuario } from '../api/tipos'

export type ValorDaAutenticacao = {
  token: string | null
  usuario: Usuario | null
  // Enquanto o token guardado não é validado contra o backend não dá para
  // decidir se o usuário está autenticado: sem isso a aplicação piscaria a
  // tela de login a cada recarga de página.
  verificando: boolean
  // Diferencia sessão vencida de quem nunca entrou, para que a tela de login
  // explique por que o usuário foi devolvido para lá.
  sessaoExpirada: boolean
  criarConta: (
    nome: string,
    email: string,
    senha: string,
  ) => Promise<void>
  entrarNaConta: (email: string, senha: string) => Promise<void>
  sair: () => void
}

export const ContextoAutenticacao =
  createContext<ValorDaAutenticacao | null>(null)
