import type { Metrica } from '../api/tipos'
import { formatarData, formatarPercentual } from '../formatacao'
import estilos from './EvolucaoDoEngajamento.module.css'

const ESQUERDA = 50
const DIREITA = 580
const TOPO = 15
const BASE = 110

const MILISSEGUNDOS_POR_DIA = 86_400_000

type Ponto = {
  x: number
  y: number
}

// Date.UTC evita o deslocamento de fuso que new Date('2026-01-01') produz:
// aqui só interessa a distância entre as datas, e ela precisa ser estável.
function emDias(isoDaData: string): number {
  const [ano, mes, dia] = isoDaData.split('-').map(Number)

  return Date.UTC(ano, mes - 1, dia) / MILISSEGUNDOS_POR_DIA
}

// Medição sem índice calculável interrompe a linha em vez de virar zero,
// pela mesma razão que a tabela mostra travessão: ausência de dado não é
// desempenho nulo.
function separarEmTrechos(pontos: (Ponto | null)[]): Ponto[][] {
  const trechos: Ponto[][] = []
  let atual: Ponto[] = []

  for (const ponto of pontos) {
    if (ponto === null) {
      if (atual.length > 0) {
        trechos.push(atual)
        atual = []
      }

      continue
    }

    atual.push(ponto)
  }

  if (atual.length > 0) {
    trechos.push(atual)
  }

  return trechos
}

type Props = {
  metricas: Metrica[]
}

export function EvolucaoDoEngajamento({ metricas }: Props) {
  // A API devolve da medição mais recente para a mais antiga, e uma linha
  // do tempo se lê ao contrário.
  const emOrdem = [...metricas].reverse()

  const calculaveis = emOrdem.filter(
    (metrica) => metrica.engajamento !== null,
  )

  if (calculaveis.length === 0) {
    return (
      <p className={estilos.legenda}>
        Nenhuma medição tem engajamento calculável ainda, então não há
        evolução para desenhar.
      </p>
    )
  }

  const maiorIndice = Math.max(
    ...calculaveis.map((metrica) => metrica.engajamento ?? 0),
  )

  const primeiroDia = emDias(emOrdem[0].data_referencia)
  const ultimoDia = emDias(emOrdem[emOrdem.length - 1].data_referencia)
  const intervalo = ultimoDia - primeiroDia

  const pontos: (Ponto | null)[] = emOrdem.map((metrica) => {
    if (metrica.engajamento === null) {
      return null
    }

    // Uma medição só, ou várias na mesma data, não têm eixo horizontal:
    // o ponto fica no centro em vez de dividir por zero.
    const posicao =
      intervalo === 0
        ? 0.5
        : (emDias(metrica.data_referencia) - primeiroDia) / intervalo

    const proporcaoVertical =
      maiorIndice === 0 ? 0 : metrica.engajamento / maiorIndice

    return {
      x: ESQUERDA + posicao * (DIREITA - ESQUERDA),
      y: BASE - proporcaoVertical * (BASE - TOPO),
    }
  })

  const trechos = separarEmTrechos(pontos)

  return (
    <div className={estilos.grafico}>
      <svg
        className={estilos.desenho}
        viewBox="0 0 600 140"
        role="img"
        aria-label={`Evolução do engajamento em ${calculaveis.length} medições, de ${formatarPercentual(
          calculaveis[0].engajamento,
        )} a ${formatarPercentual(
          calculaveis[calculaveis.length - 1].engajamento,
        )}.`}
      >
        <line
          className={estilos.eixo}
          x1={ESQUERDA}
          y1={TOPO}
          x2={ESQUERDA}
          y2={BASE}
        />
        <line
          className={estilos.eixo}
          x1={ESQUERDA}
          y1={BASE}
          x2={DIREITA}
          y2={BASE}
        />

        <text className={estilos.marcaDoEixo} x={0} y={TOPO + 5}>
          {formatarPercentual(maiorIndice)}
        </text>
        <text className={estilos.marcaDoEixo} x={0} y={BASE + 4}>
          0%
        </text>

        {/* Trecho de um ponto só não vira linha: um polyline com um ponto
            não desenha nada. O círculo abaixo é que o representa. */}
        {trechos
          .filter((trecho) => trecho.length > 1)
          .map((trecho) => (
            <polyline
              key={`${trecho[0].x}-${trecho[0].y}`}
              className={estilos.linha}
              points={trecho
                .map((ponto) => `${ponto.x},${ponto.y}`)
                .join(' ')}
            />
          ))}

        {trechos.flat().map((ponto) => (
          <circle
            key={`${ponto.x}-${ponto.y}`}
            className={estilos.ponto}
            cx={ponto.x}
            cy={ponto.y}
            r={4}
          />
        ))}
      </svg>

      <p className={estilos.legenda}>
        De {formatarData(emOrdem[0].data_referencia)} a{' '}
        {formatarData(emOrdem[emOrdem.length - 1].data_referencia)}.
        Medições sem alcance interrompem a linha.
      </p>
    </div>
  )
}
