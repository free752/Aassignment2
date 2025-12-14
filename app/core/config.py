from functools import lru_cache
from pydantic_settings import BaseSettings  # ← 이게 정확한 모듈 이름

class Settings(BaseSettings):
    PROJECT_NAME: str = "Assignment2 API"
    VERSION: str = "0.1.0"

    DATABASE_URL: str          # .env에 반드시 있어야 함
    JWT_SECRET: str            # 이것도 .env 필수
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ENV: str = "local"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()