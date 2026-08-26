from app.main import app


METODOS_HTTP = {
    "get",
    "post",
    "patch",
    "put",
    "delete",
}


def listar_operacoes():
    esquema = app.openapi()

    for caminho, metodos in esquema["paths"].items():
        for metodo, operacao in metodos.items():
            if metodo in METODOS_HTTP:
                yield f"{metodo.upper()} {caminho}", operacao


def test_toda_operacao_tem_resumo():
    sem_resumo = [
        rota
        for rota, operacao in listar_operacoes()
        if not operacao.get("summary")
    ]

    assert sem_resumo == []


def test_toda_operacao_tem_descricao():
    # O RNF04 exige API documentada. Sem esta verificação, um endpoint novo
    # entraria sem explicação e o requisito voltaria a valer só no papel.
    sem_descricao = [
        rota
        for rota, operacao in listar_operacoes()
        if not operacao.get("description")
    ]

    assert sem_descricao == []


def test_toda_operacao_pertence_a_um_grupo_descrito():
    grupos_descritos = {
        grupo["name"] for grupo in app.openapi()["tags"]
    }

    sem_grupo = []

    for rota, operacao in listar_operacoes():
        tags = operacao.get("tags", [])

        if not tags or not set(tags) <= grupos_descritos:
            sem_grupo.append(rota)

    assert sem_grupo == []


def test_a_api_descreve_a_autenticacao_e_a_convencao_de_erros():
    descricao = app.openapi()["info"]["description"]

    assert "Authorization: Bearer" in descricao
    assert "detail" in descricao


def test_erros_de_negocio_estao_documentados():
    esquema = app.openapi()

    registrar_metrica = esquema["paths"][
        "/conteudos/{content_id}/metricas"
    ]["post"]

    # O 409 é o erro que o usuário mais encontra: a documentação precisa
    # dizer que a unicidade é por conteúdo e data.
    conflito = registrar_metrica["responses"]["409"]["description"]

    assert "data de referência" in conflito

    consultar_conteudo = esquema["paths"]["/conteudos/{content_id}"]["get"]

    assert "404" in consultar_conteudo["responses"]
    assert "401" in consultar_conteudo["responses"]
