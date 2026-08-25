from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/metrica_mei.db"
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 30
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    def allowed_origins(self) -> list[str]:
        # A lista chega como texto separado por vírgula porque é
        # assim que ela cabe em uma variável de ambiente, tanto no
        # .env local quanto na hospedagem.
        origins = []

        for origin in self.cors_origins.split(","):
            normalized = origin.strip()

            if normalized:
                origins.append(normalized)

        return origins

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()