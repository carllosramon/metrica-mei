from datetime import date, datetime, timedelta, timezone

from app.domain.content import Content
from app.domain.metric import Metric
from app.services.dashboard_service import DashboardService
from app.services.engagement import engagement_of
from tests.dubles.in_memory_content_repository import (
    InMemoryContentRepository,
)
from tests.dubles.in_memory_metric_repository import (
    InMemoryMetricRepository,
)


def make_service():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    service = DashboardService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    return service, content_repository, metric_repository


def create_content(
    repository,
    *,
    user_id=1,
    titulo="Post",
    plataforma="Instagram",
    data_publicacao=None,
):
    return repository.create(
        Content(
            id=None,
            usuario_id=user_id,
            titulo=titulo,
            plataforma=plataforma,
            tipo="Reels",
            data_publicacao=(
                data_publicacao or date.today()
            ),
            criado_em=datetime.now(timezone.utc),
        )
    )


def create_metric(
    repository,
    content_id,
    *,
    data_referencia=None,
    visualizacoes=0,
    curtidas=0,
    comentarios=0,
    compartilhamentos=0,
    alcance=0,
):
    return repository.create(
        Metric(
            id=None,
            conteudo_id=content_id,
            visualizacoes=visualizacoes,
            curtidas=curtidas,
            comentarios=comentarios,
            compartilhamentos=compartilhamentos,
            alcance=alcance,
            data_referencia=(data_referencia or date.today()),
            criado_em=datetime.now(timezone.utc),
        )
    )


def test_dashboard_is_empty_for_user_without_contents():
    service, _, _ = make_service()

    dashboard = service.get(user_id=1)

    assert dashboard.total_conteudos == 0
    assert dashboard.conteudos_com_metricas == 0
    assert dashboard.total_visualizacoes == 0
    assert dashboard.total_curtidas == 0
    assert dashboard.total_comentarios == 0
    assert dashboard.total_compartilhamentos == 0
    assert dashboard.total_alcance == 0
    assert dashboard.engajamento_geral is None
    assert dashboard.desempenho_por_plataforma == []
    assert dashboard.maiores_alcances == []


def test_content_without_metrics_counts_only_in_total():
    service, content_repository, _ = make_service()

    create_content(content_repository)
    create_content(content_repository)

    dashboard = service.get(user_id=1)

    assert dashboard.total_conteudos == 2
    assert dashboard.conteudos_com_metricas == 0
    assert dashboard.total_visualizacoes == 0


def test_only_latest_snapshot_of_each_content_is_summed():
    service, content_repository, metric_repository = make_service()

    content = create_content(content_repository)

    create_metric(
        metric_repository,
        content.id,
        data_referencia=date.today() - timedelta(days=1),
        visualizacoes=100,
        curtidas=10,
        alcance=200,
    )

    create_metric(
        metric_repository,
        content.id,
        data_referencia=date.today(),
        visualizacoes=300,
        curtidas=30,
        alcance=500,
    )

    dashboard = service.get(user_id=1)

    # Snapshots são cumulativos: somar os dois daria 400 visualizações
    # para um conteúdo que teve 300.
    assert dashboard.total_visualizacoes == 300
    assert dashboard.total_curtidas == 30
    assert dashboard.total_alcance == 500
    assert dashboard.conteudos_com_metricas == 1


def test_engagement_uses_totals_instead_of_average_of_averages():
    service, content_repository, metric_repository = make_service()

    pequeno = create_content(
        content_repository,
        titulo="Alcance pequeno",
    )
    grande = create_content(
        content_repository,
        titulo="Alcance grande",
    )

    create_metric(
        metric_repository,
        pequeno.id,
        curtidas=1,
        alcance=10,
    )

    create_metric(
        metric_repository,
        grande.id,
        curtidas=10,
        alcance=1000,
    )

    dashboard = service.get(user_id=1)

    # Média das médias daria 5.5, distorcida pelo conteúdo de alcance 10.
    assert dashboard.engajamento_geral == 1.09


def test_engagement_is_none_when_total_reach_is_zero():
    service, content_repository, metric_repository = make_service()

    content = create_content(content_repository)

    create_metric(
        metric_repository,
        content.id,
        curtidas=5,
        alcance=0,
    )

    dashboard = service.get(user_id=1)

    assert dashboard.total_alcance == 0
    assert dashboard.engajamento_geral is None


