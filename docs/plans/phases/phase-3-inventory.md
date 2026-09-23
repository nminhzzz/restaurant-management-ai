# Phase 3 — Module 3: Quản lý kho

> **Cho người thực thi:** dùng skill `executing-plans` để chạy kế hoạch này theo từng task.

**Mục tiêu:** Toàn bộ FR-INV-01…12: nhập kho theo lô, trừ kho FIFO có khóa dòng, hoàn kho, xuất thủ
công, kiểm kê định kỳ, cảnh báo tồn tối thiểu, và giá bình quân gia quyền theo tháng.

**Kiến trúc:** Module `inventory` sở hữu chín bảng. Điểm khó nhất là **ba tầng lưu trữ tồn kho**
(§3.2.2): `GIAO_DICH_KHO` là sổ cái nguồn sự thật → `LO_NGUYEN_LIEU.SoLuongConLai` là cache theo lô →
`NGUYEN_LIEU.SoLuongTon` là cache tổng. Mọi thay đổi tồn kho phải là **một transaction** bao trọn cả
ba bước, và phải khóa dòng `NGUYEN_LIEU` bằng `SELECT ... FOR UPDATE` để xử lý tranh chấp (NFR-08).

**Spec:** báo cáo §2.4.3 (FR-INV-01…12), §3.2.1 a19–a27, §3.2.2 (BR-LOT-01, BR-LOT-02, ba tầng tồn
kho, CHECK cho bốn FK rời rạc), §3.2.3 (index `LO_NGUYEN_LIEU`).

**Phụ thuộc:** Phase 0, Phase 1, Phase 2 (`Ingredient`, `effective_min_stock`).
**Lộ trình:** `docs/plans/2026-09-24-master-roadmap.md` · **Nhánh:** `feat/phase-3-inventory`

## Ràng buộc chung

- **Không bao giờ để tồn kho âm** (FR-INV-06, FR-INV-11). Vi phạm trả `BusinessRuleError`.
- Mọi thay đổi tồn kho đi qua **một** hàm `apply_stock_movement()` — không nơi nào tự sửa `SoLuongTon`.
- Transaction thay đổi tồn kho gồm đúng ba bước: ghi `GIAO_DICH_KHO`, cập nhật
  `LO_NGUYEN_LIEU.SoLuongConLai`, cập nhật `NGUYEN_LIEU.SoLuongTon`. Một bước lỗi thì rollback cả ba.
- Khóa dòng bằng `SELECT ... FOR UPDATE` trên `NGUYEN_LIEU` **trước** khi chọn lô FIFO.
- FIFO **loại trừ lô `Hết hạn`** khỏi thứ tự trừ tự động (BR-LOT-01).
- Hoàn kho trả về **đúng lô đã bị trừ** ghi trên `GIAO_DICH_KHO` gốc, kể cả lô đó nay đã `Hết hạn`.
- Mọi thao tác rủi ro (xuất thủ công, điều chỉnh kiểm kê, sửa/hủy phiếu nhập) ghi audit log (FR-SET-08).
- `make gate` xanh trước khi kết thúc mỗi task.

## Hợp đồng với các phase khác

Phase này **cung cấp** cho Phase 4 và Phase 5:

| Hàm | Chữ ký | Ai dùng |
| --- | --- | --- |
| `apply_stock_movement` | `(session, change, *, actor_id) -> list[StockMovement]` | Phase 4 (trừ/hoàn kho khi bán) |
| `reverse_movement` | `(session, movement, *, actor_id) -> StockMovement` | Phase 4 (hủy/giảm món) |
| `effective_min_stock` | `(session, ingredient) -> Decimal` | Phase 5 (cảnh báo tồn) |

Phase này **tiêu thụ** từ Phase 2: `effective_min_stock`, `active_recipe`, `recipe_items`.
Chữ ký ba hàm trên phải giữ nguyên sau khi chốt — Phase 4 và Phase 5 gọi trực tiếp.

## Cấu trúc file

