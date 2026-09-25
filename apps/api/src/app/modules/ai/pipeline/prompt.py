"""Step 2 — prompt construction (FR-AI-05, FR-AI-06).

The prompt is the innermost of the three isolation layers (the view, the `GRANT`, and
this text): the model infers table names from whatever the prompt says, so it is told
about exactly one view and never about the core tables or another role's view.
"""

import json
from collections.abc import Sequence
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import REPO_ROOT
from app.modules.ai.scope import ROLE_VIEWS
from app.shared.roles import Role

_EXAMPLES_PATH = REPO_ROOT / "data" / "eval" / "questions.example.jsonl"

ROLE_SCOPE_NOTE: dict[Role, str] = {
    Role.MANAGER: "toàn bộ dữ liệu kinh doanh: đơn hàng, hóa đơn, thanh toán và tồn kho",
    Role.CASHIER: "đơn hàng, hóa đơn và thanh toán; không có giá nhập, giá vốn hay lợi nhuận",
    Role.WAREHOUSE: "tồn kho và nguyên liệu; không có doanh thu, hóa đơn hay lợi nhuận",
}

COLUMN_NOTES: dict[str, str] = {
    "BusinessDate": "ngày kinh doanh, mốc 06:00 → 06:00 hôm sau",
    "MaOrder": "mã đơn hàng",
    "MaHoaDon": "mã hóa đơn",
    "TongTien": "tổng tiền của hóa đơn",
    "SoTien": "số tiền của giao dịch thanh toán",
    "ThoiDiemXuat": "thời điểm xuất hóa đơn",
    "MaNguyenLieu": "mã nguyên liệu",
    "TenNguyenLieu": "tên nguyên liệu",
    "DonViTinh": "đơn vị tính",
    "SoLuongTon": "số lượng tồn hiện tại",
    "MucTonToiThieu": "mức tồn tối thiểu để cảnh báo",
}


async def _columns_of(session: AsyncSession, view: str) -> list[tuple[str, str]]:
    """Column name and type of the view, through the dialect-agnostic inspector.

    Reflection goes through the session's **own** connection: the inspector rolls back
    a connection it obtained from the engine itself, which (with a single-connection
    pool) would discard work the caller had already flushed.
    """

    def _read(sync_session: Any) -> list[tuple[str, str]]:
        inspector = inspect(sync_session.connection())
        return [(column["name"], str(column["type"])) for column in inspector.get_columns(view)]

    return await session.run_sync(_read)


async def schema_block(session: AsyncSession, role: Role) -> str:
    """The one view this role may read, column by column."""
    view = ROLE_VIEWS[role]
    lines = [f"View được phép truy vấn: {view}"]
    for name, type_name in await _columns_of(session, view):
        note = COLUMN_NOTES.get(name)
        lines.append(f"- {name} ({type_name})" + (f": {note}" if note else ""))
    return "\n".join(lines)


def _load_examples(role: Role) -> list[dict[str, Any]]:
    if not _EXAMPLES_PATH.is_file():
        return []
    view = ROLE_VIEWS[role]
    examples: list[dict[str, Any]] = []
    for line in _EXAMPLES_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("view") == view or item.get("role") == role.value:
            examples.append(item)
    return examples


async def build_prompt(
    session: AsyncSession,
    question: str,
    role: Role,
    examples: Sequence[object] | None = None,
) -> str:
    """Instructions + the role's schema + few-shot examples + the question."""
    view = ROLE_VIEWS[role]
    shots = list(examples) if examples is not None else _load_examples(role)

    parts = [
        "Bạn là trợ lý dữ liệu của một nhà hàng, trả lời bằng tiếng Việt.",
        f"Bạn chỉ được truy vấn đúng một view: {view}.",
        "Không được dùng bảng lõi, cũng không được dùng view của vai trò khác.",
        "Chỉ sinh đúng một câu lệnh SELECT, không kèm giải thích hay định dạng thừa.",
        f"Phạm vi dữ liệu của vai trò này: {ROLE_SCOPE_NOTE[role]}.",
        "Nếu câu hỏi nằm ngoài phạm vi hoặc còn thiếu thông tin, hãy trả lời bắt đầu bằng "
        "'CLARIFY:' kèm một câu hỏi làm rõ thay vì đoán.",
        "",
        await schema_block(session, role),
    ]

    if shots:
        parts += ["", "Ví dụ:"]
        for example in shots:
            if isinstance(example, dict):
                asked = example.get("question", "")
                sql = example.get("sql", "")
            else:
                asked = getattr(example, "question", "")
                sql = getattr(example, "sql", "")
            parts.append(f"- Hỏi: {asked}\n  SQL: {sql}")

    parts += ["", f"Câu hỏi: {question}", "SQL:"]
    return "\n".join(parts)
