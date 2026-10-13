"""Catalogue service (Module 1): groups, dishes, price/recipe versions, ingredients,
suppliers and tables.

Every mutation writes one audit entry carrying the state before and after (FR-SET-08/09).
"""

from datetime import date as _date
from decimal import Decimal as _Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.modules.catalog.models import (
    DiningTable,
    Dish,
    DishGroup,
    DishPriceVersion,
    Ingredient,
    Recipe,
    RecipeItem,
    Supplier,
)
from app.modules.catalog.versions import promote_due_versions
from app.modules.settings.service import effective_business_day_start
from app.shared import business_date as _bd
from app.shared.audit import record
from app.shared.enums import DishStatus, OrderStatus, VersionStatus

FINISHED_ORDER_STATUSES = (
    OrderStatus.DA_THANH_TOAN.value,
    OrderStatus.DONG_CHUA_THU_DUOC_TIEN.value,
    OrderStatus.DA_HUY.value,
    OrderStatus.TU_DONG_DONG.value,
)


def _audit(
    session: AsyncSession,
    actor_id: int | None,
    action: str,
    entity: str,
    target_id: object,
    *,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
) -> None:
    record(
        session,
        user_id=actor_id,
        action=action,
        target_entity=entity,
        target_id=str(target_id),
        before=before,
        after=after,
        reason=reason,
    )


def _num(value: object) -> float | None:
    return None if value is None else float(str(value))


def _group_state(group: DishGroup) -> dict[str, Any]:
    return {
        "TenNhomMon": group.name,
        "ThuTuHienThi": group.display_order,
        "DaXoa": group.is_deleted,
    }


def _dish_state(dish: Dish) -> dict[str, Any]:
    return {
        "TenMon": dish.name,
        "MaNhomMon": dish.group_id,
        "HinhAnh": dish.image_url,
        "TamDungThuCong": dish.manually_paused,
        "DaXoa": dish.is_deleted,
    }


def _price_state(version: DishPriceVersion) -> dict[str, Any]:
    return {
        "MaMon": version.dish_id,
        "GiaBan": _num(version.price),
        "BusinessDateApDung": version.business_date.isoformat(),
        "TrangThai": version.status,
        "LoaiThayDoi": version.change_type,
    }


async def _recipe_state(session: AsyncSession, recipe: Recipe) -> dict[str, Any]:
    items = (
        (await session.execute(select(RecipeItem).where(RecipeItem.recipe_id == recipe.id)))
        .scalars()
        .all()
    )
    return {
        "MaMon": recipe.dish_id,
        "BusinessDateApDung": recipe.business_date.isoformat(),
        "TrangThai": recipe.status,
        "LoaiThayDoi": recipe.change_type,
        "DongCongThuc": [
            {"MaNguyenLieu": item.ingredient_id, "DinhLuong": _num(item.quantity)}
            for item in sorted(items, key=lambda row: row.ingredient_id)
        ],
    }


def _ingredient_state(ingredient: Ingredient) -> dict[str, Any]:
    return {
        "TenNguyenLieu": ingredient.name,
        "DonViTinh": ingredient.unit,
        "MucTonToiThieu": _num(ingredient.min_stock),
        "DaXoa": ingredient.is_deleted,
    }


def _supplier_state(supplier: Supplier) -> dict[str, Any]:
    return {
        "TenNCC": supplier.name,
        "DienThoai": supplier.phone,
        "NguoiLienHe": supplier.contact_name,
        "Email": supplier.email,
        "DiaChi": supplier.address,
        "DaXoa": supplier.is_deleted,
    }


def _table_state(table: DiningTable) -> dict[str, Any]:
    return {
        "TenBan": table.name,
        "SoChoNgoi": table.capacity,
        "TrangThai": table.status,
        "MaOrderDangPhucVu": table.serving_order_id,
        "DaXoa": table.is_deleted,
    }


async def display_status_for(session: AsyncSession, dish: Dish) -> str:
    """FR-CAT-27: the status is derived on every read, from live availability and the
    manual pause flag; it is never a value somebody wrote."""
    from app.modules.inventory.stock import dish_is_out_of_stock

    if dish.is_deleted:
        return "Đã xóa"
    if dish.missing_recipe:
        return DishStatus.NHAP.value
    if await dish_is_out_of_stock(session, dish.id):
        return DishStatus.HET_NGUYEN_LIEU.value
    if dish.manually_paused:
        return DishStatus.TAM_DUNG.value
    return DishStatus.HOAT_DONG.value


