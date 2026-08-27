import type { DesempenhoDaPlataforma } from '../api/tipos'
import { formatarNumero } from '../formatacao'
import estilos from './BarrasPorPlataforma.module.css'

type Props = {
  plataformas: DesempenhoDaPlataforma[]
}

export function BarrasPorPlataforma({ plataformas }: Props) {
  // As barras são proporcionais à maior, e não a um total: comparar redes
  // entre si é a pergunta, e a fatia de cada uma no bolo já está na tabela.
  const maiorAlcance = Math.max(
    ...plataformas.map((plataforma) => plataforma.total_alcance),
    1,
  )

  return (
    <div
      className={estilos.grafico}
      role="img"
      aria-label={`Alcance por plataforma, em ${plataformas.length} redes, da maior para a menor.`}
    >
      {plataformas.map((plataforma) => (
        <div className={estilos.linha} key={plataforma.plataforma}>
          <span className={estilos.rotulo}>{plataforma.plataforma}</span>

          <div className={estilos.trilho}>
            <div
              className={estilos.barra}
              style={{
                width: `${(plataforma.total_alcance / maiorAlcance) * 100}%`,
              }}
            />
          </div>

          <span className={estilos.valor}>
            {formatarNumero(plataforma.total_alcance)}
          </span>
        </div>
      ))}
    </div>
  )
}
