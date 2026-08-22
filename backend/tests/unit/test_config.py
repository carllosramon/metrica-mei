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