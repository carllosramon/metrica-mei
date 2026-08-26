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
  alcance: number
  engajamento: number | null
  data_referencia: string
}

export type DesempenhoDaPlataforma = {
  plataforma: string
  total_conteudos: number
  total_visualizacoes: number
  total_curtidas: number
  total_comentarios: number
  total_compartilhamentos: number
  total_alcance: number
  engajamento: number | null
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
  desempenho_por_plataforma: DesempenhoDaPlataforma[]
  maiores_alcances: ConteudoDoRanking[]
}

export type Conteudo = {
  id: number
  titulo: string
  plataforma: string
  tipo: string
  data_publicacao: string
  criado_em: string
  url_publicacao: string | null
}

export type DadosDoConteudo = {
  titulo: string
  plataforma: string
  tipo: string
  data_publicacao: string
  url_publicacao: string | null
}

export type Metrica = {
  id: number
  visualizacoes: number
  curtidas: number
  comentarios: number
  compartilhamentos: number
  alcance: number
  data_referencia: string
  criado_em: string
  engajamento: number | null
}

export type DadosDaMetrica = {
  visualizacoes: number
  curtidas: number
  comentarios: number
  compartilhamentos: number
  alcance: number
  data_referencia: string
}
