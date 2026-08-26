import { useEffect, useState } from 'react'

import { ErroDaApi } from '../api/cliente'
import { buscarPainel } from '../api/painel'
import type { Painel as DadosDoPainel } from '../api/tipos'
import { usarAutenticacao } from '../autenticacao/usarAutenticacao'
import { CartaoIndicador } from '../componentes/CartaoIndicador'
import {
  formatarData,
  formatarNumero,
  formatarPercentual,
} from '../formatacao'
import estilos from './Painel.module.css'

export function Painel() {
  const { token, usuario } = usarAutenticacao()

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

          <h2 className={estilos.secao}>Melhores conteúdos</h2>

          {dados.melhores_conteudos.length === 0 ? (
            <p className={estilos.vazio}>
              Nenhum conteúdo com engajamento calculável ainda. Registre
              métricas com alcance maior que zero para ver o ranking.
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
                      Engajamento
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {dados.melhores_conteudos.map((conteudo) => (
                    <tr key={conteudo.conteudo_id}>
                      <td>{conteudo.titulo}</td>
                      <td>{conteudo.plataforma}</td>
                      <td>{formatarData(conteudo.data_referencia)}</td>
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
