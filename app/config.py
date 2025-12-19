# backend/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Outbound Email Verifier"
    JWT_SECRET: str = "supersecret"
    JWT_ALGORITHM: str = "HS256"

    #DATABASE_URL: str = "postgresql+asyncpg://localhost:123@localhost:5432/db"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:123@localhost:5432/db"



    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

