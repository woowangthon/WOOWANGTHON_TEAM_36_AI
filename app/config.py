from functools import lru_cache # 함수 결과를 기억해 두는 도구

from pydantic_settings import BaseSettings, SettingsConfigDict # .env 파일에서 설정값을 자동으로 읽어주는 라이브러리


class Settings(BaseSettings): # BaseSettings를 상속하면, 클래스에 적은 변수 이름과 같은 값을 환경변수나 .env 파일에서 찾아 채워줌
    model_config = SettingsConfigDict(env_file=".env", extra="ignore") # 실행위치의 .env 파일 읽기, Settings 클래스에 변수로 선언되지 않은 값은 무시 

    gemini_api_key: str = ""  # Gemini API 키
    gemini_model: str = "gemini-3.5-flash" # 사용할 Gemini 모델
    ai_service_token: str = "" # backend만 이 서비스를 호출할 수 있게 하는 비밀번호

    # 계획서 3장: 입력 텍스트는 3만 자에서 자르고, 429는 최대 3회 재시도
    max_input_chars: int = 30_000 
    max_retries: int = 3
    retry_base_seconds: float = 2.0 


@lru_cache
def get_settings() -> Settings: # get_settings() 를 불러 설정 가져감
    return Settings()
