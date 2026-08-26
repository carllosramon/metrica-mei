import { defineConfig, devices } from '@playwright/test'

// O interpretador varia entre máquinas: fora de um virtualenv ativo, o
// Windows costuma expor apenas o lançador `py`.
const PYTHON = process.env.PYTHON_BIN ?? 'python'

const PORTA_DA_API = 8000
const PORTA_DA_INTERFACE = 4173

export default defineConfig({
  testDir: './e2e',
  // Um backend só, com um banco compartilhado: testes em paralelo
  // disputariam os mesmos dados.
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: `http://localhost:${PORTA_DA_INTERFACE}`,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      // A migration roda antes de subir a API para que o banco de teste
      // exista mesmo na primeira execução em uma máquina nova.
      command: `${PYTHON} -m alembic upgrade head && ${PYTHON} -m uvicorn app.main:app --port ${PORTA_DA_API}`,
      cwd: '../backend',
      env: {
        DATABASE_URL: 'sqlite:///./data/e2e.db',
        JWT_SECRET: 'segredo-de-teste-com-mais-de-32-caracteres',
        CORS_ORIGINS: `http://localhost:${PORTA_DA_INTERFACE}`,
      },
      url: `http://127.0.0.1:${PORTA_DA_API}/health`,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: `npm run preview -- --port ${PORTA_DA_INTERFACE} --strictPort`,
      url: `http://localhost:${PORTA_DA_INTERFACE}`,
      reuseExistingServer: !process.env.CI,
    },
  ],
})
