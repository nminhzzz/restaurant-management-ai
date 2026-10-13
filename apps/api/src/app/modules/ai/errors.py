"""Signals the assistant pipeline raises to the orchestrator (FR-AI-06, NFR-16)."""


class ClarificationNeeded(Exception):
    """The model judged the question out of scope or too vague and asked for detail."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class QuotaExceeded(Exception):
    """The daily question quota is spent (NFR-16)."""

    def __init__(self, message: str = "Đã đạt hạn mức câu hỏi trong ngày.") -> None:
        super().__init__(message)
        self.message = message


class ExecutionFailed(Exception):
    """The database rejected the validated query and no generation attempt is left."""

    def __init__(self, sql: str) -> None:
        super().__init__("database rejected the generated query")
        self.sql = sql
