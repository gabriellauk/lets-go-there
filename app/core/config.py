from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    google_client_id: str
    google_client_secret: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