| File | Trách nhiệm |
| --- | --- |
| `apps/api/src/app/modules/inventory/schemas.py` | Hợp đồng request/response. |
| `apps/api/src/app/modules/inventory/stock.py` | **Lõi**: khóa dòng, chọn lô FIFO, ghi sổ cái, đồng bộ ba tầng. |
| `apps/api/src/app/modules/inventory/service.py` | Nghiệp vụ phiếu nhập/xuất/kiểm kê. |
| `apps/api/src/app/modules/inventory/costing.py` | Giá bình quân gia quyền theo tháng + job backfill. |
| `apps/api/src/app/modules/inventory/router.py` | Tầng HTTP. |
| `apps/web/src/features/inventory/` | Màn hình nhập, xuất, kiểm kê, tồn kho. |
| `apps/api/tests/modules/test_inventory_*.py` | Test theo từng nhóm. |

---

## Task 1: Lõi biến động kho (FR-INV-03, 04, 11 — BR-LOT-01)

**Files:**
- Create: `apps/api/src/app/modules/inventory/stock.py`
- Test: `apps/api/tests/modules/test_inventory_stock.py`

**Interfaces:**
- Consumes: `Ingredient`, `IngredientLot`, `StockMovement`, `business_date_of`;
  `catalog.service.effective_min_stock` và `catalog.versions.active_recipe`/`recipe_items` (Phase 2)
  cho móc nối tự ẩn món ở Task 6.
- Produces: `StockChange` (dataclass: ingredient_id, delta, kind, business_date, source);
  `lock_ingredient(session, ingredient_id) -> Ingredient`;
  `lots_for_fifo(session, ingredient_id) -> list[IngredientLot]`;
  `apply_stock_movement(session, change, *, actor_id) -> list[StockMovement]`;
  `reverse_movement(session, movement, *, actor_id) -> StockMovement`.

- [ ] **Step 1: Viết test cho FIFO, khóa dòng và hoàn kho**

```python
async def test_fifo_takes_the_oldest_lot_first(session, ingredient, two_lots):
    """BR-LOT-01."""
    older, newer = two_lots

    await apply_stock_movement(session, draw(ingredient, "3"), actor_id=1)

    assert (await reload(session, older)).remaining == Decimal("2")
    assert (await reload(session, newer)).remaining == Decimal("5")


async def test_a_draw_spanning_two_lots_writes_one_movement_per_lot(session, ingredient, two_lots):
    """§3.2.2: one CHI_TIET_ORDER can produce several GIAO_DICH_KHO rows."""
    movements = await apply_stock_movement(session, draw(ingredient, "7"), actor_id=1)

    assert len(movements) == 2
    assert {m.lot_id for m in movements} == {lot.id for lot in two_lots}


async def test_an_expired_lot_is_skipped_by_automatic_draw(session, ingredient, expired_and_fresh):
    """BR-LOT-01: only manual write-off may touch an expired lot."""
    expired, fresh = expired_and_fresh

    await apply_stock_movement(session, draw(ingredient, "1"), actor_id=1)

    assert (await reload(session, expired)).remaining == Decimal("5")
    assert (await reload(session, fresh)).remaining == Decimal("4")


async def test_a_draw_beyond_the_available_stock_is_rejected(session, ingredient, one_lot):
    with pytest.raises(BusinessRuleError):
        await apply_stock_movement(session, draw(ingredient, "99"), actor_id=1)


async def test_the_three_tiers_stay_in_sync(session, ingredient, two_lots):
    """§3.2.2: the ledger, the lot cache and the ingredient total must agree."""
    await apply_stock_movement(session, draw(ingredient, "7"), actor_id=1)

    total = await ingredient_total(session, ingredient.id)
    lots = await lot_total(session, ingredient.id)
    ledger = await ledger_total(session, ingredient.id)

    assert total == lots == ledger == Decimal("3")


async def test_reversing_returns_the_quantity_to_the_original_lot(session, ingredient, two_lots):
    """BR-LOT-01: reversal targets the lot named on the original movement."""
    movements = await apply_stock_movement(session, draw(ingredient, "7"), actor_id=1)
    second = movements[1]

    await reverse_movement(session, second, actor_id=1)

    assert (await reload(session, await lot_of(session, second.lot_id))).remaining == Decimal("5")


async def test_reversal_restores_an_expired_lot_too(session, ingredient, expired_and_fresh):
    """Reversal undoes a real past movement, so expiry must not block it."""
    expired, _ = expired_and_fresh
    movement = await force_draw_from_lot(session, ingredient, expired, "2", actor_id=1)

    await reverse_movement(session, movement, actor_id=1)

    assert (await reload(session, expired)).remaining == Decimal("5")


async def test_a_concurrent_draw_waits_for_the_row_lock(session_factory, ingredient, one_lot):
    """NFR-08: the row lock serialises writers on the same ingredient."""
    async with session_factory() as first, session_factory() as second:
        await apply_stock_movement(first, draw(ingredient, "3"), actor_id=1)
        with pytest.raises(OperationalError):
            await asyncio.wait_for(
                apply_stock_movement(second, draw(ingredient, "3"), actor_id=2), timeout=1
            )
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_inventory_stock.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.inventory.stock`

