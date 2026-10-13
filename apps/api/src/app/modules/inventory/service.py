"""Inventory service — receipts, issues, stocktakes."""

from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.inventory.costing import average_costs
from app.modules.inventory.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    IngredientLot,
    StockIssue,
    StockIssueLine,
    StockMovement,
    Stocktake,
    StocktakeLine,
)
from app.modules.inventory.stock import (
    StockChange,
    active_held_quantity,
    apply_stock_movement,
    lock_ingredients,
    lock_stocktake_gate,
    lots_for_fifo,
    refresh_lot_statuses,
    sellable_available,
    today_local,
)
from app.modules.settings.service import effective_business_day_start
from app.shared import business_date
from app.shared.audit import SystemAuditLog
from app.shared.enums import (
    LotStatus,
    OrderLineStatus,
    ReceiptStatus,
    StockIssueSource,
    StockMovementType,
    StocktakeStatus,
)


async def _bd(session: AsyncSession, moment: datetime) -> date:
    start = await effective_business_day_start(session, moment)
    return business_date.business_date_of(moment, start)


def _receipt_snapshot(receipt: GoodsReceipt, lines: list[GoodsReceiptLine]) -> dict:
    return {
        "TrangThai": receipt.status,
        "MaNCC": receipt.supplier_id,
        "TongTien": float(receipt.total or 0),
        "DongNhap": [
            {
                "MaChiTietNhap": line.id,
                "MaNguyenLieu": line.ingredient_id,
                "SoLuong": float(line.quantity),
                "DonGia": float(line.unit_price),
            }
            for line in lines
        ],
    }


async def _receipt_lines(session: AsyncSession, receipt_id: int) -> list[GoodsReceiptLine]:
    return list(
        (
            await session.execute(
                select(GoodsReceiptLine)
                .where(GoodsReceiptLine.receipt_id == receipt_id)
                .order_by(GoodsReceiptLine.id)
            )
        )
        .scalars()
        .all()
    )


