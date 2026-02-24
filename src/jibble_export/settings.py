from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="JIBBLE_")
    client_id: str = ""
    client_secret: str = ""
    environment: str = "prod"
    reports_dir: Path = Path("./reports")


setting = Settings()