- [ ] **Step 3: Cài đặt `stock.py`**

`apply_stock_movement()` là **cửa duy nhất** sửa tồn kho. Trình tự bắt buộc:

1. `lock_ingredient()` — `SELECT ... FOR UPDATE` trên dòng `NGUYEN_LIEU`.
2. Với `delta < 0`: duyệt `lots_for_fifo()` (lọc `SoLuongConLai > 0`, `TrangThai != 'Hết hạn'`,
   sắp `NgayNhap` tăng dần), trừ dần; hết lô mà vẫn thiếu thì `BusinessRuleError`.
3. Ghi một `GIAO_DICH_KHO` cho **mỗi lô** bị ảnh hưởng, kèm `TonSauGiaoDich` và `BusinessDate`.
4. Cập nhật `LO_NGUYEN_LIEU.SoLuongConLai` + `TrangThai` của lô.
5. Cập nhật `NGUYEN_LIEU.SoLuongTon`.

`reverse_movement()` cộng trả về `movement.lot_id`, **bỏ qua** kiểm tra hạn dùng.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_inventory_stock.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(inventory): add the stock movement core with FIFO and row locking`

---

## Task 2: Phiếu nhập kho và tạo lô (FR-INV-01, 02 — BR-LOT-01)

**Files:**
- Create: `apps/api/src/app/modules/inventory/schemas.py`
- Create: `apps/api/src/app/modules/inventory/service.py`
- Modify: `apps/api/src/app/modules/inventory/router.py`
- Test: `apps/api/tests/modules/test_inventory_receipts.py`

**Interfaces:**
- Consumes: Task 1, `Supplier`, `Ingredient`, `audit.record`.
- Produces: `create_receipt`, `update_receipt`, `cancel_receipt`, `list_receipts`;
  `GET/POST/PATCH/DELETE /inventory/receipts`.

- [ ] **Step 1: Viết test**

```python
async def test_each_receipt_line_creates_exactly_one_lot(client, warehouse_token, ingredient):
    """BR-LOT-01: the lot is created automatically, the storekeeper never types an expiry."""
    created = await create_receipt(
        client, warehouse_token, lines=[{"ingredient_id": ingredient.id, "quantity": "10", "unit_price": "20000"}]
    )

    lots = await lots_for(client, created.json()["MaPhieuNhap"])
    assert len(lots) == 1
    assert lots[0]["HanSuDung"] == expected_expiry(ingredient)


async def test_the_lot_expiry_is_receipt_date_plus_shelf_life(client, warehouse_token, ingredient):
    created = await create_receipt(client, warehouse_token, on="2026-09-01", lines=[line(ingredient, "10")])

    lot = (await lots_for(client, created.json()["MaPhieuNhap"]))[0]
    assert lot["HanSuDung"] == "2026-09-11"  # ingredient.SoNgayBaoQuan == 10


async def test_an_ingredient_without_shelf_life_gets_no_expiry(client, warehouse_token, dry_goods):
    created = await create_receipt(client, warehouse_token, lines=[line(dry_goods, "10")])

    lot = (await lots_for(client, created.json()["MaPhieuNhap"]))[0]
    assert lot["HanSuDung"] is None


async def test_the_purchase_unit_is_converted_to_the_standard_unit(client, warehouse_token, ingredient):
    """FR-INV-01: quantities are stored in the ingredient's normalised unit."""
    await create_receipt(
        client, warehouse_token,
        lines=[{"ingredient_id": ingredient.id, "quantity": "2", "unit_price": "100000",
                "purchase_unit": "bao", "conversion_factor": "25"}],
    )

    assert await ingredient_total(client, ingredient.id) == Decimal("50")


