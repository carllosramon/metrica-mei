import { Navigate, Route, Routes } from 'react-router-dom'

import { RotaProtegida } from './autenticacao/RotaProtegida'
import { Layout } from './componentes/Layout'
import { Cadastrar } from './paginas/Cadastrar'
import { ConteudoDetalhe } from './paginas/ConteudoDetalhe'
import { Conteudos } from './paginas/Conteudos'
import { Entrar } from './paginas/Entrar'
import { Painel } from './paginas/Painel'

export function App() {
  return (
    <Routes>
      <Route path="/entrar" element={<Entrar />} />
      <Route path="/cadastrar" element={<Cadastrar />} />

      {/* As rotas autenticadas compartilham a barra de navegação, então a
          proteção e o layout ficam no elemento pai. */}
      <Route
        element={
          <RotaProtegida>
            <Layout />
          </RotaProtegida>
        }
      >
        <Route path="/painel" element={<Painel />} />
        <Route path="/conteudos" element={<Conteudos />} />
        <Route
          path="/conteudos/:conteudoId"
          element={<ConteudoDetalhe />}
        />
      </Route>

      {/* Qualquer outro endereço cai no painel, que redireciona para o
          login quando não há sessão. */}
      <Route path="*" element={<Navigate to="/painel" replace />} />
    </Routes>
  )
}
