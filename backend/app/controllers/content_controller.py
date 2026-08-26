from fastapi import APIRouter, Depends, HTTPException, status

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
    ContentResponse,
    ContentUpdateRequest,
)
from app.services.content_service import (
    ContentNotFoundError,
    ContentService,
    InvalidContentError,
)


router = APIRouter(
    tags=["conteudos"],
)


_DADOS_INVALIDOS = {
    422: {
        "description": (
            "Título, plataforma ou tipo fora dos limites de tamanho, data "
            "de publicação no futuro, ou URL sem esquema http/https."
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
    try:
        return service.create(
            user_id=current_user.id,
            titulo=payload.titulo,
            plataforma=payload.plataforma,
            tipo=payload.tipo,
            data_publicacao=payload.data_publicacao,
            url_publicacao=payload.url_publicacao,
        )

    except InvalidContentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Dados do conteúdo inválidos.",
        ) from exc


@router.get(
    "/conteudos",
    response_model=list[ContentResponse],
    summary="Listar meus conteúdos",
    description=(
        "Devolve apenas os conteúdos do usuário autenticado, dos mais "
        "recentes para os mais antigos pela data de publicação."
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
    try:
        return service.get(
            content_id=content_id,
            user_id=current_user.id,
        )

    except ContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conteúdo não encontrado.",
        ) from exc


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

    try:
        return service.update(
            content_id=content_id,
            user_id=current_user.id,
            **changes,
        )

    except ContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conteúdo não encontrado.",
        ) from exc

    except InvalidContentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Dados do conteúdo inválidos.",
        ) from exc


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
    try:
        service.delete(
            content_id=content_id,
            user_id=current_user.id,
        )

    except ContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conteúdo não encontrado.",
        ) from exc
