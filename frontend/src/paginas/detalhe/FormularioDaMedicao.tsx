import type { FormEvent } from 'react'

import { Campo } from '../../componentes/Campo'
import { dataDeHoje } from '../../formatacao'
import estilos from '../ConteudoDetalhe.module.css'

export type DadosDaMedicao = {
  visualizacoes: string
  curtidas: string
  comentarios: string
  compartilhamentos: string
  alcance: string
  data_referencia: string
}

type Props = {
  dados: DadosDaMedicao
  enviando: boolean
  // A medição não pode ser anterior à publicação: não se mede desempenho
  // de conteúdo que ainda não existia.
  dataDaPublicacao: string
  aoAlterar: (campo: keyof DadosDaMedicao, valor: string) => void
  aoEnviar: (evento: FormEvent) => void
  aoCancelar: () => void
}

export function FormularioDaMedicao({
  dados,
  enviando,
  dataDaPublicacao,
  aoAlterar,
  aoEnviar,
  aoCancelar,
}: Props) {
  return (
    <form className={estilos.cartao} onSubmit={aoEnviar}>
      <div className={estilos.linhaDeCampos}>
        <Campo
          rotulo="Data de referência"
          type="date"
          value={dados.data_referencia}
          onChange={(evento) =>
            aoAlterar('data_referencia', evento.target.value)
          }
          required
          min={dataDaPublicacao}
          max={dataDeHoje()}
        />
        <Campo
          rotulo="Visualizações"
          type="number"
          value={dados.visualizacoes}
          onChange={(evento) =>
            aoAlterar('visualizacoes', evento.target.value)
          }
          required
          min={0}
          step={1}
        />
        <Campo
          rotulo="Alcance"
          type="number"
          value={dados.alcance}
          onChange={(evento) => aoAlterar('alcance', evento.target.value)}
          required
          min={0}
          step={1}
          dica="Zero deixa o engajamento sem cálculo"
        />
        <Campo
          rotulo="Curtidas"
          type="number"
          value={dados.curtidas}
          onChange={(evento) => aoAlterar('curtidas', evento.target.value)}
          required
          min={0}
          step={1}
        />
        <Campo
          rotulo="Comentários"
          type="number"
          value={dados.comentarios}
          onChange={(evento) => aoAlterar('comentarios', evento.target.value)}
          required
          min={0}
          step={1}
        />
        <Campo
          rotulo="Compartilhamentos"
          type="number"
          value={dados.compartilhamentos}
          onChange={(evento) =>
            aoAlterar('compartilhamentos', evento.target.value)
          }
          required
          min={0}
          step={1}
        />
      </div>

      <div className={estilos.botoes}>
        <button className={estilos.acao} type="submit" disabled={enviando}>
          {enviando ? 'Salvando…' : 'Salvar medição'}
        </button>
        <button
          className={`${estilos.acao} ${estilos.secundario}`}
          type="button"
          onClick={aoCancelar}
        >
          Cancelar
        </button>
      </div>
    </form>
  )
}
