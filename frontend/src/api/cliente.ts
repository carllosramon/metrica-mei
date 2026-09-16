const URL_BASE =
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const SEM_RESPOSTA_HTTP = 0

// Conexão aceita e resposta que nunca vem deixa a promessa pendente para
// sempre. Como todo formulário liga o "enviando" a essa espera, os botões
// da tela ficam travados sem nenhum aviso. Trinta segundos é folgado para
// qualquer consulta desta API e curto o bastante para o usuário não achar
// que travou.
const PRAZO_DA_RESPOSTA = 30_000

// Nestes caminhos o 401 significa credencial errada, e não sessão perdida.
// Derrubar a sessão aqui apagaria o token de quem só errou a senha na tela
// de login estando autenticado em outra aba.
const CAMINHOS_SEM_SESSAO = ['/auth/login', '/auth/register']

// O aviso leva o token da requisição que falhou. Quem controla a sessão
// compara com o token atual, e um 401 atrasado de uma requisição feita
// antes de sair não derruba a sessão de quem já entrou de novo.
type AoPerderSessao = (tokenDaRequisicao: string | null) => void

let aoPerderSessao: AoPerderSessao | null = null

export function registrarPerdaDeSessao(
  callback: AoPerderSessao | null,
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
      signal: AbortSignal.timeout(PRAZO_DA_RESPOSTA),
      body:
        opcoes.corpo === undefined
          ? undefined
          : JSON.stringify(opcoes.corpo),
    })
  } catch (falha) {
    // O prazo estourado tem mensagem própria porque a saída é outra:
    // aqui o servidor foi encontrado, e tentar de novo costuma resolver.
    if (falha instanceof Error && falha.name === 'TimeoutError') {
      throw new ErroDaApi(
        SEM_RESPOSTA_HTTP,
        'O servidor demorou demais para responder. Tente de novo.',
      )
    }

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

  let conteudo: unknown = null
  let corpoIlegivel = false

  try {
    conteudo = await resposta.json()
  } catch {
    corpoIlegivel = true
  }

  // Um 200 que não traz JSON não é resposta desta API: é o index.html que
  // o servidor de arquivos devolve quando o caminho não chega ao backend.
  // Tratado como nulo, ele virava uma lista vazia ou um "Carregando…" que
  // não terminava nunca, sem nada na tela explicando o que houve.
  if (resposta.ok && corpoIlegivel) {
    throw new ErroDaApi(
      resposta.status,
      'O servidor respondeu algo que não é a resposta esperada. Confira o endereço da API.',
    )
  }

  if (!resposta.ok) {
    // O token expira em trinta minutos e pode vencer com a tela aberta. Sem
    // avisar quem controla a sessão, o usuário ficaria vendo "Não
    // autenticado." como se fosse falha de carregamento.
    if (perdeuSessao(caminho, resposta.status)) {
      aoPerderSessao?.(opcoes.token ?? null)
    }

    throw new ErroDaApi(
      resposta.status,
      extrairMensagem(conteudo, resposta.status),
    )
  }

  return conteudo as T
}
