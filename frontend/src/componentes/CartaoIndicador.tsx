import estilos from './CartaoIndicador.module.css'

type Props = {
  rotulo: string
  valor: string
  observacao?: string
  destacado?: boolean
}

export function CartaoIndicador({
  rotulo,
  valor,
  observacao,
  destacado = false,
}: Props) {
  const classes = destacado
    ? `${estilos.cartao} ${estilos.destacado}`
    : estilos.cartao

  return (
    <article className={classes}>
      <p className={estilos.rotulo}>{rotulo}</p>
      <p className={estilos.valor}>{valor}</p>
      {observacao !== undefined && (
        <p className={estilos.observacao}>{observacao}</p>
      )}
    </article>
  )
}
