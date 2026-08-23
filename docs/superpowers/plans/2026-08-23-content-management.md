# Content Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o Marco 0.3 do MetricaMEI: CRUD autenticado de conteúdos digitais com ownership por usuário, arquitetura Controller–Service–Repository, persistência SQLAlchemy/Alembic e testes unitários e de integração.

**Architecture:** O fluxo HTTP resolve o usuário autenticado por uma dependência compartilhada, passa apenas `user_id` ao `ContentService`, e o Service depende do protocolo `ContentRepository`. A aplicação usa `SQLAlchemyContentRepository`; testes unitários usam `InMemoryContentRepository`. Consultas protegidas por ownership sempre usam `content_id` junto de `user_id`.

**Tech Stack:** Python 3.14, FastAPI, Pydantic, SQLAlchemy 2, Alembic, SQLite em desenvolvimento/testes, JWT HS256, Pytest.

**Spec:** `docs/superpowers/specs/2026-08-23-content-management-design.md`

## Global Constraints

- O marco implementa `POST /conteudos`, `GET /conteudos`, `GET /conteudos/{id}`, `PATCH /conteudos/{id}` e `DELETE /conteudos/{id}`.
- Todos os endpoints de conteúdos exigem JWT válido.
- `usuario_id` vem exclusivamente do usuário autenticado; não entra no JSON e não sai na resposta HTTP.
- `titulo`: obrigatório, `strip()`, 1–200 caracteres.
- `plataforma`: obrigatória, texto livre, `strip()`, 1–50 caracteres, preservando capitalização.
- `tipo`: obrigatório, texto livre, `strip()`, 1–50 caracteres, preservando capitalização.
- `data_publicacao`: `date`, obrigatória, aceita hoje/passado e rejeita futuro.
- Títulos duplicados são permitidos.
- Não adicionar paginação, filtros, soft delete, agendamento, `atualizado_em`, métricas, dashboard ou enums de plataforma/tipo neste marco.
- Listagem ordenada por `data_publicacao DESC, id DESC`.
- Conteúdo inexistente e conteúdo de outro usuário produzem o mesmo `404`.
- `DELETE` bem-sucedido retorna `204 No Content`.
- `PATCH` vazio é inválido e retorna `422`.
- As regras essenciais também existem no `ContentService`, independentemente dos schemas HTTP.
- A migration existente `0001_create_usuarios` não deve ser alterada.
- Desenvolvimento em TDD: RED → confirmar falha correta → GREEN mínimo → teste específico → suíte completa → refatoração.
- Fazer commits pequenos ao final de cada tarefa concluída.

---

## Mapa de arquivos

### Criar

```text
backend/app/domain/content.py
backend/app/repositories/content_repository.py
backend/app/repositories/in_memory_content_repository.py
backend/app/repositories/sqlalchemy_content_repository.py
backend/app/services/content_service.py
backend/app/schemas/content.py
backend/app/controllers/content_controller.py
backend/alembic/versions/0002_create_conteudos.py
backend/tests/unit/test_content_service_create.py
backend/tests/unit/test_content_service_crud.py
backend/tests/integration/test_sqlalchemy_content_repository.py
backend/tests/integration/test_content_api.py
backend/tests/integration/test_content_ownership.py
```

### Modificar

```text
backend/app/dependencies.py
backend/app/controllers/auth_controller.py
backend/app/database/models.py
backend/app/main.py
README.md
```

---

### Task 1: Centralizar a resolução do usuário autenticado

**Files:**
- Modify: `backend/app/dependencies.py`
- Modify: `backend/app/controllers/auth_controller.py`
- Test: `backend/tests/integration/test_auth_me.py`

**Interfaces:**
- Consumes: `AuthService.get_current_user(token: str) -> User`
- Produces: `get_current_user(...) -> User`, reutilizável por qualquer Controller protegido.

- [ ] **Step 1: Confirmar o baseline antes da refatoração**

No PowerShell:

```powershell
cd C:\Users\Cliente\Documents\metrica-mei\backend
.\.venv\Scripts\Activate.ps1
python -m pytest tests/integration/test_auth_me.py -v
python -m pytest -v
```

Expected:

```text
test_auth_me.py: todos os testes PASS
suíte completa: 27 testes PASS antes de adicionar o Marco 0.3
```

Se o baseline já falhar, parar e corrigir a causa antes de continuar.

- [ ] **Step 2: Mover a lógica Bearer para `dependencies.py`**

Substituir `backend/app/dependencies.py` por:

```python
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.connection import (
    create_engine_from_url,
    create_session_factory,
)
from app.domain.user import User
from app.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.security.jwt import TokenService
from app.security.password import PasswordService
from app.services.auth_service import AuthService, UnauthenticatedError


security = HTTPBearer(
    auto_error=False,
)


@lru_cache
def get_engine():
    return create_engine_from_url(
        get_settings().database_url
    )


@lru_cache
def get_session_factory():
    return create_session_factory(
        get_engine()
    )


def get_db_session():
    with get_session_factory()() as session:
        yield session


def get_user_repository(
    session: Session = Depends(get_db_session),
):
    return SQLAlchemyUserRepository(session)


def get_auth_service(
    repository=Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
):
    if not settings.jwt_secret:
        raise RuntimeError(
            "JWT_SECRET não configurado."
        )

    return AuthService(
        repository,
        PasswordService(),
        TokenService(
            settings.jwt_secret,
            settings.jwt_algorithm,
            settings.jwt_expires_minutes,
        ),
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    service: AuthService = Depends(get_auth_service),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    try:
        return service.get_current_user(
            credentials.credentials
        )

    except UnauthenticatedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc
```

- [ ] **Step 3: Refatorar `/auth/me` para usar a nova dependência**

Em `backend/app/controllers/auth_controller.py`, trocar os imports relacionados à segurança por:

```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_auth_service, get_current_user
from app.domain.user import User
```

No import de exceções do `auth_service`, manter apenas:

```python
from app.services.auth_service import (
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
```

Remover do arquivo:

```python
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
```

Remover também:

```python
security = HTTPBearer(
    auto_error=False,
)
```

Substituir a função `me` inteira por:

```python
@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: User = Depends(get_current_user),
):
    return current_user
```

- [ ] **Step 4: Verificar que a refatoração preservou o comportamento**

Run:

```powershell
python -m pytest tests/integration/test_auth_me.py -v
python -m pytest -v
```

Expected:

```text
PASS: usuário autenticado continua recebendo 200
PASS: sem token continua recebendo 401
PASS: token inválido continua recebendo 401
PASS: token expirado continua recebendo 401
PASS: toda a suíte anterior continua verde
```

- [ ] **Step 5: Commit**

```powershell
git add backend/app/dependencies.py backend/app/controllers/auth_controller.py
git commit -m "refactor: centralize authenticated user dependency"
```

---

### Task 2: Criar domínio, contrato, repository em memória e criação no Service

