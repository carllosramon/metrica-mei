# Marco 0.4 — Content Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o RF03 do MetricaMEI, permitindo que usuários autenticados criem, consultem, atualizem e excluam snapshots históricos de métricas dos próprios conteúdos, com ownership, unicidade por data, persistência relacional, cascade e testes automatizados.

**Architecture:** O módulo segue Controller–Service–Repository. `MetricService` depende diretamente de `ContentRepository` para validar ownership e data de publicação, e de `MetricRepository` para CRUD/persistência. A entidade `Metric` não armazena `usuario_id`; ownership é sempre inferido pelo conteúdo.

**Tech Stack:** Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, SQLite para desenvolvimento/testes, Pytest, JWT já existente.

**Spec:** `docs/superpowers/specs/2026-08-24-content-metrics-design.md`

## Global Constraints

- O Marco 0.4 implementa somente RF03 e histórico bruto de métricas; engajamento fica fora.
- `Metric` possui `id`, `conteudo_id`, `visualizacoes`, `curtidas`, `comentarios`, `compartilhamentos`, `alcance`, `data_referencia`, `criado_em`.
- `Metric` não possui `usuario_id`.
- Os cinco valores quantitativos são inteiros obrigatórios na criação e devem ser `>= 0`; zero é válido.
- `conteudo.data_publicacao <= data_referencia <= date.today()`.
- Existe no máximo um snapshot por `(conteudo_id, data_referencia)`.
- Todas as rotas de métricas exigem JWT.
- Conteúdo inexistente ou alheio retorna `404` com `{"detail":"Conteúdo não encontrado."}`.
- Métrica inexistente ou fora do conteúdo informado retorna `404` com `{"detail":"Métrica não encontrada."}`.
- Duplicidade retorna `409` com `{"detail":"Já existe uma métrica para este conteúdo nesta data."}`.
- Regras de negócio inválidas retornam `422` com `{"detail":"Dados da métrica inválidos."}`.
- `PATCH` vazio e `null` explícito são inválidos; zero continua válido.
- Listagem ordenada por `data_referencia DESC, id DESC`.
- `DELETE` de métrica retorna 204.
- `DELETE` de conteúdo remove métricas com `ON DELETE CASCADE`.
- SQLite deve habilitar `PRAGMA foreign_keys = ON`.
- Sem paginação, dashboard, gráficos, filtros por período, APIs externas, frontend ou cálculo de engajamento.
- Desenvolvimento em TDD; os 76 testes anteriores devem permanecer verdes.
- Execute comandos Python/Pytest a partir de `backend/`.

---

## Planned File Map

**Criar**
- `backend/app/domain/metric.py`
- `backend/app/repositories/metric_repository.py`
- `backend/app/repositories/in_memory_metric_repository.py`
- `backend/app/repositories/sqlalchemy_metric_repository.py`
- `backend/app/services/metric_service.py`
- `backend/app/schemas/metric.py`
- `backend/app/controllers/metric_controller.py`
- `backend/alembic/versions/0003_create_metricas.py`
- `backend/tests/unit/test_in_memory_metric_repository.py`
- `backend/tests/unit/test_metric_service_create.py`
- `backend/tests/unit/test_metric_service_crud.py`
- `backend/tests/integration/test_metric_model.py`
- `backend/tests/integration/test_metric_migration.py`
- `backend/tests/integration/test_sqlite_foreign_keys.py`
- `backend/tests/integration/test_sqlalchemy_metric_repository.py`
- `backend/tests/integration/test_metric_api.py`

**Modificar**
- `backend/app/database/connection.py`
- `backend/app/database/models.py`
- `backend/app/dependencies.py`
- `backend/app/main.py`
- `README.md`

---

### Task 1: Entidade Metric e repository em memória

**Files:**
- Create: `backend/app/domain/metric.py`
- Create: `backend/app/repositories/metric_repository.py`
- Create: `backend/app/repositories/in_memory_metric_repository.py`
- Test: `backend/tests/unit/test_in_memory_metric_repository.py`

**Interfaces:**
- Produces `Metric`
- Produces `MetricPersistenceConflictError`
- Produces `MetricRepository`
- Produces `InMemoryMetricRepository`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_in_memory_metric_repository.py`:

```python
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.metric import Metric
from app.repositories.in_memory_metric_repository import (
    InMemoryMetricRepository,
)
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
)


def make_metric(
    *,
    content_id: int = 1,
    reference_date: date | None = None,
) -> Metric:
    return Metric(
        id=None,
        conteudo_id=content_id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=reference_date or date.today(),
        criado_em=datetime.now(timezone.utc),
    )


def test_create_assigns_id_and_get_reads_same_metric():
    repository = InMemoryMetricRepository()

    created = repository.create(make_metric())

    loaded = repository.get_by_id_and_content(
        created.id,
        created.conteudo_id,
    )

    assert created.id == 1
    assert loaded == created


def test_list_by_content_filters_and_orders_descending():
    repository = InMemoryMetricRepository()

    older = repository.create(
        make_metric(
            content_id=1,
            reference_date=date.today() - timedelta(days=2),
        )
    )
    newer = repository.create(
        make_metric(
            content_id=1,
            reference_date=date.today() - timedelta(days=1),
        )
    )
    repository.create(
        make_metric(
            content_id=2,
            reference_date=date.today(),
        )
    )

    result = repository.list_by_content(1)

    assert [metric.id for metric in result] == [
        newer.id,
        older.id,
    ]


def test_get_by_content_and_reference_date_finds_snapshot():
    repository = InMemoryMetricRepository()
    created = repository.create(make_metric())

    loaded = repository.get_by_content_and_reference_date(
        created.conteudo_id,
        created.data_referencia,
    )

    assert loaded == created


def test_duplicate_content_and_date_raises_persistence_conflict():
    repository = InMemoryMetricRepository()
    repository.create(make_metric())

    with pytest.raises(MetricPersistenceConflictError):
        repository.create(make_metric())


def test_update_replaces_existing_metric():
    repository = InMemoryMetricRepository()
    created = repository.create(make_metric())

    updated = repository.update(
        replace(created, alcance=999)
    )

    loaded = repository.get_by_id_and_content(
        created.id,
        created.conteudo_id,
    )

    assert updated.alcance == 999
    assert loaded is not None
    assert loaded.alcance == 999


def test_update_rejects_date_collision():
    repository = InMemoryMetricRepository()
    first = repository.create(
        make_metric(
            reference_date=date.today() - timedelta(days=1)
        )
    )
    second = repository.create(
        make_metric(
            reference_date=date.today()
        )
    )

    with pytest.raises(MetricPersistenceConflictError):
        repository.update(
            replace(
                second,
                data_referencia=first.data_referencia,
            )
        )


def test_delete_removes_metric():
    repository = InMemoryMetricRepository()
    created = repository.create(make_metric())

    repository.delete(created)

    assert repository.get_by_id_and_content(
        created.id,
        created.conteudo_id,
    ) is None
```

- [ ] **Step 2: Run the test to verify RED**

```powershell
python -m pytest tests/unit/test_in_memory_metric_repository.py -v
```

Expected: import failure because the metric domain/repository files do not exist.

- [ ] **Step 3: Implement the domain object**

Create `app/domain/metric.py`:

```python
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(slots=True)
class Metric:
    id: int | None
    conteudo_id: int
    visualizacoes: int
    curtidas: int
    comentarios: int
    compartilhamentos: int
    alcance: int
    data_referencia: date
    criado_em: datetime
```

- [ ] **Step 4: Implement the repository protocol**

Create `app/repositories/metric_repository.py`:

```python
from datetime import date
from typing import Protocol

from app.domain.metric import Metric


class MetricPersistenceConflictError(Exception):
    pass


class MetricRepository(Protocol):
    def create(self, metric: Metric) -> Metric: ...

    def list_by_content(
        self,
        content_id: int,
    ) -> list[Metric]: ...

    def get_by_id_and_content(
        self,
        metric_id: int,
        content_id: int,
    ) -> Metric | None: ...

    def get_by_content_and_reference_date(
        self,
        content_id: int,
        data_referencia: date,
    ) -> Metric | None: ...

    def update(self, metric: Metric) -> Metric: ...

    def delete(self, metric: Metric) -> None: ...
```

- [ ] **Step 5: Implement the in-memory repository**

Create `app/repositories/in_memory_metric_repository.py`:

```python
from dataclasses import replace
from datetime import date

from app.domain.metric import Metric
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
)