async def _lot_has_outflow(session: AsyncSession, lot: IngredientLot) -> bool:
    """FR-INV-02: has anything but the receiving movement touched this lot?"""
    touched = (
        await session.execute(
            select(StockMovement.id)
            .where(
                StockMovement.lot_id == lot.id,
                StockMovement.kind != StockMovementType.NHAP.value,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    original = lot.received_quantity
    return touched is not None or Decimal(str(lot.quantity_remaining)) != Decimal(str(original))


# Receipts
async def create_receipt(
    session: AsyncSession,
    actor_id: int,
    supplier_id: int | None,
    receipt_date: datetime | None,
    lines: list[dict],
) -> GoodsReceipt:
    config = await lock_stocktake_gate(session)
    await refresh_lot_statuses(session, config.expiry_warning_days)
    await lock_ingredients(session, [line["ingredient_id"] for line in lines])
    operation_bd = await _bd(session, business_date.now())
    if supplier_id is not None:
        from app.modules.catalog.models import Supplier

        sup = await session.get(Supplier, supplier_id)
        if sup is None or sup.is_deleted:
            raise BusinessRuleError("Nhà cung cấp không tồn tại.")
    receipt = GoodsReceipt(
        supplier_id=supplier_id,
        receipt_date=receipt_date or business_date.now(),
        status="Nháp",
        created_by=actor_id,
    )
    session.add(receipt)
    await session.flush()
    # Validate no duplicate ingredient in same receipt (#13 pattern)
    seen = set()
    for _ln in lines:
        iid = _ln.get("ingredient_id")
        if iid in seen:
            raise BusinessRuleError("Nguyên liệu trùng lặp trong cùng phiếu.")
        seen.add(iid)
    for ln in lines:
        ingredient_id = ln["ingredient_id"]
        qty = Decimal(str(ln["quantity"]))
        if qty <= 0:
            raise BusinessRuleError("Số lượng phải > 0.")
        raw_factor = ln.get("conversion_factor")
        if raw_factor is not None:
            try:
                factor = Decimal(str(raw_factor))
            except Exception as exc:
                raise BusinessRuleError("Hệ số quy đổi không hợp lệ.") from exc
            if factor <= 0:
                raise BusinessRuleError("Hệ số quy đổi phải > 0.")
        else:
            factor = Decimal(1)
        qty_std = qty * factor
        if qty_std <= 0:
            raise BusinessRuleError("Số lượng quy chuẩn phải > 0.")
        unit_price = Decimal(str(ln.get("unit_price") or 0))
        if unit_price < 0:
            raise BusinessRuleError("Đơn giá không được âm.")
        from app.modules.catalog.models import Ingredient

        ing = await session.get(Ingredient, ingredient_id)
        if ing is None:
            raise BusinessRuleError("Nguyên liệu không tồn tại.")
        gl = GoodsReceiptLine(
            receipt_id=receipt.id,
            ingredient_id=ingredient_id,
            quantity=qty_std,
            unit_price=unit_price,
            original_purchase_unit=ln.get("purchase_unit"),
            conversion_factor=factor,
            total=qty_std * unit_price,
        )
        session.add(gl)
        await session.flush()
        # create lot
        lot = IngredientLot(
            ingredient_id=ingredient_id,
            receipt_line_id=gl.id,
            quantity_remaining=qty_std,
            status="Còn hạn",
            received_at=receipt.receipt_date,
            is_adjustment=False,
            received_quantity=qty_std,
            unit_price=unit_price,
            expiry_date=(receipt.receipt_date.date() + timedelta(days=ing.shelf_days))
            if ing.shelf_days
            else None,
        )
        session.add(lot)
        await session.flush()
        # ledger
        await apply_stock_movement(
            session,
            StockChange(
                ingredient_id=ingredient_id,
                delta=qty_std,
                kind="Nhập",
                business_date=operation_bd,
                source_receipt_line_id=gl.id,
                lot_id=lot.id,
            ),
            actor_id=actor_id,
        )
        receipt.total = receipt.total + gl.total
        # Mark unit locked once any receipt exists (BR-CAT)
        if not ing.unit_locked:
            ing.unit_locked = True
    await session.flush()
    await refresh_lot_statuses(session, config.expiry_warning_days)
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CREATE_RECEIPT",
            target_entity="PHIEU_NHAP_KHO",
            target_id=str(receipt.id),
            after=_receipt_snapshot(receipt, await _receipt_lines(session, receipt.id)),
        )
    )
    await session.flush()
    return receipt


async def cancel_receipt(session: AsyncSession, actor_id: int, receipt_id: int) -> None:
    """FR-INV-02: cancel only when no lot of the receipt has been drawn or held.

    The cancellation is a negative "Nhập" movement on the receipt line, so it satisfies
    the ledger CHECK (every type points at its own source document).
    """
    config = await lock_stocktake_gate(session)
    await refresh_lot_statuses(session, config.expiry_warning_days)
    operation_bd = await _bd(session, business_date.now())

    receipt = await session.get(GoodsReceipt, receipt_id)
    if receipt is None:
        raise NotFoundError("Không tìm thấy phiếu nhập.")
    if receipt.status == ReceiptStatus.DA_HUY.value:
        raise BusinessRuleError("Phiếu đã được hủy trước đó.")
    if receipt.status != ReceiptStatus.NHAP.value:
        raise BusinessRuleError("Chỉ được hủy phiếu ở trạng thái Nháp.")
    lines = await _receipt_lines(session, receipt_id)
    before = _receipt_snapshot(receipt, lines)
    await lock_ingredients(session, [line.ingredient_id for line in lines])
    lots: list[tuple[GoodsReceiptLine, IngredientLot]] = []
    for gl in lines:
        lot = (
            await session.execute(
                select(IngredientLot).where(IngredientLot.receipt_line_id == gl.id)
            )
        ).scalar_one_or_none()
        if lot is None:
            continue
        if await active_held_quantity(session, lot.id) > 0:
            raise BusinessRuleError("Lô nguyên liệu đang được giữ cho món.")
        if await _lot_has_outflow(session, lot):
            raise BusinessRuleError(
                "Đã có giao dịch xuất kho liên quan, phải điều chỉnh qua kiểm kê định kỳ."
            )
        lots.append((gl, lot))

    from app.modules.catalog.models import Ingredient

    affected_ingredient_ids: list[int] = []
    for gl, lot in lots:
        remaining = Decimal(str(lot.quantity_remaining))
        ing = await session.get(Ingredient, gl.ingredient_id)
        if ing is None or Decimal(str(ing.stock_qty)) < remaining:
            raise BusinessRuleError("Không đủ tồn kho để hủy phiếu.")
        lot.quantity_remaining = Decimal("0")
        lot.status = LotStatus.DA_DUNG_HET.value
        ing.stock_qty = ing.stock_qty - remaining
        session.add(
            StockMovement(
                ingredient_id=gl.ingredient_id,
                lot_id=lot.id,
                kind=StockMovementType.NHAP.value,
                qty=-remaining,
                balance_after=ing.stock_qty,
                business_date=operation_bd,
                receipt_line_id=gl.id,
                performed_by=actor_id,
            )
        )
        affected_ingredient_ids.append(gl.ingredient_id)
    receipt.status = ReceiptStatus.DA_HUY.value
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CANCEL_RECEIPT",
            target_entity="PHIEU_NHAP_KHO",
            target_id=str(receipt_id),
            before=before,
            after=_receipt_snapshot(receipt, lines),
        )
    )
    await session.flush()
    if affected_ingredient_ids:
        await recompute_automatic_out_of_stock(session, affected_ingredient_ids)


