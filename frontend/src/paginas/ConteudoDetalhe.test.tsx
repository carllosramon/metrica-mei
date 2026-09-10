import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  MemoryRouter,
  Route,
  Routes,
  useNavigate,
} from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

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
import { ContextoAutenticacao } from '../autenticacao/contexto'
import type { ValorDaAutenticacao } from '../autenticacao/contexto'
import { adiar } from '../testes/adiar'
import { ConteudoDetalhe } from './ConteudoDetalhe'

vi.mock('../api/conteudos', () => ({
  buscarConteudo: vi.fn(),
  atualizarConteudo: vi.fn(),
  excluirConteudo: vi.fn(),
}))

vi.mock('../api/metricas', () => ({
  listarMetricas: vi.fn(),
  criarMetrica: vi.fn(),
  atualizarMetrica: vi.fn(),
  excluirMetrica: vi.fn(),
}))

const autenticacao: ValorDaAutenticacao = {
  token: 'token-de-teste',
  usuario: {
    id: 1,
    nome: 'Carlos',
    email: 'carlos@email.com',
    criado_em: '2026-08-01T00:00:00',
  },
  verificando: false,
  sessaoExpirada: false,
  criarConta: vi.fn(),
  entrarNaConta: vi.fn(),
  sair: vi.fn(),
}

const conteudo: Conteudo = {
  id: 7,
  titulo: 'Reels sobre preço',
  plataforma: 'Instagram',
  tipo: 'Reels',
  data_publicacao: '2026-08-21',
  criado_em: '2026-08-21T10:00:00',
  url_publicacao: null,
}

const medicao: Metrica = {
  id: 3,
  visualizacoes: 3200,
  curtidas: 110,
  comentarios: 14,
  compartilhamentos: 22,
  alcance: 1450,
  data_referencia: '2026-08-22',
  criado_em: '2026-08-22T10:00:00',
  engajamento: 10.07,
}

function renderizar() {
  return render(
    <ContextoAutenticacao.Provider value={autenticacao}>
      <MemoryRouter initialEntries={['/conteudos/7']}>
        <Routes>
          <Route
            path="/conteudos/:conteudoId"
            element={<ConteudoDetalhe />}
          />
        </Routes>
      </MemoryRouter>
    </ContextoAutenticacao.Provider>,
  )
}

afterEach(() => {
  vi.clearAllMocks()
})

