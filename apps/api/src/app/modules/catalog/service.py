"""Catalog service — Task 1: groups & dishes."""

from datetime import date as _date
from decimal import Decimal as _Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.catalog.models import Dish, DishGroup, DishPriceVersion, Recipe
from app.shared import business_date as _bd
from app.shared.audit import SystemAuditLog
from app.shared.enums import VersionStatus


async def _has_active_recipe(session: AsyncSession, dish_id: int) -> bool:
    r = await session.execute(
        select(Recipe.id)
        .where(Recipe.dish_id == dish_id, Recipe.status == VersionStatus.HIEU_LUC.value)
        .limit(1)
    )
    return r.scalar_one_or_none() is not None


async def display_status_for(session: AsyncSession, dish: Dish) -> str:
    if dish.is_deleted:
        return "Đã xóa"
    if dish.hide_manual:
        return "Ẩn thủ công"
    # Nháp if no active recipe
    if not await _has_active_recipe(session, dish.id):
        return "Nháp"
    # otherwise derive from flags (GENERATED column would give same)
    if dish.out_of_stock_manual or dish.out_of_stock_auto:
        return "Hết nguyên liệu"
    return "Hoạt động"


# Groups
async def create_group(session: AsyncSession, actor_id: int, name: str) -> DishGroup:
    max_order = (
        await session.execute(
            select(func.coalesce(func.max(DishGroup.display_order), 0)).where(
                DishGroup.is_deleted == False
            )
        )
    ).scalar_one()
    g = DishGroup(name=name, display_order=int(max_order) + 1, is_deleted=False)
    session.add(g)
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id, action="CREATE_GROUP", target_entity="NHOM_MON", target_id=str(g.id)
        )
    )
    await session.flush()
    return g


async def list_groups(session: AsyncSession) -> list[DishGroup]:
    r = await session.execute(
        select(DishGroup).where(DishGroup.is_deleted == False).order_by(DishGroup.display_order)
    )
    return list(r.scalars().all())


async def update_group(
    session: AsyncSession, actor_id: int, group_id: int, name: str | None
) -> DishGroup:
    g = await session.get(DishGroup, group_id)
    if g is None or g.is_deleted:
        raise NotFoundError("Không tìm thấy nhóm món.")
    if name is not None:
        g.name = name
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id, action="UPDATE_GROUP", target_entity="NHOM_MON", target_id=str(g.id)
        )
    )
    await session.flush()
    return g


async def delete_group(session: AsyncSession, actor_id: int, group_id: int) -> None:
    g = await session.get(DishGroup, group_id)
    if g is None or g.is_deleted:
        raise NotFoundError("Không tìm thấy nhóm món.")
    cnt = (
        await session.execute(
            select(func.count())
            .select_from(Dish)
            .where(Dish.group_id == group_id, Dish.is_deleted == False)
        )
    ).scalar_one()
    if cnt > 0:
        raise BusinessRuleError("Không thể xóa nhóm còn món đang hoạt động.")
    g.is_deleted = True
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id, action="DELETE_GROUP", target_entity="NHOM_MON", target_id=str(g.id)
        )
    )
    await session.flush()


async def reorder_groups(
    session: AsyncSession, actor_id: int, ordered_ids: list[int]
) -> list[DishGroup]:
    existing = await list_groups(session)
    existing_ids = [g.id for g in existing]
    if set(ordered_ids) != set(existing_ids) or len(ordered_ids) != len(existing_ids):
        raise BusinessRuleError("Danh sách sắp xếp phải chứa đủ các nhóm đang hoạt động.")
    id_to_group = {g.id: g for g in existing}
    for idx, gid in enumerate(ordered_ids, start=1):
        id_to_group[gid].display_order = idx
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="REORDER_GROUPS",
            target_entity="NHOM_MON",
            target_id=",".join(map(str, ordered_ids)),
        )
    )
    await session.flush()
    return [id_to_group[gid] for gid in ordered_ids]