**Files:**
- Create: `backend/app/domain/content.py`
- Create: `backend/app/repositories/content_repository.py`
- Create: `backend/app/repositories/in_memory_content_repository.py`
- Create: `backend/app/services/content_service.py`
- Create: `backend/tests/unit/test_content_service_create.py`

**Interfaces:**
- Produces: `Content`
- Produces: `ContentRepository`
- Produces: `InMemoryContentRepository`
- Produces: `InvalidContentError`
- Produces: `ContentNotFoundError`
- Produces: `ContentService.create(user_id, titulo, plataforma, tipo, data_publicacao) -> Content`

- [ ] **Step 1: Escrever os testes RED da criação e validação**

Criar `backend/tests/unit/test_content_service_create.py`:

```python
from datetime import date, timedelta

import pytest

from app.repositories.in_memory_content_repository import (
    InMemoryContentRepository,
)
from app.services.content_service import (
    ContentService,
    InvalidContentError,
)


def make_service():
    repository = InMemoryContentRepository()
    service = ContentService(repository)
    return service, repository


def valid_data():
    return {
        "titulo": "Meu conteúdo",
        "plataforma": "Instagram",
        "tipo": "Reels",
        "data_publicacao": date.today(),
    }


def test_create_normalizes_text_and_assigns_user():
    service, repository = make_service()

    content = service.create(
        user_id=7,
        titulo="  Meu conteúdo  ",
        plataforma="  Instagram  ",
        tipo="  Reels  ",
        data_publicacao=date.today(),
    )

    assert content.id == 1
    assert content.usuario_id == 7
    assert content.titulo == "Meu conteúdo"
    assert content.plataforma == "Instagram"
    assert content.tipo == "Reels"
    assert content.data_publicacao == date.today()
    assert repository.get_by_id_and_user(1, 7) == content


def test_create_allows_duplicate_titles():
    service, _ = make_service()

    first = service.create(
        user_id=1,
        titulo="Título repetido",
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=date.today(),
    )
    second = service.create(
        user_id=1,
        titulo="Título repetido",
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=date.today(),
    )

    assert first.id != second.id
    assert first.titulo == second.titulo


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("titulo", ""),
        ("titulo", "   "),
        ("titulo", "A" * 201),
        ("plataforma", ""),
        ("plataforma", "   "),
        ("plataforma", "A" * 51),
        ("tipo", ""),
        ("tipo", "   "),
        ("tipo", "A" * 51),
    ],
)
def test_create_rejects_invalid_text(field, value):
    service, _ = make_service()
    data = valid_data()
    data[field] = value

    with pytest.raises(InvalidContentError):
        service.create(
            user_id=1,
            **data,
        )


def test_create_accepts_past_date():
    service, _ = make_service()

    content = service.create(
        user_id=1,
        titulo="Conteúdo antigo",
        plataforma="Instagram",
        tipo="Carrossel",
        data_publicacao=date.today() - timedelta(days=30),
    )

    assert content.id == 1


def test_create_accepts_today():
    service, _ = make_service()

    content = service.create(
        user_id=1,
        titulo="Conteúdo de hoje",
        plataforma="Instagram",
        tipo="Post",
        data_publicacao=date.today(),
    )

    assert content.data_publicacao == date.today()


def test_create_rejects_future_date():
    service, _ = make_service()

    with pytest.raises(InvalidContentError):
        service.create(
            user_id=1,
            titulo="Conteúdo futuro",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today() + timedelta(days=1),
        )
```

- [ ] **Step 2: Rodar o teste para verificar a falha correta**

Run:

```powershell
python -m pytest tests/unit/test_content_service_create.py -v
```

Expected inicialmente:

```text
FAIL durante import
ModuleNotFoundError para os módulos de conteúdo que ainda não existem
```

Essa é a falha RED esperada.

- [ ] **Step 3: Criar a entidade `Content`**

Criar `backend/app/domain/content.py`:

```python
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(slots=True)
class Content:
    id: int | None
    usuario_id: int
    titulo: str
    plataforma: str
    tipo: str
    data_publicacao: date
    criado_em: datetime
```

- [ ] **Step 4: Criar o protocolo `ContentRepository`**

Criar `backend/app/repositories/content_repository.py`:

```python
from typing import Protocol

from app.domain.content import Content


class ContentRepository(Protocol):
    def create(self, content: Content) -> Content: ...

    def list_by_user(self, user_id: int) -> list[Content]: ...

    def get_by_id_and_user(
        self,
        content_id: int,
        user_id: int,
    ) -> Content | None: ...

    def update(self, content: Content) -> Content: ...

    def delete(self, content: Content) -> None: ...
```

- [ ] **Step 5: Criar o repository em memória**

Criar `backend/app/repositories/in_memory_content_repository.py`:

```python
from dataclasses import replace

from app.domain.content import Content


class InMemoryContentRepository:
    def __init__(self):
        self._contents: dict[int, Content] = {}
        self._next_id = 1

    def create(self, content: Content) -> Content:
        stored_content = replace(
            content,
            id=self._next_id,
        )

        self._contents[self._next_id] = stored_content
        self._next_id += 1

        return stored_content

    def list_by_user(
        self,
        user_id: int,
    ) -> list[Content]:
        contents = [
            content
            for content in self._contents.values()
            if content.usuario_id == user_id
        ]

        return sorted(
            contents,
            key=lambda content: (
                content.data_publicacao,
                content.id or 0,
            ),
            reverse=True,
        )

    def get_by_id_and_user(
        self,
        content_id: int,
        user_id: int,
    ) -> Content | None:
        content = self._contents.get(content_id)

        if content is None:
            return None

        if content.usuario_id != user_id:
            return None

        return content

    def update(self, content: Content) -> Content:
        if content.id is None:
            raise ValueError(
                "Conteúdo sem id não pode ser atualizado."
            )

        self._contents[content.id] = content
        return content

    def delete(self, content: Content) -> None:
        if content.id is None:
            raise ValueError(
                "Conteúdo sem id não pode ser excluído."
            )

        self._contents.pop(content.id, None)
```

- [ ] **Step 6: Implementar o mínimo do `ContentService` para criação**

Criar `backend/app/services/content_service.py`:

```python
from datetime import date, datetime, timezone

from app.domain.content import Content
from app.repositories.content_repository import ContentRepository


class InvalidContentError(Exception):
    pass


class ContentNotFoundError(Exception):
    pass


class ContentService:
    def __init__(
        self,
        repository: ContentRepository,
    ):
        self._repository = repository

    @staticmethod
    def _normalize_text(
        value: object,
        max_length: int,
    ) -> str:
        if not isinstance(value, str):
            raise InvalidContentError

        normalized = value.strip()

        if not 1 <= len(normalized) <= max_length:
            raise InvalidContentError

        return normalized

    @staticmethod
    def _validate_publication_date(
        value: object,
    ) -> date:
        if (
            not isinstance(value, date)
            or isinstance(value, datetime)
        ):
            raise InvalidContentError

        if value > date.today():
            raise InvalidContentError

        return value

    def create(
        self,
        user_id: int,
        titulo: str,
        plataforma: str,
        tipo: str,
        data_publicacao: date,
    ) -> Content:
        content = Content(
            id=None,
            usuario_id=user_id,
            titulo=self._normalize_text(
                titulo,
                200,
            ),
            plataforma=self._normalize_text(
                plataforma,
                50,
            ),
            tipo=self._normalize_text(
                tipo,
                50,
            ),
            data_publicacao=self._validate_publication_date(
                data_publicacao
            ),
            criado_em=datetime.now(timezone.utc),
        )

        return self._repository.create(content)
```

