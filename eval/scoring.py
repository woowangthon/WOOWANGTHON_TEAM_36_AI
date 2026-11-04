"""골든셋 채점 (계획서 10장).

장학금 개수가 정답과 같은지 먼저 보고, 장학금마다 주요 필드를 완전 일치로 채점합니다.
정답률 = 맞은 필드 수 / 전체 필드 수. 장학금은 공지에 나온 순서대로 짝짓고,
예측이 모자라면 빠진 장학금의 필드는 모두 오답, 남으면 무시합니다.
"""

from dataclasses import dataclass, field

from app.schemas import ExtractedCriteria

SCHOLARSHIP_FIELDS = (
    "apply_end",
    "min_gpa",
    "target_grades",
    "max_income_bracket",
    "target_department",
)


@dataclass
class SampleScore:
    sample_id: str
    count_match: bool
    correct: int = 0
    total: int = 0
    per_field: dict[str, tuple[int, int]] = field(default_factory=dict)  # field -> (correct, total)
    mismatches: list[str] = field(default_factory=list)


def _same(field_name: str, expected, actual) -> bool:
    if field_name == "target_grades" and expected is not None and actual is not None:
        return sorted(expected) == sorted(actual)
    return expected == actual


def _tally(score: SampleScore, name: str, ok: bool, note: str) -> None:
    c, t = score.per_field.get(name, (0, 0))
    score.per_field[name] = (c + ok, t + 1)
    score.correct += ok
    score.total += 1
    if not ok:
        score.mismatches.append(note)


def score_sample(
    sample_id: str, expected: ExtractedCriteria, actual: ExtractedCriteria
) -> SampleScore:
    score = SampleScore(
        sample_id=sample_id,
        count_match=len(expected.scholarships) == len(actual.scholarships),
    )
    _tally(
        score,
        "notice_kind",
        expected.notice_kind == actual.notice_kind,
        f"notice_kind: expected {expected.notice_kind!r}, got {actual.notice_kind!r}",
    )
    for i, exp in enumerate(expected.scholarships):
        act = actual.scholarships[i] if i < len(actual.scholarships) else None
        for name in SCHOLARSHIP_FIELDS:
            e = getattr(exp, name)
            a = getattr(act, name) if act else None
            ok = act is not None and _same(name, e, a)
            label = act.scholarship_name if act else "(missing)"
            _tally(score, name, ok, f"[{i}] {label} {name}: expected {e!r}, got {a!r}")
    return score


def summarize(scores: list[SampleScore]) -> dict:
    per_field: dict[str, list[int]] = {}
    for s in scores:
        for name, (c, t) in s.per_field.items():
            acc = per_field.setdefault(name, [0, 0])
            acc[0] += c
            acc[1] += t
    correct = sum(s.correct for s in scores)
    total = sum(s.total for s in scores)
    return {
        "samples": len(scores),
        "count_match_rate": sum(s.count_match for s in scores) / len(scores) if scores else 0.0,
        "accuracy": correct / total if total else 0.0,
        "per_field": {k: c / t for k, (c, t) in per_field.items()},
    }
