import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

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
