"""Sales review gaps, payment side: the QR and exception flow of FR-SALE-13…23, 26, 33…35."""

from dataclasses import dataclass
from datetime import timedelta

import pytest
from sqlalchemy import func, select, update

from app.modules.catalog.models import Dish
from app.modules.sales.models import Invoice, Order, OrderLine, PaymentTransaction
from app.modules.sales.payments import sign_payload
from app.modules.settings.models import SystemConfig
from app.shared import business_date
from app.shared.audit import SystemAuditLog
from tests.helpers import FIXED_NOW
from tests.modules.sales_support import Sellable, api, place_order, sellable, staff, table

BASE = "/api/v1/sales"
TOTAL = 50000


@dataclass
class Scene:
    client: object
    cashier: dict
    manager: dict
    manager_id: int
    world: Sellable
    desk_id: int
    order_id: int
    line_id: int


async def scene(session, *, qr: bool = False) -> tuple[Scene, int | None]:
    world = await sellable(session)
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "cashier")
    manager, manager_user = await staff(session, "MANAGER", "manager")
    order = await place_order(client, cashier, desk, [(world.dish.id, 1)])
    ctx = Scene(
        client=client,
        cashier=cashier,
        manager=manager,
        manager_id=manager_user.id,
        world=world,
        desk_id=desk.id,
        order_id=order["MaOrder"],
        line_id=order["lines"][0]["MaChiTietOrder"],
    )
    payment_id = None
    if qr:
        started = await client.post(f"{BASE}/orders/{ctx.order_id}/pay/qr", headers=cashier)
        assert started.status_code == 201, started.text
        payment_id = started.json()["MaGiaoDich"]
    return ctx, payment_id


async def order_state(session, order_id):
    row = (
        await session.execute(
            select(Order.status, Order.closed_at, Order.updated_at).where(Order.id == order_id)
        )
    ).one()
    return row.status


async def payment_state(session, payment_id):
    return (
        await session.execute(
            select(PaymentTransaction.status).where(PaymentTransaction.id == payment_id)
        )
    ).scalar_one()


async def invoices_of(session, order_id) -> list[Invoice]:
    return list(
        (await session.execute(select(Invoice).where(Invoice.order_id == order_id))).scalars()
    )


async def ask_verification(ctx, payment_id, **body):
    body = body or {"MaGiaoDichNganHang": "FT123", "GhiChu": "Khách đưa màn hình chuyển khoản"}
    return await ctx.client.post(
        f"{BASE}/payments/{payment_id}/verification", json=body, headers=ctx.cashier
    )


async def hook(ctx, payment_id, amount=TOTAL):
    signature = sign_payload(f"{payment_id}:{amount}")
    return await ctx.client.post(
        f"{BASE}/webhooks/payment",
        json={"MaGiaoDich": payment_id, "SoTien": amount, "ChuKy": signature},
    )


async def exceptions_of(session) -> list[PaymentTransaction]:
    return list(
        (
            await session.execute(
                select(PaymentTransaction).where(PaymentTransaction.exception_status.is_not(None))
            )
        ).scalars()
    )


# --- a live QR locks the order (FR-SALE-14, FR-SALE-22, FR-SALE-29) ----------


@pytest.mark.anyio
async def test_a_qr_moves_the_order_to_waiting_for_confirmation_and_locks_it(session):
    ctx, payment_id = await scene(session, qr=True)
    other = await table(session, "Bàn 2")
    assert await order_state(session, ctx.order_id) == "Chờ xác nhận thanh toán"

    attempts = {
        "add": await ctx.client.post(
            f"{BASE}/orders/{ctx.order_id}/lines",
            json={"MaMon": ctx.world.dish.id, "SoLuong": 1},
            headers=ctx.cashier,
        ),
        "update": await ctx.client.patch(
            f"{BASE}/orders/{ctx.order_id}/lines/{ctx.line_id}",
            json={"SoLuong": 2},
            headers=ctx.cashier,
        ),
        "cancel line": await ctx.client.post(
            f"{BASE}/orders/{ctx.order_id}/lines/{ctx.line_id}/cancel",
            json={"LyDo": "x"},
            headers=ctx.cashier,
        ),
        "move": await ctx.client.post(
            f"{BASE}/orders/{ctx.order_id}/move", json={"MaBanDich": other.id}, headers=ctx.cashier
        ),
        "cancel order": await ctx.client.post(
            f"{BASE}/orders/{ctx.order_id}/cancel", json={"LyDoHuy": "x"}, headers=ctx.manager
        ),
        "second qr": await ctx.client.post(
            f"{BASE}/orders/{ctx.order_id}/pay/qr", headers=ctx.cashier
        ),
        "cash": await ctx.client.post(
            f"{BASE}/orders/{ctx.order_id}/pay/cash", headers=ctx.cashier
        ),
    }

    assert {name: r.status_code for name, r in attempts.items()} == dict.fromkeys(attempts, 422)
    assert await payment_state(session, payment_id) == "Chờ xác nhận"