async def test_receipt_raises_the_stock_and_writes_the_ledger(client, warehouse_token, ingredient):
    await create_receipt(client, warehouse_token, lines=[line(ingredient, "10")])

    movements = await movements_for(client, ingredient.id)
    assert movements[0]["LoaiGiaoDich"] == "Nhập"
    assert movements[0]["SoLuongThayDoi"] == Decimal("10")


async def test_a_receipt_cannot_be_edited_once_stock_left_afterwards(
    client, warehouse_token, posted_receipt_then_issue
):
    """FR-INV-02: adjust through a stocktake instead."""
    response = await update_receipt(client, warehouse_token, posted_receipt_then_issue.id, lines=[])

    assert response.status_code == 422
    assert "kiểm kê" in response.json()["error"]["message"]


async def test_editing_and_cancelling_receipts_is_audited(client, warehouse_token, receipt, db_session):
    await cancel_receipt(client, warehouse_token, receipt.id)

    assert (await latest_audit(db_session)).action == "CANCEL_RECEIPT"


async def test_cancelling_a_receipt_removes_its_stock(client, warehouse_token, ingredient, receipt):
    before = await ingredient_total(client, ingredient.id)

    await cancel_receipt(client, warehouse_token, receipt.id)

    assert await ingredient_total(client, ingredient.id) == before - Decimal("10")
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_inventory_receipts.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

`create_receipt` là một transaction: ghi `PHIEU_NHAP_KHO` + `CHI_TIET_PHIEU_NHAP`, rồi với **mỗi**
dòng tạo một `LO_NGUYEN_LIEU` (`NgayNhap` = `PHIEU_NHAP_KHO.NgayNhap`, `HanSuDung` =
`NgayNhap + SoNgayBaoQuan`), rồi gọi `apply_stock_movement()` loại `Nhập`.
`HeSoQuyDoi` quy đổi `DonViMuaGoc` sang đơn vị chuẩn **trước** khi lưu `SoLuong`.
`cancel_receipt` chỉ chạy khi chưa có giao dịch xuất nào sau đó (FR-INV-02); hủy bằng cách ghi giao
dịch đảo, **không** xóa lô.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_inventory_receipts.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(inventory): record goods receipts and create lots automatically`

---

## Task 3: Xuất kho thủ công (FR-INV-05, 06)

**Files:**
- Modify: `apps/api/src/app/modules/inventory/service.py`
- Modify: `apps/api/src/app/modules/inventory/router.py`
- Test: `apps/api/tests/modules/test_inventory_issues.py`

**Interfaces:**
- Consumes: Task 1–2.
- Produces: `create_issue`, `list_issues`; `GET/POST /inventory/issues`.

- [ ] **Step 1: Viết test**

```python
async def test_a_manual_issue_draws_fifo_and_writes_the_ledger(client, warehouse_token, ingredient, two_lots):
    """FR-INV-05."""
    await create_issue(client, warehouse_token, reason="Hao hụt", lines=[line(ingredient, "3")])

    movements = await movements_for(client, ingredient.id)
    assert movements[-1]["LoaiGiaoDich"] == "Xuất thủ công"


async def test_an_issue_beyond_the_available_stock_is_rejected(client, warehouse_token, ingredient, one_lot):
    """FR-INV-06."""
    response = await create_issue(client, warehouse_token, reason="Hao hụt", lines=[line(ingredient, "99")])

    assert response.status_code == 422
    assert "kiểm kê" in response.json()["error"]["message"]


async def test_an_expired_lot_can_be_written_off_manually(client, warehouse_token, ingredient, expired_lot):
    """BR-LOT-01: expired lots leave only through a manual write-off."""
    response = await create_issue(
        client, warehouse_token, reason="Hết hạn", lines=[line(ingredient, "5")]
    )

    assert response.status_code == 201


async def test_manual_write_off_is_audited(client, warehouse_token, ingredient, one_lot, db_session):
    await create_issue(client, warehouse_token, reason="Hao hụt", lines=[line(ingredient, "1")])

    assert (await latest_audit(db_session)).action == "MANUAL_STOCK_ISSUE"


async def test_a_cashier_cannot_write_stock_off(client, cashier_token, ingredient):
    """Table 33."""
    response = await create_issue(client, cashier_token, reason="Hao hụt", lines=[line(ingredient, "1")])

    assert response.status_code == 403
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_inventory_issues.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

