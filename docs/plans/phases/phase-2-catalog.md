# Phase 2 — Module 1: Quản lý danh mục

> **Cho người thực thi:** dùng skill `executing-plans` để chạy kế hoạch này theo từng task.

**Mục tiêu:** Toàn bộ FR-CAT-01…28: nhóm món, món ăn, phiên bản giá và công thức theo Business Date,
nguyên liệu, nhà cung cấp, sơ đồ bàn — kèm xóa mềm thống nhất và audit log.

**Kiến trúc:** Module `catalog` sở hữu tám bảng `NHOM_MON`, `MON_AN`, `LICH_SU_GIA_MON`, `CONG_THUC`,
`CHI_TIET_CONG_THUC`, `NGUYEN_LIEU`, `NHA_CUNG_CAP`, `BAN`. Điểm khó nhất là **cơ chế hiệu lực theo
thời gian**: giá và công thức không ghi đè mà sinh phiên bản, mỗi phiên bản neo vào một Business Date.
Module Bán hàng (Phase 4) gọi lại hai hàm tra cứu của phase này, nên chữ ký hàm phải chốt sớm.

**Spec:** báo cáo §2.4.1 (FR-CAT-01…28), §3.2.1 a5–a12 (thuộc tính), §3.2.2 (BR-CTO-01, xóa mềm,
khóa đơn vị tính), §3.4.2 (Bảng 33 — quyền theo chức năng).

**Phụ thuộc:** Phase 0 (bảng), Phase 1 (xác thực + audit). **Lộ trình:** `docs/plans/2026-09-24-master-roadmap.md`

**Nhánh:** `feat/phase-2-catalog`

## Ràng buộc chung

- **Xóa mềm là mặc định** cho nhóm món, món ăn, nguyên liệu, nhà cung cấp, bàn khi đối tượng đã bị
  dữ liệu vận hành tham chiếu; chỉ xóa cứng khi chưa từng được tham chiếu (nguyên tắc đầu §2.4.1).
- **Món ăn không bao giờ xóa cứng** (FR-CAT-04) — kể cả khi chưa có order.
- Mọi xóa và mọi thay đổi giá/công thức đều ghi audit log (FR-SET-08).
- `BusinessDateApDung` phải là **tương lai**; mặc định là Business Date kế tiếp (FR-CAT-08, FR-CAT-20).
- Tối đa **một** thay đổi giá và **một** thay đổi công thức ở trạng thái `Chờ áp dụng` cho mỗi món.
- Tra cứu giá/công thức hiệu lực **chỉ** qua `app.shared.business_date`, không tự tính lại.
- Thêm nhóm/món/nguyên liệu mới **không** phải sửa lược đồ (NFR-11): danh mục là dữ liệu, không phải
  cấu trúc. `apps/web/src/lib/modules.ts` vẫn là nguồn duy nhất mô tả module cho giao diện.
- Mọi chuỗi hiển thị cho người dùng bằng **tiếng Việt** (NFR-14); code, comment, tên hàm bằng tiếng Anh.
- `make gate` xanh trước khi kết thúc mỗi task.

## Cấu trúc file

| File | Trách nhiệm |
| --- | --- |
| `apps/api/src/app/modules/catalog/schemas.py` | Hợp đồng request/response. |
| `apps/api/src/app/modules/catalog/service.py` | Logic nghiệp vụ, gồm cả xóa mềm và phiên bản hóa. |
| `apps/api/src/app/modules/catalog/versions.py` | Tra cứu phiên bản hiệu lực — dùng chung với Phase 4. |
| `apps/api/src/app/modules/catalog/router.py` | Tầng HTTP, gắn `require_any_role`. |
| `apps/web/src/features/catalog/` | Màn hình nhóm món, món ăn, công thức, giá, nguyên liệu, NCC, bàn. |
| `apps/api/tests/modules/test_catalog_*.py` | Test theo từng nhóm chức năng. |

---

