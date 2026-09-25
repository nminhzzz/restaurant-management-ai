"""Inventory service — receipts, issues, stocktakes."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.inventory.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    IngredientLot,
    StockIssue,
    StockIssueLine,
    Stocktake,
    StocktakeLine,
)
from app.modules.inventory.stock import StockChange, apply_stock_movement
from app.shared import business_date
from app.shared.audit import SystemAuditLog


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
            quantity=float(qty_std),
            unit_price=float(unit_price),
        )
        session.add(gl)
        await session.flush()
        # create lot
        lot = IngredientLot(
            ingredient_id=ingredient_id,
            receipt_line_id=gl.id,
            quantity_remaining=float(qty_std),
            status="Còn hạn",
            received_at=receipt.receipt_date,
            is_adjustment=False,
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
                business_date=_bd(),
                source_receipt_line_id=gl.id,
            ),
            actor_id=actor_id,
        )
        # ensure expiry not needed for test - HanSuDung derived via SoNgayBaoQuan in view; we store not
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


async def cancel_receipt(session: AsyncSession, actor_id: int, receipt_id: int) -> None:
    from app.shared.enums import StockMovementType

    receipt = await session.get(GoodsReceipt, receipt_id)
    if receipt is None:
        raise NotFoundError("Không tìm thấy phiếu nhập.")
    if receipt.status == "Đã hủy":
        raise BusinessRuleError("Phiếu đã được hủy trước đó.")
    if receipt.status != "Nháp":
        raise BusinessRuleError("Chỉ được hủy phiếu ở trạng thái Nháp.")
    lines = (
        (
            await session.execute(
                select(GoodsReceiptLine).where(GoodsReceiptLine.receipt_id == receipt_id)
            )
        )
        .scalars()
        .all()
    )
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
            lot.quantity_remaining = 0
            if ing:
                ing.stock_qty = float(Decimal(str(ing.stock_qty)) - remaining)
            m = StockMovement(
                ingredient_id=gl.ingredient_id,
                lot_id=lot.id,
                kind=StockMovementType.HOAN_KHO,
                qty=float(-remaining),
                business_date=_bd(),
                receipt_line_id=gl.id,
                performed_by=actor_id,
            )
            session.add(m)
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


async def list_receipts(
    session: AsyncSession, page: int = 1, page_size: int = 20, supplier_id: int | None = None
) -> list[GoodsReceipt]:
    q = select(GoodsReceipt)
    if supplier_id is not None:
        q = q.where(GoodsReceipt.supplier_id == supplier_id)
    q = q.order_by(GoodsReceipt.id.desc()).offset((page - 1) * page_size).limit(page_size)
    r = await session.execute(q)
    return list(r.scalars().all())


# Issues
async def create_issue(
    session: AsyncSession, actor_id: int, reason: str, lines: list[dict]
) -> StockIssue:
    issue = StockIssue(reason=reason, status="Nháp")
    session.add(issue)
    await session.flush()
    for ln in lines:
        iid = ln["ingredient_id"]
        qty = Decimal(str(ln["quantity"]))
        il = StockIssueLine(
            issue_id=issue.id, ingredient_id=iid, quantity=float(qty), estimated_cost=0
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
                business_date=_bd(),
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
        )
    )
    await session.flush()
    return issue


# Stocktakes
async def create_stocktake(session: AsyncSession, actor_id: int) -> Stocktake:
    st = Stocktake(status="Nháp", stocktake_date=business_date.now())
    session.add(st)
    await session.flush()
    return st


async def record_counts(
    session: AsyncSession, stocktake_id: int, counts: list[tuple[int, Decimal]]
) -> None:
    st = await session.get(Stocktake, stocktake_id)
    if st is None:
        raise NotFoundError("Không tìm thấy phiếu kiểm kê.")
    if st.status != "Nháp":
        raise BusinessRuleError("Phiếu kiểm kê đã chốt, không thể ghi nhận thêm.")
    seen_ids: set[int] = set()
    for iid, actual in counts:
        if iid in seen_ids:
            raise BusinessRuleError("Nguyên liệu trùng lặp trong cùng phiếu kiểm kê.")
        seen_ids.add(iid)
        if Decimal(str(actual)) < 0:
            raise BusinessRuleError("Tồn thực tế không được âm.")
        # get system qty
        from app.modules.catalog.models import Ingredient

        ing = await session.get(Ingredient, iid)
        sys_qty = Decimal(str(ing.stock_qty)) if ing else Decimal(0)
        line = StocktakeLine(
            stocktake_id=stocktake_id,
            ingredient_id=iid,
            system_qty=float(sys_qty),
            actual_qty=float(actual),
        )
        session.add(line)
    await session.flush()


async def confirm_stocktake(session: AsyncSession, actor_id: int, stocktake_id: int) -> None:
    st = await session.get(Stocktake, stocktake_id)
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
    for line in lines:
        diff = Decimal(str(line.actual_qty)) - Decimal(str(line.system_qty))
        if diff == 0:
            continue
        if diff < 0:
            # Deduct via FIFO but never touch HET_HAN lots; keep 3-tier in sync
            from app.modules.inventory.stock import lots_for_fifo

            fifo_lots = await lots_for_fifo(session, line.ingredient_id)
            need = -diff
            total_avail = sum(
                (Decimal(str(lot.quantity_remaining)) for lot in fifo_lots), Decimal(0)
            )
            take_total = min(total_avail, need)
            # consume FIFO lots in order
            rem = take_total  # type: ignore[assignment]
            for _lot in fifo_lots:
                if rem <= 0:
                    break
                avail = Decimal(str(_lot.quantity_remaining))
                take = min(avail, rem)
                _lot.quantity_remaining = float(avail - take)
                from app.modules.inventory.models import StockMovement as SM2

                m2 = SM2(
                    ingredient_id=line.ingredient_id,
                    lot_id=_lot.id,
                    kind="Điều chỉnh kiểm kê",
                    qty=float(-take),
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
                ing2.stock_qty = float(line.actual_qty)
        else:
            # surplus: create adjustment receipt lineage with unit_price=0 (excluded from avg by receipt status filter in reports) is kept, but tagged is_adjustment
            gr = GoodsReceipt(supplier_id=None, receipt_date=business_date.now(), status="Nháp")
            session.add(gr)
            await session.flush()
            gl = GoodsReceiptLine(
                receipt_id=gr.id,
                ingredient_id=line.ingredient_id,
                quantity=float(diff),
                unit_price=0,
            )
            session.add(gl)
            await session.flush()
            lot = IngredientLot(
                ingredient_id=line.ingredient_id,
                receipt_line_id=gl.id,
                quantity_remaining=float(diff),
                status="Còn hạn",
                received_at=business_date.now(),
                is_adjustment=True,
            )
            session.add(lot)
            await session.flush()
            from app.modules.inventory.models import StockMovement as SM3

            m = SM3(
                ingredient_id=line.ingredient_id,
                lot_id=lot.id,
                kind="Điều chỉnh kiểm kê",
                qty=float(diff),
                business_date=_bd(),
                stocktake_line_id=line.id,
                performed_by=actor_id,
            )
            session.add(m)
            from app.modules.catalog.models import Ingredient as Ing4

            ing = await session.get(Ing4, line.ingredient_id)
            if ing:
                ing.stock_qty = float(Decimal(str(ing.stock_qty)) + diff)
    st.status = "Đã xác nhận"
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


async def list_stock(
    session,
    search: str | None = None,
    alerting: bool | None = None,
    page: int = 1,
    page_size: int = 50,
):
    from sqlalchemy import select as sel

    from app.modules.catalog.models import Ingredient
    from app.modules.settings.models import SystemConfig

    cfg = (await session.execute(sel(SystemConfig))).scalar_one_or_none()
    default = float(cfg.default_stock_threshold) if cfg else 5
    # Build base query with alert filter in SQL where possible; fallback to Python for threshold compare
    base = sel(Ingredient).where(Ingredient.is_deleted == False)
    if search:
        safe = search.replace("%", "\\%").replace("_", "\\_")
        base = base.where(Ingredient.name.ilike(f"%{safe}%", escape="\\"))
    # If alerting filter requested, fetch a larger window then filter, else SQL pagination
    if alerting is not None:
        # Need to evaluate threshold per row; fetch with LIMIT/OFFSET * factor then filter
        # Simple: fetch all matching then filter then paginate in Python (bounded by threshold check)
        # For true SQL pagination without function, keep Python slice after alert filter
        all_rows = (await session.execute(base.order_by(Ingredient.id))).scalars().all()
        filtered = []
        for ing in all_rows:
            thr = float(ing.min_stock) if ing.min_stock is not None else default
            alert = float(ing.stock_qty) < thr
            if alert == alerting:
                filtered.append((ing, thr, alert))
        start_idx = (page - 1) * page_size
        page_items = filtered[start_idx : start_idx + page_size]
        return [
            {
                "MaNguyenLieu": ing.id,
                "TenNguyenLieu": ing.name,
                "SoLuongTon": float(ing.stock_qty),
                "MucTonToiThieuApDung": thr,
                "CanhBaoTonThap": alert,
            }
            for ing, thr, alert in page_items
        ]
    # No alert filter: SQL pagination
    q = base.order_by(Ingredient.id).offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(q)).scalars().all()
    out = []
    for ing in rows:
        thr = float(ing.min_stock) if ing.min_stock is not None else default
        alert = float(ing.stock_qty) < thr
        out.append(
            {
                "MaNguyenLieu": ing.id,
                "TenNguyenLieu": ing.name,
                "SoLuongTon": float(ing.stock_qty),
                "MucTonToiThieuApDung": thr,
                "CanhBaoTonThap": alert,
            }
        )
    return out


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
            dish.out_of_stock_auto = not ok
            if not ok:
                hidden.append(dish.id)
    await session.flush()
    return hidden