async def blocking_reasons(session: AsyncSession, dish: Dish) -> list[str]:
    """All the reasons that stop a dish being ordered, for the management screen."""
    from app.modules.inventory.stock import dish_is_out_of_stock

    reasons: list[str] = []
    if dish.missing_recipe:
        reasons.append(DishStatus.NHAP.value)
    elif await dish_is_out_of_stock(session, dish.id):
        reasons.append(DishStatus.HET_NGUYEN_LIEU.value)
    if dish.manually_paused:
        reasons.append(DishStatus.TAM_DUNG.value)
    return reasons


async def _release_dish_holds(session: AsyncSession, dish_id: int) -> None:
    """A paused or removed dish frees the selections that still hold stock for it."""
    from app.modules.sales.models import ItemHold

    await session.execute(
        update(ItemHold)
        .where(ItemHold.dish_id == dish_id, ItemHold.status == "Đang giữ")
        .values(status="Đã hủy")
        .execution_options(synchronize_session="fetch")
    )


# --- Groups -----------------------------------------------------------------------------------


async def create_group(session: AsyncSession, actor_id: int, name: str) -> DishGroup:
    max_order = (
        await session.execute(
            select(func.coalesce(func.max(DishGroup.display_order), 0)).where(
                DishGroup.is_deleted.is_(False)
            )
        )
    ).scalar_one()
    group = DishGroup(name=name, display_order=int(max_order) + 1, is_deleted=False)
    session.add(group)
    await session.flush()
    _audit(session, actor_id, "CREATE_GROUP", "NHOM_MON", group.id, after=_group_state(group))
    await session.flush()
    return group


async def list_groups(session: AsyncSession) -> list[DishGroup]:
    result = await session.execute(
        select(DishGroup).where(DishGroup.is_deleted.is_(False)).order_by(DishGroup.display_order)
    )
    return list(result.scalars().all())


async def update_group(
    session: AsyncSession, actor_id: int, group_id: int, name: str | None
) -> DishGroup:
    group = await session.get(DishGroup, group_id)
    if group is None or group.is_deleted:
        raise NotFoundError("Không tìm thấy nhóm món.")
    before = _group_state(group)
    if name is not None:
        group.name = name
    await session.flush()
    _audit(
        session,
        actor_id,
        "UPDATE_GROUP",
        "NHOM_MON",
        group.id,
        before=before,
        after=_group_state(group),
    )
    await session.flush()
    return group


async def delete_group(session: AsyncSession, actor_id: int, group_id: int) -> None:
    """FR-CAT-03: refused while a live dish remains; removed for good only if the group
    never held a dish, soft-deleted otherwise so the history still resolves."""
    group = await session.get(DishGroup, group_id)
    if group is None or group.is_deleted:
        raise NotFoundError("Không tìm thấy nhóm món.")
    live = (
        await session.execute(
            select(func.count())
            .select_from(Dish)
            .where(Dish.group_id == group_id, Dish.is_deleted.is_(False))
        )
    ).scalar_one()
    if live > 0:
        raise BusinessRuleError("Không thể xóa nhóm còn món đang hoạt động.")
    ever = (
        await session.execute(
            select(func.count()).select_from(Dish).where(Dish.group_id == group_id)
        )
    ).scalar_one()
    before = _group_state(group)
    if ever == 0:
        await session.delete(group)
        after = None
    else:
        group.is_deleted = True
        group.deleted_at = _bd.now().replace(tzinfo=None)
        after = _group_state(group)
    await session.flush()
    _audit(session, actor_id, "DELETE_GROUP", "NHOM_MON", group_id, before=before, after=after)
    await session.flush()


async def reorder_groups(
    session: AsyncSession, actor_id: int, ordered_ids: list[int]
) -> list[DishGroup]:
    existing = await list_groups(session)
    existing_ids = [g.id for g in existing]
    if set(ordered_ids) != set(existing_ids) or len(ordered_ids) != len(existing_ids):
        raise BusinessRuleError("Danh sách sắp xếp phải chứa đủ các nhóm đang hoạt động.")
    id_to_group = {g.id: g for g in existing}
    before = {"ThuTu": existing_ids}
    for idx, gid in enumerate(ordered_ids, start=1):
        id_to_group[gid].display_order = idx
    await session.flush()
    _audit(
        session,
        actor_id,
        "REORDER_GROUPS",
        "NHOM_MON",
        ",".join(map(str, ordered_ids)),
        before=before,
        after={"ThuTu": ordered_ids},
    )
    await session.flush()
    return [id_to_group[gid] for gid in ordered_ids]


# --- Dishes -----------------------------------------------------------------------------------


async def _live_group(session: AsyncSession, group_id: int) -> DishGroup:
    group = await session.get(DishGroup, group_id)
    if group is None or group.is_deleted:
        raise BusinessRuleError("Nhóm món không tồn tại.")
    return group


