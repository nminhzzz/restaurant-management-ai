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
from app.core.errors import BusinessRuleError
from app.modules.ai.guard import validate_sql
from app.modules.ai.scope import views_for
from app.shared import business_date
from app.shared.roles import Role

_EXAMPLES_PATH = REPO_ROOT / "data" / "eval" / "questions.example.jsonl"

ROLE_SCOPE_NOTE: dict[Role, str] = {
    Role.MANAGER: "toàn bộ dữ liệu kinh doanh: đơn hàng, hóa đơn, thanh toán và tồn kho",
    Role.CASHIER: "đơn hàng, hóa đơn và thanh toán; không có giá nhập, giá vốn hay lợi nhuận",
    Role.WAREHOUSE: "tồn kho và nguyên liệu; không có doanh thu, hóa đơn hay lợi nhuận",
}

# The exact LoaiBanGhi branch values of each view (must match db/views/*.sql), so the
# model is told what to filter on instead of guessing or asking a clarifying question.
VIEW_LOAIBANGHI_VALUES: dict[str, tuple[str, ...]] = {
    "vw_ai_quanly": (
        "ORDER",
        "DONG_MON",
        "HOA_DON",
        "THANH_TOAN",
        "TON_KHO",
        "GIA_VON_THANG",
        "GIAO_DICH_KHO",
        "PHIEU_NHAP",
    ),
    "vw_ai_thungan": ("ORDER", "DONG_MON", "HOA_DON", "THANH_TOAN"),
    "vw_ai_kho": ("TON_KHO", "GIAO_DICH_KHO", "LO_NGUYEN_LIEU"),
}