def test_ranking_orders_contents_by_reach_desc():
    service, content_repository, metric_repository = make_service()

    maior = create_content(content_repository, titulo="Maior alcance")
    menor = create_content(content_repository, titulo="Menor alcance")
    meio = create_content(content_repository, titulo="Alcance do meio")

    create_metric(metric_repository, maior.id, alcance=5000, curtidas=10)
    create_metric(metric_repository, menor.id, alcance=100, curtidas=50)
    create_metric(metric_repository, meio.id, alcance=800, curtidas=20)

    dashboard = service.get(user_id=1)

    assert [item.titulo for item in dashboard.maiores_alcances] == [
        "Maior alcance",
        "Alcance do meio",
        "Menor alcance",
    ]

    # O conteúdo de menor alcance tem o melhor engajamento: o ranking é de
    # alcance, e não de desempenho relativo.
    assert dashboard.maiores_alcances[0].alcance == 5000
    assert dashboard.maiores_alcances[0].engajamento == 0.2
    assert dashboard.maiores_alcances[2].engajamento == 50.0


def test_ranking_is_limited_to_five_contents():
    service, content_repository, metric_repository = make_service()

    for posicao in range(6):
        content = create_content(
            content_repository,
            titulo=f"Conteúdo {posicao}",
        )

        create_metric(
            metric_repository,
            content.id,
            alcance=(posicao + 1) * 100,
        )

    dashboard = service.get(user_id=1)

    assert dashboard.total_conteudos == 6
    assert len(dashboard.maiores_alcances) == 5

    # Contar cinco não diz quais cinco. Trocar o corte do começo para o
    # fim da lista devolveria os cinco piores, no mesmo número, e a
    # contagem continuaria passando.
    assert [
        item.titulo for item in dashboard.maiores_alcances
    ] == [
        "Conteúdo 5",
        "Conteúdo 4",
        "Conteúdo 3",
        "Conteúdo 2",
        "Conteúdo 1",
    ]


def test_ranking_keeps_content_without_reach():
    service, content_repository, metric_repository = make_service()

    medido = create_content(content_repository, titulo="Medido")
    sem_alcance = create_content(content_repository, titulo="Sem alcance")

    create_metric(metric_repository, medido.id, alcance=100, curtidas=10)
    create_metric(metric_repository, sem_alcance.id, alcance=0, curtidas=5)

    dashboard = service.get(user_id=1)

    # Alcance zero é medição real e pertence ao ranking, na última posição.
    # Só o índice de engajamento fica sem valor.
    assert [item.titulo for item in dashboard.maiores_alcances] == [
        "Medido",
        "Sem alcance",
    ]
    assert dashboard.maiores_alcances[1].engajamento is None


def test_ranking_excludes_content_without_metrics():
    service, content_repository, metric_repository = make_service()

    medido = create_content(content_repository, titulo="Medido")
    create_content(content_repository, titulo="Sem métrica")

    create_metric(metric_repository, medido.id, alcance=100)

    dashboard = service.get(user_id=1)

    assert dashboard.total_conteudos == 2
    assert [item.titulo for item in dashboard.maiores_alcances] == [
        "Medido"
    ]


def test_platform_performance_groups_and_sums():
    service, content_repository, metric_repository = make_service()

    primeiro = create_content(
        content_repository,
        titulo="Reels",
        plataforma="Instagram",
    )
    segundo = create_content(
        content_repository,
        titulo="Carrossel",
        plataforma="Instagram",
    )
    terceiro = create_content(
        content_repository,
        titulo="Vídeo",
        plataforma="TikTok",
    )

    create_metric(
        metric_repository,
        primeiro.id,
        visualizacoes=1000,
        curtidas=80,
        comentarios=10,
        compartilhamentos=10,
        alcance=800,
    )
    create_metric(
        metric_repository,
        segundo.id,
        visualizacoes=500,
        curtidas=20,
        comentarios=0,
        compartilhamentos=0,
        alcance=200,
    )
    create_metric(
        metric_repository,
        terceiro.id,
        visualizacoes=3000,
        curtidas=100,
        comentarios=20,
        compartilhamentos=30,
        alcance=2000,
    )

    dashboard = service.get(user_id=1)

    por_plataforma = {
        item.plataforma: item
        for item in dashboard.desempenho_por_plataforma
    }

    assert por_plataforma["Instagram"].total_conteudos == 2
    assert por_plataforma["Instagram"].conteudos_com_metricas == 2
    assert por_plataforma["Instagram"].total_visualizacoes == 1500
    assert por_plataforma["Instagram"].total_alcance == 1000
    # (80 + 10 + 10 + 20) / 1000 x 100
    assert por_plataforma["Instagram"].engajamento == 12.0

    assert por_plataforma["TikTok"].total_conteudos == 1
    assert por_plataforma["TikTok"].engajamento == 7.5