class InMemoryMetricRepository:
    def __init__(self):
        self._metrics: dict[int, Metric] = {}
        self._next_id = 1

    def create(self, metric: Metric) -> Metric:
        if self.get_by_content_and_reference_date(
            metric.conteudo_id,
            metric.data_referencia,
        ) is not None:
            raise MetricPersistenceConflictError

        stored = replace(
            metric,
            id=self._next_id,
        )

        self._metrics[self._next_id] = stored
        self._next_id += 1

        return stored

    def list_by_content(
        self,
        content_id: int,
    ) -> list[Metric]:
        metrics = [
            metric
            for metric in self._metrics.values()
            if metric.conteudo_id == content_id
        ]

        return sorted(
            metrics,
            key=lambda metric: (
                metric.data_referencia,
                metric.id or 0,
            ),
            reverse=True,
        )

    def get_by_id_and_content(
        self,
        metric_id: int,
        content_id: int,
    ) -> Metric | None:
        metric = self._metrics.get(metric_id)

        if metric is None:
            return None

        if metric.conteudo_id != content_id:
            return None

        return metric

    def get_by_content_and_reference_date(
        self,
        content_id: int,
        data_referencia: date,
    ) -> Metric | None:
        for metric in self._metrics.values():
            if (
                metric.conteudo_id == content_id
                and metric.data_referencia == data_referencia
            ):
                return metric

        return None

    def update(self, metric: Metric) -> Metric:
        existing = self.get_by_content_and_reference_date(
            metric.conteudo_id,
            metric.data_referencia,
        )

        if (
            existing is not None
            and existing.id != metric.id
        ):
            raise MetricPersistenceConflictError

        if metric.id is not None:
            self._metrics[metric.id] = metric

        return metric

    def delete(self, metric: Metric) -> None:
        if metric.id is not None:
            self._metrics.pop(metric.id, None)
```

- [ ] **Step 6: Run tests and verify GREEN**

```powershell
python -m pytest tests/unit/test_in_memory_metric_repository.py -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add app/domain/metric.py app/repositories/metric_repository.py app/repositories/in_memory_metric_repository.py tests/unit/test_in_memory_metric_repository.py
git commit -m "feat: add metric domain and repository contract"
```

---

### Task 2: MetricService — criação e regras de validação

**Files:**
- Create: `backend/app/services/metric_service.py`
- Test: `backend/tests/unit/test_metric_service_create.py`

**Interfaces:**
- Consumes `ContentRepository.get_by_id_and_user`
- Consumes `MetricRepository`
- Produces `InvalidMetricError`
- Produces `MetricNotFoundError`
- Produces `DuplicateMetricError`
- Produces `MetricContentNotFoundError`
- Produces `MetricService.create(...)`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_metric_service_create.py`:

```python
from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.content import Content
from app.repositories.in_memory_content_repository import (
    InMemoryContentRepository,
)
from app.repositories.in_memory_metric_repository import (
    InMemoryMetricRepository,
)
from app.services.metric_service import (
    DuplicateMetricError,
    InvalidMetricError,
    MetricContentNotFoundError,
    MetricService,
)


def build_service(
    publication_date: date | None = None,
):
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=publication_date or date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    return (
        MetricService(
            content_repository,
            metric_repository,
        ),
        content,
    )


def valid_payload(
    reference_date: date | None = None,
):
    return {
        "visualizacoes": 100,
        "curtidas": 10,
        "comentarios": 2,
        "compartilhamentos": 3,
        "alcance": 80,
        "data_referencia": (
            reference_date or date.today()
        ),
    }


def test_create_metric_for_owned_content():
    service, content = build_service()

    metric = service.create(
        user_id=1,
        content_id=content.id,
        **valid_payload(),
    )

    assert metric.id == 1
    assert metric.conteudo_id == content.id
    assert metric.alcance == 80


@pytest.mark.parametrize(
    "field",
    [
        "visualizacoes",
        "curtidas",
        "comentarios",
        "compartilhamentos",
        "alcance",
    ],
)
def test_create_accepts_zero(field):
    service, content = build_service()
    payload = valid_payload()
    payload[field] = 0

    metric = service.create(
        user_id=1,
        content_id=content.id,
        **payload,
    )

    assert getattr(metric, field) == 0


@pytest.mark.parametrize(
    "field",
    [
        "visualizacoes",
        "curtidas",
        "comentarios",
        "compartilhamentos",
        "alcance",
    ],
)
def test_create_rejects_negative_values(field):
    service, content = build_service()
    payload = valid_payload()
    payload[field] = -1

    with pytest.raises(InvalidMetricError):
        service.create(
            user_id=1,
            content_id=content.id,
            **payload,
        )


@pytest.mark.parametrize(
    "bad_value",
    [True, 1.5, "1", None],
)
def test_create_rejects_non_integer_values(
    bad_value,
):
    service, content = build_service()
    payload = valid_payload()
    payload["alcance"] = bad_value

    with pytest.raises(InvalidMetricError):
        service.create(
            user_id=1,
            content_id=content.id,
            **payload,
        )


def test_create_rejects_date_before_publication():
    publication = date.today() - timedelta(days=1)
    service, content = build_service(publication)

    with pytest.raises(InvalidMetricError):
        service.create(
            user_id=1,
            content_id=content.id,
            **valid_payload(
                publication - timedelta(days=1)
            ),
        )


def test_create_accepts_date_equal_to_publication():
    publication = date.today() - timedelta(days=1)
    service, content = build_service(publication)

    metric = service.create(
        user_id=1,
        content_id=content.id,
        **valid_payload(publication),
    )

    assert metric.data_referencia == publication


def test_create_accepts_today():
    service, content = build_service()

    metric = service.create(
        user_id=1,
        content_id=content.id,
        **valid_payload(date.today()),
    )

    assert metric.data_referencia == date.today()


def test_create_rejects_future_date():
    service, content = build_service()

    with pytest.raises(InvalidMetricError):
        service.create(
            user_id=1,
            content_id=content.id,
            **valid_payload(
                date.today() + timedelta(days=1)
            ),
        )


def test_create_rejects_datetime_reference():
    service, content = build_service()
    payload = valid_payload()
    payload["data_referencia"] = datetime.now(
        timezone.utc
    )

    with pytest.raises(InvalidMetricError):
        service.create(
            user_id=1,
            content_id=content.id,
            **payload,
        )


def test_create_hides_foreign_content():
    service, content = build_service()

    with pytest.raises(
        MetricContentNotFoundError
    ):
        service.create(
            user_id=999,
            content_id=content.id,
            **valid_payload(),
        )


def test_create_hides_missing_content():
    service, _ = build_service()

    with pytest.raises(
        MetricContentNotFoundError
    ):
        service.create(
            user_id=1,
            content_id=999,
            **valid_payload(),
        )


def test_create_rejects_duplicate_date():
    service, content = build_service()

    service.create(
        user_id=1,
        content_id=content.id,
        **valid_payload(),
    )

    with pytest.raises(DuplicateMetricError):
        service.create(
            user_id=1,
            content_id=content.id,
            **valid_payload(),
        )
```

- [ ] **Step 2: Run and verify RED**

```powershell
python -m pytest tests/unit/test_metric_service_create.py -v
```

Expected: import failure because `MetricService` does not exist.

- [ ] **Step 3: Implement MetricService create path**

Create `app/services/metric_service.py`:

