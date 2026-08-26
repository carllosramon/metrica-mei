import { chamarApi } from './cliente'
import type { DadosDaMetrica, Metrica } from './tipos'

export function listarMetricas(
  token: string,
  conteudoId: number,
): Promise<Metrica[]> {
  return chamarApi<Metrica[]>(
    `/conteudos/${conteudoId}/metricas`,
    { token },
  )
}

export function criarMetrica(
  token: string,
  conteudoId: number,
  dados: DadosDaMetrica,
): Promise<Metrica> {
  return chamarApi<Metrica>(`/conteudos/${conteudoId}/metricas`, {
    metodo: 'POST',
    corpo: dados,
    token,
  })
}

export function atualizarMetrica(
  token: string,
  conteudoId: number,
  metricaId: number,
  dados: DadosDaMetrica,
): Promise<Metrica> {
  return chamarApi<Metrica>(
    `/conteudos/${conteudoId}/metricas/${metricaId}`,
    {
      metodo: 'PATCH',
      corpo: dados,
      token,
    },
  )
}

export function excluirMetrica(
  token: string,
  conteudoId: number,
  metricaId: number,
): Promise<void> {
  return chamarApi<void>(
    `/conteudos/${conteudoId}/metricas/${metricaId}`,
    {
      metodo: 'DELETE',
      token,
    },
  )
}
