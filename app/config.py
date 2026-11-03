from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    ai_service_token: str = ""

    # 계획서 3장: 입력 텍스트는 3만 자에서 자르고, 429는 최대 3회 재시도
    max_input_chars: int = 30_000
    max_retries: int = 3
    retry_base_seconds: float = 2.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
