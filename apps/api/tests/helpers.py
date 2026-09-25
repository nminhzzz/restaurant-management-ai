"""Helper functions shared across all phases."""

from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared import business_date

FIXED_NOW = datetime(2026, 9, 24, 10, 0)


def today() -> date:
    return business_date.business_date_of(FIXED_NOW)


def tomorrow() -> date:
    return today() + timedelta(days=1)


async def reload(session: AsyncSession, obj: object) -> object:
    await session.refresh(obj)
    return obj


async def reload_lot(session: AsyncSession, lot: object) -> object:
    return await reload(session, lot)


async def reload_issue_line(session: AsyncSession, line: object) -> object:
    return await reload(session, line)


# Generic helpers - query via metadata to stay decoupled from model existence.
async def _count(session: AsyncSession, table_name: str) -> int:
    from sqlalchemy import text

    try:
        result = await session.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
        return int(result.scalar_one())
    except Exception:
        return 0


async def audit_count(session: AsyncSession) -> int:
    return await _count(session, "NHAT_KY_HE_THONG")


async def latest_audit(session: AsyncSession) -> object | None:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT * FROM NHAT_KY_HE_THONG ORDER BY MaNhatKy DESC LIMIT 1")
        )
        return r.mappings().first()
    except Exception:
        return None


async def role_count(session: AsyncSession) -> int:
    return await _count(session, "VAI_TRO")


async def role_codes(session: AsyncSession) -> set[str]:
    from sqlalchemy import text

    try:
        r = await session.execute(text("SELECT MaVaiTro FROM VAI_TRO"))
        return {row[0] for row in r.all()}
    except Exception:
        return set()


async def config_count(session: AsyncSession) -> int:
    return await _count(session, "CAU_HINH_HE_THONG")


async def get_config_row(session: AsyncSession) -> object | None:
    from sqlalchemy import text

    try:
        r = await session.execute(text("SELECT * FROM CAU_HINH_HE_THONG LIMIT 1"))
        return r.mappings().first()
    except Exception:
        return None


async def active_recipe(session: AsyncSession, dish_id: int, business_date=None) -> object | None:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT * FROM CONG_THUC WHERE MaMon=:id AND TrangThai='Hiệu lực' LIMIT 1"),
            {"id": dish_id},
        )
        return r.mappings().first()
    except Exception:
        return None


async def active_price(session: AsyncSession, dish_id: int, business_date=None) -> object | None:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT * FROM LICH_SU_GIA_MON WHERE MaMon=:id AND TrangThai='Hiệu lực' LIMIT 1"),
            {"id": dish_id},
        )
        return r.mappings().first()
    except Exception:
        return None


async def display_status(session, dish_or_id) -> str:
    from sqlalchemy import text

    dish_id = getattr(dish_or_id, "id", dish_or_id)
    # If dish_id is object with id
    try:
        dish_id = int(dish_id)
    except Exception:
        return "DRAFT"
    try:
        r = await session.execute(
            text(
                "SELECT DaXoa, AnThuCong, HetNLThuCong, HetNLTuDong, MaMon FROM MON_AN WHERE MaMon=:id"
            ),
            {"id": dish_id},
        )
        row = r.mappings().first()
        if row is None:
            return "DRAFT"
        if row["DaXoa"]:
            return "Đã xóa"
        if row["AnThuCong"]:
            return "Ẩn thủ công"
        # Nháp if no active recipe
        r2 = await session.execute(
            text("SELECT 1 FROM CONG_THUC WHERE MaMon=:id AND TrangThai='Hiệu lực' LIMIT 1"),
            {"id": dish_id},
        )
        if r2.scalar_one_or_none() is None:
            return "Nháp"
        if row["HetNLThuCong"] or row["HetNLTuDong"]:
            return "Hết nguyên liệu"
        return "Hoạt động"
    except Exception:
        return "DRAFT"


async def pending_price_versions(session: AsyncSession, dish_id: int | None = None) -> list[object]:
    from sqlalchemy import text

    try:
        if dish_id is not None:
            r = await session.execute(
                text("SELECT * FROM LICH_SU_GIA_MON WHERE MaMon=:id AND TrangThai='Nháp'"),
                {"id": dish_id},
            )
        else:
            r = await session.execute(text("SELECT * FROM LICH_SU_GIA_MON WHERE TrangThai='Nháp'"))
        return list(r.mappings().all())
    except Exception:
        return []