async def update_receipt(
    session: AsyncSession, actor_id: int, receipt_id: int, lines: list[dict]
) -> None:
    """FR-INV-02: correct quantity/unit price on lines that have not been drawn yet.

    Editing is only allowed while the receipt is still "Nháp" and its lot has not
    been touched by any later issue/order/stocktake. The edited quantity is the
    already-converted standard-unit quantity stored on the line.
    """
    config = await lock_stocktake_gate(session)
    await refresh_lot_statuses(session, config.expiry_warning_days)
    target_lines = [await session.get(GoodsReceiptLine, line["line_id"]) for line in lines]
    await lock_ingredients(
        session, [line.ingredient_id for line in target_lines if line is not None]
    )
    operation_bd = await _bd(session, business_date.now())
    receipt = await session.get(GoodsReceipt, receipt_id)
    if receipt is None:
        raise NotFoundError("Không tìm thấy phiếu nhập.")
    if receipt.status != ReceiptStatus.NHAP.value:
        raise BusinessRuleError("Chỉ được sửa phiếu ở trạng thái Nháp.")
    before = _receipt_snapshot(receipt, await _receipt_lines(session, receipt_id))
    from app.modules.catalog.models import Ingredient

    for ln in lines:
        line_id = ln["line_id"]
        new_qty = Decimal(str(ln["quantity"]))
        new_price = Decimal(str(ln["unit_price"]))
        if new_qty <= 0:
            raise BusinessRuleError("Số lượng phải > 0.")
        if new_price < 0:
            raise BusinessRuleError("Đơn giá không được âm.")
        gl = await session.get(GoodsReceiptLine, line_id)
        if gl is None or gl.receipt_id != receipt_id:
            raise BusinessRuleError("Dòng phiếu nhập không hợp lệ.")
        lot = (
            await session.execute(
                select(IngredientLot).where(IngredientLot.receipt_line_id == gl.id)
            )
        ).scalar_one_or_none()
        if lot is None:
            raise BusinessRuleError("Không tìm thấy lô hàng của dòng phiếu nhập.")
        if await active_held_quantity(session, lot.id) > 0:
            raise BusinessRuleError("Lô nguyên liệu đang được giữ cho món.")
        if await _lot_has_outflow(session, lot):
            raise BusinessRuleError(
                "Đã có giao dịch xuất kho liên quan, phải điều chỉnh qua kiểm kê định kỳ."
            )
        delta = new_qty - Decimal(str(gl.quantity))
        ing = await session.get(Ingredient, gl.ingredient_id)
        if ing is not None and Decimal(str(ing.stock_qty)) + delta < 0:
            raise BusinessRuleError("Tồn kho sau khi sửa không được âm.")
        gl.quantity = new_qty
        gl.unit_price = new_price
        gl.total = new_qty * new_price
        lot.quantity_remaining = new_qty
        lot.received_quantity = new_qty
        lot.unit_price = new_price
        if ing is not None:
            ing.stock_qty = ing.stock_qty + delta
        if delta != 0:
            session.add(
                StockMovement(
                    ingredient_id=gl.ingredient_id,
                    lot_id=lot.id,
                    kind=StockMovementType.NHAP.value,
                    qty=delta,
                    balance_after=ing.stock_qty if ing is not None else 0,
                    business_date=operation_bd,
                    receipt_line_id=gl.id,
                    performed_by=actor_id,
                )
            )
        await session.flush()
        await recompute_automatic_out_of_stock(session, [gl.ingredient_id])
    after_lines = await _receipt_lines(session, receipt_id)
    receipt.total = sum((line.total for line in after_lines), Decimal(0))
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="UPDATE_RECEIPT",
            target_entity="PHIEU_NHAP_KHO",
            target_id=str(receipt_id),
            before=before,
            after=_receipt_snapshot(receipt, after_lines),
        )
    )
    await session.flush()


async def list_receipts(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    supplier_id: int | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[GoodsReceipt], int]:
    filters = []
    if supplier_id is not None:
        filters.append(GoodsReceipt.supplier_id == supplier_id)
    if status is not None:
        filters.append(GoodsReceipt.status == status)
    if date_from is not None:
        filters.append(func.date(GoodsReceipt.receipt_date) >= date_from)
    if date_to is not None:
        filters.append(func.date(GoodsReceipt.receipt_date) <= date_to)
    total = (
        await session.execute(select(func.count(GoodsReceipt.id)).where(*filters))
    ).scalar_one()
    q = (
        select(GoodsReceipt)
        .where(*filters)
        .order_by(GoodsReceipt.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    r = await session.execute(q)
    return list(r.scalars().all()), total


# Issues
async def create_issue(
    session: AsyncSession, actor_id: int, reason: str, lines: list[dict]
) -> StockIssue:
    config = await lock_stocktake_gate(session)
    await refresh_lot_statuses(session, config.expiry_warning_days)
    await lock_ingredients(session, [line["ingredient_id"] for line in lines])
    operation_bd = await _bd(session, business_date.now())
    issue = StockIssue(
        reason=reason,
        status="Nháp",
        issue_date=business_date.now(),
        created_by=actor_id,
        source="Nguyên liệu",
    )
    session.add(issue)
    await session.flush()
    for ln in lines:
        iid = ln["ingredient_id"]
        qty = Decimal(str(ln["quantity"]))
        il = StockIssueLine(
            issue_id=issue.id, ingredient_id=iid, quantity=qty, estimated_cost=Decimal("0")
        )
        session.add(il)
        await session.flush()
        _allow_exp = "hết hạn" in reason.lower() if reason else False
        await apply_stock_movement(
            session,
            StockChange(
                ingredient_id=iid,
                delta=-qty,
                kind="Xuất thủ công",
                allow_expired=_allow_exp,
                business_date=operation_bd,
                source_issue_line_id=il.id,
            ),
            actor_id=actor_id,
        )
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="MANUAL_STOCK_ISSUE",
            target_entity="PHIEU_XUAT_KHO",
            target_id=str(issue.id),
            after={
                "LyDo": reason,
                "NguonXuat": issue.source,
                "DongXuat": [
                    {"MaNguyenLieu": ln["ingredient_id"], "SoLuong": float(ln["quantity"])}
                    for ln in lines
                ],
            },
        )
    )
    await session.flush()
    return issue


_PREPARED_LINE_STATUSES = (
    OrderLineStatus.DA_XAC_NHAN_XONG.value,
    OrderLineStatus.DA_PHUC_VU.value,
)
_QUANTITY_STEP = Decimal("0.0001")


