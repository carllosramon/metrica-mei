import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// O sistema formata datas para o público brasileiro, e a conversão entre o
// calendário local e o UTC é justamente o que alguns testes verificam. Sem
// fixar o fuso, eles passariam aqui e falhariam em qualquer máquina que
// rodasse em UTC.
process.env.TZ = 'America/Sao_Paulo'

export default defineConfig({
  plugins: [react()],
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
        statements: 65,
        branches: 63,
        functions: 57,
        lines: 65,
      },
    },
  },
})
