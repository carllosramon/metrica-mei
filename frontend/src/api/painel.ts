import { chamarApi } from './cliente'
import type { Painel } from './tipos'

export function buscarPainel(token: string): Promise<Painel> {
  return chamarApi<Painel>('/painel', { token })
}