async def create_dish(
    session: AsyncSession,
    actor_id: int,
    name: str,
    group_id: int | None,
    image: str | None = None,
    price: float | None = None,
) -> Dish:
    # FR-CAT-02: every dish belongs to exactly one group.
    if group_id is None:
        raise BusinessRuleError("Món ăn phải thuộc đúng một nhóm món.")
    await _live_group(session, group_id)
    dish = Dish(
        name=name,
        group_id=group_id,
        image_url=image,
        missing_recipe=True,
        out_of_stock=False,
        manually_paused=False,
        is_deleted=False,
    )
    session.add(dish)
    await session.flush()
    if price is not None:
        # The price lives in LICH_SU_GIA_MON, the same table orders snapshot from.
        await apply_price_directly(session, actor_id, dish.id, _Decimal(str(price)))
    _audit(session, actor_id, "CREATE_DISH", "MON_AN", dish.id, after=_dish_state(dish))
    await session.flush()
    return dish


async def get_dish(session: AsyncSession, dish_id: int) -> Dish | None:
    return await session.get(Dish, dish_id)


async def list_dishes(session: AsyncSession, search: str | None = None) -> tuple[list[Dish], int]:
    query = select(Dish).where(Dish.is_deleted.is_(False))
    count = select(func.count()).select_from(Dish).where(Dish.is_deleted.is_(False))
    if search:
        like = f"%{search}%"
        query = query.where(Dish.name.ilike(like))
        count = count.where(Dish.name.ilike(like))
    total = (await session.execute(count)).scalar_one()
    result = await session.execute(query.order_by(Dish.id))
    return list(result.scalars().all()), total


async def update_dish(
    session: AsyncSession,
    actor_id: int,
    dish_id: int,
    name: str | None = None,
    group_id: int | None = None,
    image: str | None = None,
    image_provided: bool = False,
) -> Dish:
    dish = await session.get(Dish, dish_id)
    if dish is None or dish.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    before = _dish_state(dish)
    if name is not None:
        dish.name = name
    if group_id is not None:
        await _live_group(session, group_id)
        dish.group_id = group_id
    if image_provided:
        dish.image_url = image
    await session.flush()
    _audit(
        session,
        actor_id,
        "UPDATE_DISH",
        "MON_AN",
        dish.id,
        before=before,
        after=_dish_state(dish),
    )
    await session.flush()
    return dish


async def _cancel_pending_versions(
    session: AsyncSession, actor_id: int | None, dish_id: int, reason: str
) -> None:
    """Mark the dish's pending price and recipe changes as cancelled, with an audit entry
    for each (FR-CAT-05, FR-CAT-09, FR-CAT-21): nothing is deleted."""
    prices = (
        (
            await session.execute(
                select(DishPriceVersion).where(
                    DishPriceVersion.dish_id == dish_id,
                    DishPriceVersion.status == VersionStatus.NHAP.value,
                )
            )
        )
        .scalars()
        .all()
    )
    for price in prices:
        before = _price_state(price)
        price.status = VersionStatus.DA_HUY.value
        _audit(
            session,
            actor_id,
            "CANCEL_PRICE_CHANGE",
            "LICH_SU_GIA_MON",
            price.id,
            before=before,
            after=_price_state(price),
            reason=reason,
        )
    recipes = (
        (
            await session.execute(
                select(Recipe).where(
                    Recipe.dish_id == dish_id, Recipe.status == VersionStatus.NHAP.value
                )
            )
        )
        .scalars()
        .all()
    )
    for recipe in recipes:
        before = await _recipe_state(session, recipe)
        recipe.status = VersionStatus.DA_HUY.value
        _audit(
            session,
            actor_id,
            "CANCEL_RECIPE_CHANGE",
            "CONG_THUC",
            recipe.id,
            before=before,
            after=await _recipe_state(session, recipe),
            reason=reason,
        )
    await session.flush()


async def delete_dish(session: AsyncSession, actor_id: int, dish_id: int) -> Dish:
    dish = await session.get(Dish, dish_id)
    if dish is None or dish.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    before = _dish_state(dish)
    dish.is_deleted = True
    await session.flush()
    await _cancel_pending_versions(session, actor_id, dish_id, "Món bị xóa mềm")
    await _release_dish_holds(session, dish_id)
    _audit(
        session,
        actor_id,
        "DELETE_DISH",
        "MON_AN",
        dish.id,
        before=before,
        after=_dish_state(dish),
    )
    await session.flush()
    return dish


async def set_manual_pause(
    session: AsyncSession, actor_id: int, dish_id: int, paused: bool
) -> Dish:
    """FR-CAT-26: the manager's own pause flag, independent of the derived stock state."""
    dish = await session.get(Dish, dish_id)
    if dish is None or dish.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    before = _dish_state(dish)
    dish.manually_paused = paused
    await session.flush()
    if paused:
        await _release_dish_holds(session, dish_id)
    _audit(
        session,
        actor_id,
        "PAUSE_DISH" if paused else "RESUME_DISH",
        "MON_AN",
        dish_id,
        before=before,
        after=_dish_state(dish),
    )
    await session.flush()
    return dish