- [ ] **Step 7: Confirmar GREEN**

Run:

```powershell
python -m pytest tests/unit/test_content_service_create.py -v
python -m pytest tests/unit -v
```

Expected:

```text
PASS em todos os testes de criação/validação
PASS em toda a suíte unitária anterior
```

- [ ] **Step 8: Commit**

```powershell
git add backend/app/domain/content.py `
        backend/app/repositories/content_repository.py `
        backend/app/repositories/in_memory_content_repository.py `
        backend/app/services/content_service.py `
        backend/tests/unit/test_content_service_create.py

git commit -m "feat: add content creation domain"
```

---

### Task 3: Completar listagem, busca, PATCH e exclusão no Service

**Files:**
- Modify: `backend/app/services/content_service.py`
- Test: `backend/tests/unit/test_content_service_crud.py`

**Interfaces:**
- Consumes: `ContentRepository`
- Produces:
  - `ContentService.list(user_id: int) -> list[Content]`
  - `ContentService.get(user_id: int, content_id: int) -> Content`
  - `ContentService.update(user_id: int, content_id: int, changes: dict[str, object]) -> Content`
  - `ContentService.delete(user_id: int, content_id: int) -> None`

- [ ] **Step 1: Escrever os testes RED dos casos de uso restantes**

Criar `backend/tests/unit/test_content_service_crud.py`:

```python
from datetime import date, timedelta

import pytest

from app.repositories.in_memory_content_repository import (
    InMemoryContentRepository,
)
from app.services.content_service import (
    ContentNotFoundError,
    ContentService,
    InvalidContentError,
)


def make_service():
    repository = InMemoryContentRepository()
    return ContentService(repository), repository


def create_content(
    service,
    user_id,
    titulo,
    data_publicacao=None,
):
    return service.create(
        user_id=user_id,
        titulo=titulo,
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=(
            data_publicacao
            if data_publicacao is not None
            else date.today()
        ),
    )


def test_list_returns_only_user_contents_in_expected_order():
    service, _ = make_service()

    old = create_content(
        service,
        1,
        "Antigo",
        date.today() - timedelta(days=1),
    )
    same_date_first = create_content(
        service,
        1,
        "Mesmo dia 1",
        date.today(),
    )
    same_date_second = create_content(
        service,
        1,
        "Mesmo dia 2",
        date.today(),
    )
    create_content(
        service,
        2,
        "Outro usuário",
        date.today(),
    )

    contents = service.list(user_id=1)

    assert [content.id for content in contents] == [
        same_date_second.id,
        same_date_first.id,
        old.id,
    ]


def test_get_returns_own_content():
    service, _ = make_service()
    created = create_content(service, 1, "Meu conteúdo")

    loaded = service.get(
        user_id=1,
        content_id=created.id,
    )

    assert loaded == created


@pytest.mark.parametrize(
    "content_id",
    [999],
)
def test_get_raises_not_found_for_missing_content(content_id):
    service, _ = make_service()

    with pytest.raises(ContentNotFoundError):
        service.get(
            user_id=1,
            content_id=content_id,
        )


def test_get_raises_not_found_for_other_users_content():
    service, _ = make_service()
    foreign = create_content(
        service,
        2,
        "Conteúdo de outro usuário",
    )

    with pytest.raises(ContentNotFoundError):
        service.get(
            user_id=1,
            content_id=foreign.id,
        )


def test_update_changes_only_sent_fields():
    service, _ = make_service()
    created = create_content(service, 1, "Título antigo")

    updated = service.update(
        user_id=1,
        content_id=created.id,
        changes={
            "titulo": "  Título novo  ",
        },
    )

    assert updated.titulo == "Título novo"
    assert updated.plataforma == created.plataforma
    assert updated.tipo == created.tipo
    assert updated.data_publicacao == created.data_publicacao
    assert updated.usuario_id == created.usuario_id
    assert updated.criado_em == created.criado_em


def test_update_rejects_empty_changes():
    service, _ = make_service()
    created = create_content(service, 1, "Conteúdo")

    with pytest.raises(InvalidContentError):
        service.update(
            user_id=1,
            content_id=created.id,
            changes={},
        )


def test_update_rejects_future_date():
    service, _ = make_service()
    created = create_content(service, 1, "Conteúdo")

    with pytest.raises(InvalidContentError):
        service.update(
            user_id=1,
            content_id=created.id,
            changes={
                "data_publicacao": (
                    date.today() + timedelta(days=1)
                )
            },
        )


def test_update_rejects_unknown_field():
    service, _ = make_service()
    created = create_content(service, 1, "Conteúdo")

    with pytest.raises(InvalidContentError):
        service.update(
            user_id=1,
            content_id=created.id,
            changes={
                "usuario_id": 999,
            },
        )


def test_update_other_users_content_looks_not_found():
    service, _ = make_service()
    foreign = create_content(service, 2, "Outro")

    with pytest.raises(ContentNotFoundError):
        service.update(
            user_id=1,
            content_id=foreign.id,
            changes={
                "titulo": "Tentativa",
            },
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("titulo", "   "),
        ("titulo", "A" * 201),
        ("plataforma", "   "),
        ("plataforma", "A" * 51),
        ("tipo", "   "),
        ("tipo", "A" * 51),
    ],
)
def test_update_rejects_invalid_text(field, value):
    service, _ = make_service()
    created = create_content(service, 1, "Conteúdo")

    with pytest.raises(InvalidContentError):
        service.update(
            user_id=1,
            content_id=created.id,
            changes={
                field: value,
            },
        )


def test_update_missing_content_looks_not_found():
    service, _ = make_service()

    with pytest.raises(ContentNotFoundError):
        service.update(
            user_id=1,
            content_id=999,
            changes={
                "titulo": "Novo título",
            },
        )


def test_delete_missing_content_looks_not_found():
    service, _ = make_service()

    with pytest.raises(ContentNotFoundError):
        service.delete(
            user_id=1,
            content_id=999,
        )


def test_delete_removes_own_content():
    service, _ = make_service()
    created = create_content(service, 1, "Excluir")

    service.delete(
        user_id=1,
        content_id=created.id,
    )

    with pytest.raises(ContentNotFoundError):
        service.get(
            user_id=1,
            content_id=created.id,
        )


def test_delete_other_users_content_looks_not_found():
    service, _ = make_service()
    foreign = create_content(service, 2, "Outro")

    with pytest.raises(ContentNotFoundError):
        service.delete(
            user_id=1,
            content_id=foreign.id,
        )

    assert service.get(
        user_id=2,
        content_id=foreign.id,
    ) == foreign
```

