# ai 저장소

장학 공지 텍스트 -> `ExtractedCriteria` JSON (Gemini 구조화 출력). DB 없음, 상태 없음.

## 명령
- 실행: `uv run uvicorn app.main:app --reload --port 8001`
- 테스트: `uv run pytest` (Gemini 호출 없음, 가짜 클라이언트 사용)
- 린트: `uv run ruff check . && uv run ruff format --check .`
- 정확도: `uv run python -m eval.run_eval` (실제 Gemini 호출, GEMINI_API_KEY 필요)

## 규칙
- `app/schemas.py`가 backend와의 계약 원본. 바꾸면 `SCHEMA_VERSION`을 올리고 backend 사본도 같이 고친다.
- 사용자 정보는 이 서비스에 절대 들어오지 않는다. 요청은 공지 텍스트만.
- LLM은 공지 내용을 옮기기만 한다. 날짜 형식 검증, 학년 범위 정리 같은 결정론적 처리는 `extractor.postprocess`에서 코드로.
- `null` = 조건 없음, `ambiguous_fields` = 조건은 있는데 값이 모호함. 이 구분을 깨지 않는다.
- 프롬프트를 바꾸면 새 파일(`extract_v2.md`)로 만들고 `PROMPT_VERSION`을 올린 뒤 골든셋으로 재측정한다.
- 모델 이름은 코드에 쓰지 않고 `GEMINI_MODEL` 환경변수로만.
