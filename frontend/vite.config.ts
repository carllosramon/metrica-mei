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
  },
})