async def _net_consumption(
    session: AsyncSession, line_ids: list[int]
) -> dict[int, dict[int, Decimal]]:
    """Ingredients each order line drew and never got back, per line and ingredient."""
    if not line_ids:
        return {}
    rows = await session.execute(
        select(
            StockMovement.order_line_id,
            StockMovement.ingredient_id,
            func.sum(StockMovement.qty),
        )
        .where(
            StockMovement.order_line_id.in_(line_ids),
            StockMovement.kind.in_(
                [StockMovementType.TRU_TU_DONG.value, StockMovementType.HOAN_KHO.value]
            ),
        )
        .group_by(StockMovement.order_line_id, StockMovement.ingredient_id)
    )
    net: dict[int, dict[int, Decimal]] = {}
    for line_id, ingredient_id, total in rows:
        drawn = -Decimal(str(total or 0))
        if drawn > 0:
            net.setdefault(int(line_id), {})[int(ingredient_id)] = drawn
    return net


async def _written_off_servings(session: AsyncSession, line_ids: list[int]) -> dict[int, int]:
    """Servings already written off per order line.

    A voucher repeats the servings on each ingredient row of the line, so they are counted
    once per voucher (BR: "không cộng lặp qua các dòng nguyên liệu").
    """
    if not line_ids:
        return {}
    rows = await session.execute(
        select(
            StockIssueLine.issue_id,
            StockIssueLine.order_line_id,
            func.max(StockIssueLine.servings),
        )
        .join(StockIssue, StockIssue.id == StockIssueLine.issue_id)
        .where(
            StockIssue.source == StockIssueSource.MON_DA_CHE_BIEN.value,
            StockIssueLine.order_line_id.in_(line_ids),
        )
        .group_by(StockIssueLine.issue_id, StockIssueLine.order_line_id)
    )
    written: dict[int, int] = {}
    for _issue_id, line_id, servings in rows:
        written[int(line_id)] = written.get(int(line_id), 0) + int(servings or 0)
    return written


async def create_dish_issue(
    session: AsyncSession,
    actor_id: int,
    reason: str,
    note: str | None,
    lines: list[dict],
) -> tuple[StockIssue, list[dict]]:
    """FR-INV-05/06: write off prepared dishes (source "Món đã chế biến").

    The sale already drew the ingredients (FR-INV-03), so the voucher moves no stock and books
    no movement: it records, per ingredient of the dish, the quantity of that original
    consumption that `servings` stand for. All lines succeed or none does.
    """
    from app.modules.sales.models import Order, OrderLine

    await lock_stocktake_gate(session)
    requested: dict[int, int] = {}
    for item in lines:
        line_id = int(item["order_line_id"])
        requested[line_id] = requested.get(line_id, 0) + int(item["servings"])
    line_ids = sorted(requested)
    query = (
        select(OrderLine, Order)
        .join(Order, Order.id == OrderLine.order_id)
        .where(OrderLine.id.in_(line_ids))
        .order_by(OrderLine.id)
        .execution_options(populate_existing=True)
    )
    if session.get_bind().dialect.name == "mysql":
        query = query.with_for_update()
    found = {line.id: (line, order) for line, order in (await session.execute(query)).all()}
    if set(found) != set(line_ids):
        raise NotFoundError("Không tìm thấy dòng món.")
    consumption = await _net_consumption(session, line_ids)
    already = await _written_off_servings(session, line_ids)

    for line_id in line_ids:
        line = found[line_id][0]
        if line.status not in _PREPARED_LINE_STATUSES:
            raise BusinessRuleError(
                "Chỉ xuất hủy món đã chế biến (đã xác nhận xong hoặc đã phục vụ); "
                "món chờ làm được hoàn kho theo FR-INV-04."
            )
        if line.id not in consumption:
            raise BusinessRuleError("Dòng món không có tiêu hao nguyên liệu để xuất hủy.")
        left = int(line.quantity) - already.get(line_id, 0)
        if requested[line_id] > left:
            raise BusinessRuleError(
                f"Dòng món {line_id} chỉ còn {max(left, 0)} suất có thể xuất hủy."
            )

    voucher = StockIssue(
        reason=reason,
        status="Nháp",
        issue_date=business_date.now(),
        created_by=actor_id,
        note=note,
        source=StockIssueSource.MON_DA_CHE_BIEN.value,
    )
    session.add(voucher)
    await session.flush()
    prices: dict[tuple[int, int], Decimal] = {}
    for line_id in line_ids:
        line, order = found[line_id]
        month = order.business_date.year * 100 + order.business_date.month
        ingredient_ids = sorted(consumption[line_id])
        for ingredient_id, price in (await average_costs(session, month, ingredient_ids)).items():
            prices[(month, ingredient_id)] = price
        booked = 0
        for ingredient_id in ingredient_ids:
            quantity = (
                consumption[line_id][ingredient_id] * requested[line_id] / int(line.quantity)
            ).quantize(_QUANTITY_STEP, rounding=ROUND_HALF_UP)
            if quantity <= 0:
                continue
            price_for = prices.get((month, ingredient_id))
            session.add(
                StockIssueLine(
                    issue_id=voucher.id,
                    ingredient_id=ingredient_id,
                    quantity=quantity,
                    estimated_cost=(
                        (quantity * price_for).quantize(_QUANTITY_STEP, rounding=ROUND_HALF_UP)
                        if price_for is not None
                        else Decimal(0)
                    ),
                    order_line_id=line_id,
                    servings=requested[line_id],
                )
            )
            booked += 1
        if booked == 0:
            raise BusinessRuleError("Lượng tiêu hao của số suất này quá nhỏ để ghi nhận.")
    summary = [
        {
            "MaChiTietOrder": line_id,
            "SoSuatHuy": requested[line_id],
            "SoSuatConLai": int(found[line_id][0].quantity)
            - already.get(line_id, 0)
            - requested[line_id],
        }
        for line_id in line_ids
    ]
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="DISH_STOCK_WRITE_OFF",
            target_entity="PHIEU_XUAT_KHO",
            target_id=str(voucher.id),
            before={
                "DongMon": [
                    {
                        "MaChiTietOrder": line_id,
                        "SoSuatDaHuy": already.get(line_id, 0),
                        "SoSuatTieuHao": int(found[line_id][0].quantity),
                    }
                    for line_id in line_ids
                ]
            },
            after={
                "LyDo": reason,
                "NguonXuat": voucher.source,
                "DongMon": [
                    {
                        "MaChiTietOrder": line_id,
                        "SoSuatHuy": requested[line_id],
                        "SoSuatDaHuy": already.get(line_id, 0) + requested[line_id],
                    }
                    for line_id in line_ids
                ],
            },
        )
    )
    await session.flush()
    return voucher, summary


