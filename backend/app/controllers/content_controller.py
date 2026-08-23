from fastapi import APIRouter, Depends, HTTPException, status

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


@router.post(
    "/conteudos",
    response_model=ContentResponse,
    status_code=status.HTTP_201_CREATED,
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
    )


@router.get(
    "/conteudos",
    response_model=list[ContentResponse],
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

