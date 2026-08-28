import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { ErroDaApi } from '../api/cliente'
import { useAutenticacao } from '../autenticacao/useAutenticacao'
import { Campo } from '../componentes/Campo'
import estilos from './Formulario.module.css'

const TAMANHO_MINIMO_DA_SENHA = 8

export function Cadastrar() {
  const { criarConta } = useAutenticacao()
  const navegar = useNavigate()

  const [nome, definirNome] = useState('')
  const [email, definirEmail] = useState('')
  const [senha, definirSenha] = useState('')
  const [erro, definirErro] = useState<string | null>(null)
  const [enviando, definirEnviando] = useState(false)

  async function aoEnviar(evento: FormEvent) {
    evento.preventDefault()
    definirErro(null)
    definirEnviando(true)

    try {
      await criarConta(nome, email, senha)
      navegar('/painel', { replace: true })
    } catch (falha) {
      definirErro(
        falha instanceof ErroDaApi
          ? falha.message
          : 'Não foi possível criar a conta.',
      )
      definirEnviando(false)
    }
  }

  return (
    <main className={estilos.pagina}>
      <form className={estilos.cartao} onSubmit={aoEnviar}>
        <h1 className={estilos.titulo}>Criar conta</h1>
        <p className={estilos.subtitulo}>
          Comece a medir o retorno das suas publicações.
        </p>

        {erro !== null && (
          <p className={estilos.erro} role="alert">
            {erro}
          </p>
        )}

        <Campo
          rotulo="Nome"
          type="text"
          name="nome"
          autoComplete="name"
          required
          minLength={2}
          value={nome}
          onChange={(evento) => definirNome(evento.target.value)}
        />

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
          autoComplete="new-password"
          required
          // O backend recusa senha com menos de 8 caracteres; avisar aqui
          // evita uma ida ao servidor para descobrir isso.
          minLength={TAMANHO_MINIMO_DA_SENHA}
          value={senha}
          onChange={(evento) => definirSenha(evento.target.value)}
        />

        <button className={estilos.botao} type="submit" disabled={enviando}>
          {enviando ? 'Criando…' : 'Criar conta'}
        </button>

        <p className={estilos.alternativa}>
          Já tem conta? <Link to="/entrar">Entrar</Link>
        </p>
      </form>
    </main>
  )
}
