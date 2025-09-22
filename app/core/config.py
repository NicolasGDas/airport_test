from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./airports.db"
    APP_ENV: str = "local"
    LOG_LEVEL: str = "INFO"

settings = Settings()
