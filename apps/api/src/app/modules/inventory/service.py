"""Inventory service — receipts, issues, stocktakes."""

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.catalog.models import Ingredient, RecipeItem
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
    apply_stock_movement,
    ensure_no_open_stocktake,
    lock_ingredient,
    lock_stock_operations,
)
from app.modules.sales.models import OrderLine
from app.shared import business_date
from app.shared.audit import SystemAuditLog
from app.shared.enums import StocktakeStatus


def _bd():
    return business_date.business_date_of(business_date.now())


# Receipts
async def create_receipt(
    session: AsyncSession,
    actor_id: int,
    supplier_id: int | None,
    receipt_date: datetime | None,
    lines: list[dict],
) -> GoodsReceipt:
    await ensure_no_open_stocktake(session)
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
        ing = await lock_ingredient(session, ingredient_id)
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
        movements = await apply_stock_movement(
            session,
            StockChange(
                ingredient_id=ingredient_id,
                delta=qty_std,
                kind="Nhập",
                business_date=_bd(),
                source_receipt_line_id=gl.id,
            ),
            actor_id=actor_id,
        )
        for movement in movements:
            movement.lot_id = lot.id
        # Mark unit locked once any receipt exists (BR-CAT)
        if not ing.unit_locked:
            ing.unit_locked = True
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CREATE_RECEIPT",
            target_entity="PHIEU_NHAP_KHO",
            target_id=str(receipt.id),
        )
    )
    await session.flush()
    return receipt


async def _ensure_receipt_untouched(session: AsyncSession, receipt_id: int) -> None:
    """FR-INV-02: once stock left the lot or a hold points at it, correct via stocktake."""
    from app.modules.inventory.models import StockMovement
    from app.modules.sales.models import Reservation, ReservationDetail

    line_ids = select(GoodsReceiptLine.id).where(GoodsReceiptLine.receipt_id == receipt_id)
    lot_ids = select(IngredientLot.id).where(IngredientLot.receipt_line_id.in_(line_ids))
    used = (
        await session.execute(
            select(StockMovement.id)
            .where(StockMovement.lot_id.in_(lot_ids), StockMovement.qty < 0)
            .limit(1)
        )
    ).first()
    if used is not None:
        raise BusinessRuleError(
            "Phiếu nhập đã phát sinh xuất kho, phải điều chỉnh qua kiểm kê định kỳ."
        )
    held = (
        await session.execute(
            select(ReservationDetail.lot_id)
            .join(Reservation, Reservation.id == ReservationDetail.reservation_id)
            .where(
                ReservationDetail.lot_id.in_(lot_ids),
                Reservation.status == "Đang giữ",
                Reservation.expires_at > business_date.now().replace(tzinfo=None),
            )
            .limit(1)
        )
    ).first()
    if held is not None:
        raise BusinessRuleError("Lô của phiếu đang được giữ chỗ, không thể sửa/hủy phiếu.")