## Task 1: Nhóm món và món ăn (FR-CAT-01…06, 26, 27, 28)

**Files:**
- Create: `apps/api/src/app/modules/catalog/schemas.py`
- Create: `apps/api/src/app/modules/catalog/service.py`
- Modify: `apps/api/src/app/modules/catalog/router.py`
- Test: `apps/api/tests/modules/test_catalog_dishes.py`

**Interfaces:**
- Consumes: `DishGroup`, `Dish`, `audit.record`, `require_any_role`.
- Produces: `create_group`, `update_group`, `delete_group`, `create_dish`, `update_dish`,
  `delete_dish`, `list_dishes`; `GET/POST/PATCH/DELETE /catalog/groups`, `/catalog/dishes`.

- [ ] **Step 1: Viết test cho xóa mềm và điều kiện xóa nhóm**

```python
async def test_a_group_with_live_dishes_cannot_be_deleted(client, manager_token, group_with_dish):
    """FR-CAT-03."""
    response = await delete_group(client, manager_token, group_with_dish.id)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


async def test_a_group_can_be_deleted_once_every_dish_is_soft_deleted(
    client, manager_token, group_with_dish
):
    await delete_dish(client, manager_token, group_with_dish.dish_id)

    assert (await delete_group(client, manager_token, group_with_dish.id)).status_code == 204


async def test_a_dish_is_never_hard_deleted(client, manager_token, dish, db_session):
    """FR-CAT-04: the row survives so old orders keep resolving."""
    await delete_dish(client, manager_token, dish.id)

    row = await get_dish(db_session, dish.id)
    assert row is not None
    assert row.is_deleted is True


async def test_soft_deleting_a_dish_cancels_its_pending_changes(
    client, manager_token, dish_with_pending_price, db_session
):
    """FR-CAT-05."""
    await delete_dish(client, manager_token, dish_with_pending_price.id)

    pending = await pending_price_versions(db_session, dish_with_pending_price.id)
    assert pending == []


async def test_dish_deletion_is_audited(client, manager_token, dish, db_session):
    await delete_dish(client, manager_token, dish.id)

    assert (await latest_audit(db_session)).action == "DELETE_DISH"


async def test_a_new_dish_starts_as_draft(client, manager_token, group, db_session):
    """FR-CAT-06: no recipe yet, so it is not on the order screen."""
    created = await create_dish(client, manager_token, name="Phở bò", group_id=group.id)

    dish = await get_dish(db_session, created.json()["MaMon"])
    assert dish.status == "Nháp"
    assert dish.manual_hidden is False


async def test_a_dish_carries_a_name_a_price_a_group_and_a_picture(client, manager_token, group):
    """FR-CAT-02: the four attributes the manager enters."""
    body = (await create_dish(client, manager_token, name="Phở bò", group_id=group.id)).json()

    assert {"TenMon", "MaNhomMon", "HinhAnh", "GiaHienTai"} <= set(body)


async def test_dishes_can_be_searched_by_name(client, manager_token, three_dishes):
    """FR-CAT-02."""
    found = (await list_dishes(client, manager_token, search="phở")).json()["items"]

    assert [item["TenMon"] for item in found] == ["Phở bò"]


async def test_a_dish_belongs_to_exactly_one_group(client, manager_token, group, other_group):
    """FR-CAT-02 and business rule 3."""
    created = await create_dish(client, manager_token, name="Phở bò", group_id=group.id)

    moved = await update_dish(client, manager_token, created.json()["MaMon"], group_id=other_group.id)

    assert moved.json()["MaNhomMon"] == other_group.id
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_catalog_dishes.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

`delete_group` đếm món chưa xóa mềm thuộc nhóm; còn món thì trả `BusinessRuleError`. `delete_dish`
đặt `DaXoa = True`, `NgayXoa`, và **hủy mọi phiên bản giá/công thức `Chờ áp dụng`** của món đó
(FR-CAT-05). `TrangThai` của món mới là `Nháp` — đây là giá trị do **service** gán, không phải cột
GENERATED (xem Quyết định #1 ở phase-0).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_catalog_dishes.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(catalog): manage dish groups and dishes with soft delete`