Khác với trừ tự động, xuất thủ công **được phép** chọn lô `Hết hạn` — nên `apply_stock_movement()`
nhận cờ `allow_expired` trong `StockChange`. Mặc định cờ này tắt để bảo vệ luồng bán hàng.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_inventory_issues.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(inventory): write stock off manually with the negative-stock guard`

---

## Task 4: Kiểm kê định kỳ (FR-INV-08, FR-INV-09 — BR-LOT-02)

**Files:**
- Modify: `apps/api/src/app/modules/inventory/service.py`
- Modify: `apps/api/src/app/modules/inventory/router.py`
- Test: `apps/api/tests/modules/test_inventory_stocktakes.py`

**Interfaces:**
- Consumes: Task 1–3.
- Produces: `create_stocktake`, `record_counts`, `confirm_stocktake`, `list_stocktakes`;
  `GET/POST /inventory/stocktakes`, `POST /inventory/stocktakes/{id}/confirm`.

- [ ] **Step 1: Viết test**

```python
async def test_the_difference_is_computed_by_the_database(client, warehouse_token, stocktake_line):
    """CHI_TIET_KIEM_KE.ChenhLech is a generated column."""
    line = (await get_stocktake_line(client, stocktake_line.id))
    assert line["ChenhLech"] == line["TonThucTe"] - line["TonHeThong"]


async def test_confirming_a_shortfall_draws_fifo_down_to_the_counted_total(
    client, warehouse_token, ingredient, two_lots, stocktake
):
    """BR-LOT-02: a negative difference is allocated to lots FIFO."""
    await record_counts(client, warehouse_token, stocktake.id, [(ingredient.id, "3")])
    await confirm_stocktake(client, warehouse_token, stocktake.id)

    assert await ingredient_total(client, ingredient.id) == Decimal("3")


async def test_confirming_a_surplus_adds_to_the_newest_live_lot(
    client, warehouse_token, ingredient, two_lots, stocktake
):
    await record_counts(client, warehouse_token, stocktake.id, [(ingredient.id, "12")])
    await confirm_stocktake(client, warehouse_token, stocktake.id)

    newest = max(two_lots, key=lambda lot: lot.received_on)
    assert (await reload_lot(client, newest.id))["SoLuongConLai"] == Decimal("7")


async def test_a_surplus_with_no_live_lot_creates_an_adjustment_lot(
    client, warehouse_token, ingredient_with_no_lots, stocktake
):
    """BR-LOT-02: flagged so it is never mistaken for a real delivery."""
    await record_counts(client, warehouse_token, stocktake.id, [(ingredient_with_no_lots.id, "4")])
    await confirm_stocktake(client, warehouse_token, stocktake.id)

    lot = (await lots_for(client, ingredient_with_no_lots.id))[0]
    assert lot["LoDieuChinhKiemKe"] is True
    assert lot["HanSuDung"] is None


async def test_each_adjusted_lot_gets_its_own_ledger_row(client, warehouse_token, ingredient, two_lots, stocktake):
    await record_counts(client, warehouse_token, stocktake.id, [(ingredient.id, "1")])
    await confirm_stocktake(client, warehouse_token, stocktake.id)

    adjustments = [m for m in await movements_for(client, ingredient.id) if m["LoaiGiaoDich"] == "Điều chỉnh kiểm kê"]
    assert len(adjustments) == 2


async def test_the_draft_cannot_be_confirmed_until_every_line_is_counted(
    client, warehouse_token, stocktake_two_lines
):
    await record_counts(client, warehouse_token, stocktake_two_lines.id, [(1, "3")])

    assert (await confirm_stocktake(client, warehouse_token, stocktake_two_lines.id)).status_code == 422


async def test_confirming_is_audited(client, warehouse_token, ingredient, two_lots, stocktake, db_session):
    await record_counts(client, warehouse_token, stocktake.id, [(ingredient.id, "3")])
    await confirm_stocktake(client, warehouse_token, stocktake.id)

    assert (await latest_audit(db_session)).action == "CONFIRM_STOCKTAKE"


