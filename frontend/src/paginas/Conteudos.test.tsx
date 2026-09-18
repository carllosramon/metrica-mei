import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { criarConteudo, listarConteudos } from '../api/conteudos'
import type { ConteudoDaLista } from '../api/tipos'
import { ContextoAutenticacao } from '../autenticacao/contexto'
import type { ValorDaAutenticacao } from '../autenticacao/contexto'
import { dataDeHoje } from '../formatacao'
import { adiar } from '../testes/adiar'
import { Conteudos } from './Conteudos'

vi.mock('../api/conteudos', () => ({
  listarConteudos: vi.fn(),
  criarConteudo: vi.fn(),
}))

// Só a data de hoje é substituível. O resto da formatação segue real.
vi.mock('../formatacao', async (importarOriginal) => {
  const original = await importarOriginal<typeof import('../formatacao')>()

  return { ...original, dataDeHoje: vi.fn(original.dataDeHoje) }
})

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

const reels: ConteudoDaLista = {
  id: 7,
  titulo: 'Reels sobre preço',
  plataforma: 'Instagram',
  tipo: 'Reels',
  data_publicacao: '2026-08-21',
  criado_em: '2026-08-21T10:00:00',
  url_publicacao: 'https://instagram.com/p/abc',
  ultima_medicao: '2026-08-22',
}

function renderizar() {
  return render(
    <ContextoAutenticacao.Provider value={autenticacao}>
      <MemoryRouter>
        <Conteudos />
      </MemoryRouter>
    </ContextoAutenticacao.Provider>,
  )
}

afterEach(() => {
  vi.clearAllMocks()
})

describe('Conteudos', () => {
  it('lista os conteúdos do usuário', async () => {
    vi.mocked(listarConteudos).mockResolvedValue([reels])

    renderizar()

    expect(await screen.findByText('Reels sobre preço')).toBeInTheDocument()
    expect(screen.getByText('Instagram')).toBeInTheDocument()
    expect(screen.getByText('21/08/2026')).toBeInTheDocument()
  })

  it('diz quando cada conteúdo foi medido pela última vez', async () => {
    vi.mocked(listarConteudos).mockResolvedValue([
      reels,
      { ...reels, id: 8, titulo: 'Carrossel novo', ultima_medicao: null },
    ])

    renderizar()

    // A coluna responde "o que falta anotar" sem abrir conteúdo por
    // conteúdo, que é a rotina que o sistema se propõe a apoiar.
    expect(await screen.findByText('22/08/2026')).toBeInTheDocument()
    expect(screen.getByText('nunca medido')).toBeInTheDocument()
  })

  it('orienta quem ainda não cadastrou nada', async () => {
    vi.mocked(listarConteudos).mockResolvedValue([])

    renderizar()

    expect(
      await screen.findByText(/Nenhum conteúdo cadastrado ainda/),
    ).toBeInTheDocument()
  })

  it('mantém a falha de carga visível depois de abrir o formulário', async () => {
    const usuario = userEvent.setup()

    vi.mocked(listarConteudos).mockRejectedValue(
      new Error('conexão recusada'),
    )

    renderizar()

    expect(
      await screen.findByText(/Não foi possível carregar os conteúdos/),
    ).toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: 'Novo conteúdo' }))

    // Abrir o formulário limpa o erro do cadastro, não o da carga. Se
    // limpasse os dois, a lista continuaria nula e sem aviso, e a tela
    // voltaria a "Carregando…" sem nunca sair de lá.
    expect(
      screen.getByText(/Não foi possível carregar os conteúdos/),
    ).toBeInTheDocument()

    expect(screen.queryByText('Carregando…')).not.toBeInTheDocument()
  })

  it('a data padrão do conteúdo é a de quando o formulário abre', async () => {
    const usuario = userEvent.setup()

    vi.mocked(listarConteudos).mockResolvedValue([])

    renderizar()

    vi.mocked(dataDeHoje).mockReturnValue('2026-09-09')

    await usuario.click(
      await screen.findByRole('button', { name: 'Novo conteúdo' }),
    )

    expect(screen.getByLabelText('Data de publicação')).toHaveValue(
      '2026-09-09',
    )

    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }))

    // Virou o dia com a aba aberta. O formulário era composto uma vez na
    // montagem, então a data ficava presa em quando a página carregou, e
    // o conteúdo nascia com a data de ontem.
    vi.mocked(dataDeHoje).mockReturnValue('2026-09-10')

    await usuario.click(screen.getByRole('button', { name: 'Novo conteúdo' }))

    expect(screen.getByLabelText('Data de publicação')).toHaveValue(
      '2026-09-10',
    )
  })

  it('envia o formulário e recarrega a lista', async () => {
    const usuario = userEvent.setup()

    vi.mocked(listarConteudos).mockResolvedValue([])
    vi.mocked(criarConteudo).mockResolvedValue(reels)

    renderizar()

    await usuario.click(
      await screen.findByRole('button', { name: 'Novo conteúdo' }),
    )

    await usuario.type(screen.getByLabelText('Título'), 'Reels sobre preço')
    await usuario.type(screen.getByLabelText('Plataforma'), 'Instagram')
    await usuario.type(screen.getByLabelText('Tipo'), 'Reels')

    await usuario.click(screen.getByRole('button', { name: 'Salvar' }))

    await waitFor(() => {
      expect(criarConteudo).toHaveBeenCalledTimes(1)
    })

    const [, enviado] = vi.mocked(criarConteudo).mock.calls[0]

    expect(enviado.titulo).toBe('Reels sobre preço')
    // Campo em branco vira null, e não texto vazio, que o backend recusa.
    expect(enviado.url_publicacao).toBeNull()

    expect(listarConteudos).toHaveBeenCalledTimes(2)
  })

  it('mostra a mensagem de erro quando a listagem falha', async () => {
    vi.mocked(listarConteudos).mockRejectedValue(new Error('caiu'))

    renderizar()

    expect(
      await screen.findByText('Não foi possível carregar os conteúdos.'),
    ).toBeInTheDocument()
  })

  it('a carga inicial lenta não apaga o conteúdo recém-criado', async () => {
    const usuario = userEvent.setup()

    // A primeira listagem fica presa. O cadastro dispara uma segunda, que
    // responde antes, e só depois a primeira chega, já velha.
    const cargaInicial = adiar<ConteudoDaLista[]>()

    vi.mocked(listarConteudos)
      .mockReturnValueOnce(cargaInicial.promessa)
      .mockResolvedValue([reels])
    vi.mocked(criarConteudo).mockResolvedValue(reels)

    renderizar()

    await usuario.click(
      await screen.findByRole('button', { name: 'Novo conteúdo' }),
    )
    await usuario.type(screen.getByLabelText('Título'), 'Reels sobre preço')
    await usuario.type(screen.getByLabelText('Plataforma'), 'Instagram')
    await usuario.type(screen.getByLabelText('Tipo'), 'Reels')
    await usuario.click(screen.getByRole('button', { name: 'Salvar' }))

    expect(await screen.findByText('Reels sobre preço')).toBeInTheDocument()

    await act(async () => {
      cargaInicial.resolver([])
    })

    // A lista vazia era a resposta certa quando foi pedida, e a errada
    // agora. O conteúdo criado precisa continuar na tela.
    expect(screen.getByText('Reels sobre preço')).toBeInTheDocument()
    expect(screen.queryByText(/Nenhum conteúdo cadastrado/)).toBeNull()
  })
})
