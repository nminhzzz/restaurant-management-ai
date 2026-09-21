"""Step 2 — Prompt construction (schema block + few-shot examples).

To implement: read column metadata for the role's view from
`information_schema.columns` and render it together with the curated few-shot
examples. The schema block is built from the role's view only, never from the
core tables (FR-AI-05).
"""

from collections.abc import Sequence

from app.shared.roles import Role


def schema_block(role: Role) -> str:
    """Schema description shown to the model for this role."""
    raise NotImplementedError


def build_prompt(question: str, role: Role, examples: Sequence[object]) -> str:
    """Full prompt: instructions, schema block, few-shot examples, question."""
    raise NotImplementedError
