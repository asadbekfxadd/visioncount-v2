from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    PROJECT_NAME: str = "VisionCount API"
    DATABASE_URL: str = "postgresql+asyncpg://visioncount:visioncount@localhost:5432/visioncount"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change_me_to_a_long_random_string"
    FERNET_KEY: str = "wOeucZZWOZBR1jipIzmwSb5O3VNUx6GzbXHPS8XpWks="
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:3000"
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
    class Config:
        env_file = ".env"
settings = Settings()
