import { NavLink } from 'react-router-dom'

import { useAutenticacao } from '../autenticacao/useAutenticacao'
import estilos from './Navegacao.module.css'

function classeDoLink({ isActive }: { isActive: boolean }): string {
  return isActive
    ? `${estilos.link} ${estilos.ativo}`
    : estilos.link
}

export function Navegacao() {
  const { usuario, sair } = useAutenticacao()

  return (
    <header className={estilos.barra}>
      <nav className={estilos.links}>
        <NavLink to="/painel" className={classeDoLink}>
          Painel
        </NavLink>
        <NavLink to="/conteudos" className={classeDoLink}>
          Conteúdos
        </NavLink>
      </nav>

      <div className={estilos.conta}>
        {usuario !== null && (
          <span className={estilos.nome}>{usuario.nome}</span>
        )}
        <button className={estilos.sair} type="button" onClick={sair}>
          Sair
        </button>
      </div>
    </header>
  )
}
