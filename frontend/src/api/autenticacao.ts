import { chamarApi } from './cliente'
import type { Token, Usuario } from './tipos'

export function cadastrar(
  nome: string,
  email: string,
  senha: string,
): Promise<Usuario> {
  return chamarApi<Usuario>('/auth/register', {
    metodo: 'POST',
    corpo: { nome, email, senha },
  })
}

export function entrar(
  email: string,
  senha: string,
): Promise<Token> {
  return chamarApi<Token>('/auth/login', {
    metodo: 'POST',
    corpo: { email, senha },
  })
}

export function buscarUsuarioAtual(
  token: string,
): Promise<Usuario> {
  return chamarApi<Usuario>('/auth/me', { token })
}
