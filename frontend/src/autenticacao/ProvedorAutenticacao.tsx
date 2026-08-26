import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import {
  buscarUsuarioAtual,
  cadastrar,
  entrar,
} from '../api/autenticacao'
import { registrarPerdaDeSessao } from '../api/cliente'
import type { Usuario } from '../api/tipos'
import { ContextoAutenticacao } from './contexto'

const CHAVE_DO_TOKEN = 'metricamei.token'

type Props = {
  children: ReactNode
}

export function ProvedorAutenticacao({ children }: Props) {
  const [token, definirToken] = useState<string | null>(() =>
    localStorage.getItem(CHAVE_DO_TOKEN),
  )
  const [usuario, definirUsuario] = useState<Usuario | null>(null)
  const [verificando, definirVerificando] = useState(true)
  const [sessaoExpirada, definirSessaoExpirada] = useState(false)

  const encerrarSessao = useCallback(() => {
    localStorage.removeItem(CHAVE_DO_TOKEN)
    definirToken(null)
    definirUsuario(null)
    definirVerificando(false)
  }, [])

  useEffect(() => {
    // O cliente HTTP avisa quando qualquer requisição volta 401, porque o
    // token pode vencer com a tela já aberta e não há outro momento em que
    // a aplicação descubra isso.
    registrarPerdaDeSessao(() => {
      definirSessaoExpirada(true)
      encerrarSessao()
    })

    return () => {
      registrarPerdaDeSessao(null)
    }
  }, [encerrarSessao])

  useEffect(() => {
    if (token === null) {
      definirUsuario(null)
      definirVerificando(false)
      return
    }

    let cancelado = false

    // O token expira em 30 minutos, então o guardado pode estar vencido. Só
    // o backend sabe dizer, e perguntar aqui evita que a aplicação abra o
    // painel para quem já perdeu a sessão.
    buscarUsuarioAtual(token)
      .then((encontrado) => {
        if (cancelado) {
          return
        }

        definirUsuario(encontrado)
        definirVerificando(false)
      })
      .catch(() => {
        if (!cancelado) {
          encerrarSessao()
        }
      })

    return () => {
      cancelado = true
    }
  }, [token, encerrarSessao])

  const guardarToken = useCallback((novoToken: string) => {
    localStorage.setItem(CHAVE_DO_TOKEN, novoToken)
    definirSessaoExpirada(false)
    definirVerificando(true)
    definirToken(novoToken)
  }, [])

  const entrarNaConta = useCallback(
    async (email: string, senha: string) => {
      const resposta = await entrar(email, senha)
      guardarToken(resposta.access_token)
    },
    [guardarToken],
  )

  const criarConta = useCallback(
    async (nome: string, email: string, senha: string) => {
      await cadastrar(nome, email, senha)

      // O cadastro não devolve token, então a sessão só começa depois do
      // login. Fazer os dois aqui poupa o usuário de digitar de novo.
      const resposta = await entrar(email, senha)
      guardarToken(resposta.access_token)
    },
    [guardarToken],
  )

  const sair = useCallback(() => {
    // Saída deliberada não é sessão vencida: a tela de login não deve
    // acusar expiração para quem clicou em "Sair".
    definirSessaoExpirada(false)
    encerrarSessao()
  }, [encerrarSessao])

  const valor = useMemo(
    () => ({
      token,
      usuario,
      verificando,
      sessaoExpirada,
      criarConta,
      entrarNaConta,
      sair,
    }),
    [
      token,
      usuario,
      verificando,
      sessaoExpirada,
      criarConta,
      entrarNaConta,
      sair,
    ],
  )

  return (
    <ContextoAutenticacao.Provider value={valor}>
      {children}
    </ContextoAutenticacao.Provider>
  )
}
