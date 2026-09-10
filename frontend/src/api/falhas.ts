import { ErroDaApi } from './cliente'

// A mensagem da API é a que explica o que houve. Falha sem status, como
// rede fora do ar, fica com o texto que a tela escolher.
export function mensagemDe(falha: unknown, alternativa: string): string {
  return falha instanceof ErroDaApi ? falha.message : alternativa
}