COLUMN_NOTES: dict[str, str] = {
    "LoaiBanGhi": (
        "loại bản ghi của dòng này — luôn lọc bằng WHERE LoaiBanGhi = '...' trước, "
        "vì các cột khác chỉ có dữ liệu ở đúng nhánh của nó"
    ),
    "BusinessDate": "ngày kinh doanh theo lịch mốc giờ hiệu lực của hệ thống",
    "MaOrder": "mã đơn hàng; có ở các nhánh ORDER, DONG_MON, HOA_DON và THANH_TOAN",
    "TrangThaiOrder": (
        "trạng thái order: Đang mở, Chờ xác nhận, Chờ xác minh thanh toán, Chờ đối soát, "
        "Tranh chấp, Đã thanh toán, Đã hủy, Tự động đóng, Đóng \u2013 chưa thu được tiền"
    ),
    "LyDoHuyOrder": "lý do hủy order, chỉ có ở LoaiBanGhi = 'ORDER'",
    "MaHoaDon": (
        "mã hóa đơn, chỉ có ở LoaiBanGhi = 'HOA_DON'; mỗi hóa đơn chỉ phát hành sau khi "
        "thanh toán thành công"
    ),
    "TongTien": "tổng tiền của hóa đơn, chỉ có ở LoaiBanGhi = 'HOA_DON'",
    "MaGiaoDich": "mã giao dịch thanh toán, chỉ có ở LoaiBanGhi = 'THANH_TOAN'",
    "PhuongThuc": "hình thức thanh toán (Tiền mặt/QR), chỉ có ở LoaiBanGhi = 'THANH_TOAN'",
    "SoTien": ("số tiền của giao dịch thanh toán thành công, chỉ có ở LoaiBanGhi = 'THANH_TOAN'"),
    "ThoiDiemXuat": "thời điểm xuất hóa đơn",
    "TenMon": "tên món ăn, ở LoaiBanGhi = 'DONG_MON'",
    "TenNhom": "tên nhóm món",
    "SoLuongMon": "số lượng món trong dòng order",
    "DonGiaMon": "đơn giá bán của món tại thời điểm order",
    "ThanhTienMon": (
        "thành tiền của dòng món = SoLuongMon * DonGiaMon; dòng món đã hủy không có trong view"
    ),
    "MaNguyenLieu": "mã nguyên liệu",
    "TenNguyenLieu": "tên nguyên liệu",
    "DonViTinh": "đơn vị tính",
    "SoLuongTon": "số lượng tồn hiện tại, chỉ có ở LoaiBanGhi = 'TON_KHO'",
    "SoLuongGiu": "lượng nguyên liệu đang được giữ cho các lượt chọn còn hiệu lực",
    "SoLuongKhaDung": (
        "lượng còn dùng được sau khi trừ giữ chỗ, dùng để trả lời số suất còn phục vụ"
    ),
    "MucTonToiThieu": "mức tồn tối thiểu hiệu lực để cảnh báo",
    "CanhBaoTonThap": "1 nếu tồn hiện tại dưới mức tối thiểu, ngược lại 0",
    "Thang": (
        "tháng của giá vốn bình quân, định dạng YYYYMM (ví dụ 202609, không phải 1-12), "
        "ở LoaiBanGhi = 'GIA_VON_THANG'"
    ),
    "GiaBinhQuanThang": "giá vốn bình quân gia quyền trong tháng của nguyên liệu",
    "TongSoLuongNhapThang": "tổng số lượng nhập trong tháng dùng để tính giá bình quân",
    "MaGiaoDichKho": "mã giao dịch kho",
    "SoLuong": "số lượng của giao dịch kho (nhập/xuất/trừ tự động/điều chỉnh)",
    "LoaiGiaoDich": (
        "loại giao dịch kho: Nhập, Trừ tự động, Hoàn kho, Xuất thủ công, Điều chỉnh kiểm kê"
    ),
    "MaPhieuNhap": "mã phiếu nhập kho, ở LoaiBanGhi = 'PHIEU_NHAP'",
    "TenNhaCungCap": "tên nhà cung cấp của phiếu nhập",
    "DonGiaNhap": "đơn giá nhập (giá mua) của nguyên liệu trong phiếu nhập chưa hủy",
    "SoLuongNhap": "số lượng nhập trong dòng phiếu nhập",
    "MaLo": "mã lô nguyên liệu, ở LoaiBanGhi = 'LO_NGUYEN_LIEU'",
    "SoLuongConLai": "số lượng còn lại của lô",
    "TrangThaiLo": "trạng thái lô (Còn hạn, Hết hạn, ...)",
    "NgayNhapLo": "ngày nhập của lô",
    "HanSuDungLo": "hạn sử dụng tính từ ngày nhập lô + số ngày bảo quản",
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
    lines = [
        "Chỉ các view theo chủ đề sau được phép truy vấn.",
        "Mỗi view có một mức chi tiết riêng. Tổng hợp từng quan hệ một-nhiều theo khóa "
        "trước khi JOIN để tránh nhân doanh thu/số lượng.",
        "View *_suat chỉ có số suất khả dụng đã tính tại ThoiDiemTinh; dùng view này "
        "để hỏi món còn phục vụ, không suy ngược công thức.",
    ]
    for view in sorted(views_for(role)):
        lines.append(f"View được phép truy vấn: {view}")
        for name, type_name in await _columns_of(session, view):
            note = COLUMN_NOTES.get(name)
            if name == "LoaiBanGhi":
                note = "loại bản ghi cố định của chủ đề này"
            lines.append(f"- {name} ({type_name})" + (f": {note}" if note else ""))
    return "\n".join(lines)


def _load_examples(role: Role) -> list[dict[str, Any]]:
    if not _EXAMPLES_PATH.is_file():
        return []
    examples: list[dict[str, Any]] = []
    for line in _EXAMPLES_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("view") in views_for(role) or item.get("role") == role.value:
            try:
                validate_sql(str(item.get("sql", "")), allowed_views=views_for(role), max_rows=500)
            except BusinessRuleError:
                continue
            examples.append(item)
    return examples


async def build_prompt(
    session: AsyncSession,
    question: str,
    role: Role,
    examples: Sequence[object] | None = None,
    history: Sequence[tuple[str, str | None, str | None]] | None = None,
) -> str:
    """Instructions + schema + examples + recent conversation + the question.

    `history` entries are (question, sql, answer summary) from the same session. A
    short follow-up such as "doanh thu thôi" is meaningless without them, which is
    why the assistant used to ask the same clarification over and over.
    """
    shots = list(examples) if examples is not None else _load_examples(role)

    parts = [
        "Bạn là trợ lý dữ liệu của một nhà hàng, trả lời bằng tiếng Việt.",
        f"Bạn chỉ được truy vấn các view theo chủ đề: {', '.join(sorted(views_for(role)))}.",
        "Không được dùng bảng lõi, cũng không được dùng view của vai trò khác.",
        "Chỉ sinh đúng một câu lệnh SELECT, không kèm giải thích hay định dạng thừa.",
        # Without the dialect the model drifts to SQL Server (GETDATE, TOP), which MySQL
        # rejects; this is an instruction, so the schema-only baseline carries it too.
        "Hệ quản trị là MySQL 8.4: chỉ dùng cú pháp MySQL (CURDATE(), NOW(), DATE_SUB, "
        "DATE_FORMAT, LIMIT), không dùng GETDATE, TOP hay cú pháp của hệ quản trị khác.",
        "Ngày kinh doanh nằm ở cột BusinessDate, theo lịch mốc giờ hiệu lực của hệ thống.",
        # CURDATE() is wrong before 06:00: the business day is still yesterday.
        "'Hôm nay' nghĩa là BusinessDate = "
        f"'{business_date.business_date_of(business_date.now()):%Y-%m-%d}'; "
        "hãy dùng đúng hằng ngày này thay vì CURDATE() khi câu hỏi nói hôm nay/hôm qua.",
        f"Phạm vi dữ liệu của vai trò này: {ROLE_SCOPE_NOTE[role]}.",
        "Quy ước khoảng thời gian: 'tháng này' = từ ngày kinh doanh đầu tháng đến hôm nay; "
        "'tháng trước' = trọn tháng dương lịch trước; 'N ngày gần nhất' = N ngày kinh doanh "
        "kết thúc hôm nay; '1 tháng nay' = 30 ngày gần nhất.",
        "Nếu câu hỏi nằm ngoài phạm vi hoặc còn thiếu thông tin, hãy trả lời bắt đầu bằng "
        "'CLARIFY:' kèm một câu hỏi làm rõ thay vì đoán. Chỉ hỏi lại khi thực sự không thể "
        "suy ra từ ngữ cảnh hội thoại bên dưới.",
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
            try:
                validate_sql(str(sql), allowed_views=views_for(role), max_rows=500)
            except BusinessRuleError:
                continue
            parts.append(f"- Hỏi: {asked}\n  SQL: {sql}")

    if history:
        parts += ["", "Ngữ cảnh hội thoại gần nhất:"]
        for previous_question, previous_sql, previous_answer in list(history)[-4:]:
            parts.append(f"- Người dùng: {previous_question}")
            if previous_sql:
                try:
                    validate_sql(previous_sql, allowed_views=views_for(role), max_rows=500)
                except BusinessRuleError:
                    continue
                parts.append(f"  SQL đã dùng: {previous_sql}")
            elif previous_answer:
                parts.append(f"  Trợ lý đã hỏi lại: {previous_answer[:200]}")
        parts.append(
            "Nếu câu hỏi mới là câu nối tiếp (ví dụ 'doanh thu thôi', 'từng ngày trong "
            "tháng'), hãy dùng ngữ cảnh trên để hoàn thiện câu hỏi rồi trả SQL luôn."
        )

    parts += ["", f"Câu hỏi: {question}", "SQL:"]
    return "\n".join(parts)