# Helpers for helpers.py compatibility
async def pending_price_versions(session: AsyncSession, dish_id: int) -> list[DishPriceVersion]:
    result = await session.execute(
        select(DishPriceVersion).where(
            DishPriceVersion.dish_id == dish_id, DishPriceVersion.status == VersionStatus.NHAP.value
        )
    )
    return list(result.scalars().all())


async def active_recipe(session: AsyncSession, dish_id: int) -> Recipe | None:
    result = await session.execute(
        select(Recipe)
        .where(Recipe.dish_id == dish_id, Recipe.status == VersionStatus.HIEU_LUC.value)
        .limit(1)
    )
    return result.scalar_one_or_none()


# --- Price versions ---------------------------------------------------------------------------


async def _future_business_date(session: AsyncSession, requested: _date | None) -> _date:
    moment = _bd.now()
    start = await effective_business_day_start(session, moment)
    business_date = requested or _bd.next_business_date(moment, start)
    if business_date <= _bd.business_date_of(moment, start):
        raise BusinessRuleError("BusinessDate áp dụng phải là ngày trong tương lai.")
    return business_date


async def schedule_price_change(
    session: AsyncSession,
    actor_id: int,
    dish_id: int,
    price: _Decimal,
    business_date_val: _date | None = None,
):
    dish = await session.get(Dish, dish_id)
    if dish is None or dish.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    if price is not None and _Decimal(str(price)) <= 0:
        raise BusinessRuleError("Giá phải lớn hơn 0.")
    business_date = await _future_business_date(session, business_date_val)
    # FR-CAT-21: at most one pending change; the older one is cancelled and audited.
    pending = (
        (
            await session.execute(
                select(DishPriceVersion).where(
                    DishPriceVersion.dish_id == dish_id,
                    DishPriceVersion.status == VersionStatus.NHAP.value,
                )
            )
        )
        .scalars()
        .all()
    )
    for old in pending:
        before = _price_state(old)
        old.status = VersionStatus.DA_HUY.value
        _audit(
            session,
            actor_id,
            "CANCEL_PRICE_CHANGE",
            "LICH_SU_GIA_MON",
            old.id,
            before=before,
            after=_price_state(old),
            reason="Bị ghi đè bởi thay đổi giá mới",
        )
    await session.flush()
    version = DishPriceVersion(
        dish_id=dish_id,
        price=price,
        business_date=business_date,
        status=VersionStatus.NHAP.value,
        change_type="Tạo mới",
        created_by=actor_id,
    )
    session.add(version)
    await session.flush()
    _audit(
        session,
        actor_id,
        "SCHEDULE_PRICE_CHANGE",
        "LICH_SU_GIA_MON",
        version.id,
        before=_price_state(pending[-1]) if pending else None,
        after=_price_state(version),
    )
    await session.flush()
    return version


async def cancel_pending_price_change(session: AsyncSession, actor_id: int, version_id: int):
    version = await session.get(DishPriceVersion, version_id)
    if version is None or version.status != VersionStatus.NHAP.value:
        raise NotFoundError("Không tìm thấy phiên bản chờ áp dụng.")
    before = _price_state(version)
    version.status = VersionStatus.DA_HUY.value
    await session.flush()
    _audit(
        session,
        actor_id,
        "CANCEL_PRICE_CHANGE",
        "LICH_SU_GIA_MON",
        version_id,
        before=before,
        after=_price_state(version),
        reason="Quản lý hủy thay đổi chờ áp dụng",
    )
    await session.flush()


async def apply_price_directly(session: AsyncSession, actor_id: int, dish_id: int, price: _Decimal):
    dish = await session.get(Dish, dish_id)
    if dish is None or dish.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    if _Decimal(str(price)) <= 0:
        raise BusinessRuleError("Giá phải lớn hơn 0.")
    moment = _bd.now()
    current = (
        (
            await session.execute(
                select(DishPriceVersion).where(
                    DishPriceVersion.dish_id == dish_id,
                    DishPriceVersion.status == VersionStatus.HIEU_LUC.value,
                )
            )
        )
        .scalars()
        .all()
    )
    before = _price_state(current[-1]) if current else None
    for row in current:
        row.status = VersionStatus.HET_HIEU_LUC.value
        row.effective_to = moment
    await session.flush()
    start = await effective_business_day_start(session, moment)
    version = DishPriceVersion(
        dish_id=dish_id,
        price=price,
        business_date=_bd.business_date_of(moment, start),
        status=VersionStatus.HIEU_LUC.value,
        change_type="Cập nhật",
        created_by=actor_id,
        effective_from=moment,
    )
    session.add(version)
    await session.flush()
    _audit(
        session,
        actor_id,
        "APPLY_PRICE_DIRECTLY",
        "LICH_SU_GIA_MON",
        version.id,
        before=before,
        after=_price_state(version),
    )
    await session.flush()
    return version