async def list_writable_dish_lines(
    session: AsyncSession, day: date | None, page: int, page_size: int
) -> tuple[list[dict], int]:
    """Prepared dish lines of one Business Date that still have servings to write off."""
    from app.modules.catalog.models import Dish
    from app.modules.sales.models import Order, OrderLine

    if day is None:
        day = await _bd(session, business_date.now())
    rows = (
        await session.execute(
            select(OrderLine, Order, Dish.name)
            .join(Order, Order.id == OrderLine.order_id)
            .join(Dish, Dish.id == OrderLine.dish_id)
            .where(Order.business_date == day, OrderLine.status.in_(_PREPARED_LINE_STATUSES))
            .order_by(OrderLine.id)
        )
    ).all()
    line_ids = [line.id for line, _, _ in rows]
    consumption = await _net_consumption(session, line_ids)
    written = await _written_off_servings(session, line_ids)
    items = []
    for line, order, dish_name in rows:
        left = int(line.quantity) - written.get(line.id, 0)
        if line.id not in consumption or left <= 0:
            continue
        items.append(
            {
                "MaChiTietOrder": line.id,
                "MaOrder": order.id,
                "MaOrderHienThi": order.display_code,
                "MaMon": line.dish_id,
                "TenMon": dish_name,
                "TrangThai": line.status,
                "BusinessDate": order.business_date.isoformat(),
                "SoLuong": int(line.quantity),
                "SoSuatDaHuy": written.get(line.id, 0),
                "SoSuatConLai": left,
            }
        )
    start = (page - 1) * page_size
    return items[start : start + page_size], len(items)


