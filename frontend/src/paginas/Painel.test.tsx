import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { Painel as DadosDoPainel } from '../api/tipos'
import { buscarPainel } from '../api/painel'
import { ContextoAutenticacao } from '../autenticacao/contexto'
import type { ValorDaAutenticacao } from '../autenticacao/contexto'
import { Painel } from './Painel'

vi.mock('../api/painel', () => ({
  buscarPainel: vi.fn(),
}))

const painelVazio: DadosDoPainel = {
  total_conteudos: 0,
  conteudos_com_metricas: 0,
  total_visualizacoes: 0,
  total_curtidas: 0,
  total_comentarios: 0,
  total_compartilhamentos: 0,
  total_alcance: 0,
  engajamento_geral: null,
  desempenho_por_plataforma: [],
  maiores_alcances: [],
}

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

function renderizarPainel(dados: DadosDoPainel) {
  vi.mocked(buscarPainel).mockResolvedValue(dados)

  return render(
    <ContextoAutenticacao.Provider value={autenticacao}>
      <Painel />
    </ContextoAutenticacao.Provider>,
  )
}

afterEach(() => {
  vi.clearAllMocks()
})

describe('Painel', () => {
  it('mostra os indicadores consolidados', async () => {
    renderizarPainel({
      ...painelVazio,
      total_conteudos: 3,
      conteudos_com_metricas: 2,
      total_visualizacoes: 4000,
      total_alcance: 2000,
      engajamento_geral: 8.55,
    })

    expect(await screen.findByText('8,55%')).toBeInTheDocument()
    expect(screen.getByText('4.000')).toBeInTheDocument()
    expect(screen.getByText('2.000')).toBeInTheDocument()
    expect(
      screen.getByText('2 com métrica registrada'),
    ).toBeInTheDocument()
  })

  it('explica o traço quando não há alcance para calcular', async () => {
    renderizarPainel(painelVazio)

    expect(await screen.findByText('—')).toBeInTheDocument()
    expect(
      screen.getByText('Sem alcance registrado para calcular.'),
    ).toBeInTheDocument()
  })

  it('orienta o usuário quando o ranking está vazio', async () => {
    renderizarPainel(painelVazio)

    expect(
      await screen.findByText(/Nenhuma medição registrada ainda/),
    ).toBeInTheDocument()
  })

  it('lista os melhores conteúdos com data no formato brasileiro', async () => {
    renderizarPainel({
      ...painelVazio,
      total_conteudos: 1,
      conteudos_com_metricas: 1,
      engajamento_geral: 10.07,
      maiores_alcances: [
        {
          conteudo_id: 7,
          titulo: 'Reels sobre preço',
          plataforma: 'Instagram',
          alcance: 1450,
          engajamento: 10.07,
          data_referencia: '2026-08-21',
        },
      ],
    })

    expect(
      await screen.findByText('Reels sobre preço'),
    ).toBeInTheDocument()
    expect(screen.getByText('Instagram')).toBeInTheDocument()
    expect(screen.getByText('21/08/2026')).toBeInTheDocument()
  })

  it('mostra a mensagem de erro quando a busca falha', async () => {
    vi.mocked(buscarPainel).mockRejectedValue(
      new Error('qualquer falha'),
    )

    render(
      <ContextoAutenticacao.Provider value={autenticacao}>
        <Painel />
      </ContextoAutenticacao.Provider>,
    )

    expect(
      await screen.findByText('Não foi possível carregar o painel.'),
    ).toBeInTheDocument()
  })
})

describe('Painel — desempenho por plataforma', () => {
  it('lista cada plataforma com seus totais consolidados', async () => {
    renderizarPainel({
      ...painelVazio,
      total_conteudos: 3,
      conteudos_com_metricas: 3,
      desempenho_por_plataforma: [
        {
          plataforma: 'Instagram',
          total_conteudos: 2,
          total_visualizacoes: 1500,
          total_curtidas: 100,
          total_comentarios: 10,
          total_compartilhamentos: 10,
          total_alcance: 1000,
          engajamento: 12,
        },
        {
          plataforma: 'TikTok',
          total_conteudos: 1,
          total_visualizacoes: 3000,
          total_curtidas: 100,
          total_comentarios: 20,
          total_compartilhamentos: 30,
          total_alcance: 2000,
          engajamento: 7.5,
        },
      ],
    })

    // Cada plataforma aparece na tabela e no gráfico de barras.
    expect(
      await screen.findByRole('cell', { name: 'Instagram' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'TikTok' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: '12,00%' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: '7,50%' })).toBeInTheDocument()

    expect(
      screen.getByRole('img', { name: /Alcance por plataforma, em 2 redes/ }),
    ).toBeInTheDocument()
  })

  it('orienta quando ainda não há plataforma medida', async () => {
    renderizarPainel(painelVazio)

    expect(
      await screen.findByText(
        'Registre medições para comparar o desempenho das suas redes.',
      ),
    ).toBeInTheDocument()
  })
})