# --- Recipe versions --------------------------------------------------------------------------


async def _validated_recipe_items(
    session: AsyncSession, items: list[tuple[int, _Decimal]]
) -> list[tuple[int, _Decimal]]:
    seen: set[int] = set()
    for ingredient_id, quantity in items:
        if _Decimal(str(quantity)) <= 0:
            raise BusinessRuleError("Định lượng phải lớn hơn 0.")
        if ingredient_id in seen:
            raise BusinessRuleError("Nguyên liệu trùng lặp trong cùng công thức.")
        seen.add(ingredient_id)
        ingredient = await session.get(Ingredient, ingredient_id)
        if ingredient is None or ingredient.is_deleted:
            raise BusinessRuleError(f"Nguyên liệu {ingredient_id} không tồn tại.")
    return items


async def _add_recipe(
    session: AsyncSession,
    actor_id: int,
    dish_id: int,
    items: list[tuple[int, _Decimal]],
    *,
    business_date: _date,
    status: str,
    change_type: str,
    effective_from=None,
) -> Recipe:
    last_version = (
        await session.execute(
            select(func.coalesce(func.max(Recipe.version_number), 0)).where(
                Recipe.dish_id == dish_id
            )
        )
    ).scalar_one()
    recipe = Recipe(
        dish_id=dish_id,
        business_date=business_date,
        status=status,
        change_type=change_type,
        created_by=actor_id,
        effective_from=effective_from,
        version_number=int(last_version) + 1,
    )
    session.add(recipe)
    await session.flush()
    for ingredient_id, quantity in items:
        session.add(RecipeItem(recipe_id=recipe.id, ingredient_id=ingredient_id, quantity=quantity))
        ingredient = await session.get(Ingredient, ingredient_id)
        if ingredient is not None:
            ingredient.unit_locked = True
    await session.flush()
    return recipe


async def schedule_recipe_change(
    session: AsyncSession,
    actor_id: int,
    dish_id: int,
    items: list[tuple[int, _Decimal]],
    business_date_val: _date | None = None,
):
    dish = await session.get(Dish, dish_id)
    if dish is None or dish.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    await _validated_recipe_items(session, items)
    business_date = await _future_business_date(session, business_date_val)
    pending = (
        (
            await session.execute(
                select(Recipe).where(
                    Recipe.dish_id == dish_id, Recipe.status == VersionStatus.NHAP.value
                )
            )
        )
        .scalars()
        .all()
    )
    # FR-CAT-09: at most one pending change; the older one is cancelled and audited.
    overwritten = None
    for old in pending:
        overwritten = await _recipe_state(session, old)
        old.status = VersionStatus.DA_HUY.value
        _audit(
            session,
            actor_id,
            "CANCEL_RECIPE_CHANGE",
            "CONG_THUC",
            old.id,
            before=overwritten,
            after=await _recipe_state(session, old),
            reason="Bị ghi đè bởi thay đổi công thức mới",
        )
    await session.flush()
    recipe = await _add_recipe(
        session,
        actor_id,
        dish_id,
        items,
        business_date=business_date,
        status=VersionStatus.NHAP.value,
        change_type="Tạo mới",
    )
    dish.missing_recipe = False
    _audit(
        session,
        actor_id,
        "SCHEDULE_RECIPE_CHANGE",
        "CONG_THUC",
        recipe.id,
        before=overwritten,
        after=await _recipe_state(session, recipe),
    )
    await session.flush()
    return recipe


async def assign_recipe(
    session: AsyncSession, actor_id: int, dish_id: int, items: list[tuple[int, _Decimal]]
):
    """FR-CAT-11: the first recipe takes effect immediately."""
    dish = await session.get(Dish, dish_id)
    if dish is None or dish.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    await _validated_recipe_items(session, items)
    moment = _bd.now()
    start = await effective_business_day_start(session, moment)
    recipe = await _add_recipe(
        session,
        actor_id,
        dish_id,
        items,
        business_date=_bd.business_date_of(moment, start),
        status=VersionStatus.HIEU_LUC.value,
        change_type="Tạo mới",
        effective_from=moment,
    )
    dish.missing_recipe = False
    _audit(
        session,
        actor_id,
        "ASSIGN_RECIPE",
        "CONG_THUC",
        recipe.id,
        after=await _recipe_state(session, recipe),
    )
    await session.flush()
    return recipe


