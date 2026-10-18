"""Fixtures for the benchmark set (Phase 7 Task 3) and the A/B/C harness (Task 4)."""

import json
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio

from app.core.config import REPO_ROOT

QUESTIONS_PATH = REPO_ROOT / "data" / "eval" / "questions.jsonl"
SAFETY_PATH = REPO_ROOT / "data" / "eval" / "questions.safety.jsonl"
DEV_PATH = REPO_ROOT / "data" / "eval" / "questions.dev.jsonl"


class Question(dict):
    """A record readable both as a mapping and by attribute.

    The question-set tests read `question["sql"]` while the harness reads
    `question.sql`; one small type keeps both spellings honest.
    """

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as exc:  # pragma: no cover - only on a malformed record
            raise AttributeError(name) from exc


def load_questions() -> list[Question]:
    if not QUESTIONS_PATH.is_file():
        raise FileNotFoundError(
            f"Chưa có {QUESTIONS_PATH}. Soạn bộ câu hỏi theo data/eval/README.md "
            "(Phase 7 Task 3 Step 3) trước khi chạy nhóm test này."
        )
    lines = QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()
    return [Question(json.loads(line)) for line in lines if line.strip()]


def load_safety_questions() -> list[Question]:
    if not SAFETY_PATH.is_file():
        raise FileNotFoundError(f"Chưa có bộ ca an toàn {SAFETY_PATH}.")
    lines = SAFETY_PATH.read_text(encoding="utf-8").splitlines()
    return [Question(json.loads(line)) for line in lines if line.strip()]


@pytest.fixture(scope="session")
def questions() -> list[Question]:
    return load_questions()


@pytest.fixture(scope="session")
def safety_questions() -> list[Question]:
    return load_safety_questions()


@pytest.fixture(scope="session")
def dev_questions() -> list[Question]:
    lines = DEV_PATH.read_text(encoding="utf-8").splitlines()
    return [Question(json.loads(line)) for line in lines if line.strip()]


@pytest.fixture
def one_question(questions: list[Question]) -> Question:
    return questions[0]


@pytest.fixture
def refusal_question(safety_questions: list[Question]) -> Question:
    for question in safety_questions:
        if question.get("expect") == "refusal":
            return question
    raise AssertionError("Bộ ca an toàn phải có ít nhất một ca kỳ vọng từ chối.")


@pytest_asyncio.fixture(autouse=True)
async def benchmark_environment(session, seed_views, fake_engine_factory, monkeypatch):
    """Point the harness at the test session and a fake execution layer.

    The harness is a batch driver: it opens its own session and executes queries on
    the role's read-only account. In the suite both seams are replaced, so the
    measurement logic is exercised without a database server or an LLM.
    """
    from data.eval import harness

    fake_engine_factory.columns = ["n"]
    fake_engine_factory.rows = [(1,)]

    @asynccontextmanager
    async def _open():
        yield session

    monkeypatch.setattr(harness, "open_session", _open)
    return fake_engine_factory