# Dishes
async def create_dish(
    session: AsyncSession,
    actor_id: int,
    name: str,
    group_id: int | None,
    image: str | None = None,
    price: float | None = None,
) -> Dish:
    if group_id is not None:
        g = await session.get(DishGroup, group_id)
        if g is None or g.is_deleted:
            raise BusinessRuleError("Nhóm món không tồn tại.")
    d = Dish(
        name=name,
        group_id=group_id,
        image_url=image,
        hide_manual=False,
        out_of_stock_manual=False,
        out_of_stock_auto=False,
        is_deleted=False,
    )
    session.add(d)
    await session.flush()
    # price not stored in MON_AN in this phase; GiaHienTai is derived from active price version (placeholder)
    session.add(
        SystemAuditLog(
            user_id=actor_id, action="CREATE_DISH", target_entity="MON_AN", target_id=str(d.id)
        )
    )
    await session.flush()
    return d


async def get_dish(session: AsyncSession, dish_id: int) -> Dish | None:
    return await session.get(Dish, dish_id)


async def list_dishes(session: AsyncSession, search: str | None = None) -> tuple[list[Dish], int]:
    q = select(Dish).where(Dish.is_deleted == False)
    cq = select(func.count()).select_from(Dish).where(Dish.is_deleted == False)
    if search:
        like = f"%{search}%"
        q = q.where(Dish.name.ilike(like))
        cq = cq.where(Dish.name.ilike(like))
    total = (await session.execute(cq)).scalar_one()
    r = await session.execute(q.order_by(Dish.id))
    return list(r.scalars().all()), total


async def update_dish(
    session: AsyncSession,
    actor_id: int,
    dish_id: int,
    name: str | None = None,
    group_id: int | None = None,
    image: str | None = None,
    image_provided: bool = False,
) -> Dish:
    d = await session.get(Dish, dish_id)
    if d is None or d.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    if name is not None:
        d.name = name
    if group_id is not None:
        g = await session.get(DishGroup, group_id)
        if g is None or g.is_deleted:
            raise BusinessRuleError("Nhóm món không tồn tại.")
        d.group_id = group_id
    if image_provided:
        d.image_url = image
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id, action="UPDATE_DISH", target_entity="MON_AN", target_id=str(d.id)
        )
    )
    await session.flush()
    return d


async def delete_dish(session: AsyncSession, actor_id: int, dish_id: int) -> Dish:
    d = await session.get(Dish, dish_id)
    if d is None or d.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    d.is_deleted = True
    await session.flush()
    # cancel pending price/recipe versions (FR-CAT-05)
    for row in (
        (
            await session.execute(
                select(DishPriceVersion).where(
                    DishPriceVersion.dish_id == dish_id, DishPriceVersion.status == "Nháp"
                )
            )
        )
        .scalars()
        .all()
    ):
        row.status = "Hết hiệu lực"
    for row2 in (
        (
            await session.execute(
                select(Recipe).where(Recipe.dish_id == dish_id, Recipe.status == "Nháp")
            )
        )
        .scalars()
        .all()
    ):
        row2.status = "Hết hiệu lực"
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id, action="DELETE_DISH", target_entity="MON_AN", target_id=str(d.id)
        )
    )
    await session.flush()
    return d


# Helpers for helpers.py compatibility
async def pending_price_versions(session: AsyncSession, dish_id: int) -> list[DishPriceVersion]:
    r = await session.execute(
        select(DishPriceVersion).where(
            DishPriceVersion.dish_id == dish_id, DishPriceVersion.status == "Nháp"
        )
    )
    return list(r.scalars().all())


async def active_recipe(session: AsyncSession, dish_id: int) -> Recipe | None:
    r = await session.execute(
        select(Recipe)
        .where(Recipe.dish_id == dish_id, Recipe.status == VersionStatus.HIEU_LUC.value)
        .limit(1)
    )
    return r.scalar_one_or_none()


# --- Price versions (Task 2) ---


