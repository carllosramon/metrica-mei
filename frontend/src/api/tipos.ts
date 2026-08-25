// Espelha os schemas de resposta do backend. Quando um campo muda lá, o
// TypeScript quebra o build aqui, e não a tela na frente do usuário.

export type Usuario = {
  id: number
  nome: string
  email: string
  criado_em: string
}

export type Token = {
  access_token: string
  token_type: string
}

export type ConteudoDoRanking = {
  conteudo_id: number
  titulo: string
  plataforma: string
  engajamento: number
  data_referencia: string
}

export type Painel = {
  total_conteudos: number
  conteudos_com_metricas: number
  total_visualizacoes: number
  total_curtidas: number
  total_comentarios: number
  total_compartilhamentos: number
  total_alcance: number
  // Nulo quando o alcance total é zero: o índice não é calculável, o que é
  // diferente de um engajamento realmente zero.
  engajamento_geral: number | null
  melhores_conteudos: ConteudoDoRanking[]
}
