import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { criarConteudo, listarConteudos } from '../api/conteudos'
import { mensagemDe } from '../api/falhas'
import type { ConteudoDaLista } from '../api/tipos'
import { useAutenticacao } from '../autenticacao/useAutenticacao'
import { reservarPedido } from '../carregamento'
import { Campo } from '../componentes/Campo'
import { dataDeHoje, formatarData } from '../formatacao'
import estilos from './Conteudos.module.css'
import { urlOuNulo } from './formularios'

type DadosDoFormulario = {
  titulo: string
  plataforma: string
  tipo: string
  data_publicacao: string
  url_publicacao: string
}

// A data padrão é calculada na hora de abrir o formulário. Calculada no
// carregamento do módulo, numa aba aberta depois da meia-noite ela ficava
// em ontem.
function formularioVazio(): DadosDoFormulario {
  return {
    titulo: '',
    plataforma: '',
    tipo: '',
    data_publicacao: dataDeHoje(),
    url_publicacao: '',
  }
}

export function Conteudos() {
  const { token } = useAutenticacao()

  const [conteudos, definirConteudos] = useState<ConteudoDaLista[] | null>(null)

  // Dois erros, porque a tela distingue "a lista não veio" de "o cadastro
  // não passou". Com um estado só, limpar o erro ao cadastrar apagava
  // também a falha de carga, e a lista, que continuava nula, voltava a
  // dizer "Carregando…" para sempre.
  const [erroDeCarga, definirErroDeCarga] = useState<string | null>(null)
  const [erroDoFormulario, definirErroDoFormulario] = useState<string | null>(
    null,
  )
  const [formularioAberto, definirFormularioAberto] = useState(false)
  const [formulario, definirFormulario] = useState(formularioVazio)
  const [enviando, definirEnviando] = useState(false)

  // A carga inicial lenta podia responder depois da recarga que segue um
  // cadastro e apagar da tela o conteúdo recém-criado. Com o contador, a
  // última carga pedida é a única que escreve.
  const pedidoDeCarga = useRef(0)

  const carregar = useCallback(async () => {
    if (token === null) {
      return
    }

    const aindaVale = reservarPedido(pedidoDeCarga)

    try {
      const encontrados = await listarConteudos(token)

      if (aindaVale()) {
        definirConteudos(encontrados)
        definirErroDeCarga(null)
      }
    } catch (falha) {
      if (!aindaVale()) {
        return
      }

      definirErroDeCarga(
        mensagemDe(falha, 'Não foi possível carregar os conteúdos.'),
      )
    }
  }, [token])

  useEffect(() => {
    void carregar()
  }, [carregar])

  function alterar(campo: keyof DadosDoFormulario, valor: string) {
    definirFormulario((atual) => ({ ...atual, [campo]: valor }))
  }

  function abrirFormulario() {
    definirErroDoFormulario(null)
    // O formulário é recomposto ao abrir, e não só ao fechar. Inicializado
    // uma vez na montagem, a data padrão era a de quando a página carregou:
    // numa aba aberta às 23h50, o conteúdo cadastrado depois da meia-noite
    // nascia com a data de ontem, que ainda vira o mínimo de todas as
    // medições dele.
    definirFormulario(formularioVazio())
    definirFormularioAberto(true)
  }

  function fecharFormulario() {
    definirErroDoFormulario(null)
    definirFormularioAberto(false)
    definirFormulario(formularioVazio())
  }

  async function aoEnviar(evento: FormEvent) {
    evento.preventDefault()

    if (token === null) {
      return
    }

    definirErroDoFormulario(null)
    definirEnviando(true)

    try {
      await criarConteudo(token, {
        titulo: formulario.titulo,
        plataforma: formulario.plataforma,
        tipo: formulario.tipo,
        data_publicacao: formulario.data_publicacao,
        url_publicacao: urlOuNulo(formulario.url_publicacao),
      })

      fecharFormulario()
      await carregar()
    } catch (falha) {
      definirErroDoFormulario(
        mensagemDe(falha, 'Não foi possível cadastrar o conteúdo.'),
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
            onClick={abrirFormulario}
          >
            Novo conteúdo
          </button>
        )}
      </header>

      {erroDeCarga !== null && (
        <p className={estilos.erro} role="alert">
          {erroDeCarga}
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
            dica="Opcional. Endereço completo da publicação, começando com http:// ou https://"
          />

          {/* Junto dos botões, como na tela de detalhe. No topo da página
              o aviso ficava acima do formulário inteiro, longe do clique
              que o produziu. */}
          {erroDoFormulario !== null && (
            <p className={estilos.erro} role="alert">
              {erroDoFormulario}
            </p>
          )}

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

      {conteudos === null && erroDeCarga === null && <p>Carregando…</p>}

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
                <th scope="col">Última medição</th>
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
                  {/* A coluna é o que responde "o que eu esqueci de
                      medir" sem abrir um conteúdo por vez. */}
                  <td>
                    {conteudo.ultima_medicao === null ? (
                      <span className={estilos.nuncaMedido}>
                        nunca medido
                      </span>
                    ) : (
                      formatarData(conteudo.ultima_medicao)
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}
