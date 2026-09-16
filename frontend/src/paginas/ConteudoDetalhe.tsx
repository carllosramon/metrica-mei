import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ErroDaApi } from '../api/cliente'
import {
  atualizarConteudo,
  buscarConteudo,
  excluirConteudo,
} from '../api/conteudos'
import { mensagemDe } from '../api/falhas'
import {
  atualizarMetrica,
  criarMetrica,
  excluirMetrica,
  listarMetricas,
} from '../api/metricas'
import type { Conteudo, Metrica } from '../api/tipos'
import { useAutenticacao } from '../autenticacao/useAutenticacao'
import { reservarPedido } from '../carregamento'
import { EvolucaoDoEngajamento } from '../componentes/EvolucaoDoEngajamento'
import { dataDeHoje } from '../formatacao'
import estilos from './ConteudoDetalhe.module.css'
import { FormularioDaMedicao } from './detalhe/FormularioDaMedicao'
import type { DadosDaMedicao } from './detalhe/FormularioDaMedicao'
import { FormularioDoConteudo } from './detalhe/FormularioDoConteudo'
import type { DadosEditaveis } from './detalhe/FormularioDoConteudo'
import { TabelaDeMedicoes } from './detalhe/TabelaDeMedicoes'
import { inteiroDigitado, urlOuNulo } from './formularios'

// A data padrão é calculada na hora de abrir o formulário. Calculada no
// carregamento do módulo, numa aba aberta depois da meia-noite ela ficava
// em ontem, e a medição era salva no dia errado.
function medicaoVazia(): DadosDaMedicao {
  return {
    visualizacoes: '0',
    curtidas: '0',
    comentarios: '0',
    compartilhamentos: '0',
    alcance: '0',
    data_referencia: dataDeHoje(),
  }
}

const CONTEUDO_VAZIO: DadosEditaveis = {
  titulo: '',
  plataforma: '',
  tipo: '',
  data_publicacao: '',
  url_publicacao: '',
}

