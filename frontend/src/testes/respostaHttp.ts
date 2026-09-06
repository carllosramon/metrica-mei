import { vi } from 'vitest'

// Resposta mínima que o chamarApi consome. Cada teste que simula o fetch
// precisava montar isso por conta própria, e a cópia já tinha começado.
export function responderCom(status: number, corpo: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => corpo,
  } as Response
}

// Troca o fetch global por uma simulação que responde 200 com o corpo dado
// e devolve o espião, para o teste inspecionar endereço, método e
// cabeçalhos. Desfazer fica por conta do vi.unstubAllGlobals de cada
// arquivo.
export function simularApi(corpo: unknown = {}) {
  const requisicao = vi.fn().mockResolvedValue(responderCom(200, corpo))

  vi.stubGlobal('fetch', requisicao)

  return requisicao
}
