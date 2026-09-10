from app.domain.metric import Metric


def calculate_engagement(
    curtidas: int,
    comentarios: int,
    compartilhamentos: int,
    alcance: int,
) -> float | None:
    # Alcance zero não significa engajamento zero: significa que o
    # índice não é calculável, então o painel deve exibir ausência
    # de dado em vez de um desempenho falsamente nulo.
    if alcance == 0:
        return None

    interacoes = curtidas + comentarios + compartilhamentos

    return round(
        interacoes / alcance * 100,
        2,
    )


def engagement_of(metric: Metric) -> float | None:
    # Quais campos contam como interação é decisão de uma linha só. Escrita
    # em dois serviços, uma mudança nela deixaria o índice do painel e o da
    # medição discordando sobre a mesma medição.
    return calculate_engagement(
        curtidas=metric.curtidas,
        comentarios=metric.comentarios,
        compartilhamentos=metric.compartilhamentos,
        alcance=metric.alcance,
    )
