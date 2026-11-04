"""공지 텍스트 -> ExtractedCriteria.

LLM은 공지 내용을 옮기기만 하고, 형식 검증과 정리는 이 파일의 코드가 합니다.
"""

import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Protocol

from google import genai
from google.genai import errors, types

from app.config import Settings
from app.schemas import SCHEMA_VERSION, ExtractedCriteria, ExtractRequest, ExtractResponse

logger = logging.getLogger(__name__)

PROMPT_VERSION = "extract_v1"
PROMPT_PATH = Path(__file__).parent / "prompts" / f"{PROMPT_VERSION}.md"

_DATE_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%d")
_RETRYABLE_CODES = {429, 500, 503}


class Extractor(Protocol):
    def extract(self, req: ExtractRequest) -> ExtractResponse: ...


class ExtractionError(Exception):
    """재시도 후에도 추출에 실패함.

    backend는 extract_status = FAILED로 남기고 다음 주기에 재시도합니다.
    """


def build_prompt(req: ExtractRequest, text: str) -> str:
    # 공지 본문에 중괄호가 들어 있을 수 있어 str.format 대신 replace를 씁니다
    template = PROMPT_PATH.read_text(encoding="utf-8")
    values = {
        "source_code": req.source_code,
        "posted_at": req.posted_at,
        "title": req.title,
        "text": text,
    }
    for key, value in values.items():
        template = template.replace("{" + key + "}", value)
    return template


def _normalize_date(value: str | None) -> tuple[str | None, bool]:
    """(정규화된 값, 유효 여부). 형식이 틀리면 None과 False."""
    if value is None:
        return None, True
    value = re.sub(r"\s+", " ", value.strip())
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime(fmt), True
        except ValueError:
            continue
    return None, False


def postprocess(criteria: ExtractedCriteria) -> ExtractedCriteria:
    if criteria.notice_kind in ("결과", "기타"):
        return criteria.model_copy(update={"scholarships": []})

    cleaned = []
    for s in criteria.scholarships:
        ambiguous = list(s.ambiguous_fields)
        updates: dict = {}
        for field in ("apply_start", "apply_end"):
            value, ok = _normalize_date(getattr(s, field))
            updates[field] = value
            if not ok:
                ambiguous.append(field)
        if s.target_grades is not None:
            updates["target_grades"] = sorted({g for g in s.target_grades if 1 <= g <= 4}) or None
        updates["ambiguous_fields"] = list(dict.fromkeys(ambiguous))
        cleaned.append(s.model_copy(update=updates))
    return criteria.model_copy(update={"scholarships": cleaned})


class GeminiExtractor:
    def __init__(self, settings: Settings, client: genai.Client | None = None):
        self.settings = settings
        self.client = client or genai.Client(api_key=settings.gemini_api_key)

    @property
    def model_version(self) -> str:
        return f"{self.settings.gemini_model}/{PROMPT_VERSION}/{SCHEMA_VERSION}"

    def extract(self, req: ExtractRequest) -> ExtractResponse:
        text = req.text
        truncated = len(text) > self.settings.max_input_chars
        if truncated:
            text = text[: self.settings.max_input_chars]

        raw = self._generate(build_prompt(req, text))
        try:
            criteria = ExtractedCriteria.model_validate_json(raw)
        except ValueError as e:
            raise ExtractionError(f"schema validation failed: {e}") from e

        return ExtractResponse(
            criteria=postprocess(criteria),
            model_version=self.model_version,
            truncated=truncated,
        )

    def _generate(self, prompt: str) -> str:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=ExtractedCriteria.model_json_schema(),
            temperature=0,
        )
        attempt = 0
        while True:
            try:
                response = self.client.models.generate_content(
                    model=self.settings.gemini_model, contents=prompt, config=config
                )
                if not response.text:
                    raise ExtractionError("empty response")
                return response.text
            except errors.APIError as e:
                if e.code not in _RETRYABLE_CODES or attempt >= self.settings.max_retries:
                    raise ExtractionError(f"gemini error {e.code}") from e
                delay = self.settings.retry_base_seconds * (2**attempt)
                logger.warning("gemini %s, retry %d in %.1fs", e.code, attempt + 1, delay)
                time.sleep(delay)
                attempt += 1
