from app.domain.dashboard import (
    Dashboard,
    DashboardContent,
    DashboardPlatform,
)
from app.repositories.content_repository import ContentRepository
from app.repositories.metric_repository import MetricRepository
from app.services.engagement import calculate_engagement


_LIMITE_MAIORES_ALCANCES = 5


class DashboardService:
    def __init__(
        self,
        content_repository: ContentRepository,
        metric_repository: MetricRepository,
    ):
        self._content_repository = content_repository
        self._metric_repository = metric_repository

    def _latest_metric(
        self,
        content_id: int,
    ):
        # list_by_content já devolve em data_referencia DESC, id DESC, então
        # o primeiro item é a medição mais recente do conteúdo.
        metrics = self._metric_repository.list_by_content(content_id)

        if not metrics:
            return None

        return metrics[0]

    def _measured_contents(
        self,
        contents,
    ):
        # Cada conteúdo entra nos totais uma única vez, pela medição mais
        # recente: os snapshots são cumulativos, e somar o histórico inteiro
        # contaria de novo tudo o que já estava nas medições anteriores.
        measured = []

        for content in contents:
            metric = self._latest_metric(content.id)

            if metric is None:
                continue

            measured.append((content, metric))

        return measured

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
                    engajamento=calculate_engagement(
                        curtidas=metric.curtidas,
                        comentarios=metric.comentarios,
                        compartilhamentos=metric.compartilhamentos,
                        alcance=metric.alcance,
                    ),
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
        measured,
    ) -> list[DashboardPlatform]:
        # A plataforma é texto livre digitado pelo usuário, então "Instagram"
        # e "instagram" precisam cair no mesmo grupo — senão o painel
        # mostraria a mesma rede duas vezes por diferença de maiúscula.
        grupos: dict[str, list] = {}
        grafias: dict[str, tuple[int, str]] = {}

        for content, metric in measured:
            chave = content.plataforma.casefold()

            grupos.setdefault(chave, []).append(metric)

            # Entre grafias concorrentes vale a do conteúdo cadastrado
            # primeiro, para que o rótulo não mude conforme a ordenação da
            # listagem.
            registrada = grafias.get(chave)

            if registrada is None or content.id < registrada[0]:
                grafias[chave] = (content.id, content.plataforma)

        desempenho = []

        for chave, metrics in grupos.items():
            desempenho.append(
                DashboardPlatform(
                    plataforma=grafias[chave][1],
                    total_conteudos=len(metrics),
                    total_visualizacoes=sum(
                        metric.visualizacoes for metric in metrics
                    ),
                    total_curtidas=sum(
                        metric.curtidas for metric in metrics
                    ),
                    total_comentarios=sum(
                        metric.comentarios for metric in metrics
                    ),
                    total_compartilhamentos=sum(
                        metric.compartilhamentos for metric in metrics
                    ),
                    total_alcance=sum(
                        metric.alcance for metric in metrics
                    ),
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

        total_visualizacoes = sum(
            metric.visualizacoes for metric in metrics
        )
        total_curtidas = sum(metric.curtidas for metric in metrics)
        total_comentarios = sum(metric.comentarios for metric in metrics)
        total_compartilhamentos = sum(
            metric.compartilhamentos for metric in metrics
        )
        total_alcance = sum(metric.alcance for metric in metrics)

        return Dashboard(
            total_conteudos=len(contents),
            conteudos_com_metricas=len(measured),
            total_visualizacoes=total_visualizacoes,
            total_curtidas=total_curtidas,
            total_comentarios=total_comentarios,
            total_compartilhamentos=total_compartilhamentos,
            total_alcance=total_alcance,
            # O índice da conta sai dos totais, e não da média dos índices
            # individuais: na média, um conteúdo de alcance 10 pesaria o
            # mesmo que um de alcance 50.000.
            engajamento_geral=self._sum_engagement(metrics),
            desempenho_por_plataforma=self._platform_performance(measured),
            maiores_alcances=self._biggest_reaches(measured),
        )