```python
from dataclasses import replace
from datetime import date, datetime, timezone

from app.domain.content import Content
from app.domain.metric import Metric
from app.repositories.content_repository import (
    ContentRepository,
)
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
    MetricRepository,
)


_UNSET = object()


class InvalidMetricError(Exception):
    pass


class MetricNotFoundError(Exception):
    pass


class DuplicateMetricError(Exception):
    pass


class MetricContentNotFoundError(Exception):
    pass


class MetricService:
    def __init__(
        self,
        content_repository: ContentRepository,
        metric_repository: MetricRepository,
    ):
        self._content_repository = content_repository
        self._metric_repository = metric_repository

    def _get_owned_content(
        self,
        *,
        content_id: int,
        user_id: int,
    ) -> Content:
        content = (
            self._content_repository
            .get_by_id_and_user(
                content_id,
                user_id,
            )
        )

        if content is None:
            raise MetricContentNotFoundError

        return content

    @staticmethod
    def _validate_count(
        value: object,
    ) -> int:
        if type(value) is not int:
            raise InvalidMetricError

        if value < 0:
            raise InvalidMetricError

        return value

    @staticmethod
    def _validate_reference_date(
        value: object,
        publication_date: date,
    ) -> date:
        if (
            not isinstance(value, date)
            or isinstance(value, datetime)
        ):
            raise InvalidMetricError

        if value < publication_date:
            raise InvalidMetricError

        if value > date.today():
            raise InvalidMetricError

        return value

    def _ensure_unique_reference_date(
        self,
        *,
        content_id: int,
        data_referencia: date,
        exclude_metric_id: int | None = None,
    ) -> None:
        existing = (
            self._metric_repository
            .get_by_content_and_reference_date(
                content_id,
                data_referencia,
            )
        )

        if (
            existing is not None
            and existing.id != exclude_metric_id
        ):
            raise DuplicateMetricError

    def create(
        self,
        *,
        user_id: int,
        content_id: int,
        visualizacoes: object,
        curtidas: object,
        comentarios: object,
        compartilhamentos: object,
        alcance: object,
        data_referencia: object,
    ) -> Metric:
        content = self._get_owned_content(
            content_id=content_id,
            user_id=user_id,
        )

        validated_visualizacoes = (
            self._validate_count(visualizacoes)
        )
        validated_curtidas = (
            self._validate_count(curtidas)
        )
        validated_comentarios = (
            self._validate_count(comentarios)
        )
        validated_compartilhamentos = (
            self._validate_count(
                compartilhamentos
            )
        )
        validated_alcance = (
            self._validate_count(alcance)
        )

        validated_date = (
            self._validate_reference_date(
                data_referencia,
                content.data_publicacao,
            )
        )

        self._ensure_unique_reference_date(
            content_id=content.id,
            data_referencia=validated_date,
        )

        metric = Metric(
            id=None,
            conteudo_id=content.id,
            visualizacoes=(
                validated_visualizacoes
            ),
            curtidas=validated_curtidas,
            comentarios=validated_comentarios,
            compartilhamentos=(
                validated_compartilhamentos
            ),
            alcance=validated_alcance,
            data_referencia=validated_date,
            criado_em=datetime.now(timezone.utc),
        )

        try:
            return self._metric_repository.create(
                metric
            )
        except MetricPersistenceConflictError as exc:
            raise DuplicateMetricError from exc
```

The imports `replace` and `_UNSET` are intentionally included now because Task 3 extends this same file with PATCH support.

- [ ] **Step 4: Run and verify GREEN**

```powershell
python -m pytest tests/unit/test_metric_service_create.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Check existing content service tests**

```powershell
python -m pytest tests/unit/test_content_service_create.py tests/unit/test_content_service_crud.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add app/services/metric_service.py tests/unit/test_metric_service_create.py
git commit -m "feat: add metric creation rules"
```

---

### Task 3: MetricService — list, get, update e delete

**Files:**
- Modify: `backend/app/services/metric_service.py`
- Create: `backend/tests/unit/test_metric_service_crud.py`

**Interfaces:**
- Produces `list(user_id, content_id) -> list[Metric]`
- Produces `get(user_id, content_id, metric_id) -> Metric`
- Produces `update(...) -> Metric`
- Produces `delete(user_id, content_id, metric_id) -> None`

- [ ] **Step 1: Write failing CRUD tests**

Create `tests/unit/test_metric_service_crud.py`:

```python
from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.domain.content import Content
from app.repositories.in_memory_content_repository import (
    InMemoryContentRepository,
)
from app.repositories.in_memory_metric_repository import (
    InMemoryMetricRepository,
)
from app.services.metric_service import (
    DuplicateMetricError,
    InvalidMetricError,
    MetricContentNotFoundError,
    MetricNotFoundError,
    MetricService,
)


def setup_service():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="A",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=(
                date.today()
                - timedelta(days=5)
            ),
            criado_em=datetime.now(timezone.utc),
        )
    )

    other_content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="B",
            plataforma="TikTok",
            tipo="Vídeo",
            data_publicacao=(
                date.today()
                - timedelta(days=5)
            ),
            criado_em=datetime.now(timezone.utc),
        )
    )

    return (
        MetricService(
            content_repository,
            metric_repository,
        ),
        content,
        other_content,
    )


def create_metric(
    service,
    content,
    *,
    reference_date,
    alcance=80,
):
    return service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=alcance,
        data_referencia=reference_date,
    )


def test_list_returns_empty_for_owned_content():
    service, content, _ = setup_service()

    assert service.list(
        user_id=1,
        content_id=content.id,
    ) == []


def test_list_orders_by_reference_date_desc():
    service, content, _ = setup_service()

    older = create_metric(
        service,
        content,
        reference_date=(
            date.today() - timedelta(days=2)
        ),
    )
    newer = create_metric(
        service,
        content,
        reference_date=(
            date.today() - timedelta(days=1)
        ),
    )

    result = service.list(
        user_id=1,
        content_id=content.id,
    )

    assert [metric.id for metric in result] == [
        newer.id,
        older.id,
    ]


def test_list_hides_foreign_content():
    service, content, _ = setup_service()

    with pytest.raises(
        MetricContentNotFoundError
    ):
        service.list(
            user_id=999,
            content_id=content.id,
        )


def test_get_returns_metric_inside_content():
    service, content, _ = setup_service()
    metric = create_metric(
        service,
        content,
        reference_date=date.today(),
    )

    loaded = service.get(
        user_id=1,
        content_id=content.id,
        metric_id=metric.id,
    )

    assert loaded == metric


def test_get_rejects_metric_from_other_content():
    service, content, other_content = (
        setup_service()
    )
    metric = create_metric(
        service,
        other_content,
        reference_date=date.today(),
    )

    with pytest.raises(MetricNotFoundError):
        service.get(
            user_id=1,
            content_id=content.id,
            metric_id=metric.id,
        )


def test_update_changes_only_sent_field():
    service, content, _ = setup_service()
    metric = create_metric(
        service,
        content,
        reference_date=date.today(),
    )

    updated = service.update(
        user_id=1,
        content_id=content.id,
        metric_id=metric.id,
        alcance=999,
    )

    assert updated.alcance == 999
    assert (
        updated.visualizacoes
        == metric.visualizacoes
    )
    assert updated.data_referencia == (
        metric.data_referencia
    )


def test_update_accepts_zero():
    service, content, _ = setup_service()
    metric = create_metric(
        service,
        content,
        reference_date=date.today(),
    )

    updated = service.update(
        user_id=1,
        content_id=content.id,
        metric_id=metric.id,
        alcance=0,
    )

    assert updated.alcance == 0


def test_update_rejects_explicit_null():
    service, content, _ = setup_service()
    metric = create_metric(
        service,
        content,
        reference_date=date.today(),
    )

    with pytest.raises(InvalidMetricError):
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=metric.id,
            alcance=None,
        )


def test_update_rejects_empty_changes():
    service, content, _ = setup_service()
    metric = create_metric(
        service,
        content,
        reference_date=date.today(),
    )

    with pytest.raises(InvalidMetricError):
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=metric.id,
        )


def test_update_revalidates_reference_date():
    service, content, _ = setup_service()
    metric = create_metric(
        service,
        content,
        reference_date=date.today(),
    )

    with pytest.raises(InvalidMetricError):
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=metric.id,
            data_referencia=(
                content.data_publicacao
                - timedelta(days=1)
            ),
        )


def test_update_rejects_date_collision():
    service, content, _ = setup_service()

    first = create_metric(
        service,
        content,
        reference_date=(
            date.today() - timedelta(days=1)
        ),
    )
    second = create_metric(
        service,
        content,
        reference_date=date.today(),
    )

    with pytest.raises(DuplicateMetricError):
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=second.id,
            data_referencia=(
                first.data_referencia
            ),
        )


def test_delete_removes_metric():
    service, content, _ = setup_service()
    metric = create_metric(
        service,
        content,
        reference_date=date.today(),
    )

    service.delete(
        user_id=1,
        content_id=content.id,
        metric_id=metric.id,
    )

    with pytest.raises(MetricNotFoundError):
        service.get(
            user_id=1,
            content_id=content.id,
            metric_id=metric.id,
        )


def test_delete_rejects_missing_metric():
    service, content, _ = setup_service()

    with pytest.raises(MetricNotFoundError):
        service.delete(
            user_id=1,
            content_id=content.id,
            metric_id=999,
        )