@pytest.mark.anyio
async def test_cancelling_the_qr_unlocks_the_order_and_allows_cash(session):
    ctx, payment_id = await scene(session, qr=True)

    cancelled = await ctx.client.post(f"{BASE}/payments/{payment_id}/cancel", headers=ctx.cashier)
    paid = await ctx.client.post(f"{BASE}/orders/{ctx.order_id}/pay/cash", headers=ctx.cashier)

    assert cancelled.status_code == 200 and cancelled.json()["TrangThai"] == "Đã hủy"
    assert paid.status_code == 200, paid.text
    assert await order_state(session, ctx.order_id) == "Đã thanh toán"


@pytest.mark.anyio
async def test_an_expired_qr_returns_the_order_to_open(session, monkeypatch):
    ctx, payment_id = await scene(session, qr=True)
    monkeypatch.setattr(business_date, "now", lambda: FIXED_NOW + timedelta(minutes=11))

    detail = await ctx.client.get(f"{BASE}/orders/{ctx.order_id}", headers=ctx.cashier)

    assert detail.json()["TrangThai"] == "Đang mở"
    assert await payment_state(session, payment_id) == "Hết hạn"
    added = await ctx.client.post(
        f"{BASE}/orders/{ctx.order_id}/lines",
        json={"MaMon": ctx.world.dish.id, "SoLuong": 1},
        headers=ctx.cashier,
    )
    assert added.status_code == 201, added.text


@pytest.mark.anyio
async def test_payment_waits_for_unsent_add_on_selections(session):
    ctx, _ = await scene(session)
    selection = (
        await ctx.client.post(
            f"{BASE}/selections",
            json={"MaBan": ctx.desk_id, "MaOrder": ctx.order_id},
            headers=ctx.cashier,
        )
    ).json()["MaLuotChon"]
    held = await ctx.client.put(
        f"{BASE}/selections/{selection}/lines/{ctx.world.dish.id}",
        json={"SoLuong": 1, "MaBan": ctx.desk_id, "MaOrder": ctx.order_id},
        headers=ctx.cashier,
    )
    assert held.status_code == 200, held.text

    cash = await ctx.client.post(f"{BASE}/orders/{ctx.order_id}/pay/cash", headers=ctx.cashier)
    qr = await ctx.client.post(f"{BASE}/orders/{ctx.order_id}/pay/qr", headers=ctx.cashier)
    dropped = await ctx.client.delete(
        f"{BASE}/holds/{held.json()['MaGiuCho']}", headers=ctx.cashier
    )
    cash_after = await ctx.client.post(
        f"{BASE}/orders/{ctx.order_id}/pay/cash", headers=ctx.cashier
    )

    assert cash.status_code == 422 and qr.status_code == 422
    assert dropped.status_code == 200 and cash_after.status_code == 200


# --- cash, invoice and provisional bill (FR-SALE-13, 21, 26) ----------


@pytest.mark.anyio
async def test_cash_issues_a_unique_numbered_invoice_for_the_cashier(session):
    ctx, _ = await scene(session)
    second = await place_order(
        ctx.client, ctx.cashier, await table(session, "Bàn 2"), [(ctx.world.dish.id, 1)]
    )

    first_paid = await ctx.client.post(
        f"{BASE}/orders/{ctx.order_id}/pay/cash", headers=ctx.cashier
    )
    second_paid = await ctx.client.post(
        f"{BASE}/orders/{second['MaOrder']}/pay/cash", headers=ctx.manager
    )

    numbers = [first_paid.json()["invoice"]["SoHoaDon"], second_paid.json()["invoice"]["SoHoaDon"]]
    assert numbers[0] != numbers[1] and all(n.startswith("HD-") for n in numbers)
    invoice = (await invoices_of(session, ctx.order_id))[0]
    assert invoice.invoice_number == numbers[0]
    assert invoice.issued_by is not None and invoice.issued_at == FIXED_NOW
    other = (await invoices_of(session, second["MaOrder"]))[0]
    assert other.issued_by == ctx.manager_id
    assert invoice.business_date == (await session.get(Order, ctx.order_id)).business_date


