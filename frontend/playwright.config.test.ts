import { afterEach, describe, expect, it, vi } from 'vitest'

// O resetModules é necessário para a configuração ser reavaliada com o
// ambiente trocado, e isso reimporta o @playwright/test inteiro a cada
// chamada. Com a máquina carregada, o padrão de 5 s do Vitest não dava:
// a suíte falhava aqui de vez em quando, e só quando havia outra coisa
// rodando ao lado, que é justamente a situação da integração contínua.
const PRAZO_PARA_CARREGAR = 30_000

async function carregarConfiguracao() {
  vi.resetModules()

  const modulo = await import('./playwright.config.ts')

  return modulo.default
}

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('configuração do Playwright', () => {
  it('recusa test.only na integração contínua', async () => {
    vi.stubEnv('CI', 'true')

    // Um test.only esquecido faz a CI rodar um único teste e reportar
    // verde, como se a jornada inteira tivesse passado. É o tipo de
    // engano que só aparece quando um bug chega em produção por um
    // caminho que a suíte "cobria".
    expect((await carregarConfiguracao()).forbidOnly).toBe(true)
  }, PRAZO_PARA_CARREGAR)

  it('deixa o test.only funcionar na máquina de quem desenvolve', async () => {
    vi.stubEnv('CI', '')

    // Fora da CI o test.only é ferramenta de trabalho, e proibi-lo
    // atrapalharia quem está depurando uma jornada longa.
    expect((await carregarConfiguracao()).forbidOnly).toBe(false)
  }, PRAZO_PARA_CARREGAR)
})
