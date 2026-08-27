import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ErroDaApi } from '../api/cliente'
import {
  atualizarConteudo,
  buscarConteudo,
  excluirConteudo,
} from '../api/conteudos'
import {
  atualizarMetrica,
  criarMetrica,
  excluirMetrica,
  listarMetricas,
} from '../api/metricas'
import type { Conteudo, Metrica } from '../api/tipos'
import { useAutenticacao } from '../autenticacao/useAutenticacao'
import { EvolucaoDoEngajamento } from '../componentes/EvolucaoDoEngajamento'
import { dataDeHoje } from '../formatacao'
import estilos from './ConteudoDetalhe.module.css'
import { FormularioDaMedicao } from './detalhe/FormularioDaMedicao'
import type { DadosDaMedicao } from './detalhe/FormularioDaMedicao'
import { FormularioDoConteudo } from './detalhe/FormularioDoConteudo'
import type { DadosEditaveis } from './detalhe/FormularioDoConteudo'
import { TabelaDeMedicoes } from './detalhe/TabelaDeMedicoes'

const MEDICAO_VAZIA: DadosDaMedicao = {
  visualizacoes: '0',
  curtidas: '0',
  comentarios: '0',
  compartilhamentos: '0',
  alcance: '0',
  data_referencia: dataDeHoje(),
}

const CONTEUDO_VAZIO: DadosEditaveis = {
  titulo: '',
  plataforma: '',
  tipo: '',
  data_publicacao: '',
  url_publicacao: '',
}

function mensagemDe(falha: unknown, alternativa: string): string {
  return falha instanceof ErroDaApi ? falha.message : alternativa
}

// Campo em branco significa remover a URL, e o backend recusa texto vazio:
// null é como ele entende a remoção.
function urlOuNulo(valor: string): string | null {
  return valor.trim() === '' ? null : valor
}