```

- [ ] **Step 2: Run and verify RED**

```powershell
python -m pytest tests/unit/test_metric_service_crud.py -v
```

Expected: failures because list/get/update/delete are absent.

- [ ] **Step 3: Extend MetricService with CRUD**

Append these methods inside `MetricService` in `app/services/metric_service.py`:

```python
    def list(
        self,
        *,
        user_id: int,
        content_id: int,
    ) -> list[Metric]:
        content = self._get_owned_content(
            content_id=content_id,
            user_id=user_id,
        )

        return self._metric_repository.list_by_content(
            content.id
        )

    def get(
        self,
        *,
        user_id: int,
        content_id: int,
        metric_id: int,
    ) -> Metric:
        content = self._get_owned_content(
            content_id=content_id,
            user_id=user_id,
        )

        metric = (
            self._metric_repository
            .get_by_id_and_content(
                metric_id,
                content.id,
            )
        )

        if metric is None:
            raise MetricNotFoundError

        return metric

    def update(
        self,
        *,
        user_id: int,
        content_id: int,
        metric_id: int,
        visualizacoes: object = _UNSET,
        curtidas: object = _UNSET,
        comentarios: object = _UNSET,
        compartilhamentos: object = _UNSET,
        alcance: object = _UNSET,
        data_referencia: object = _UNSET,
    ) -> Metric:
        content = self._get_owned_content(
            content_id=content_id,
            user_id=user_id,
        )

        metric = (
            self._metric_repository
            .get_by_id_and_content(
                metric_id,
                content.id,
            )
        )

        if metric is None:
            raise MetricNotFoundError

        if (
            visualizacoes is _UNSET
            and curtidas is _UNSET
            and comentarios is _UNSET
            and compartilhamentos is _UNSET
            and alcance is _UNSET
            and data_referencia is _UNSET
        ):
            raise InvalidMetricError

        updated_reference_date = (
            self._validate_reference_date(
                data_referencia,
                content.data_publicacao,
            )
            if data_referencia is not _UNSET
            else metric.data_referencia
        )

        if (
            updated_reference_date
            != metric.data_referencia
        ):
            self._ensure_unique_reference_date(
                content_id=content.id,
                data_referencia=(
                    updated_reference_date
                ),
                exclude_metric_id=metric.id,
            )

        updated_metric = replace(
            metric,
            visualizacoes=(
                self._validate_count(
                    visualizacoes
                )
                if visualizacoes is not _UNSET
                else metric.visualizacoes
            ),
            curtidas=(
                self._validate_count(curtidas)
                if curtidas is not _UNSET
                else metric.curtidas
            ),
            comentarios=(
                self._validate_count(
                    comentarios
                )
                if comentarios is not _UNSET
                else metric.comentarios
            ),
            compartilhamentos=(
                self._validate_count(
                    compartilhamentos
                )
                if compartilhamentos
                is not _UNSET
                else metric.compartilhamentos
            ),
            alcance=(
                self._validate_count(alcance)
                if alcance is not _UNSET
                else metric.alcance
            ),
            data_referencia=(
                updated_reference_date
            ),
        )

        try:
            return self._metric_repository.update(
                updated_metric
            )
        except MetricPersistenceConflictError as exc:
            raise DuplicateMetricError from exc

    def delete(
        self,
        *,
        user_id: int,
        content_id: int,
        metric_id: int,
    ) -> None:
        metric = self.get(
            user_id=user_id,
            content_id=content_id,
            metric_id=metric_id,
        )

        self._metric_repository.delete(metric)
```

- [ ] **Step 4: Run MetricService tests**

```powershell
python -m pytest tests/unit/test_metric_service_create.py tests/unit/test_metric_service_crud.py -v
```

Expected: PASS.

- [ ] **Step 5: Run all unit tests**

```powershell
python -m pytest tests/unit -q
```

Expected: all unit tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add app/services/metric_service.py tests/unit/test_metric_service_crud.py
git commit -m "feat: add metric service crud"
```

---

### Task 4: MetricModel, migration 0003 e foreign keys SQLite

**Files:**
- Modify: `backend/app/database/connection.py`
- Modify: `backend/app/database/models.py`
- Create: `backend/alembic/versions/0003_create_metricas.py`
- Create: `backend/tests/integration/test_metric_model.py`
- Create: `backend/tests/integration/test_metric_migration.py`
- Create: `backend/tests/integration/test_sqlite_foreign_keys.py`

**Interfaces:**
- Produces table `metricas`
- Produces constraint `uq_metricas_conteudo_data_referencia`
- Produces SQLite engine with foreign keys enabled

- [ ] **Step 1: Write failing model test**

Create `tests/integration/test_metric_model.py`:

```python
from app.database.models import MetricModel


def test_metric_model_has_expected_columns_and_constraints():
    columns = set(
        MetricModel.__table__.columns.keys()
    )

    assert columns == {
        "id",
        "conteudo_id",
        "visualizacoes",
        "curtidas",
        "comentarios",
        "compartilhamentos",
        "alcance",
        "data_referencia",
        "criado_em",
    }

    foreign_key = next(
        iter(
            MetricModel.__table__
            .c.conteudo_id.foreign_keys
        )
    )

    assert foreign_key.target_fullname == (
        "conteudos.id"
    )
    assert foreign_key.ondelete == "CASCADE"

    unique_constraints = [
        constraint
        for constraint
        in MetricModel.__table__.constraints
        if constraint.__class__.__name__
        == "UniqueConstraint"
    ]

    assert len(unique_constraints) == 1

    constraint = unique_constraints[0]

    assert constraint.name == (
        "uq_metricas_conteudo_data_referencia"
    )
    assert [
        column.name
        for column in constraint.columns
    ] == [
        "conteudo_id",
        "data_referencia",
    ]
```

- [ ] **Step 2: Write failing migration test**

Create `tests/integration/test_metric_migration.py`:

```python
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import get_settings


def test_alembic_upgrade_head_creates_metric_table(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "metric_migration.db"
    database_url = f"sqlite:///{database_path}"

    monkeypatch.setenv(
        "DATABASE_URL",
        database_url,
    )
    get_settings.cache_clear()

    try:
        config = Config("alembic.ini")
        command.upgrade(config, "head")

        engine = create_engine(database_url)
        inspector = inspect(engine)

        assert "metricas" in (
            inspector.get_table_names()
        )

        columns = {
            column["name"]
            for column in inspector.get_columns(
                "metricas"
            )
        }

        assert columns == {
            "id",
            "conteudo_id",
            "visualizacoes",
            "curtidas",
            "comentarios",
            "compartilhamentos",
            "alcance",
            "data_referencia",
            "criado_em",
        }

        foreign_keys = (
            inspector.get_foreign_keys(
                "metricas"
            )
        )

        assert len(foreign_keys) == 1
        assert (
            foreign_keys[0]["referred_table"]
            == "conteudos"
        )
        assert (
            foreign_keys[0]["constrained_columns"]
            == ["conteudo_id"]
        )
        assert (
            foreign_keys[0]["referred_columns"]
            == ["id"]
        )
        assert (
            foreign_keys[0]
            .get("options", {})
            .get("ondelete")
            == "CASCADE"
        )

        unique_constraints = (
            inspector.get_unique_constraints(
                "metricas"
            )
        )

        matching = [
            constraint
            for constraint in unique_constraints
            if constraint["name"]
            == (
                "uq_metricas_conteudo_"
                "data_referencia"
            )
        ]

        assert len(matching) == 1
        assert matching[0]["column_names"] == [
            "conteudo_id",
            "data_referencia",
        ]
    finally:
        get_settings.cache_clear()
```

- [ ] **Step 3: Write failing SQLite foreign-key test**

Create `tests/integration/test_sqlite_foreign_keys.py`:

```python
from datetime import date, datetime, timezone

from sqlalchemy import select, text

from app.database import models  # noqa: F401
from app.database.connection import (
    Base,
    create_engine_from_url,
    create_session_factory,
)
from app.database.models import (
    ContentModel,
    MetricModel,
    UserModel,
)


def test_sqlite_engine_enables_foreign_keys(
    tmp_path,
):
    engine = create_engine_from_url(
        f"sqlite:///{tmp_path / 'fk.db'}"
    )

    with engine.connect() as connection:
        enabled = connection.scalar(
            text("PRAGMA foreign_keys")
        )

    assert enabled == 1


def test_deleting_content_cascades_metrics(
    tmp_path,
):
    engine = create_engine_from_url(
        f"sqlite:///{tmp_path / 'cascade.db'}"
    )
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(
        engine
    )

    with session_factory() as session:
        user = UserModel(
            nome="Carlos",
            email="carlos@email.com",
            senha_hash="hash",
            criado_em=datetime.now(timezone.utc),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        content = ContentModel(
            usuario_id=user.id,
            titulo="Post",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
        session.add(content)
        session.commit()
        session.refresh(content)

        metric = MetricModel(
            conteudo_id=content.id,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
        session.add(metric)
        session.commit()
        metric_id = metric.id

        session.delete(content)
        session.commit()

        remaining = session.scalar(
            select(MetricModel).where(
                MetricModel.id == metric_id
            )
        )

    assert remaining is None
```

- [ ] **Step 4: Run and verify RED**

```powershell
python -m pytest tests/integration/test_metric_model.py tests/integration/test_metric_migration.py tests/integration/test_sqlite_foreign_keys.py -v
```

