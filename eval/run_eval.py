"""골든셋 정확도 측정.

    uv run python -m eval.run_eval              # 전체
    uv run python -m eval.run_eval --only sw_1154830

tests/fixtures/golden/ 의 <id>.input.json (ExtractRequest) 과 <id>.expected.json
(ExtractedCriteria) 쌍을 읽습니다. 이름이 _ 로 시작하는 파일은 형식 예시라 건너뜁니다.
결과는 eval/results/<시각>.json 에 저장됩니다.
"""

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from app.config import get_settings
from app.extractor import ExtractionError, GeminiExtractor
from app.schemas import ExtractedCriteria, ExtractRequest
from eval.scoring import score_sample, summarize

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / "tests" / "fixtures" / "golden"
RESULTS_DIR = ROOT / "eval" / "results"


def load_samples(only: str | None) -> list[tuple[str, ExtractRequest, ExtractedCriteria]]:
    samples = []
    for input_path in sorted(GOLDEN_DIR.glob("*.input.json")):
        sample_id = input_path.name.removesuffix(".input.json")
        if sample_id.startswith("_") or (only and sample_id != only):
            continue
        expected_path = GOLDEN_DIR / f"{sample_id}.expected.json"
        if not expected_path.exists():
            print(f"skip {sample_id}: expected.json 없음", file=sys.stderr)
            continue
        req = ExtractRequest.model_validate_json(input_path.read_text(encoding="utf-8"))
        expected = ExtractedCriteria.model_validate_json(expected_path.read_text(encoding="utf-8"))
        samples.append((sample_id, req, expected))
    return samples


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="한 샘플만 실행")
    args = parser.parse_args()

    samples = load_samples(args.only)
    if not samples:
        sys.exit(f"샘플이 없습니다: {GOLDEN_DIR}")

    extractor = GeminiExtractor(get_settings())
    scores, details = [], []
    for sample_id, req, expected in samples:
        try:
            actual = extractor.extract(req).criteria
        except ExtractionError as e:
            print(f"{sample_id}: 추출 실패 ({e})")
            actual = ExtractedCriteria(notice_kind="기타", scholarships=[])
        s = score_sample(sample_id, expected, actual)
        scores.append(s)
        details.append({**asdict(s), "actual": actual.model_dump()})
        print(f"{sample_id}: {s.correct}/{s.total}" + ("" if s.count_match else " (개수 불일치)"))
        for m in s.mismatches:
            print(f"    {m}")

    summary = summarize(scores)
    print()
    print(f"정답률 {summary['accuracy']:.1%} · 장학금 개수 일치 {summary['count_match_rate']:.1%}")
    for name, acc in summary["per_field"].items():
        print(f"  {name:<20} {acc:.1%}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{datetime.now():%Y%m%d-%H%M%S}.json"
    out.write_text(
        json.dumps(
            {"model_version": extractor.model_version, "summary": summary, "samples": details},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n저장: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