@pytest.mark.anyio
async def test_paying_does_not_free_the_table_the_cashier_does(session):
    ctx, _ = await scene(session)
    await ctx.client.post(f"{BASE}/orders/{ctx.order_id}/pay/cash", headers=ctx.cashier)

    from app.modules.catalog.models import DiningTable

    row = (
        await session.execute(
            select(DiningTable.status, DiningTable.serving_order_id).where(
                DiningTable.id == ctx.desk_id
            )
        )
    ).one()
    assert tuple(row) == ("Đang phục vụ", ctx.order_id)
    released = await ctx.client.post(
        f"/api/v1/catalog/tables/{ctx.desk_id}/release",
        json={"MaOrder": ctx.order_id},
        headers=ctx.cashier,
    )
    assert released.status_code == 200 and released.json()["TrangThai"] == "Trống"


@pytest.mark.anyio
async def test_reprint_renders_the_stored_invoice_not_the_live_data(session):
    ctx, _ = await scene(session)
    await ctx.client.post(f"{BASE}/orders/{ctx.order_id}/pay/cash", headers=ctx.cashier)
    original = (
        await ctx.client.get(f"{BASE}/orders/{ctx.order_id}/invoice", headers=ctx.cashier)
    ).json()
    await session.execute(update(Dish).where(Dish.id == ctx.world.dish.id).values(name="Tên mới"))
    config = (await session.execute(select(SystemConfig))).scalar_one()
    config.restaurant_name = "Nhà hàng đổi tên"
    await session.commit()

    again = await ctx.client.post(
        f"{BASE}/orders/{ctx.order_id}/invoice/reprint", headers=ctx.cashier
    )

    body = again.json()
    assert body["lines"] == original["lines"] and body["TenNhaHang"] == original["TenNhaHang"]
    assert body["SoHoaDon"] == original["SoHoaDon"] and body["TongTien"] == original["TongTien"]
    assert body["SoLanIn"] == original["SoLanIn"] + 1
    audit = (
        await session.execute(
            select(SystemAuditLog).where(SystemAuditLog.action == "REPRINT_INVOICE")
        )
    ).scalar_one()
    assert audit.before == {"SoLanIn": 1} and audit.after["SoLanIn"] == 2


@pytest.mark.anyio
async def test_the_provisional_bill_bills_nothing_and_locks_nothing(session):
    ctx, _ = await scene(session)

    bill = await ctx.client.get(
        f"{BASE}/orders/{ctx.order_id}/provisional-bill", headers=ctx.cashier
    )
    again = await ctx.client.get(
        f"{BASE}/orders/{ctx.order_id}/provisional-bill", headers=ctx.cashier
    )

    body = bill.json()
    assert bill.status_code == 200 and again.status_code == 200
    assert body["TieuDe"] == "PHIẾU TẠM TÍNH - CHƯA THANH TOÁN" and body["TongTien"] == TOTAL
    assert [line["TenMon"] for line in body["lines"]] == ["Món"]
    assert "SoHoaDon" not in body
    assert await invoices_of(session, ctx.order_id) == []
    assert await order_state(session, ctx.order_id) == "Đang mở"
    added = await ctx.client.post(
        f"{BASE}/orders/{ctx.order_id}/lines",
        json={"MaMon": ctx.world.dish.id, "SoLuong": 1},
        headers=ctx.cashier,
    )
    assert added.status_code == 201
    paid_total = (
        await ctx.client.get(f"{BASE}/orders/{ctx.order_id}/provisional-bill", headers=ctx.cashier)
    ).json()["TongTien"]
    assert paid_total == 2 * TOTAL


