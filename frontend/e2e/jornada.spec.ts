import { expect, test } from '@playwright/test'

// O banco de teste sobrevive entre execuções, então cada rodada precisa de
// um e-mail próprio para não esbarrar no cadastro já existente. O domínio
// não pode ser .test: o validador do backend recusa TLDs reservados.
function emailUnico(): string {
  return `dev-${Date.now()}@metricamei.com`
}

const SENHA = 'minhasenha'

test('jornada completa: da conta nova ao painel com engajamento', async ({
  page,
}) => {
  const email = emailUnico()

  await test.step('criar conta', async () => {
    await page.goto('/cadastrar')

    await page.getByLabel('Nome').fill('Joao')
    await page.getByLabel('E-mail').fill(email)
    await page.getByLabel('Senha').fill(SENHA)
    await page.getByRole('button', { name: 'Criar conta' }).click()

    await expect(
      page.getByRole('heading', { name: 'Painel de análise' }),
    ).toBeVisible()
  })

  await test.step('painel de conta nova vem zerado', async () => {
    await expect(
      page.getByText('Nenhuma medição registrada ainda.', { exact: false }),
    ).toBeVisible()
  })

  await test.step('cadastrar conteúdo', async () => {
    await page.getByRole('link', { name: 'Conteúdos' }).click()
    await page.getByRole('button', { name: 'Novo conteúdo' }).click()

    await page.getByLabel('Título').fill('Reels sobre precificação')
    await page.getByLabel('Plataforma').fill('Instagram')
    await page.getByLabel('Tipo').fill('Reels')
    await page.getByRole('button', { name: 'Salvar' }).click()

    await expect(
      page.getByRole('link', { name: 'Reels sobre precificação' }),
    ).toBeVisible()
  })

  await test.step('registrar medição', async () => {
    await page.getByRole('link', { name: 'Reels sobre precificação' }).click()
    await page.getByRole('button', { name: 'Registrar medição' }).click()

    await page.getByLabel('Visualizações').fill('3200')
    await page.getByLabel('Alcance').fill('1450')
    await page.getByLabel('Curtidas').fill('110')
    await page.getByLabel('Comentários').fill('14')
    await page.getByLabel('Compartilhamentos').fill('22')
    await page.getByRole('button', { name: 'Salvar medição' }).click()

    // (110 + 14 + 22) / 1450 x 100 = 10,07
    await expect(page.getByRole('cell', { name: '10,07%' })).toBeVisible()
  })

  await test.step('a mesma data é recusada com orientação', async () => {
    await page.getByRole('button', { name: 'Registrar medição' }).click()
    await page.getByLabel('Alcance').fill('900')
    await page.getByRole('button', { name: 'Salvar medição' }).click()

    await expect(
      page.getByText(/Edite a medição existente ou escolha outra data/),
    ).toBeVisible()

    await page.getByRole('button', { name: 'Cancelar' }).click()
  })

  await test.step('o painel consolida a medição', async () => {
    await page.getByRole('link', { name: 'Painel' }).click()

    await expect(page.getByText('10,07%').first()).toBeVisible()
    await expect(page.getByText('1 com métrica registrada')).toBeVisible()
    await expect(
      page.getByRole('cell', { name: 'Reels sobre precificação' }),
    ).toBeVisible()
  })

  await test.step('conteúdo sem alcance entra sem índice', async () => {
    await page.getByRole('link', { name: 'Conteúdos' }).click()
    await page.getByRole('button', { name: 'Novo conteúdo' }).click()

    await page.getByLabel('Título').fill('Story sem alcance medido')
    await page.getByLabel('Plataforma').fill('Instagram')
    await page.getByLabel('Tipo').fill('Story')
    await page.getByRole('button', { name: 'Salvar' }).click()

    await page
      .getByRole('link', { name: 'Story sem alcance medido' })
      .click()
    await page.getByRole('button', { name: 'Registrar medição' }).click()

    await page.getByLabel('Curtidas').fill('5')
    await page.getByRole('button', { name: 'Salvar medição' }).click()

    // Alcance zero não é desempenho zero: o índice não é calculável.
    await expect(page.getByRole('cell', { name: '—' })).toBeVisible()

    await page.getByRole('link', { name: 'Painel' }).click()

    await expect(page.getByText('2 com métrica registrada')).toBeVisible()

    // O ranking é de alcance: a medição zerada aparece, e o que fica
    // sem valor é apenas o índice de engajamento.
    await expect(
      page.getByRole('cell', { name: 'Story sem alcance medido' }),
    ).toBeVisible()
  })

  await test.step('sair e entrar de novo devolve ao painel', async () => {
    await page.getByRole('button', { name: 'Sair' }).click()

    await expect(
      page.getByRole('heading', { name: 'Entrar no MetricaMEI' }),
    ).toBeVisible()

    await page.getByLabel('E-mail').fill(email)
    await page.getByLabel('Senha').fill(SENHA)
    await page.getByRole('button', { name: 'Entrar' }).click()

    await expect(page.getByText('10,07%').first()).toBeVisible()
  })
})

test('rota protegida manda quem não tem sessão para o login', async ({
  page,
}) => {
  await page.goto('/painel')

  await expect(
    page.getByRole('heading', { name: 'Entrar no MetricaMEI' }),
  ).toBeVisible()
})
