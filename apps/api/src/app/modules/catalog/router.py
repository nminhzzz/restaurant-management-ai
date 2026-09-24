"""HTTP layer for the catalogue module."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import Principal, get_current_user, require_roles
from app.modules.catalog import service as svc
from app.modules.catalog.schemas import (
    DishCreate,
    DishOut,
    DishUpdate,
    GroupCreate,
    GroupOut,
    GroupReorderRequest,
    GroupUpdate,
)
from app.shared.pagination import Page
from app.shared.roles import Role

router = APIRouter(prefix="/catalog", tags=["Module 1 — Catalogue"])


# Groups
@router.get("/groups", response_model=list[GroupOut])
async def list_groups(
    user: Principal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[GroupOut]:
    items = await svc.list_groups(session)
    return [GroupOut.model_validate(x) for x in items]


@router.post("/groups", response_model=GroupOut, status_code=201)
async def create_group(
    payload: GroupCreate,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> GroupOut:
    g = await svc.create_group(session, user.user_id, payload.TenNhom)
    await session.commit()
    return GroupOut.model_validate(g)


@router.put("/groups/order", response_model=list[GroupOut])
async def reorder_groups(
    payload: GroupReorderRequest,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> list[GroupOut]:
    items = await svc.reorder_groups(session, user.user_id, payload.MaNhomMon)
    await session.commit()
    return [GroupOut.model_validate(x) for x in items]


@router.patch("/groups/{group_id}", response_model=GroupOut)
async def update_group(
    group_id: int,
    payload: GroupUpdate,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> GroupOut:
    g = await svc.update_group(session, user.user_id, group_id, payload.TenNhom)
    await session.commit()
    return GroupOut.model_validate(g)


@router.delete("/groups/{group_id}", status_code=204)
async def delete_group(
    group_id: int,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> None:
    await svc.delete_group(session, user.user_id, group_id)
    await session.commit()


# Dishes
@router.get("/dishes", response_model=Page[DishOut])
async def list_dishes(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    user: Principal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Page[DishOut]:
    items, total = await svc.list_dishes(session, search)
    # paginate in memory (small dataset for Task 1)
    start = (page - 1) * size
    sliced = items[start : start + size]
    out: list[DishOut] = []
    for d in sliced:
        status = await svc.display_status_for(session, d)
        out.append(
            DishOut(
                MaMon=d.id,
                TenMon=d.name,
                MaNhomMon=d.group_id,
                HinhAnh=None,
                GiaHienTai=None,
                TrangThai=status,
                AnThuCong=d.hide_manual,
                DaXoa=d.is_deleted,
            )
        )
    return Page[DishOut](items=out, total=total, page=page, size=size)


@router.post("/dishes", response_model=DishOut, status_code=201)
async def create_dish(
    payload: DishCreate,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> DishOut:
    d = await svc.create_dish(
        session,
        user.user_id,
        payload.TenMon,
        payload.MaNhomMon,
        payload.HinhAnh,
        payload.GiaHienTai,
    )
    await session.commit()
    # reload to get DB defaults
    await session.refresh(d)
    status = await svc.display_status_for(session, d)
    return DishOut(
        MaMon=d.id,
        TenMon=d.name,
        MaNhomMon=d.group_id,
        HinhAnh=payload.HinhAnh,
        GiaHienTai=payload.GiaHienTai,
        TrangThai=status,
        AnThuCong=d.hide_manual,
        DaXoa=d.is_deleted,
    )


@router.patch("/dishes/{dish_id}", response_model=DishOut)
async def update_dish(
    dish_id: int,
    payload: DishUpdate,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> DishOut:
    d = await svc.update_dish(session, user.user_id, dish_id, payload.TenMon, payload.MaNhomMon)
    await session.commit()
    await session.refresh(d)
    status = await svc.display_status_for(session, d)
    return DishOut(
        MaMon=d.id,
        TenMon=d.name,
        MaNhomMon=d.group_id,
        HinhAnh=payload.HinhAnh,
        GiaHienTai=None,
        TrangThai=status,
        AnThuCong=d.hide_manual,
        DaXoa=d.is_deleted,
    )


@router.delete("/dishes/{dish_id}", status_code=204)
async def delete_dish(
    dish_id: int,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> None:
    await svc.delete_dish(session, user.user_id, dish_id)
    await session.commit()
