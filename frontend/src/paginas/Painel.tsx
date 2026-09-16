import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ErroDaApi } from '../api/cliente'
import { buscarPainel } from '../api/painel'
import type { Painel as DadosDoPainel } from '../api/tipos'
import { useAutenticacao } from '../autenticacao/useAutenticacao'
import { BarrasPorPlataforma } from '../componentes/BarrasPorPlataforma'
import { CartaoIndicador } from '../componentes/CartaoIndicador'
import {
  formatarData,
  formatarNumero,
  formatarPercentual,
} from '../formatacao'
import estilos from './Painel.module.css'

export function Painel() {
  const { token, usuario } = useAutenticacao()

  const [dados, definirDados] = useState<DadosDoPainel | null>(null)
  const [erro, definirErro] = useState<string | null>(null)

  useEffect(() => {
    if (token === null) {
      return
    }

    let cancelado = false

    buscarPainel(token)
      .then((painel) => {
        if (!cancelado) {
          definirDados(painel)
        }
      })
      .catch((falha) => {
        if (cancelado) {
          return
        }

        definirErro(
          falha instanceof ErroDaApi
            ? falha.message
            : 'Não foi possível carregar o painel.',
        )
      })

    return () => {
      cancelado = true
    }
  }, [token])

  return (
    <main className={estilos.pagina}>
      <header className={estilos.cabecalho}>
        <div>
          <h1 className={estilos.titulo}>Painel de análise</h1>
          {usuario !== null && (
            <p className={estilos.saudacao}>Olá, {usuario.nome}.</p>
          )}
        </div>
      </header>

      {erro !== null && (
        <p className={estilos.erro} role="alert">
          {erro}
        </p>
      )}

      {erro === null && dados === null && <p>Carregando o painel…</p>}

      {/* Quem chega sem nada cadastrado caía num painel zerado, sem link
          e sem saber que a primeira etapa é outra tela. O bloco explica
          a ordem das coisas e leva para o começo dela. */}
      {dados !== null && dados.total_conteudos === 0 && (
        <section className={estilos.primeiroUso}>
          <h2 className={estilos.tituloDoPrimeiroUso}>
            Você ainda não cadastrou nenhum conteúdo
          </h2>

          <p>
            Não há nada para somar aqui por enquanto. Funciona assim:
            primeiro você cadastra uma publicação que já fez. Depois abre
            essa publicação e anota os números que a rede social mostra
            sobre ela. Só então este painel começa a comparar suas redes.
          </p>

          <Link className={estilos.acao} to="/conteudos">
            Cadastrar minha primeira publicação
          </Link>
        </section>
      )}

      {dados !== null && (
        <>
          <section className={estilos.indicadores}>
            <CartaoIndicador
              rotulo="Engajamento geral"
              valor={formatarPercentual(dados.engajamento_geral)}
              observacao={
                dados.engajamento_geral === null
                  ? 'Sem alcance registrado para calcular.'
                  : undefined
              }
              destacado
            />
            <CartaoIndicador
              rotulo="Conteúdos"
              valor={formatarNumero(dados.total_conteudos)}
              observacao={`${formatarNumero(
                dados.conteudos_com_metricas,
              )} com métrica registrada`}
            />
            <CartaoIndicador
              rotulo="Visualizações"
              valor={formatarNumero(dados.total_visualizacoes)}
            />
            <CartaoIndicador
              rotulo="Alcance"
              valor={formatarNumero(dados.total_alcance)}
            />
            <CartaoIndicador
              rotulo="Curtidas"
              valor={formatarNumero(dados.total_curtidas)}
            />
            <CartaoIndicador
              rotulo="Comentários"
              valor={formatarNumero(dados.total_comentarios)}
            />
            <CartaoIndicador
              rotulo="Compartilhamentos"
              valor={formatarNumero(dados.total_compartilhamentos)}
            />
          </section>

          <h2 className={estilos.secao}>Desempenho por plataforma</h2>

          {dados.desempenho_por_plataforma.length === 0 ? (
            <p className={estilos.vazio}>
              {dados.total_conteudos === 0
                ? 'Comece cadastrando um conteúdo. A comparação entre redes aparece depois que houver o que comparar.'
                : 'Registre medições para comparar o desempenho das suas redes.'}
            </p>
          ) : (
            <>
              {/* Sem esta linha o usuário não sabe qual coluna responde
                  "qual rede rende mais", e escolhe uma no chute. */}
              <p className={estilos.leitura}>
                Ordenado pelo alcance, da rede onde você chegou a mais
                pessoas para a que chegou a menos. Se quiser saber onde o
                público reage mais, e não onde ele só é maior, compare a
                coluna Engajamento.
              </p>

              <BarrasPorPlataforma
                plataformas={dados.desempenho_por_plataforma}
              />

              <div className={estilos.moldura}>
                <table className={estilos.tabela}>
                  <thead>
                    <tr>
                      <th scope="col">Plataforma</th>
                      <th scope="col" className={estilos.numerico}>
                        Conteúdos medidos
                      </th>
                      <th scope="col" className={estilos.numerico}>
                        Visualizações
                      </th>
                      <th scope="col" className={estilos.numerico}>
                        Alcance
                      </th>
                      <th scope="col" className={estilos.numerico}>
                        Engajamento
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {dados.desempenho_por_plataforma.map((plataforma) => (
                      <tr key={plataforma.plataforma}>
                        <td>{plataforma.plataforma}</td>
                        {/* Os dois números juntos, porque "2" sozinho era
                            lido como o total da rede, e não como a parte
                            dela que já tem medição. */}
                        <td className={estilos.numerico}>
                          {formatarNumero(
                            plataforma.conteudos_com_metricas,
                          )}{' '}
                          de {formatarNumero(plataforma.total_conteudos)}
                        </td>
                        <td className={estilos.numerico}>
                          {formatarNumero(plataforma.total_visualizacoes)}
                        </td>
                        <td className={estilos.numerico}>
                          {formatarNumero(plataforma.total_alcance)}
                        </td>
                        <td className={estilos.numerico}>
                          {formatarPercentual(plataforma.engajamento)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          <h2 className={estilos.secao}>Conteúdos de maior alcance</h2>

          {/* Mandar "registre medições" para quem não tem conteúdo é
              pedir um passo que ainda não dá para dar. */}
          {dados.maiores_alcances.length === 0 ? (
            <p className={estilos.vazio}>
              {dados.total_conteudos === 0
                ? 'O ranking compara os conteúdos que você já cadastrou, e ainda não há nenhum.'
                : 'Nenhuma medição registrada ainda. Registre métricas dos seus conteúdos para ver o ranking.'}
            </p>
          ) : (
            <>
              {/* A ressalva é a razão registrada no RF05 para o índice
                  aparecer ao lado do alcance, e nunca tinha chegado à
                  tela: o título empurra para a leitura contrária. */}
              <p className={estilos.leitura}>
                Estão ordenados por alcance. Alcançar mais pessoas não é a
                mesma coisa que ir melhor, então olhe o engajamento ao
                lado para saber qual post fez mais gente reagir.
              </p>

              <div className={estilos.moldura}>
              <table className={estilos.tabela}>
                <thead>
                  <tr>
                    <th scope="col">Conteúdo</th>
                    <th scope="col">Plataforma</th>
                    <th scope="col">Medição</th>
                    <th scope="col" className={estilos.numerico}>
                      Alcance
                    </th>
                    <th scope="col" className={estilos.numerico}>
                      Engajamento
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {dados.maiores_alcances.map((conteudo) => (
                    <tr key={conteudo.conteudo_id}>
                      {/* Do painel para o conteúdo em um clique. O
                          identificador já vinha na resposta e só era
                          usado como chave da linha. */}
                      <td>
                        <Link to={`/conteudos/${conteudo.conteudo_id}`}>
                          {conteudo.titulo}
                        </Link>
                      </td>
                      <td>{conteudo.plataforma}</td>
                      <td>{formatarData(conteudo.data_referencia)}</td>
                      <td className={estilos.numerico}>
                        {formatarNumero(conteudo.alcance)}
                      </td>
                      <td className={estilos.numerico}>
                        {formatarPercentual(conteudo.engajamento)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
            </>
          )}
        </>
      )}
    </main>
  )
}
