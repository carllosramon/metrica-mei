import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ErroDaApi } from '../api/cliente'
import {
  atualizarConteudo,
  buscarConteudo,
  excluirConteudo,
} from '../api/conteudos'
import {
  atualizarMetrica,
  criarMetrica,
  excluirMetrica,
  listarMetricas,
} from '../api/metricas'
import type { Conteudo, Metrica } from '../api/tipos'
import { usarAutenticacao } from '../autenticacao/usarAutenticacao'
import { Campo } from '../componentes/Campo'
import {
  dataDeHoje,
  formatarData,
  formatarNumero,
  formatarPercentual,
} from '../formatacao'
import estilos from './ConteudoDetalhe.module.css'

const METRICA_VAZIA = {
  visualizacoes: '0',
  curtidas: '0',
  comentarios: '0',
  compartilhamentos: '0',
  alcance: '0',
  data_referencia: dataDeHoje(),
}

function mensagemDe(falha: unknown, alternativa: string): string {
  return falha instanceof ErroDaApi ? falha.message : alternativa
}

export function ConteudoDetalhe() {
  const { token } = usarAutenticacao()
  const { conteudoId } = useParams()
  const navegar = useNavigate()

  const identificador = Number(conteudoId)

  const [conteudo, definirConteudo] = useState<Conteudo | null>(null)
  const [metricas, definirMetricas] = useState<Metrica[] | null>(null)
  const [erro, definirErro] = useState<string | null>(null)

  const [dadosDoConteudo, definirDadosDoConteudo] = useState({
    titulo: '',
    plataforma: '',
    tipo: '',
    data_publicacao: '',
    url_publicacao: '',
  })

  const [confirmandoExclusao, definirConfirmandoExclusao] = useState(false)
  const [metricaConfirmada, definirMetricaConfirmada] = useState<
    number | null
  >(null)

  const [formularioAberto, definirFormularioAberto] = useState(false)
  const [metricaEmEdicao, definirMetricaEmEdicao] = useState<number | null>(
    null,
  )
  const [formularioDaMetrica, definirFormularioDaMetrica] =
    useState(METRICA_VAZIA)
  const [enviando, definirEnviando] = useState(false)

  const carregar = useCallback(async () => {
    if (token === null) {
      return
    }

    try {
      const encontrado = await buscarConteudo(token, identificador)

      definirConteudo(encontrado)
      definirDadosDoConteudo({
        titulo: encontrado.titulo,
        plataforma: encontrado.plataforma,
        tipo: encontrado.tipo,
        data_publicacao: encontrado.data_publicacao,
        url_publicacao: encontrado.url_publicacao ?? '',
      })
      definirMetricas(await listarMetricas(token, identificador))
    } catch (falha) {
      // Conteúdo inexistente ou de outro usuário não tem tela própria: a
      // lista é o único lugar coerente para devolver o usuário.
      if (falha instanceof ErroDaApi && falha.status === 404) {
        navegar('/conteudos', { replace: true })
        return
      }

      definirErro(mensagemDe(falha, 'Não foi possível carregar o conteúdo.'))
    }
  }, [token, identificador, navegar])

  useEffect(() => {
    void carregar()
  }, [carregar])

  async function salvarConteudo(evento: FormEvent) {
    evento.preventDefault()

    if (token === null) {
      return
    }

    definirErro(null)
    definirEnviando(true)

    try {
      await atualizarConteudo(token, identificador, {
        ...dadosDoConteudo,
        // Campo em branco significa remover a URL, e o backend recusa texto
        // vazio — null é como ele entende a remoção.
        url_publicacao:
          dadosDoConteudo.url_publicacao.trim() === ''
            ? null
            : dadosDoConteudo.url_publicacao,
      })

      await carregar()
    } catch (falha) {
      definirErro(mensagemDe(falha, 'Não foi possível salvar o conteúdo.'))
    } finally {
      definirEnviando(false)
    }
  }

  async function removerConteudo() {
    if (token === null) {
      return
    }

    try {
      await excluirConteudo(token, identificador)
      navegar('/conteudos', { replace: true })
    } catch (falha) {
      definirErro(mensagemDe(falha, 'Não foi possível excluir o conteúdo.'))
    }
  }

  function abrirNovaMetrica() {
    definirMetricaEmEdicao(null)
    definirFormularioDaMetrica(METRICA_VAZIA)
    definirFormularioAberto(true)
  }

  function abrirEdicaoDaMetrica(metrica: Metrica) {
    definirMetricaEmEdicao(metrica.id)
    definirFormularioDaMetrica({
      visualizacoes: String(metrica.visualizacoes),
      curtidas: String(metrica.curtidas),
      comentarios: String(metrica.comentarios),
      compartilhamentos: String(metrica.compartilhamentos),
      alcance: String(metrica.alcance),
      data_referencia: metrica.data_referencia,
    })
    definirFormularioAberto(true)
  }

  async function salvarMetrica(evento: FormEvent) {
    evento.preventDefault()

    if (token === null) {
      return
    }

    definirErro(null)
    definirEnviando(true)

    const dados = {
      visualizacoes: Number(formularioDaMetrica.visualizacoes),
      curtidas: Number(formularioDaMetrica.curtidas),
      comentarios: Number(formularioDaMetrica.comentarios),
      compartilhamentos: Number(formularioDaMetrica.compartilhamentos),
      alcance: Number(formularioDaMetrica.alcance),
      data_referencia: formularioDaMetrica.data_referencia,
    }

    try {
      if (metricaEmEdicao === null) {
        await criarMetrica(token, identificador, dados)
      } else {
        await atualizarMetrica(token, identificador, metricaEmEdicao, dados)
      }

      definirFormularioAberto(false)
      await carregar()
    } catch (falha) {
      // A unicidade por data é o erro que o usuário mais encontra, e a
      // mensagem genérica não diria o que fazer a respeito.
      if (falha instanceof ErroDaApi && falha.status === 409) {
        definirErro(
          'Já existe uma medição deste conteúdo nesta data. Edite a medição existente ou escolha outra data.',
        )
      } else {
        definirErro(mensagemDe(falha, 'Não foi possível salvar a medição.'))
      }
    } finally {
      definirEnviando(false)
    }
  }

  async function removerMetrica(metricaId: number) {
    if (token === null) {
      return
    }

    try {
      await excluirMetrica(token, identificador, metricaId)
      definirMetricaConfirmada(null)
      await carregar()
    } catch (falha) {
      definirErro(mensagemDe(falha, 'Não foi possível excluir a medição.'))
    }
  }

  function alterarMetrica(campo: keyof typeof METRICA_VAZIA, valor: string) {
    definirFormularioDaMetrica((atual) => ({ ...atual, [campo]: valor }))
  }

  function alterarConteudo(
    campo: keyof typeof dadosDoConteudo,
    valor: string,
  ) {
    definirDadosDoConteudo((atual) => ({ ...atual, [campo]: valor }))
  }

  if (conteudo === null) {
    return (
      <main className={estilos.pagina}>
        {erro === null ? (
          <p>Carregando…</p>
        ) : (
          <p className={estilos.erro} role="alert">
            {erro}
          </p>
        )}
      </main>
    )
  }

  return (
    <main className={estilos.pagina}>
      <Link className={estilos.voltar} to="/conteudos">
        &larr; Meus conteúdos
      </Link>

      <header className={estilos.cabecalho}>
        <h1 className={estilos.titulo}>{conteudo.titulo}</h1>

        <button
          className={`${estilos.acao} ${
            confirmandoExclusao ? estilos.confirmando : estilos.perigo
          }`}
          type="button"
          onClick={() =>
            confirmandoExclusao
              ? void removerConteudo()
              : definirConfirmandoExclusao(true)
          }
        >
          {confirmandoExclusao ? 'Confirmar exclusão' : 'Excluir conteúdo'}
        </button>
      </header>

      {erro !== null && (
        <p className={estilos.erro} role="alert">
          {erro}
        </p>
      )}

      <form className={estilos.cartao} onSubmit={salvarConteudo}>
        <Campo
          rotulo="Título"
          value={dadosDoConteudo.titulo}
          onChange={(evento) => alterarConteudo('titulo', evento.target.value)}
          required
          maxLength={200}
        />

        <div className={estilos.linhaDeCampos}>
          <Campo
            rotulo="Plataforma"
            value={dadosDoConteudo.plataforma}
            onChange={(evento) =>
              alterarConteudo('plataforma', evento.target.value)
            }
            required
            maxLength={50}
          />
          <Campo
            rotulo="Tipo"
            value={dadosDoConteudo.tipo}
            onChange={(evento) => alterarConteudo('tipo', evento.target.value)}
            required
            maxLength={50}
          />
          <Campo
            rotulo="Data de publicação"
            type="date"
            value={dadosDoConteudo.data_publicacao}
            onChange={(evento) =>
              alterarConteudo('data_publicacao', evento.target.value)
            }
            required
            max={dataDeHoje()}
          />
        </div>

        <Campo
          rotulo="URL da publicação"
          type="url"
          value={dadosDoConteudo.url_publicacao}
          onChange={(evento) =>
            alterarConteudo('url_publicacao', evento.target.value)
          }
          maxLength={500}
          dica="Deixe em branco para remover a URL"
        />

        <div className={estilos.botoes}>
          <button className={estilos.acao} type="submit" disabled={enviando}>
            Salvar alterações
          </button>
        </div>
      </form>

      <h2 className={estilos.secao}>Medições</h2>

      {!formularioAberto && (
        <div className={estilos.botoes}>
          <button
            className={estilos.acao}
            type="button"
            onClick={abrirNovaMetrica}
          >
            Registrar medição
          </button>
        </div>
      )}

      {formularioAberto && (
        <form className={estilos.cartao} onSubmit={salvarMetrica}>
          <div className={estilos.linhaDeCampos}>
            <Campo
              rotulo="Data de referência"
              type="date"
              value={formularioDaMetrica.data_referencia}
              onChange={(evento) =>
                alterarMetrica('data_referencia', evento.target.value)
              }
              required
              min={conteudo.data_publicacao}
              max={dataDeHoje()}
            />
            <Campo
              rotulo="Visualizações"
              type="number"
              value={formularioDaMetrica.visualizacoes}
              onChange={(evento) =>
                alterarMetrica('visualizacoes', evento.target.value)
              }
              required
              min={0}
              step={1}
            />
            <Campo
              rotulo="Alcance"
              type="number"
              value={formularioDaMetrica.alcance}
              onChange={(evento) =>
                alterarMetrica('alcance', evento.target.value)
              }
              required
              min={0}
              step={1}
              dica="Zero deixa o engajamento sem cálculo"
            />
            <Campo
              rotulo="Curtidas"
              type="number"
              value={formularioDaMetrica.curtidas}
              onChange={(evento) =>
                alterarMetrica('curtidas', evento.target.value)
              }
              required
              min={0}
              step={1}
            />
            <Campo
              rotulo="Comentários"
              type="number"
              value={formularioDaMetrica.comentarios}
              onChange={(evento) =>
                alterarMetrica('comentarios', evento.target.value)
              }
              required
              min={0}
              step={1}
            />
            <Campo
              rotulo="Compartilhamentos"
              type="number"
              value={formularioDaMetrica.compartilhamentos}
              onChange={(evento) =>
                alterarMetrica('compartilhamentos', evento.target.value)
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
              onClick={() => definirFormularioAberto(false)}
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      {metricas !== null && metricas.length === 0 && (
        <p className={estilos.vazio}>
          Nenhuma medição registrada. Cada medição é um retrato acumulado do
          desempenho numa data.
        </p>
      )}

      {metricas !== null && metricas.length > 0 && (
        <div className={estilos.moldura}>
          <table className={estilos.tabela}>
            <thead>
              <tr>
                <th scope="col">Data</th>
                <th scope="col" className={estilos.numerico}>
                  Visualizações
                </th>
                <th scope="col" className={estilos.numerico}>
                  Alcance
                </th>
                <th scope="col" className={estilos.numerico}>
                  Curtidas
                </th>
                <th scope="col" className={estilos.numerico}>
                  Comentários
                </th>
                <th scope="col" className={estilos.numerico}>
                  Compart.
                </th>
                <th scope="col" className={estilos.numerico}>
                  Engajamento
                </th>
                <th scope="col">Ações</th>
              </tr>
            </thead>
            <tbody>
              {metricas.map((metrica) => (
                <tr key={metrica.id}>
                  <td>{formatarData(metrica.data_referencia)}</td>
                  <td className={estilos.numerico}>
                    {formatarNumero(metrica.visualizacoes)}
                  </td>
                  <td className={estilos.numerico}>
                    {formatarNumero(metrica.alcance)}
                  </td>
                  <td className={estilos.numerico}>
                    {formatarNumero(metrica.curtidas)}
                  </td>
                  <td className={estilos.numerico}>
                    {formatarNumero(metrica.comentarios)}
                  </td>
                  <td className={estilos.numerico}>
                    {formatarNumero(metrica.compartilhamentos)}
                  </td>
                  <td className={estilos.numerico}>
                    {formatarPercentual(metrica.engajamento)}
                  </td>
                  <td>
                    <div className={estilos.linhaDeAcoes}>
                      <button
                        className={estilos.botaoDaLinha}
                        type="button"
                        onClick={() => abrirEdicaoDaMetrica(metrica)}
                      >
                        Editar
                      </button>
                      <button
                        className={estilos.botaoDaLinha}
                        type="button"
                        onClick={() =>
                          metricaConfirmada === metrica.id
                            ? void removerMetrica(metrica.id)
                            : definirMetricaConfirmada(metrica.id)
                        }
                      >
                        {metricaConfirmada === metrica.id
                          ? 'Confirmar'
                          : 'Excluir'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}
