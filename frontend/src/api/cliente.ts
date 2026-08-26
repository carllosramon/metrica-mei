const URL_BASE =
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const SEM_RESPOSTA_HTTP = 0

// Nestes caminhos o 401 significa credencial errada, e não sessão perdida.
// Derrubar a sessão aqui apagaria o token de quem só errou a senha na tela
// de login estando autenticado em outra aba.
const CAMINHOS_SEM_SESSAO = ['/auth/login', '/auth/register']

let aoPerderSessao: (() => void) | null = null

export function registrarPerdaDeSessao(
  callback: (() => void) | null,
): void {
  aoPerderSessao = callback
}

export class ErroDaApi extends Error {
  readonly status: number

  constructor(status: number, mensagem: string) {
    super(mensagem)
    this.name = 'ErroDaApi'
    this.status = status
  }
}

type Opcoes = {
  metodo?: string
  corpo?: unknown
  token?: string | null
}

function extrairMensagem(conteudo: unknown, status: number): string {
  const detalhe = (conteudo as { detail?: unknown } | null)?.detail

  if (typeof detalhe === 'string') {
    return detalhe
  }

  // O 422 do FastAPI devolve uma lista de erros, um por campo, em vez do
  // texto único das demais falhas. Sem este tratamento a tela exibiria
  // "[object Object]" para o usuário.
  if (Array.isArray(detalhe)) {
    const mensagens: string[] = []

    for (const erro of detalhe) {
      const mensagem = (erro as { msg?: unknown }).msg

      if (typeof mensagem === 'string') {
        mensagens.push(mensagem)
      }
    }

    if (mensagens.length > 0) {
      return mensagens.join('. ')
    }
  }

  return `Erro inesperado do servidor (${status}).`
}

function perdeuSessao(caminho: string, status: number): boolean {
  if (status !== 401) {
    return false
  }

  return !CAMINHOS_SEM_SESSAO.includes(caminho)
}

export async function chamarApi<T>(
  caminho: string,
  opcoes: Opcoes = {},
): Promise<T> {
  const cabecalhos: Record<string, string> = {}

  if (opcoes.corpo !== undefined) {
    cabecalhos['Content-Type'] = 'application/json'
  }

  if (opcoes.token) {
    cabecalhos['Authorization'] = `Bearer ${opcoes.token}`
  }

  let resposta: Response

  try {
    resposta = await fetch(`${URL_BASE}${caminho}`, {
      method: opcoes.metodo ?? 'GET',
      headers: cabecalhos,
      body:
        opcoes.corpo === undefined
          ? undefined
          : JSON.stringify(opcoes.corpo),
    })
  } catch {
    // Falha de rede não tem status HTTP: o backend pode estar fora do ar ou
    // o navegador ter bloqueado a origem.
    throw new ErroDaApi(
      SEM_RESPOSTA_HTTP,
      'Não foi possível falar com o servidor.',
    )
  }

  if (resposta.status === 204) {
    return undefined as T
  }

  const conteudo = await resposta.json().catch(() => null)

  if (!resposta.ok) {
    // O token expira em trinta minutos e pode vencer com a tela aberta. Sem
    // avisar quem controla a sessão, o usuário ficaria vendo "Não
    // autenticado." como se fosse falha de carregamento.
    if (perdeuSessao(caminho, resposta.status)) {
      aoPerderSessao?.()
    }

    throw new ErroDaApi(
      resposta.status,
      extrairMensagem(conteudo, resposta.status),
    )
  }

  return conteudo as T
}
