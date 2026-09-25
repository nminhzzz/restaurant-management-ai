"""FR-INV-01/02 — goods receipts: create, cancel, edit."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.catalog.models import Ingredient, Supplier
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from tests.helpers import lot_total, movements_for


async def _first_line_id(session, receipt_id: int) -> int:
    from sqlalchemy import select as sel

    from app.modules.inventory.models import GoodsReceiptLine

    r = await session.execute(
        sel(GoodsReceiptLine.id).where(GoodsReceiptLine.receipt_id == receipt_id)
    )
    return r.scalar_one()


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(session, role="WAREHOUSE", username="kho01"):
    await seed_reference_data(session)
    from sqlalchemy import select as sel

    r = await session.execute(sel(User).where(User.username == username))
    u = r.scalar_one_or_none()
    if u is None:
        u = User(
            username=username,
            password_hash=hash_password("pass"),
            full_name=username,
            role_id=role,
            status="Hoạt động",
        )
        session.add(u)
        await session.flush()
        await session.commit()
    tok = create_access_token(str(u.id), {"role": u.role_id, "username": u.username})
    return {"Authorization": f"Bearer {tok}"}, u


async def _ingredient(session, name="Gạo", min_stock=0, stock_qty=0):
    ing = Ingredient(
        name=name, unit="kg", min_stock=min_stock, stock_qty=stock_qty, is_deleted=False
    )
    session.add(ing)
    await session.flush()
    await session.commit()
    return ing


@pytest.mark.anyio
async def test_receipt_creates_lot_and_raises_stock_by_purchase_unit_times_factor(session):
    ing = await _ingredient(session, stock_qty=0)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={
            "lines": [
                {
                    "ingredient_id": ing.id,
                    "quantity": 3,
                    "unit_price": 20000,
                    "purchase_unit": "bao",
                    "conversion_factor": 5,
                }
            ]
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    rid = r.json()["MaPhieuNhap"]
    await session.refresh(ing)
    # 3 bao x 5 kg/bao = 15 kg
    assert float(ing.stock_qty) == 15
    assert await lot_total(session, ing.id) == 15
    moves = await movements_for(session, ing.id)
    assert len(moves) == 1
    assert moves[0]["LoaiGiaoDich"] == "Nhập"
    assert rid


@pytest.mark.anyio
async def test_receipt_with_supplier_and_default_factor(session):
    ing = await _ingredient(session)
    sup = Supplier(name="NCC A", is_deleted=False)
    session.add(sup)
    await session.flush()
    await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={
            "supplier_id": sup.id,
            "lines": [{"ingredient_id": ing.id, "quantity": 10, "unit_price": 5000}],
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    await session.refresh(ing)
    assert float(ing.stock_qty) == 10


@pytest.mark.anyio
async def test_receipt_rejects_unknown_supplier(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={
            "supplier_id": 999,
            "lines": [{"ingredient_id": ing.id, "quantity": 10, "unit_price": 5000}],
        },
        headers=h,
    )
    assert r.status_code == 422


@pytest.mark.anyio
async def test_cancel_receipt_reverses_stock(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 8, "unit_price": 1000}]},
        headers=h,
    )
    rid = r.json()["MaPhieuNhap"]
    r2 = await client.delete(f"/api/v1/inventory/receipts/{rid}", headers=h)
    assert r2.status_code == 200, r2.text
    await session.refresh(ing)
    assert float(ing.stock_qty) == 0
    assert await lot_total(session, ing.id) == 0


@pytest.mark.anyio
async def test_cancel_receipt_refused_once_lot_fully_consumed(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 5, "unit_price": 1000}]},
        headers=h,
    )
    rid = r.json()["MaPhieuNhap"]
    # Draw all of it via a manual issue so the lot is fully consumed.
    r3 = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 5}]},
        headers=h,
    )
    assert r3.status_code == 201, r3.text
    r2 = await client.delete(f"/api/v1/inventory/receipts/{rid}", headers=h)
    assert r2.status_code == 422


@pytest.mark.anyio
async def test_cancel_receipt_twice_refused(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 5, "unit_price": 1000}]},
        headers=h,
    )
    rid = r.json()["MaPhieuNhap"]
    r1 = await client.delete(f"/api/v1/inventory/receipts/{rid}", headers=h)
    assert r1.status_code == 200
    r2 = await client.delete(f"/api/v1/inventory/receipts/{rid}", headers=h)
    assert r2.status_code == 422


@pytest.mark.anyio
async def test_cashier_cannot_create_receipt(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session, role="CASHIER", username="cashier_x")
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 5, "unit_price": 1000}]},
        headers=h,
    )
    assert r.status_code == 403


@pytest.mark.anyio
async def test_list_receipts_filters_by_supplier(session):
    ing = await _ingredient(session)
    sup1 = Supplier(name="A", is_deleted=False)
    sup2 = Supplier(name="B", is_deleted=False)
    session.add_all([sup1, sup2])
    await session.flush()
    await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)
    await client.post(
        "/api/v1/inventory/receipts",
        json={
            "supplier_id": sup1.id,
            "lines": [{"ingredient_id": ing.id, "quantity": 1, "unit_price": 1000}],
        },
        headers=h,
    )
    await client.post(
        "/api/v1/inventory/receipts",
        json={
            "supplier_id": sup2.id,
            "lines": [{"ingredient_id": ing.id, "quantity": 1, "unit_price": 1000}],
        },
        headers=h,
    )
    r = await client.get(f"/api/v1/inventory/receipts?supplier_id={sup1.id}", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["MaNhaCungCap"] == sup1.id


@pytest.mark.anyio
async def test_list_receipts_filters_by_status_and_date_range(session):
    from datetime import timedelta

    from app.shared import business_date

    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 1, "unit_price": 1000}]},
        headers=h,
    )
    rid = r.json()["MaPhieuNhap"]
    await client.delete(f"/api/v1/inventory/receipts/{rid}", headers=h)
    await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 1, "unit_price": 1000}]},
        headers=h,
    )

    by_status = await client.get("/api/v1/inventory/receipts?status=Đã hủy", headers=h)
    assert by_status.status_code == 200
    assert by_status.json()["total"] == 1
    assert by_status.json()["items"][0]["MaPhieuNhap"] == rid

    today = business_date.now().date()
    tomorrow = today + timedelta(days=1)
    out_of_range = await client.get(
        f"/api/v1/inventory/receipts?date_from={tomorrow.isoformat()}&date_to={tomorrow.isoformat()}",
        headers=h,
    )
    assert out_of_range.json()["total"] == 0


@pytest.mark.anyio
async def test_list_receipts_rejects_a_malformed_date(session):
    await _headers(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.get("/api/v1/inventory/receipts?date_from=25-09-2026", headers=h)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_list_receipts_total_reflects_all_rows_across_pages(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    for _ in range(3):
        await client.post(
            "/api/v1/inventory/receipts",
            json={"lines": [{"ingredient_id": ing.id, "quantity": 1, "unit_price": 1000}]},
            headers=h,
        )
    r = await client.get("/api/v1/inventory/receipts?page=1&page_size=2", headers=h)
    body = r.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


@pytest.mark.anyio
async def test_edit_receipt_line_before_consumption_adjusts_stock(session):
    """FR-INV-02 edit: quantity/price on an untouched line can be corrected.

    This edits the already-converted (standard-unit) line quantity directly —
    there is no migration adding a distinct "purchase unit" column to
    CHI_TIET_PHIEU_NHAP, so the edit endpoint works on the stored quantity.
    """
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 5, "unit_price": 1000}]},
        headers=h,
    )
    rid = r.json()["MaPhieuNhap"]
    line_id = await _first_line_id(session, rid)
    r2 = await client.patch(
        f"/api/v1/inventory/receipts/{rid}",
        json={"lines": [{"line_id": line_id, "quantity": 9, "unit_price": 1200}]},
        headers=h,
    )
    assert r2.status_code == 200, r2.text
    await session.refresh(ing)
    assert float(ing.stock_qty) == 9
    assert await lot_total(session, ing.id) == 9


@pytest.mark.anyio
async def test_edit_receipt_refused_once_consumed(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 5, "unit_price": 1000}]},
        headers=h,
    )
    rid = r.json()["MaPhieuNhap"]
    line_id = await _first_line_id(session, rid)
    await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 2}]},
        headers=h,
    )
    r2 = await client.patch(
        f"/api/v1/inventory/receipts/{rid}",
        json={"lines": [{"line_id": line_id, "quantity": 9, "unit_price": 1200}]},
        headers=h,
    )
    assert r2.status_code == 422