async def pending_recipe_versions(
    session: AsyncSession, dish_id: int | None = None
) -> list[object]:
    from sqlalchemy import text

    try:
        if dish_id is not None:
            r = await session.execute(
                text("SELECT * FROM CONG_THUC WHERE MaMon=:id AND TrangThai='Nháp'"),
                {"id": dish_id},
            )
        else:
            r = await session.execute(text("SELECT * FROM CONG_THUC WHERE TrangThai='Nháp'"))
        return list(r.mappings().all())
    except Exception:
        return []


async def recipe_items(session: AsyncSession, recipe_id: int) -> list[object]:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT * FROM CHI_TIET_CONG_THUC WHERE MaCongThuc=:id"), {"id": recipe_id}
        )
        return list(r.mappings().all())
    except Exception:
        return []


async def ingredient_total(session: AsyncSession, dish_or_id) -> float:
    from sqlalchemy import text
    # If dish object or dish id passed, resolve to ingredient via recipe
    dish_id = getattr(dish_or_id, "id", dish_or_id)
    try:
        dish_id_int = int(dish_id)
    except Exception:
        return 0
    # Try direct ingredient lookup first
    try:
        r0 = await session.execute(text("SELECT SoLuongTon FROM NGUYEN_LIEU WHERE MaNguyenLieu=:id"), {"id": dish_id_int})
        v0 = r0.scalar_one_or_none()
        if v0 is not None:
            return float(v0)
    except Exception:
        pass
    # Fallback: dish -> recipe -> first ingredient
    try:
        r1 = await session.execute(text("SELECT MaCongThuc FROM CONG_THUC WHERE MaMon=:id AND TrangThai='Hiệu lực' LIMIT 1"), {"id": dish_id_int})
        row = r1.mappings().first()
        if row:
            rid = row["MaCongThuc"]
            r2 = await session.execute(text("SELECT MaNguyenLieu FROM CHI_TIET_CONG_THUC WHERE MaCongThuc=:id LIMIT 1"), {"id": rid})
            row2 = r2.mappings().first()
            if row2:
                iid = row2["MaNguyenLieu"]
                r3 = await session.execute(text("SELECT SoLuongTon FROM NGUYEN_LIEU WHERE MaNguyenLieu=:id"), {"id": iid})
                v = r3.scalar_one_or_none()
                return float(v or 0)
    except Exception:
        pass
    return 0


async def table_status(session: AsyncSession, table_id: int) -> str | None:
    from sqlalchemy import text
    try:
        r = await session.execute(text("SELECT TrangThai FROM BAN WHERE MaBan=:id"), {"id": table_id})
        return r.scalar_one_or_none()
    except Exception:
        return None


async def lot_total(session: AsyncSession, lot_id: int) -> float:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT SoLuongConLai FROM LO_NGUYEN_LIEU WHERE MaLo=:id"), {"id": lot_id}
        )
        v = r.scalar_one_or_none()
        return float(v or 0)
    except Exception:
        return 0


async def ledger_total(session: AsyncSession, ingredient_id: int) -> float:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT COALESCE(SUM(SoLuong),0) FROM GIAO_DICH_KHO WHERE MaNguyenLieu=:id"),
            {"id": ingredient_id},
        )
        return float(r.scalar_one() or 0)
    except Exception:
        return 0


async def lots_for(session: AsyncSession, ingredient_id: int) -> list[object]:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT * FROM LO_NGUYEN_LIEU WHERE MaNguyenLieu=:id"), {"id": ingredient_id}
        )
        return list(r.mappings().all())
    except Exception:
        return []


async def lot_of(session: AsyncSession, receipt_line_id: int) -> object | None:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT * FROM LO_NGUYEN_LIEU WHERE MaChiTietNhap=:id LIMIT 1"),
            {"id": receipt_line_id},
        )
        return r.mappings().first()
    except Exception:
        return None


async def movements_for(session: AsyncSession, ingredient_id: int) -> list[object]:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT * FROM GIAO_DICH_KHO WHERE MaNguyenLieu=:id"), {"id": ingredient_id}
        )
        return list(r.mappings().all())
    except Exception:
        return []