def test_platform_counts_all_contents_and_only_measured_ones():
    service, content_repository, metric_repository = make_service()

    medido = create_content(
        content_repository,
        titulo="Reels",
        plataforma="Instagram",
    )
    create_content(
        content_repository,
        titulo="Carrossel sem medição",
        plataforma="Instagram",
    )
    create_content(
        content_repository,
        titulo="Story sem medição",
        plataforma="Instagram",
    )

    create_metric(metric_repository, medido.id, alcance=800, curtidas=80)

    dashboard = service.get(user_id=1)

    instagram = dashboard.desempenho_por_plataforma[0]

    # Os dois contadores separam "quantos publiquei nesta rede" de "de
    # quantos eu já tenho número". Um só dizia a segunda coisa com o nome
    # da primeira.
    assert instagram.total_conteudos == 3
    assert instagram.conteudos_com_metricas == 1
    assert instagram.total_alcance == 800


def test_platform_without_any_measurement_still_appears():
    service, content_repository, metric_repository = make_service()

    medido = create_content(
        content_repository,
        titulo="Reels",
        plataforma="Instagram",
    )
    create_content(
        content_repository,
        titulo="Vídeo sem medição",
        plataforma="TikTok",
    )

    create_metric(metric_repository, medido.id, alcance=500, curtidas=50)

    dashboard = service.get(user_id=1)

    por_plataforma = {
        item.plataforma: item
        for item in dashboard.desempenho_por_plataforma
    }

    # A rede onde o usuário publicou e ainda não mediu desaparecia do
    # painel, e ele não tinha como notar que faltava medir ali.
    assert set(por_plataforma) == {"Instagram", "TikTok"}

    tiktok = por_plataforma["TikTok"]

    assert tiktok.total_conteudos == 1
    assert tiktok.conteudos_com_metricas == 0
    assert tiktok.total_alcance == 0
    assert tiktok.engajamento is None


def test_platform_without_measurement_is_last_even_tied_at_zero():
    service, content_repository, metric_repository = make_service()

    medido = create_content(
        content_repository,
        titulo="Vídeo",
        plataforma="Zeta",
    )
    create_content(
        content_repository,
        titulo="Post sem medição",
        plataforma="Alfa",
    )

    create_metric(metric_repository, medido.id, alcance=0, curtidas=5)

    dashboard = service.get(user_id=1)

    # As duas redes empatam em alcance zero. Com desempate só pelo nome, a
    # que nunca foi medida vinha primeiro, contra o critério 9 do RF05.
    assert [
        item.plataforma
        for item in dashboard.desempenho_por_plataforma
    ] == ["Zeta", "Alfa"]


def test_engagement_ignores_measurement_without_reach():
    service, content_repository, metric_repository = make_service()

    medido = create_content(content_repository, titulo="Com alcance")
    sem_alcance = create_content(
        content_repository,
        titulo="Sem alcance",
    )

    create_metric(metric_repository, medido.id, curtidas=10, alcance=100)
    create_metric(
        metric_repository,
        sem_alcance.id,
        curtidas=90,
        alcance=0,
    )

    dashboard = service.get(user_id=1)

    # As 90 curtidas não têm alcance pelo qual dividir. Somadas ao
    # numerador, eram cobradas do alcance do outro conteúdo e levavam a
    # conta a 100%, dez vezes o índice do único conteúdo que tem índice.
    assert dashboard.engajamento_geral == 10.0

    # O usuário digitou aquelas curtidas: os totais brutos continuam
    # inteiros, e o que muda é só a conta do índice.
    assert dashboard.total_curtidas == 100
    assert dashboard.total_alcance == 100
    assert dashboard.conteudos_com_metricas == 2


def test_platform_engagement_ignores_measurement_without_reach():
    service, content_repository, metric_repository = make_service()

    medido = create_content(
        content_repository,
        titulo="Reels",
        plataforma="Instagram",
    )
    sem_alcance = create_content(
        content_repository,
        titulo="Story",
        plataforma="Instagram",
    )

    create_metric(metric_repository, medido.id, curtidas=10, alcance=100)
    create_metric(
        metric_repository,
        sem_alcance.id,
        curtidas=90,
        alcance=0,
    )

    dashboard = service.get(user_id=1)

    instagram = dashboard.desempenho_por_plataforma[0]

    # A rede usa a mesma regra do topo. Se divergisse, a linha da tabela
    # contradiria o cartão destacado sobre as mesmas duas medições.
    assert instagram.engajamento == 10.0
    assert instagram.total_curtidas == 100
    assert instagram.conteudos_com_metricas == 2

    # Sem alcance para comparar, a rede não medida fica por último.
    assert dashboard.desempenho_por_plataforma[0].plataforma == "Instagram"


