import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import {
  buscarUsuarioAtual,
  cadastrar,
  entrar,
} from '../api/autenticacao'
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
        if (cancelado) {
          return
        }

        localStorage.removeItem(CHAVE_DO_TOKEN)
        definirToken(null)
        definirUsuario(null)
        definirVerificando(false)
      })

    return () => {
      cancelado = true
    }
  }, [token])

  const guardarToken = useCallback((novoToken: string) => {
    localStorage.setItem(CHAVE_DO_TOKEN, novoToken)
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
    localStorage.removeItem(CHAVE_DO_TOKEN)
    definirToken(null)
    definirUsuario(null)
    definirVerificando(false)
  }, [])

  const valor = useMemo(
    () => ({
      token,
      usuario,
      verificando,
      criarConta,
      entrarNaConta,
      sair,
    }),
    [token, usuario, verificando, criarConta, entrarNaConta, sair],
  )

  return (
    <ContextoAutenticacao.Provider value={valor}>
      {children}
    </ContextoAutenticacao.Provider>
  )
}
