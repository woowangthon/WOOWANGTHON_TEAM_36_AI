import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.extractor import ExtractionError
from app.main import app, get_extractor
from app.schemas import ExtractResponse

TOKEN = "test-token"


class FakeExtractor:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def extract(self, req):
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def client():
    app.dependency_overrides[get_settings] = lambda: Settings(ai_service_token=TOKEN)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("headers", [{}, {"X-Service-Token": "wrong"}])
def test_extract_requires_token(client, example_request, headers):
    res = client.post("/extract", json=example_request.model_dump(), headers=headers)
    assert res.status_code == 401


def test_extract_returns_criteria(client, example_request, example_expected):
    result = ExtractResponse(criteria=example_expected, model_version="fake", truncated=False)
    app.dependency_overrides[get_extractor] = lambda: FakeExtractor(result=result)
    res = client.post(
        "/extract", json=example_request.model_dump(), headers={"X-Service-Token": TOKEN}
    )
    assert res.status_code == 200
    assert res.json()["criteria"]["scholarships"][0]["min_gpa"] == 3.5


def test_extract_failure_is_502(client, example_request):
    app.dependency_overrides[get_extractor] = lambda: FakeExtractor(
        error=ExtractionError("gemini error 429")
    )
    res = client.post(
        "/extract", json=example_request.model_dump(), headers={"X-Service-Token": TOKEN}
    )
    assert res.status_code == 502