async def list_issues(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    reason: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[StockIssue], int]:
    filters = []
    if reason is not None:
        filters.append(StockIssue.reason == reason)
    if date_from is not None:
        filters.append(func.date(StockIssue.created_at) >= date_from)
    if date_to is not None:
        filters.append(func.date(StockIssue.created_at) <= date_to)
    total = (await session.execute(select(func.count(StockIssue.id)).where(*filters))).scalar_one()
    q = (
        select(StockIssue)
        .where(*filters)
        .order_by(StockIssue.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    r = await session.execute(q)
    return list(r.scalars().all()), total


# Stocktakes
async def _current_stocktake(session: AsyncSession, stocktake_id: int) -> Stocktake | None:
    query = select(Stocktake).where(Stocktake.id == stocktake_id)
    if session.get_bind().dialect.name == "mysql":
        query = query.with_for_update().execution_options(populate_existing=True)
    return (await session.execute(query)).scalar_one_or_none()


async def create_stocktake(session: AsyncSession, actor_id: int) -> Stocktake:
    await lock_stocktake_gate(session, allow_active=True)
    from app.modules.sales.models import ItemHold

    live_hold = (
        await session.execute(
            select(ItemHold.id)
            .where(ItemHold.status == "Đang giữ", ItemHold.expires_at > business_date.now())
            .limit(1)
        )
    ).scalar_one_or_none()
    if live_hold is not None:
        raise BusinessRuleError(
            "Còn lượt chọn chưa gửi hoặc giữ chỗ còn hiệu lực, hãy xử lý trước khi kiểm kê."
        )
    active_query = select(Stocktake.id).where(
        Stocktake.status == StocktakeStatus.DANG_KIEM_KE.value
    )
    if session.get_bind().dialect.name == "mysql":
        active_query = active_query.with_for_update()
    active = (await session.execute(active_query)).scalar_one_or_none()
    if active is not None:
        raise BusinessRuleError("Đã có phiếu kiểm kê đang hoạt động.")
    st = Stocktake(
        status=StocktakeStatus.DANG_KIEM_KE.value,
        stocktake_date=business_date.now(),
        performed_by=actor_id,
    )
    session.add(st)
    await session.flush()
    return st


async def list_stocktakes(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[Stocktake], int]:
    filters = []
    if status is not None:
        filters.append(Stocktake.status == status)
    if date_from is not None:
        filters.append(func.date(Stocktake.stocktake_date) >= date_from)
    if date_to is not None:
        filters.append(func.date(Stocktake.stocktake_date) <= date_to)
    total = (await session.execute(select(func.count(Stocktake.id)).where(*filters))).scalar_one()
    q = (
        select(Stocktake)
        .where(*filters)
        .order_by(Stocktake.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    r = await session.execute(q)
    return list(r.scalars().all()), total


async def record_counts(
    session: AsyncSession, stocktake_id: int, counts: list[tuple[int, Decimal]]
) -> None:
    await lock_stocktake_gate(session, allow_active=True)
    st = await _current_stocktake(session, stocktake_id)
    if st is None:
        raise NotFoundError("Không tìm thấy phiếu kiểm kê.")
    if st.status != StocktakeStatus.DANG_KIEM_KE.value:
        raise BusinessRuleError("Phiếu kiểm kê đã chốt, không thể ghi nhận thêm.")
    await lock_ingredients(session, [ingredient_id for ingredient_id, _ in counts])
    seen_ids: set[int] = set()
    for iid, actual in counts:
        if iid in seen_ids:
            raise BusinessRuleError("Nguyên liệu trùng lặp trong cùng phiếu kiểm kê.")
        seen_ids.add(iid)
        if Decimal(str(actual)) < 0:
            raise BusinessRuleError("Tồn thực tế không được âm.")
        existing_lines = (
            (
                await session.execute(
                    select(StocktakeLine)
                    .where(
                        StocktakeLine.stocktake_id == stocktake_id,
                        StocktakeLine.ingredient_id == iid,
                    )
                    .order_by(StocktakeLine.id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
            )
            .scalars()
            .all()
        )
        if existing_lines:
            existing_lines[0].actual_qty = actual
            for duplicate in existing_lines[1:]:
                await session.delete(duplicate)
            continue
        from app.modules.catalog.models import Ingredient

        ing = await session.get(Ingredient, iid)
        session.add(
            StocktakeLine(
                stocktake_id=stocktake_id,
                ingredient_id=iid,
                system_qty=Decimal(str(ing.stock_qty)) if ing else Decimal(0),
                actual_qty=actual,
            )
        )
    await session.flush()


async def _latest_valid_lot(session: AsyncSession, ingredient_id: int) -> IngredientLot | None:
    """BR-LOT-02: the most recently received lot that still counts as valid stock."""
    return (
        (
            await session.execute(
                select(IngredientLot)
                .where(
                    IngredientLot.ingredient_id == ingredient_id,
                    IngredientLot.quantity_remaining > 0,
                    IngredientLot.status.in_(
                        [LotStatus.CON_HAN.value, LotStatus.SAP_HET_HAN.value]
                    ),
                )
                .order_by(IngredientLot.received_at.desc(), IngredientLot.id.desc())
                .limit(1)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        )
        .scalars()
        .first()
    )


async def confirm_stocktake(session: AsyncSession, actor_id: int, stocktake_id: int) -> None:
    """FR-INV-08/09, BR-LOT-02: book the counted differences lot by lot in one transaction."""
    from app.modules.catalog.models import Ingredient

    config = await lock_stocktake_gate(session, allow_active=True)
    await refresh_lot_statuses(session, config.expiry_warning_days)
    operation_bd = await _bd(session, business_date.now())
    st = await _current_stocktake(session, stocktake_id)
    if st is None:
        raise NotFoundError("Không tìm thấy phiếu kiểm kê.")
    if st.status != StocktakeStatus.DANG_KIEM_KE.value:
        raise BusinessRuleError("Phiếu kiểm kê đã được xác nhận trước đó.")
    lines = list(
        (
            await session.execute(
                select(StocktakeLine)
                .where(StocktakeLine.stocktake_id == stocktake_id)
                .order_by(StocktakeLine.ingredient_id)
            )
        )
        .scalars()
        .all()
    )
    if not lines:
        raise BusinessRuleError("Chưa ghi nhận kiểm kê.")
    await lock_ingredients(session, [line.ingredient_id for line in lines])

    # NFR-20: the count was taken against the book stock; writers are blocked while the
    # session is open, so a different figure now means something bypassed the lock.
    for line in lines:
        ingredient = await session.get(Ingredient, line.ingredient_id)
        if ingredient is None or Decimal(str(ingredient.stock_qty)) != Decimal(
            str(line.system_qty)
        ):
            raise BusinessRuleError(
                "Tồn kho đã thay đổi trong phiên kiểm kê, vui lòng kiểm kê lại."
            )

    before = {"TrangThai": st.status}
    shortage_lines: list[tuple[StocktakeLine, Decimal]] = []
    affected_ingredient_ids: list[int] = []
    for line in lines:
        affected_ingredient_ids.append(line.ingredient_id)
        actual = Decimal(str(line.actual_qty))
        diff = actual - Decimal(str(line.system_qty))
        all_lots = (
            (
                await session.execute(
                    select(IngredientLot)
                    .where(IngredientLot.ingredient_id == line.ingredient_id)
                    .order_by(IngredientLot.id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
            )
            .scalars()
            .all()
        )
        held_by_lot = {lot.id: await active_held_quantity(session, lot.id) for lot in all_lots}
        if actual < sum(held_by_lot.values(), Decimal(0)) or any(
            Decimal(str(lot.quantity_remaining)) < held_by_lot[lot.id] for lot in all_lots
        ):
            raise BusinessRuleError("Tồn thực tế thấp hơn số lượng đang được giữ cho món.")
        if diff == 0:
            continue
        ingredient = await session.get(Ingredient, line.ingredient_id)
        assert ingredient is not None
        if diff < 0:
            # FIFO over every lot with stock left, expired ones included (BR-LOT-02).
            need = -diff
            for drawn in await lots_for_fifo(session, line.ingredient_id, allow_expired=True):
                if need <= 0:
                    break
                free = max(
                    Decimal(0), Decimal(str(drawn.quantity_remaining)) - held_by_lot[drawn.id]
                )
                take = min(free, need)
                if take <= 0:
                    continue
                drawn.quantity_remaining = Decimal(str(drawn.quantity_remaining)) - take
                ingredient.stock_qty = Decimal(str(ingredient.stock_qty)) - take
                session.add(
                    StockMovement(
                        ingredient_id=line.ingredient_id,
                        lot_id=drawn.id,
                        kind=StockMovementType.DIEU_CHINH_KIEM_KE.value,
                        qty=-take,
                        balance_after=ingredient.stock_qty,
                        business_date=operation_bd,
                        stocktake_line_id=line.id,
                        performed_by=actor_id,
                    )
                )
                need -= take
            # Book stock that no lot backs cannot be traced to a lot; settle the total.
            ingredient.stock_qty = actual
            shortage_lines.append((line, -diff))
        else:
            lot: IngredientLot | None = await _latest_valid_lot(session, line.ingredient_id)
            if lot is None:
                lot = IngredientLot(
                    ingredient_id=line.ingredient_id,
                    receipt_line_id=None,
                    quantity_remaining=Decimal(0),
                    received_quantity=diff,
                    status=LotStatus.CON_HAN.value,
                    received_at=st.stocktake_date,
                    expiry_date=None,
                    is_adjustment=True,
                    unit_price=Decimal(0),
                )
                session.add(lot)
                await session.flush()
            lot.quantity_remaining = Decimal(str(lot.quantity_remaining)) + diff
            ingredient.stock_qty = Decimal(str(ingredient.stock_qty)) + diff
            session.add(
                StockMovement(
                    ingredient_id=line.ingredient_id,
                    lot_id=lot.id,
                    kind=StockMovementType.DIEU_CHINH_KIEM_KE.value,
                    qty=diff,
                    balance_after=ingredient.stock_qty,
                    business_date=operation_bd,
                    stocktake_line_id=line.id,
                    performed_by=actor_id,
                )
            )
    st.status = StocktakeStatus.DA_CHOT.value
    await session.flush()

    voucher_id: int | None = None
    if shortage_lines:
        # The voucher only classifies the loss (FR-INV-09); the ledger rows above already
        # moved the stock, so it creates no movement of its own.
        voucher = StockIssue(
            reason="Hao hụt",
            status="Nháp",
            issue_date=business_date.now(),
            created_by=actor_id,
            source="Kiểm kê",
            stocktake_id=stocktake_id,
        )
        session.add(voucher)
        await session.flush()
        for line, quantity in shortage_lines:
            session.add(
                StockIssueLine(
                    issue_id=voucher.id,
                    ingredient_id=line.ingredient_id,
                    quantity=quantity,
                    estimated_cost=Decimal(0),
                )
            )
        voucher_id = voucher.id
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CONFIRM_STOCKTAKE",
            target_entity="PHIEU_KIEM_KE",
            target_id=str(stocktake_id),
            before=before,
            after={
                "TrangThai": st.status,
                "PhieuXuatHuy": voucher_id,
                "ChenhLech": [
                    {
                        "MaNguyenLieu": line.ingredient_id,
                        "TonHeThong": float(line.system_qty),
                        "TonThucTe": float(line.actual_qty),
                    }
                    for line in lines
                    if line.actual_qty != line.system_qty
                ],
            },
        )
    )
    await session.flush()
    await refresh_lot_statuses(session, config.expiry_warning_days)
    if affected_ingredient_ids:
        await recompute_automatic_out_of_stock(session, affected_ingredient_ids)


async def cancel_stocktake(session: AsyncSession, actor_id: int, stocktake_id: int) -> None:
    await lock_stocktake_gate(session, allow_active=True)
    stocktake = await _current_stocktake(session, stocktake_id)
    if stocktake is None:
        raise NotFoundError("Không tìm thấy phiếu kiểm kê.")
    if stocktake.status != StocktakeStatus.DANG_KIEM_KE.value:
        raise BusinessRuleError("Phiếu kiểm kê không còn hoạt động.")
    before = {"TrangThai": stocktake.status}
    stocktake.status = StocktakeStatus.DA_HUY.value
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CANCEL_STOCKTAKE",
            target_entity="PHIEU_KIEM_KE",
            target_id=str(stocktake_id),
            before=before,
            after={"TrangThai": stocktake.status},
        )
    )
    await session.flush()


async def _stock_row(ing, default_threshold: float, available: dict[int, Decimal], held: Decimal):
    threshold = float(ing.min_stock) if ing.min_stock is not None else default_threshold
    sellable = available.get(ing.id, Decimal(0))
    return {
        "MaNguyenLieu": ing.id,
        "TenNguyenLieu": ing.name,
        "DonViTinh": ing.unit,
        "SoLuongTon": float(ing.stock_qty),
        "SoLuongDuDieuKienBan": float(sellable + held),
        "SoLuongGiu": float(held),
        "SoLuongKhaDung": float(sellable),
        "MucTonToiThieuApDung": threshold,
        "CanhBaoTonThap": float(sellable) < threshold,
    }


async def list_stock(
    session,
    search: str | None = None,
    alerting: bool | None = None,
    page: int = 1,
    page_size: int = 50,
):
    """FR-INV-07/12: book stock, sellable stock, holds, availability and the low-stock flag.

    The alert compares the *available* quantity with the threshold in force: the
    ingredient's own one, or the live system default when it has none (NULL, not 0).
    """
    from app.modules.catalog.models import Ingredient
    from app.modules.inventory.stock import held_by_ingredient
    from app.modules.settings.models import SystemConfig

    cfg = (await session.execute(select(SystemConfig))).scalar_one_or_none()
    if cfg is not None:
        await refresh_lot_statuses(session, cfg.expiry_warning_days)
    default = float(cfg.default_stock_threshold) if cfg else 5
    base = select(Ingredient).where(Ingredient.is_deleted.is_(False))
    if search:
        safe = search.replace("%", "\\%").replace("_", "\\_")
        base = base.where(Ingredient.name.ilike(f"%{safe}%", escape="\\"))
    ingredients = list((await session.execute(base.order_by(Ingredient.id))).scalars().all())
    ids = [ing.id for ing in ingredients]
    available = await sellable_available(session, ids)
    held = await held_by_ingredient(session, ids)
    rows = [
        await _stock_row(ing, default, available, held.get(ing.id, Decimal(0)))
        for ing in ingredients
    ]
    if alerting is not None:
        rows = [row for row in rows if row["CanhBaoTonThap"] == alerting]
    total = len(rows)
    start = (page - 1) * page_size
    return rows[start : start + page_size], total


async def list_lot_expiry(
    session: AsyncSession, *, page: int, page_size: int
) -> tuple[list[dict], int]:
    """FR-INV-14: every lot with its stored expiry status, refreshed on read."""
    from app.modules.catalog.models import Ingredient
    from app.modules.settings.models import SystemConfig

    config = (await session.execute(select(SystemConfig))).scalar_one_or_none()
    warning_days = config.expiry_warning_days if config else 3
    await refresh_lot_statuses(session, warning_days)
    base = (
        select(IngredientLot, Ingredient)
        .join(Ingredient, IngredientLot.ingredient_id == Ingredient.id)
        .where(Ingredient.is_deleted.is_(False))
    )
    total = (await session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        await session.execute(
            base.order_by(IngredientLot.id).offset((page - 1) * page_size).limit(page_size)
        )
    ).all()
    today = today_local()
    items = [
        {
            "MaLoNguyenLieu": lot.id,
            "MaNguyenLieu": ingredient.id,
            "TenNguyenLieu": ingredient.name,
            "SoLuongConLai": float(lot.quantity_remaining),
            "HanSuDung": lot.expiry_date,
            "SoNgayConLai": (lot.expiry_date - today).days if lot.expiry_date else None,
            "TrangThaiHanSuDung": lot.status,
        }
        for lot, ingredient in rows
    ]
    return items, total


async def recompute_automatic_out_of_stock(session, ingredient_ids: list[int]) -> list[int]:
    """Refresh the cached HetNguyenLieu flag of dishes whose active recipe uses these
    ingredients, from sellable stock net of live holds (FR-CAT-27, FR-INV-10)."""
    from app.modules.catalog.models import Dish, Recipe, RecipeItem
    from app.modules.catalog.versions import promote_due_versions
    from app.modules.inventory.stock import sellable_available
    from app.shared.enums import VersionStatus

    if not ingredient_ids:
        return []
    await promote_due_versions(session)
    affected_recipe_ids = {
        row.recipe_id
        for row in (
            await session.execute(
                select(RecipeItem).where(RecipeItem.ingredient_id.in_(ingredient_ids))
            )
        ).scalars()
    }
    if not affected_recipe_ids:
        return []
    recipes = (
        (
            await session.execute(
                select(Recipe).where(
                    Recipe.id.in_(affected_recipe_ids),
                    Recipe.status == VersionStatus.HIEU_LUC.value,
                )
            )
        )
        .scalars()
        .all()
    )
    if not recipes:
        return []
    all_items = (
        (
            await session.execute(
                select(RecipeItem).where(RecipeItem.recipe_id.in_([r.id for r in recipes]))
            )
        )
        .scalars()
        .all()
    )
    items_by_recipe: dict[int, list] = {}
    for it in all_items:
        items_by_recipe.setdefault(it.recipe_id, []).append(it)
    available = await sellable_available(session, sorted({it.ingredient_id for it in all_items}))
    out_of_stock: list[int] = []
    for recipe in recipes:
        enough = all(
            available[it.ingredient_id] >= Decimal(str(it.quantity))
            for it in items_by_recipe.get(recipe.id, [])
        )
        dish = await session.get(Dish, recipe.dish_id)
        if dish and not dish.is_deleted:
            dish.out_of_stock = not enough
            if not enough:
                out_of_stock.append(dish.id)
    await session.flush()
    return out_of_stock
