from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str
    storage_secret: str
    access_token_expire_minutes: int = 60
    admin_emails: str = ""
    government_email_domains: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()