async def schedule_price_change(
    session, actor_id: int, dish_id: int, price: _Decimal, business_date_val: _date | None = None
):
    from app.modules.catalog.models import Dish as _Dish

    d = await session.get(_Dish, dish_id)
    if d is None or d.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    if price is not None and _Decimal(str(price)) <= 0:
        raise BusinessRuleError("Giá phải lớn hơn 0.")
    bd = business_date_val or _bd.next_business_date(_bd.now())
    # must be future
    current_bd = _bd.business_date_of(_bd.now())
    if bd <= current_bd:
        raise BusinessRuleError("BusinessDate áp dụng phải là ngày trong tương lai.")
    # only one pending: delete existing Nháp
    for row in (
        (
            await session.execute(
                select(DishPriceVersion).where(
                    DishPriceVersion.dish_id == dish_id, DishPriceVersion.status == "Nháp"
                )
            )
        )
        .scalars()
        .all()
    ):
        await session.delete(row)
    await session.flush()
    v = DishPriceVersion(
        dish_id=dish_id,
        price=float(price),
        business_date=bd,
        status="Nháp",
        change_type="Tạo mới",
        created_by=actor_id,
    )
    session.add(v)
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="SCHEDULE_PRICE_CHANGE",
            target_entity="LICH_SU_GIA_MON",
            target_id=str(v.id),
        )
    )
    await session.flush()
    return v


async def cancel_pending_price_change(session, actor_id: int, version_id: int):
    v = await session.get(DishPriceVersion, version_id)
    if v is None or v.status != "Nháp":
        raise NotFoundError("Không tìm thấy phiên bản chờ áp dụng.")
    await session.delete(v)
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CANCEL_PRICE_CHANGE",
            target_entity="LICH_SU_GIA_MON",
            target_id=str(version_id),
        )
    )
    await session.flush()


async def apply_price_directly(session, actor_id: int, dish_id: int, price: _Decimal):
    from app.modules.catalog.models import Dish as _Dish

    d = await session.get(_Dish, dish_id)
    if d is None or d.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    if _Decimal(str(price)) <= 0:
        raise BusinessRuleError("Giá phải lớn hơn 0.")
    # close current active
    cur = await session.execute(
        select(DishPriceVersion).where(
            DishPriceVersion.dish_id == dish_id, DishPriceVersion.status == "Hiệu lực"
        )
    )
    for row in cur.scalars().all():
        row.status = "Hết hiệu lực"
        row.effective_to = _bd.now()
    await session.flush()
    bd = _bd.business_date_of(_bd.now())
    v = DishPriceVersion(
        dish_id=dish_id,
        price=float(price),
        business_date=bd,
        status="Hiệu lực",
        change_type="Cập nhật",
        created_by=actor_id,
        effective_from=_bd.now(),
    )
    session.add(v)
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="APPLY_PRICE_DIRECTLY",
            target_entity="LICH_SU_GIA_MON",
            target_id=str(v.id),
        )
    )
    await session.flush()
    return v


# --- Recipe (Task 3) ---
async def schedule_recipe_change(
    session,
    actor_id: int,
    dish_id: int,
    items: list[tuple[int, _Decimal]],
    business_date_val: _date | None = None,
):
    from app.modules.catalog.models import Ingredient as _Ing
    from app.modules.catalog.models import RecipeItem as _RI

    d = await session.get(Dish, dish_id)
    if d is None or d.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    for _, qty in items:
        if _Decimal(str(qty)) <= 0:
            raise BusinessRuleError("Định lượng phải lớn hơn 0.")
    bd = business_date_val or _bd.next_business_date(_bd.now())
    current_bd = _bd.business_date_of(_bd.now())
    if bd <= current_bd:
        raise BusinessRuleError("BusinessDate áp dụng phải là ngày trong tương lai.")
    # validate ingredients exist
    for ing_id, _ in items:
        ing = await session.get(_Ing, ing_id)
        if ing is None or ing.is_deleted:
            raise BusinessRuleError(f"Nguyên liệu {ing_id} không tồn tại.")
    # only one pending
    for row in (
        (
            await session.execute(
                select(Recipe).where(Recipe.dish_id == dish_id, Recipe.status == "Nháp")
            )
        )
        .scalars()
        .all()
    ):
        # delete items
        for ri in (
            (await session.execute(select(_RI).where(_RI.recipe_id == row.id))).scalars().all()
        ):
            await session.delete(ri)
        await session.delete(row)
    await session.flush()
    r = Recipe(
        dish_id=dish_id, business_date=bd, status="Nháp", change_type="Tạo mới", created_by=actor_id
    )
    session.add(r)
    await session.flush()
    for ing_id, qty in items:
        session.add(_RI(recipe_id=r.id, ingredient_id=ing_id, quantity=float(qty)))
        # lock unit
        ing = await session.get(_Ing, ing_id)
        if ing:
            ing.unit_locked = True
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="SCHEDULE_RECIPE_CHANGE",
            target_entity="CONG_THUC",
            target_id=str(r.id),
        )
    )
    await session.flush()
    return r


