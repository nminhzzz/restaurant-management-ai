"""Structured assistant answers.

The interpreter asks the model for JSON; this module turns whatever comes back into a
bounded `StructuredAnswer`, and converts it to and from the plain text stored in
`TRUY_VAN_AI.KetQuaTomTat`. Nothing here trusts the model's output shape.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any

SCOPE_PREFIX = "Phạm vi dữ liệu:"
MAX_HEADLINE = 300
MAX_HIGHLIGHT = 300
MAX_HIGHLIGHTS = 4
MAX_FOLLOW_UP = 200
MAX_FOLLOW_UPS = 3

_FENCE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")


@dataclass(frozen=True)
class StructuredAnswer:
    headline: str
    highlights: list[str] = field(default_factory=list)
    follow_ups: list[str] = field(default_factory=list)


def _clip(value: str, limit: int) -> str:
    text = " ".join(value.split())
    return text if len(text) <= limit else text[:limit]


def _strings(value: Any, limit: int, cap: int) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        text = _clip(item, limit)
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) == cap:
            break
    return out


def parse_model_answer(raw: str) -> StructuredAnswer:
    text = _FENCE.sub("", raw.strip()).strip()
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if isinstance(data, dict) and isinstance(data.get("headline"), str):
        headline = _clip(data["headline"], MAX_HEADLINE)
        if headline:
            return StructuredAnswer(
                headline=headline,
                highlights=_strings(data.get("highlights"), MAX_HIGHLIGHT, MAX_HIGHLIGHTS),
                follow_ups=_strings(data.get("follow_ups"), MAX_FOLLOW_UP, MAX_FOLLOW_UPS),
            )
    return StructuredAnswer(headline=raw.strip())


def compose_answer(answer: StructuredAnswer, scope_note: str) -> str:
    lines = [answer.headline, *(f"- {point}" for point in answer.highlights)]
    return "\n".join(lines) + f"\n\n{scope_note}"


def split_answer(text: str) -> tuple[str, list[str]]:
    paragraphs = text.strip().split("\n\n")
    if len(paragraphs) > 1 and paragraphs[-1].startswith(SCOPE_PREFIX):
        paragraphs = paragraphs[:-1]
    body = "\n\n".join(paragraphs).strip()
    lines = body.split("\n")
    bullets = [line[2:].strip() for line in lines if line.startswith("- ")]
    if not bullets:
        return body, []
    head = " ".join(line.strip() for line in lines if not line.startswith("- ")).strip()
    return head, bullets