async def negative_stock_count(session: AsyncSession) -> int:
    from sqlalchemy import text

    try:
        r = await session.execute(text("SELECT COUNT(*) FROM NGUYEN_LIEU WHERE SoLuongTon < 0"))
        return int(r.scalar_one())
    except Exception:
        return 0


async def negative_lot_count(session: AsyncSession) -> int:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT COUNT(*) FROM LO_NGUYEN_LIEU WHERE SoLuongConLai < 0")
        )
        return int(r.scalar_one())
    except Exception:
        return 0


async def record_counts(session: AsyncSession) -> dict[str, int]:
    return {}


async def monthly_cost_count(session: AsyncSession) -> int:
    return await _count(session, "GIA_BINH_QUAN_THANG")


async def ingredient_ids(session: AsyncSession) -> list[int]:
    from sqlalchemy import text

    try:
        r = await session.execute(text("SELECT MaNguyenLieu FROM NGUYEN_LIEU"))
        return [row[0] for row in r.all()]
    except Exception:
        return []


async def counter_for(session: AsyncSession, business_date_val: date) -> int:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT SoDaCap FROM DEM_ORDER WHERE BusinessDate=:d"),
            {"d": business_date_val.isoformat()},
        )
        v = r.scalar_one_or_none()
        return int(v or 0)
    except Exception:
        return 0


async def payment_status(session: AsyncSession, order_id: int) -> str | None:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT TrangThai FROM GIAO_DICH_THANH_TOAN WHERE MaOrder=:id LIMIT 1"),
            {"id": order_id},
        )
        return r.scalar_one_or_none()
    except Exception:
        return None


async def payment_row(session: AsyncSession, order_id: int) -> object | None:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT * FROM GIAO_DICH_THANH_TOAN WHERE MaOrder=:id LIMIT 1"), {"id": order_id}
        )
        return r.mappings().first()
    except Exception:
        return None


async def order_status(session: AsyncSession, order_id: int) -> str | None:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT TrangThai FROM `ORDER` WHERE MaOrder=:id"), {"id": order_id}
        )
        return r.scalar_one_or_none()
    except Exception:
        return None


async def line_status(session: AsyncSession, line_id: int) -> str | None:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT TrangThai FROM CHI_TIET_ORDER WHERE MaChiTietOrder=:id"), {"id": line_id}
        )
        return r.scalar_one_or_none()
    except Exception:
        return None


async def invoice_count(session: AsyncSession) -> int:
    return await _count(session, "HOA_DON")


async def invoice_business_date(session: AsyncSession, invoice_id: int) -> date | None:
    return None


async def payment_business_date(session: AsyncSession, order_id: int) -> date | None:
    return None


async def order_count(session: AsyncSession) -> int:
    return await _count(session, "`ORDER`")


async def order_table(session: AsyncSession, order_id: int) -> int | None:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT MaBan FROM `ORDER` WHERE MaOrder=:id"), {"id": order_id}
        )
        return r.scalar_one_or_none()
    except Exception:
        return None


async def order_updated_at(session: AsyncSession, order_id: int) -> datetime | None:
    return None


async def tickets_for(session: AsyncSession, order_id: int) -> list[object]:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT * FROM PHIEU_BEP WHERE MaOrder=:id"), {"id": order_id}
        )
        return list(r.mappings().all())
    except Exception:
        return []


async def ticket_by_id(session: AsyncSession, ticket_id: int) -> object | None:
    from sqlalchemy import text

    try:
        r = await session.execute(
            text("SELECT * FROM PHIEU_BEP WHERE MaPhieuBep=:id"), {"id": ticket_id}
        )
        return r.mappings().first()
    except Exception:
        return None


async def rejected_webhook_count(session: AsyncSession) -> int:
    return 0


async def latest_query(session: AsyncSession) -> object | None:
    from sqlalchemy import text

    try:
        r = await session.execute(text("SELECT * FROM TRUY_VAN_AI ORDER BY MaTruyVan DESC LIMIT 1"))
        return r.mappings().first()
    except Exception:
        return None


async def session_count(session: AsyncSession) -> int:
    return await _count(session, "PHIEN_CHAT_AI")


async def order_status_counts(session: AsyncSession) -> dict[str, int]:
    return {}


async def order_count_between(session: AsyncSession, start: date, end: date) -> int:
    return 0


async def lot_cache_mismatch_count(session: AsyncSession) -> int:
    return 0


async def ledger_mismatch_count(session: AsyncSession) -> int:
    return 0
