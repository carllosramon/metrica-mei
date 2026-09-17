import react from '@vitejs/plugin-react'
import type { Plugin } from 'vite'
import { defineConfig } from 'vitest/config'

const AVISO_SEM_ENDERECO =
  'VITE_API_URL não foi definida. O pacote vai procurar a API em ' +
  'http://localhost:8000, o que só funciona na sua máquina. ' +
  'Defina a variável antes de publicar.'

// Sem VITE_API_URL o cliente cai em http://localhost:8000, que fica
// embutido no pacote e só falha na máquina de quem abrir o site.
//
// Na máquina de quem desenvolve isso é só um aviso, porque ali o endereço
// padrão é o certo. Na integração contínua é erro: build sem endereço é
// pacote que não serve para publicar, e como aviso ele acendia em toda
// execução verde, o que treina qualquer um a ignorá-lo.
function exigirOEnderecoDaApiNaIntegracao(): Plugin {
  return {
    name: 'exigir-o-endereco-da-api-na-integracao',
    apply: 'build',
    configResolved(configuracao) {
      if (configuracao.env.VITE_API_URL) {
        return
      }

      if (process.env.CI) {
        throw new Error(AVISO_SEM_ENDERECO)
      }

      configuracao.logger.warn(`\n${AVISO_SEM_ENDERECO}\n`)
    },
  }
}

// O sistema formata datas para o público brasileiro, e a conversão entre o
// calendário local e o UTC é justamente o que alguns testes verificam. Sem
// fixar o fuso, eles passariam aqui e falhariam em qualquer máquina que
// rodasse em UTC.
process.env.TZ = 'America/Sao_Paulo'

export default defineConfig({
  plugins: [react(), exigirOEnderecoDaApiNaIntegracao()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/testes/preparacao.ts'],
    // Os specs do Playwright sobem servidores de verdade e não rodam
    // no jsdom do Vitest.
    exclude: ['node_modules/**', 'e2e/**'],
    coverage: {
      provider: 'v8',
      include: ['src/**'],
      // Fora da conta fica o que não decide comportamento, o ponto de
      // entrada que só monta a árvore, as declarações de tipo que somem na
      // compilação e os próprios testes.
      exclude: [
        'src/main.tsx',
        'src/vite-env.d.ts',
        'src/api/tipos.ts',
        'src/testes/**',
        '**/*.test.ts',
        '**/*.test.tsx',
      ],
      // O piso é o que foi medido, arredondado para baixo, e não uma meta
      // escolhida no chute. Serve de trava contra queda, e sobe junto quando
      // a cobertura sobe.
      thresholds: {
        statements: 92,
        branches: 85,
        functions: 94,
        lines: 92,
      },
    },
  },
})