def test_platform_performance_ignores_letter_case():
    service, content_repository, metric_repository = make_service()

    primeiro = create_content(
        content_repository,
        titulo="Reels",
        plataforma="Instagram",
    )
    segundo = create_content(
        content_repository,
        titulo="Carrossel",
        plataforma="instagram",
    )

    create_metric(metric_repository, primeiro.id, alcance=300)
    create_metric(metric_repository, segundo.id, alcance=200)

    dashboard = service.get(user_id=1)

    # A plataforma é texto livre: variação de maiúscula não pode partir a
    # mesma rede em duas linhas do painel.
    assert len(dashboard.desempenho_por_plataforma) == 1
    assert dashboard.desempenho_por_plataforma[0].plataforma == "Instagram"
    assert dashboard.desempenho_por_plataforma[0].total_alcance == 500


def test_platform_spelling_does_not_follow_listing_order():
    service, content_repository, metric_repository = make_service()

    # A listagem ordena por data de publicação decrescente, então o
    # conteúdo cadastrado primeiro aparece primeiro quando é também o
    # publicado mais tarde. Nessa ordem, a grafia vencedora não pode ser a
    # da linha seguinte.
    cadastrado_primeiro = create_content(
        content_repository,
        titulo="Publicado hoje",
        plataforma="Instagram",
        data_publicacao=date.today(),
    )
    cadastrado_depois = create_content(
        content_repository,
        titulo="Publicado ontem",
        plataforma="INSTAGRAM",
        data_publicacao=date.today() - timedelta(days=1),
    )

    create_metric(metric_repository, cadastrado_primeiro.id, alcance=100)
    create_metric(metric_repository, cadastrado_depois.id, alcance=200)

    dashboard = service.get(user_id=1)

    assert len(dashboard.desempenho_por_plataforma) == 1
    assert (
        dashboard.desempenho_por_plataforma[0].plataforma == "Instagram"
    )


def test_platform_performance_is_ordered_by_reach_desc():
    service, content_repository, metric_repository = make_service()

    menor = create_content(
        content_repository,
        titulo="No TikTok",
        plataforma="TikTok",
    )
    maior = create_content(
        content_repository,
        titulo="No YouTube",
        plataforma="YouTube",
    )

    create_metric(metric_repository, menor.id, alcance=100)
    create_metric(metric_repository, maior.id, alcance=900)

    dashboard = service.get(user_id=1)

    assert [
        item.plataforma
        for item in dashboard.desempenho_por_plataforma
    ] == ["YouTube", "TikTok"]


def test_dashboard_ignores_contents_of_other_users():
    service, content_repository, metric_repository = make_service()

    proprio = create_content(
        content_repository,
        titulo="Meu conteúdo",
    )
    alheio = create_content(
        content_repository,
        user_id=2,
        titulo="Conteúdo de outro",
        plataforma="TikTok",
    )

    create_metric(
        metric_repository,
        proprio.id,
        visualizacoes=100,
        curtidas=10,
        alcance=100,
    )
    create_metric(
        metric_repository,
        alheio.id,
        visualizacoes=9999,
        curtidas=9999,
        alcance=9999,
    )

    dashboard = service.get(user_id=1)

    assert dashboard.total_conteudos == 1
    assert dashboard.total_visualizacoes == 100
    assert [item.titulo for item in dashboard.maiores_alcances] == [
        "Meu conteúdo"
    ]
    assert [
        item.plataforma
        for item in dashboard.desempenho_por_plataforma
    ] == ["Instagram"]


def test_dashboard_engagement_agrees_with_the_shared_calculation():
    # O RF04 exige que o painel reaproveite o cálculo, e não faça o
    # próprio. Isso não tinha teste: uma segunda implementação, com
    # arredondamento diferente ou outra ordem de soma, passaria calada
    # e o índice do painel divergiria do que a tela de detalhe mostra
    # para a mesma medição.
    service, content_repository, metric_repository = make_service()

    content = create_content(content_repository)

    metric = create_metric(
        metric_repository,
        content.id,
        curtidas=37,
        comentarios=11,
        compartilhamentos=5,
        alcance=433,
    )

    dashboard = service.get(user_id=1)

    esperado = engagement_of(metric)

    assert dashboard.engajamento_geral == esperado
    assert dashboard.maiores_alcances[0].engajamento == esperado
    assert (
        dashboard.desempenho_por_plataforma[0].engajamento
        == esperado
    )
