from app.domain.dashboard import Dashboard, DashboardContent
from app.repositories.content_repository import ContentRepository
from app.repositories.metric_repository import MetricRepository
from app.services.engagement import calculate_engagement

_LIMITE_MELHORES_CONTEUDOS = 5


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
    def _best_contents(
        measured,
    ) -> list[DashboardContent]:
        ranking = []

        for content, metric in measured:
            engajamento = calculate_engagement(
                curtidas=metric.curtidas,
                comentarios=metric.comentarios,
                compartilhamentos=metric.compartilhamentos,
                alcance=metric.alcance,
            )

            # Sem índice calculável o conteúdo não é comparável com os
            # demais, e entrar como zero o rebaixaria sem ter ido mal.
            if engajamento is None:
                continue

            ranking.append(
                DashboardContent(
                    conteudo_id=content.id,
                    titulo=content.titulo,
                    plataforma=content.plataforma,
                    engajamento=engajamento,
                    data_referencia=metric.data_referencia,
                )
            )

        ranking.sort(
            key=lambda item: (
                item.engajamento,
                item.data_referencia,
                item.conteudo_id,
            ),
            reverse=True,
        )

        return ranking[:_LIMITE_MELHORES_CONTEUDOS]

    def get(
        self,
        user_id: int,
    ) -> Dashboard:
        contents = self._content_repository.list_by_user(user_id)

        measured = self._measured_contents(contents)

        metrics = [metric for _, metric in measured]

        total_visualizacoes = sum(metric.visualizacoes for metric in metrics)
        total_curtidas = sum(metric.curtidas for metric in metrics)
        total_comentarios = sum(metric.comentarios for metric in metrics)
        total_compartilhamentos = sum(metric.compartilhamentos for metric in metrics)
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
            engajamento_geral=calculate_engagement(
                curtidas=total_curtidas,
                comentarios=total_comentarios,
                compartilhamentos=total_compartilhamentos,
                alcance=total_alcance,
            ),
            melhores_conteudos=self._best_contents(measured),
        )
