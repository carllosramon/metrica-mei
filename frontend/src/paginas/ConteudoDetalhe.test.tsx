import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ErroDaApi } from '../api/cliente'
import { buscarConteudo } from '../api/conteudos'
import { criarMetrica, listarMetricas } from '../api/metricas'
import type { Conteudo, Metrica } from '../api/tipos'
import { ContextoAutenticacao } from '../autenticacao/contexto'
import type { ValorDaAutenticacao } from '../autenticacao/contexto'
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
    expect(screen.getByText('10,07%')).toBeInTheDocument()
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
})