async def apply_recipe_directly(
    session: AsyncSession, actor_id: int, dish_id: int, items: list[tuple[int, _Decimal]]
):
    """FR-CAT-23/24: an immediate correction; a pending scheduled change is left alone."""
    dish = await session.get(Dish, dish_id)
    if dish is None or dish.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    await _validated_recipe_items(session, items)
    moment = _bd.now()
    current = (
        (
            await session.execute(
                select(Recipe).where(
                    Recipe.dish_id == dish_id, Recipe.status == VersionStatus.HIEU_LUC.value
                )
            )
        )
        .scalars()
        .all()
    )
    before = await _recipe_state(session, current[-1]) if current else None
    for row in current:
        row.status = VersionStatus.HET_HIEU_LUC.value
        row.effective_to = moment
    await session.flush()
    start = await effective_business_day_start(session, moment)
    recipe = await _add_recipe(
        session,
        actor_id,
        dish_id,
        items,
        business_date=_bd.business_date_of(moment, start),
        status=VersionStatus.HIEU_LUC.value,
        change_type="Cập nhật",
        effective_from=moment,
    )
    dish.missing_recipe = False
    _audit(
        session,
        actor_id,
        "APPLY_RECIPE_DIRECTLY",
        "CONG_THUC",
        recipe.id,
        before=before,
        after=await _recipe_state(session, recipe),
    )
    await session.flush()
    return recipe


async def cancel_pending_recipe_change(session: AsyncSession, actor_id: int, recipe_id: int):
    recipe = await session.get(Recipe, recipe_id)
    if recipe is None or recipe.status != VersionStatus.NHAP.value:
        raise NotFoundError("Không tìm thấy phiên bản chờ áp dụng.")
    before = await _recipe_state(session, recipe)
    recipe.status = VersionStatus.DA_HUY.value
    await session.flush()
    _audit(
        session,
        actor_id,
        "CANCEL_RECIPE_CHANGE",
        "CONG_THUC",
        recipe_id,
        before=before,
        after=await _recipe_state(session, recipe),
        reason="Quản lý hủy thay đổi chờ áp dụng",
    )
    await session.flush()


async def promote_and_commit(session: AsyncSession, dish_id: int | None = None) -> None:
    """For read endpoints: promote what is due and persist it, since a GET never commits."""
    if await promote_due_versions(session, dish_id=dish_id):
        await session.commit()


# --- Ingredients & suppliers ------------------------------------------------------------------


async def default_stock_threshold(session: AsyncSession) -> float:
    from app.modules.settings.models import SystemConfig

    config = (await session.execute(select(SystemConfig))).scalar_one_or_none()
    return float(config.default_stock_threshold) if config else 5.0


async def create_ingredient(
    session: AsyncSession,
    actor_id: int,
    name: str,
    unit: str = "kg",
    min_stock: float | None = None,
) -> Ingredient:
    # FR-CAT-12: no own threshold means NULL, so the live system default applies (0 is a value).
    ingredient = Ingredient(
        name=name,
        unit=unit,
        min_stock=None if min_stock is None else _Decimal(str(min_stock)),
        stock_qty=0,
        is_deleted=False,
        unit_locked=False,
    )
    session.add(ingredient)
    await session.flush()
    _audit(
        session,
        actor_id,
        "CREATE_INGREDIENT",
        "NGUYEN_LIEU",
        ingredient.id,
        after=_ingredient_state(ingredient),
    )
    await session.flush()
    return ingredient


async def update_ingredient(
    session: AsyncSession,
    actor_id: int,
    ingredient_id: int,
    name: str | None = None,
    unit: str | None = None,
    min_stock: float | None = None,
    min_stock_provided: bool | None = None,
) -> Ingredient:
    """`min_stock_provided` lets a caller reset the threshold to the default by sending null."""
    ingredient = await session.get(Ingredient, ingredient_id)
    if ingredient is None or ingredient.is_deleted:
        raise NotFoundError("Không tìm thấy nguyên liệu.")
    before = _ingredient_state(ingredient)
    if unit is not None and unit != ingredient.unit:
        if ingredient.unit_locked:
            raise BusinessRuleError("Không thể đổi đơn vị tính sau khi đã được sử dụng.")
        ingredient.unit = unit
    if name is not None:
        ingredient.name = name
    if min_stock is not None or min_stock_provided:
        ingredient.min_stock = None if min_stock is None else _Decimal(str(min_stock))
    await session.flush()
    _audit(
        session,
        actor_id,
        "UPDATE_INGREDIENT",
        "NGUYEN_LIEU",
        ingredient.id,
        before=before,
        after=_ingredient_state(ingredient),
    )
    await session.flush()
    return ingredient