@pytest.mark.anyio
async def test_no_provisional_bill_once_the_order_is_paid(session):
    ctx, _ = await scene(session)
    await ctx.client.post(f"{BASE}/orders/{ctx.order_id}/pay/cash", headers=ctx.cashier)

    bill = await ctx.client.get(
        f"{BASE}/orders/{ctx.order_id}/provisional-bill", headers=ctx.cashier
    )

    assert bill.status_code == 422


# --- verification (FR-SALE-19, 20, 23, 34, 35) ----------


@pytest.mark.anyio
@pytest.mark.parametrize("expire_first", [False, True])
async def test_verification_works_while_the_qr_is_valid_or_expired(
    session, monkeypatch, expire_first
):
    ctx, payment_id = await scene(session, qr=True)
    if expire_first:
        monkeypatch.setattr(business_date, "now", lambda: FIXED_NOW + timedelta(minutes=30))

    response = await ask_verification(ctx, payment_id)

    assert response.status_code == 200, response.text
    assert response.json()["TrangThai"] == "Chờ xác minh thanh toán"
    assert await order_state(session, ctx.order_id) == "Chờ xác minh thanh toán"
    row = (
        await session.execute(select(PaymentTransaction).where(PaymentTransaction.id == payment_id))
    ).scalar_one()
    assert row.bank_ref == "FT123"


@pytest.mark.anyio
async def test_verification_needs_a_reference_or_a_note(session):
    ctx, payment_id = await scene(session, qr=True)

    response = await ctx.client.post(
        f"{BASE}/payments/{payment_id}/verification", json={}, headers=ctx.cashier
    )

    assert response.status_code == 422
    assert await order_state(session, ctx.order_id) == "Chờ xác nhận thanh toán"


@pytest.mark.anyio
async def test_a_waiting_order_is_locked_against_every_change_and_new_payment(session):
    ctx, payment_id = await scene(session, qr=True)
    await ask_verification(ctx, payment_id)
    other = await table(session, "Bàn 2")

    attempts = [
        await ctx.client.post(
            f"{BASE}/orders/{ctx.order_id}/lines",
            json={"MaMon": ctx.world.dish.id, "SoLuong": 1},
            headers=ctx.cashier,
        ),
        await ctx.client.post(
            f"{BASE}/orders/{ctx.order_id}/move", json={"MaBanDich": other.id}, headers=ctx.cashier
        ),
        await ctx.client.post(
            f"{BASE}/orders/{ctx.order_id}/cancel", json={"LyDoHuy": "x"}, headers=ctx.manager
        ),
        await ctx.client.post(f"{BASE}/orders/{ctx.order_id}/pay/qr", headers=ctx.cashier),
        await ctx.client.post(f"{BASE}/orders/{ctx.order_id}/pay/cash", headers=ctx.cashier),
        await ask_verification(ctx, payment_id),
    ]

    assert [r.status_code for r in attempts] == [422] * 6


@pytest.mark.anyio
async def test_a_cancelled_qr_can_still_be_claimed_by_a_guest_who_paid(session):
    ctx, payment_id = await scene(session, qr=True)
    await ctx.client.post(f"{BASE}/payments/{payment_id}/cancel", headers=ctx.cashier)

    response = await ask_verification(ctx, payment_id)

    assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_only_the_manager_decides_on_unverified_money(session):
    ctx, payment_id = await scene(session, qr=True)
    await ask_verification(ctx, payment_id)
    decision = {"LyDo": "đã thống nhất", "KetQuaXuLy": "khách trả lại"}

    denied = [
        await ctx.client.post(
            f"{BASE}/payments/{payment_id}/confirm-received", json={}, headers=ctx.cashier
        ),
        await ctx.client.post(
            f"{BASE}/payments/{payment_id}/reopen", json=decision, headers=ctx.cashier
        ),
        await ctx.client.post(
            f"{BASE}/payments/{payment_id}/close-unpaid", json=decision, headers=ctx.cashier
        ),
        await ctx.client.get(f"{BASE}/payment-exceptions", headers=ctx.cashier),
    ]

    assert [r.status_code for r in denied] == [403] * 4
    assert await order_state(session, ctx.order_id) == "Chờ xác minh thanh toán"


