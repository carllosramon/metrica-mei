import { afterEach, describe, expect, it, vi } from 'vitest'

import { simularApi } from '../testes/respostaHttp'
import {
  atualizarMetrica,
  criarMetrica,
  excluirMetrica,
  listarMetricas,
} from './metricas'
import type { DadosDaMetrica } from './tipos'

// O caminho de métrica é o mais fundo da API, aninhado dentro do conteúdo
// com dois ids para intercalar. Errar a ordem deles passaria em todos os
// testes de tela, que simulam este módulo.

const dados: DadosDaMetrica = {
  visualizacoes: 3200,
  curtidas: 110,
  comentarios: 14,
  compartilhamentos: 22,
  alcance: 1450,
  data_referencia: '2026-09-02',
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api de métricas', () => {
  it('listarMetricas consulta as medições do conteúdo', async () => {
    const requisicao = simularApi([])

    await listarMetricas('meu-token', 7)

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe('http://localhost:8000/conteudos/7/metricas')
    expect(opcoes.method).toBe('GET')
    expect(opcoes.headers.Authorization).toBe('Bearer meu-token')
  })

  it('criarMetrica envia a medição por POST', async () => {
    const requisicao = simularApi({})

    await criarMetrica('meu-token', 7, dados)

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe('http://localhost:8000/conteudos/7/metricas')
    expect(opcoes.method).toBe('POST')
    expect(JSON.parse(opcoes.body)).toEqual(dados)
  })

  it('atualizarMetrica intercala os dois ids no caminho', async () => {
    const requisicao = simularApi({})

    await atualizarMetrica('meu-token', 7, 3, dados)

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe(
      'http://localhost:8000/conteudos/7/metricas/3',
    )
    expect(opcoes.method).toBe('PATCH')
    expect(JSON.parse(opcoes.body)).toEqual(dados)
  })

  it('excluirMetrica remove a medição certa', async () => {
    const requisicao = simularApi(undefined)

    await excluirMetrica('meu-token', 7, 3)

    const [endereco, opcoes] = requisicao.mock.calls[0]

    expect(endereco).toBe(
      'http://localhost:8000/conteudos/7/metricas/3',
    )
    expect(opcoes.method).toBe('DELETE')
  })
})
