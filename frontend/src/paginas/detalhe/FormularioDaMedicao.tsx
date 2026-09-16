import type { FormEvent } from 'react'

import { Campo } from '../../componentes/Campo'
import { dataDeHoje, formatarData } from '../../formatacao'
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
  // O erro do salvamento é mostrado aqui dentro, e não no topo da
  // página, onde ficava fora da área visível junto com o botão clicado.
  erro?: string | null
  // Sem dizer qual data está em edição, "Editar" e "Registrar" abrem
  // exatamente o mesmo formulário e o usuário não sabe onde está.
  dataEmEdicao?: string | null
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
  erro = null,
  dataEmEdicao = null,
  dataDaPublicacao,
  aoAlterar,
  aoEnviar,
  aoCancelar,
}: Props) {
  return (
    <form className={estilos.cartao} onSubmit={aoEnviar}>
      <h3 className={estilos.tituloDoFormulario}>
        {dataEmEdicao === null
          ? 'Nova medição'
          : `Editando a medição de ${formatarData(dataEmEdicao)}`}
      </h3>

      {/* A única menção a "acumulado" ficava no estado vazio, abaixo do
          formulário, e sumia da segunda medição em diante. Quem anotasse
          o movimento do dia estragaria o histórico sem nunca saber. */}
      <p className={estilos.instrucao}>
        Anote os números <strong>totais</strong> que a rede social mostra
        hoje, desde que você publicou, e não o que rendeu só hoje. Se o
        post já tem 4.000 visualizações e ganhou 300 desde a última
        anotação, escreva 4.300.
      </p>

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
          dica="Quantas vezes o post foi exibido, contando repetições. É normal ser maior que o alcance."
        />
        <Campo
          rotulo="Alcance"
          type="number"
          value={dados.alcance}
          onChange={(evento) => aoAlterar('alcance', evento.target.value)}
          required
          min={0}
          step={1}
          dica="Quantas pessoas diferentes viram o post. No Instagram aparece como “Contas alcançadas”. Deixar em zero deixa o engajamento sem cálculo."
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

      {erro !== null && (
        <p className={estilos.erro} role="alert">
          {erro}
        </p>
      )}

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