async def test_a_stocktake_is_the_way_back_after_a_refused_write_off(
    client, warehouse_token, ingredient, one_lot
):
    """FR-INV-09: when the figures disagree, a stocktake is the only way out."""
    refused = await create_issue(client, warehouse_token, reason="Hao hụt", lines=[line(ingredient, "99")])
    assert refused.status_code == 422
    assert "kiểm kê" in refused.json()["error"]["message"]

    stocktake_id = (await create_stocktake(client, warehouse_token)).json()["MaPhieuKiemKe"]
    await record_counts(client, warehouse_token, stocktake_id, [(ingredient.id, "5")])
    await confirm_stocktake(client, warehouse_token, stocktake_id)

    assert await ingredient_total(client, ingredient.id) == Decimal("5")
    assert (await create_issue(
        client, warehouse_token, reason="Hao hụt", lines=[line(ingredient, "2")]
    )).status_code == 201

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_inventory_stocktakes.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

`confirm_stocktake` là transaction duy nhất: với mỗi dòng, phân bổ `ChenhLech` xuống lô theo BR-LOT-02,
gọi `apply_stock_movement()` cho từng lô bị ảnh hưởng với `LoaiGiaoDich = 'Điều chỉnh kiểm kê'` và
`MaChiTietKiemKe` tương ứng, rồi đặt `PHIEU_KIEM_KE.TrangThai = 'Đã xác nhận'`.
Kiểm kê ghi **đè** tồn (FR-INV-08), nên nó là con đường duy nhất sửa sai lệch.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_inventory_stocktakes.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(inventory): run periodic stocktakes and allocate differences to lots`

---

## Task 5: Giá bình quân gia quyền và job backfill (FR-REP-05)

**Files:**
- Create: `apps/api/src/app/modules/inventory/costing.py`
- Modify: `apps/api/src/app/modules/inventory/router.py`
- Test: `apps/api/tests/modules/test_inventory_costing.py`

**Interfaces:**
- Consumes: `MonthlyAverageCost`, `StockIssueLine`, `GoodsReceiptLine`.
- Produces: `close_month(session, month: int) -> MonthlyAverageCost` (một nguyên liệu);
  `backfill_issue_costs(session, month: int) -> int` (số dòng cập nhật);
  `POST /inventory/costing/{month}/close`.

- [ ] **Step 1: Viết test**

```python
async def test_the_weighted_average_uses_receipts_of_that_month_only(session, receipts_in_two_months):
    """FR-REP-05a."""
    cost = await close_month(session, 202609)

    assert cost.average_price == Decimal("22500")  # (10×20000 + 10×25000) / 20
    assert cost.total_quantity == Decimal("20")


async def test_an_issue_before_the_month_is_closed_is_provisional(session, issue_before_close):
    """A zero cost marks the row as not yet costed."""
    assert issue_before_close.estimated_cost == Decimal("0")


async def test_backfill_fills_in_rows_left_at_zero(session, month_closed_after_issue):
    updated = await backfill_issue_costs(session, 202609)

    assert updated == 1
    line = await reload_issue_line(session, month_closed_after_issue.id)
    assert line.estimated_cost == Decimal("22500") * line.quantity


async def test_backfill_leaves_rows_that_already_have_a_cost(session, month_closed_after_issue):
    await backfill_issue_costs(session, 202609)

    assert await backfill_issue_costs(session, 202609) == 0


async def test_closing_a_month_twice_recomputes_rather_than_duplicates(session, receipts_in_one_month):
    await close_month(session, 202609)
    await close_month(session, 202609)

    assert await monthly_cost_count(session, 202609) == 1
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_inventory_costing.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.inventory.costing`

- [ ] **Step 3: Cài đặt**

`close_month` tính `SUM(SoLuong × DonGia) / SUM(SoLuong)` trên `CHI_TIET_PHIEU_NHAP` thuộc tháng
(join `PHIEU_NHAP_KHO.NgayNhap`), upsert vào `GIA_BINH_QUAN_THANG` theo khóa ghép
`(MaNguyenLieu, Thang)`. `backfill_issue_costs` quét `CHI_TIET_PHIEU_XUAT` của tháng còn
`GiaVonUocTinh = 0` và cập nhật theo đơn giá vừa chốt — **job này là thành phần bắt buộc của MVP**
(§3.2.2).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_inventory_costing.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(inventory): close monthly weighted-average costs and backfill issues`

---