describe('ConteudoDetalhe', () => {
  it('mostra as medições com o engajamento calculado', async () => {
    vi.mocked(buscarConteudo).mockResolvedValue(conteudo)
    vi.mocked(listarMetricas).mockResolvedValue([medicao])

    renderizar()

    expect(await screen.findByText('22/08/2026')).toBeInTheDocument()
    expect(screen.getByText('3.200')).toBeInTheDocument()

    // O valor aparece na tabela e no eixo do gráfico: a busca precisa
    // dizer de qual dos dois se trata.
    expect(
      screen.getByRole('cell', { name: '10,07%' }),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('img', { name: /Evolução do engajamento/ }),
    ).toBeInTheDocument()
  })

  it('mostra travessão quando a medição não tem alcance', async () => {
    vi.mocked(buscarConteudo).mockResolvedValue(conteudo)
    vi.mocked(listarMetricas).mockResolvedValue([
      { ...medicao, alcance: 0, engajamento: null },
    ])

    renderizar()

    expect(await screen.findByText('—')).toBeInTheDocument()
  })

  it('orienta quando ainda não há medição', async () => {
    vi.mocked(buscarConteudo).mockResolvedValue(conteudo)
    vi.mocked(listarMetricas).mockResolvedValue([])

    renderizar()

    expect(
      await screen.findByText(/Nenhuma medição registrada/),
    ).toBeInTheDocument()
  })

  it('explica o que fazer quando a data já tem medição', async () => {
    const usuario = userEvent.setup()

    vi.mocked(buscarConteudo).mockResolvedValue(conteudo)
    vi.mocked(listarMetricas).mockResolvedValue([])
    vi.mocked(criarMetrica).mockRejectedValue(
      new ErroDaApi(409, 'Já existe uma métrica para este conteúdo nesta data.'),
    )

    renderizar()

    await usuario.click(
      await screen.findByRole('button', { name: 'Registrar medição' }),
    )
    await usuario.click(
      screen.getByRole('button', { name: 'Salvar medição' }),
    )

    // A mensagem do backend diz o que houve; a da tela diz o que fazer.
    expect(
      await screen.findByText(/Edite a medição existente ou escolha outra data/),
    ).toBeInTheDocument()
  })

  it('pede confirmação antes de excluir o conteúdo', async () => {
    const usuario = userEvent.setup()

    vi.mocked(buscarConteudo).mockResolvedValue(conteudo)
    vi.mocked(listarMetricas).mockResolvedValue([])

    renderizar()

    await usuario.click(
      await screen.findByRole('button', { name: 'Excluir conteúdo' }),
    )

    expect(
      screen.getByRole('button', { name: 'Confirmar exclusão' }),
    ).toBeInTheDocument()
  })

  it('salva o conteúdo mandando URL em branco como nula', async () => {
    const usuario = userEvent.setup()

    vi.mocked(buscarConteudo).mockResolvedValue(conteudo)
    vi.mocked(listarMetricas).mockResolvedValue([])
    vi.mocked(atualizarConteudo).mockResolvedValue(conteudo)

    renderizar()

    await usuario.click(
      await screen.findByRole('button', { name: 'Salvar alterações' }),
    )

    // O campo vazio na tela vira null na API, e é assim que se remove a
    // URL de um conteúdo. Mandar texto vazio seria recusado.
    expect(atualizarConteudo).toHaveBeenCalledWith(
      'token-de-teste',
      7,
      expect.objectContaining({
        titulo: 'Reels sobre preço',
        url_publicacao: null,
      }),
    )
  })

  it('mostra o motivo quando salvar o conteúdo falha', async () => {
    const usuario = userEvent.setup()

    vi.mocked(buscarConteudo).mockResolvedValue(conteudo)
    vi.mocked(listarMetricas).mockResolvedValue([])
    vi.mocked(atualizarConteudo).mockRejectedValue(
      new ErroDaApi(422, 'Título não pode ficar em branco.'),
    )

    renderizar()

    await usuario.click(
      await screen.findByRole('button', { name: 'Salvar alterações' }),
    )

    expect(
      await screen.findByText('Título não pode ficar em branco.'),
    ).toBeInTheDocument()

    // A tela continua utilizável para a correção.
    expect(
      screen.getByRole('button', { name: 'Salvar alterações' }),
    ).toBeEnabled()
  })

  it('editar abre o formulário preenchido e corrige a medição certa', async () => {
    const usuario = userEvent.setup()

    vi.mocked(buscarConteudo).mockResolvedValue(conteudo)
    vi.mocked(listarMetricas).mockResolvedValue([medicao])
    vi.mocked(atualizarMetrica).mockResolvedValue(medicao)

    renderizar()

    await usuario.click(await screen.findByRole('button', { name: 'Editar' }))

    expect(screen.getByLabelText('Alcance')).toHaveValue(1450)
    expect(screen.getByLabelText('Data de referência')).toHaveValue(
      '2026-08-22',
    )

    await usuario.click(
      screen.getByRole('button', { name: 'Salvar medição' }),
    )

    // O id da medição em edição é o que separa corrigir de criar outra.
    expect(atualizarMetrica).toHaveBeenCalledWith(
      'token-de-teste',
      7,
      3,
      expect.objectContaining({ alcance: 1450 }),
    )
  })

  it('exclui a medição só no segundo clique', async () => {
    const usuario = userEvent.setup()

    // A lista muda depois da exclusão, então a simulação lê uma variável
    // em vez de devolver sempre a mesma resposta.
    let medicoes = [medicao]

    vi.mocked(buscarConteudo).mockResolvedValue(conteudo)
    vi.mocked(listarMetricas).mockImplementation(async () => medicoes)
    vi.mocked(excluirMetrica).mockImplementation(async () => {
      medicoes = []
    })

    renderizar()

    // Fora da tabela existe "Excluir conteúdo", que não é o alvo aqui.
    const tabela = await screen.findByRole('table')

    await usuario.click(within(tabela).getByRole('button', { name: 'Excluir' }))

    expect(excluirMetrica).not.toHaveBeenCalled()

    await usuario.click(
      within(tabela).getByRole('button', { name: 'Confirmar' }),
    )

    expect(excluirMetrica).toHaveBeenCalledWith('token-de-teste', 7, 3)
    expect(
      await screen.findByText(/Nenhuma medição registrada/),
    ).toBeInTheDocument()
  })

  it('mantém a linha e mostra o motivo quando excluir a medição falha', async () => {
    const usuario = userEvent.setup()

    vi.mocked(buscarConteudo).mockResolvedValue(conteudo)
    vi.mocked(listarMetricas).mockResolvedValue([medicao])
    vi.mocked(excluirMetrica).mockRejectedValue(
      new ErroDaApi(500, 'O servidor não conseguiu excluir.'),
    )

    renderizar()

    const tabela = await screen.findByRole('table')

    await usuario.click(within(tabela).getByRole('button', { name: 'Excluir' }))
    await usuario.click(
      within(tabela).getByRole('button', { name: 'Confirmar' }),
    )

    expect(
      await screen.findByText('O servidor não conseguiu excluir.'),
    ).toBeInTheDocument()
    expect(
      within(tabela).getByRole('cell', { name: '22/08/2026' }),
    ).toBeInTheDocument()
  })

  it('fica na tela e mostra o motivo quando excluir o conteúdo falha', async () => {
    const usuario = userEvent.setup()

    vi.mocked(buscarConteudo).mockResolvedValue(conteudo)
    vi.mocked(listarMetricas).mockResolvedValue([])
    vi.mocked(excluirConteudo).mockRejectedValue(
      new ErroDaApi(500, 'O servidor não conseguiu excluir.'),
    )

    renderizar()

    await usuario.click(
      await screen.findByRole('button', { name: 'Excluir conteúdo' }),
    )
    await usuario.click(
      screen.getByRole('button', { name: 'Confirmar exclusão' }),
    )

    expect(
      await screen.findByText('O servidor não conseguiu excluir.'),
    ).toBeInTheDocument()

    // Sem navegar, o conteúdo segue na tela para uma nova tentativa.
    expect(
      screen.getByRole('heading', { name: 'Reels sobre preço' }),
    ).toBeInTheDocument()
  })
})