async def assign_recipe(session, actor_id: int, dish_id: int, items: list[tuple[int, _Decimal]]):
    # first recipe: immediate HieuLuc
    from app.modules.catalog.models import Ingredient as _Ing
    from app.modules.catalog.models import RecipeItem as _RI

    d = await session.get(Dish, dish_id)
    if d is None or d.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    for _, qty in items:
        if _Decimal(str(qty)) <= 0:
            raise BusinessRuleError("Định lượng phải lớn hơn 0.")
    for ing_id, _ in items:
        ing = await session.get(_Ing, ing_id)
        if ing is None or ing.is_deleted:
            raise BusinessRuleError(f"Nguyên liệu {ing_id} không tồn tại.")
    bd = _bd.business_date_of(_bd.now())
    r = Recipe(
        dish_id=dish_id,
        business_date=bd,
        status="Hiệu lực",
        change_type="Tạo mới",
        created_by=actor_id,
        effective_from=_bd.now(),
    )
    session.add(r)
    await session.flush()
    for ing_id, qty in items:
        session.add(_RI(recipe_id=r.id, ingredient_id=ing_id, quantity=float(qty)))
        ing = await session.get(_Ing, ing_id)
        if ing:
            ing.unit_locked = True
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id, action="ASSIGN_RECIPE", target_entity="CONG_THUC", target_id=str(r.id)
        )
    )
    await session.flush()
    return r


async def apply_recipe_directly(
    session, actor_id: int, dish_id: int, items: list[tuple[int, _Decimal]]
):
    from app.modules.catalog.models import Ingredient as _Ing
    from app.modules.catalog.models import RecipeItem as _RI

    d = await session.get(Dish, dish_id)
    if d is None or d.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    for _, qty in items:
        if _Decimal(str(qty)) <= 0:
            raise BusinessRuleError("Định lượng phải lớn hơn 0.")
    for ing_id, _ in items:
        ing = await session.get(_Ing, ing_id)
        if ing is None or ing.is_deleted:
            raise BusinessRuleError(f"Nguyên liệu {ing_id} không tồn tại.")
    # close current active (Nháp pending changes are untouched — FR-CAT-24)
    cur = await session.execute(
        select(Recipe).where(Recipe.dish_id == dish_id, Recipe.status == "Hiệu lực")
    )
    for row in cur.scalars().all():
        row.status = "Hết hiệu lực"
        row.effective_to = _bd.now()
    await session.flush()
    bd = _bd.business_date_of(_bd.now())
    r = Recipe(
        dish_id=dish_id,
        business_date=bd,
        status="Hiệu lực",
        change_type="Cập nhật",
        created_by=actor_id,
        effective_from=_bd.now(),
    )
    session.add(r)
    await session.flush()
    for ing_id, qty in items:
        session.add(_RI(recipe_id=r.id, ingredient_id=ing_id, quantity=float(qty)))
        ing = await session.get(_Ing, ing_id)
        if ing:
            ing.unit_locked = True
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="APPLY_RECIPE_DIRECTLY",
            target_entity="CONG_THUC",
            target_id=str(r.id),
        )
    )
    await session.flush()
    return r


async def cancel_pending_recipe_change(session, actor_id: int, recipe_id: int):
    from app.modules.catalog.models import RecipeItem as _RI

    r = await session.get(Recipe, recipe_id)
    if r is None or r.status != "Nháp":
        raise NotFoundError("Không tìm thấy phiên bản chờ áp dụng.")
    for ri in (
        (await session.execute(select(_RI).where(_RI.recipe_id == recipe_id))).scalars().all()
    ):
        await session.delete(ri)
    await session.delete(r)
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CANCEL_RECIPE_CHANGE",
            target_entity="CONG_THUC",
            target_id=str(recipe_id),
        )
    )
    await session.flush()