---

## Task 2: Phiên bản giá theo Business Date (FR-CAT-20, 21, 22, 23, 24, 25)

**Files:**
- Create: `apps/api/src/app/modules/catalog/versions.py`
- Modify: `apps/api/src/app/modules/catalog/service.py`
- Modify: `apps/api/src/app/modules/catalog/router.py`
- Test: `apps/api/tests/modules/test_catalog_prices.py`

**Interfaces:**
- Consumes: `DishPriceVersion`, `business_date.next_business_date`.
- Produces: `schedule_price_change`, `cancel_pending_price_change`, `apply_price_directly`,
  `active_price_version(session, dish_id, business_date) -> DishPriceVersion | None`,
  `active_price(session, dish_id, business_date) -> Decimal | None`.

- [ ] **Step 1: Viết test**

```python
async def test_a_scheduled_change_must_target_a_future_business_date(
    client, manager_token, dish
):
    """FR-CAT-20."""
    past = await schedule_price(client, manager_token, dish.id, price="50000", on=today())
    future = await schedule_price(client, manager_token, dish.id, price="50000", on=tomorrow())

    assert past.status_code == 422
    assert future.status_code == 201


async def test_the_default_target_is_the_next_business_date(client, manager_token, dish):
    created = await schedule_price(client, manager_token, dish.id, price="50000")

    assert created.json()["BusinessDateApDung"] == next_business_date().isoformat()


async def test_only_one_change_waits_per_dish_and_the_newest_wins(
    client, manager_token, dish, db_session
):
    """FR-CAT-21: a new scheduled change overwrites the waiting one."""
    await schedule_price(client, manager_token, dish.id, price="50000", on=tomorrow())
    await schedule_price(client, manager_token, dish.id, price="60000", on=tomorrow())

    pending = await pending_price_versions(db_session, dish.id)
    assert len(pending) == 1
    assert pending[0].price == Decimal("60000")
    assert pending[0].status == "Đã hủy" or pending[0].price == Decimal("60000")


async def test_a_direct_edit_applies_now_and_keeps_the_scheduled_change(
    client, manager_token, dish, db_session
):
    """FR-CAT-23 and FR-CAT-24: the two mechanisms are independent."""
    await schedule_price(client, manager_token, dish.id, price="60000", on=tomorrow())

    await edit_price_now(client, manager_token, dish.id, price="45000")

    assert await active_price(db_session, dish.id, today()) == Decimal("45000")
    assert len(await pending_price_versions(db_session, dish.id)) == 1


async def test_cancelling_a_pending_change_is_audited(client, manager_token, dish, db_session):
    """FR-CAT-22."""
    created = await schedule_price(client, manager_token, dish.id, price="50000", on=tomorrow())

    await cancel_price_change(client, manager_token, created.json()["MaPhienBanGia"])

    assert (await latest_audit(db_session)).action == "CANCEL_PRICE_CHANGE"


async def test_the_active_version_is_the_one_in_force_on_that_business_date(
    client, manager_token, dish, db_session
):
    """A scheduled version does not affect orders placed before it takes effect."""
    await edit_price_now(client, manager_token, dish.id, price="45000")
    await schedule_price(client, manager_token, dish.id, price="60000", on=tomorrow())

    assert await active_price(db_session, dish.id, today()) == Decimal("45000")
    assert await active_price(db_session, dish.id, tomorrow()) == Decimal("60000")
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_catalog_prices.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.catalog.versions`

- [ ] **Step 3: Cài đặt**

