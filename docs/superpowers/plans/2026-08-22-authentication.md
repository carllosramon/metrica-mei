# Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar cadastro, login JWT e identificação do usuário autenticado no MetricaMEI, com persistência SQLAlchemy/SQLite, migrations Alembic e testes unitários e de integração.

**Architecture:** A API seguirá Controller → Service → Repository. O `AuthService` conterá as regras de negócio e dependerá de `UserRepository`; a aplicação real usará `SQLAlchemyUserRepository`, enquanto testes unitários usarão `InMemoryUserRepository`. Senhas serão protegidas com Argon2 e JWT será usado apenas como access token de 30 minutos.

**Tech Stack:** Python 3.14, FastAPI, Pydantic, SQLAlchemy, SQLite, Alembic, argon2-cffi, PyJWT, pytest, httpx2.

**Spec:** `docs/superpowers/specs/2026-08-22-authentication-design.md`

## Global Constraints

- Cadastro separado do login; `POST /auth/register` não autentica automaticamente.
- Usuário: `id`, `nome`, `email`, `senha_hash`, `criado_em`.
- Nome: obrigatório, trim, 2–100 caracteres.
- E-mail: obrigatório, válido, trim, lowercase e único.
- Senha: obrigatória, 8–128 caracteres e nunca persistida em texto puro.
- Hash de senha: Argon2.
- JWT: HS256, 30 minutos, sem refresh token; payload mínimo `sub` e `exp`.
- `.env` e banco SQLite de desenvolvimento não podem ser versionados.
- `/health` deve continuar funcionando e permanecer fora das camadas de negócio.
- Testes unitários não usam HTTP, SQLite ou SQLAlchemy.
- Testes de integração usam SQLite isolado do banco de desenvolvimento.

---

## File map

- `backend/app/config.py`: configurações carregadas do ambiente.
- `backend/app/domain/user.py`: entidade de domínio `User`.
- `backend/app/repositories/user_repository.py`: contrato `UserRepository`.
- `backend/app/repositories/in_memory_user_repository.py`: repositório para testes unitários.
- `backend/app/repositories/sqlalchemy_user_repository.py`: persistência real.
- `backend/app/services/auth_service.py`: regras de cadastro, login e usuário atual.
- `backend/app/security/password.py`: Argon2.
- `backend/app/security/jwt.py`: geração e validação do JWT.
- `backend/app/database/connection.py`: engine, base e session factory.
- `backend/app/database/models.py`: modelo SQLAlchemy `UserModel`.
- `backend/app/schemas/auth.py`: schemas HTTP.
- `backend/app/dependencies.py`: composição das dependências FastAPI.
- `backend/app/controllers/auth_controller.py`: endpoints `/auth/*`.
- `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/0001_create_usuarios.py`: migrations.
- `backend/tests/unit/*`: regras de negócio sem banco/HTTP.
- `backend/tests/integration/*`: API e persistência com SQLite isolado.

---

### Task 1: Configuration and dependency baseline

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/.env.example`
- Modify: `.gitignore`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/unit/test_config.py`

**Interfaces:**
- Produces: `Settings`, `get_settings() -> Settings`.
- Later tasks consume `database_url`, `jwt_secret`, `jwt_algorithm`, `jwt_expires_minutes`.

- [ ] **Step 1: Install the new top-level dependencies**

Run from `backend/` with `.venv` active:

```powershell
python -m pip install sqlalchemy alembic argon2-cffi PyJWT pydantic-settings email-validator
python -m pip freeze | Set-Content -Encoding ascii requirements.txt
```

- [ ] **Step 2: Write the failing settings test**

Create `tests/unit/test_config.py`:

```python
from app.config import get_settings


def test_settings_reads_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/test.db")
    monkeypatch.setenv("JWT_SECRET", "segredo-de-teste")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_EXPIRES_MINUTES", "30")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.database_url == "sqlite:///./data/test.db"
    assert settings.jwt_secret == "segredo-de-teste"
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expires_minutes == 30

    get_settings.cache_clear()
```

