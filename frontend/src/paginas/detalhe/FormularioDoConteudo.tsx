import type { FormEvent } from 'react'

import { Campo } from '../../componentes/Campo'
import { dataDeHoje } from '../../formatacao'
import estilos from '../ConteudoDetalhe.module.css'

export type DadosEditaveis = {
  titulo: string
  plataforma: string
  tipo: string
  data_publicacao: string
  url_publicacao: string
}

type Props = {
  dados: DadosEditaveis
  enviando: boolean
  aoAlterar: (campo: keyof DadosEditaveis, valor: string) => void
  aoEnviar: (evento: FormEvent) => void
}

export function FormularioDoConteudo({
  dados,
  enviando,
  aoAlterar,
  aoEnviar,
}: Props) {
  return (
    <form className={estilos.cartao} onSubmit={aoEnviar}>
      <Campo
        rotulo="Título"
        value={dados.titulo}
        onChange={(evento) => aoAlterar('titulo', evento.target.value)}
        required
        maxLength={200}
      />

      <div className={estilos.linhaDeCampos}>
        <Campo
          rotulo="Plataforma"
          value={dados.plataforma}
          onChange={(evento) => aoAlterar('plataforma', evento.target.value)}
          required
          maxLength={50}
        />
        <Campo
          rotulo="Tipo"
          value={dados.tipo}
          onChange={(evento) => aoAlterar('tipo', evento.target.value)}
          required
          maxLength={50}
        />
        <Campo
          rotulo="Data de publicação"
          type="date"
          value={dados.data_publicacao}
          onChange={(evento) =>
            aoAlterar('data_publicacao', evento.target.value)
          }
          required
          max={dataDeHoje()}
        />
      </div>

      <Campo
        rotulo="URL da publicação"
        type="url"
        value={dados.url_publicacao}
        onChange={(evento) => aoAlterar('url_publicacao', evento.target.value)}
        maxLength={500}
        dica="Deixe em branco para remover a URL"
      />

      <div className={estilos.botoes}>
        <button className={estilos.acao} type="submit" disabled={enviando}>
          Salvar alterações
        </button>
      </div>
    </form>
  )
}