## Task 6: Danh sách tồn kho, cảnh báo và tự động ẩn món (FR-INV-07, 10, 12 — FR-CAT-27a)

**Files:**
- Modify: `apps/api/src/app/modules/inventory/service.py`
- Modify: `apps/api/src/app/modules/inventory/router.py`
- Modify: `apps/api/src/app/modules/catalog/service.py` (hàm recompute cờ hết nguyên liệu)
- Create: `apps/web/src/features/inventory/stock-table.tsx`
- Create: `apps/web/src/features/inventory/receipt-form.tsx`
- Create: `apps/web/src/features/inventory/stock-table.test.tsx`
- Modify: `apps/web/src/app/(app)/inventory/page.tsx`
- Test: `apps/api/tests/modules/test_inventory_listing.py`

**Interfaces:**
- Consumes: Task 1–5, `effective_min_stock`, `active_recipe`/`recipe_items` (Phase 2).
- Produces: `list_stock`, `low_stock_alerts`;
  `recompute_automatic_out_of_stock(session, ingredient_ids) -> list[int]`;
  `GET /inventory/stock`; `StockTable`, `ReceiptForm`.

- [ ] **Step 1: Viết test**

```python
async def test_a_lot_below_its_own_threshold_is_flagged(client, warehouse_token, ingredient_below_threshold):
    """FR-INV-07."""
    item = (await list_stock(client, warehouse_token)).json()["items"][0]

    assert item["CanhBaoTonThap"] is True


async def test_an_ingredient_without_its_own_threshold_uses_the_default(
    client, warehouse_token, ingredient_using_default_threshold, config_default
):
    item = (await list_stock(client, warehouse_token)).json()["items"][0]
    assert item["MucTonToiThieuApDung"] == config_default


async def test_stock_can_be_filtered_by_name_and_alert_state(client, warehouse_token, mixed_stock):
    by_name = (await list_stock(client, warehouse_token, search="bột")).json()["items"]
    alerted = (await list_stock(client, warehouse_token, alerting=True)).json()["items"]

    assert all("bột" in item["TenNguyenLieu"].lower() for item in by_name)
    assert all(item["CanhBaoTonThap"] for item in alerted)


async def test_the_cashier_sees_only_the_out_of_stock_signal(client, cashier_token):
    """Table 33: the cashier sees the alert, not the stock figures."""
    response = await list_stock(client, cashier_token)

    assert response.status_code == 200
    assert "SoLuongTon" not in response.json()["items"][0]


async def test_a_dish_is_hidden_when_its_ingredients_no_longer_cover_it(
    session, dish_with_recipe, ingredient_at_the_limit
):
    """FR-INV-10 and FR-CAT-27a: stock decides, without anyone pressing a button."""
    hidden = await recompute_automatic_out_of_stock(session, [ingredient_at_the_limit.id])

    assert dish_with_recipe.id in hidden
    assert (await get_dish(session, dish_with_recipe.id)).auto_out_of_stock is True


async def test_the_dish_comes_back_as_soon_as_stock_covers_it_again(
    session, dish_with_recipe, ingredient_restocked
):
    """FR-CAT-27a: the flag clears itself; only the manager clears the manual one."""
    await recompute_automatic_out_of_stock(session, [ingredient_restocked.id])

    dish = await get_dish(session, dish_with_recipe.id)
    assert dish.auto_out_of_stock is False


async def test_the_manual_flag_survives_a_restock(session, dish_with_manual_flag, ingredient_restocked):
    """FR-CAT-27b: two independent causes, and the manual one stays until a human clears it."""
    await recompute_automatic_out_of_stock(session, [ingredient_restocked.id])

    dish = await get_dish(session, dish_with_manual_flag.id)
    assert dish.auto_out_of_stock is False
    assert dish.manual_out_of_stock is True
    assert dish.status == "Hết nguyên liệu"


async def test_a_dish_with_no_recipe_is_never_auto_hidden(session, draft_dish, ingredient):
    """A draft dish is off the order screen for a different reason."""
    hidden = await recompute_automatic_out_of_stock(session, [ingredient.id])

    assert draft_dish.id not in hidden


async def test_every_stock_change_recomputes_the_affected_dishes(
    client, warehouse_token, dish_with_recipe, ingredient
):
    """The hook must fire on receipt, issue, stocktake and order draw alike."""
    await create_issue(client, warehouse_token, reason="Hao hụt", lines=[line(ingredient, "99")])

    assert (await get_dish(db, dish_with_recipe.id)).auto_out_of_stock is True
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_inventory_listing.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt API rồi giao diện**

`list_stock` trả `MucTonToiThieuApDung` (mức riêng hoặc mặc định) và `CanhBaoTonThap` =
`SoLuongTon < MucTonToiThieuApDung` (FR-INV-07, FR-INV-12). Với vai trò Thu ngân, response schema
**không** có trường số lượng — chỉ cờ cảnh báo (Bảng 32: Thu ngân "Chỉ đọc `SoLuongTon` (cảnh báo
hết món)").

`recompute_automatic_out_of_stock()` là **móc nối kho → danh mục** (FR-INV-10, FR-CAT-27a): với mỗi
nguyên liệu vừa đổi, tìm các món dùng nguyên liệu đó trong phiên bản công thức **đang hiệu lực**, rồi
tính `SoLuongTon` hiện có đủ cho định lượng một suất hay không; đặt `HetNLTuDong` tương ứng. Hàm này
phải được gọi ở **mọi** đường làm đổi tồn kho: `apply_stock_movement()` là điểm gọi duy nhất — đặt
lời gọi ngay trong đó để không đường nào quên, chứ không rải ở từng service.

Giao diện: bảng tồn kho có lọc theo tên/trạng thái cảnh báo, bốn trạng thái hiển thị theo §3.3.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_inventory_listing.py -v && cd ../../../apps/web && pnpm test`
Expected: PASS