async def cancel_receipt(session: AsyncSession, actor_id: int, receipt_id: int) -> None:
    await ensure_no_open_stocktake(session)
    from app.shared.enums import StockMovementType

    await ensure_no_open_stocktake(session)
    receipt = await session.get(GoodsReceipt, receipt_id)
    if receipt is None:
        raise NotFoundError("Không tìm thấy phiếu nhập.")
    if receipt.status == "Đã hủy":
        raise BusinessRuleError("Phiếu đã được hủy trước đó.")
    if receipt.status != "Nháp":
        raise BusinessRuleError("Chỉ được hủy phiếu ở trạng thái Nháp.")
    await _ensure_receipt_untouched(session, receipt_id)
    lines = (
        (
            await session.execute(
                select(GoodsReceiptLine).where(GoodsReceiptLine.receipt_id == receipt_id)
            )
        )
        .scalars()
        .all()
    )
    affected_ingredient_ids: list[int] = []
    for gl in lines:
        lot = (
            await session.execute(
                select(IngredientLot).where(IngredientLot.receipt_line_id == gl.id)
            )
        ).scalar_one_or_none()
        if lot is None:
            continue
        # If lot has been partially/fully consumed, we can only cancel up to remaining
        remaining = Decimal(str(lot.quantity_remaining))
        original = Decimal(str(gl.quantity))
        consumed = original - remaining
        if consumed > 0 and remaining == 0:
            # fully drawn lot -> cannot cancel without negative stock
            raise BusinessRuleError("Không thể hủy phiếu đã xuất hết.")
        # Directly reverse the receipt lot: subtract remaining from ingredient total and lot
        from app.modules.catalog.models import Ingredient
        from app.modules.inventory.models import StockMovement

        ing = await session.get(Ingredient, gl.ingredient_id)
        if remaining > 0:
            if ing and Decimal(str(ing.stock_qty)) < remaining:
                raise BusinessRuleError("Không đủ tồn kho để hủy phiếu.")
            lot.quantity_remaining = Decimal("0")
            if ing:
                ing.stock_qty = ing.stock_qty - remaining
            m = StockMovement(
                ingredient_id=gl.ingredient_id,
                lot_id=lot.id,
                kind=StockMovementType.HOAN_KHO,
                qty=-remaining,
                business_date=_bd(),
                receipt_line_id=gl.id,
                performed_by=actor_id,
            )
            session.add(m)
            affected_ingredient_ids.append(gl.ingredient_id)
        lot.status = "Đã hủy"
    receipt.status = "Đã hủy"
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CANCEL_RECEIPT",
            target_entity="PHIEU_NHAP_KHO",
            target_id=str(receipt_id),
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
    been touched by any later issue/order/stocktake (quantity_remaining == the
    line's original quantity). There is no migration adding a separate purchase
    unit/conversion column to CHI_TIET_PHIEU_NHAP, so the edited quantity is the
    already-converted standard-unit quantity stored on the line.
    """
    await ensure_no_open_stocktake(session)
    receipt = await session.get(GoodsReceipt, receipt_id)
    if receipt is None:
        raise NotFoundError("Không tìm thấy phiếu nhập.")
    if receipt.status != "Nháp":
        raise BusinessRuleError("Chỉ được sửa phiếu ở trạng thái Nháp.")
    await _ensure_receipt_untouched(session, receipt_id)
    for ln in lines:
        line_id = ln["line_id"]
        new_qty = Decimal(str(ln["quantity"]))
        new_price = Decimal(str(ln["unit_price"]))
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
        if Decimal(str(lot.quantity_remaining)) != Decimal(str(gl.quantity)):
            raise BusinessRuleError(
                "Đã có giao dịch xuất kho liên quan, phải điều chỉnh qua kiểm kê định kỳ."
            )
        delta = new_qty - Decimal(str(gl.quantity))
        from app.modules.catalog.models import Ingredient
        from app.modules.inventory.models import StockMovement

        ing = await session.get(Ingredient, gl.ingredient_id)
        if ing is not None and Decimal(str(ing.stock_qty)) + delta < 0:
            raise BusinessRuleError("Tồn kho sau khi sửa không được âm.")
        gl.quantity = new_qty
        gl.unit_price = new_price
        # Keep the lot's own costing data in step with the edited receipt line:
        # opening-stock valuation falls back to these fields (FR-REP-05a).
        lot.quantity_remaining = new_qty
        lot.received_quantity = new_qty
        lot.unit_price = new_price
        if ing is not None:
            ing.stock_qty = ing.stock_qty + delta
        if delta != 0:
            session.add(
                StockMovement(
                    ingredient_id=gl.ingredient_id,
                    lot_id=None,
                    kind="Nhập",
                    qty=delta,
                    business_date=_bd(),
                    receipt_line_id=gl.id,
                    performed_by=actor_id,
                )
            )
        await session.flush()
        await recompute_automatic_out_of_stock(session, [gl.ingredient_id])
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="UPDATE_RECEIPT",
            target_entity="PHIEU_NHAP_KHO",
            target_id=str(receipt_id),
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
ISSUE_SOURCES = ("Nguyên liệu", "Món đã chế biến", "Kiểm kê")


async def _written_servings(session: AsyncSession, order_line_ids: list[int]) -> dict[int, int]:
    """Servings already written off per order line, counted once per voucher.

    `CHI_TIET_PHIEU_XUAT` repeats the same `servings` on every ingredient row of a
    prepared-dish voucher, so summing the column would count one serving once per
    ingredient. The inner MAX collapses a voucher to one number before summing.
    """
    if not order_line_ids:
        return {}
    per_voucher = (
        select(
            StockIssueLine.order_line_id.label("order_line_id"),
            StockIssueLine.issue_id.label("issue_id"),
            func.max(StockIssueLine.servings).label("servings"),
        )
        .where(
            StockIssueLine.order_line_id.in_(order_line_ids),
            StockIssueLine.servings.is_not(None),
        )
        .group_by(StockIssueLine.order_line_id, StockIssueLine.issue_id)
        .subquery()
    )
    rows = await session.execute(
        select(per_voucher.c.order_line_id, func.sum(per_voucher.c.servings)).group_by(
            per_voucher.c.order_line_id
        )
    )
    return {int(line_id): int(total or 0) for line_id, total in rows}


async def _consumption_per_serving(
    session: AsyncSession, order_line: OrderLine
) -> dict[int, Decimal]:
    """Ingredient quantity one serving consumed, from the original stock movements.

    The current recipe is deliberately not consulted: a later recipe change must not
    rewrite what the kitchen actually used. If the line predates stock movements
    (legacy/manual data), fall back to the recipe version snapshotted on the line.
    """
    rows = await session.execute(
        select(StockMovement.ingredient_id, func.sum(StockMovement.qty))
        .where(StockMovement.order_line_id == order_line.id)
        .group_by(StockMovement.ingredient_id)
    )
    net: dict[int, Decimal] = {}
    for ingredient_id, change in rows:
        consumed = -Decimal(str(change or 0))
        if consumed > 0:
            net[int(ingredient_id)] = consumed
    if net:
        servings = int(order_line.quantity)
        if servings <= 0:
            raise BusinessRuleError("Dòng món không còn suất để ghi nhận hủy.")
        return {ingredient_id: amount / Decimal(servings) for ingredient_id, amount in net.items()}

    if order_line.recipe_id is None:
        return {}
    recipe_rows = await session.execute(
        select(RecipeItem.ingredient_id, func.sum(RecipeItem.quantity))
        .where(RecipeItem.recipe_id == order_line.recipe_id)
        .group_by(RecipeItem.ingredient_id)
    )
    return {
        int(ingredient_id): Decimal(str(quantity))
        for ingredient_id, quantity in recipe_rows
        if quantity is not None and Decimal(str(quantity)) > 0
    }


async def preview_prepared_write_off(
    session: AsyncSession, *, order_line_id: int, servings: int
) -> dict:
    """Derive the ingredient list for a prepared-dish write-off (FR-INV-05/06)."""
    if servings <= 0:
        raise BusinessRuleError("Số suất hủy phải lớn hơn 0.")
    line = await session.get(OrderLine, order_line_id)
    if line is None:
        raise NotFoundError("Dòng món không tồn tại.")
    if line.status == "Đã hủy":
        raise BusinessRuleError("Dòng món đã hủy, không thể ghi nhận hủy thêm.")
    written = (await _written_servings(session, [order_line_id])).get(order_line_id, 0)
    eligible = max(0, int(line.quantity) - written)
    if servings > eligible:
        raise BusinessRuleError("Số suất hủy vượt quá số suất đã tiêu hao chưa ghi nhận.")
    per_serving = await _consumption_per_serving(session, line)
    if not per_serving:
        raise BusinessRuleError("Dòng món chưa có tiêu hao để ghi nhận hủy.")
    ingredients = {
        ingredient.id: ingredient
        for ingredient in (
            await session.execute(select(Ingredient).where(Ingredient.id.in_(per_serving.keys())))
        )
        .scalars()
        .all()
    }
    lines = []
    for ingredient_id, per_serving_quantity in per_serving.items():
        quantity = (per_serving_quantity * servings).quantize(Decimal("0.0001"))
        if quantity <= 0:
            continue
        ingredient = ingredients.get(ingredient_id)
        lines.append(
            {
                "ingredient_id": ingredient_id,
                "ingredient_name": ingredient.name if ingredient else f"#{ingredient_id}",
                "unit": ingredient.unit if ingredient else "",
                "quantity": quantity,
                "order_line_id": order_line_id,
                "servings": servings,
            }
        )
    if not lines:
        raise BusinessRuleError("Dòng món chưa có tiêu hao để ghi nhận hủy.")
    return {
        "order_line_id": order_line_id,
        "servings": servings,
        "written_servings": written,
        "eligible_servings": eligible,
        "lines": lines,
    }


async def create_issue(
    session: AsyncSession,
    actor_id: int,
    reason: str,
    lines: list[dict],
    *,
    source: str = "Nguyên liệu",
    stocktake_id: int | None = None,
) -> StockIssue:
    """FR-INV-05/06: a write-off document with an explicit source.

    Only the "Nguyên liệu" source moves stock (from the chosen lots or FIFO). The
    other two sources classify cost that a stock movement already recorded, so they
    must not draw inventory a second time.
    """
    await ensure_no_open_stocktake(session)

    if source not in ISSUE_SOURCES:
        raise BusinessRuleError("Nguồn xuất hủy không hợp lệ.")
    if source == "Kiểm kê":
        if stocktake_id is None:
            raise BusinessRuleError("Phiếu xuất từ kiểm kê phải tham chiếu phiếu kiểm kê.")
        stocktake = await session.get(Stocktake, stocktake_id)
        if stocktake is None:
            raise NotFoundError("Không tìm thấy phiếu kiểm kê.")
        if stocktake.status != "Đã chốt":
            raise BusinessRuleError("Chỉ ghi nhận hủy cho phiếu kiểm kê đã chốt.")

    # The prepared-dish source is expanded server-side: the client sends the order
    # line and the number of servings, never the ingredient quantities.
    issue_lines: list[dict] = []
    if source == "Món đã chế biến":
        requested: dict[int, int] = {}
        for ln in lines:
            line_id = ln.get("order_line_id")
            servings = ln.get("servings")
            if not line_id or not servings:
                raise BusinessRuleError("Nguồn món đã chế biến cần dòng món và số suất hủy.")
            requested[int(line_id)] = requested.get(int(line_id), 0) + int(servings)
        for line_id, servings in requested.items():
            preview = await preview_prepared_write_off(
                session, order_line_id=line_id, servings=servings
            )
            issue_lines.extend(preview["lines"])
    else:
        for ln in lines:
            if ln.get("ingredient_id") is None or ln.get("quantity") is None:
                raise BusinessRuleError("Cần nguyên liệu và số lượng cho phiếu xuất hủy.")
            quantity = Decimal(str(ln["quantity"]))
            if quantity <= 0:
                raise BusinessRuleError("Số lượng phải lớn hơn 0.")
            issue_lines.append(
                {
                    "ingredient_id": int(ln["ingredient_id"]),
                    "quantity": quantity,
                    "lot_id": ln.get("lot_id"),
                    "order_line_id": None,
                    "servings": None,
                }
            )

    moment = business_date.now()
    issue = StockIssue(
        reason=reason,
        status="Nháp",
        created_at=moment,
        issue_date=moment,
        created_by=actor_id,
        stocktake_id=stocktake_id if source == "Kiểm kê" else None,
        note=source,
    )
    session.add(issue)
    await session.flush()
    for ln in issue_lines:
        iid = ln["ingredient_id"]
        qty = Decimal(str(ln["quantity"]))
        il = StockIssueLine(
            issue_id=issue.id,
            ingredient_id=iid,
            quantity=qty,
            estimated_cost=Decimal("0"),
            order_line_id=ln.get("order_line_id"),
            servings=ln.get("servings"),
        )
        session.add(il)
        await session.flush()
        if source != "Nguyên liệu":
            continue
        _allow_exp = "hết hạn" in reason.lower() if reason else False
        selected_lot = ln.get("lot_id")
        await apply_stock_movement(
            session,
            StockChange(
                ingredient_id=iid,
                delta=-qty,
                kind="Xuất thủ công",
                allow_expired=_allow_exp,
                business_date=_bd(),
                source_issue_line_id=il.id,
                lot_ids=[int(selected_lot)] if selected_lot else None,
            ),
            actor_id=actor_id,
        )
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="MANUAL_STOCK_ISSUE",
            target_entity="PHIEU_XUAT_KHO",
            target_id=str(issue.id),
            after={"Nguon": source, "MaPhieuKiemKe": stocktake_id},
        )
    )
    await session.flush()
    return issue


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
async def create_stocktake(session: AsyncSession, actor_id: int) -> Stocktake:
    await lock_stock_operations(session)
    # NFR-20: one open counting session at a time; the session blocks stock changes.
    existing = (
        await session.execute(
            select(Stocktake.id).where(Stocktake.status == "Nháp").limit(1).with_for_update()
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise BusinessRuleError("Đang có phiên kiểm kê chưa chốt.")
    from app.modules.sales.models import OrderLine, Reservation
    from app.modules.sales.reservations import expire_due_holds

    await expire_due_holds(session)
    active_holds = (
        await session.execute(
            select(Reservation.id)
            .where(Reservation.status == "Đang giữ")
            .limit(1)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if active_holds:
        raise BusinessRuleError("Còn lượt giữ chỗ chưa gửi, hãy xử lý trước khi kiểm kê.")
    pending = (
        await session.execute(
            select(OrderLine.id).where(OrderLine.status == "Chờ").limit(1).with_for_update()
        )
    ).scalar_one_or_none()
    if pending is not None:
        raise BusinessRuleError("Còn món Chờ làm, hãy xử lý trước khi kiểm kê.")
    st = Stocktake(status="Nháp", stocktake_date=business_date.now(), performed_by=actor_id)
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


async def cancel_stocktake(session: AsyncSession, actor_id: int, stocktake_id: int) -> None:
    """Abandon an open counting sheet (R22) without touching stock.

    Without this, a draft left behind after a reload keeps `ensure_no_open_stocktake`
    blocking every stock change and there is no way out from the UI.
    """
    await lock_stock_operations(session)
    st = (
        await session.execute(
            select(Stocktake)
            .where(Stocktake.id == stocktake_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if st is None:
        raise NotFoundError("Không tìm thấy phiếu kiểm kê.")
    if st.status != "Nháp":
        raise BusinessRuleError("Chỉ hủy được phiên kiểm kê đang mở.")
    st.status = "Đã hủy"
    st.note = "Hủy phiên kiểm kê"
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CANCEL_STOCKTAKE",
            target_entity="PHIEU_KIEM_KE",
            target_id=str(st.id),
            reason="Hủy phiên kiểm kê đang mở",
        )
    )
    await session.flush()


async def record_counts(
    session: AsyncSession,
    stocktake_id: int,
    counts: list[tuple[int, Decimal, str | None]],
) -> None:
    await lock_stock_operations(session)
    st = (
        await session.execute(
            select(Stocktake)
            .where(Stocktake.id == stocktake_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if st is None:
        raise NotFoundError("Không tìm thấy phiếu kiểm kê.")
    if st.status != "Nháp":
        raise BusinessRuleError("Phiếu kiểm kê đã chốt, không thể ghi nhận thêm.")
    existing = {
        line.ingredient_id: line
        for line in (
            await session.execute(
                select(StocktakeLine).where(StocktakeLine.stocktake_id == stocktake_id)
            )
        )
        .scalars()
        .all()
    }
    seen_ids: set[int] = set()
    for iid, actual, reason in counts:
        if iid in seen_ids:
            raise BusinessRuleError("Nguyên liệu trùng lặp trong cùng phiếu kiểm kê.")
        seen_ids.add(iid)
        if Decimal(str(actual)) < 0:
            raise BusinessRuleError("Tồn thực tế không được âm.")
        # get system qty
        from app.modules.catalog.models import Ingredient

        ing = await session.get(Ingredient, iid)
        sys_qty = Decimal(str(ing.stock_qty)) if ing else Decimal(0)
        line = existing.get(iid)
        if line is None:
            session.add(
                StocktakeLine(
                    stocktake_id=stocktake_id,
                    ingredient_id=iid,
                    system_qty=sys_qty,
                    actual_qty=actual,
                    reason=reason,
                )
            )
        else:
            # Re-counting an ingredient updates its line instead of duplicating it.
            line.system_qty = sys_qty
            line.actual_qty = actual
            line.reason = reason
    await session.flush()


async def confirm_stocktake(session: AsyncSession, actor_id: int, stocktake_id: int) -> None:
    await lock_stock_operations(session)
    st = (
        await session.execute(
            select(Stocktake)
            .where(Stocktake.id == stocktake_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if st is None:
        raise NotFoundError("Không tìm thấy phiếu kiểm kê.")
    if st.status != "Nháp":
        raise BusinessRuleError("Phiếu kiểm kê đã được xác nhận trước đó.")
    lines = (
        (
            await session.execute(
                select(StocktakeLine).where(StocktakeLine.stocktake_id == stocktake_id)
            )
        )
        .scalars()
        .all()
    )
    if not lines:
        raise BusinessRuleError("Chưa ghi nhận kiểm kê.")
    from app.modules.catalog.models import Ingredient as ActiveIngredient

    active_count = (
        await session.execute(
            select(func.count())
            .select_from(ActiveIngredient)
            .where(ActiveIngredient.is_deleted.is_(False))
        )
    ).scalar_one()
    counted = len({line.ingredient_id for line in lines})
    if counted < active_count:
        raise BusinessRuleError("Chưa kiểm đủ nguyên liệu đang hoạt động.")
    affected_ingredient_ids: list[int] = []
    write_off: list[tuple[int, Decimal]] = []
    for line in lines:
        affected_ingredient_ids.append(line.ingredient_id)
        diff = Decimal(str(line.actual_qty)) - Decimal(str(line.system_qty))
        if diff == 0:
            continue
        if diff < 0:
            write_off.append((line.ingredient_id, -diff))
            # The physical count includes expired lots, so the shortage must be
            # deducted from every lot, not only the still-sellable ones.
            from app.modules.inventory.stock import lots_for_fifo

            fifo_lots = await lots_for_fifo(session, line.ingredient_id, allow_expired=True)
            need = -diff
            total_avail = sum(
                (Decimal(str(lot.quantity_remaining)) for lot in fifo_lots), Decimal(0)
            )
            take_total = min(total_avail, need)
            # consume FIFO lots in order
            rem = take_total
            for _lot in fifo_lots:
                if rem <= 0:
                    break
                avail = Decimal(str(_lot.quantity_remaining))
                take = min(avail, rem)
                _lot.quantity_remaining = avail - take
                from app.modules.inventory.models import StockMovement as SM2

                m2 = SM2(
                    ingredient_id=line.ingredient_id,
                    lot_id=_lot.id,
                    kind="Điều chỉnh kiểm kê",
                    qty=-take,
                    business_date=_bd(),
                    stocktake_line_id=line.id,
                    performed_by=actor_id,
                )
                session.add(m2)
                rem -= take
            # remaining shortage (system > FIFO sum) is shortage beyond lots — adjust ingredient total directly
            from app.modules.catalog.models import Ingredient as Ing2

            ing2 = await session.get(Ing2, line.ingredient_id)
            if ing2:
                # ing total should become actual_qty; we already deducted take_total via lots, so set directly
                ing2.stock_qty = line.actual_qty
        else:
            # BR-LOT-02 includes empty but still valid lots; never invent a receipt.
            today = business_date.now().date()
            lot = (
                await session.execute(
                    select(IngredientLot)
                    .where(
                        IngredientLot.ingredient_id == line.ingredient_id,
                        IngredientLot.status != "Hết hạn",
                        (IngredientLot.expiry_date.is_(None))
                        | (IngredientLot.expiry_date >= today),
                    )
                    .order_by(IngredientLot.received_at.desc(), IngredientLot.id.desc())
                    .limit(1)
                    .with_for_update()
                )
            ).scalar_one_or_none()
            if lot is None:
                lot = IngredientLot(
                    ingredient_id=line.ingredient_id,
                    receipt_line_id=None,
                    quantity_remaining=diff,
                    status="Còn hạn",
                    received_at=st.stocktake_date,
                    expiry_date=None,
                    is_adjustment=True,
                )
                session.add(lot)
            else:
                lot.quantity_remaining = Decimal(str(lot.quantity_remaining)) + diff
                lot.status = "Còn hạn"
            await session.flush()
            from app.modules.inventory.models import StockMovement as SM3

            m = SM3(
                ingredient_id=line.ingredient_id,
                lot_id=lot.id,
                kind="Điều chỉnh kiểm kê",
                qty=diff,
                business_date=_bd(),
                stocktake_line_id=line.id,
                performed_by=actor_id,
            )
            session.add(m)
            from app.modules.catalog.models import Ingredient as Ing4

            ing = await session.get(Ing4, line.ingredient_id)
            if ing:
                ing.stock_qty = ing.stock_qty + diff
    if write_off:
        # FR-INV-05: the write-off document is evidence only; its cost stays on
        # the negative stocktake movement so reports do not count it twice.
        issue = StockIssue(
            reason="Hủy do kiểm kê",
            status="Đã xác nhận",
            created_at=business_date.now(),
            issue_date=business_date.now(),
            created_by=actor_id,
            note=f"Tự sinh từ phiếu kiểm kê #{st.id}",
            stocktake_id=st.id,
        )
        session.add(issue)
        await session.flush()
        for ingredient_id, quantity in write_off:
            session.add(
                StockIssueLine(
                    issue_id=issue.id,
                    ingredient_id=ingredient_id,
                    quantity=quantity,
                    estimated_cost=Decimal("0"),
                )
            )
        await session.flush()

    st.status = StocktakeStatus.DA_CHOT.value
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CONFIRM_STOCKTAKE",
            target_entity="PHIEU_KIEM_KE",
            target_id=str(stocktake_id),
        )
    )
    await session.flush()
    if affected_ingredient_ids:
        await recompute_automatic_out_of_stock(session, affected_ingredient_ids)


async def list_stock(
    session,
    search: str | None = None,
    alerting: bool | None = None,
    page: int = 1,
    page_size: int = 50,
):
    from app.modules.inventory.queries import list_stock as query_stock

    return await query_stock(
        session, search=search, alerting=alerting, page=page, page_size=page_size
    )


async def recompute_automatic_out_of_stock(session, ingredient_ids: list[int]) -> list[int]:
    from app.modules.catalog.models import Dish, Recipe, RecipeItem
    from app.modules.catalog.models import Ingredient as Ing
    from app.shared.enums import VersionStatus

    if not ingredient_ids:
        return []
    # batch: find all recipe items that use any of these ingredients
    affected_items = (
        (
            await session.execute(
                select(RecipeItem).where(RecipeItem.ingredient_id.in_(ingredient_ids))
            )
        )
        .scalars()
        .all()
    )
    affected_recipe_ids = {it.recipe_id for it in affected_items}
    if not affected_recipe_ids:
        return []
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
    # batch load all items for those recipes
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
    ing_ids_needed = {it.ingredient_id for it in all_items}
    ings = (await session.execute(select(Ing).where(Ing.id.in_(ing_ids_needed)))).scalars().all()
    ing_map = {i.id: i for i in ings}
    hidden: list[int] = []
    for r in recipes:
        items = items_by_recipe.get(r.id, [])
        ok = all(
            float(ing_map[it.ingredient_id].stock_qty) >= float(it.quantity)
            for it in items
            if it.ingredient_id in ing_map
        )
        dish = await session.get(Dish, r.dish_id)
        if dish and not dish.is_deleted:
            dish.out_of_stock = not ok
            if not ok:
                hidden.append(dish.id)
    await session.flush()
    return hidden
