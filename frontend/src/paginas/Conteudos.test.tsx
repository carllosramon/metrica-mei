import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { criarConteudo, listarConteudos } from '../api/conteudos'
import type { Conteudo } from '../api/tipos'
import { ContextoAutenticacao } from '../autenticacao/contexto'
import type { ValorDaAutenticacao } from '../autenticacao/contexto'
import { Conteudos } from './Conteudos'

vi.mock('../api/conteudos', () => ({
  listarConteudos: vi.fn(),
  criarConteudo: vi.fn(),
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

const reels: Conteudo = {
  id: 7,
  titulo: 'Reels sobre preço',
  plataforma: 'Instagram',
  tipo: 'Reels',
  data_publicacao: '2026-08-21',
  criado_em: '2026-08-21T10:00:00',
  url_publicacao: 'https://instagram.com/p/abc',
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

  it('orienta quem ainda não cadastrou nada', async () => {
    vi.mocked(listarConteudos).mockResolvedValue([])

    renderizar()

    expect(
      await screen.findByText(/Nenhum conteúdo cadastrado ainda/),
    ).toBeInTheDocument()
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
})
