# Phase 4 — Module 2: Quản lý bán hàng

> **Cho người thực thi:** dùng skill `executing-plans` để chạy kế hoạch này theo từng task.

**Mục tiêu:** Toàn bộ FR-SALE-01…29: lập order, in phiếu bếp, trừ/hoàn kho theo trạng thái món, đổi
bàn, thanh toán tiền mặt/QR, đối soát thủ công, hóa đơn, hủy order.

**Kiến trúc:** Module `sales` sở hữu sáu bảng. Đây là phase **đường đi của tiền** nên các bất biến
nghiệp vụ phải được ép ở tầng service, không dựa vào giao diện. Module gọi lại hai hợp đồng đã chốt:
`catalog.versions.active_price/active_recipe` (Phase 2) và `inventory.stock.apply_stock_movement`
(Phase 3).

**Spec:** báo cáo §2.4.2 (FR-SALE-01…29), §3.2.1 a13–a18, §3.2.2 (BR-ORDER-01, BR-CTO-01,
`BusinessDate` denormalize trên `HOA_DON`/`GIAO_DICH_THANH_TOAN`), SD-02/SD-03a/SD-03b.

**Phụ thuộc:** Phase 0–3. **Lộ trình:** `docs/plans/2026-09-24-master-roadmap.md`

**Nhánh:** `feat/phase-4-sales` · **Cổng người duyệt:** G3 (đường đi của tiền)

## Ràng buộc chung

- **Order chỉ tồn tại từ lúc Submit** (FR-SALE-03) — không lưu order rỗng.
- `MaOrderHienThi` dạng `ORD-ddMMyy-nnn`, `nnn` bắt đầu từ 001 **mỗi Business Date**, duy nhất toàn
  hệ thống, **số đã cấp không tái sử dụng** kể cả khi rollback (FR-SALE-04).
- Chỉ sửa/hủy món khi món đang `Chờ làm`; từ `Đã xác nhận xong` trở đi là khóa (FR-SALE-07).
- Sau tất toán — kể cả `Chờ đối soát` — order **khóa hoàn toàn** (FR-SALE-20).
- Webhook xử lý **idempotent**: không tạo hóa đơn hay ghi doanh thu lần hai (FR-SALE-16).
- Chỉ **Quản lý** xác nhận kết quả đối soát (FR-SALE-18) — tách khỏi Thu ngân đã nhận tiền.
- Mọi thao tác rủi ro ghi audit log: hủy món, đổi bàn, hủy order, chuyển `Chờ đối soát`, hủy QR.
- Thao tác nghiệp vụ chính (submit order, thanh toán, cập nhật món) phản hồi **dưới 2 giây** ở tải
  bình thường (NFR-01); không đặt truy vấn nặng trong đường submit.
- Webhook sai chữ ký/sai số tiền phải được **ghi log** để điều tra, nhưng response không lộ chi tiết
  (NFR-15).
- Giao diện gọi món và thanh toán kiểm thử trên Chrome, Edge, Safari ở cả máy tính lẫn tablet (NFR-17).
- `make gate` xanh trước khi kết thúc mỗi task.

## Hợp đồng với các phase khác

| Hướng | Hàm / kiểu | Phase sở hữu | Phase tiêu thụ |
| --- | --- | --- | --- |
| Cấp | `submit_order`, `pay_cash`, `start_qr`, `expire_stale_qr` | 4 (Task 1–6) | 7 (`seed_operations`) |
| Cấp | `DEM_ORDER` (bảng đếm số order) | 4 (Task 1) | 0 (`EXPECTED_TABLES` phải cập nhật), 7 |
| Cấp | `ensure_order_is_open(order) -> None`, `OPEN_ORDER_STATUSES` | 4 (Task 1) | 4 (Task 2–6) |
| Nhận | `apply_stock_movement`, `reload` | 3 (Task 1) | 4 (Task 1) |
| Nhận | `active_price`, `active_recipe`, `set_table_occupied`/`release_table` | 2 (Task 2–4) | 4 (Task 1) |
| Nhận | `seed_reference_data` | 1 (Task 1) | 7 (trước khi seed) |

**`DEM_ORDER` là bảng thứ 30, không có trong báo cáo.** Phase 0 Task 5 viết `EXPECTED_TABLES` với
đúng 29 bảng theo §3.2.1; **Phase 4 Task 1 thêm `DEM_ORDER` vào `sales/models.py` và phải sửa
`EXPECTED_TABLES` trong `tests/schema/test_schema_contract.py` cùng lúc** — nếu không,
`test_the_schema_has_exactly_the_29_tables_of_the_report` sẽ đỏ ngay khi bảng này xuất hiện.

