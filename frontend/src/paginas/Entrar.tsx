import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { ErroDaApi } from '../api/cliente'
import { usarAutenticacao } from '../autenticacao/usarAutenticacao'
import { Campo } from '../componentes/Campo'
import estilos from './Formulario.module.css'

export function Entrar() {
  const { entrarNaConta, sessaoExpirada } = usarAutenticacao()
  const navegar = useNavigate()

  const [email, definirEmail] = useState('')
  const [senha, definirSenha] = useState('')
  const [erro, definirErro] = useState<string | null>(null)
  const [enviando, definirEnviando] = useState(false)

  async function aoEnviar(evento: FormEvent) {
    evento.preventDefault()
    definirErro(null)
    definirEnviando(true)

    try {
      await entrarNaConta(email, senha)
      navegar('/painel', { replace: true })
    } catch (falha) {
      definirErro(
        falha instanceof ErroDaApi
          ? falha.message
          : 'Não foi possível entrar.',
      )
      definirEnviando(false)
    }
  }

  return (
    <main className={estilos.pagina}>
      <form className={estilos.cartao} onSubmit={aoEnviar}>
        <h1 className={estilos.titulo}>Entrar no MetricaMEI</h1>
        <p className={estilos.subtitulo}>
          Acompanhe o desempenho dos seus conteúdos.
        </p>

        {sessaoExpirada && erro === null && (
          <p className={estilos.aviso} role="status">
            Sua sessão expirou. Entre novamente para continuar.
          </p>
        )}

        {erro !== null && (
          <p className={estilos.erro} role="alert">
            {erro}
          </p>
        )}

        <Campo
          rotulo="E-mail"
          type="email"
          name="email"
          autoComplete="email"
          required
          value={email}
          onChange={(evento) => definirEmail(evento.target.value)}
        />

        <Campo
          rotulo="Senha"
          type="password"
          name="senha"
          autoComplete="current-password"
          required
          value={senha}
          onChange={(evento) => definirSenha(evento.target.value)}
        />

        <button className={estilos.botao} type="submit" disabled={enviando}>
          {enviando ? 'Entrando…' : 'Entrar'}
        </button>

        <p className={estilos.alternativa}>
          Ainda não tem conta? <Link to="/cadastrar">Cadastre-se</Link>
        </p>
      </form>
    </main>
  )
}
