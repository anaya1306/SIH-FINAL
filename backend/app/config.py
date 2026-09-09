from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "legal-metrology-api"
    database_url: str | None = None
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    jwt_secret: str = "packscan-dev-secret"
    ocr_api_url: str = "http://localhost:8000"
    ocr_api_key: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
