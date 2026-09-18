from time import perf_counter

import pytest

from app.security.jwt import TokenService
from app.security.password import PasswordService
from app.services.auth_service import AuthService, InvalidCredentialsError
from tests.dubles.in_memory_user_repository import InMemoryUserRepository


def make_service():
    repository = InMemoryUserRepository()
    service = AuthService(
        repository,
        PasswordService(),
        TokenService(
            "test-secret-key-with-at-least-32-bytes",
            "HS256",
            30,
        ),
    )

    service.register(
        "Carlos",
        "carlos@email.com",
        "minhasenha",
    )

    return service


def test_login_returns_token_for_valid_credentials():
    token = make_service().login(
        "CARLOS@EMAIL.COM",
        "minhasenha",
    )

    assert isinstance(token, str)
    assert token


def test_login_rejects_wrong_password():
    with pytest.raises(InvalidCredentialsError):
        make_service().login(
            "carlos@email.com",
            "senhaerrada",
        )


def test_login_rejects_unknown_email():
    with pytest.raises(InvalidCredentialsError):
        make_service().login(
            "ninguem@email.com",
            "minhasenha",
        )


def test_email_inexistente_custa_o_mesmo_que_senha_errada():
    service = make_service()

    tempos = {}

    for rotulo, email in (
        ("existe", "carlos@email.com"),
        ("nao_existe", "ninguem@email.com"),
    ):
        inicio = perf_counter()

        with pytest.raises(InvalidCredentialsError):
            service.login(email, "senha-errada")

        tempos[rotulo] = perf_counter() - inicio

    # O texto e o status das duas respostas são iguais de propósito. Sem
    # gastar o Argon2 no caminho do e-mail inexistente, ele saía em cerca
    # de 1 ms contra dezenas de milissegundos do outro, e o relógio
    # entregava quem tem conta. A margem é larga porque medir tempo em
    # máquina compartilhada oscila; a diferença que se quer barrar era de
    # duas ordens de grandeza.
    assert tempos["nao_existe"] > tempos["existe"] / 5