- [ ] **Step 3: Run test to verify RED**

```powershell
python -m pytest tests/unit/test_config.py -v
```

Expected: FAIL because `app.config` does not exist.

- [ ] **Step 4: Write minimal configuration code**

Create `app/config.py`:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/metrica_mei.db"
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 5: Add safe environment templates and DB ignore rule**

Create `backend/.env.example`:

```text
DATABASE_URL=sqlite:///./data/metrica_mei.db
JWT_SECRET=replace-with-a-local-secret
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=30
```

Append to root `.gitignore`:

```text
# Local MetricaMEI database
backend/data/*.db
```

Create a local, untracked `backend/.env`:

```powershell
$secret = python -c "import secrets; print(secrets.token_urlsafe(48))"
@"
DATABASE_URL=sqlite:///./data/metrica_mei.db
JWT_SECRET=$secret
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=30
"@ | Set-Content -Encoding ascii .env
```

- [ ] **Step 6: Verify GREEN and safety**

```powershell
python -m pytest tests/unit/test_config.py -v
python -m pip check
cd ..
git check-ignore -v backend/.env
```

Expected: test PASS, no broken requirements, `.env` ignored.

- [ ] **Step 7: Commit**

```powershell
git add .gitignore backend/.env.example backend/requirements.txt backend/app/config.py backend/tests/unit/test_config.py
git commit -m "chore: configure authentication dependencies"
```

---

### Task 2: User domain, repository contract and registration service

**Files:**
- Create: `backend/app/domain/__init__.py`
- Create: `backend/app/domain/user.py`
- Create: `backend/app/repositories/__init__.py`
- Create: `backend/app/repositories/user_repository.py`
- Create: `backend/app/repositories/in_memory_user_repository.py`
- Create: `backend/app/security/__init__.py`
- Create: `backend/app/security/password.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/auth_service.py`
- Test: `backend/tests/unit/test_auth_service_registration.py`

**Interfaces:**
- Produces `User(id: int | None, nome: str, email: str, senha_hash: str, criado_em: datetime)`.
- Produces `UserRepository.get_by_email(email)`, `get_by_id(user_id)`, `create(user)`.
- Produces `PasswordService.hash(password)` and `verify(password, password_hash)`.
- Produces `AuthService.register(nome, email, senha) -> User`.

- [ ] **Step 1: Write failing registration tests**

Create `tests/unit/test_auth_service_registration.py`:

```python
import pytest

from app.repositories.in_memory_user_repository import InMemoryUserRepository
from app.security.password import PasswordService
from app.services.auth_service import AuthService, EmailAlreadyRegisteredError


def make_service():
    repository = InMemoryUserRepository()
    password_service = PasswordService()
    return AuthService(repository, password_service), repository, password_service


def test_register_normalizes_user_and_hashes_password():
    service, repository, password_service = make_service()
    user = service.register("  Carlos Ramon  ", "  CARLOS@EMAIL.COM  ", "minhasenha")

    assert user.id == 1
    assert user.nome == "Carlos Ramon"
    assert user.email == "carlos@email.com"
    assert user.senha_hash != "minhasenha"
    assert password_service.verify("minhasenha", user.senha_hash)
    assert repository.get_by_email("carlos@email.com") == user


def test_register_rejects_duplicate_email_case_insensitively():
    service, _, _ = make_service()
    service.register("Carlos", "carlos@email.com", "minhasenha")

    with pytest.raises(EmailAlreadyRegisteredError):
        service.register("Outro", "CARLOS@email.com", "outrasenha")
```

- [ ] **Step 2: Run and confirm RED**

```powershell
python -m pytest tests/unit/test_auth_service_registration.py -v
```

Expected: FAIL because domain/repository/service modules do not exist.

- [ ] **Step 3: Implement domain and repository contract**

Create `app/domain/user.py`:

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class User:
    id: int | None
    nome: str
    email: str
    senha_hash: str
    criado_em: datetime
```

Create `app/repositories/user_repository.py`:

```python
from typing import Protocol

