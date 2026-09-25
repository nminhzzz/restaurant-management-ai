"""Fixtures for the benchmark set (Phase 7 Task 3)."""

import json

import pytest

from app.core.config import REPO_ROOT

QUESTIONS_PATH = REPO_ROOT / "data" / "eval" / "questions.jsonl"


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


@pytest.fixture(scope="session")
def questions() -> list[Question]:
    return load_questions()


@pytest.fixture
def one_question(questions: list[Question]) -> Question:
    return questions[0]


@pytest.fixture
def refusal_question(questions: list[Question]) -> Question:
    for question in questions:
        if question.get("notes") and "vượt quyền" in question["notes"]:
            return question
    raise AssertionError("Bộ câu hỏi phải có ít nhất một ca vượt quyền.")
