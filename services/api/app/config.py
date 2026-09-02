from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mbas_env: str = "development"
    mbas_log_level: str = "INFO"
    mbas_cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql://mbas:mbas@postgres:5432/mbas"
    auth_secret: str = "development-only-change-me"
    whatsapp_verify_token: str = "development-verify-token"
    whatsapp_app_secret: str = "development-app-secret"
    sarvam_api_key: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    livekit_url: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.mbas_cors_origins.split(",") if origin.strip()]


settings = Settings()
