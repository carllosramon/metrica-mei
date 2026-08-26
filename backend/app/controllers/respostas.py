# Descrições reutilizadas na documentação OpenAPI. O texto do 401 vale para
# todas as rotas protegidas, e repeti-lo em cada uma faria as descrições
# divergirem com o tempo.

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
