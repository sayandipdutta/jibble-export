from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jibble_client_id: str = ""
    jibble_client_secret: str = ""
    environment: str = "prod"
    model_config = SettingsConfigDict(env_file=".env")


setting = Settings()
