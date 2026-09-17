import { expect, test } from '@playwright/test'

// O banco de teste sobrevive entre execuções, então cada rodada precisa
// de um e-mail próprio. O domínio não pode ser .test: o validador do
// backend recusa TLDs reservados.
function emailUnico(): string {
  return `painel-${Date.now()}@metricamei.com`
}

const SENHA = 'minhasenha'

function diasAtras(dias: number): string {
  const dia = new Date()

  dia.setDate(dia.getDate() - dias)

  return dia.toISOString().slice(0, 10)
}

async function cadastrarConteudo(
  page: import('@playwright/test').Page,
  dados: { titulo: string; plataforma: string; tipo: string },
) {
  await page.getByRole('link', { name: 'Conteúdos', exact: true }).click()
  await page.getByRole('button', { name: 'Novo conteúdo' }).click()

  await page.getByLabel('Título').fill(dados.titulo)
  await page.getByLabel('Plataforma').fill(dados.plataforma)
  await page.getByLabel('Tipo').fill(dados.tipo)
  await page.getByLabel('Data de publicação').fill(diasAtras(5))
  await page.getByRole('button', { name: 'Salvar' }).click()

  await expect(page.getByRole('link', { name: dados.titulo })).toBeVisible()
}

async function registrarMedicao(
  page: import('@playwright/test').Page,
  medidas: {
    data: string
    visualizacoes: string
    alcance: string
    curtidas: string
  },
) {
  await page.getByRole('button', { name: 'Registrar medição' }).click()

  await page.getByLabel('Data de referência').fill(medidas.data)
  await page.getByLabel('Visualizações').fill(medidas.visualizacoes)
  await page.getByLabel('Alcance').fill(medidas.alcance)
  await page.getByLabel('Curtidas').fill(medidas.curtidas)

  // Os cinco campos são obrigatórios e nascem vazios, então os que este
  // cenário não usa precisam receber zero explicitamente.
  await page.getByLabel('Comentários').fill('0')
  await page.getByLabel('Compartilhamentos').fill('0')
  await page.getByRole('button', { name: 'Salvar medição' }).click()
}

// A jornada principal usa uma rede só e uma data por conteúdo, e por
// isso nunca exercitou a regra central do RF05 ponta a ponta: cada
// conteúdo entra no painel só pela medição mais recente, porque os
// números anotados são acumulados, e o índice consolidado é média
// ponderada pelo alcance, não média de índices.
test('o painel conta cada conteúdo uma vez, pela medição mais recente', async ({
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

  await test.step('duas redes, e uma delas medida duas vezes', async () => {
    await cadastrarConteudo(page, {
      titulo: 'Carrossel de preços',
      plataforma: 'Instagram',
      tipo: 'Carrossel',
    })

    await page.getByRole('link', { name: 'Carrossel de preços' }).click()

    // Primeiro retrato, três dias atrás.
    await registrarMedicao(page, {
      data: diasAtras(3),
      visualizacoes: '200',
      alcance: '100',
      curtidas: '10',
    })

    // Segundo retrato, ontem. Os números são acumulados desde a
    // publicação, e não o que rendeu no dia.
    await registrarMedicao(page, {
      data: diasAtras(1),
      visualizacoes: '2000',
      alcance: '1000',
      curtidas: '100',
    })

    await expect(page.getByRole('cell', { name: '2.000' })).toBeVisible()

    await cadastrarConteudo(page, {
      titulo: 'Vídeo de bastidores',
      plataforma: 'TikTok',
      tipo: 'Vídeo',
    })

    await page.getByRole('link', { name: 'Vídeo de bastidores' }).click()

    await registrarMedicao(page, {
      data: diasAtras(1),
      visualizacoes: '800',
      alcance: '500',
      curtidas: '25',
    })
  })

  await test.step('os totais usam só o retrato mais recente', async () => {
    await page.getByRole('link', { name: 'Painel' }).click()

    // 2000 + 800. Somar o histórico daria 2.200 no Instagram e 3.000 no
    // total, contando de novo o que já estava no primeiro retrato.
    await expect(page.getByText('2.800')).toBeVisible()

    // 1000 + 500, pela mesma razão.
    await expect(page.getByText('1.500')).toBeVisible()

    await expect(page.getByText('2 com métrica registrada')).toBeVisible()
  })

  await test.step('o índice geral é ponderado pelo alcance', async () => {
    // 125 interações sobre 1.500 de alcance dá 8,33%. A média dos dois
    // índices, 10,00% e 5,00%, daria 7,50% e trataria uma rede com o
    // dobro do alcance como se pesasse o mesmo que a outra.
    await expect(page.getByText('8,33%')).toBeVisible()
  })

  await test.step('cada rede aparece com o seu próprio índice', async () => {
    const tabelaDePlataformas = page.getByRole('table').first()

    await expect(
      tabelaDePlataformas.getByRole('cell', { name: '10,00%' }),
    ).toBeVisible()

    await expect(
      tabelaDePlataformas.getByRole('cell', { name: '5,00%' }),
    ).toBeVisible()

    // Ordenado por alcance: o Instagram, com 1.000, vem antes do TikTok.
    const redes = tabelaDePlataformas.getByRole('row')

    await expect(redes.nth(1)).toContainText('Instagram')
    await expect(redes.nth(2)).toContainText('TikTok')
  })
})
