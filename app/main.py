import hmac
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

from app.config import Settings, get_settings
from app.extractor import ExtractionError, Extractor, GeminiExtractor
from app.schemas import ExtractRequest, ExtractResponse

app = FastAPI(title="woowangthon-ai", version="0.1.0")

_extractor: Extractor | None = None


def get_extractor(settings: Annotated[Settings, Depends(get_settings)]) -> Extractor:
    global _extractor
    if _extractor is None:
        _extractor = GeminiExtractor(settings)
    return _extractor


def verify_token(
    settings: Annotated[Settings, Depends(get_settings)],
    x_service_token: Annotated[str | None, Header()] = None,
) -> None:
    expected = settings.ai_service_token
    if not expected or not x_service_token or not hmac.compare_digest(x_service_token, expected):
        raise HTTPException(status_code=401, detail="invalid service token")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract", dependencies=[Depends(verify_token)])
def extract(
    req: ExtractRequest, extractor: Annotated[Extractor, Depends(get_extractor)]
) -> ExtractResponse:
    # 동기 함수라 FastAPI가 스레드 풀에서 실행합니다
    # (Gemini 호출·재시도 대기 중에도 이벤트 루프를 막지 않음)
    try:
        return extractor.extract(req)
    except ExtractionError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