function AtalhoParaOutroConteudo() {
  const navegar = useNavigate()

  return (
    <button type="button" onClick={() => navegar('/conteudos/8')}>
      ir para o outro
    </button>
  )
}

describe('ConteudoDetalhe — resposta obsoleta', () => {
  it('ignora a resposta do conteúdo que o usuário já deixou', async () => {
    const usuario = userEvent.setup()

    const primeiro = adiar<Conteudo>()
    const segundo = adiar<Conteudo>()

    vi.mocked(buscarConteudo)
      .mockReturnValueOnce(primeiro.promessa)
      .mockReturnValueOnce(segundo.promessa)

    vi.mocked(listarMetricas).mockResolvedValue([])

    render(
      <ContextoAutenticacao.Provider value={autenticacao}>
        <MemoryRouter initialEntries={['/conteudos/7']}>
          <AtalhoParaOutroConteudo />
          <Routes>
            <Route
              path="/conteudos/:conteudoId"
              element={<ConteudoDetalhe />}
            />
          </Routes>
        </MemoryRouter>
      </ContextoAutenticacao.Provider>,
    )

    await usuario.click(
      screen.getByRole('button', { name: 'ir para o outro' }),
    )

    // O segundo pedido responde primeiro; o primeiro chega atrasado, como
    // acontece quando a rede entrega fora de ordem.
    segundo.resolver({ ...conteudo, id: 8, titulo: 'Carrossel de dicas' })
    primeiro.resolver({ ...conteudo, id: 7, titulo: 'Reels sobre preço' })

    expect(
      await screen.findByRole('heading', { name: 'Carrossel de dicas' }),
    ).toBeInTheDocument()

    expect(screen.queryByText('Reels sobre preço')).toBeNull()
  })

  it('recarga atrasada de uma exclusão não veste o outro conteúdo', async () => {
    const usuario = userEvent.setup()

    // A primeira carga do 7 responde na hora. A recarga depois da exclusão
    // fica presa até o teste soltar, já com a tela no 8.
    const recargaDoSete = adiar<Conteudo>()
    let cargasDoSete = 0

    vi.mocked(buscarConteudo).mockImplementation(async (_token, id) => {
      if (id === 8) {
        return { ...conteudo, id: 8, titulo: 'Carrossel de dicas' }
      }

      cargasDoSete += 1

      return cargasDoSete === 1 ? conteudo : recargaDoSete.promessa
    })
    vi.mocked(listarMetricas).mockImplementation(async (_token, id) =>
      id === 7 ? [medicao] : [],
    )
    vi.mocked(excluirMetrica).mockResolvedValue(undefined)

    render(
      <ContextoAutenticacao.Provider value={autenticacao}>
        <MemoryRouter initialEntries={['/conteudos/7']}>
          <AtalhoParaOutroConteudo />
          <Routes>
            <Route
              path="/conteudos/:conteudoId"
              element={<ConteudoDetalhe />}
            />
          </Routes>
        </MemoryRouter>
      </ContextoAutenticacao.Provider>,
    )

    const tabela = await screen.findByRole('table')

    await usuario.click(within(tabela).getByRole('button', { name: 'Excluir' }))
    await usuario.click(
      within(tabela).getByRole('button', { name: 'Confirmar' }),
    )

    await usuario.click(
      screen.getByRole('button', { name: 'ir para o outro' }),
    )

    expect(
      await screen.findByRole('heading', { name: 'Carrossel de dicas' }),
    ).toBeInTheDocument()

    // A recarga do 7 chega agora. Sem a guarda, ela vestiria a tela do 8
    // com o título do 7, e o próximo salvar gravaria no conteúdo errado.
    await act(async () => {
      recargaDoSete.resolver(conteudo)
    })

    expect(
      screen.getByRole('heading', { name: 'Carrossel de dicas' }),
    ).toBeInTheDocument()
    expect(screen.queryByText('Reels sobre preço')).toBeNull()
  })
})