export function ConteudoDetalhe() {
  const { token } = useAutenticacao()
  const { conteudoId } = useParams()
  const navegar = useNavigate()

  const identificador = Number(conteudoId)

  // Endereço como /conteudos/abc viraria GET /conteudos/NaN, um 422 com a
  // mensagem do Pydantic em inglês na tela. A lista é o destino certo.
  const identificadorValido =
    Number.isInteger(identificador) && identificador > 0

  useEffect(() => {
    if (!identificadorValido) {
      navegar('/conteudos', { replace: true })
    }
  }, [identificadorValido, navegar])

  const [conteudo, definirConteudo] = useState<Conteudo | null>(null)
  const [metricas, definirMetricas] = useState<Metrica[] | null>(null)
  const [erro, definirErro] = useState<string | null>(null)
  const [enviando, definirEnviando] = useState(false)

  const [dadosDoConteudo, definirDadosDoConteudo] = useState(CONTEUDO_VAZIO)
  const [confirmandoExclusao, definirConfirmandoExclusao] = useState(false)

  const [medicao, definirMedicao] = useState(medicaoVazia)
  const [formularioAberto, definirFormularioAberto] = useState(false)
  const [medicaoEmEdicao, definirMedicaoEmEdicao] = useState<number | null>(
    null,
  )
  const [medicaoConfirmada, definirMedicaoConfirmada] = useState<
    number | null
  >(null)

  const areaDoFormulario = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!formularioAberto) {
      return
    }

    // O formulário abre acima do gráfico e da tabela, então quem clicou
    // numa linha lá embaixo não via nada acontecer. A rolagem e o foco
    // levam a pessoa até onde a ação continua.
    areaDoFormulario.current?.scrollIntoView({ block: 'center' })
    areaDoFormulario.current
      ?.querySelector<HTMLInputElement>('input')
      ?.focus()
  }, [formularioAberto])

  // A guarda contra resposta atrasada vale para toda carga, a do efeito e
  // as disparadas depois de salvar ou excluir. Antes só a do efeito tinha,
  // e uma recarga pós-exclusão podia chegar com a tela já em outro
  // conteúdo e vesti-la com os dados do anterior.
  const pedidoDeConteudo = useRef(0)
  const pedidoDeMedicoes = useRef(0)

  const tratarFalhaDeCarga = useCallback(
    (falha: unknown, alternativa: string) => {
      // Conteúdo inexistente ou de outro usuário não tem tela própria:
      // a lista é o único lugar coerente para devolver o usuário.
      if (falha instanceof ErroDaApi && falha.status === 404) {
        navegar('/conteudos', { replace: true })
        return
      }

      definirErro(mensagemDe(falha, alternativa))
    },
    [navegar],
  )

  const carregarConteudo = useCallback(async () => {
    if (token === null || !identificadorValido) {
      return
    }

    const aindaVale = reservarPedido(pedidoDeConteudo)

    try {
      const encontrado = await buscarConteudo(token, identificador)

      if (!aindaVale()) {
        return
      }

      definirConteudo(encontrado)
      definirDadosDoConteudo({
        titulo: encontrado.titulo,
        plataforma: encontrado.plataforma,
        tipo: encontrado.tipo,
        data_publicacao: encontrado.data_publicacao,
        url_publicacao: encontrado.url_publicacao ?? '',
      })

      // Dados novos na tela, confirmação antiga fora. Um botão armado que
      // sobrevivesse à recarga excluiria no clique seguinte sem a segunda
      // etapa que é a razão de ele existir.
      definirConfirmandoExclusao(false)
    } catch (falha) {
      if (!aindaVale()) {
        return
      }

      tratarFalhaDeCarga(falha, 'Não foi possível carregar o conteúdo.')
    }
  }, [token, identificador, identificadorValido, tratarFalhaDeCarga])

  // Salvar ou excluir uma medição recarrega só as medições. Recarregar o
  // conteúdo junto reescrevia o formulário e apagava, em silêncio, o que
  // o usuário tinha digitado ali e ainda não salvado.
  const carregarMedicoes = useCallback(async () => {
    if (token === null || !identificadorValido) {
      return
    }

    const aindaVale = reservarPedido(pedidoDeMedicoes)

    try {
      const medicoes = await listarMetricas(token, identificador)

      if (!aindaVale()) {
        return
      }

      definirMetricas(medicoes)
      definirMedicaoConfirmada(null)
    } catch (falha) {
      if (!aindaVale()) {
        return
      }

      tratarFalhaDeCarga(falha, 'Não foi possível carregar as medições.')
    }
  }, [token, identificador, identificadorValido, tratarFalhaDeCarga])

  useEffect(() => {
    void carregarConteudo()
    void carregarMedicoes()
  }, [carregarConteudo, carregarMedicoes])

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

      await carregarConteudo()
    } catch (falha) {
      definirErro(mensagemDe(falha, 'Não foi possível salvar o conteúdo.'))
    } finally {
      definirEnviando(false)
    }
  }

  async function removerConteudo() {
    if (token === null || enviando) {
      return
    }

    definirErro(null)
    definirEnviando(true)

    try {
      await excluirConteudo(token, identificador)
      navegar('/conteudos', { replace: true })
    } catch (falha) {
      // A falha desarma o botão. Deixá-lo em "Confirmar exclusão" faria o
      // próximo clique, talvez acidental, excluir sem a segunda etapa.
      definirConfirmandoExclusao(false)
      definirErro(mensagemDe(falha, 'Não foi possível excluir o conteúdo.'))
    } finally {
      definirEnviando(false)
    }
  }

  function abrirNovaMedicao() {
    // Cada ação começa com a tela limpa. O erro que sobrava descrevia o
    // que o usuário tentou antes, e passava a acusar o que ele está
    // fazendo agora.
    definirErro(null)
    definirMedicaoConfirmada(null)
    definirMedicaoEmEdicao(null)
    definirMedicao(medicaoVazia())
    definirFormularioAberto(true)
  }

  function abrirEdicaoDaMedicao(metrica: Metrica) {
    definirErro(null)
    definirMedicaoConfirmada(null)
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

    const medidas = {
      visualizacoes: inteiroDigitado(medicao.visualizacoes),
      curtidas: inteiroDigitado(medicao.curtidas),
      comentarios: inteiroDigitado(medicao.comentarios),
      compartilhamentos: inteiroDigitado(medicao.compartilhamentos),
      alcance: inteiroDigitado(medicao.alcance),
    }

    // Recusar antes de chamar a API. O campo numérico aceita "12.000" e
    // Number() lê isso como 12, então gravar seria trocar doze mil por
    // doze e contaminar o painel com um número que ninguém digitou.
    const recusada = Object.values(medidas).some(
      (medida) => medida === null,
    )

    if (recusada) {
      definirErro(
        'Confira os números da medição. Use apenas números inteiros, ' +
          'com ou sem ponto de milhar, como 12000 ou 12.000.',
      )
      return
    }

    definirEnviando(true)

    const dados = {
      visualizacoes: medidas.visualizacoes as number,
      curtidas: medidas.curtidas as number,
      comentarios: medidas.comentarios as number,
      compartilhamentos: medidas.compartilhamentos as number,
      alcance: medidas.alcance as number,
      data_referencia: medicao.data_referencia,
    }

    try {
      if (medicaoEmEdicao === null) {
        await criarMetrica(token, identificador, dados)
      } else {
        await atualizarMetrica(token, identificador, medicaoEmEdicao, dados)
      }

      definirFormularioAberto(false)
      await carregarMedicoes()
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

    definirErro(null)
    definirEnviando(true)

    try {
      await excluirMetrica(token, identificador, metricaId)
      await carregarMedicoes()
    } catch (falha) {
      definirErro(mensagemDe(falha, 'Não foi possível excluir a medição.'))
    } finally {
      definirEnviando(false)
    }
  }

  function confirmarOuRemoverMedicao(metricaId: number) {
    // Um clique duplo em "Confirmar" mandava duas exclusões, e o 404 da
    // segunda aparecia como erro depois de a linha já ter sumido.
    if (enviando) {
      return
    }

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
          disabled={enviando}
          onClick={() =>
            confirmandoExclusao
              ? void removerConteudo()
              : definirConfirmandoExclusao(true)
          }
        >
          {confirmandoExclusao ? 'Confirmar exclusão' : 'Excluir conteúdo'}
        </button>
      </header>

      {/* Com o formulário de medição aberto, o erro é dele e aparece junto
          dos botões. Repetir aqui em cima dava duas cópias da mesma frase
          em tela grande e nenhuma visível em tela pequena. */}
      {erro !== null && !formularioAberto && (
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
        <div ref={areaDoFormulario}>
          <FormularioDaMedicao
            dados={medicao}
            enviando={enviando}
            erro={erro}
            dataEmEdicao={
              medicaoEmEdicao === null ? null : medicao.data_referencia
            }
            dataDaPublicacao={conteudo.data_publicacao}
            aoAlterar={alterarMedicao}
            aoEnviar={salvarMedicao}
            aoCancelar={() => {
              definirErro(null)
              definirFormularioAberto(false)
            }}
          />
        </div>
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
            desabilitada={enviando}
            aoEditar={abrirEdicaoDaMedicao}
            aoExcluir={confirmarOuRemoverMedicao}
          />
        </>
      )}
    </main>
  )
}
