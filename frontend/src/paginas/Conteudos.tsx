import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { ErroDaApi } from '../api/cliente'
import { criarConteudo, listarConteudos } from '../api/conteudos'
import type { Conteudo } from '../api/tipos'
import { usarAutenticacao } from '../autenticacao/usarAutenticacao'
import { Campo } from '../componentes/Campo'
import { dataDeHoje, formatarData } from '../formatacao'
import estilos from './Conteudos.module.css'

const FORMULARIO_VAZIO = {
  titulo: '',
  plataforma: '',
  tipo: '',
  data_publicacao: dataDeHoje(),
  url_publicacao: '',
}

export function Conteudos() {
  const { token } = usarAutenticacao()

  const [conteudos, definirConteudos] = useState<Conteudo[] | null>(null)
  const [erro, definirErro] = useState<string | null>(null)
  const [formularioAberto, definirFormularioAberto] = useState(false)
  const [formulario, definirFormulario] = useState(FORMULARIO_VAZIO)
  const [enviando, definirEnviando] = useState(false)

  const carregar = useCallback(async () => {
    if (token === null) {
      return
    }

    try {
      definirConteudos(await listarConteudos(token))
    } catch (falha) {
      definirErro(
        falha instanceof ErroDaApi
          ? falha.message
          : 'Não foi possível carregar os conteúdos.',
      )
    }
  }, [token])

  useEffect(() => {
    void carregar()
  }, [carregar])

  function alterar(campo: keyof typeof FORMULARIO_VAZIO, valor: string) {
    definirFormulario((atual) => ({ ...atual, [campo]: valor }))
  }

  function fecharFormulario() {
    definirFormularioAberto(false)
    definirFormulario(FORMULARIO_VAZIO)
  }

  async function aoEnviar(evento: FormEvent) {
    evento.preventDefault()

    if (token === null) {
      return
    }

    definirErro(null)
    definirEnviando(true)

    try {
      await criarConteudo(token, {
        titulo: formulario.titulo,
        plataforma: formulario.plataforma,
        tipo: formulario.tipo,
        data_publicacao: formulario.data_publicacao,
        // O backend recusa texto vazio, e campo em branco significa que o
        // usuário não quis informar a URL.
        url_publicacao:
          formulario.url_publicacao.trim() === ''
            ? null
            : formulario.url_publicacao,
      })

      fecharFormulario()
      await carregar()
    } catch (falha) {
      definirErro(
        falha instanceof ErroDaApi
          ? falha.message
          : 'Não foi possível cadastrar o conteúdo.',
      )
    } finally {
      definirEnviando(false)
    }
  }

  return (
    <main className={estilos.pagina}>
      <header className={estilos.cabecalho}>
        <h1 className={estilos.titulo}>Meus conteúdos</h1>

        {!formularioAberto && (
          <button
            className={estilos.acao}
            type="button"
            onClick={() => definirFormularioAberto(true)}
          >
            Novo conteúdo
          </button>
        )}
      </header>

      {erro !== null && (
        <p className={estilos.erro} role="alert">
          {erro}
        </p>
      )}

      {formularioAberto && (
        <form className={estilos.formulario} onSubmit={aoEnviar}>
          <Campo
            rotulo="Título"
            value={formulario.titulo}
            onChange={(evento) => alterar('titulo', evento.target.value)}
            required
            maxLength={200}
          />

          <div className={estilos.linhaDeCampos}>
            <Campo
              rotulo="Plataforma"
              value={formulario.plataforma}
              onChange={(evento) =>
                alterar('plataforma', evento.target.value)
              }
              required
              maxLength={50}
              dica="Instagram, TikTok, YouTube…"
            />
            <Campo
              rotulo="Tipo"
              value={formulario.tipo}
              onChange={(evento) => alterar('tipo', evento.target.value)}
              required
              maxLength={50}
              dica="Reels, Carrossel, Vídeo…"
            />
            <Campo
              rotulo="Data de publicação"
              type="date"
              value={formulario.data_publicacao}
              onChange={(evento) =>
                alterar('data_publicacao', evento.target.value)
              }
              required
              max={dataDeHoje()}
            />
          </div>

          <Campo
            rotulo="URL da publicação"
            type="url"
            value={formulario.url_publicacao}
            onChange={(evento) =>
              alterar('url_publicacao', evento.target.value)
            }
            maxLength={500}
            dica="Opcional. Precisa começar com http:// ou https://"
          />

          <div className={estilos.botoes}>
            <button
              className={estilos.acao}
              type="submit"
              disabled={enviando}
            >
              {enviando ? 'Salvando…' : 'Salvar'}
            </button>
            <button
              className={`${estilos.acao} ${estilos.secundario}`}
              type="button"
              onClick={fecharFormulario}
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      {conteudos === null && erro === null && <p>Carregando…</p>}

      {conteudos !== null && conteudos.length === 0 && (
        <p className={estilos.vazio}>
          Nenhum conteúdo cadastrado ainda. Comece registrando a sua
          primeira publicação.
        </p>
      )}

      {conteudos !== null && conteudos.length > 0 && (
        <div className={estilos.moldura}>
          <table className={estilos.tabela}>
            <thead>
              <tr>
                <th scope="col">Título</th>
                <th scope="col">Plataforma</th>
                <th scope="col">Tipo</th>
                <th scope="col">Publicação</th>
              </tr>
            </thead>
            <tbody>
              {conteudos.map((conteudo) => (
                <tr key={conteudo.id}>
                  <td>
                    <Link to={`/conteudos/${conteudo.id}`}>
                      {conteudo.titulo}
                    </Link>
                  </td>
                  <td>{conteudo.plataforma}</td>
                  <td>{conteudo.tipo}</td>
                  <td>{formatarData(conteudo.data_publicacao)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}
