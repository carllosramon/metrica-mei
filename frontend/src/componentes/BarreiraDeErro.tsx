import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'

import estilos from './BarreiraDeErro.module.css'

type Props = {
  children: ReactNode
}

type Estado = {
  falha: Error | null
}

// Precisa ser classe: capturar erro de renderização é a única coisa que
// os hooks ainda não fazem.
export class BarreiraDeErro extends Component<Props, Estado> {
  state: Estado = { falha: null }

  static getDerivedStateFromError(falha: Error): Estado {
    return { falha }
  }

  componentDidCatch(falha: Error, info: ErrorInfo): void {
    // Sem isto, o React só reporta que houve um erro. O console é o que
    // temos de registro enquanto o projeto não tem coleta de telemetria.
    console.error('Falha na renderização', falha, info.componentStack)
  }

  render(): ReactNode {
    if (this.state.falha === null) {
      return this.props.children
    }

    return (
      <main className={estilos.pagina}>
        <h1 className={estilos.titulo}>Algo deu errado nesta tela</h1>

        <p className={estilos.texto}>
          Os seus conteúdos e medições continuam gravados, nada se perdeu.
          Recarregar a página costuma resolver.
        </p>

        <button
          className={estilos.acao}
          type="button"
          onClick={() => window.location.reload()}
        >
          Recarregar a página
        </button>

        <details className={estilos.detalhe}>
          <summary>Detalhes técnicos</summary>
          <p className={estilos.mensagem}>{this.state.falha.message}</p>
        </details>
      </main>
    )
  }
}
