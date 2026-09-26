"""HTTP layer for the catalogue module."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import Principal, get_current_user, require_roles
from app.core.errors import NotFoundError
from app.modules.catalog import service as svc
from app.modules.catalog import versions as catalog_versions
from app.modules.catalog.schemas import (
    DishCreate,
    DishOut,
    DishUpdate,
    GroupCreate,
    GroupOut,
    GroupReorderRequest,
    GroupUpdate,
    IngredientCreate,
    IngredientOut,
    IngredientUpdate,
    PriceApplyNowRequest,
    PriceScheduleRequest,
    PriceVersionOut,
    RecipeApplyNowRequest,
    RecipeAssignRequest,
    RecipeLineOut,
    RecipeOut,
    RecipeScheduleRequest,
    RecipeVersionOut,
    SupplierCreate,
    SupplierOut,
    SupplierUpdate,
    TableCreate,
    TableOut,
    VisibilityUpdate,
)
from app.modules.catalog.versions import active_price, active_prices
from app.shared import business_date
from app.shared.pagination import Page
from app.shared.roles import Role

router = APIRouter(prefix="/catalog", tags=["Module 1 — Catalogue"])


def _today():
    return business_date.business_date_of(business_date.now())


def _money(value) -> float | None:
    return float(value) if value is not None else None


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
    prices = await active_prices(session, [d.id for d in sliced], _today())
    out: list[DishOut] = []
    for d in sliced:
        status = await svc.display_status_for(session, d)
        out.append(
            DishOut(
                MaMon=d.id,
                TenMon=d.name,
                MaNhomMon=d.group_id,
                HinhAnh=d.image_url,
                GiaHienTai=_money(prices.get(d.id)),
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
        HinhAnh=d.image_url,
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
    d = await svc.update_dish(
        session,
        user.user_id,
        dish_id,
        payload.TenMon,
        payload.MaNhomMon,
        payload.HinhAnh,
        image_provided="HinhAnh" in payload.model_fields_set,
    )
    await session.commit()
    await session.refresh(d)
    status = await svc.display_status_for(session, d)
    return DishOut(
        MaMon=d.id,
        TenMon=d.name,
        MaNhomMon=d.group_id,
        HinhAnh=d.image_url,
        GiaHienTai=_money(await active_price(session, d.id, _today())),
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


# Prices
@router.get("/dishes/{dish_id}/prices", response_model=list[PriceVersionOut])
async def list_dish_prices(
    dish_id: int,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
    session: AsyncSession = Depends(get_session),
) -> list[PriceVersionOut]:
    d = await svc.get_dish(session, dish_id)
    if d is None or d.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    items = await catalog_versions.list_price_versions(session, dish_id)
    return [PriceVersionOut.model_validate(v) for v in items]


@router.post("/dishes/{dish_id}/prices/schedule", response_model=PriceVersionOut, status_code=201)
async def schedule_price(
    dish_id: int,
    payload: PriceScheduleRequest,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> PriceVersionOut:
    v = await svc.schedule_price_change(
        session, user.user_id, dish_id, payload.Gia, payload.BusinessDateApDung
    )
    await session.commit()
    return PriceVersionOut.model_validate(v)


@router.post("/dishes/{dish_id}/prices/apply-now", response_model=PriceVersionOut, status_code=201)
async def apply_price_now(
    dish_id: int,
    payload: PriceApplyNowRequest,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> PriceVersionOut:
    v = await svc.apply_price_directly(session, user.user_id, dish_id, payload.Gia)
    await session.commit()
    return PriceVersionOut.model_validate(v)


@router.delete("/prices/{version_id}", status_code=204)
async def cancel_price(
    version_id: int,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> None:
    await svc.cancel_pending_price_change(session, user.user_id, version_id)
    await session.commit()


# Recipes
@router.get("/dishes/{dish_id}/recipes", response_model=list[RecipeVersionOut])
async def list_dish_recipes(
    dish_id: int,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
    session: AsyncSession = Depends(get_session),
) -> list[RecipeVersionOut]:
    d = await svc.get_dish(session, dish_id)
    if d is None or d.is_deleted:
        raise NotFoundError("Không tìm thấy món ăn.")
    recipes = await catalog_versions.list_recipe_versions(session, dish_id)
    out: list[RecipeVersionOut] = []
    for r in recipes:
        lines = await catalog_versions.recipe_items_detailed(session, r.id)
        out.append(
            RecipeVersionOut(
                MaCongThuc=r.id,
                MaMon=r.dish_id,
                BusinessDateApDung=r.business_date,
                TrangThai=r.status,
                LoaiThayDoi=r.change_type,
                items=[RecipeLineOut(**line) for line in lines],
            )
        )
    return out


@router.post("/dishes/{dish_id}/recipes/schedule", response_model=RecipeOut, status_code=201)
async def schedule_recipe(
    dish_id: int,
    payload: RecipeScheduleRequest,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> RecipeOut:
    items = [(x.MaNguyenLieu, x.SoLuong) for x in payload.items]
    r = await svc.schedule_recipe_change(
        session, user.user_id, dish_id, items, payload.BusinessDateApDung
    )
    await session.commit()
    return RecipeOut.model_validate(r)


@router.post("/dishes/{dish_id}/recipes/assign", response_model=RecipeOut, status_code=201)
async def assign_recipe(
    dish_id: int,
    payload: RecipeAssignRequest,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> RecipeOut:
    items = [(x.MaNguyenLieu, x.SoLuong) for x in payload.items]
    r = await svc.assign_recipe(session, user.user_id, dish_id, items)
    await session.commit()
    return RecipeOut.model_validate(r)


@router.post("/dishes/{dish_id}/recipes/apply-now", response_model=RecipeOut, status_code=201)
async def apply_recipe_now(
    dish_id: int,
    payload: RecipeApplyNowRequest,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> RecipeOut:
    items = [(x.MaNguyenLieu, x.SoLuong) for x in payload.items]
    r = await svc.apply_recipe_directly(session, user.user_id, dish_id, items)
    await session.commit()
    return RecipeOut.model_validate(r)


@router.delete("/recipes/{recipe_id}", status_code=204)
async def cancel_recipe(
    recipe_id: int,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> None:
    await svc.cancel_pending_recipe_change(session, user.user_id, recipe_id)
    await session.commit()


# Ingredients
@router.get("/ingredients", response_model=Page[IngredientOut])
async def list_ingredients(
    search: str | None = Query(None),
    user: Principal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Page[IngredientOut]:
    items, total = await svc.list_ingredients(session, search)
    return Page[IngredientOut](
        items=[IngredientOut.model_validate(x) for x in items], total=total, page=1, size=200
    )


@router.post("/ingredients", response_model=IngredientOut, status_code=201)
async def create_ingredient(
    payload: IngredientCreate,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
) -> IngredientOut:
    ing = await svc.create_ingredient(
        session,
        user.user_id,
        payload.TenNguyenLieu,
        payload.DonViTinh or "kg",
        payload.MucTonToiThieu,
    )
    await session.commit()
    return IngredientOut.model_validate(ing)


@router.patch("/ingredients/{ingredient_id}", response_model=IngredientOut)
async def update_ingredient(
    ingredient_id: int,
    payload: IngredientUpdate,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
) -> IngredientOut:
    ing = await svc.update_ingredient(
        session,
        user.user_id,
        ingredient_id,
        payload.TenNguyenLieu,
        payload.DonViTinh,
        payload.MucTonToiThieu,
    )
    await session.commit()
    return IngredientOut.model_validate(ing)


@router.delete("/ingredients/{ingredient_id}", status_code=204)
async def delete_ingredient(
    ingredient_id: int,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
) -> None:
    await svc.delete_ingredient(session, user.user_id, ingredient_id)
    await session.commit()


# Suppliers
@router.get("/suppliers", response_model=list[SupplierOut])
async def list_suppliers(
    user: Principal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[SupplierOut]:
    items = await svc.list_suppliers(session)
    return [SupplierOut.model_validate(x) for x in items]


@router.post("/suppliers", response_model=SupplierOut, status_code=201)
async def create_supplier(
    payload: SupplierCreate,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
) -> SupplierOut:
    s = await svc.create_supplier(session, user.user_id, payload.TenNhaCungCap, payload.SoDienThoai)
    await session.commit()
    return SupplierOut.model_validate(s)


@router.get("/suppliers/{supplier_id}", response_model=SupplierOut)
async def get_supplier(
    supplier_id: int,
    user: Principal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SupplierOut:
    s = await svc.get_supplier(session, supplier_id)
    if s is None or s.is_deleted:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Không tìm thấy nhà cung cấp.")
    # load receipts
    from sqlalchemy import select as _sel

    from app.modules.inventory.models import GoodsReceipt

    r = await session.execute(_sel(GoodsReceipt).where(GoodsReceipt.supplier_id == supplier_id))
    receipts = [{"MaPhieuNhap": gr.id} for gr in r.scalars().all()]
    out = SupplierOut.model_validate(s)
    out.PhieuNhap = receipts
    return out


@router.patch("/suppliers/{supplier_id}", response_model=SupplierOut)
async def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
) -> SupplierOut:
    s = await svc.update_supplier(
        session, user.user_id, supplier_id, payload.TenNhaCungCap, payload.SoDienThoai
    )
    await session.commit()
    return SupplierOut.model_validate(s)


@router.delete("/suppliers/{supplier_id}", status_code=204)
async def delete_supplier(
    supplier_id: int,
    user: Principal = Depends(require_roles(Role.MANAGER, Role.WAREHOUSE)),
    session: AsyncSession = Depends(get_session),
) -> None:
    await svc.delete_supplier(session, user.user_id, supplier_id)
    await session.commit()


# Tables
@router.get("/tables", response_model=list[TableOut])
async def list_tables(
    user: Principal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[TableOut]:
    items = await svc.list_tables(session)
    return [TableOut.model_validate(x) for x in items]


@router.post("/tables", response_model=TableOut, status_code=201)
async def create_table(
    payload: TableCreate,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> TableOut:
    t2 = await svc.create_table(session, user.user_id, payload.TenBan)
    await session.commit()
    return TableOut.model_validate(t2)


@router.delete("/tables/{table_id}", status_code=204)
async def delete_table(
    table_id: int,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> None:
    await svc.delete_table(session, user.user_id, table_id)
    await session.commit()


# Visibility
@router.patch("/dishes/{dish_id}/visibility", response_model=DishOut)
async def update_visibility(
    dish_id: int,
    payload: VisibilityUpdate,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> DishOut:
    if payload.AnThuCong is not None:
        await svc.set_manual_hidden(session, user.user_id, dish_id, payload.AnThuCong)
    if payload.HetNLThuCong is not None:
        await svc.set_manual_out_of_stock(session, user.user_id, dish_id, payload.HetNLThuCong)
    await session.commit()
    d = await svc.get_dish(session, dish_id)
    assert d is not None
    status = await svc.display_status_for(session, d)
    return DishOut(
        MaMon=d.id,
        TenMon=d.name,
        MaNhomMon=d.group_id,
        HinhAnh=d.image_url,
        GiaHienTai=_money(await active_price(session, d.id, _today())),
        TrangThai=status,
        AnThuCong=d.hide_manual,
        DaXoa=d.is_deleted,
    )
