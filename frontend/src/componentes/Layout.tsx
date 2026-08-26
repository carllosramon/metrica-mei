import { Outlet } from 'react-router-dom'

import { Navegacao } from './Navegacao'

export function Layout() {
  return (
    <>
      <Navegacao />
      <Outlet />
    </>
  )
}
