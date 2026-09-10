from app.domain.dashboard import (
    Dashboard,
    DashboardContent,
    DashboardPlatform,
)
from app.repositories.content_repository import ContentRepository
from app.repositories.metric_repository import MetricRepository
from app.services.engagement import (
    calculate_engagement,
    engagement_of,
)


_LIMITE_MAIORES_ALCANCES = 5


class DashboardService:
    def __init__(
        self,
        content_repository: ContentRepository,
        metric_repository: MetricRepository,
    ):
        self._content_repository = content_repository
        self._metric_repository = metric_repository

    def _measured_contents(
        self,
        contents,
    ):
        # Cada conteúdo entra nos totais uma única vez, pela medição mais
        # recente: os snapshots são cumulativos, e somar o histórico inteiro
        # contaria de novo tudo o que já estava nas medições anteriores.
        identificadores = []

        for content in contents:
            identificadores.append(content.id)

        medicao_do_conteudo = (
            self._metric_repository.latest_by_contents(
                identificadores
            )
        )

        measured = []

        for content in contents:
            metric = medicao_do_conteudo.get(content.id)

            if metric is None:
                continue

            measured.append((content, metric))

        return measured

    @staticmethod
    def _totais(metrics) -> dict[str, int]:
        # Os mesmos cinco totais servem à conta inteira e a cada rede. Somar
        # em dois lugares deixava os números do topo e da tabela livres para
        # divergirem quando um deles mudasse.
        return {
            "visualizacoes": sum(
                metric.visualizacoes for metric in metrics
            ),
            "curtidas": sum(metric.curtidas for metric in metrics),
            "comentarios": sum(metric.comentarios for metric in metrics),
            "compartilhamentos": sum(
                metric.compartilhamentos for metric in metrics
            ),
            "alcance": sum(metric.alcance for metric in metrics),
        }

    @staticmethod
    def _sum_engagement(metrics) -> float | None:
        return calculate_engagement(
            curtidas=sum(metric.curtidas for metric in metrics),
            comentarios=sum(metric.comentarios for metric in metrics),
            compartilhamentos=sum(
                metric.compartilhamentos for metric in metrics
            ),
            alcance=sum(metric.alcance for metric in metrics),
        )

    @staticmethod
    def _biggest_reaches(
        measured,
    ) -> list[DashboardContent]:
        ranking = []

        for content, metric in measured:
            ranking.append(
                DashboardContent(
                    conteudo_id=content.id,
                    titulo=content.titulo,
                    plataforma=content.plataforma,
                    alcance=metric.alcance,
                    engajamento=engagement_of(metric),
                    data_referencia=metric.data_referencia,
                )
            )

        ranking.sort(
            key=lambda item: (
                item.alcance,
                item.data_referencia,
                item.conteudo_id,
            ),
            reverse=True,
        )

        return ranking[:_LIMITE_MAIORES_ALCANCES]

    @classmethod
    def _platform_performance(
        cls,
        contents,
        measured,
    ) -> list[DashboardPlatform]:
        medicao_do_conteudo = {
            content.id: metric for content, metric in measured
        }

        # A plataforma é texto livre digitado pelo usuário, então "Instagram"
        # e "instagram" precisam cair no mesmo grupo — senão o painel
        # mostraria a mesma rede duas vezes por diferença de maiúscula.
        grupos: dict[str, list] = {}
        contagens: dict[str, int] = {}
        grafias: dict[str, tuple[int, str]] = {}

        # O laço percorre todos os conteúdos, e não só os medidos: uma rede
        # onde o usuário publicou e ainda não mediu precisa aparecer zerada
        # em vez de desaparecer do painel.
        for content in contents:
            chave = content.plataforma.casefold()

            contagens[chave] = contagens.get(chave, 0) + 1
            grupos.setdefault(chave, [])

            metric = medicao_do_conteudo.get(content.id)

            if metric is not None:
                grupos[chave].append(metric)

            # Entre grafias concorrentes vale a do conteúdo cadastrado
            # primeiro, para que o rótulo não mude conforme a ordenação da
            # listagem.
            registrada = grafias.get(chave)

            if registrada is None or content.id < registrada[0]:
                grafias[chave] = (content.id, content.plataforma)

        desempenho = []

        for chave, metrics in grupos.items():
            totais = cls._totais(metrics)

            desempenho.append(
                DashboardPlatform(
                    plataforma=grafias[chave][1],
                    total_conteudos=contagens[chave],
                    conteudos_com_metricas=len(metrics),
                    total_visualizacoes=totais["visualizacoes"],
                    total_curtidas=totais["curtidas"],
                    total_comentarios=totais["comentarios"],
                    total_compartilhamentos=totais["compartilhamentos"],
                    total_alcance=totais["alcance"],
                    engajamento=cls._sum_engagement(metrics),
                )
            )

        desempenho.sort(
            key=lambda item: (
                -item.total_alcance,
                item.plataforma.casefold(),
            ),
        )

        return desempenho

    def get(
        self,
        user_id: int,
    ) -> Dashboard:
        contents = self._content_repository.list_by_user(user_id)

        measured = self._measured_contents(contents)

        metrics = [metric for _, metric in measured]

        totais = self._totais(metrics)

        return Dashboard(
            total_conteudos=len(contents),
            conteudos_com_metricas=len(measured),
            total_visualizacoes=totais["visualizacoes"],
            total_curtidas=totais["curtidas"],
            total_comentarios=totais["comentarios"],
            total_compartilhamentos=totais["compartilhamentos"],
            total_alcance=totais["alcance"],
            # O índice da conta sai dos totais, e não da média dos índices
            # individuais: na média, um conteúdo de alcance 10 pesaria o
            # mesmo que um de alcance 50.000.
            engajamento_geral=self._sum_engagement(metrics),
            desempenho_por_plataforma=self._platform_performance(
                contents,
                measured,
            ),
            maiores_alcances=self._biggest_reaches(measured),
        )