@pytest.mark.anyio
async def test_the_cashier_adds_evidence_and_the_manager_saves_a_check_without_closing(session):
    ctx, payment_id = await scene(session, qr=True)
    await ask_verification(ctx, payment_id, GhiChu="khách báo đã chuyển")

    cashier_note = await ctx.client.post(
        f"{BASE}/payments/{payment_id}/verification-notes",
        json={
            "GhiChu": "khách gửi ảnh",
            "AnhChungTu": "evidence/1.png",
            "MaGiaoDichNganHang": "FT999",
        },
        headers=ctx.cashier,
    )
    manager_note = await ctx.client.post(
        f"{BASE}/payments/{payment_id}/verification-notes",
        json={"GhiChu": "chưa thấy khoản nhận trong sao kê"},
        headers=ctx.manager,
    )

    assert cashier_note.status_code == 200 and manager_note.status_code == 200
    assert await order_state(session, ctx.order_id) == "Chờ xác minh thanh toán"
    notes = list(
        (
            await session.execute(
                select(SystemAuditLog)
                .where(SystemAuditLog.action == "PAYMENT_VERIFICATION_NOTE")
                .order_by(SystemAuditLog.id)
            )
        ).scalars()
    )
    assert [n.reason for n in notes] == ["khách gửi ảnh", "chưa thấy khoản nhận trong sao kê"]
    assert notes[0].after["AnhChungTu"] == "evidence/1.png"
    row = (
        await session.execute(select(PaymentTransaction).where(PaymentTransaction.id == payment_id))
    ).scalar_one()
    assert (row.bank_ref, row.evidence) == ("FT999", "evidence/1.png")


