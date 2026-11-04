from app.schemas import ExtractedCriteria
from eval.scoring import score_sample, summarize


def test_perfect_match(example_expected):
    s = score_sample("x", example_expected, example_expected)
    assert s.count_match
    assert s.correct == s.total == 6


def test_field_mismatch_counted(example_expected):
    wrong = example_expected.scholarships[0].model_copy(update={"min_gpa": 3.0})
    actual = example_expected.model_copy(update={"scholarships": [wrong]})
    s = score_sample("x", example_expected, actual)
    assert (s.correct, s.total) == (5, 6)
    assert s.per_field["min_gpa"] == (0, 1)


def test_missing_scholarship_scores_zero_for_its_fields(example_expected):
    actual = ExtractedCriteria(notice_kind="모집", scholarships=[])
    s = score_sample("x", example_expected, actual)
    assert not s.count_match
    assert (s.correct, s.total) == (1, 6)


def test_summarize(example_expected):
    s = score_sample("x", example_expected, example_expected)
    summary = summarize([s])
    assert summary["accuracy"] == 1.0
    assert summary["per_field"]["min_gpa"] == 1.0