Expected: failures because `MetricModel`, migration 0003 and SQLite PRAGMA wiring do not exist.

- [ ] **Step 5: Modify SQLite engine creation**

Replace `create_engine_from_url` in `app/database/connection.py` with this implementation and add `event` to the SQLAlchemy import:

```python
from sqlalchemy import create_engine, event
```

```python
def create_engine_from_url(
    database_url: str,
) -> Engine:
    connect_args = (
        {"check_same_thread": False}
        if database_url.startswith("sqlite")
        else {}
    )

    engine = create_engine(
        database_url,
        connect_args=connect_args,
    )

    if database_url.startswith("sqlite"):
        @event.listens_for(
            engine,
            "connect",
        )
        def set_sqlite_foreign_keys(
            dbapi_connection,
            _connection_record,
        ):
            cursor = dbapi_connection.cursor()
            cursor.execute(
                "PRAGMA foreign_keys=ON"
            )
            cursor.close()

    return engine
```

- [ ] **Step 6: Add MetricModel**

Add `UniqueConstraint` to imports in `app/database/models.py`:

```python
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
```

Append:

```python
class MetricModel(Base):
    __tablename__ = "metricas"

    __table_args__ = (
        UniqueConstraint(
            "conteudo_id",
            "data_referencia",
            name=(
                "uq_metricas_conteudo_"
                "data_referencia"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    conteudo_id: Mapped[int] = mapped_column(
        ForeignKey(
            "conteudos.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    visualizacoes: Mapped[int] = mapped_column(
        nullable=False,
    )

    curtidas: Mapped[int] = mapped_column(
        nullable=False,
    )

    comentarios: Mapped[int] = mapped_column(
        nullable=False,
    )

    compartilhamentos: Mapped[int] = (
        mapped_column(
            nullable=False,
        )
    )

    alcance: Mapped[int] = mapped_column(
        nullable=False,
    )

    data_referencia: Mapped[date] = (
        mapped_column(
            Date,
            nullable=False,
        )
    )

    criado_em: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            nullable=False,
        )
    )
```

- [ ] **Step 7: Create migration 0003**

Create `alembic/versions/0003_create_metricas.py`:

```python
from alembic import op
import sqlalchemy as sa


revision = "0003_create_metricas"
down_revision = "0002_create_conteudos"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "metricas",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "conteudo_id",
            sa.Integer(),
            sa.ForeignKey(
                "conteudos.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "visualizacoes",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "curtidas",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "comentarios",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "compartilhamentos",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "alcance",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "data_referencia",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "conteudo_id",
            "data_referencia",
            name=(
                "uq_metricas_conteudo_"
                "data_referencia"
            ),
        ),
    )


def downgrade():
    op.drop_table("metricas")
```

- [ ] **Step 8: Run targeted tests and verify GREEN**

```powershell
python -m pytest tests/integration/test_metric_model.py tests/integration/test_metric_migration.py tests/integration/test_sqlite_foreign_keys.py -v
```

Expected: PASS.

- [ ] **Step 9: Run previous model/migration tests**

```powershell
python -m pytest tests/integration/test_content_model.py tests/integration/test_content_migration.py -q
```

Expected: PASS.

- [ ] **Step 10: Commit**

```powershell
git add app/database/connection.py app/database/models.py alembic/versions/0003_create_metricas.py tests/integration/test_metric_model.py tests/integration/test_metric_migration.py tests/integration/test_sqlite_foreign_keys.py
git commit -m "feat: add metric persistence schema"
```

---

### Task 5: SQLAlchemyMetricRepository

**Files:**
- Create: `backend/app/repositories/sqlalchemy_metric_repository.py`
- Create: `backend/tests/integration/test_sqlalchemy_metric_repository.py`

**Interfaces:**
- Implements `MetricRepository`
- Raises `MetricPersistenceConflictError` for the named metric/date unique violation
- Re-raises unrelated `IntegrityError`

- [ ] **Step 1: Write failing repository tests**

Create `tests/integration/test_sqlalchemy_metric_repository.py`:

```python
from dataclasses import replace
from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.database import models  # noqa: F401
from app.database.connection import (
    Base,
    create_engine_from_url,
    create_session_factory,
)
from app.database.models import (
    ContentModel,
    UserModel,
)
from app.domain.metric import Metric
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
)
from app.repositories.sqlalchemy_metric_repository import (
    SQLAlchemyMetricRepository,
)


def setup_database(tmp_path):
    engine = create_engine_from_url(
        f"sqlite:///{tmp_path / 'metric_repo.db'}"
    )
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(
        engine
    )

    session = session_factory()

    user = UserModel(
        nome="Carlos",
        email="carlos@email.com",
        senha_hash="hash",
        criado_em=datetime.now(timezone.utc),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    content = ContentModel(
        usuario_id=user.id,
        titulo="Post",
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=(
            date.today() - timedelta(days=5)
        ),
        criado_em=datetime.now(timezone.utc),
    )
    other_content = ContentModel(
        usuario_id=user.id,
        titulo="Outro",
        plataforma="TikTok",
        tipo="Vídeo",
        data_publicacao=(
            date.today() - timedelta(days=5)
        ),
        criado_em=datetime.now(timezone.utc),
    )
    session.add_all([
        content,
        other_content,
    ])
    session.commit()
    session.refresh(content)
    session.refresh(other_content)

    return session, content, other_content


def make_metric(
    content_id,
    reference_date,
):
    return Metric(
        id=None,
        conteudo_id=content_id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=reference_date,
        criado_em=datetime.now(timezone.utc),
    )


def test_repository_create_and_get(
    tmp_path,
):
    session, content, _ = setup_database(
        tmp_path
    )

    try:
        repository = SQLAlchemyMetricRepository(
            session
        )
        created = repository.create(
            make_metric(
                content.id,
                date.today(),
            )
        )

        loaded = repository.get_by_id_and_content(
            created.id,
            content.id,
        )

        assert created.id is not None
        assert loaded == created
    finally:
        session.close()


def test_repository_lists_only_content_in_desc_order(
    tmp_path,
):
    session, content, other = setup_database(
        tmp_path
    )

    try:
        repository = SQLAlchemyMetricRepository(
            session
        )
        older = repository.create(
            make_metric(
                content.id,
                date.today()
                - timedelta(days=2),
            )
        )
        newer = repository.create(
            make_metric(
                content.id,
                date.today()
                - timedelta(days=1),
            )
        )
        repository.create(
            make_metric(
                other.id,
                date.today(),
            )
        )

        result = repository.list_by_content(
            content.id
        )

        assert [
            metric.id
            for metric in result
        ] == [
            newer.id,
            older.id,
        ]
    finally:
        session.close()


def test_repository_gets_by_content_and_date(
    tmp_path,
):
    session, content, _ = setup_database(
        tmp_path
    )

    try:
        repository = SQLAlchemyMetricRepository(
            session
        )
        created = repository.create(
            make_metric(
                content.id,
                date.today(),
            )
        )

        loaded = (
            repository
            .get_by_content_and_reference_date(
                content.id,
                date.today(),
            )
        )

        assert loaded == created
    finally:
        session.close()


def test_repository_update_persists(
    tmp_path,
):
    session, content, _ = setup_database(
        tmp_path
    )

    try:
        repository = SQLAlchemyMetricRepository(
            session
        )
        created = repository.create(
            make_metric(
                content.id,
                date.today(),
            )
        )

        updated = repository.update(
            replace(
                created,
                alcance=999,
            )
        )

        assert updated.alcance == 999
    finally:
        session.close()


def test_repository_delete_persists(
    tmp_path,
):
    session, content, _ = setup_database(
        tmp_path
    )

    try:
        repository = SQLAlchemyMetricRepository(
            session
        )
        created = repository.create(
            make_metric(
                content.id,
                date.today(),
            )
        )

        repository.delete(created)

        assert (
            repository.get_by_id_and_content(
                created.id,
                content.id,
            )
            is None
        )
    finally:
        session.close()


def test_repository_translates_duplicate_create(
    tmp_path,
):
    session, content, _ = setup_database(
        tmp_path
    )

    try:
        repository = SQLAlchemyMetricRepository(
            session
        )
        repository.create(
            make_metric(
                content.id,
                date.today(),
            )
        )

        with pytest.raises(
            MetricPersistenceConflictError
        ):
            repository.create(
                make_metric(
                    content.id,
                    date.today(),
                )
            )

        assert (
            len(
                repository.list_by_content(
                    content.id
                )
            )
            == 1
        )
    finally:
        session.close()


def test_repository_translates_duplicate_update(
    tmp_path,
):
    session, content, _ = setup_database(
        tmp_path
    )

    try:
        repository = SQLAlchemyMetricRepository(
            session
        )
        first = repository.create(
            make_metric(
                content.id,
                date.today()
                - timedelta(days=1),
            )
        )
        second = repository.create(
            make_metric(
                content.id,
                date.today(),
            )
        )

        with pytest.raises(
            MetricPersistenceConflictError
        ):
            repository.update(
                replace(
                    second,
                    data_referencia=(
                        first.data_referencia
                    ),
                )
            )

        assert (
            len(
                repository.list_by_content(
                    content.id
                )
            )
            == 2
        )
    finally:
        session.close()
```