Lý do không đưa `DEM_ORDER` vào Phase 0: nó phát sinh từ một ràng buộc nghiệp vụ (FR-SALE-04 "số đã
cấp không được tái sử dụng") chỉ lộ ra khi viết test rollback — nó không có trong báo cáo, nên ghi nó
vào Phase 0 như thể có từ đầu là làm sai lệch tài liệu so với báo cáo. Tên test vẫn đúng nếu đọc là
"29 bảng của báo cáo" + bảng phụ trợ; đổi tên test thành
`test_the_schema_has_the_report_tables_plus_the_counter` khi sửa, để tên không nói dối.

## Cấu trúc file

| File | Trách nhiệm |
| --- | --- |
| `apps/api/src/app/modules/sales/schemas.py` | Hợp đồng request/response. |
| `apps/api/src/app/modules/sales/orders.py` | Vòng đời order: submit, thêm/sửa/hủy món, đổi bàn, hủy order. |
| `apps/api/src/app/modules/sales/payments.py` | Tiền mặt, QR, webhook, đối soát, phát hành hóa đơn. |
| `apps/api/src/app/modules/sales/tickets.py` | Sinh nội dung phiếu bếp + ghi `PHIEU_BEP`. |
| `apps/api/src/app/modules/sales/service.py` | Điều phối, gắn audit log. |
| `apps/api/src/app/modules/sales/router.py` | Tầng HTTP. |
| `apps/web/src/features/sales/` | Màn hình gọi món, thanh toán, chi tiết order, tra cứu. |
| `apps/api/tests/modules/test_sales_*.py` | Test theo từng nhóm. |

**Fixture của phase này** (khai báo trong `tests/modules/conftest.py`): `dish`, `scarce_dish`, `table`,
`table2`, `free_table`, `occupied_table`, `open_order`, `settled_order`, `single_line_order`,
`order_with_mixed_lines`, `order_awaiting_reconciliation`, `line`, `waiting_line`, `served_line`,
`payment`, `live_qr`, `stale_qr`, `expired_qr`, `ticket`, `printer_down`.

Helper đọc dùng ở đây (`counter_for`, `payment_status`, `payment_row`, `order_status`, `line_status`,
`invoice_count`, `invoice_business_date`, `payment_business_date`, `order_count`, `order_table`,
`order_updated_at`, `tickets_for`, `ticket_by_id`, `rejected_webhook_count`, `ingredient_total`,
`audit_count`, `latest_audit`) đến từ `tests/helpers.py` — Phase 0 Task 0.

---

## Task 1: Khởi tạo order, mã order và trừ kho (FR-SALE-01…06, 08, 09 — SD-02)

**Files:**
- Create: `apps/api/src/app/modules/sales/schemas.py`
- Create: `apps/api/src/app/modules/sales/orders.py`
- Create: `apps/api/src/app/modules/sales/service.py`
- Modify: `apps/api/src/app/modules/sales/models.py` (thêm `DEM_ORDER` — bảng thứ 30)
- Modify: `apps/api/tests/schema/test_schema_contract.py` (thêm `DEM_ORDER` vào `EXPECTED_TABLES`)
- Modify: `apps/api/src/app/modules/sales/router.py`
- Test: `apps/api/tests/modules/test_sales_orders.py`

**Interfaces:**
- Consumes: `Order`, `OrderLine`;
  `catalog.versions.active_price(session, dish_id, business_date) -> Decimal | None` và
  `catalog.versions.active_recipe(session, dish_id, business_date) -> Recipe | None` (Phase 2);
  `inventory.stock.apply_stock_movement(session, change, *, actor_id) -> list[StockMovement]` và
  `inventory.stock.reverse_movement(session, movement, *, actor_id) -> StockMovement` (Phase 3);
  `catalog.service.set_table_occupied`/`release_table` (Phase 2); `business_date_of`.
- Produces: `OrderLineInput`; `submit_order(session, payload, *, actor) -> Order`;
  `next_display_code(session, business_date) -> str`;
  `ensure_order_is_open(order) -> None` (**khai báo ngay ở task này**, dùng lại ở Task 2–6);
  `OPEN_ORDER_STATUSES: frozenset[str]`;
  `POST /sales/orders`, `GET /sales/orders/{id}`.

- [ ] **Step 1: Viết test**

```python
async def test_a_submitted_order_takes_its_price_from_the_active_version(
    client, cashier_token, dish, table, db_session
):
    """FR-SALE-01 and the price snapshot rule of section 3.2."""
    created = await submit_order(client, cashier_token, table_id=table.id, lines=[(dish.id, 2)])

    line = created.json()["lines"][0]
    assert line["DonGia"] == str(await active_price(db_session, dish.id, today()))
    assert line["MaPhienBanGia"] is not None
    assert line["MaCongThuc"] is not None


async def test_the_display_code_counts_from_001_per_business_date(client, cashier_token, dish, table):
    """FR-SALE-04."""
    first = await submit_order(client, cashier_token, table_id=table.id, lines=[(dish.id, 1)])
    second = await submit_order(client, cashier_token, table_id=table2.id, lines=[(dish.id, 1)])

    assert first.json()["MaOrderHienThi"].endswith("-001")
    assert second.json()["MaOrderHienThi"].endswith("-002")


async def test_a_rolled_back_order_does_not_release_its_number(
    client, cashier_token, dish, table, table2, monkeypatch
):
    """FR-SALE-04: the counter lives outside the order transaction, so the number is burnt."""
    await submit_order(client, cashier_token, table_id=table.id, lines=[(dish.id, 1)])
    monkeypatch.setattr(orders, "write_kitchen_ticket", fail)
    with pytest.raises(Exception):
        await submit_order(client, cashier_token, table_id=table2.id, lines=[(dish.id, 1)])

    third = await submit_order(client, cashier_token, table_id=table2.id, lines=[(dish.id, 1)])
    assert third.json()["MaOrderHienThi"].endswith("-003")


async def test_the_counter_starts_at_one_for_each_business_date(client, cashier_token, dish, table, db_session):
    """FR-SALE-04: numbering restarts per business date, not per calendar day."""
    await submit_order(client, cashier_token, table_id=table.id, lines=[(dish.id, 1)])

    assert await counter_for(db_session, today()) == 1
    assert await counter_for(db_session, tomorrow()) == 0


async def test_submitting_occupies_the_table_and_draws_stock(client, cashier_token, dish, table):
    """FR-SALE-03."""
    await submit_order(client, cashier_token, table_id=table.id, lines=[(dish.id, 2)])

    assert await table_status(table.id) == "Đang phục vụ"
    assert await ingredient_total(dish) == initial - expected_draw(dish, 2)


async def test_takeaway_orders_carry_no_table(client, cashier_token, dish):
    created = await submit_order(client, cashier_token, table_id=None, order_type="Mang về", lines=[(dish.id, 1)])

    assert created.json()["MaBan"] is None


async def test_a_dish_that_ran_out_is_rejected_but_the_others_are_kept(client, cashier_token, dish, scarce_dish, table):
    """FR-SALE-05."""
    response = await submit_order(
        client, cashier_token, table_id=table.id, lines=[(dish.id, 1), (scarce_dish.id, 99)]
    )

    assert response.status_code == 201
    assert [line["MaMon"] for line in response.json()["lines"]] == [dish.id]
    assert response.json()["rejected"] == [{"MaMon": scarce_dish.id, "reason": "không đủ tồn kho"}]


async def test_an_order_where_every_dish_fails_is_not_created(client, cashier_token, scarce_dish, table):
    """FR-SALE-05: nothing is written when no line survives."""
    response = await submit_order(client, cashier_token, table_id=table.id, lines=[(scarce_dish.id, 99)])

    assert response.status_code == 422
    assert await order_count() == 0


async def test_a_note_is_stored_per_line_and_does_not_change_stock(client, cashier_token, dish, table):
    """FR-SALE-02."""
    created = await submit_order(
        client, cashier_token, table_id=table.id, lines=[(dish.id, 1, "không hành")]
    )

    assert created.json()["lines"][0]["GhiChu"] == "không hành"


async def test_adding_a_dish_to_an_open_order_draws_more_stock(client, cashier_token, open_order, dish):
    """FR-SALE-06 and FR-SALE-09."""
    await add_line(client, cashier_token, open_order.id, dish.id, quantity=2)

    assert await ingredient_total(dish) == initial - expected_draw(dish, 3)


async def test_increasing_the_quantity_beyond_stock_is_refused(client, cashier_token, open_order, scarce_dish):
    """FR-SALE-08."""
    response = await update_line(client, cashier_token, open_order.id, scarce_dish.id, quantity=99)

    assert response.status_code == 422
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_sales_orders.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

**Cấp số order (FR-SALE-04).** Yêu cầu là "số đã cấp không được tái sử dụng, kể cả khi transaction
rollback" — điều đó chỉ đúng nếu bộ đếm **nằm ngoài** transaction ghi order. `SELECT MAX(...) FOR UPDATE`
trên `ORDER` **không** làm được: khi bảng chưa có dòng nào cho Business Date đó thì không có dòng nào
để khoá, nên hai request đồng thời cùng đọc `MAX = NULL` và cùng cấp số `001`.

Thêm bảng đếm `DEM_ORDER(BusinessDate DATE PRIMARY KEY, SoDaCap INT NOT NULL)`:

1. `INSERT INTO DEM_ORDER (BusinessDate, SoDaCap) VALUES (:bd, 1) ON DUPLICATE KEY UPDATE SoDaCap = SoDaCap + 1`
   — câu này **tự khoá dòng** và tự cấp số trong một bước, không cần đọc trước.
2. `SELECT SoDaCap FROM DEM_ORDER WHERE BusinessDate = :bd` để lấy số vừa cấp.
3. Chạy hai bước trên trong **transaction riêng, commit ngay**, trước khi ghi `ORDER`. Rollback ở
   transaction sau không trả lại số — đúng yêu cầu "không tái sử dụng".
4. Định dạng: `ORD-{ddMMyy của BusinessDate}-{SoDaCap:03d}`.

Bảng này là bảng thứ **30**; Phase 0 Task 1–5 phải thêm nó vào `EXPECTED_TABLES` và bảng đếm không
tham chiếu bảng nào nên không ảnh hưởng thứ tự tạo bảng. Nó cũng không lộ ra ngoài: `vw_ai_*` không
phơi bảng này cho trợ lý AI.

`ensure_order_is_open(order)` là **choke point duy nhất** cho FR-SALE-20/25: ném `BusinessRuleError`
khi `TrangThai` không nằm trong `OPEN_ORDER_STATUSES` (`Đang mở`). Định nghĩa nó ở **task này** —
ngay khi endpoint ghi đầu tiên ra đời — rồi Task 2–6 gọi lại, để không tồn tại hai đường kiểm trạng
thái song song. Mọi handler ghi (`submit`, `add_line`, `update_line`, `cancel_line`, `move_table`,
`cancel_order`, `payments`) gọi nó trước khi chạm dữ liệu.

`submit_order()` trong **một transaction**: cấp số (bước riêng ở trên), tra giá + công thức hiệu lực,
kiểm tồn theo công thức, ghi `ORDER` + `CHI_TIET_ORDER`, gọi `apply_stock_movement()` cho từng dòng đủ
tồn, đặt bàn `Đang phục vụ`, ghi `PHIEU_BEP`. Món thiếu tồn bị loại riêng và trả về trong `rejected`
(FR-SALE-05).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_sales_orders.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(sales): submit orders, snapshot prices and draw stock`

---

## Task 2: Trạng thái món, sửa/hủy món, hoàn kho, đổi bàn (FR-SALE-07, 10…13, 26)

**Files:**
- Modify: `apps/api/src/app/modules/sales/orders.py`
- Modify: `apps/api/src/app/modules/sales/service.py`
- Modify: `apps/api/src/app/modules/sales/router.py`
- Test: `apps/api/tests/modules/test_sales_line_lifecycle.py`

**Interfaces:**
- Consumes: Task 1, `reverse_movement`, `release_table`, `set_table_occupied`.
- Produces: `advance_line_status`, `cancel_line`, `move_table`, `cancel_order`;
  `PATCH /sales/orders/{id}/lines/{line_id}`, `POST /sales/orders/{id}/move`,
  `POST /sales/orders/{id}/cancel`.

- [ ] **Step 1: Viết test**

```python
async def test_the_status_only_moves_forward(client, cashier_token, open_order, line):
    """FR-SALE-10."""
    await advance_line_status(client, cashier_token, line.id, to="Đã xác nhận xong")
    await advance_line_status(client, cashier_token, line.id, to="Đã phục vụ")

    assert await line_status(line.id) == "Đã phục vụ"
    assert (await advance_line_status(client, cashier_token, line.id, to="Chờ làm")).status_code == 422


async def test_a_waiting_line_can_be_cancelled_and_returns_its_stock(client, cashier_token, open_order, line, dish):
    """FR-SALE-11 and FR-INV-04."""
    before = await ingredient_total(dish)

    await cancel_line(client, cashier_token, line.id, reason="khách đổi ý")

    assert await ingredient_total(dish) == before + expected_draw(dish, line.quantity)


async def test_a_confirmed_line_cannot_be_cancelled(client, cashier_token, open_order, line):
    """FR-SALE-07: from 'Đã xác nhận xong' onwards the line is locked."""
    await advance_line_status(client, cashier_token, line.id, to="Đã xác nhận xong")

    assert (await cancel_line(client, cashier_token, line.id, reason="x")).status_code == 422


async def test_cancelling_a_line_is_audited_with_actor_quantity_and_reason(
    client, cashier_token, open_order, line, db_session
):
    """FR-SALE-11: the audit row carries who, when, how many and why."""
    await cancel_line(client, cashier_token, line.id, reason="khách đổi ý")

    entry = await latest_audit(db_session)
    assert entry.action == "CANCEL_ORDER_LINE"
    assert entry.after["SoLuong"] == line.quantity
    assert entry.reason == "khách đổi ý"


async def test_reducing_the_quantity_returns_the_difference(client, cashier_token, open_order, line, dish):
    before = await ingredient_total(dish)

    await update_line(client, cashier_token, open_order.id, line.id, quantity=line.quantity - 1)

    assert await ingredient_total(dish) == before + expected_draw(dish, 1)


async def test_cancelling_every_line_closes_the_order_without_an_invoice(
    client, cashier_token, single_line_order, line, dish, table
):
    """FR-SALE-12."""
    await cancel_line(client, cashier_token, line.id, reason="khách về")

    assert await order_status(single_line_order.id) == "Tự động đóng"
    assert await invoice_count(single_line_order.id) == 0
    assert await table_status(table.id) == "Trống"


async def test_moving_a_table_swaps_both_tables(client, cashier_token, open_order, table, free_table):
    """FR-SALE-13."""
    await move_table(client, cashier_token, open_order.id, to=free_table.id)

    assert await order_table(open_order.id) == free_table.id
    assert await table_status(table.id) == "Trống"
    assert await table_status(free_table.id) == "Đang phục vụ"


async def test_moving_to_an_occupied_table_is_refused(client, cashier_token, open_order, occupied_table):
    assert (await move_table(client, cashier_token, open_order.id, to=occupied_table.id)).status_code == 422


async def test_moving_a_table_is_audited(client, cashier_token, open_order, free_table, db_session):
    await move_table(client, cashier_token, open_order.id, to=free_table.id)

    assert (await latest_audit(db_session)).action == "MOVE_ORDER_TABLE"


async def test_only_a_manager_may_cancel_a_whole_order(client, cashier_token, manager_token, open_order):
    """FR-SALE-24."""
    assert (await cancel_order(client, cashier_token, open_order.id, reason="x")).status_code == 403
    assert (await cancel_order(client, manager_token, open_order.id, reason="khách bỏ về")).status_code == 200


async def test_cancelling_a_whole_order_requires_a_reason(client, manager_token, open_order):
    assert (await cancel_order(client, manager_token, open_order.id, reason="")).status_code == 422


async def test_cancelling_returns_only_the_waiting_lines_to_stock(
    client, manager_token, order_with_mixed_lines, waiting_line, served_line
):
    """FR-SALE-26: served dishes were already cooked, so their stock stays consumed."""
    before = await ingredient_total(waiting_line.ingredient_id)

    await cancel_order(client, manager_token, order_with_mixed_lines.id, reason="khách bỏ về")

    assert await ingredient_total(waiting_line.ingredient_id) == before + expected_draw(waiting_line)
    assert await served_line_stock_unchanged(served_line)


async def test_cancelling_a_whole_order_is_audited_with_the_reason(
    client, manager_token, open_order, db_session
):
    await cancel_order(client, manager_token, open_order.id, reason="khách bỏ về")

    entry = await latest_audit(db_session)
    assert entry.action == "CANCEL_ORDER"
    assert entry.reason == "khách bỏ về"
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_sales_line_lifecycle.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

Trạng thái chỉ tiến: `Chờ làm → Đã xác nhận xong → Đã phục vụ`. `cancel_line` và giảm số lượng gọi
`reverse_movement()` cho đúng các giao dịch gốc của dòng đó. `cancel_order` (Quản lý) hoàn kho **chỉ**
cho dòng `Chờ làm`, đặt `TrangThai = 'Đã hủy'`, lưu `LyDoHuy`, trả bàn về `Trống`, và ghi giá trị
order bị hủy để Phase 5 báo cáo (FR-REP-10).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_sales_line_lifecycle.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(sales): drive line states, cancellations, stock returns and table moves`

---

## Task 3: Phiếu bếp (FR-SALE-27, 28)

**Files:**
- Create: `apps/api/src/app/modules/sales/tickets.py`
- Modify: `apps/api/src/app/modules/sales/orders.py`
- Modify: `apps/api/src/app/modules/sales/router.py`
- Test: `apps/api/tests/modules/test_sales_tickets.py`

**Interfaces:**
- Consumes: `KitchenTicket`, `Order`, `OrderLine`.
- Produces: `render_ticket(order, lines) -> str`; `write_kitchen_ticket(session, order, lines, *, actor) -> KitchenTicket`;
  `record_print_result(ticket, ok)`; `POST /sales/orders/{id}/tickets/{ticket_id}/reprint`.

- [ ] **Step 1: Viết test**

```python
async def test_a_ticket_carries_table_code_lines_quantities_and_notes(client, cashier_token, dish, table):
    """FR-SALE-27."""
    order = await submit_order(client, cashier_token, table_id=table.id, lines=[(dish.id, 2, "không hành")])

    ticket = (await tickets_for(client, order.id))[0]
    assert order.json()["MaOrderHienThi"] in ticket["NoiDung"]
    assert "không hành" in ticket["NoiDung"]
    assert "2" in ticket["NoiDung"]


async def test_adding_a_dish_prints_an_additional_ticket(client, cashier_token, open_order, dish):
    """FR-SALE-06: every addition prints its own ticket."""
    await add_line(client, cashier_token, open_order.id, dish.id, quantity=1)

    assert len(await tickets_for(client, open_order.id)) == 2


async def test_a_failed_print_is_recorded_and_the_warning_is_surfaced(client, cashier_token, open_order, dish, printer_down):
    """FR-SALE-28."""
    response = await add_line(client, cashier_token, open_order.id, dish.id, quantity=1)

    assert response.json()["print_warning"] is not None
    assert (await tickets_for(client, open_order.id))[-1]["TrangThaiIn"] == "Thất bại"


async def test_reprinting_is_unlimited_and_does_not_change_the_order(
    client, cashier_token, open_order, ticket
):
    """FR-SALE-28: the employee retries as often as needed."""
    for _ in range(3):
        assert (await reprint(client, cashier_token, open_order.id, ticket.id)).status_code == 200

    assert (await ticket_by_id(ticket.id))["SoLanIn"] == 4
    assert await order_updated_at(open_order.id) == original_updated_at


async def test_the_kitchen_role_cannot_reach_the_api(client, warehouse_token, open_order, ticket):
    """There is no kitchen account in the system (section 1.4.3)."""
    assert (await reprint(client, warehouse_token, open_order.id, ticket.id)).status_code == 403
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_sales_tickets.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.sales.tickets`

- [ ] **Step 3: Cài đặt**

`render_ticket()` sinh **nội dung văn bản** của phiếu. Chi tiết driver máy in nằm ngoài phạm vi
(§1.4.3), nên tầng in thật chỉ là `window.print()` ở giao diện — backend ghi `PHIEU_BEP` với
`NoiDung` và `TrangThaiIn`. In lỗi **không** rollback order (FR-SALE-28): ghi `Thất bại`, trả
`print_warning` cho giao diện.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_sales_tickets.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(sales): print kitchen tickets and handle print failures`

---

## Task 4: Thanh toán tiền mặt và QR (FR-SALE-14, 15, 29 — SD-03a)

**Files:**
- Create: `apps/api/src/app/modules/sales/payments.py`
- Modify: `apps/api/src/app/modules/sales/service.py`
- Modify: `apps/api/src/app/modules/sales/router.py`
- Modify: `apps/api/src/app/core/config.py` (thêm `payment_webhook_secret`)
- Modify: `.env.example` (thêm `PAYMENT_WEBHOOK_SECRET=` — để **trống**, không commit giá trị thật)
- Test: `apps/api/tests/modules/test_sales_payments.py`

**Interfaces:**
- Consumes: `PaymentTransaction`, `Invoice`, `business_date_of`.
- Produces: `PaymentGateway` (protocol: `create_qr`, `verify_webhook`);
  `MockGateway` (mặc định); `start_qr_payment`, `pay_cash`, `cancel_qr`, `handle_webhook`;
  `POST /sales/orders/{id}/payments`, `POST /sales/webhooks/payment`.

- [ ] **Step 1: Viết test**

```python
async def test_cash_payment_settles_the_order_and_issues_an_invoice(client, cashier_token, open_order, table):
    """FR-SALE-14 and FR-SALE-19."""
    response = await pay_cash(client, cashier_token, open_order.id)

    assert response.status_code == 200
    assert response.json()["invoice"]["SoHoaDon"] is not None
    assert response.json()["invoice"]["TongTien"] == open_order.total
    assert await order_status(open_order.id) == "Đã thanh toán"
    assert await table_status(table.id) == "Trống"


async def test_a_qr_transaction_starts_pending_with_a_ten_minute_deadline(client, cashier_token, open_order):
    """FR-SALE-15."""
    created = await start_qr(client, cashier_token, open_order.id)

    body = created.json()
    assert body["TrangThai"] == "Chờ xác nhận"
    assert body["ThoiDiemHetHan"] == body["ThoiDiemTaoQR"] + timedelta(minutes=10)


async def test_a_second_qr_is_refused_while_the_first_is_live(client, cashier_token, open_order, live_qr):
    """FR-SALE-15."""
    assert (await start_qr(client, cashier_token, open_order.id)).status_code == 422


async def test_a_valid_webhook_settles_the_order_and_issues_the_invoice(
    client, cashier_token, open_order, live_qr, table
):
    """FR-SALE-16."""
    response = await webhook(client, live_qr.id, amount=open_order.total, signature="valid")

    assert response.status_code == 200
    assert await payment_status(live_qr.id) == "Thành công"
    assert await invoice_count(open_order.id) == 1


async def test_a_repeated_webhook_does_not_issue_a_second_invoice(client, open_order, live_qr):
    """FR-SALE-16: idempotent."""
    await webhook(client, live_qr.id, amount=open_order.total, signature="valid")
    await webhook(client, live_qr.id, amount=open_order.total, signature="valid")

    assert await invoice_count(open_order.id) == 1


async def test_a_webhook_with_the_wrong_amount_is_refused(client, live_qr, open_order):
    """FR-SALE-16."""
    response = await webhook(client, live_qr.id, amount=open_order.total - 1, signature="valid")

    assert response.status_code == 422
    assert await payment_status(live_qr.id) == "Chờ xác nhận"


async def test_a_webhook_with_a_bad_signature_is_refused(client, live_qr, open_order):
    """FR-SALE-16: refused, never silently accepted.

    The refusal is asserted on the response and on the transaction state, not on a log
    string — log text is not a contract (rule 4 of the global conventions).
    """
    response = await webhook(client, live_qr.id, amount=open_order.total, signature="bad")

    assert response.status_code == 401
    assert await payment_status(live_qr.id) == "Chờ xác nhận"
    assert await invoice_count(open_order.id) == 0


async def test_a_refused_webhook_is_still_recorded_for_investigation(client, live_qr, open_order, db_session):
    """NFR-15: failures are logged server-side, but the API leaks no internals."""
    response = await webhook(client, live_qr.id, amount=open_order.total, signature="bad")

    assert response.status_code == 401
    assert "Traceback" not in response.text
    assert await rejected_webhook_count(db_session, live_qr.id) == 1


async def test_a_cashier_may_cancel_a_live_qr_and_start_a_new_one(client, cashier_token, open_order, live_qr):
    """FR-SALE-29."""
    assert (await cancel_qr(client, cashier_token, live_qr.id)).status_code == 200
    assert await payment_status(live_qr.id) == "Đã hủy"
    assert (await start_qr(client, cashier_token, open_order.id)).status_code == 201


async def test_cancelling_a_qr_is_audited(client, cashier_token, live_qr, db_session):
    await cancel_qr(client, cashier_token, live_qr.id)

    assert (await latest_audit(db_session)).action == "CANCEL_QR_TRANSACTION"


async def test_the_business_date_is_copied_onto_the_payment_and_the_invoice(
    client, cashier_token, open_order, live_qr
):
    """Section 3.2.2: denormalised on purpose, never derived from ThoiDiem."""
    await webhook(client, live_qr.id, amount=open_order.total, signature="valid")

    assert await payment_business_date(live_qr.id) == today()
    assert await invoice_business_date(open_order.id) == today()
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_sales_payments.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.sales.payments`

- [ ] **Step 3: Cài đặt**

`PaymentGateway` là Protocol; `MockGateway` ký webhook bằng HMAC-SHA256 trên
`settings.payment_webhook_secret` và xác thực lại đúng cách (so sánh bằng `hmac.compare_digest`, không
so chuỗi thường) — luồng bảo mật được kiểm thử đầy đủ dù chưa có cổng thật (Q1 ở master roadmap).
Khoá đọc từ settings, **không** hardcode; `.env.example` để trống và ghi rõ đây là giá trị chỉ dùng
cho môi trường cục bộ.

`handle_webhook()` idempotent: **khoá dòng** `GIAO_DICH_THANH_TOAN` (`SELECT ... FOR UPDATE`) trước khi
kiểm trạng thái, vì hai webhook đến song song có thể cùng thấy `Chờ xác nhận` và cùng tạo hóa đơn.
Giao dịch đã `Thành công` thì trả 200 luôn, **không** tạo hóa đơn thứ hai. Phát hành hóa đơn nằm trong
cùng transaction với việc đổi trạng thái giao dịch.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_sales_payments.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(sales): take cash and QR payments behind a gateway adapter`

---

## Task 5: Timeout QR và đối soát thủ công (FR-SALE-17, 18 — SD-03b)

**Files:**
- Modify: `apps/api/src/app/modules/sales/payments.py`
- Modify: `apps/api/src/app/modules/sales/router.py`
- Test: `apps/api/tests/modules/test_sales_reconciliation.py`

**Interfaces:**
- Consumes: Task 4.
- Produces: `expire_stale_qr(session) -> int`; `mark_for_reconciliation`, `record_bank_reference`,
  `resolve_reconciliation`;
  `POST /sales/orders/{id}/reconcile`, `POST /sales/payments/{id}/resolve`.

- [ ] **Step 1: Viết test**

```python
async def test_a_qr_past_its_deadline_becomes_expired(
    client, cashier_token, open_order, stale_qr, db_session
):
    """FR-SALE-17."""
    await expire_stale_qr(db_session)

    assert await payment_status(stale_qr.id) == "Hết hạn"


async def test_an_expired_qr_can_be_flagged_for_reconciliation(client, cashier_token, open_order, expired_qr):
    """FR-SALE-17: the guest says they paid, so it waits for a human."""
    await mark_for_reconciliation(client, cashier_token, expired_qr.id)

    assert await payment_status(expired_qr.id) == "Chờ đối soát"
    assert await order_status(open_order.id) == "Chờ đối soát"


async def test_a_new_qr_is_refused_while_reconciliation_is_pending(client, cashier_token, order_awaiting_reconciliation):
    """FR-SALE-17."""
    assert (await start_qr(client, cashier_token, order_awaiting_reconciliation.id)).status_code == 422


async def test_the_cashier_records_the_bank_reference_and_evidence(
    client, cashier_token, order_awaiting_reconciliation, payment
):
    """FR-SALE-18."""
    response = await record_bank_reference(
        client, cashier_token, payment.id, reference="FT123456", evidence="bien-lai.jpg"
    )

    assert response.status_code == 200
    assert (await payment_row(payment.id))["MaGiaoDichNganHang"] == "FT123456"
    assert (await payment_row(payment.id))["AnhChungTu"] == "bien-lai.jpg"


async def test_only_a_manager_may_resolve_the_reconciliation(client, cashier_token, manager_token, payment):
    """FR-SALE-18: the person who took the money must not confirm it."""
    assert (await resolve(client, cashier_token, payment.id, outcome="received")).status_code == 403
    assert (await resolve(client, manager_token, payment.id, outcome="received")).status_code == 200


async def test_confirming_receipt_settles_the_order_and_issues_the_invoice(
    client, manager_token, order_awaiting_reconciliation, payment, table
):
    """FR-SALE-18."""
    await resolve(client, manager_token, payment.id, outcome="received")

    assert await payment_status(payment.id) == "Thành công"
    assert await invoice_count(order_awaiting_reconciliation.id) == 1
    assert await table_status(table.id) == "Trống"


async def test_reporting_no_transaction_marks_a_dispute(client, manager_token, payment):
    """FR-SALE-18."""
    await resolve(client, manager_token, payment.id, outcome="not_received")

    assert await payment_status(payment.id) == "Tranh chấp"


async def test_the_reconciliation_trail_is_audited(client, manager_token, payment, db_session):
    """FR-SALE-18: reference, confirmer, time and outcome."""
    await resolve(client, manager_token, payment.id, outcome="received")

    entry = await latest_audit(db_session)
    assert entry.action == "RESOLVE_RECONCILIATION"
    assert entry.after["ketQua"] == "received"


async def test_flagging_for_reconciliation_is_audited(client, cashier_token, expired_qr, db_session):
    await mark_for_reconciliation(client, cashier_token, expired_qr.id)

    assert (await latest_audit(db_session)).action == "FLAG_RECONCILIATION"
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_sales_reconciliation.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

`expire_stale_qr()` là job quét các giao dịch `Chờ xác nhận` đã quá `ThoiDiemHetHan`. `resolve()` chỉ
nhận `received` / `not_received`; `received` phát hành hóa đơn trong cùng transaction. Mọi bước ghi
audit.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_sales_reconciliation.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(sales): expire stale QR payments and reconcile them by hand`

---

## Task 6: Khóa order sau tất toán, in lại hóa đơn, tra cứu (FR-SALE-19…23, 25)

**Files:**
- Modify: `apps/api/src/app/modules/sales/payments.py`
- Modify: `apps/api/src/app/modules/sales/service.py`
- Modify: `apps/api/src/app/modules/sales/router.py`
- Test: `apps/api/tests/modules/test_sales_locking_and_search.py`

**Interfaces:**
- Consumes: Task 1–5.
- Produces: `reprint_invoice`, `search_orders`; `POST /sales/orders/{id}/invoice/reprint`,
  `GET /sales/orders`.

- [ ] **Step 1: Viết test**

```python
async def test_a_settled_order_rejects_every_mutation(client, cashier_token, manager_token, settled_order):
    """FR-SALE-20: locked after settlement, including while awaiting reconciliation."""
    assert (await add_line(client, cashier_token, settled_order.id, 1, 1)).status_code == 422
    assert (await cancel_line(client, cashier_token, settled_order.line_id, "x")).status_code == 422
    assert (await cancel_order(client, manager_token, settled_order.id, "x")).status_code == 422


async def test_an_order_awaiting_reconciliation_cannot_be_cancelled(
    client, manager_token, order_awaiting_reconciliation
):
    """FR-SALE-25."""
    response = await cancel_order(client, manager_token, order_awaiting_reconciliation.id, "x")

    assert response.status_code == 422
    assert "QR" in response.json()["error"]["message"]


async def test_reprinting_an_invoice_repeats_the_original_content(client, cashier_token, settled_order):
    """FR-SALE-23: identical content, never editable."""
    first = await get_invoice(client, cashier_token, settled_order.id)
    again = await reprint_invoice(client, cashier_token, settled_order.id)

    assert again.json()["SoHoaDon"] == first.json()["SoHoaDon"]
    assert again.json()["TongTien"] == first.json()["TongTien"]
    assert again.json()["SoLanIn"] == first.json()["SoLanIn"] + 1


async def test_the_invoice_has_no_vat_line(client, cashier_token, settled_order):
    """FR-SALE-19 and section 1.4.3."""
    invoice = (await get_invoice(client, cashier_token, settled_order.id)).json()

    assert "VAT" not in invoice
    assert "Thue" not in invoice


async def test_orders_can_be_found_by_code_table_and_business_date(client, cashier_token, settled_order):
    """FR-SALE-22."""
    by_code = await search_orders(client, cashier_token, code=settled_order.display_code)
    by_table = await search_orders(client, cashier_token, table_id=settled_order.table_id)
    by_date = await search_orders(client, cashier_token, business_date=today())

    assert by_code.json()["total"] == 1
    assert by_table.json()["total"] >= 1
    assert by_date.json()["total"] >= 1


async def test_transactions_carry_a_precise_timestamp(client, cashier_token, settled_order):
    """FR-SALE-21: the input of every report and of the assistant."""
    order = (await get_order(client, cashier_token, settled_order.id)).json()

    assert order["ThoiDiemTao"] is not None
    assert order["ThoiDiemDong"] is not None
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_sales_locking_and_search.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

Mọi endpoint ghi phải kiểm `TrangThai` của order trước: `Đã thanh toán`, `Chờ đối soát`, `Tranh chấp`,
`Đã hủy`, `Tự động đóng` đều là trạng thái khóa. Gom kiểm tra này vào **một** hàm
`ensure_order_is_open(order)` để không sót ở endpoint nào.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_sales_locking_and_search.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(sales): lock settled orders and support invoice reprints`

---

## Task 7: Giao diện bán hàng

**Files:**
- Create: `apps/web/src/features/sales/order-screen.tsx`
- Create: `apps/web/src/features/sales/payment-panel.tsx`
- Create: `apps/web/src/features/sales/payment-panel.test.tsx`
- Create: `apps/web/src/features/sales/order-lookup.tsx`
- Modify: `apps/web/src/app/(app)/sales/page.tsx`

**Interfaces:**
- Consumes: endpoint Task 1–6.
- Produces: `OrderScreen`, `PaymentPanel`, `OrderLookup`.

- [ ] **Step 1: Viết test**

```tsx
it("hides dishes that are out of stock from the picker", async () => {
  stubFetch({ items: [dish({ name: "Phở bò", status: "Hoạt động" }), dish({ name: "Bún chả", status: "Hết nguyên liệu" })] });

  render(<OrderScreen />);

  expect(await screen.findByText("Phở bò")).toBeInTheDocument();
  expect(screen.queryByText("Bún chả")).not.toBeInTheDocument();
});

it("counts the QR deadline down and shows an expiry state", async () => {
  vi.useFakeTimers();
  stubFetch(qr({ ThoiDiemHetHan: inTenMinutes() }));

  render(<PaymentPanel orderId={1} />);
  fireEvent.click(await screen.findByRole("button", { name: "Thanh toán QR" }));

  expect(screen.getByText("10:00")).toBeInTheDocument();
  act(() => vi.advanceTimersByTime(600_000));
  expect(screen.getByText("Hết hạn")).toBeInTheDocument();
});

it("disables creating a new QR while one is still live", async () => {
  stubFetch(qr({ TrangThai: "Chờ xác nhận" }));

  render(<PaymentPanel orderId={1} />);

  expect(await screen.findByRole("button", { name: "Tạo mã QR mới" })).toBeDisabled();
});

it("only offers the full-order cancellation to a manager", async () => {
  saveSession({ token: "t", role: "CASHIER", username: "thungan01" });

  render(<OrderScreen />);

  expect(screen.queryByRole("button", { name: "Hủy toàn bộ order" })).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/web && pnpm test`
Expected: FAIL — module chưa tồn tại

- [ ] **Step 3: Cài đặt**

Theo §3.3: màn hình gọi món hiển thị sơ đồ bàn + danh sách món theo nhóm, **tự động ẩn món `Hết
nguyên liệu`**; màn hình thanh toán có đồng hồ đếm ngược 10 phút và nút tạo QR mới bị vô hiệu hóa khi
giao dịch hiện tại còn hiệu lực hoặc order đang `Chờ đối soát`; nút hủy toàn bộ order chỉ hiện với
Quản lý (FR-SALE-24). Vùng chạm lớn, ưu tiên bàn phím số cho trường số lượng (NFR-13).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/web && pnpm test`
Expected: PASS

- [ ] **Step 5: Chạy cổng kiểm tra đầy đủ**

Run: `UV_CACHE_DIR=/tmp/uv-cache make gate`
Expected: xanh. Commit: `feat(web): build the order, payment and lookup screens`

- [ ] **Step 6: Kiểm thử thủ công trên ba trình duyệt (NFR-17)**

Mở màn hình gọi món và màn hình thanh toán trên Chrome, Edge và Safari, ở cả cỡ máy tính lẫn tablet.
Kiểm: vùng chạm đủ lớn cho thao tác giờ cao điểm, bàn phím số hiện cho trường số lượng, đồng hồ đếm
ngược QR hiển thị đúng. Ghi lại kết quả vào mô tả PR.

---

## Kiểm chứng

| Cổng | Lệnh | Kỳ vọng |
| --- | --- | --- |
| Order + trừ kho | `pytest tests/modules/test_sales_orders.py` | xanh |
| Vòng đời dòng món | `pytest tests/modules/test_sales_line_lifecycle.py` | xanh |
| Phiếu bếp | `pytest tests/modules/test_sales_tickets.py` | xanh |
| Thanh toán + webhook | `pytest tests/modules/test_sales_payments.py` | xanh |
| Timeout + đối soát | `pytest tests/modules/test_sales_reconciliation.py` | xanh |
| Khóa + tra cứu | `pytest tests/modules/test_sales_locking_and_search.py` | xanh |
| Giao diện | `cd apps/web && pnpm test` | xanh |
| Toàn bộ | `make gate` | xanh |

## Rủi ro

- **Đây là phase đường đi của tiền.** Mọi test về webhook, idempotent, đối soát và khóa order phải
  giữ nguyên độ chặt — nới lỏng một test ở đây là mở đường cho ghi nhận doanh thu sai.
- **Idempotent webhook**: nếu chỉ dựa vào `TrangThai` mà không khóa dòng giao dịch, hai webhook đến
  song song có thể cùng tạo hóa đơn. Khóa dòng `GIAO_DICH_THANH_TOAN` trong transaction.
- **Cấp số order**: cách `MAX(...) FOR UPDATE` chịu được tải nhỏ của đồ án nhưng tuần tự hóa theo
  Business Date. Nếu về sau thấy nghẽn, thay bằng bảng đếm riêng — chữ ký `next_display_code()` giữ
  nguyên nên đổi ruột được.
- **Món `Đã phục vụ` không hoàn kho** khi hủy order (FR-SALE-26): đúng theo báo cáo, nhưng nếu nhân
  viên quên cập nhật trạng thái thì kho sẽ bị trừ oan. Đây là giới hạn đã biết (business rule 21) —
  Phase 3 có kiểm kê làm van an toàn.
- **Cổng thanh toán thật chưa chọn (Q1)**: `MockGateway` là mặc định. Khi cắm cổng thật, chỉ cần
  viết một lớp `PaymentGateway` mới và đổi cấu hình; không sửa luồng nghiệp vụ.