`active_price_version()` chọn phiên bản có `ThoiDiemHieuLuc <= business_date_start(bd)` và
(`ThoiDiemHetHieuLuc IS NULL` hoặc `> business_date_start(bd)`), ưu tiên bản mới nhất. Hàm này là
**hợp đồng công khai** — Phase 4 gọi lại, nên chữ ký phải giữ nguyên từ đây.
`edit_price_now` đóng phiên bản đang hiệu lực (`ThoiDiemHetHieuLuc = now`) rồi tạo bản mới với
`LoaiThayDoi = 'Sửa trực tiếp'` (FR-CAT-25).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_catalog_prices.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(catalog): version dish prices by business date`

---

## Task 3: Công thức và định lượng (FR-CAT-07, 08, 09, 10, 11)

**Files:**
- Modify: `apps/api/src/app/modules/catalog/versions.py`
- Modify: `apps/api/src/app/modules/catalog/service.py`
- Modify: `apps/api/src/app/modules/catalog/router.py`
- Test: `apps/api/tests/modules/test_catalog_recipes.py`

**Interfaces:**
- Consumes: `Recipe`, `RecipeItem`, `Ingredient`, Task 2.
- Produces: `schedule_recipe_change`, `cancel_pending_recipe_change`, `apply_recipe_directly`,
  `active_recipe(session, dish_id, business_date) -> Recipe | None`,
  `recipe_items(session, recipe_id) -> list[RecipeItem]`.

- [ ] **Step 1: Viết test**

```python
async def test_the_first_recipe_activates_the_dish(client, manager_token, draft_dish, db_session):
    """FR-CAT-11."""
    await assign_recipe(client, manager_token, draft_dish.id, items=[(flour.id, "0.2")])

    dish = await get_dish(db_session, draft_dish.id)
    assert dish.status in {"Hoạt động", "Hết nguyên liệu"}


async def test_a_recipe_line_carries_no_unit_of_its_own(client, manager_token, draft_dish, db_session):
    """§3.2.2: the unit always comes from NGUYEN_LIEU.DonViTinh."""
    await assign_recipe(client, manager_token, draft_dish.id, items=[(flour.id, "0.2")])

    recipe = await active_recipe(db_session, draft_dish.id, today())
    item = (await recipe_items(db_session, recipe.id))[0]
    assert item.ingredient_id == flour.id
    assert not hasattr(item, "unit")


async def test_only_one_pending_recipe_change_per_dish(client, manager_token, dish_with_recipe, db_session):
    """FR-CAT-09 applies to recipes as well as prices."""
    await schedule_recipe(client, manager_token, dish_with_recipe.id, items=[(flour.id, "0.3")])
    await schedule_recipe(client, manager_token, dish_with_recipe.id, items=[(flour.id, "0.4")])

    assert len(await pending_recipe_versions(db_session, dish_with_recipe.id)) == 1


async def test_cancelling_a_pending_recipe_change_is_audited(
    client, manager_token, dish_with_recipe, db_session
):
    """FR-CAT-10."""
    created = await schedule_recipe(client, manager_token, dish_with_recipe.id, items=[(flour.id, "0.3")])

    await cancel_recipe_change(client, manager_token, created.json()["MaCongThuc"])

    assert (await latest_audit(db_session)).action == "CANCEL_RECIPE_CHANGE"


async def test_a_zero_or_negative_quantity_is_rejected(client, manager_token, dish_with_recipe):
    response = await schedule_recipe(
        client, manager_token, dish_with_recipe.id, items=[(flour.id, "0")]
    )

    assert response.status_code == 422
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_catalog_recipes.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