- [ ] **Step 2: Verificar RED**

Run:

```powershell
python -m pytest tests/unit/test_content_service_crud.py -v
```

Expected:

```text
FAIL com AttributeError porque list/get/update/delete ainda não existem no ContentService
```

- [ ] **Step 3: Completar o `ContentService`**

Adicionar no topo de `backend/app/services/content_service.py`:

```python
from dataclasses import replace
```

Dentro de `ContentService`, após `create`, adicionar:

```python
    def list(
        self,
        user_id: int,
    ) -> list[Content]:
        return self._repository.list_by_user(
            user_id
        )

    def get(
        self,
        user_id: int,
        content_id: int,
    ) -> Content:
        content = self._repository.get_by_id_and_user(
            content_id,
            user_id,
        )

        if content is None:
            raise ContentNotFoundError

        return content

    def update(
        self,
        user_id: int,
        content_id: int,
        changes: dict[str, object],
    ) -> Content:
        allowed_fields = {
            "titulo",
            "plataforma",
            "tipo",
            "data_publicacao",
        }

        if not changes:
            raise InvalidContentError

        if set(changes) - allowed_fields:
            raise InvalidContentError

        content = self.get(
            user_id=user_id,
            content_id=content_id,
        )

        titulo = content.titulo
        plataforma = content.plataforma
        tipo = content.tipo
        data_publicacao = content.data_publicacao

        if "titulo" in changes:
            titulo = self._normalize_text(
                changes["titulo"],
                200,
            )

        if "plataforma" in changes:
            plataforma = self._normalize_text(
                changes["plataforma"],
                50,
            )

        if "tipo" in changes:
            tipo = self._normalize_text(
                changes["tipo"],
                50,
            )

        if "data_publicacao" in changes:
            data_publicacao = self._validate_publication_date(
                changes["data_publicacao"]
            )

        updated = replace(
            content,
            titulo=titulo,
            plataforma=plataforma,
            tipo=tipo,
            data_publicacao=data_publicacao,
        )

        return self._repository.update(updated)

    def delete(
        self,
        user_id: int,
        content_id: int,
    ) -> None:
        content = self.get(
            user_id=user_id,
            content_id=content_id,
        )

        self._repository.delete(content)
```

- [ ] **Step 4: Confirmar GREEN e regressão unitária**

Run:

```powershell
python -m pytest tests/unit/test_content_service_crud.py -v
python -m pytest tests/unit/test_content_service_create.py -v
python -m pytest tests/unit -v
```

Expected:

```text
PASS em CRUD, ownership e validações do Service
PASS em toda a suíte unitária
```

- [ ] **Step 5: Commit**

```powershell
git add backend/app/services/content_service.py `
        backend/tests/unit/test_content_service_crud.py

git commit -m "feat: add content service CRUD"
```

---

### Task 4: Adicionar persistência SQLAlchemy e migration `0002`

**Files:**
- Modify: `backend/app/database/models.py`
- Create: `backend/app/repositories/sqlalchemy_content_repository.py`
- Create: `backend/alembic/versions/0002_create_conteudos.py`
- Create: `backend/tests/integration/test_sqlalchemy_content_repository.py`

**Interfaces:**
- Consumes: `Content`
- Produces: `ContentModel`
- Produces: `SQLAlchemyContentRepository`
- Produces: tabela `conteudos` com FK `usuario_id -> usuarios.id` e índice `ix_conteudos_usuario_id`.

- [ ] **Step 1: Escrever o teste RED do repository SQLAlchemy**

Criar `backend/tests/integration/test_sqlalchemy_content_repository.py`:

```python
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

from app.database import models  # noqa: F401
from app.database.connection import (
    Base,
    create_engine_from_url,
    create_session_factory,
)
from app.domain.content import Content
from app.domain.user import User
from app.repositories.sqlalchemy_content_repository import (
    SQLAlchemyContentRepository,
)
from app.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)


def create_user(repository, email):
    return repository.create(
        User(
            id=None,
            nome="Usuário",
            email=email,
            senha_hash="hash",
            criado_em=datetime.now(timezone.utc),
        )
    )


def make_content(user_id, titulo, published_at):
    return Content(
        id=None,
        usuario_id=user_id,
        titulo=titulo,
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=published_at,
        criado_em=datetime.now(timezone.utc),
    )


def test_sqlalchemy_content_repository_crud_and_ownership(tmp_path):
    database_path = tmp_path / "content_repository.db"

    engine = create_engine_from_url(
        f"sqlite:///{database_path}"
    )
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        user_repository = SQLAlchemyUserRepository(session)
        content_repository = SQLAlchemyContentRepository(session)

        user_a = create_user(
            user_repository,
            "a@email.com",
        )
        user_b = create_user(
            user_repository,
            "b@email.com",
        )

        assert user_a.id is not None
        assert user_b.id is not None

        old = content_repository.create(
            make_content(
                user_a.id,
                "Antigo",
                date.today() - timedelta(days=1),
            )
        )
        newest_1 = content_repository.create(
            make_content(
                user_a.id,
                "Novo 1",
                date.today(),
            )
        )
        newest_2 = content_repository.create(
            make_content(
                user_a.id,
                "Novo 2",
                date.today(),
            )
        )
        foreign = content_repository.create(
            make_content(
                user_b.id,
                "Outro usuário",
                date.today(),
            )
        )

        listed = content_repository.list_by_user(
            user_a.id
        )

        assert [content.id for content in listed] == [
            newest_2.id,
            newest_1.id,
            old.id,
        ]

        assert content_repository.get_by_id_and_user(
            foreign.id,
            user_a.id,
        ) is None

        updated_input = replace(
            newest_1,
            titulo="Título atualizado",
        )

        updated = content_repository.update(
            updated_input
        )

        assert updated.titulo == "Título atualizado"

        content_repository.delete(updated)

        assert content_repository.get_by_id_and_user(
            updated.id,
            user_a.id,
        ) is None
