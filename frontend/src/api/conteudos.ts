import { chamarApi } from './cliente'
import type { Conteudo, DadosDoConteudo } from './tipos'

export function listarConteudos(
  token: string,
): Promise<Conteudo[]> {
  return chamarApi<Conteudo[]>('/conteudos', { token })
}

export function buscarConteudo(
  token: string,
  conteudoId: number,
): Promise<Conteudo> {
  return chamarApi<Conteudo>(`/conteudos/${conteudoId}`, { token })
}

export function criarConteudo(
  token: string,
  dados: DadosDoConteudo,
): Promise<Conteudo> {
  return chamarApi<Conteudo>('/conteudos', {
    metodo: 'POST',
    corpo: dados,
    token,
  })
}

export function atualizarConteudo(
  token: string,
  conteudoId: number,
  dados: DadosDoConteudo,
): Promise<Conteudo> {
  return chamarApi<Conteudo>(`/conteudos/${conteudoId}`, {
    metodo: 'PATCH',
    corpo: dados,
    token,
  })
}

export function excluirConteudo(
  token: string,
  conteudoId: number,
): Promise<void> {
  return chamarApi<void>(`/conteudos/${conteudoId}`, {
    metodo: 'DELETE',
    token,
  })
}
