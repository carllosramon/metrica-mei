import type { Metrica } from '../../api/tipos'
import {
  formatarData,
  formatarNumero,
  formatarPercentual,
} from '../../formatacao'
import estilos from '../ConteudoDetalhe.module.css'

type Props = {
  metricas: Metrica[]
  // Exclusão pede dois cliques: o primeiro marca a linha, o segundo
  // confirma. Guardar qual linha está marcada é da página, porque só ela
  // sabe quando a lista foi recarregada.
  metricaConfirmada: number | null
  aoEditar: (metrica: Metrica) => void
  aoExcluir: (metricaId: number) => void
}

export function TabelaDeMedicoes({
  metricas,
  metricaConfirmada,
  aoEditar,
  aoExcluir,
}: Props) {
  return (
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
                    onClick={() => aoEditar(metrica)}
                  >
                    Editar
                  </button>
                  <button
                    className={estilos.botaoDaLinha}
                    type="button"
                    onClick={() => aoExcluir(metrica.id)}
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
  )
}
