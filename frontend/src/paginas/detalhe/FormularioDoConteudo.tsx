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
  // Além de desarmar o botão, trava os campos. Quem salva e continua
  // digitando perdia o que escreveu, porque a recarga que segue o
  // salvamento reescreve o formulário com a resposta do servidor — e o
  // aviso de sucesso ainda aparecia por cima da perda.
  enviando: boolean
  // Salvar aqui não muda nada na tela, porque os campos já mostram o que
  // foi digitado. Sem um aviso, a única pista de que deu certo é o botão
  // piscar, e quem não vê fica salvando de novo.
  salvo?: boolean
  aoAlterar: (campo: keyof DadosEditaveis, valor: string) => void
  aoEnviar: (evento: FormEvent) => void
}

export function FormularioDoConteudo({
  dados,
  enviando,
  salvo = false,
  aoAlterar,
  aoEnviar,
}: Props) {
  return (
    <form className={estilos.cartao} onSubmit={aoEnviar}>
      <Campo
        disabled={enviando}
        rotulo="Título"
        value={dados.titulo}
        onChange={(evento) => aoAlterar('titulo', evento.target.value)}
        required
        maxLength={200}
      />

      <div className={estilos.linhaDeCampos}>
        <Campo
          disabled={enviando}
          rotulo="Plataforma"
          value={dados.plataforma}
          onChange={(evento) => aoAlterar('plataforma', evento.target.value)}
          required
          maxLength={50}
        />
        <Campo
          disabled={enviando}
          rotulo="Tipo"
          value={dados.tipo}
          onChange={(evento) => aoAlterar('tipo', evento.target.value)}
          required
          maxLength={50}
        />
        <Campo
          disabled={enviando}
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
        disabled={enviando}
        rotulo="URL da publicação"
        type="url"
        value={dados.url_publicacao}
        onChange={(evento) => aoAlterar('url_publicacao', evento.target.value)}
        maxLength={500}
        dica="Endereço completo, começando com http:// ou https://. Deixe em branco para remover."
      />

      <div className={estilos.botoes}>
        <button className={estilos.acao} type="submit" disabled={enviando}>
          {enviando ? 'Salvando…' : 'Salvar alterações'}
        </button>

        {salvo && !enviando && (
          <p className={estilos.sucesso} role="status">
            Alterações salvas.
          </p>
        )}
      </div>
    </form>
  )
}
