from fastapi import APIRouter, Depends, status

from app.controllers.respostas import (
    CONTEUDO_NAO_ENCONTRADO,
    SEM_SESSAO,
)
from app.dependencies import (
    get_content_service,
    get_current_user,
)
from app.schemas.content import (
    ContentCreateRequest,
    ContentListItemResponse,
    ContentResponse,
    ContentUpdateRequest,
)
from app.services.content_service import ContentService


router = APIRouter(
    tags=["conteudos"],
)


_DADOS_INVALIDOS = {
    422: {
        "description": (
            "Título, plataforma ou tipo fora dos limites de tamanho, data "
            "de publicação no futuro, ou URL sem esquema http/https."
            "\n\n"
            "A URL precisa ser um endereço completo, e não só o esquema: "
            "`https://` sozinho é recusado. O esquema aceita caixa alta, "
            "porque `HTTPS://` é válido, e o endereço inteiro cabe em 500 "
            "caracteres."
        ),
    },
}


@router.post(
    "/conteudos",
    response_model=ContentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar conteúdo",
    description=(
        "Registra uma publicação do usuário autenticado. A data de "
        "publicação não pode ser futura, porque medição é registro de "
        "desempenho já ocorrido."
        "\n\n"
        "`url_publicacao` é opcional e, quando informada, precisa começar "
        "com `http://` ou `https://`."
    ),
    responses={**SEM_SESSAO, **_DADOS_INVALIDOS},
)
def create_content(
    payload: ContentCreateRequest,
    current_user=Depends(get_current_user),
    service: ContentService = Depends(
        get_content_service
    ),
):
    return service.create(
        user_id=current_user.id,
        titulo=payload.titulo,
        plataforma=payload.plataforma,
        tipo=payload.tipo,
        data_publicacao=payload.data_publicacao,
        url_publicacao=payload.url_publicacao,
    )


@router.get(
    "/conteudos",
    response_model=list[ContentListItemResponse],
    summary="Listar meus conteúdos",
    description=(
        "Devolve apenas os conteúdos do usuário autenticado, dos mais "
        "recentes para os mais antigos pela data de publicação."
        "\n\n"
        "`ultima_medicao` é a data de referência da medição mais recente "
        "do conteúdo, e vem nula quando ele nunca foi medido. É o que "
        "responde, sem abrir um por um, o que está faltando anotar."
    ),
    responses=SEM_SESSAO,
)
def list_contents(
    current_user=Depends(get_current_user),
    service: ContentService = Depends(
        get_content_service
    ),
):
    return service.list(
        user_id=current_user.id
    )


@router.get(
    "/conteudos/{content_id}",
    response_model=ContentResponse,
    summary="Consultar um conteúdo",
    description=(
        "Conteúdo de outro usuário responde `404`, e não `403`: confirmar "
        "que o registro existe revelaria dado alheio."
    ),
    responses={**SEM_SESSAO, **CONTEUDO_NAO_ENCONTRADO},
)
def get_content(
    content_id: int,
    current_user=Depends(get_current_user),
    service: ContentService = Depends(
        get_content_service
    ),
):
    return service.get(
        content_id=content_id,
        user_id=current_user.id,
    )


@router.patch(
    "/conteudos/{content_id}",
    response_model=ContentResponse,
    summary="Editar um conteúdo",
    description=(
        "Altera somente os campos enviados; os ausentes permanecem como "
        "estão."
        "\n\n"
        "`url_publicacao` é o único campo que aceita `null`, e o valor nulo "
        "remove a URL. Nos demais campos, `null` explícito é recusado."
    ),
    responses={
        **SEM_SESSAO,
        **CONTEUDO_NAO_ENCONTRADO,
        **_DADOS_INVALIDOS,
    },
)
def update_content(
    content_id: int,
    payload: ContentUpdateRequest,
    current_user=Depends(get_current_user),
    service: ContentService = Depends(
        get_content_service
    ),
):
    changes = payload.model_dump(
        exclude_unset=True,
    )

    return service.update(
        content_id=content_id,
        user_id=current_user.id,
        **changes,
    )


@router.delete(
    "/conteudos/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir um conteúdo",
    description=(
        "Remove o conteúdo e, em cascata, todas as suas medições. Medição "
        "sem conteúdo não teria significado nem dono, já que o vínculo com "
        "o usuário passa pelo conteúdo."
    ),
    responses={**SEM_SESSAO, **CONTEUDO_NAO_ENCONTRADO},
)
def delete_content(
    content_id: int,
    current_user=Depends(get_current_user),
    service: ContentService = Depends(
        get_content_service
    ),
):
    service.delete(
        content_id=content_id,
        user_id=current_user.id,
    )
