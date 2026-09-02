from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mbas_env: str = "development"
    mbas_log_level: str = "INFO"
    mbas_cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql://mbas:mbas@postgres:5432/mbas"


settings = Settings()

