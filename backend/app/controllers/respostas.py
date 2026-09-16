# Descrições reutilizadas na documentação OpenAPI. O texto do 401 vale para
# todas as rotas protegidas, e repeti-lo em cada uma faria as descrições
# divergirem com o tempo.

from app.config import get_settings


def prazo_do_token() -> str:
    """Quanto vale o token, lido da configuração.

    Estava escrito "trinta minutos" em três lugares. Quem subisse a API
    com outro JWT_EXPIRES_MINUTES ficava com a documentação mentindo, e
    é documentação que quem integra lê para decidir quando renovar.
    """
    minutos = get_settings().jwt_expires_minutes

    if minutos == 1:
        return "1 minuto"

    return f"{minutos} minutos"


SEM_SESSAO = {
    401: {
        "description": "Token ausente, inválido ou expirado.",
    },
}

CONTEUDO_NAO_ENCONTRADO = {
    404: {
        "description": (
            "Conteúdo inexistente ou pertencente a outro usuário."
        ),
    },
}

METRICA_NAO_ENCONTRADA = {
    404: {
        "description": (
            "Conteúdo ou medição inexistente, ou pertencente a outro "
            "usuário."
        ),
    },
}

MEDICAO_DUPLICADA = {
    409: {
        "description": (
            "Já existe medição deste conteúdo na data informada. A "
            "unicidade é por conteúdo e data de referência: corrija a "
            "medição existente ou escolha outra data."
        ),
    },
}
