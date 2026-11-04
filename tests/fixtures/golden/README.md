# 골든셋

공지 30건(장학금이 여러 개 실린 공지 포함)과 사람이 직접 만든 정답입니다.

- `<id>.input.json`: `ExtractRequest` 형식 (`source_code`, `title`, `posted_at`, `text`)
- `<id>.expected.json`: `ExtractedCriteria` 형식의 정답
- `<id>`는 `출처_글ID` 로 짓습니다 (예: `sw_1154830`, `aibc_aq74eFJIirVMESsaQS7qtM`, `kosaf_21449`)
- `_`로 시작하는 파일은 형식 예시라 채점에서 빠집니다 (`_example.*`)

## 고르는 기준
- 출처별로 섞기: 학부 게시판, 사업단, 한국장학재단
- 모집 / 기준안내 / 결과 / 기타가 모두 들어가게
- 장학금이 여러 개인 공지, 조건이 첨부 PDF에만 있는 공지, 조건이 모호한 공지를 꼭 포함

## 라벨링 규칙
`app/prompts/extract_v1.md`의 값 규칙을 그대로 따릅니다. 특히 `null`(조건 없음)과
`ambiguous_fields`(조건은 있지만 값이 모호함)를 구분하세요. 채점 필드는
`notice_kind`, `apply_end`, `min_gpa`, `target_grades`, `max_income_bracket`, `target_department`입니다.
