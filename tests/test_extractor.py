from types import SimpleNamespace

import pytest
from google.genai import errors

from app.config import Settings
from app.extractor import ExtractionError, GeminiExtractor, build_prompt, postprocess


class FakeModels:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.prompts = []

    def generate_content(self, model, contents, config):
        self.prompts.append(contents)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(text=outcome)


def make_extractor(outcomes, **settings):
    models = FakeModels(outcomes)
    client = SimpleNamespace(models=models)
    # .env 값에 테스트가 흔들리지 않도록 모델 이름을 고정합니다
    s = Settings(retry_base_seconds=0, gemini_model="test-model", **settings)
    return GeminiExtractor(s, client=client), models


def api_error(code):
    return errors.APIError(code, {"error": {"message": "x", "status": "x"}})


def test_build_prompt_keeps_braces_in_text(example_request):
    req = example_request.model_copy(update={"text": "조건 {중괄호} 포함"})
    prompt = build_prompt(req, req.text)
    assert "조건 {중괄호} 포함" in prompt
    assert "{text}" not in prompt
    assert req.title in prompt


def test_extract_parses_and_tags_version(example_request, example_expected):
    extractor, _ = make_extractor([example_expected.model_dump_json()])
    res = extractor.extract(example_request)
    assert res.criteria == example_expected
    assert res.model_version == "test-model/extract_v1/v1"
    assert res.truncated is False


def test_extract_truncates_long_text(example_request, example_expected):
    extractor, models = make_extractor([example_expected.model_dump_json()], max_input_chars=10)
    req = example_request.model_copy(update={"text": "가" * 50})
    res = extractor.extract(req)
    assert res.truncated is True
    assert "가" * 11 not in models.prompts[0]


def test_extract_retries_on_429(example_request, example_expected):
    extractor, models = make_extractor([api_error(429), example_expected.model_dump_json()])
    extractor.extract(example_request)
    assert len(models.prompts) == 2


def test_extract_gives_up_after_max_retries(example_request):
    extractor, models = make_extractor([api_error(429)] * 4, max_retries=3)
    with pytest.raises(ExtractionError):
        extractor.extract(example_request)
    assert len(models.prompts) == 4


def test_extract_does_not_retry_client_errors(example_request):
    extractor, models = make_extractor([api_error(400)])
    with pytest.raises(ExtractionError):
        extractor.extract(example_request)
    assert len(models.prompts) == 1


def test_extract_rejects_invalid_json(example_request):
    extractor, _ = make_extractor(['{"notice_kind": "모집"}'])
    with pytest.raises(ExtractionError):
        extractor.extract(example_request)


def test_postprocess_clears_scholarships_for_result_notice(example_expected):
    criteria = example_expected.model_copy(update={"notice_kind": "결과"})
    assert postprocess(criteria).scholarships == []


def test_postprocess_flags_bad_dates_as_ambiguous(example_expected):
    s = example_expected.scholarships[0].model_copy(
        update={"apply_end": "11월 12일까지", "target_grades": [3, 2, 2, 7]}
    )
    criteria = example_expected.model_copy(update={"scholarships": [s]})
    out = postprocess(criteria).scholarships[0]
    assert out.apply_end is None
    assert "apply_end" in out.ambiguous_fields
    assert out.target_grades == [2, 3]
