"""Document 06 cases that the 01/11 traceability found without a mapped test."""

from datetime import timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import func, select, text

from app.core.errors import BusinessRuleError
from app.core.security import create_access_token, hash_password
from app.modules.catalog.models import Dish, DishGroup, Ingredient
from app.modules.inventory.models import GoodsReceipt, IngredientLot, StockIssue
from app.modules.sales.gateways import sepay
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from app.shared import business_date
from app.shared.audit import SystemAuditLog
from tests.modules.test_sales_holds import _hold, _make_client, _setup

pytestmark = pytest.mark.anyio


async def _user(session, role, username, password="pass123"):
    await seed_reference_data(session)
    user = (
        await session.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()
    if user is None:
        user = User(
            username=username,
            password_hash=hash_password(password),
            full_name=username,
            role_id=role,
            status="Hoạt động",
        )
        session.add(user)
        await session.commit()
    token = create_access_token(str(user.id), {"role": role, "username": username})
    return {"Authorization": f"Bearer {token}"}, user.id


async def _audit_count(session):
    return (await session.execute(select(func.count()).select_from(SystemAuditLog))).scalar_one()


# --- TC-CAT -----------------------------------------------------------------------------------


async def test_renaming_a_group_keeps_its_code_and_dishes(session):
    """TC-CAT-02 (FR-CAT-01)."""
    group = DishGroup(name="Món nướng", display_order=1, is_deleted=False)
    session.add(group)
    await session.flush()
    dish = Dish(name="Ba chỉ", group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.commit()
    gid, did = group.id, dish.id
    manager, _ = await _user(session, "MANAGER", "mgr_cat")
    client = await _make_client(session)

    renamed = await client.patch(
        f"/api/v1/catalog/groups/{gid}", json={"TenNhom": "Món nướng than"}, headers=manager
    )

    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["MaNhomMon"] == gid
    assert renamed.json()["TenNhom"] == "Món nướng than"
    session.expire_all()
    assert (await session.get(Dish, did)).group_id == gid


async def test_a_negative_stock_threshold_is_refused_and_the_old_one_stays(session):
    """TC-CAT-46 (FR-INV-07)."""
    ingredient = Ingredient(name="NL ngưỡng", unit="g", min_stock=500, stock_qty=0)
    session.add(ingredient)
    await session.commit()
    iid = ingredient.id
    manager, _ = await _user(session, "MANAGER", "mgr_thr")
    client = await _make_client(session)

    refused = await client.patch(
        f"/api/v1/catalog/ingredients/{iid}", json={"MucTonToiThieu": -1}, headers=manager
    )

    assert refused.status_code == 422
    session.expire_all()
    assert (await session.get(Ingredient, iid)).min_stock == 500


# --- TC-SET -----------------------------------------------------------------------------------


async def _login(client, username, password):
    return await client.post(
        "/api/v1/settings/auth/login", json={"username": username, "password": password}
    )


async def test_a_user_changes_their_own_password_without_an_audit_entry(session):
    """TC-SET-02 (FR-SET-02)."""
    headers, _ = await _user(session, "CASHIER", "cashier_pw", "old-pass-1")
    client = await _make_client(session)
    audits = await _audit_count(session)

    changed = await client.post(
        "/api/v1/settings/auth/change-password",
        json={"old_password": "old-pass-1", "new_password": "new-pass-2"},
        headers=headers,
    )

    assert changed.status_code == 204, changed.text
    assert (await _login(client, "cashier_pw", "old-pass-1")).status_code in (400, 401, 403, 422)
    assert (await _login(client, "cashier_pw", "new-pass-2")).status_code == 200
    assert await _audit_count(session) == audits


async def test_a_wrong_current_password_changes_nothing(session):
    """TC-SET-03 (FR-SET-02)."""
    headers, _ = await _user(session, "CASHIER", "cashier_pw2", "old-pass-1")
    client = await _make_client(session)

    refused = await client.post(
        "/api/v1/settings/auth/change-password",
        json={"old_password": "wrong-pass", "new_password": "new-pass-2"},
        headers=headers,
    )

    assert refused.status_code in (400, 401, 403, 422)
    assert (await _login(client, "cashier_pw2", "old-pass-1")).status_code == 200


async def test_only_a_manager_can_reset_someone_elses_password(session):
    """TC-SET-05 (FR-SET-02, FR-SET-03, NFR-04)."""
    cashier, _ = await _user(session, "CASHIER", "cashier_rs")
    kitchen, _ = await _user(session, "WAREHOUSE", "kitchen_rs")
    _, target = await _user(session, "CASHIER", "target_rs", "keep-pass-1")
    client = await _make_client(session)
    audits = await _audit_count(session)

    for headers in (cashier, kitchen):
        denied = await client.post(
            f"/api/v1/settings/users/{target}/reset-password",
            json={"new_password": "hacked-pass-9"},
            headers=headers,
        )
        assert denied.status_code == 403

    assert (await _login(client, "target_rs", "keep-pass-1")).status_code == 200
    assert await _audit_count(session) == audits


# --- TC-SALE ----------------------------------------------------------------------------------


async def test_the_kitchen_cannot_submit_an_order(session):
    """TC-SALE-50 (FR-SALE-03, NFR-04)."""
    dish, ingredient, table = await _setup(session)
    kitchen, _ = await _user(session, "WAREHOUSE", "kitchen_so")
    client = await _make_client(session)

    denied = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": table.id, "lines": [{"MaMon": dish.id, "SoLuong": 1}]},
        headers=kitchen,
    )

    assert denied.status_code == 403
    orders = (await session.execute(text("SELECT COUNT(*) FROM `ORDER`"))).scalar_one()
    assert orders == 0
    await session.refresh(ingredient)
    assert float(ingredient.stock_qty) == 10


async def test_another_user_cannot_change_someone_elses_hold(session):
    """TC-SALE-51 (FR-INV-11, NFR-04)."""
    dish, _, table = await _setup(session)
    owner, _ = await _user(session, "CASHIER", "owner_hold")
    other, _ = await _user(session, "CASHIER", "other_hold")
    client = await _make_client(session)
    hold = (await _hold(client, owner, dish, table, quantity=2)).json()

    refused = await client.patch(
        f"/api/v1/sales/holds/{hold['MaGiuCho']}", json={"quantity": 5}, headers=other
    )

    assert refused.status_code in (403, 404, 422)
    listed = await client.get(
        f"/api/v1/sales/holds?selection_code={hold['MaLuotChon']}", headers=owner
    )
    assert [row["SoLuong"] for row in listed.json()] == [2]


async def test_a_manager_cannot_cancel_an_order_that_is_awaiting_or_paid(session):
    """TC-SALE-99 (FR-SALE-27)."""
    dish, _, _table = await _setup(session, stock=20)
    cashier, _ = await _user(session, "CASHIER", "cashier_cx")
    manager, _ = await _user(session, "MANAGER", "mgr_cx")
    client = await _make_client(session)

    async def submit():
        r = await client.post(
            "/api/v1/sales/orders",
            json={"order_type": "Mang về", "lines": [{"MaMon": dish.id, "SoLuong": 1}]},
            headers=cashier,
        )
        assert r.status_code == 201, r.text
        return r.json()["MaOrder"]

    waiting = await submit()
    qr = await client.post(f"/api/v1/sales/orders/{waiting}/pay/qr", headers=cashier)
    assert qr.status_code == 201, qr.text
    verifying = await client.post(
        f"/api/v1/sales/payments/{qr.json()['MaGiaoDich']}/request-verification",
        json={},
        headers=cashier,
    )
    assert verifying.status_code == 200, verifying.text
    paid = await submit()
    assert (
        await client.post(f"/api/v1/sales/orders/{paid}/pay/cash", headers=cashier)
    ).status_code < 300

    for order_id in (waiting, paid):
        refused = await client.post(
            f"/api/v1/sales/orders/{order_id}/cancel", json={"reason": "thử"}, headers=manager
        )
        assert refused.status_code == 422, refused.text

    states = dict((await session.execute(text("SELECT MaOrder, TrangThai FROM `ORDER`"))).all())
    assert states[waiting] == "Chờ xác minh thanh toán"
    assert states[paid] == "Đã thanh toán"


async def test_the_bank_listing_is_read_completely_and_a_truncated_one_fails(monkeypatch):
    """TC-SALE-94 / TC-SALE-95 (FR-SALE-15)."""

    def listing(count):
        rows = [
            {
                "id": str(n),
                "amount_in": "1000.00",
                "amount_out": "0.00",
                "transaction_content": f"TT{n}",
                "reference_number": f"FT{n}",
                "code": f"TT{n}",
            }
            for n in range(count, 0, -1)  # newest first, like the real API
        ]
        return httpx.MockTransport(lambda request: httpx.Response(200, json={"transactions": rows}))

    monkeypatch.setattr(sepay, "_transport", listing(151))
    rows = await sepay.recent_transfers(api_url="https://x/userapi", token="t", account="1")
    assert len(rows) == 151
    assert {row["id"] for row in rows} >= {"1", "151"}  # the oldest transfer is not lost

    monkeypatch.setattr(sepay, "_transport", listing(sepay.LISTING_LIMIT))
    with pytest.raises(BusinessRuleError):
        await sepay.recent_transfers(api_url="https://x/userapi", token="t", account="1")


# --- TC-INV / TC-BR ---------------------------------------------------------------------------


async def test_a_receipt_with_a_live_hold_cannot_be_edited_or_cancelled(session):
    """TC-INV-04 / TC-INV-07 (FR-INV-02)."""
    dish, ingredient, table = await _setup(session, stock=10)
    cashier, _ = await _user(session, "CASHIER", "cashier_inv")
    kitchen, _ = await _user(session, "WAREHOUSE", "kitchen_inv")
    client = await _make_client(session)
    assert (await _hold(client, cashier, dish, table, quantity=2)).status_code == 201
    rid = (await session.execute(select(GoodsReceipt.id))).scalars().first()
    iid = ingredient.id
    line = (
        await session.execute(text("SELECT MaChiTietNhap FROM CHI_TIET_PHIEU_NHAP"))
    ).scalar_one()

    edited = await client.patch(
        f"/api/v1/inventory/receipts/{rid}",
        json={"lines": [{"line_id": line, "quantity": 12, "unit_price": 1000}]},
        headers=kitchen,
    )
    cancelled = await client.delete(f"/api/v1/inventory/receipts/{rid}", headers=kitchen)

    assert edited.status_code == 422 and cancelled.status_code == 422
    session.expire_all()
    assert (await session.get(GoodsReceipt, rid)).status == "Hiệu lực"
    lot = (await session.execute(select(IngredientLot))).scalar_one()
    assert lot.quantity_remaining == 10 and lot.status != "Đã hủy"
    assert float((await session.get(Ingredient, iid)).stock_qty) == 10


async def test_a_stocktake_waits_for_every_hold_to_end(session):
    """TC-INV-33 / TC-INV-34 / TC-BR-02 / TC-BR-03 (FR-INV-08)."""
    from app.modules.sales.models import Reservation

    dish, _, table = await _setup(session)
    cashier, _ = await _user(session, "CASHIER", "cashier_st")
    kitchen, _ = await _user(session, "WAREHOUSE", "kitchen_st")
    client = await _make_client(session)
    created = await _hold(client, cashier, dish, table, quantity=2)
    hold_id = created.json()["MaGiuCho"]

    live = await client.post("/api/v1/inventory/stocktakes", headers=kitchen)
    assert live.status_code == 422  # TC-INV-34: a live hold blocks

    hold = await session.get(Reservation, hold_id)
    hold.expires_at = business_date.now().replace(tzinfo=None) - timedelta(minutes=1)
    await session.commit()
    expired = await client.post("/api/v1/inventory/stocktakes", headers=kitchen)
    assert expired.status_code == 422  # TC-INV-33 / TC-BR-02: expired but still unsent

    released = await client.delete(f"/api/v1/sales/holds/{hold_id}", headers=cashier)
    assert released.status_code == 200, released.text
    opened = await client.post("/api/v1/inventory/stocktakes", headers=kitchen)
    assert opened.status_code == 201, opened.text  # TC-BR-03: nothing left in the way
    second = await client.post("/api/v1/inventory/stocktakes", headers=kitchen)
    assert second.status_code == 422  # one counting session at a time


async def test_a_stocktake_with_no_difference_changes_nothing(session):
    """TC-INV-44 (FR-INV-08, FR-INV-09)."""
    ingredient = Ingredient(name="NL khớp sổ", unit="g", stock_qty=Decimal(500), min_stock=0)
    session.add(ingredient)
    await session.flush()
    session.add(
        IngredientLot(
            ingredient_id=ingredient.id,
            quantity_remaining=Decimal(500),
            received_quantity=Decimal(500),
            status="Còn hạn",
            received_at=business_date.now(),
        )
    )
    await session.commit()
    iid = ingredient.id
    kitchen, _ = await _user(session, "WAREHOUSE", "kitchen_eq")
    client = await _make_client(session)
    sid = (await client.post("/api/v1/inventory/stocktakes", headers=kitchen)).json()[
        "MaPhieuKiemKe"
    ]
    await client.post(
        f"/api/v1/inventory/stocktakes/{sid}/counts",
        json=[{"ingredient_id": iid, "actual_qty": 500}],
        headers=kitchen,
    )

    confirmed = await client.post(f"/api/v1/inventory/stocktakes/{sid}/confirm", headers=kitchen)

    assert confirmed.status_code == 200, confirmed.text
    session.expire_all()
    assert float((await session.get(Ingredient, iid)).stock_qty) == 500
    assert (await session.execute(select(func.count()).select_from(StockIssue))).scalar_one() == 0
    status = (await session.execute(text("SELECT TrangThai FROM PHIEU_KIEM_KE"))).scalar_one()
    assert status == "Đã xác nhận"
