from pydantic_settings import BaseSettings
DEFAULT_SECRET = "change_me_to_a_long_random_string"
DEFAULT_FERNET = "wOeucZZWOZBR1jipIzmwSb5O3VNUx6GzbXHPS8XpWks="


class Settings(BaseSettings):
    PROJECT_NAME: str = "VisionCount API"
    DATABASE_URL: str = "postgresql+asyncpg://visioncount:visioncount@localhost:5432/visioncount"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = DEFAULT_SECRET
    FERNET_KEY: str = DEFAULT_FERNET
    SERVICE_KEY: str = ""  # ключ ai-service для /internal/*; пусто — используется SECRET_KEY (как раньше)
    APP_ENV: str = ""
    DEMO_MODE: bool | None = None  # None: демо-данные включены везде, кроме production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:3000"
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        import os
        return self.APP_ENV.lower() == "production" or bool(os.environ.get("RAILWAY_ENVIRONMENT"))

    @property
    def demo_enabled(self) -> bool:
        return (not self.is_production) if self.DEMO_MODE is None else self.DEMO_MODE

    @property
    def service_key(self) -> str:
        return self.SERVICE_KEY or self.SECRET_KEY

    def check_production(self) -> None:
        """В production нельзя стартовать с ключами из репозитория."""
        if not self.is_production:
            return
        bad = []
        if self.SECRET_KEY == DEFAULT_SECRET or len(self.SECRET_KEY) < 32:
            bad.append("SECRET_KEY (не короче 32 символов, не значение по умолчанию)")
        if self.FERNET_KEY == DEFAULT_FERNET:
            bad.append("FERNET_KEY (сгенерируйте: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\")")
        if bad:
            raise RuntimeError("Задайте безопасные значения в окружении: " + "; ".join(bad))


settings = Settings()
