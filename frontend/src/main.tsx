import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import { App } from './App'
import { ProvedorAutenticacao } from './autenticacao/ProvedorAutenticacao'
import { BarreiraDeErro } from './componentes/BarreiraDeErro'
import './estilos/globais.css'

// A barreira envolve o provedor, e não só o App, porque o provedor lê o
// localStorage durante a renderização. Num navegador com dados de site
// bloqueados essa leitura levanta, e a tela ficava em branco sem nenhuma
// explicação.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BarreiraDeErro>
      <BrowserRouter>
        <ProvedorAutenticacao>
          <App />
        </ProvedorAutenticacao>
      </BrowserRouter>
    </BarreiraDeErro>
  </StrictMode>,
)