from app.domain.user import User


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None: ...
    def get_by_id(self, user_id: int) -> User | None: ...
    def create(self, user: User) -> User: ...
```

- [ ] **Step 4: Implement in-memory repository**

Create `app/repositories/in_memory_user_repository.py`:

```python
from dataclasses import replace

from app.domain.user import User


class InMemoryUserRepository:
    def __init__(self):
        self._users: dict[int, User] = {}
        self._next_id = 1

    def get_by_email(self, email: str) -> User | None:
        return next((user for user in self._users.values() if user.email == email), None)

    def get_by_id(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def create(self, user: User) -> User:
        stored_user = replace(user, id=self._next_id)
        self._users[self._next_id] = stored_user
        self._next_id += 1
        return stored_user
```

- [ ] **Step 5: Implement Argon2 and registration service**

Create `app/security/password.py`:

```python
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


class PasswordService:
    def __init__(self):
        self._hasher = PasswordHasher()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
```

Create `app/services/auth_service.py`:

```python
from datetime import datetime, timezone

from app.domain.user import User
from app.repositories.user_repository import UserRepository
from app.security.password import PasswordService


class EmailAlreadyRegisteredError(Exception):
    pass


class AuthService:
    def __init__(self, repository: UserRepository, password_service: PasswordService):
        self._repository = repository
        self._password_service = password_service

    def register(self, nome: str, email: str, senha: str) -> User:
        normalized_name = nome.strip()
        normalized_email = email.strip().lower()
        if self._repository.get_by_email(normalized_email) is not None:
            raise EmailAlreadyRegisteredError

        user = User(
            id=None,
            nome=normalized_name,
            email=normalized_email,
            senha_hash=self._password_service.hash(senha),
            criado_em=datetime.now(timezone.utc),
        )
        return self._repository.create(user)
```

Create empty `__init__.py` files for the new packages.

- [ ] **Step 6: Verify GREEN and regression**

```powershell
python -m pytest tests/unit/test_auth_service_registration.py -v
python -m pytest -v
```

Expected: registration tests PASS and `/health` remains PASS.

- [ ] **Step 7: Commit**

```powershell
git add backend/app backend/tests/unit
git commit -m "feat: add user registration domain service"
```

---

### Task 3: SQLAlchemy persistence and Alembic migration

**Files:**
- Create: `backend/app/database/__init__.py`
- Create: `backend/app/database/connection.py`
- Create: `backend/app/database/models.py`
- Create: `backend/app/repositories/sqlalchemy_user_repository.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_create_usuarios.py`
- Create: `backend/data/.gitkeep`
- Test: `backend/tests/integration/test_sqlalchemy_user_repository.py`

**Interfaces:**
- Produces `Base`, `create_engine_from_url(url)`, `create_session_factory(engine)`.
- Produces `UserModel` mapped to `usuarios`.
- Produces `SQLAlchemyUserRepository` implementing `UserRepository`.

- [ ] **Step 1: Write failing repository test**

Create `tests/integration/test_sqlalchemy_user_repository.py`:

```python
from datetime import datetime, timezone

from app.database.connection import Base, create_engine_from_url, create_session_factory
from app.database import models  # noqa: F401
from app.domain.user import User
from app.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository


def test_sqlalchemy_repository_persists_and_reads_user(tmp_path):
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'repository.db'}")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        repository = SQLAlchemyUserRepository(session)
        created = repository.create(
            User(None, "Carlos", "carlos@email.com", "hash", datetime.now(timezone.utc))
        )
        loaded = repository.get_by_email("carlos@email.com")

    assert created.id is not None
    assert loaded is not None
    assert loaded.id == created.id