# --- Ingredients & Suppliers (Task 4) ---
async def create_ingredient(
    session, actor_id: int, name: str, unit: str = "kg", min_stock: float | None = None
):
    from app.modules.catalog.models import Ingredient as _Ing
    from app.modules.settings.models import SystemConfig

    if min_stock is None:
        cfg = (await session.execute(select(SystemConfig))).scalar_one_or_none()
        min_stock = float(cfg.default_stock_threshold) if cfg else 5
    ing = _Ing(
        name=name,
        unit=unit,
        min_stock=float(min_stock),
        stock_qty=0,
        is_deleted=False,
        unit_locked=False,
    )
    session.add(ing)
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CREATE_INGREDIENT",
            target_entity="NGUYEN_LIEU",
            target_id=str(ing.id),
        )
    )
    await session.flush()
    return ing


async def update_ingredient(
    session,
    actor_id: int,
    ing_id: int,
    name: str | None = None,
    unit: str | None = None,
    min_stock: float | None = None,
):
    from app.modules.catalog.models import Ingredient as _Ing

    ing = await session.get(_Ing, ing_id)
    if ing is None or ing.is_deleted:
        raise NotFoundError("Không tìm thấy nguyên liệu.")
    if unit is not None and unit != ing.unit:
        if ing.unit_locked:
            raise BusinessRuleError("Không thể đổi đơn vị tính sau khi đã được sử dụng.")
        ing.unit = unit
    if name is not None:
        ing.name = name
    if min_stock is not None:
        ing.min_stock = float(min_stock)
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="UPDATE_INGREDIENT",
            target_entity="NGUYEN_LIEU",
            target_id=str(ing.id),
        )
    )
    await session.flush()
    return ing


async def delete_ingredient(session, actor_id: int, ing_id: int):
    from app.modules.catalog.models import Ingredient as _Ing
    from app.modules.catalog.models import RecipeItem as _RI

    ing = await session.get(_Ing, ing_id)
    if ing is None or ing.is_deleted:
        raise NotFoundError("Không tìm thấy nguyên liệu.")
    # check referenced
    ref = (
        await session.execute(select(_RI).where(_RI.ingredient_id == ing_id).limit(1))
    ).scalar_one_or_none()
    if ref is not None:
        ing.is_deleted = True
        await session.flush()
        session.add(
            SystemAuditLog(
                user_id=actor_id,
                action="DELETE_INGREDIENT",
                target_entity="NGUYEN_LIEU",
                target_id=str(ing.id),
            )
        )
        await session.flush()
        return ing
    # also check inventory lots
    from app.modules.inventory.models import GoodsReceiptLine as _GRL

    ref2 = (
        await session.execute(select(_GRL).where(_GRL.ingredient_id == ing_id).limit(1))
    ).scalar_one_or_none()
    if ref2 is not None:
        ing.is_deleted = True
        await session.flush()
        session.add(
            SystemAuditLog(
                user_id=actor_id,
                action="DELETE_INGREDIENT",
                target_entity="NGUYEN_LIEU",
                target_id=str(ing.id),
            )
        )
        await session.flush()
        return ing
    await session.delete(ing)
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="DELETE_INGREDIENT",
            target_entity="NGUYEN_LIEU",
            target_id=str(ing_id),
        )
    )
    await session.flush()


async def list_ingredients(session, search: str | None = None):
    from app.modules.catalog.models import Ingredient as _Ing

    q = select(_Ing).where(_Ing.is_deleted == False)
    if search:
        q = q.where(_Ing.name.ilike(f"%{search}%"))
    r = await session.execute(q.order_by(_Ing.id))
    items = list(r.scalars().all())
    return items, len(items)


async def effective_min_stock(session, ingredient) -> float:
    if ingredient.min_stock and float(ingredient.min_stock) > 0:
        return float(ingredient.min_stock)
    from app.modules.settings.models import SystemConfig

    cfg = (await session.execute(select(SystemConfig))).scalar_one_or_none()
    return float(cfg.default_stock_threshold) if cfg else 5


async def create_supplier(session, actor_id: int, name: str, phone: str | None = None):
    from app.modules.catalog.models import Supplier as _Sup

    s = _Sup(name=name, phone=phone, is_deleted=False)
    session.add(s)
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CREATE_SUPPLIER",
            target_entity="NHA_CUNG_CAP",
            target_id=str(s.id),
        )
    )
    await session.flush()
    return s


