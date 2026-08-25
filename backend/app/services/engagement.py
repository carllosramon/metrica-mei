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