- [ ] **Step 2: Run and verify RED**

```powershell
python -m pytest tests/integration/test_sqlalchemy_metric_repository.py -v
```

Expected: import failure because repository implementation does not exist.

- [ ] **Step 3: Implement SQLAlchemyMetricRepository**

Create `app/repositories/sqlalchemy_metric_repository.py`:

```python
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import MetricModel
from app.domain.metric import Metric
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
)


_CONSTRAINT_NAME = (
    "uq_metricas_conteudo_data_referencia"
)


class SQLAlchemyMetricRepository:
    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(
        model: MetricModel,
    ) -> Metric:
        return Metric(
            id=model.id,
            conteudo_id=model.conteudo_id,
            visualizacoes=model.visualizacoes,
            curtidas=model.curtidas,
            comentarios=model.comentarios,
            compartilhamentos=(
                model.compartilhamentos
            ),
            alcance=model.alcance,
            data_referencia=model.data_referencia,
            criado_em=model.criado_em,
        )

    @staticmethod
    def _is_duplicate_error(
        exc: IntegrityError,
    ) -> bool:
        diag = getattr(
            exc.orig,
            "diag",
            None,
        )

        if (
            diag is not None
            and getattr(
                diag,
                "constraint_name",
                None,
            )
            == _CONSTRAINT_NAME
        ):
            return True

        message = str(exc.orig)

        return (
            "UNIQUE constraint failed"
            in message
            and "metricas.conteudo_id"
            in message
            and "metricas.data_referencia"
            in message
        )

    def _commit_or_translate_conflict(
        self,
    ) -> None:
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()

            if self._is_duplicate_error(exc):
                raise (
                    MetricPersistenceConflictError
                ) from exc

            raise

    def create(
        self,
        metric: Metric,
    ) -> Metric:
        model = MetricModel(
            conteudo_id=metric.conteudo_id,
            visualizacoes=metric.visualizacoes,
            curtidas=metric.curtidas,
            comentarios=metric.comentarios,
            compartilhamentos=(
                metric.compartilhamentos
            ),
            alcance=metric.alcance,
            data_referencia=(
                metric.data_referencia
            ),
            criado_em=metric.criado_em,
        )

        self._session.add(model)
        self._commit_or_translate_conflict()
        self._session.refresh(model)

        return self._to_domain(model)

    def list_by_content(
        self,
        content_id: int,
    ) -> list[Metric]:
        statement = (
            select(MetricModel)
            .where(
                MetricModel.conteudo_id
                == content_id
            )
            .order_by(
                MetricModel
                .data_referencia.desc(),
                MetricModel.id.desc(),
            )
        )

        models = self._session.scalars(
            statement
        ).all()

        return [
            self._to_domain(model)
            for model in models
        ]

    def get_by_id_and_content(
        self,
        metric_id: int,
        content_id: int,
    ) -> Metric | None:
        statement = select(
            MetricModel
        ).where(
            MetricModel.id == metric_id,
            MetricModel.conteudo_id
            == content_id,
        )

        model = self._session.scalar(
            statement
        )

        if model is None:
            return None

        return self._to_domain(model)

    def get_by_content_and_reference_date(
        self,
        content_id: int,
        data_referencia: date,
    ) -> Metric | None:
        statement = select(
            MetricModel
        ).where(
            MetricModel.conteudo_id
            == content_id,
            MetricModel.data_referencia
            == data_referencia,
        )

        model = self._session.scalar(
            statement
        )

        if model is None:
            return None

        return self._to_domain(model)

    def update(
        self,
        metric: Metric,
    ) -> Metric:
        statement = select(
            MetricModel
        ).where(
            MetricModel.id == metric.id,
            MetricModel.conteudo_id
            == metric.conteudo_id,
        )

        model = self._session.scalar(
            statement
        )

        if model is None:
            return metric

        model.visualizacoes = (
            metric.visualizacoes
        )
        model.curtidas = metric.curtidas
        model.comentarios = metric.comentarios
        model.compartilhamentos = (
            metric.compartilhamentos
        )
        model.alcance = metric.alcance
        model.data_referencia = (
            metric.data_referencia
        )

        self._commit_or_translate_conflict()
        self._session.refresh(model)

        return self._to_domain(model)

    def delete(
        self,
        metric: Metric,
    ) -> None:
        statement = select(
            MetricModel
        ).where(
            MetricModel.id == metric.id,
            MetricModel.conteudo_id
            == metric.conteudo_id,
        )

        model = self._session.scalar(
            statement
        )

        if model is None:
            return

        self._session.delete(model)
        self._session.commit()
```

- [ ] **Step 4: Run and verify GREEN**

```powershell
python -m pytest tests/integration/test_sqlalchemy_metric_repository.py -v
```

Expected: PASS.

- [ ] **Step 5: Run repository regression set**

```powershell
python -m pytest tests/integration/test_sqlalchemy_user_repository.py tests/integration/test_sqlalchemy_content_repository.py tests/integration/test_sqlalchemy_metric_repository.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add app/repositories/sqlalchemy_metric_repository.py tests/integration/test_sqlalchemy_metric_repository.py
git commit -m "feat: add sqlalchemy metric repository"
```

---

### Task 6: Schemas, dependency injection e POST/LIST/GET

**Files:**
- Create: `backend/app/schemas/metric.py`
- Modify: `backend/app/dependencies.py`
- Create: `backend/app/controllers/metric_controller.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/integration/test_metric_api.py`

**Interfaces:**
- Produces `MetricCreateRequest`
- Produces `MetricUpdateRequest`
- Produces `MetricResponse`
- Produces `get_metric_repository`
- Produces `get_metric_service`
- Produces POST/LIST/GET nested routes

- [ ] **Step 1: Write failing API tests for POST/LIST/GET**

Create `tests/integration/test_metric_api.py`:

```python
from datetime import date, timedelta


def authenticated_headers(
    client,
    *,
    name="Carlos",
    email="carlos@email.com",
):
    register = client.post(
        "/auth/register",
        json={
            "nome": name,
            "email": email,
            "senha": "minhasenha",
        },
    )
    assert register.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": email,
            "senha": "minhasenha",
        },
    )
    assert login.status_code == 200

    token = login.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def create_content(
    client,
    headers,
    *,
    publication_date=None,
    title="Post",
):
    response = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": title,
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": (
                publication_date
                or date.today().isoformat()
            ),
        },
    )
    assert response.status_code == 201
    return response.json()


def metric_payload(
    *,
    reference_date=None,
):
    return {
        "visualizacoes": 100,
        "curtidas": 10,
        "comentarios": 2,
        "compartilhamentos": 3,
        "alcance": 80,
        "data_referencia": (
            reference_date
            or date.today().isoformat()
        ),
    }


def test_create_metric_returns_201_and_public_dto(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )

    response = client.post(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
        json=metric_payload(),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] is not None
    assert body["alcance"] == 80
    assert "criado_em" in body
    assert "conteudo_id" not in body
    assert "usuario_id" not in body


def test_list_metrics_returns_empty_list(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )

    response = client.get(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_metrics_orders_reference_date_desc(
    client,
):
    headers = authenticated_headers(client)
    publication = (
        date.today() - timedelta(days=3)
    )
    content = create_content(
        client,
        headers,
        publication_date=publication.isoformat(),
    )

    for reference in [
        date.today() - timedelta(days=2),
        date.today() - timedelta(days=1),
    ]:
        response = client.post(
            f"/conteudos/{content['id']}/metricas",
            headers=headers,
            json=metric_payload(
                reference_date=reference.isoformat()
            ),
        )
        assert response.status_code == 201

    response = client.get(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
    )

    body = response.json()

    assert response.status_code == 200
    assert body[0]["data_referencia"] == (
        date.today()
        - timedelta(days=1)
    ).isoformat()
    assert body[1]["data_referencia"] == (
        date.today()
        - timedelta(days=2)
    ).isoformat()


def test_get_metric_returns_owned_metric(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )

    created = client.post(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
        json=metric_payload(),
    ).json()

    response = client.get(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{created['id']}"
        ),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == (
        created["id"]
    )


def test_metric_routes_require_token(
    client,
):
    response = client.get(
        "/conteudos/1/metricas"
    )

    assert response.status_code == 401


def test_metric_routes_reject_invalid_token(
    client,
):
    response = client.get(
        "/conteudos/1/metricas",
        headers={
            "Authorization": "Bearer invalid"
        },
    )

    assert response.status_code == 401


def test_metric_routes_hide_foreign_content(
    client,
):
    owner_headers = authenticated_headers(
        client,
        email="owner@email.com",
    )
    content = create_content(
        client,
        owner_headers,
    )

    other_headers = authenticated_headers(
        client,
        name="Outro",
        email="other@email.com",
    )

    response = client.get(
        f"/conteudos/{content['id']}/metricas",
        headers=other_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conteúdo não encontrado."
    }
```

