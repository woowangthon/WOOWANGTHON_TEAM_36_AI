# WOOWANGTHON_TEAM_36_AI

2026 AI 우왕톤 36팀 장학금 매칭 서비스의 AI 저장소입니다.
장학 공지 텍스트를 받아 Gemini로 자격 조건을 구조화한 `ExtractedCriteria` JSON을 돌려줍니다.
DB가 없고 사용자 정보를 받지 않는 상태 없는 서비스입니다. 학생과의 비교(판정)는 backend의 규칙 엔진이 합니다.

## 실행

[uv](https://docs.astral.sh/uv/)가 필요합니다. Python 3.12는 uv가 알아서 받습니다.

```bash
cp .env.example .env      # GEMINI_API_KEY, AI_SERVICE_TOKEN 입력
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

- `GET /health`: 상태 확인
- `POST /extract`: 헤더 `X-Service-Token: <AI_SERVICE_TOKEN>` 필요. 문서는 http://localhost:8001/docs

```bash
curl -X POST localhost:8001/extract \
  -H "X-Service-Token: change-me" -H "Content-Type: application/json" \
  -d @tests/fixtures/golden/_example.input.json
```

## 테스트 · 린트

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

테스트는 Gemini를 호출하지 않습니다.

## 골든셋 정확도

```bash
uv run python -m eval.run_eval
```

`tests/fixtures/golden/`의 공지와 정답으로 주요 필드 정답률을 계산하고 `eval/results/`에 저장합니다.
목표는 90%입니다. 라벨링 방법은 [골든셋 README](tests/fixtures/golden/README.md)를 보세요.

## 구조

```
app/
  main.py            FastAPI: POST /extract, GET /health
  schemas.py         ExtractRequest, ExtractedCriteria  ★ backend와의 계약 원본
  extractor.py       Gemini 호출, 재시도, 결과 정리
  config.py          환경변수
  prompts/extract_v1.md
eval/                골든셋 채점
tests/
```

## 계약 변경

`app/schemas.py`를 바꾸면 `SCHEMA_VERSION`을 올리고, backend의 `app/schemas/ai_contract.py` 사본을 고치는 PR과 함께 머지합니다.
