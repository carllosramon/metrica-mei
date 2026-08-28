import { useEffect, useState } from 'react'

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
              Registre medições para comparar o desempenho das suas redes.
            </p>
          ) : (
            <>
              <BarrasPorPlataforma
                plataformas={dados.desempenho_por_plataforma}
              />

              <div className={estilos.moldura}>
                <table className={estilos.tabela}>
                  <thead>
                    <tr>
                      <th scope="col">Plataforma</th>
                      <th scope="col" className={estilos.numerico}>
                        Conteúdos
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
                        <td className={estilos.numerico}>
                          {formatarNumero(plataforma.total_conteudos)}
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

          {dados.maiores_alcances.length === 0 ? (
            <p className={estilos.vazio}>
              Nenhuma medição registrada ainda. Registre métricas dos seus
              conteúdos para ver o ranking.
            </p>
          ) : (
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
                      <td>{conteudo.titulo}</td>
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
          )}
        </>
      )}
    </main>
  )
}
