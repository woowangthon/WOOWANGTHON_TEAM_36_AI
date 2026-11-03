from pathlib import Path

import pytest

from app.schemas import ExtractedCriteria, ExtractRequest

GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden"


@pytest.fixture
def example_request() -> ExtractRequest:
    return ExtractRequest.model_validate_json(
        (GOLDEN_DIR / "_example.input.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def example_expected() -> ExtractedCriteria:
    return ExtractedCriteria.model_validate_json(
        (GOLDEN_DIR / "_example.expected.json").read_text(encoding="utf-8")
    )