`assign_recipe` (lần đầu) tạo phiên bản `CONG_THUC` hiệu lực ngay và chuyển món khỏi `Nháp` sang
`Hoạt động` hoặc `Hết nguyên liệu` tùy tồn kho hiện có. `active_recipe()` cùng hình dạng với
`active_price_version()` để Phase 4 và Phase 3 dùng lại.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_catalog_recipes.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(catalog): version recipes and activate dishes on first assignment`

---

## Task 4: Nguyên liệu và nhà cung cấp (FR-CAT-12, 13, 14, 15, 16)

**Files:**
- Modify: `apps/api/src/app/modules/catalog/service.py`
- Modify: `apps/api/src/app/modules/catalog/router.py`
- Test: `apps/api/tests/modules/test_catalog_ingredients.py`

**Interfaces:**
- Consumes: `Ingredient`, `Supplier`, `SystemConfig`.
- Produces: `create_ingredient`, `update_ingredient`, `delete_ingredient`,
  `effective_min_stock(session, ingredient) -> Decimal`; `/catalog/ingredients`, `/catalog/suppliers`.

- [ ] **Step 1: Viết test**

```python
async def test_an_ingredient_without_its_own_threshold_uses_the_default(
    client, manager_token, config_with_default_threshold
):
    """FR-INV-07."""
    created = await create_ingredient(client, manager_token, name="Bột mì", min_stock=None)

    assert created.json()["MucTonToiThieu"] == config_with_default_threshold.default_min_stock


async def test_the_unit_is_locked_once_the_ingredient_is_referenced(
    client, manager_token, ingredient_in_recipe
):
    """FR-CAT-14."""
    response = await update_ingredient(client, manager_token, ingredient_in_recipe.id, unit="kg")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


async def test_the_unit_can_still_be_changed_before_any_reference(
    client, manager_token, fresh_ingredient
):
    assert (await update_ingredient(client, manager_token, fresh_ingredient.id, unit="kg")).status_code == 200


async def test_deleting_a_referenced_ingredient_is_soft_only(
    client, manager_token, ingredient_in_recipe, db_session
):
    """FR-CAT-13."""
    await delete_ingredient(client, manager_token, ingredient_in_recipe.id)

    row = await get_ingredient(db_session, ingredient_in_recipe.id)
    assert row is not None and row.is_deleted is True


async def test_ingredient_deletion_is_audited(client, manager_token, fresh_ingredient, db_session):
    await delete_ingredient(client, manager_token, fresh_ingredient.id)

    assert (await latest_audit(db_session)).action == "DELETE_INGREDIENT"


async def test_warehouse_staff_may_manage_ingredients_but_not_dishes(
    client, warehouse_token, manager_token
):
    """Table 33: ingredients belong to the manager *and* the warehouse role."""
    assert (await create_ingredient(client, warehouse_token, name="Hành lá")).status_code == 201
    assert (await create_dish(client, warehouse_token, name="Món", group_id=1)).status_code == 403


async def test_ingredients_can_be_searched_by_name(client, warehouse_token, three_ingredients):
    """FR-CAT-12."""
    found = (await list_ingredients(client, warehouse_token, search="hành")).json()["items"]

    assert [item["TenNguyenLieu"] for item in found] == ["Hành lá"]


async def test_a_supplier_shows_its_receipt_history(client, warehouse_token, supplier_with_receipts):
    """FR-CAT-15."""
    detail = (await get_supplier(client, warehouse_token, supplier_with_receipts.id)).json()

    assert len(detail["PhieuNhap"]) == 2


async def test_a_supplier_with_receipts_is_only_soft_deleted(
    client, warehouse_token, supplier_with_receipts, db_session
):
    """FR-CAT-16."""
    await delete_supplier(client, warehouse_token, supplier_with_receipts.id)

    row = await get_supplier_row(db_session, supplier_with_receipts.id)
    assert row is not None and row.is_deleted is True
    assert (await latest_audit(db_session)).action == "DELETE_SUPPLIER"


async def test_a_supplier_with_no_history_is_deleted_outright(
    client, warehouse_token, fresh_supplier, db_session
):
    """The opening rule of section 2.4.1: never referenced, so it can go for good."""
    await delete_supplier(client, warehouse_token, fresh_supplier.id)

    assert await get_supplier_row(db_session, fresh_supplier.id) is None
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_catalog_ingredients.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