```

- [ ] **Step 2: Verificar RED**

Run:

```powershell
python -m pytest tests/integration/test_sqlalchemy_content_repository.py -v
```

Expected inicialmente:

```text
FAIL durante import porque SQLAlchemyContentRepository ainda não existe
```

- [ ] **Step 3: Adicionar `ContentModel`**

Substituir os imports de `backend/app/database/models.py` por:

```python
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
```

Manter `UserModel` como está.

Depois de `UserModel`, adicionar:

```python
class ContentModel(Base):
    __tablename__ = "conteudos"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )

    titulo: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    plataforma: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    tipo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    data_publicacao: Mapped[date] = mapped_column(
        Date(),
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
```

Não adicionar `relationship()` neste marco; nenhuma regra atual precisa disso.

- [ ] **Step 4: Criar `SQLAlchemyContentRepository`**

Criar `backend/app/repositories/sqlalchemy_content_repository.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import ContentModel
from app.domain.content import Content


class SQLAlchemyContentRepository:
    def __init__(
        self,
        session: Session,
    ):
        self._session = session

    @staticmethod
    def _to_domain(
        model: ContentModel,
    ) -> Content:
        return Content(
            id=model.id,
            usuario_id=model.usuario_id,
            titulo=model.titulo,
            plataforma=model.plataforma,
            tipo=model.tipo,
            data_publicacao=model.data_publicacao,
            criado_em=model.criado_em,
        )

    def create(
        self,
        content: Content,
    ) -> Content:
        model = ContentModel(
            usuario_id=content.usuario_id,
            titulo=content.titulo,
            plataforma=content.plataforma,
            tipo=content.tipo,
            data_publicacao=content.data_publicacao,
            criado_em=content.criado_em,
        )

        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)

        return self._to_domain(model)

    def list_by_user(
        self,
        user_id: int,
    ) -> list[Content]:
        statement = (
            select(ContentModel)
            .where(
                ContentModel.usuario_id == user_id
            )
            .order_by(
                ContentModel.data_publicacao.desc(),
                ContentModel.id.desc(),
            )
        )

        models = self._session.scalars(
            statement
        ).all()

        return [
            self._to_domain(model)
            for model in models
        ]

    def get_by_id_and_user(
        self,
        content_id: int,
        user_id: int,
    ) -> Content | None:
        statement = select(ContentModel).where(
            ContentModel.id == content_id,
            ContentModel.usuario_id == user_id,
        )

        model = self._session.scalar(statement)

        if model is None:
            return None

        return self._to_domain(model)

    def update(
        self,
        content: Content,
    ) -> Content:
        if content.id is None:
            raise ValueError(
                "Conteúdo sem id não pode ser atualizado."
            )

        statement = select(ContentModel).where(
            ContentModel.id == content.id,
            ContentModel.usuario_id == content.usuario_id,
        )

        model = self._session.scalar(statement)

        if model is None:
            raise ValueError(
                "Conteúdo não encontrado para atualização."
            )

        model.titulo = content.titulo
        model.plataforma = content.plataforma
        model.tipo = content.tipo
        model.data_publicacao = content.data_publicacao

        self._session.commit()
        self._session.refresh(model)

        return self._to_domain(model)

    def delete(
        self,
        content: Content,
    ) -> None:
        if content.id is None:
            raise ValueError(
                "Conteúdo sem id não pode ser excluído."
            )

        statement = select(ContentModel).where(
            ContentModel.id == content.id,
            ContentModel.usuario_id == content.usuario_id,
        )

        model = self._session.scalar(statement)

        if model is None:
            raise ValueError(
                "Conteúdo não encontrado para exclusão."
            )

        self._session.delete(model)
        self._session.commit()
```

- [ ] **Step 5: Criar a migration `0002_create_conteudos`**

Criar `backend/alembic/versions/0002_create_conteudos.py`:

```python
from alembic import op
import sqlalchemy as sa


revision = "0002_create_conteudos"
down_revision = "0001_create_usuarios"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "conteudos",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "titulo",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "plataforma",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "tipo",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "data_publicacao",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name="fk_conteudos_usuario_id_usuarios",
        ),
    )

    op.create_index(
        "ix_conteudos_usuario_id",
        "conteudos",
        ["usuario_id"],
    )


def downgrade():
    op.drop_index(
        "ix_conteudos_usuario_id",
        table_name="conteudos",
    )

    op.drop_table("conteudos")
```

- [ ] **Step 6: Confirmar GREEN no repository**

Run:

```powershell
python -m pytest tests/integration/test_sqlalchemy_content_repository.py -v
python -m pytest tests/integration/test_sqlalchemy_user_repository.py -v
```

Expected:

```text
PASS nos repositories de conteúdo e usuário
```

- [ ] **Step 7: Verificar a migration real do ambiente de desenvolvimento**

Ainda dentro de `backend`:

```powershell
python -m alembic current
python -m alembic upgrade head
python -m alembic current
```

Expected após o upgrade:

```text
0002_create_conteudos (head)
```

Não editar `0001_create_usuarios.py`.

- [ ] **Step 8: Rodar a suíte completa**

```powershell
python -m pytest -v
```

Expected:

```text
todos os testes existentes + novos PASS
```

- [ ] **Step 9: Commit**

```powershell
git add backend/app/database/models.py `
        backend/app/repositories/sqlalchemy_content_repository.py `
        backend/alembic/versions/0002_create_conteudos.py `
        backend/tests/integration/test_sqlalchemy_content_repository.py

git commit -m "feat: add content persistence"
```

---

### Task 5: Expor criação, listagem e consulta pela API

**Files:**
- Create: `backend/app/schemas/content.py`
- Create: `backend/app/controllers/content_controller.py`
- Modify: `backend/app/dependencies.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/integration/test_content_api.py`

**Interfaces:**
- Consumes: `get_current_user() -> User`
- Consumes: `ContentService`
- Produces:
  - `ContentCreate`
  - `ContentResponse`
  - `get_content_repository`
  - `get_content_service`
  - `POST /conteudos`
  - `GET /conteudos`
  - `GET /conteudos/{id}`

- [ ] **Step 1: Escrever os testes RED da API de criação/leitura**

Criar `backend/tests/integration/test_content_api.py`:

```python
from datetime import date, timedelta


def register_and_login(
    client,
    nome="Carlos",
    email="carlos@email.com",
    senha="minhasenha",
):
    register_response = client.post(
        "/auth/register",
        json={
            "nome": nome,
            "email": email,
            "senha": senha,
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "senha": senha,
        },
    )
    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def create_payload(
    titulo="Conteúdo",
    published_at=None,
):
    return {
        "titulo": titulo,
        "plataforma": "Instagram",
        "tipo": "Reels",
        "data_publicacao": str(
            published_at or date.today()
        ),
    }


def test_contents_requires_authentication(client):
    response = client.get("/conteudos")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Não autenticado."
    }


def test_contents_rejects_invalid_token(client):
    response = client.get(
        "/conteudos",
        headers={
            "Authorization": "Bearer token-invalido"
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Não autenticado."
    }


def test_create_content_returns_201_without_user_id(client):
    token = register_and_login(client)

    response = client.post(
        "/conteudos",
        headers=auth_headers(token),
        json={
            "titulo": "  Meu conteúdo  ",
            "plataforma": "  Instagram  ",
            "tipo": "  Reels  ",
            "data_publicacao": str(date.today()),
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] is not None
    assert body["titulo"] == "Meu conteúdo"
    assert body["plataforma"] == "Instagram"
    assert body["tipo"] == "Reels"
    assert body["data_publicacao"] == str(date.today())
    assert "criado_em" in body
    assert "usuario_id" not in body


def test_create_content_rejects_user_id_in_payload(client):
    token = register_and_login(client)

    payload = create_payload()
    payload["usuario_id"] = 999

    response = client.post(
        "/conteudos",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 422


def test_create_content_rejects_future_date(client):
    token = register_and_login(client)

    response = client.post(
        "/conteudos",
        headers=auth_headers(token),
        json=create_payload(
            published_at=(
                date.today() + timedelta(days=1)
            )
        ),
    )

    assert response.status_code == 422


def test_list_returns_empty_array_for_new_user(client):
    token = register_and_login(client)

    response = client.get(
        "/conteudos",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_contents_ordered_by_date_and_id(client):
    token = register_and_login(client)
    headers = auth_headers(token)

    old = client.post(
        "/conteudos",
        headers=headers,
        json=create_payload(
            "Antigo",
            date.today() - timedelta(days=1),
        ),
    ).json()

    same_date_first = client.post(
        "/conteudos",
        headers=headers,
        json=create_payload(
            "Mesmo dia 1",
            date.today(),
        ),
    ).json()

    same_date_second = client.post(
        "/conteudos",
        headers=headers,
        json=create_payload(
            "Mesmo dia 2",
            date.today(),
        ),
    ).json()

    response = client.get(
        "/conteudos",
        headers=headers,
    )

    assert response.status_code == 200
    assert [
        content["id"]
        for content in response.json()
    ] == [
        same_date_second["id"],
        same_date_first["id"],
        old["id"],
    ]


def test_get_own_content_returns_200(client):
    token = register_and_login(client)
    headers = auth_headers(token)

    created = client.post(
        "/conteudos",
        headers=headers,
        json=create_payload(),
    ).json()

    response = client.get(
        f"/conteudos/{created['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_missing_content_returns_404(client):
    token = register_and_login(client)

    response = client.get(
        "/conteudos/999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conteúdo não encontrado."
    }
```

