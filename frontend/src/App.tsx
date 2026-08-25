import { Navigate, Route, Routes } from 'react-router-dom'

import { RotaProtegida } from './autenticacao/RotaProtegida'
import { Cadastrar } from './paginas/Cadastrar'
import { Entrar } from './paginas/Entrar'
import { Painel } from './paginas/Painel'

export function App() {
  return (
    <Routes>
      <Route path="/entrar" element={<Entrar />} />
      <Route path="/cadastrar" element={<Cadastrar />} />
      <Route
        path="/painel"
        element={
          <RotaProtegida>
            <Painel />
          </RotaProtegida>
        }
      />
      {/* Qualquer outro endereço cai no painel, que redireciona para o
          login quando não há sessão. */}
      <Route path="*" element={<Navigate to="/painel" replace />} />
    </Routes>
  )
}