async def delete_ingredient(session: AsyncSession, actor_id: int, ingredient_id: int):
    from app.modules.inventory.models import GoodsReceiptLine

    ingredient = await session.get(Ingredient, ingredient_id)
    if ingredient is None or ingredient.is_deleted:
        raise NotFoundError("Không tìm thấy nguyên liệu.")
    before = _ingredient_state(ingredient)
    referenced = (
        await session.execute(
            select(RecipeItem.recipe_id).where(RecipeItem.ingredient_id == ingredient_id).limit(1)
        )
    ).scalar_one_or_none() is not None or (
        await session.execute(
            select(GoodsReceiptLine.id)
            .where(GoodsReceiptLine.ingredient_id == ingredient_id)
            .limit(1)
        )
    ).scalar_one_or_none() is not None
    if referenced:
        ingredient.is_deleted = True
        after = _ingredient_state(ingredient)
    else:
        await session.delete(ingredient)
        after = None
    await session.flush()
    _audit(
        session,
        actor_id,
        "DELETE_INGREDIENT",
        "NGUYEN_LIEU",
        ingredient_id,
        before=before,
        after=after,
    )
    await session.flush()
    return ingredient if referenced else None


async def list_ingredients(session: AsyncSession, search: str | None = None):
    query = select(Ingredient).where(Ingredient.is_deleted.is_(False))
    if search:
        query = query.where(Ingredient.name.ilike(f"%{search}%"))
    result = await session.execute(query.order_by(Ingredient.id))
    items = list(result.scalars().all())
    return items, len(items)


async def effective_min_stock(session: AsyncSession, ingredient: Ingredient) -> float:
    """FR-SET-05: the ingredient's own threshold, else the live system default."""
    if ingredient.min_stock is not None:
        return float(ingredient.min_stock)
    return await default_stock_threshold(session)


async def create_supplier(
    session: AsyncSession,
    actor_id: int,
    name: str,
    phone: str | None = None,
    contact_name: str | None = None,
    email: str | None = None,
    address: str | None = None,
) -> Supplier:
    supplier = Supplier(
        name=name,
        phone=phone,
        contact_name=contact_name,
        email=email,
        address=address,
        is_deleted=False,
    )
    session.add(supplier)
    await session.flush()
    _audit(
        session,
        actor_id,
        "CREATE_SUPPLIER",
        "NHA_CUNG_CAP",
        supplier.id,
        after=_supplier_state(supplier),
    )
    await session.flush()
    return supplier


async def update_supplier(
    session: AsyncSession,
    actor_id: int,
    supplier_id: int,
    name: str | None = None,
    phone: str | None = None,
    contact_name: str | None = None,
    email: str | None = None,
    address: str | None = None,
) -> Supplier:
    supplier = await session.get(Supplier, supplier_id)
    if supplier is None or supplier.is_deleted:
        raise NotFoundError("Không tìm thấy nhà cung cấp.")
    before = _supplier_state(supplier)
    if name is not None:
        supplier.name = name
    if phone is not None:
        supplier.phone = phone
    if contact_name is not None:
        supplier.contact_name = contact_name
    if email is not None:
        supplier.email = email
    if address is not None:
        supplier.address = address
    await session.flush()
    _audit(
        session,
        actor_id,
        "UPDATE_SUPPLIER",
        "NHA_CUNG_CAP",
        supplier.id,
        before=before,
        after=_supplier_state(supplier),
    )
    await session.flush()
    return supplier


async def delete_supplier(session: AsyncSession, actor_id: int, supplier_id: int):
    from app.modules.inventory.models import GoodsReceipt

    supplier = await session.get(Supplier, supplier_id)
    if supplier is None or supplier.is_deleted:
        raise NotFoundError("Không tìm thấy nhà cung cấp.")
    before = _supplier_state(supplier)
    has_history = (
        await session.execute(
            select(GoodsReceipt.id).where(GoodsReceipt.supplier_id == supplier_id).limit(1)
        )
    ).scalar_one_or_none() is not None
    if has_history:
        supplier.is_deleted = True
        after = _supplier_state(supplier)
    else:
        await session.delete(supplier)
        after = None
    await session.flush()
    _audit(
        session,
        actor_id,
        "DELETE_SUPPLIER",
        "NHA_CUNG_CAP",
        supplier_id,
        before=before,
        after=after,
    )
    await session.flush()
    return supplier if has_history else None


async def get_supplier(session: AsyncSession, supplier_id: int):
    return await session.get(Supplier, supplier_id)


async def list_suppliers(session: AsyncSession):
    result = await session.execute(
        select(Supplier).where(Supplier.is_deleted.is_(False)).order_by(Supplier.id)
    )
    return list(result.scalars().all())


# --- Tables (FR-CAT-17..19) -------------------------------------------------------------------