- [ ] **Step 2: Verificar RED**

Run:

```powershell
python -m pytest tests/integration/test_content_api.py -v
```

Expected:

```text
FAIL com 404 nas rotas /conteudos porque o router ainda não existe
```

- [ ] **Step 3: Criar os schemas de criação e resposta**

Criar `backend/app/schemas/content.py` inicialmente com:

```python
from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class ContentCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    titulo: str = Field(
        min_length=1,
        max_length=200,
    )
    plataforma: str = Field(
        min_length=1,
        max_length=50,
    )
    tipo: str = Field(
        min_length=1,
        max_length=50,
    )
    data_publicacao: date

    @field_validator(
        "titulo",
        "plataforma",
        "tipo",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value


class ContentResponse(BaseModel):
    id: int
    titulo: str
    plataforma: str
    tipo: str
    data_publicacao: date
    criado_em: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
```

Não adicionar `usuario_id` a `ContentResponse`.

- [ ] **Step 4: Adicionar dependências do domínio de Conteúdo**

Em `backend/app/dependencies.py`, adicionar imports:

```python
from app.repositories.sqlalchemy_content_repository import (
    SQLAlchemyContentRepository,
)
from app.services.content_service import ContentService
```

Depois de `get_user_repository`, adicionar:

```python
def get_content_repository(
    session: Session = Depends(get_db_session),
):
    return SQLAlchemyContentRepository(session)
```

Depois de `get_auth_service`, adicionar:

```python
def get_content_service(
    repository=Depends(get_content_repository),
):
    return ContentService(repository)
```

Manter `get_current_user` funcionando como na Task 1.

- [ ] **Step 5: Criar o Controller com POST/GET/GET por id**

Criar `backend/app/controllers/content_controller.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import (
    get_content_service,
    get_current_user,
)
from app.domain.user import User
from app.schemas.content import (
    ContentCreate,
    ContentResponse,
)
from app.services.content_service import (
    ContentNotFoundError,
    ContentService,
    InvalidContentError,
)


router = APIRouter(
    prefix="/conteudos",
    tags=["conteudos"],
)


def _require_user_id(
    current_user: User,
) -> int:
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return current_user.id


@router.post(
    "",
    response_model=ContentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_content(
    payload: ContentCreate,
    current_user: User = Depends(get_current_user),
    service: ContentService = Depends(get_content_service),
):
    try:
        return service.create(
            user_id=_require_user_id(current_user),
            titulo=payload.titulo,
            plataforma=payload.plataforma,
            tipo=payload.tipo,
            data_publicacao=payload.data_publicacao,
        )

    except InvalidContentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dados do conteúdo inválidos.",
        ) from exc


@router.get(
    "",
    response_model=list[ContentResponse],
)
def list_contents(
    current_user: User = Depends(get_current_user),
    service: ContentService = Depends(get_content_service),
):
    return service.list(
        user_id=_require_user_id(current_user)
    )


@router.get(
    "/{content_id}",
    response_model=ContentResponse,
)
def get_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    service: ContentService = Depends(get_content_service),
):
    try:
        return service.get(
            user_id=_require_user_id(current_user),
            content_id=content_id,
        )

    except ContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conteúdo não encontrado.",
        ) from exc
```

- [ ] **Step 6: Registrar o router e atualizar a versão da API**

Substituir `backend/app/main.py` por:

```python
from fastapi import FastAPI

from app.controllers.auth_controller import router as auth_router
from app.controllers.content_controller import router as content_router


app = FastAPI(
    title="MetricaMEI API",
    version="0.3.0",
)

app.include_router(auth_router)
app.include_router(content_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 7: Confirmar GREEN dos endpoints de leitura/criação**

Run:

```powershell
python -m pytest tests/integration/test_content_api.py -v
python -m pytest tests/integration/test_auth_me.py -v
python -m pytest -v
```

Expected:

```text
PASS em autenticação, criação, listagem, ordenação e consulta individual
PASS na suíte completa
```

- [ ] **Step 8: Commit**

```powershell
git add backend/app/schemas/content.py `
        backend/app/controllers/content_controller.py `
        backend/app/dependencies.py `
        backend/app/main.py `
        backend/tests/integration/test_content_api.py