`DaKhoaDonVi` bật thành `True` ngay khi nguyên liệu xuất hiện trong `CHI_TIET_CONG_THUC` hoặc
`CHI_TIET_PHIEU_NHAP`; từ đó `update_ingredient` từ chối đổi `DonViTinh` (FR-CAT-14).
`effective_min_stock()` là hợp đồng cho Phase 3 dùng lại khi tính cảnh báo tồn.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_catalog_ingredients.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(catalog): manage ingredients and suppliers with the unit lock`

---

## Task 5: Sơ đồ bàn và ẩn/hiện món (FR-CAT-17…19, 26, 27)

**Files:**
- Modify: `apps/api/src/app/modules/catalog/service.py`
- Modify: `apps/api/src/app/modules/catalog/router.py`
- Test: `apps/api/tests/modules/test_catalog_tables.py`

**Interfaces:**
- Consumes: `DiningTable`, `Dish`.
- Produces: `create_table`, `update_table`, `delete_table`, `set_table_occupied`,
  `release_table`, `set_manual_hidden`, `set_manual_out_of_stock`;
  `/catalog/tables`, `/catalog/dishes/{id}/visibility`.

- [ ] **Step 1: Viết test**

```python
async def test_a_table_in_use_cannot_be_deleted(client, manager_token, occupied_table):
    """FR-CAT-19."""
    response = await delete_table(client, manager_token, occupied_table.id)

    assert response.status_code == 422


async def test_a_soft_deleted_table_frees_its_name(client, manager_token, db_session):
    """TenBan_Active is NULL once the table is soft-deleted, so the name can be reused."""
    await delete_table(client, manager_token, (await free_table(db_session)).id)

    assert (await create_table(client, manager_token, name="Bàn 1")).status_code == 201


async def test_the_two_out_of_stock_causes_are_independent(client, manager_token, dish, db_session):
    """FR-CAT-27: the dish is orderable only when both flags are off."""
    await set_manual_out_of_stock(client, manager_token, dish.id, value=True)
    assert (await get_dish(db_session, dish.id)).status == "Hết nguyên liệu"

    await set_manual_out_of_stock(client, manager_token, dish.id, value=False)
    await set_automatic_out_of_stock(db_session, dish.id, value=False)
    assert (await get_dish(db_session, dish.id)).status == "Hoạt động"


async def test_manual_hiding_is_independent_of_stock(client, manager_token, dish, db_session):
    """FR-CAT-26."""
    await set_manual_hidden(client, manager_token, dish.id, value=True)

    assert (await get_dish(db_session, dish.id)).manual_hidden is True


async def test_soft_deleted_table_is_hidden_from_the_floor_plan(client, manager_token, free_table):
    await delete_table(client, manager_token, free_table.id)

    listed = (await list_tables(client, manager_token)).json()["items"]
    assert all(item["MaBan"] != free_table.id for item in listed)


async def test_the_cashier_sees_the_floor_plan_but_cannot_edit_it(client, cashier_token):
    """FR-CAT-17."""
    assert (await list_tables(client, cashier_token)).status_code == 200
    assert (await create_table(client, cashier_token, name="Bàn 9")).status_code == 403


async def test_soft_delete_is_a_state_of_its_own(client, manager_token, dish, db_session):
    """FR-CAT-28: deletion is independent of the operating state."""
    await delete_dish(client, manager_token, dish.id)

    row = await get_dish(db_session, dish.id)
    assert row.is_deleted is True
    assert row.status in {"Hoạt động", "Hết nguyên liệu", "Nháp"}
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_catalog_tables.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