export function ConteudoDetalhe() {
  const { token } = useAutenticacao()
  const { conteudoId } = useParams()
  const navegar = useNavigate()

  const identificador = Number(conteudoId)

  const [conteudo, definirConteudo] = useState<Conteudo | null>(null)
  const [metricas, definirMetricas] = useState<Metrica[] | null>(null)
  const [erro, definirErro] = useState<string | null>(null)
  const [enviando, definirEnviando] = useState(false)

  const [dadosDoConteudo, definirDadosDoConteudo] = useState(CONTEUDO_VAZIO)
  const [confirmandoExclusao, definirConfirmandoExclusao] = useState(false)

  const [medicao, definirMedicao] = useState(MEDICAO_VAZIA)
  const [formularioAberto, definirFormularioAberto] = useState(false)
  const [medicaoEmEdicao, definirMedicaoEmEdicao] = useState<number | null>(
    null,
  )
  const [medicaoConfirmada, definirMedicaoConfirmada] = useState<
    number | null
  >(null)

  const carregar = useCallback(async () => {
    if (token === null) {
      return
    }

    try {
      const encontrado = await buscarConteudo(token, identificador)

      definirConteudo(encontrado)
      definirDadosDoConteudo({
        titulo: encontrado.titulo,
        plataforma: encontrado.plataforma,
        tipo: encontrado.tipo,
        data_publicacao: encontrado.data_publicacao,
        url_publicacao: encontrado.url_publicacao ?? '',
      })
      definirMetricas(await listarMetricas(token, identificador))
    } catch (falha) {
      // Conteúdo inexistente ou de outro usuário não tem tela própria: a
      // lista é o único lugar coerente para devolver o usuário.
      if (falha instanceof ErroDaApi && falha.status === 404) {
        navegar('/conteudos', { replace: true })
        return
      }

      definirErro(mensagemDe(falha, 'Não foi possível carregar o conteúdo.'))
    }
  }, [token, identificador, navegar])

  useEffect(() => {
    void carregar()
  }, [carregar])

  async function salvarConteudo(evento: FormEvent) {
    evento.preventDefault()

    if (token === null) {
      return
    }

    definirErro(null)
    definirEnviando(true)

    try {
      await atualizarConteudo(token, identificador, {
        ...dadosDoConteudo,
        url_publicacao: urlOuNulo(dadosDoConteudo.url_publicacao),
      })

      await carregar()
    } catch (falha) {
      definirErro(mensagemDe(falha, 'Não foi possível salvar o conteúdo.'))
    } finally {
      definirEnviando(false)
    }
  }

  async function removerConteudo() {
    if (token === null) {
      return
    }

    try {
      await excluirConteudo(token, identificador)
      navegar('/conteudos', { replace: true })
    } catch (falha) {
      definirErro(mensagemDe(falha, 'Não foi possível excluir o conteúdo.'))
    }
  }

  function abrirNovaMedicao() {
    definirMedicaoEmEdicao(null)
    definirMedicao(MEDICAO_VAZIA)
    definirFormularioAberto(true)
  }

  function abrirEdicaoDaMedicao(metrica: Metrica) {
    definirMedicaoEmEdicao(metrica.id)
    definirMedicao({
      visualizacoes: String(metrica.visualizacoes),
      curtidas: String(metrica.curtidas),
      comentarios: String(metrica.comentarios),
      compartilhamentos: String(metrica.compartilhamentos),
      alcance: String(metrica.alcance),
      data_referencia: metrica.data_referencia,
    })
    definirFormularioAberto(true)
  }

  async function salvarMedicao(evento: FormEvent) {
    evento.preventDefault()

    if (token === null) {
      return
    }

    definirErro(null)
    definirEnviando(true)

    const dados = {
      visualizacoes: Number(medicao.visualizacoes),
      curtidas: Number(medicao.curtidas),
      comentarios: Number(medicao.comentarios),
      compartilhamentos: Number(medicao.compartilhamentos),
      alcance: Number(medicao.alcance),
      data_referencia: medicao.data_referencia,
    }

    try {
      if (medicaoEmEdicao === null) {
        await criarMetrica(token, identificador, dados)
      } else {
        await atualizarMetrica(token, identificador, medicaoEmEdicao, dados)
      }

      definirFormularioAberto(false)
      await carregar()
    } catch (falha) {
      // A unicidade por data é o erro que o usuário mais encontra, e a
      // mensagem genérica não diria o que fazer a respeito.
      if (falha instanceof ErroDaApi && falha.status === 409) {
        definirErro(
          'Já existe uma medição deste conteúdo nesta data. Edite a medição existente ou escolha outra data.',
        )
      } else {
        definirErro(mensagemDe(falha, 'Não foi possível salvar a medição.'))
      }
    } finally {
      definirEnviando(false)
    }
  }

  async function removerMedicao(metricaId: number) {
    if (token === null) {
      return
    }

    try {
      await excluirMetrica(token, identificador, metricaId)
      definirMedicaoConfirmada(null)
      await carregar()
    } catch (falha) {
      definirErro(mensagemDe(falha, 'Não foi possível excluir a medição.'))
    }
  }

  function confirmarOuRemoverMedicao(metricaId: number) {
    if (medicaoConfirmada === metricaId) {
      void removerMedicao(metricaId)
      return
    }

    definirMedicaoConfirmada(metricaId)
  }

  function alterarMedicao(campo: keyof DadosDaMedicao, valor: string) {
    definirMedicao((atual) => ({ ...atual, [campo]: valor }))
  }

  function alterarConteudo(campo: keyof DadosEditaveis, valor: string) {
    definirDadosDoConteudo((atual) => ({ ...atual, [campo]: valor }))
  }

  if (conteudo === null) {
    return (
      <main className={estilos.pagina}>
        {erro === null ? (
          <p>Carregando…</p>
        ) : (
          <p className={estilos.erro} role="alert">
            {erro}
          </p>
        )}
      </main>
    )
  }

  return (
    <main className={estilos.pagina}>
      <Link className={estilos.voltar} to="/conteudos">
        &larr; Meus conteúdos
      </Link>

      <header className={estilos.cabecalho}>
        <h1 className={estilos.titulo}>{conteudo.titulo}</h1>

        <button
          className={`${estilos.acao} ${
            confirmandoExclusao ? estilos.confirmando : estilos.perigo
          }`}
          type="button"
          onClick={() =>
            confirmandoExclusao
              ? void removerConteudo()
              : definirConfirmandoExclusao(true)
          }
        >
          {confirmandoExclusao ? 'Confirmar exclusão' : 'Excluir conteúdo'}
        </button>
      </header>

      {erro !== null && (
        <p className={estilos.erro} role="alert">
          {erro}
        </p>
      )}

      <FormularioDoConteudo
        dados={dadosDoConteudo}
        enviando={enviando}
        aoAlterar={alterarConteudo}
        aoEnviar={salvarConteudo}
      />

      <h2 className={estilos.secao}>Medições</h2>

      {!formularioAberto && (
        <div className={estilos.botoes}>
          <button
            className={estilos.acao}
            type="button"
            onClick={abrirNovaMedicao}
          >
            Registrar medição
          </button>
        </div>
      )}

      {formularioAberto && (
        <FormularioDaMedicao
          dados={medicao}
          enviando={enviando}
          dataDaPublicacao={conteudo.data_publicacao}
          aoAlterar={alterarMedicao}
          aoEnviar={salvarMedicao}
          aoCancelar={() => definirFormularioAberto(false)}
        />
      )}

      {metricas !== null && metricas.length === 0 && (
        <p className={estilos.vazio}>
          Nenhuma medição registrada. Cada medição é um retrato acumulado do
          desempenho numa data.
        </p>
      )}

      {metricas !== null && metricas.length > 0 && (
        <>
          <EvolucaoDoEngajamento metricas={metricas} />

          <TabelaDeMedicoes
            metricas={metricas}
            metricaConfirmada={medicaoConfirmada}
            aoEditar={abrirEdicaoDaMedicao}
            aoExcluir={confirmarOuRemoverMedicao}
          />
        </>
      )}
    </main>
  )
}