- [ ] **Step 2: Run and verify RED**

```powershell
python -m pytest tests/integration/test_metric_api.py -v
```

Expected: route failures because metric router does not exist.

- [ ] **Step 3: Create HTTP schemas**

Create `app/schemas/metric.py`:

```python
from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    StrictInt,
)


class MetricCreateRequest(BaseModel):
    visualizacoes: StrictInt
    curtidas: StrictInt
    comentarios: StrictInt
    compartilhamentos: StrictInt
    alcance: StrictInt
    data_referencia: date


class MetricResponse(BaseModel):
    id: int
    visualizacoes: int
    curtidas: int
    comentarios: int
    compartilhamentos: int
    alcance: int
    data_referencia: date
    criado_em: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class MetricUpdateRequest(BaseModel):
    visualizacoes: StrictInt | None = None
    curtidas: StrictInt | None = None
    comentarios: StrictInt | None = None
    compartilhamentos: StrictInt | None = None
    alcance: StrictInt | None = None
    data_referencia: date | None = None
```

Note: malformed transport types can be rejected directly by FastAPI/Pydantic with 422; service-level rule violations continue to use the exact business message from the spec.

- [ ] **Step 4: Wire dependencies**

Add imports to `app/dependencies.py`:

```python
from app.repositories.sqlalchemy_metric_repository import (
    SQLAlchemyMetricRepository,
)
from app.services.metric_service import MetricService
```

Append:

```python
def get_metric_repository(
    session: Session = Depends(get_db_session),
):
    return SQLAlchemyMetricRepository(session)


def get_metric_service(
    content_repository=Depends(
        get_content_repository
    ),
    metric_repository=Depends(
        get_metric_repository
    ),
):
    return MetricService(
        content_repository,
        metric_repository,
    )
```

- [ ] **Step 5: Create controller with POST/LIST/GET**

Create `app/controllers/metric_controller.py`:

```python
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.dependencies import (
    get_current_user,
    get_metric_service,
)
from app.schemas.metric import (
    MetricCreateRequest,
    MetricResponse,
    MetricUpdateRequest,
)
from app.services.metric_service import (
    DuplicateMetricError,
    InvalidMetricError,
    MetricContentNotFoundError,
    MetricNotFoundError,
    MetricService,
)


router = APIRouter(
    tags=["metricas"],
)


def _raise_content_not_found(exc):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Conteúdo não encontrado.",
    ) from exc


def _raise_metric_not_found(exc):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Métrica não encontrada.",
    ) from exc


def _raise_invalid_metric(exc):
    raise HTTPException(
        status_code=(
            status.HTTP_422_UNPROCESSABLE_CONTENT
        ),
        detail="Dados da métrica inválidos.",
    ) from exc


def _raise_duplicate_metric(exc):
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            "Já existe uma métrica para este "
            "conteúdo nesta data."
        ),
    ) from exc


@router.post(
    "/conteudos/{content_id}/metricas",
    response_model=MetricResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_metric(
    content_id: int,
    payload: MetricCreateRequest,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    try:
        return service.create(
            user_id=current_user.id,
            content_id=content_id,
            visualizacoes=payload.visualizacoes,
            curtidas=payload.curtidas,
            comentarios=payload.comentarios,
            compartilhamentos=(
                payload.compartilhamentos
            ),
            alcance=payload.alcance,
            data_referencia=(
                payload.data_referencia
            ),
        )
    except MetricContentNotFoundError as exc:
        _raise_content_not_found(exc)
    except DuplicateMetricError as exc:
        _raise_duplicate_metric(exc)
    except InvalidMetricError as exc:
        _raise_invalid_metric(exc)


@router.get(
    "/conteudos/{content_id}/metricas",
    response_model=list[MetricResponse],
)
def list_metrics(
    content_id: int,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    try:
        return service.list(
            user_id=current_user.id,
            content_id=content_id,
        )
    except MetricContentNotFoundError as exc:
        _raise_content_not_found(exc)


@router.get(
    (
        "/conteudos/{content_id}/metricas/"
        "{metric_id}"
    ),
    response_model=MetricResponse,
)
def get_metric(
    content_id: int,
    metric_id: int,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    try:
        return service.get(
            user_id=current_user.id,
            content_id=content_id,
            metric_id=metric_id,
        )
    except MetricContentNotFoundError as exc:
        _raise_content_not_found(exc)
    except MetricNotFoundError as exc:
        _raise_metric_not_found(exc)
```

`MetricUpdateRequest` is imported now because Task 7 extends this same controller.

- [ ] **Step 6: Include metric router**

Modify `app/main.py`:

```python
from app.controllers.metric_controller import (
    router as metric_router,
)
```

Add after existing routers:

```python
app.include_router(metric_router)
```

Do not alter `/health`.

- [ ] **Step 7: Run targeted API tests**

```powershell
python -m pytest tests/integration/test_metric_api.py -v
```

Expected: POST/LIST/GET/auth/ownership tests PASS.

- [ ] **Step 8: Run existing API regression tests**

```powershell
python -m pytest tests/integration/test_auth_dependency.py tests/integration/test_content_api.py -q
```

Expected: PASS.

- [ ] **Step 9: Commit**

```powershell
git add app/schemas/metric.py app/dependencies.py app/controllers/metric_controller.py app/main.py tests/integration/test_metric_api.py
git commit -m "feat: add metric read and create endpoints"
```

---

### Task 7: PATCH/DELETE API e cobertura de erros

**Files:**
- Modify: `backend/app/controllers/metric_controller.py`
- Modify: `backend/tests/integration/test_metric_api.py`

**Interfaces:**
- Produces PATCH nested route
- Produces DELETE nested route

- [ ] **Step 1: Append failing API tests**

Append to `tests/integration/test_metric_api.py`:

```python
def create_metric(
    client,
    headers,
    content_id,
    *,
    reference_date=None,
):
    response = client.post(
        f"/conteudos/{content_id}/metricas",
        headers=headers,
        json=metric_payload(
            reference_date=reference_date
        ),
    )
    assert response.status_code == 201
    return response.json()


def test_patch_metric_updates_one_field(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )
    metric = create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.patch(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{metric['id']}"
        ),
        headers=headers,
        json={"alcance": 999},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["alcance"] == 999
    assert (
        body["visualizacoes"]
        == metric["visualizacoes"]
    )


def test_patch_metric_accepts_zero(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )
    metric = create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.patch(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{metric['id']}"
        ),
        headers=headers,
        json={"alcance": 0},
    )

    assert response.status_code == 200
    assert response.json()["alcance"] == 0


def test_patch_metric_rejects_empty_payload(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )
    metric = create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.patch(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{metric['id']}"
        ),
        headers=headers,
        json={},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Dados da métrica inválidos."
    }


def test_patch_metric_rejects_explicit_null(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )
    metric = create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.patch(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{metric['id']}"
        ),
        headers=headers,
        json={"alcance": None},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Dados da métrica inválidos."
    }


def test_create_metric_rejects_negative_value(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )
    payload = metric_payload()
    payload["alcance"] = -1

    response = client.post(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Dados da métrica inválidos."
    }



def test_create_metric_rejects_reference_date_before_publication(
    client,
):
    headers = authenticated_headers(client)
    publication = (
        date.today() - timedelta(days=1)
    )
    content = create_content(
        client,
        headers,
        publication_date=publication.isoformat(),
    )

    response = client.post(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
        json=metric_payload(
            reference_date=(
                publication - timedelta(days=1)
            ).isoformat()
        ),
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Dados da métrica inválidos."
    }


def test_create_metric_rejects_future_reference_date(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )

    response = client.post(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
        json=metric_payload(
            reference_date=(
                date.today() + timedelta(days=1)
            ).isoformat()
        ),
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Dados da métrica inválidos."
    }


def test_create_metric_rejects_duplicate_date(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )
    create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.post(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
        json=metric_payload(),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Já existe uma métrica para este "
            "conteúdo nesta data."
        )
    }


def test_patch_metric_rejects_date_collision(
    client,
):
    headers = authenticated_headers(client)
    publication = (
        date.today() - timedelta(days=3)
    )
    content = create_content(
        client,
        headers,
        publication_date=publication.isoformat(),
    )

    first_date = (
        date.today() - timedelta(days=1)
    )

    first = create_metric(
        client,
        headers,
        content["id"],
        reference_date=first_date.isoformat(),
    )
    second = create_metric(
        client,
        headers,
        content["id"],
        reference_date=date.today().isoformat(),
    )

    response = client.patch(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{second['id']}"
        ),
        headers=headers,
        json={
            "data_referencia": (
                first["data_referencia"]
            )
        },
    )

    assert response.status_code == 409


def test_metric_id_from_other_content_is_hidden(
    client,
):
    headers = authenticated_headers(client)
    first_content = create_content(
        client,
        headers,
        title="A",
    )
    second_content = create_content(
        client,
        headers,
        title="B",
    )
    metric = create_metric(
        client,
        headers,
        second_content["id"],
    )

    response = client.get(
        (
            f"/conteudos/{first_content['id']}"
            f"/metricas/{metric['id']}"
        ),
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Métrica não encontrada."
    }


def test_delete_metric_returns_204(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )
    metric = create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.delete(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{metric['id']}"
        ),
        headers=headers,
    )

    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_metric_returns_404(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )

    response = client.delete(
        (
            f"/conteudos/{content['id']}"
            "/metricas/999"
        ),
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Métrica não encontrada."
    }
```