`set_table_occupied`/`release_table` là API nội bộ mà Phase 4 gọi khi order mở/đóng (FR-CAT-18).
Chúng **không** expose qua HTTP cho người dùng tự đổi trạng thái bàn.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_catalog_tables.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(catalog): manage tables and dish visibility`

---

## Task 6: Giao diện danh mục

**Files:**
- Create: `apps/web/src/features/catalog/dish-list.tsx`
- Create: `apps/web/src/features/catalog/price-scheduler.tsx`
- Create: `apps/web/src/features/catalog/recipe-editor.tsx`
- Create: `apps/web/src/features/catalog/dish-list.test.tsx`
- Modify: `apps/web/src/app/(app)/catalog/page.tsx`

**Interfaces:**
- Consumes: các endpoint ở Task 1–5, `apiFetch`.
- Produces: `DishList`, `PriceScheduler`, `RecipeEditor`.

- [ ] **Step 1: Viết test**

```tsx
it("shows the four display states of the screen", async () => {
  render(<DishList />);

  expect(screen.getByText("Đang tải…")).toBeInTheDocument();
  expect(await screen.findByText("Phở bò")).toBeInTheDocument();
});

it("shows an empty state with a next step when there are no dishes", async () => {
  stubFetch({ items: [], total: 0 });

  render(<DishList />);

  expect(await screen.findByText(/Chưa có món nào/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Thêm món" })).toBeInTheDocument();
});

it("rejects a scheduled date in the past before calling the API", async () => {
  render(<PriceScheduler dishId={1} />);
  fireEvent.change(screen.getByLabelText("Business Date áp dụng"), {
    target: { value: "2020-01-01" },
  });

  expect(screen.getByText(/phải là một Business Date trong tương lai/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Lưu" })).toBeDisabled();
});
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/web && pnpm test`
Expected: FAIL — module chưa tồn tại

- [ ] **Step 3: Cài đặt**

Bốn trạng thái hiển thị (success / error / loading / empty) theo §3.3. Màn hình lên lịch chỉ cho lưu
khi Business Date hợp lệ trong tương lai (FR-CAT-08, FR-CAT-20) — chặn ở giao diện **và** API vẫn
kiểm tra lại.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/web && pnpm test`
Expected: PASS

- [ ] **Step 5: Chạy cổng kiểm tra đầy đủ**

Run: `UV_CACHE_DIR=/tmp/uv-cache make gate`
Expected: xanh. Commit: `feat(web): build the catalogue screens`

---

## Kiểm chứng

| Cổng | Lệnh | Kỳ vọng |
| --- | --- | --- |
| Nhóm món + món ăn | `pytest tests/modules/test_catalog_dishes.py` | xanh |
| Phiên bản giá | `pytest tests/modules/test_catalog_prices.py` | xanh |
| Công thức | `pytest tests/modules/test_catalog_recipes.py` | xanh |
| Nguyên liệu + NCC | `pytest tests/modules/test_catalog_ingredients.py` | xanh |
| Bàn + ẩn/hiện | `pytest tests/modules/test_catalog_tables.py` | xanh |
| Giao diện | `cd apps/web && pnpm test` | xanh |
| Toàn bộ | `make gate` | xanh |

## Rủi ro

- **Cơ chế hiệu lực hai trục** (lên lịch vs sửa trực tiếp) là chỗ dễ sai nhất. Test
  `test_a_direct_edit_applies_now_and_keeps_the_scheduled_change` là chốt chặn cho FR-CAT-24.
- **`active_price`/`active_recipe` là hợp đồng liên module**: Phase 3 và Phase 4 gọi lại. Đổi chữ ký
  sau này sẽ vỡ cả hai phase — chốt sớm ở Task 2 và Task 3.
- **Múi giờ**: `ThoiDiemHieuLuc` lưu `DATETIME` giờ hệ thống, `BusinessDateApDung` là `DATE`. Luôn
  quy đổi qua `business_date_start()` trước khi so sánh, đừng so `DATE` với `DATETIME` trực tiếp.
- **FR-CAT-11 khi tồn kho bằng 0**: món chuyển thẳng sang `Hết nguyên liệu`. Phase 3 mới có API bật
  lại `HetNLTuDong`, nên trước Phase 3 test phải tự set cờ này qua fixture.
