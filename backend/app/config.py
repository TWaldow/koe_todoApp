from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings): #liest die .env-Datei und 

    model_config = SettingsConfigDict(env_files=".env", extra="ignore")
    database_url: str
    api_token: str
    anthropic_api_key: str = ""


env = EnvSettings