```

- [ ] **Step 2: Run and confirm RED**

```powershell
python -m pytest tests/integration/test_sqlalchemy_user_repository.py -v
```

- [ ] **Step 3: Implement SQLAlchemy connection/model/repository**

Create `app/database/connection.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def create_engine_from_url(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def create_session_factory(engine: Engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
```

Create `app/database/models.py`:

```python
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class UserModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

Create `app/repositories/sqlalchemy_user_repository.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import UserModel
from app.domain.user import User


class SQLAlchemyUserRepository:
    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(model.id, model.nome, model.email, model.senha_hash, model.criado_em)

    def get_by_email(self, email: str) -> User | None:
        model = self._session.scalar(select(UserModel).where(UserModel.email == email))
        return self._to_domain(model) if model is not None else None

    def get_by_id(self, user_id: int) -> User | None:
        model = self._session.get(UserModel, user_id)
        return self._to_domain(model) if model is not None else None

    def create(self, user: User) -> User:
        model = UserModel(
            nome=user.nome,
            email=user.email,
            senha_hash=user.senha_hash,
            criado_em=user.criado_em,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)
```

- [ ] **Step 4: Verify repository GREEN**

```powershell
python -m pytest tests/integration/test_sqlalchemy_user_repository.py -v
```

- [ ] **Step 5: Initialize Alembic and configure metadata**

From `backend/`:

```powershell
python -m alembic init alembic
```

Replace `alembic/env.py` with:

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.database.connection import Base
from app.database import models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Create `alembic/versions/0001_create_usuarios.py`:

```python
from alembic import op
import sqlalchemy as sa

revision = "0001_create_usuarios"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_usuarios_email"),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)


def downgrade():
    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_table("usuarios")
```

Create `data/.gitkeep`.

- [ ] **Step 6: Verify migration**

```powershell
python -m alembic upgrade head
python -c "import sqlite3; c=sqlite3.connect('data/metrica_mei.db'); print(c.execute(\"select name from sqlite_master where type='table' and name='usuarios'\").fetchone()); c.close()"
```

Expected: `('usuarios',)`.

- [ ] **Step 7: Full tests and commit**

```powershell
python -m pytest -v
cd ..
git add backend/app/database backend/app/repositories/sqlalchemy_user_repository.py backend/alembic.ini backend/alembic backend/data/.gitkeep backend/tests/integration/test_sqlalchemy_user_repository.py
git commit -m "feat: add user persistence and migration"
```

---

### Task 4: Registration HTTP endpoint

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/controllers/__init__.py`
- Create: `backend/app/controllers/auth_controller.py`
- Create: `backend/app/dependencies.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/integration/conftest.py`
- Create: `backend/tests/integration/test_auth_register.py`

**Interfaces:**
- Produces `POST /auth/register`.
- Produces `get_db_session()`, `get_user_repository()`, `get_auth_service()`.

- [ ] **Step 1: Write failing endpoint tests**

Create `tests/integration/test_auth_register.py`:

```python
def test_register_returns_201_and_public_user(client):
    response = client.post(
        "/auth/register",
        json={"nome": "Carlos Ramon", "email": "CARLOS@EMAIL.COM", "senha": "minhasenha"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "carlos@email.com"
    assert "senha" not in body
    assert "senha_hash" not in body


def test_register_returns_409_for_duplicate_email(client):
    payload = {"nome": "Carlos", "email": "carlos@email.com", "senha": "minhasenha"}
    assert client.post("/auth/register", json=payload).status_code == 201
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json() == {"detail": "E-mail já cadastrado."}


def test_register_returns_422_for_invalid_payload(client):
    response = client.post(
        "/auth/register",
        json={"nome": "C", "email": "email-invalido", "senha": "123"},
    )
    assert response.status_code == 422
```

- [ ] **Step 2: Create isolated SQLite client fixture**

Create `tests/integration/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient

from app.database.connection import Base, create_engine_from_url, create_session_factory
from app.database import models  # noqa: F401
from app.dependencies import get_db_session
from app.main import app


@pytest.fixture
def client(tmp_path):
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'api.db'}")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    def override_db_session():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

- [ ] **Step 3: Run and confirm RED**

```powershell
python -m pytest tests/integration/test_auth_register.py -v
```

- [ ] **Step 4: Implement schemas**

Create `app/schemas/auth.py`:

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)

    @field_validator("nome", mode="before")
    @classmethod
    def normalize_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class UserResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 5: Implement dependencies/controller and mount router**

Create `app/dependencies.py`:

```python
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.connection import create_engine_from_url, create_session_factory
from app.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.security.password import PasswordService
from app.services.auth_service import AuthService


@lru_cache
def get_engine():
    return create_engine_from_url(get_settings().database_url)


@lru_cache
def get_session_factory():
    return create_session_factory(get_engine())


def get_db_session():
    with get_session_factory()() as session:
        yield session


def get_user_repository(session: Session = Depends(get_db_session)):
    return SQLAlchemyUserRepository(session)


def get_auth_service(repository=Depends(get_user_repository)):
    return AuthService(repository, PasswordService())
```

Create `app/controllers/auth_controller.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_auth_service
from app.schemas.auth import RegisterRequest, UserResponse
from app.services.auth_service import AuthService, EmailAlreadyRegisteredError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return service.register(payload.nome, str(payload.email), payload.senha)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.") from exc
```

Modify `app/main.py`:

```python
from fastapi import FastAPI

from app.controllers.auth_controller import router as auth_router

app = FastAPI(title="MetricaMEI API", version="0.2.0")
app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 6: Verify GREEN and regression**

```powershell
python -m pytest tests/integration/test_auth_register.py -v
python -m pytest -v
```

- [ ] **Step 7: Commit**

```powershell
git add backend/app backend/tests/integration
git commit -m "feat: add user registration endpoint"
```

---

### Task 5: Login and JWT access token

**Files:**
- Create: `backend/app/security/jwt.py`
- Modify: `backend/app/services/auth_service.py`
- Modify: `backend/app/dependencies.py`
- Modify: `backend/app/schemas/auth.py`
- Modify: `backend/app/controllers/auth_controller.py`
- Modify: `backend/tests/integration/conftest.py`
- Modify: `backend/tests/unit/test_auth_service_registration.py`
- Create: `backend/tests/unit/test_auth_service_login.py`
- Create: `backend/tests/integration/test_auth_login.py`

**Interfaces:**
- Produces `TokenService.create_access_token(user_id) -> str` and `decode_subject(token) -> int | None`.
- Changes `AuthService` constructor to `(repository, password_service, token_service)`.
- Produces `AuthService.login(email, senha) -> str` and `POST /auth/login`.

- [ ] **Step 1: Write failing login service tests**

Create `tests/unit/test_auth_service_login.py`:

```python
import pytest

from app.repositories.in_memory_user_repository import InMemoryUserRepository
from app.security.jwt import TokenService
from app.security.password import PasswordService
from app.services.auth_service import AuthService, InvalidCredentialsError


def make_service():
    repository = InMemoryUserRepository()
    service = AuthService(repository, PasswordService(), TokenService("test-secret", "HS256", 30))
    service.register("Carlos", "carlos@email.com", "minhasenha")
    return service


def test_login_returns_token_for_valid_credentials():
    assert isinstance(make_service().login("CARLOS@EMAIL.COM", "minhasenha"), str)


def test_login_rejects_wrong_password():
    with pytest.raises(InvalidCredentialsError):
        make_service().login("carlos@email.com", "senhaerrada")


def test_login_rejects_unknown_email():
    with pytest.raises(InvalidCredentialsError):
        make_service().login("ninguem@email.com", "minhasenha")
```

- [ ] **Step 2: Run and confirm RED**

```powershell
python -m pytest tests/unit/test_auth_service_login.py -v
```

- [ ] **Step 3: Implement JWT service**

Create `app/security/jwt.py`:

```python
from datetime import datetime, timedelta, timezone

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError


class TokenService:
    def __init__(self, secret: str, algorithm: str = "HS256", expires_minutes: int = 30):
        self._secret = secret
        self._algorithm = algorithm
        self._expires_minutes = expires_minutes

    def create_access_token(self, user_id: int) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self._expires_minutes)
        return jwt.encode({"sub": str(user_id), "exp": expires_at}, self._secret, algorithm=self._algorithm)

    def decode_subject(self, token: str) -> int | None:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            return int(payload["sub"])
        except (ExpiredSignatureError, InvalidTokenError, KeyError, TypeError, ValueError):
            return None
```

- [ ] **Step 4: Extend AuthService for login**

Add `TokenService`, `InvalidCredentialsError`, third constructor dependency, and:

```python
def login(self, email: str, senha: str) -> str:
    user = self._repository.get_by_email(email.strip().lower())
    if user is None or not self._password_service.verify(senha, user.senha_hash):
        raise InvalidCredentialsError
    return self._token_service.create_access_token(user.id)
```

Update registration unit-test constructors to pass `TokenService("test-secret", "HS256", 30)`.

- [ ] **Step 5: Add HTTP login schema, dependency wiring and endpoint**

Append to `app/schemas/auth.py`:

```python
class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

Change `get_auth_service`:

```python
from app.config import Settings, get_settings
from app.security.jwt import TokenService


def get_auth_service(repository=Depends(get_user_repository), settings: Settings = Depends(get_settings)):
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET não configurado.")
    return AuthService(
        repository,
        PasswordService(),
        TokenService(settings.jwt_secret, settings.jwt_algorithm, settings.jwt_expires_minutes),
    )
```

Add login endpoint:

```python
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)):
    try:
        token = service.login(str(payload.email), payload.senha)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return TokenResponse(access_token=token)
```

- [ ] **Step 6: Override test settings**

In `tests/integration/conftest.py`, add:

```python
from app.config import Settings, get_settings

app.dependency_overrides[get_settings] = lambda: Settings(
    database_url=f"sqlite:///{tmp_path / 'api.db'}",
    jwt_secret="test-secret",
    jwt_algorithm="HS256",
    jwt_expires_minutes=30,
)
```

- [ ] **Step 7: Write API login tests**

Create `tests/integration/test_auth_login.py`:

```python
def register(client):
    return client.post(
        "/auth/register",
        json={"nome": "Carlos", "email": "carlos@email.com", "senha": "minhasenha"},
    )


def test_login_returns_access_token(client):
    assert register(client).status_code == 201
    response = client.post("/auth/login", json={"email": "carlos@email.com", "senha": "minhasenha"})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_returns_401_for_invalid_credentials(client):
    assert register(client).status_code == 201
    response = client.post("/auth/login", json={"email": "carlos@email.com", "senha": "errada"})
    assert response.status_code == 401
    assert response.json() == {"detail": "E-mail ou senha inválidos."}
```

- [ ] **Step 8: Verify GREEN and commit**

```powershell
python -m pytest tests/unit/test_auth_service_login.py tests/integration/test_auth_login.py -v
python -m pytest -v
cd ..
git add backend/app backend/tests
git commit -m "feat: add jwt login"
```

---

### Task 6: Protected `/auth/me`

**Files:**
- Modify: `backend/app/services/auth_service.py`
- Modify: `backend/app/controllers/auth_controller.py`
- Create: `backend/tests/unit/test_auth_service_current_user.py`
- Create: `backend/tests/integration/test_auth_me.py`

**Interfaces:**
- Produces `AuthService.get_current_user(token) -> User`.
- Produces `GET /auth/me` with Bearer authentication.

- [ ] **Step 1: Write failing current-user tests**

Create `tests/unit/test_auth_service_current_user.py`:

```python
import pytest

from app.repositories.in_memory_user_repository import InMemoryUserRepository
from app.security.jwt import TokenService
from app.security.password import PasswordService
from app.services.auth_service import AuthService, UnauthenticatedError


def test_get_current_user_returns_token_subject_user():
    repository = InMemoryUserRepository()
    tokens = TokenService("test-secret", "HS256", 30)
    service = AuthService(repository, PasswordService(), tokens)
    user = service.register("Carlos", "carlos@email.com", "minhasenha")
    token = tokens.create_access_token(user.id)
    assert service.get_current_user(token) == user


def test_get_current_user_rejects_invalid_token():
    service = AuthService(InMemoryUserRepository(), PasswordService(), TokenService("test-secret"))
    with pytest.raises(UnauthenticatedError):
        service.get_current_user("token-invalido")
```

- [ ] **Step 2: Run and confirm RED**

```powershell
python -m pytest tests/unit/test_auth_service_current_user.py -v
```

- [ ] **Step 3: Implement current-user rule**

Add:

```python
class UnauthenticatedError(Exception):
    pass


def get_current_user(self, token: str) -> User:
    user_id = self._token_service.decode_subject(token)
    if user_id is None:
        raise UnauthenticatedError
    user = self._repository.get_by_id(user_id)
    if user is None:
        raise UnauthenticatedError
    return user
```

- [ ] **Step 4: Add protected controller endpoint**

Add:

```python
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


@router.get("/me", response_model=UserResponse)
def me(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    service: AuthService = Depends(get_auth_service),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Não autenticado.", headers={"WWW-Authenticate": "Bearer"})
    try:
        return service.get_current_user(credentials.credentials)
    except UnauthenticatedError as exc:
        raise HTTPException(
            status_code=401,
            detail="Não autenticado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
```

- [ ] **Step 5: Write integration tests**

Create `tests/integration/test_auth_me.py`:

```python
from app.security.jwt import TokenService


def register_and_login(client):
    assert client.post(
        "/auth/register",
        json={"nome": "Carlos", "email": "carlos@email.com", "senha": "minhasenha"},
    ).status_code == 201
    response = client.post("/auth/login", json={"email": "carlos@email.com", "senha": "minhasenha"})
    return response.json()["access_token"]


def test_me_returns_authenticated_user(client):
    token = register_and_login(client)
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "carlos@email.com"
    assert "senha_hash" not in response.json()


def test_me_returns_401_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Não autenticado."}


def test_me_returns_401_for_invalid_token(client):
    assert client.get("/auth/me", headers={"Authorization": "Bearer invalido"}).status_code == 401


def test_me_returns_401_for_expired_token(client):
    assert client.post(
        "/auth/register",
        json={"nome": "Carlos", "email": "carlos@email.com", "senha": "minhasenha"},
    ).status_code == 201
    expired = TokenService("test-secret", "HS256", -1).create_access_token(1)
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Não autenticado."}
```

- [ ] **Step 6: Verify GREEN and commit**

```powershell
python -m pytest tests/unit/test_auth_service_current_user.py tests/integration/test_auth_me.py -v
python -m pytest -v
cd ..
git add backend/app backend/tests
git commit -m "feat: add authenticated user endpoint"
```

---

### Task 7: Final validation and reproducibility

**Files:**
- Modify: `README.md`

**Interfaces:**
- Produces documented setup and a branch ready for PR review.

- [ ] **Step 1: Document setup**

Add to README:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

State that `JWT_SECRET` must be replaced with a local secret.

- [ ] **Step 2: Verify migration**

```powershell
python -m alembic upgrade head
python -m alembic current
```

Expected: `0001_create_usuarios`.

- [ ] **Step 3: Verify all tests and dependencies**

```powershell
python -m pytest -v
python -m pip check
```

Expected: zero failures and `No broken requirements found.`

- [ ] **Step 4: Verify secrets/database are ignored**

From repo root:

```powershell
git check-ignore -v backend/.env
git check-ignore -v backend/data/metrica_mei.db
git status
```

- [ ] **Step 5: Smoke-test API**

Run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Use `/docs` in this order:

```text
POST /auth/register -> 201
POST /auth/login    -> 200 + access_token
GET  /auth/me       -> 200 with Bearer token
GET  /health        -> 200 {"status":"ok"}
```

- [ ] **Step 6: Commit docs and push**

```powershell
git add README.md
git commit -m "docs: add authentication setup instructions"
git push
```

- [ ] **Step 7: Final branch comparison**

```powershell
git status
git log --oneline --decorate -8
```

Expected: clean working tree on `feature/auth`, ready for PR review against `main`.