- [ ] **Step 2: Run and verify RED**

```powershell
python -m pytest tests/integration/test_metric_api.py -v
```

Expected: PATCH/DELETE tests fail because routes do not exist.

- [ ] **Step 3: Add PATCH route**

Append to `app/controllers/metric_controller.py`:

```python
@router.patch(
    (
        "/conteudos/{content_id}/metricas/"
        "{metric_id}"
    ),
    response_model=MetricResponse,
)
def update_metric(
    content_id: int,
    metric_id: int,
    payload: MetricUpdateRequest,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    changes = payload.model_dump(
        exclude_unset=True,
    )

    try:
        return service.update(
            user_id=current_user.id,
            content_id=content_id,
            metric_id=metric_id,
            **changes,
        )
    except MetricContentNotFoundError as exc:
        _raise_content_not_found(exc)
    except MetricNotFoundError as exc:
        _raise_metric_not_found(exc)
    except DuplicateMetricError as exc:
        _raise_duplicate_metric(exc)
    except InvalidMetricError as exc:
        _raise_invalid_metric(exc)
```

- [ ] **Step 4: Add DELETE route**

Append:

```python
@router.delete(
    (
        "/conteudos/{content_id}/metricas/"
        "{metric_id}"
    ),
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_metric(
    content_id: int,
    metric_id: int,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    try:
        service.delete(
            user_id=current_user.id,
            content_id=content_id,
            metric_id=metric_id,
        )
    except MetricContentNotFoundError as exc:
        _raise_content_not_found(exc)
    except MetricNotFoundError as exc:
        _raise_metric_not_found(exc)
```

- [ ] **Step 5: Run metric API tests and verify GREEN**

```powershell
python -m pytest tests/integration/test_metric_api.py -v
```

Expected: PASS.

- [ ] **Step 6: Run all integration tests**

```powershell
python -m pytest tests/integration -q
```

Expected: all integration tests PASS, including the SQLite cascade proof from Task 4.

- [ ] **Step 7: Commit**

```powershell
git add app/controllers/metric_controller.py tests/integration/test_metric_api.py
git commit -m "feat: complete metric api"
```

---

### Task 8: README, migration real e final verification

**Files:**
- Modify: `README.md`

**Interfaces:**
- No new runtime interface.
- Documents Marco 0.4 as current state.

- [ ] **Step 1: Update database section**

In `README.md`, replace:

```text
As migrations atuais criam as tabelas:

usuarios
conteudos

A tabela `conteudos` referencia `usuarios.id` por `usuario_id`.
```

with:

```text
As migrations atuais criam as tabelas:

usuarios
conteudos
metricas

A tabela `conteudos` referencia `usuarios.id` por `usuario_id`.

A tabela `metricas` referencia `conteudos.id` por `conteudo_id`, com `ON DELETE CASCADE`, e permite somente um snapshot por conteúdo por data de referência.
```

- [ ] **Step 2: Add metric endpoints to README**

After the content DELETE documentation, add:

```markdown
### POST /conteudos/{content_id}/metricas

Cria um snapshot de métricas para um conteúdo do usuário autenticado.

Exemplo:

```json
{
  "visualizacoes": 1700,
  "curtidas": 110,
  "comentarios": 14,
  "compartilhamentos": 22,
  "alcance": 1450,
  "data_referencia": "2026-08-24"
}
```

### GET /conteudos/{content_id}/metricas

Lista o histórico de snapshots do conteúdo, ordenado por data de referência decrescente.

### GET /conteudos/{content_id}/metricas/{metric_id}

Retorna um snapshot específico.

### PATCH /conteudos/{content_id}/metricas/{metric_id}

Atualiza parcialmente os valores ou a data de referência do snapshot.

### DELETE /conteudos/{content_id}/metricas/{metric_id}

Exclui definitivamente um snapshot e retorna `204 No Content`.
```

- [ ] **Step 3: Update Estado atual**

Replace the current Marco 0.3 block with:

```markdown
## Estado atual

O Marco 0.4 implementa:

```text
cadastro/login
      ↓
     JWT
      ↓
usuário autenticado
      ↓
CRUD de conteúdos
      ↓
histórico de métricas
      ↓
ownership por conteúdo
```

O backend possui autenticação, gerenciamento de conteúdos e snapshots históricos de métricas com arquitetura Controller–Service–Repository, testes unitários com Repositories em memória e testes de integração com SQLite isolado.

Cálculo de engajamento, dashboard e frontend fazem parte dos próximos marcos.
```

- [ ] **Step 4: Run Alembic upgrade on local development DB**

From `backend/`:

```powershell
python -m alembic upgrade head
python -m alembic current
```

Expected:

```text
0003_create_metricas (head)
```

- [ ] **Step 5: Run full suite**

```powershell
python -m pytest -q
```

Expected: zero failures; total test count must be greater than the previous 76.

- [ ] **Step 6: Verify installed dependencies**

```powershell
python -m pip check
```

Expected:

```text
No broken requirements found.
```

- [ ] **Step 7: Verify whitespace and working tree**

```powershell
git diff --check
git status --short
```

Expected: only intentional README change before the docs commit; no `.db`, cache or unrelated source files tracked.

- [ ] **Step 8: Commit README**

If currently inside `backend/`:

```powershell
git add ..\README.md
git commit -m "docs: mark metrics milestone complete"
```

- [ ] **Step 9: Run fresh final verification after commit**

```powershell
python -m pytest -q
python -m pip check
python -m alembic current
git diff --check
git status --short
git log --oneline -9
```

Expected:
- zero test failures
- no broken requirements
- `0003_create_metricas (head)`
- no `git diff --check` output
- empty `git status --short`
- recent history includes design, implementation-plan and Task 1–8 commits

---

## Final Acceptance Checklist

- [ ] POST metric returns 201.
- [ ] LIST returns 200 and date/id descending.
- [ ] GET individual returns 200.
- [ ] PATCH partial returns 200.
- [ ] DELETE returns 204.
- [ ] Missing/invalid JWT returns 401.
- [ ] Foreign content returns content 404.
- [ ] Metric outside requested content returns metric 404.
- [ ] Negative values are rejected.
- [ ] Non-integer service inputs are rejected.
- [ ] Zero values are accepted.
- [ ] Date before publication is rejected.
- [ ] Future date is rejected.
- [ ] Duplicate content/date returns 409.
- [ ] PATCH empty/null is rejected.
- [ ] DB unique constraint exists.
- [ ] FK `metricas.conteudo_id -> conteudos.id` exists with `ON DELETE CASCADE`.
- [ ] SQLite foreign keys are enabled.
- [ ] Deleting content removes metric rows.
- [ ] `Metric` has no `usuario_id`.
- [ ] Public DTO has no `conteudo_id` or `usuario_id`.
- [ ] No pagination, engagement, dashboard or frontend was introduced.
- [ ] All previous and new tests pass.
- [ ] Alembic reports `0003_create_metricas (head)`.
- [ ] Working tree is clean.