@pytest.mark.anyio
async def test_a_bank_reference_can_only_belong_to_one_transaction(session):
    first, first_payment = await scene(session, qr=True)
    await ask_verification(first, first_payment, MaGiaoDichNganHang="FT-SAME")
    second_world = await place_order(
        first.client, first.cashier, await table(session, "Bàn 2"), [(first.world.dish.id, 1)]
    )
    started = await first.client.post(
        f"{BASE}/orders/{second_world['MaOrder']}/pay/qr", headers=first.cashier
    )

    response = await first.client.post(
        f"{BASE}/payments/{started.json()['MaGiaoDich']}/verification",
        json={"MaGiaoDichNganHang": "FT-SAME"},
        headers=first.cashier,
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_the_manager_confirms_receipt_once_and_the_invoice_is_issued_once(session):
    ctx, payment_id = await scene(session, qr=True)
    await ask_verification(ctx, payment_id)

    confirmed = await ctx.client.post(
        f"{BASE}/payments/{payment_id}/confirm-received",
        json={"GhiChu": "đã thấy"},
        headers=ctx.manager,
    )
    again = await ctx.client.post(
        f"{BASE}/payments/{payment_id}/confirm-received", json={}, headers=ctx.manager
    )

    assert confirmed.status_code == 200, confirmed.text
    assert again.status_code == 422
    assert await order_state(session, ctx.order_id) == "Đã thanh toán"
    assert await payment_state(session, payment_id) == "Thành công"
    invoices = await invoices_of(session, ctx.order_id)
    assert len(invoices) == 1 and invoices[0].issued_by == ctx.manager_id
    assert invoices[0].payment_transaction_id == payment_id


@pytest.mark.anyio
async def test_reopening_cancels_the_old_attempt_and_lets_the_cashier_collect_again(session):
    ctx, payment_id = await scene(session, qr=True)
    await ask_verification(ctx, payment_id)

    reopened = await ctx.client.post(
        f"{BASE}/payments/{payment_id}/reopen",
        json={"LyDo": "khách chịu trả lại", "KetQuaXuLy": "ngân hàng chưa thấy tiền"},
        headers=ctx.manager,
    )
    cash = await ctx.client.post(f"{BASE}/orders/{ctx.order_id}/pay/cash", headers=ctx.cashier)

    assert reopened.status_code == 200, reopened.text
    assert await payment_state(session, payment_id) == "Đã hủy"
    assert cash.status_code == 200 and await order_state(session, ctx.order_id) == "Đã thanh toán"
    entry = (
        await session.execute(
            select(SystemAuditLog).where(
                SystemAuditLog.action == "REOPEN_PAYMENT", SystemAuditLog.target_entity == "ORDER"
            )
        )
    ).scalar_one()
    assert entry.reason == "khách chịu trả lại" and entry.user_id == ctx.manager_id
    assert entry.after["KetQuaXuLy"] == "ngân hàng chưa thấy tiền"


@pytest.mark.anyio
async def test_a_reopen_needs_a_reason_and_an_outcome(session):
    ctx, payment_id = await scene(session, qr=True)
    await ask_verification(ctx, payment_id)

    response = await ctx.client.post(
        f"{BASE}/payments/{payment_id}/reopen", json={"LyDo": "x"}, headers=ctx.manager
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_closing_unpaid_records_who_why_and_how_much_and_issues_no_invoice(session):
    ctx, payment_id = await scene(session, qr=True)
    await ask_verification(ctx, payment_id)

    closed = await ctx.client.post(
        f"{BASE}/payments/{payment_id}/close-unpaid",
        json={"LyDo": "khách bỏ đi", "KetQuaXuLy": "ngân hàng xác nhận không có tiền"},
        headers=ctx.manager,
    )

    assert closed.status_code == 200, closed.text
    assert await order_state(session, ctx.order_id) == "Đóng \u2013 chưa thu được tiền"
    assert await payment_state(session, payment_id) == "Đóng \u2013 chưa thu được tiền"
    assert await invoices_of(session, ctx.order_id) == []
    order = await session.get(Order, ctx.order_id)
    assert order.closed_at == FIXED_NOW
    latest = (
        (
            await session.execute(
                select(SystemAuditLog)
                .where(
                    SystemAuditLog.target_entity == "ORDER",
                    SystemAuditLog.target_id == str(ctx.order_id),
                )
                .order_by(SystemAuditLog.id.desc())
            )
        )
        .scalars()
        .first()
    )
    assert latest.action == "CLOSE_ORDER_UNPAID" and latest.reason == "khách bỏ đi"
    assert latest.user_id == ctx.manager_id and latest.after["SoTienChuaThu"] == TOTAL
    # stock stays consumed and the order stays locked; the table is not freed by itself
    lines = (
        await session.execute(select(OrderLine.status).where(OrderLine.order_id == ctx.order_id))
    ).scalars()
    assert list(lines) == ["Chờ làm"]
    locked = await ctx.client.post(f"{BASE}/orders/{ctx.order_id}/pay/cash", headers=ctx.cashier)
    assert locked.status_code == 422


@pytest.mark.anyio
async def test_the_waiting_order_shows_in_the_unsettled_report_with_the_latest_result(session):
    ctx, payment_id = await scene(session, qr=True)
    await ask_verification(ctx, payment_id)
    await ctx.client.post(
        f"{BASE}/payments/{payment_id}/verification-notes",
        json={"GhiChu": "chưa tìm thấy khoản nhận"},
        headers=ctx.manager,
    )

    from app.modules.reports.queries import unsettled_orders

    items = await unsettled_orders(session, FIXED_NOW + timedelta(minutes=5))

    assert [i.MaOrder for i in items] == [ctx.order_id]
    assert items[0].GiaTriOrder == TOTAL and items[0].SoPhutDaCho == 5
    assert items[0].KetQuaXuLyGanNhat == "chưa tìm thấy khoản nhận"
    revenue = (await session.execute(select(func.count(Invoice.id)))).scalar_one()
    assert revenue == 0


# --- late and exceptional money (FR-SALE-15…17) ----------


@pytest.mark.anyio
async def test_a_full_payment_settles_the_waiting_order_automatically(session):
    ctx, payment_id = await scene(session, qr=True)
    await ask_verification(ctx, payment_id)

    response = await hook(ctx, payment_id)

    assert response.status_code == 200 and response.json()["KetQua"] == "confirmed"
    assert await order_state(session, ctx.order_id) == "Đã thanh toán"
    assert await payment_state(session, payment_id) == "Thành công"
    assert len(await invoices_of(session, ctx.order_id)) == 1
    assert (await invoices_of(session, ctx.order_id))[0].issued_by is None


@pytest.mark.anyio
@pytest.mark.parametrize("how", ["expired", "cancelled"])
async def test_late_full_payment_for_an_expired_or_cancelled_qr_is_confirmed(
    session, monkeypatch, how
):
    ctx, payment_id = await scene(session, qr=True)
    if how == "expired":
        monkeypatch.setattr(business_date, "now", lambda: FIXED_NOW + timedelta(minutes=30))
    else:
        await ctx.client.post(f"{BASE}/payments/{payment_id}/cancel", headers=ctx.cashier)

    response = await hook(ctx, payment_id)

    assert response.json()["KetQua"] == "confirmed"
    assert await order_state(session, ctx.order_id) == "Đã thanh toán"
    assert await exceptions_of(session) == []


@pytest.mark.anyio
async def test_late_payment_cancels_a_newer_qr_that_has_no_money(session, monkeypatch):
    ctx, first_payment = await scene(session, qr=True)
    monkeypatch.setattr(business_date, "now", lambda: FIXED_NOW + timedelta(minutes=30))
    second = await ctx.client.post(f"{BASE}/orders/{ctx.order_id}/pay/qr", headers=ctx.cashier)
    assert second.status_code == 201, second.text

    response = await hook(ctx, first_payment)

    assert response.json()["KetQua"] == "confirmed"
    assert await payment_state(session, first_payment) == "Thành công"
    assert await payment_state(session, second.json()["MaGiaoDich"]) == "Đã hủy"
    assert len(await invoices_of(session, ctx.order_id)) == 1


@pytest.mark.anyio
async def test_a_wrong_amount_is_an_exception_and_changes_nothing(session):
    ctx, payment_id = await scene(session, qr=True)

    response = await hook(ctx, payment_id, amount=TOTAL - 1000)

    assert response.status_code == 200 and response.json()["KetQua"] == "exception"
    assert await order_state(session, ctx.order_id) == "Chờ xác nhận thanh toán"
    assert await payment_state(session, payment_id) == "Chờ xác nhận"
    assert await invoices_of(session, ctx.order_id) == []
    entry = (await exceptions_of(session))[0]
    assert (entry.exception_status, float(entry.exception_amount)) == ("Chờ xử lý", TOTAL - 1000)
    # the right amount can still settle the QR afterwards
    paid = await hook(ctx, payment_id)
    assert paid.json()["KetQua"] == "confirmed"


@pytest.mark.anyio
async def test_the_manager_lists_pending_exceptions_and_refunds_one_with_a_reference(session):
    ctx, payment_id = await scene(session, qr=True)
    await hook(ctx, payment_id, amount=TOTAL + 5000)

    listing = await ctx.client.get(
        f"{BASE}/payment-exceptions?status=Chờ xử lý", headers=ctx.manager
    )
    item = listing.json()["items"][0]
    refunded = await ctx.client.post(
        f"{BASE}/payment-exceptions/{item['MaGiaoDich']}/refund",
        json={"MaThamChieuHoan": "REF-001", "GhiChu": "hoàn qua ngân hàng"},
        headers=ctx.manager,
    )
    again = await ctx.client.post(
        f"{BASE}/payment-exceptions/{item['MaGiaoDich']}/refund",
        json={"MaThamChieuHoan": "REF-002"},
        headers=ctx.manager,
    )

    assert item["SoTienNgoaiLe"] == TOTAL + 5000 and item["CoTheApDung"] is False
    assert refunded.status_code == 200 and again.status_code == 422
    entry = (await exceptions_of(session))[0]
    assert entry.exception_status == "Đã hoàn tiền" and entry.refund_reference == "REF-001"
    assert entry.exception_handled_by == ctx.manager_id and entry.exception_handled_at == FIXED_NOW
    assert await invoices_of(session, ctx.order_id) == []
    pending = await ctx.client.get(
        f"{BASE}/payment-exceptions?status=Chờ xử lý", headers=ctx.manager
    )
    assert pending.json()["items"] == []


@pytest.mark.anyio
async def test_money_for_an_order_closed_unpaid_can_be_applied_by_the_manager_once(session):
    ctx, payment_id = await scene(session, qr=True)
    await ask_verification(ctx, payment_id)
    await ctx.client.post(
        f"{BASE}/payments/{payment_id}/close-unpaid",
        json={"LyDo": "không thấy tiền", "KetQuaXuLy": "đã tra soát"},
        headers=ctx.manager,
    )
    late = await hook(ctx, payment_id)
    assert late.json()["KetQua"] == "exception"
    assert await order_state(session, ctx.order_id) == "Đóng \u2013 chưa thu được tiền"
    entry_id = (await exceptions_of(session))[0].id

    applied = await ctx.client.post(
        f"{BASE}/payment-exceptions/{entry_id}/apply", json={}, headers=ctx.manager
    )
    twice = await ctx.client.post(
        f"{BASE}/payment-exceptions/{entry_id}/apply", json={}, headers=ctx.manager
    )

    assert applied.status_code == 200, applied.text
    assert twice.status_code == 422
    assert await order_state(session, ctx.order_id) == "Đã thanh toán"
    invoices = await invoices_of(session, ctx.order_id)
    assert len(invoices) == 1 and invoices[0].payment_transaction_id == entry_id
    assert (
        await session.get(PaymentTransaction, entry_id)
    ).exception_status == "Đã áp dụng cho order"


@pytest.mark.anyio
async def test_money_for_a_reopened_order_is_applied_and_the_new_attempt_dropped(session):
    ctx, payment_id = await scene(session, qr=True)
    await ask_verification(ctx, payment_id)
    await ctx.client.post(
        f"{BASE}/payments/{payment_id}/reopen",
        json={"LyDo": "thu lại", "KetQuaXuLy": "khách đồng ý"},
        headers=ctx.manager,
    )
    new_qr = await ctx.client.post(f"{BASE}/orders/{ctx.order_id}/pay/qr", headers=ctx.cashier)

    late = await hook(ctx, payment_id)  # the money of the reopened attempt arrives
    assert late.json()["KetQua"] == "exception"
    entry = (await exceptions_of(session))[0]
    applied = await ctx.client.post(
        f"{BASE}/payment-exceptions/{entry.id}/apply", json={}, headers=ctx.manager
    )

    assert applied.status_code == 200, applied.text
    assert await payment_state(session, new_qr.json()["MaGiaoDich"]) == "Đã hủy"
    assert await order_state(session, ctx.order_id) == "Đã thanh toán"
    assert len(await invoices_of(session, ctx.order_id)) == 1


@pytest.mark.anyio
async def test_money_for_an_already_paid_order_is_never_applied_or_counted_twice(session):
    ctx, payment_id = await scene(session, qr=True)
    first = await hook(ctx, payment_id)
    assert first.json()["KetQua"] == "confirmed"

    second = await ctx.client.post(
        f"{BASE}/webhooks/payment",
        json={
            "MaGiaoDich": payment_id,
            "SoTien": TOTAL,
            "ChuKy": sign_payload(f"{payment_id}:{TOTAL}"),
        },
    )
    third_amount = TOTAL + 1
    third = await hook(ctx, payment_id, amount=third_amount)

    assert second.json()["KetQua"] == "duplicate"
    assert third.json()["KetQua"] == "exception"
    assert len(await invoices_of(session, ctx.order_id)) == 1
    entry = (await exceptions_of(session))[0]
    refused = await ctx.client.post(
        f"{BASE}/payment-exceptions/{entry.id}/apply", json={}, headers=ctx.manager
    )
    assert refused.status_code == 422
    assert await order_state(session, ctx.order_id) == "Đã thanh toán"


@pytest.mark.anyio
async def test_the_exception_list_is_for_managers_only_and_filters_by_status(session):
    ctx, payment_id = await scene(session, qr=True)
    await hook(ctx, payment_id, amount=1000)

    cashier = await ctx.client.get(f"{BASE}/payment-exceptions", headers=ctx.cashier)
    bad_filter = await ctx.client.get(f"{BASE}/payment-exceptions?status=abc", headers=ctx.manager)
    refunded_only = await ctx.client.get(
        f"{BASE}/payment-exceptions?status=Đã hoàn tiền", headers=ctx.manager
    )

    assert cashier.status_code == 403 and bad_filter.status_code == 422
    assert refunded_only.json()["items"] == []


@pytest.mark.anyio
async def test_a_webhook_exception_row_cannot_be_pushed_into_verification_or_confirmed(session):
    ctx, payment_id = await scene(session, qr=True)
    await hook(ctx, payment_id, amount=TOTAL - 1000)
    exception_id = (await exceptions_of(session))[0].id

    asked = await ask_verification(ctx, exception_id)
    confirmed = await ctx.client.post(
        f"{BASE}/payments/{exception_id}/confirm-received", json={}, headers=ctx.manager
    )

    assert asked.status_code >= 400 and confirmed.status_code >= 400
    assert await order_state(session, ctx.order_id) == "Chờ xác nhận thanh toán"
    assert await invoices_of(session, ctx.order_id) == []