git commit -m "feat: add content create and read endpoints"
```

---

### Task 6: Adicionar PATCH, DELETE e testes HTTP de ownership

**Files:**
- Modify: `backend/app/schemas/content.py`
- Modify: `backend/app/controllers/content_controller.py`
- Create: `backend/tests/integration/test_content_ownership.py`
- Modify: `backend/tests/integration/test_content_api.py`

**Interfaces:**
- Produces: `ContentUpdate`
- Produces: `PATCH /conteudos/{id}`
- Produces: `DELETE /conteudos/{id}`

- [ ] **Step 1: Escrever testes RED de PATCH e DELETE próprios**

Adicionar ao final de `backend/tests/integration/test_content_api.py`:

```python
def test_patch_updates_only_sent_fields(client):
    token = register_and_login(client)
    headers = auth_headers(token)

    created = client.post(
        "/conteudos",
        headers=headers,
        json=create_payload("Título antigo"),
    ).json()

    response = client.patch(
        f"/conteudos/{created['id']}",
        headers=headers,
        json={
            "titulo": "  Título novo  "
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["titulo"] == "Título novo"
    assert body["plataforma"] == created["plataforma"]
    assert body["tipo"] == created["tipo"]
    assert (
        body["data_publicacao"]
        == created["data_publicacao"]
    )


def test_patch_empty_payload_returns_422(client):
    token = register_and_login(client)
    headers = auth_headers(token)

    created = client.post(
        "/conteudos",
        headers=headers,
        json=create_payload(),
    ).json()

    response = client.patch(
        f"/conteudos/{created['id']}",
        headers=headers,
        json={},
    )

    assert response.status_code == 422


def test_patch_rejects_explicit_null(client):
    token = register_and_login(client)
    headers = auth_headers(token)

    created = client.post(
        "/conteudos",
        headers=headers,
        json=create_payload(),
    ).json()

    response = client.patch(
        f"/conteudos/{created['id']}",
        headers=headers,
        json={
            "titulo": None,
        },
    )

    assert response.status_code == 422


def test_patch_rejects_user_id_field(client):
    token = register_and_login(client)
    headers = auth_headers(token)

    created = client.post(
        "/conteudos",
        headers=headers,
        json=create_payload(),
    ).json()

    response = client.patch(
        f"/conteudos/{created['id']}",
        headers=headers,
        json={
            "usuario_id": 999,
        },
    )

    assert response.status_code == 422


def test_patch_rejects_future_date(client):
    token = register_and_login(client)
    headers = auth_headers(token)

    created = client.post(
        "/conteudos",
        headers=headers,
        json=create_payload(),
    ).json()

    response = client.patch(
        f"/conteudos/{created['id']}",
        headers=headers,
        json={
            "data_publicacao": str(
                date.today() + timedelta(days=1)
            )
        },
    )

    assert response.status_code == 422


def test_patch_missing_content_returns_404(client):
    token = register_and_login(client)

    response = client.patch(
        "/conteudos/999",
        headers=auth_headers(token),
        json={
            "titulo": "Novo título",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conteúdo não encontrado."
    }


def test_delete_missing_content_returns_404(client):
    token = register_and_login(client)

    response = client.delete(
        "/conteudos/999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conteúdo não encontrado."
    }


def test_delete_returns_204_and_removes_content(client):
    token = register_and_login(client)
    headers = auth_headers(token)

    created = client.post(
        "/conteudos",
        headers=headers,
        json=create_payload(),
    ).json()

    response = client.delete(
        f"/conteudos/{created['id']}",
        headers=headers,
    )

    assert response.status_code == 204
    assert response.content == b""

    get_response = client.get(
        f"/conteudos/{created['id']}",
        headers=headers,
    )

    assert get_response.status_code == 404
```

- [ ] **Step 2: Escrever o teste RED de isolamento entre dois usuários**

Criar `backend/tests/integration/test_content_ownership.py`:

```python
from datetime import date


def register_and_login(
    client,
    nome,
    email,
):
    password = "minhasenha"

    register_response = client.post(
        "/auth/register",
        json={
            "nome": nome,
            "email": email,
            "senha": password,
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "senha": password,
        },
    )
    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def create_content(
    client,
    token,
    titulo,
):
    response = client.post(
        "/conteudos",
        headers=headers(token),
        json={
            "titulo": titulo,
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": str(date.today()),
        },
    )

    assert response.status_code == 201
    return response.json()


def test_user_cannot_read_update_or_delete_other_users_content(
    client,
):
    token_a = register_and_login(
        client,
        "Usuário A",
        "a@email.com",
    )
    token_b = register_and_login(
        client,
        "Usuário B",
        "b@email.com",
    )

    create_content(
        client,
        token_a,
        "Conteúdo A",
    )
    content_b = create_content(
        client,
        token_b,
        "Conteúdo B",
    )

    foreign_id = content_b["id"]

    get_response = client.get(
        f"/conteudos/{foreign_id}",
        headers=headers(token_a),
    )
    assert get_response.status_code == 404
    assert get_response.json() == {
        "detail": "Conteúdo não encontrado."
    }

    patch_response = client.patch(
        f"/conteudos/{foreign_id}",
        headers=headers(token_a),
        json={
            "titulo": "Tentativa de alteração"
        },
    )
    assert patch_response.status_code == 404
    assert patch_response.json() == {
        "detail": "Conteúdo não encontrado."
    }

    delete_response = client.delete(
        f"/conteudos/{foreign_id}",
        headers=headers(token_a),
    )
    assert delete_response.status_code == 404
    assert delete_response.json() == {
        "detail": "Conteúdo não encontrado."
    }

    owner_response = client.get(
        f"/conteudos/{foreign_id}",
        headers=headers(token_b),
    )

    assert owner_response.status_code == 200
    assert (
        owner_response.json()["titulo"]
        == "Conteúdo B"
    )


def test_list_never_returns_other_users_contents(client):
    token_a = register_and_login(
        client,
        "Usuário A",
        "a@email.com",
    )
    token_b = register_and_login(
        client,
        "Usuário B",
        "b@email.com",
    )

    content_a = create_content(
        client,
        token_a,
        "Conteúdo A",
    )
    create_content(
        client,
        token_b,
        "Conteúdo B",
    )

    response = client.get(
        "/conteudos",
        headers=headers(token_a),
    )

    assert response.status_code == 200
    assert [
        content["id"]
        for content in response.json()
    ] == [
        content_a["id"]
    ]
```

- [ ] **Step 3: Verificar RED**

Run:

```powershell
python -m pytest tests/integration/test_content_api.py -v
python -m pytest tests/integration/test_content_ownership.py -v
```

Expected antes da implementação:

```text
PATCH /conteudos/{id}: 405 Method Not Allowed
DELETE /conteudos/{id}: 405 Method Not Allowed
testes de ownership de PATCH/DELETE ainda falham
```

- [ ] **Step 4: Adicionar `ContentUpdate` ao schema**

Em `backend/app/schemas/content.py`, adicionar `model_validator` ao import:

```python
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
```

Entre `ContentCreate` e `ContentResponse`, adicionar:

```python
class ContentUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    titulo: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    plataforma: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    tipo: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    data_publicacao: date | None = None

    @field_validator(
        "titulo",
        "plataforma",
        "tipo",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError(
                "Ao menos um campo deve ser enviado."
            )

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(
                    "Campos enviados não podem ser nulos."
                )

        return self
```

- [ ] **Step 5: Adicionar PATCH e DELETE ao Controller**

Em `backend/app/controllers/content_controller.py`, alterar import do FastAPI para:

```python
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
```

Adicionar `ContentUpdate` ao import dos schemas:

```python
from app.schemas.content import (
    ContentCreate,
    ContentResponse,
    ContentUpdate,
)
```

Depois de `get_content`, adicionar:

```python
@router.patch(
    "/{content_id}",
    response_model=ContentResponse,
)
def update_content(
    content_id: int,
    payload: ContentUpdate,
    current_user: User = Depends(get_current_user),
    service: ContentService = Depends(get_content_service),
):
    try:
        return service.update(
            user_id=_require_user_id(current_user),
            content_id=content_id,
            changes=payload.model_dump(
                exclude_unset=True
            ),
        )

    except ContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conteúdo não encontrado.",
        ) from exc

    except InvalidContentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dados do conteúdo inválidos.",
        ) from exc


@router.delete(
    "/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    service: ContentService = Depends(get_content_service),
):
    try:
        service.delete(
            user_id=_require_user_id(current_user),
            content_id=content_id,
        )

    except ContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conteúdo não encontrado.",
        ) from exc

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
```

- [ ] **Step 6: Confirmar GREEN do CRUD HTTP e ownership**

Run:

```powershell
python -m pytest tests/integration/test_content_api.py -v
python -m pytest tests/integration/test_content_ownership.py -v
python -m pytest tests/integration/test_auth_me.py -v
python -m pytest -v
```

Expected:

```text
PATCH próprio: 200
PATCH vazio/nulo/futuro: 422
DELETE próprio: 204 sem corpo
GET/PATCH/DELETE de conteúdo alheio: 404
conteúdo do outro usuário permanece intacto
listagem não mistura usuários
toda a suíte PASS
```

- [ ] **Step 7: Commit**

```powershell
git add backend/app/schemas/content.py `
        backend/app/controllers/content_controller.py `
        backend/tests/integration/test_content_api.py `
        backend/tests/integration/test_content_ownership.py

git commit -m "feat: add content update delete and ownership"
```

---

### Task 7: Documentação e verificação final do Marco 0.3

**Files:**
- Modify: `README.md`
- Verify: entire repository

**Interfaces:**
- Produces: documentação do Marco 0.3 e evidência final de que a branch está pronta para revisão/PR.

- [ ] **Step 1: Atualizar a seção de banco de dados no README**

No `README.md`, substituir:

````markdown
A migration inicial cria a tabela:

```text
usuarios
```
````

por:

````markdown
As migrations atuais criam as tabelas:

```text
usuarios
conteudos
```

A tabela `conteudos` referencia `usuarios.id` por `usuario_id`.
````

- [ ] **Step 2: Documentar os endpoints de Conteúdo**

Após a seção `### GET /auth/me`, adicionar:

````markdown
### POST /conteudos

Cria um conteúdo para o usuário autenticado.

Requer:

```text
Authorization: Bearer <token>
```

Exemplo:

```json
{
  "titulo": "Resultados do mês",
  "plataforma": "Instagram",
  "tipo": "Carrossel",
  "data_publicacao": "2026-08-20"
}
```

### GET /conteudos

Lista somente os conteúdos do usuário autenticado, ordenados por data de publicação mais recente e, em caso de empate, pelo maior `id`.

### GET /conteudos/{id}

Retorna um conteúdo do usuário autenticado.

Conteúdo inexistente ou pertencente a outro usuário retorna `404`.

### PATCH /conteudos/{id}

Atualiza parcialmente `titulo`, `plataforma`, `tipo` e/ou `data_publicacao`.

Payload vazio é inválido.

### DELETE /conteudos/{id}

Exclui definitivamente um conteúdo do usuário autenticado.

Em caso de sucesso retorna `204 No Content`.
````

- [ ] **Step 3: Atualizar o estado atual**

Substituir a seção `## Estado atual` por:

````markdown
## Estado atual

O Marco 0.3 implementa:

```text
cadastro/login
      ↓
     JWT
      ↓
usuário autenticado
      ↓
CRUD de conteúdos
      ↓
ownership por usuário
```

O backend possui autenticação e gerenciamento de conteúdos com arquitetura Controller–Service–Repository, testes unitários com Repository em memória e testes de integração com SQLite isolado.

Métricas, cálculo de engajamento, dashboard e frontend fazem parte dos próximos marcos.
````

- [ ] **Step 4: Rodar verificação funcional completa**

Dentro de `backend` e com `.venv` ativa:

```powershell
python --version
python -m pytest -v
python -m pip check
python -m alembic current
```

Expected:

```text
Python 3.14.x
todos os testes PASS
No broken requirements found.
0002_create_conteudos (head)
```

- [ ] **Step 5: Verificar qualidade do diff e estado Git**

Voltar para a raiz:

```powershell
cd ..
git diff --check
git status --short
git branch --show-current
```

Expected:

```text
git diff --check: sem saída
branch: feature/conteudos
status: apenas README.md modificado antes do commit desta tarefa
```

- [ ] **Step 6: Commit da documentação**

```powershell
git add README.md
git commit -m "docs: document content management milestone"
```

- [ ] **Step 7: Rodar a verificação pós-commit**

```powershell
cd backend
python -m pytest -v
python -m pip check
python -m alembic current
cd ..
git diff --check
git status --short
git log --oneline --decorate -8
```

Expected:

```text
todos os testes PASS
No broken requirements found.
0002_create_conteudos (head)
git diff --check sem saída
git status --short sem saída
histórico mostra os commits do Marco 0.3 na feature/conteudos
```

- [ ] **Step 8: Critérios de aceite antes do PR**

Confirmar manualmente todos os itens:

```text
[ ] POST /conteudos → 201
[ ] GET /conteudos → 200 e somente dados do dono
[ ] GET /conteudos/{id} → 200/404
[ ] PATCH /conteudos/{id} → 200/404/422
[ ] DELETE /conteudos/{id} → 204/404
[ ] usuario_id nunca entra no payload
[ ] usuario_id nunca aparece no response
[ ] data futura é rejeitada
[ ] PATCH vazio é rejeitado
[ ] outro usuário recebe 404 em GET/PATCH/DELETE
[ ] conteúdo alheio permanece intacto após tentativas
[ ] ContentService é independente de HTTP/SQLAlchemy
[ ] InMemoryContentRepository cobre testes unitários
[ ] SQLAlchemyContentRepository cobre aplicação real
[ ] migration 0002 está em head
[ ] suíte antiga de autenticação continua verde
[ ] pip check limpo
[ ] working tree limpa
```

Somente depois desses itens a branch está pronta para revisão e Pull Request.

---

## Ordem esperada de commits

Ao final da execução, a branch deve conter aproximadamente esta sequência após o commit da spec e do plano:

```text
refactor: centralize authenticated user dependency
feat: add content creation domain
feat: add content service CRUD
feat: add content persistence
feat: add content create and read endpoints
feat: add content update delete and ownership
docs: document content management milestone
```

Não fazer squash durante o desenvolvimento. Manter os commits pequenos facilita revisão, diagnóstico de regressões e demonstra o processo incremental/TDD do TCC.

## Verificação final contra a spec

Este plano cobre:

```text
Seção 3  → Controller–Service–Repository
Seção 4  → Content e regras de domínio
Seção 5  → ContentModel, índice, FK e migration 0002
Seção 6  → ContentCreate, ContentUpdate e ContentResponse
Seção 7  → cinco endpoints HTTP e status
Seção 8  → get_current_user compartilhado + ownership
Seção 9  → InvalidContentError e ContentNotFoundError
Seção 10 → testes unitários, integração e TDD
Seção 11 → critérios de conclusão
Seção 12 → RF02, RF06, RNF01, RNF02, RNF03, RNF05 e RNF06
```

Não há implementação de métricas, engajamento, dashboard, paginação, filtros, soft delete, agendamento, `atualizado_em` ou enums neste plano.
