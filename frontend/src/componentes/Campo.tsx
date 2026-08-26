import { useId } from 'react'
import type { InputHTMLAttributes } from 'react'

import estilos from './Campo.module.css'

// Os atributos nativos passam direto para o input: as validações que o
// backend já aplica (tamanho, mínimo, data máxima) são declaradas em cada
// uso, sem este componente precisar conhecê-las.
type Props = InputHTMLAttributes<HTMLInputElement> & {
  rotulo: string
  dica?: string
}

export function Campo({ rotulo, dica, id, ...atributos }: Props) {
  const idGerado = useId()
  const idDoCampo = id ?? idGerado
  const idDaDica = `${idDoCampo}-dica`

  return (
    <div className={estilos.campo}>
      <label className={estilos.rotulo} htmlFor={idDoCampo}>
        {rotulo}
      </label>

      {/* A dica fica em aria-describedby, e não dentro do label: aninhada,
          ela entraria no nome do campo e o leitor de tela anunciaria
          "Plataforma Instagram, TikTok, YouTube" como se fosse o rótulo. */}
      <input
        className={estilos.entrada}
        id={idDoCampo}
        aria-describedby={dica === undefined ? undefined : idDaDica}
        {...atributos}
      />

      {dica !== undefined && (
        <span className={estilos.dica} id={idDaDica}>
          {dica}
        </span>
      )}
    </div>
  )
}