async def update_supplier(
    session,
    actor_id: int,
    sup_id: int,
    name: str | None = None,
    phone: str | None = None,
):
    from app.modules.catalog.models import Supplier as _Sup

    s = await session.get(_Sup, sup_id)
    if s is None or s.is_deleted:
        raise NotFoundError("Không tìm thấy nhà cung cấp.")
    if name is not None:
        s.name = name
    if phone is not None:
        s.phone = phone
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="UPDATE_SUPPLIER",
            target_entity="NHA_CUNG_CAP",
            target_id=str(s.id),
        )
    )
    await session.flush()
    return s


async def delete_supplier(session, actor_id: int, sup_id: int):
    from app.modules.catalog.models import Supplier as _Sup
    from app.modules.inventory.models import GoodsReceipt as _GR

    s = await session.get(_Sup, sup_id)
    if s is None or s.is_deleted:
        raise NotFoundError("Không tìm thấy nhà cung cấp.")
    has = (
        await session.execute(select(_GR).where(_GR.supplier_id == sup_id).limit(1))
    ).scalar_one_or_none()
    if has is not None:
        s.is_deleted = True
        await session.flush()
        session.add(
            SystemAuditLog(
                user_id=actor_id,
                action="DELETE_SUPPLIER",
                target_entity="NHA_CUNG_CAP",
                target_id=str(s.id),
            )
        )
        await session.flush()
        return s
    await session.delete(s)
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="DELETE_SUPPLIER",
            target_entity="NHA_CUNG_CAP",
            target_id=str(sup_id),
        )
    )
    await session.flush()


async def get_supplier(session, sup_id: int):
    from app.modules.catalog.models import Supplier as _Sup

    return await session.get(_Sup, sup_id)


async def list_suppliers(session):
    from app.modules.catalog.models import Supplier as _Sup

    r = await session.execute(select(_Sup).where(_Sup.is_deleted == False).order_by(_Sup.id))
    return list(r.scalars().all())


# --- Tables & visibility (Task 5) ---
async def create_table(session, actor_id: int, name: str):
    from app.modules.catalog.models import DiningTable as _T

    t = _T(name=name, is_deleted=False)
    session.add(t)
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id, action="CREATE_TABLE", target_entity="BAN", target_id=str(t.id)
        )
    )
    await session.flush()
    return t


async def delete_table(session, actor_id: int, table_id: int):
    from app.modules.catalog.models import DiningTable as _T

    t = await session.get(_T, table_id)
    if t is None or t.is_deleted:
        raise NotFoundError("Không tìm thấy bàn.")
    # check if in use: any ORDER with TrangThai != Da thanh toan / Da huy and MaBan == table_id
    from app.modules.sales.models import Order as _O

    has = (
        await session.execute(
            select(_O)
            .where(_O.table_id == table_id, _O.status.notin_(["Đã thanh toán", "Đã hủy"]))
            .limit(1)
        )
    ).scalar_one_or_none()
    if has is not None:
        raise BusinessRuleError("Không thể xóa bàn đang được sử dụng.")
    t.is_deleted = True
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id, action="DELETE_TABLE", target_entity="BAN", target_id=str(t.id)
        )
    )
    await session.flush()


async def list_tables(session):
    from app.modules.catalog.models import DiningTable as _T

    r = await session.execute(select(_T).where(_T.is_deleted == False).order_by(_T.id))
    return list(r.scalars().all())


async def set_manual_hidden(session, actor_id: int, dish_id: int, value: bool):
    d = await session.get(Dish, dish_id)
    if d is None or d.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    d.hide_manual = value
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="SET_MANUAL_HIDDEN",
            target_entity="MON_AN",
            target_id=str(dish_id),
        )
    )
    await session.flush()
    return d


async def set_manual_out_of_stock(session, actor_id: int, dish_id: int, value: bool):
    d = await session.get(Dish, dish_id)
    if d is None or d.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    d.out_of_stock_manual = value
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="SET_MANUAL_OUT_OF_STOCK",
            target_entity="MON_AN",
            target_id=str(dish_id),
        )
    )
    await session.flush()
    return d
