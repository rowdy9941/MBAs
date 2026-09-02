from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mbas_env: str = "development"
    mbas_log_level: str = "INFO"
    mbas_cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql://mbas:mbas@postgres:5432/mbas"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.mbas_cors_origins.split(",") if origin.strip()]


settings = Settings()