- [ ] **Step 5: Chạy cổng kiểm tra đầy đủ**

Run: `UV_CACHE_DIR=/tmp/uv-cache make gate`
Expected: xanh. Commit: `feat(inventory): expose stock levels, alerts and the warehouse screens`

---

## Kiểm chứng

| Cổng | Lệnh | Kỳ vọng |
| --- | --- | --- |
| Lõi kho + FIFO + khóa dòng | `pytest tests/modules/test_inventory_stock.py` | xanh |
| Phiếu nhập + tạo lô | `pytest tests/modules/test_inventory_receipts.py` | xanh |
| Xuất thủ công | `pytest tests/modules/test_inventory_issues.py` | xanh |
| Kiểm kê | `pytest tests/modules/test_inventory_stocktakes.py` | xanh |
| Giá bình quân + backfill | `pytest tests/modules/test_inventory_costing.py` | xanh |
| Tồn kho + cảnh báo + tự ẩn món | `pytest tests/modules/test_inventory_listing.py` | xanh |
| Toàn bộ | `make gate` | xanh |

## Rủi ro

- **Test khóa dòng cần MySQL thật.** SQLite không hỗ trợ `SELECT ... FOR UPDATE`, nên
  `test_a_concurrent_draw_waits_for_the_row_lock` phải đánh dấu `integration` và chạy trên MySQL.
- **Ba tầng lệch nhau** là lỗi tốn kém nhất. Mọi test ở Task 1 đều kiểm tra cả ba tầng bằng nhau;
  giữ thói quen đó cho mọi thay đổi tồn kho về sau.
- **`allow_expired`**: nếu đặt mặc định `True` thì luồng bán hàng sẽ trừ vào lô hết hạn — vi phạm
  BR-LOT-01. Giữ mặc định `False`, chỉ bật ở `create_issue` với lý do `Hết hạn`.
- **Job backfill chạy sau**: báo cáo hao hụt (Phase 5) phải hiển thị nhãn "tạm tính" cho dòng còn
  `GiaVonUocTinh = 0`, nếu không người quản lý sẽ đọc số sai.
- **Hủy phiếu nhập** phải ghi giao dịch đảo chứ không xóa lô — xóa lô sẽ mồ côi mọi
  `GIAO_DICH_KHO` đã tham chiếu nó.
- **Móc nối tự ẩn món** (FR-INV-10) là chỗ dễ bỏ sót nhất: nếu chỉ gọi ở phiếu nhập mà quên ở xuất
  thủ công, kiểm kê hay lúc bán hàng thì món sẽ hiển thị sai. Đặt lời gọi **bên trong**
  `apply_stock_movement()` — mọi đường đổi tồn kho đều đi qua đó.
