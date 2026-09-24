"""Catalog service — Task 1: groups & dishes."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.modules.catalog.models import Dish, DishGroup, DishPriceVersion, Recipe
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
