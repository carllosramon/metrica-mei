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

def test_allowed_origins_ignores_spacing_and_trailing_slash(
    monkeypatch,
):
    # A barra final é o engano de quem copia o endereço da barra do
    # navegador. O CORS compara a origem como texto exato, então
    # "https://app.metricamei.com/" nunca casaria, e a falha chega ao
    # desenvolvedor como requisição bloqueada, sem motivo declarado.
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://app.metricamei.com/, http://localhost:5173 ,,",
    )
    get_settings.cache_clear()

    assert get_settings().allowed_origins() == [
        "https://app.metricamei.com",
        "http://localhost:5173",
    ]

    get_settings.cache_clear()
