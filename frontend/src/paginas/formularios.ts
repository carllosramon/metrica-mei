// Campo em branco significa remover a URL, e o backend recusa texto vazio.
// Null é como ele entende a remoção.
export function urlOuNulo(endereco: string): string | null {
  return endereco.trim() === '' ? null : endereco
}