async def _ensure_table_name_free(
    session: AsyncSession, name: str, *, excluding: int | None = None
) -> None:
    query = select(DiningTable.id).where(
        DiningTable.name == name, DiningTable.is_deleted.is_(False)
    )
    if excluding is not None:
        query = query.where(DiningTable.id != excluding)
    if (await session.execute(query.limit(1))).scalar_one_or_none() is not None:
        raise ConflictError("Tên bàn đã tồn tại.")


async def create_table(
    session: AsyncSession, actor_id: int, name: str, capacity: int | None = None
) -> DiningTable:
    await _ensure_table_name_free(session, name)
    table = DiningTable(name=name, capacity=capacity, is_deleted=False)
    session.add(table)
    await session.flush()
    _audit(session, actor_id, "CREATE_TABLE", "BAN", table.id, after=_table_state(table))
    await session.flush()
    return table


async def update_table(
    session: AsyncSession,
    actor_id: int,
    table_id: int,
    name: str | None = None,
    capacity: int | None = None,
) -> DiningTable:
    table = await session.get(DiningTable, table_id)
    if table is None or table.is_deleted:
        raise NotFoundError("Không tìm thấy bàn.")
    before = _table_state(table)
    if name is not None and name != table.name:
        await _ensure_table_name_free(session, name, excluding=table_id)
        table.name = name
    if capacity is not None:
        table.capacity = capacity
    await session.flush()
    _audit(
        session,
        actor_id,
        "UPDATE_TABLE",
        "BAN",
        table.id,
        before=before,
        after=_table_state(table),
    )
    await session.flush()
    return table


async def delete_table(session: AsyncSession, actor_id: int, table_id: int):
    """FR-CAT-19: never while serving; removed for good only if no order ever used it."""
    from app.modules.sales.models import ItemHold, Order, TableMoveLog

    table = await session.get(DiningTable, table_id)
    if table is None or table.is_deleted:
        raise NotFoundError("Không tìm thấy bàn.")
    unfinished = (
        await session.execute(
            select(Order.id)
            .where(Order.table_id == table_id, Order.status.notin_(FINISHED_ORDER_STATUSES))
            .limit(1)
        )
    ).scalar_one_or_none()
    if table.status == "Đang phục vụ" or table.serving_order_id is not None or unfinished:
        raise BusinessRuleError("Không thể xóa bàn đang được sử dụng.")
    used = False
    for column, condition in (
        (Order.id, Order.table_id == table_id),
        (
            TableMoveLog.id,
            (TableMoveLog.from_table == table_id) | (TableMoveLog.to_table == table_id),
        ),
        (ItemHold.id, ItemHold.table_id == table_id),
    ):
        if (await session.execute(select(column).where(condition).limit(1))).first() is not None:
            used = True
            break
    before = _table_state(table)
    if used:
        table.is_deleted = True
        after = _table_state(table)
    else:
        await session.delete(table)
        after = None
    await session.flush()
    _audit(session, actor_id, "DELETE_TABLE", "BAN", table_id, before=before, after=after)
    await session.flush()


async def release_table(
    session: AsyncSession, actor_id: int, table_id: int, order_id: int | None = None
) -> DiningTable:
    """FR-CAT-18: the cashier confirms the guests left.

    Only applies while the table is still bound to the order being released, so a late
    payment of an old order can never free the table of a new one.
    """
    from app.modules.sales.models import ItemHold

    query = select(DiningTable).where(DiningTable.id == table_id)
    if session.get_bind().dialect.name == "mysql":
        query = query.with_for_update().execution_options(populate_existing=True)
    table = (await session.execute(query)).scalar_one_or_none()
    if table is None or table.is_deleted:
        raise NotFoundError("Không tìm thấy bàn.")
    if table.status != "Đang phục vụ":
        raise BusinessRuleError("Bàn đang trống.")
    if order_id is not None and table.serving_order_id not in (None, order_id):
        raise ConflictError("Bàn đã được gắn với order khác, không thể giải phóng.")
    before = _table_state(table)
    table.status = "Trống"
    table.serving_order_id = None
    # Unsent add-on selections of the departed order stop holding stock.
    await session.execute(
        update(ItemHold)
        .where(
            ItemHold.table_id == table_id,
            ItemHold.order_id.is_not(None),
            ItemHold.status == "Đang giữ",
        )
        .values(status="Đã hủy")
        .execution_options(synchronize_session="fetch")
    )
    await session.flush()
    _audit(
        session,
        actor_id,
        "RELEASE_TABLE",
        "BAN",
        table_id,
        before=before,
        after=_table_state(table),
    )
    await session.flush()
    return table


async def list_tables(session: AsyncSession):
    result = await session.execute(
        select(DiningTable).where(DiningTable.is_deleted.is_(False)).order_by(DiningTable.id)
    )
    return list(result.scalars().all())
