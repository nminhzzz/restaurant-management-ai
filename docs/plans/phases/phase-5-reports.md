# Phase 5 — Module 4: Báo cáo thống kê

> **Cho người thực thi:** dùng skill `executing-plans` để chạy kế hoạch này theo từng task.

**Mục tiêu:** Toàn bộ FR-REP-01…10: doanh thu theo nhiều mốc thời gian, xếp hạng món, biên lợi
nhuận gộp, cấu thành giá vốn, phân bố khung giờ, so sánh hai khoảng, báo cáo order bị hủy.

**Kiến trúc:** Module `reports` **chỉ đọc** — không sở hữu bảng nào. Nó tổng hợp từ `ORDER`,
`HOA_DON`, `GIAO_DICH_THANH_TOAN`, `CHI_TIET_ORDER`, `GIAO_DICH_KHO`, `GIA_BINH_QUAN_THANG`. Toàn bộ
phép gom nhóm theo thời gian dùng **`BusinessDate`** (cột đã denormalize ở Phase 0/4), không suy diễn
lại từ `ThoiDiem`.

**Spec:** báo cáo §2.4.4 (FR-REP-01…10), §3.2.2 (`BusinessDate` denormalize), §3.4.2 (chỉ Quản lý).

**Phụ thuộc:** Phase 4 (dữ liệu order/hóa đơn), Phase 3 (`GIA_BINH_QUAN_THANG`).
**Lộ trình:** `docs/plans/2026-09-24-master-roadmap.md` · **Nhánh:** `feat/phase-5-reports`

## Ràng buộc chung

- **Chỉ Quản lý** truy cập mọi endpoint báo cáo (Bảng 33). Thu ngân và Nhân viên kho nhận 403.
- Gom nhóm theo `BusinessDate`, **không** theo ngày lịch của `ThoiDiem`.
- Giao dịch `Chờ đối soát` **tính tạm vào doanh thu**; khi Quản lý gắn cờ `Tranh chấp` thì **trừ lùi**
  (FR-REP-02). Số liệu tạm phải được đánh dấu rõ.
- Dòng `CHI_TIET_PHIEU_XUAT` còn `GiaVonUocTinh = 0` là **chưa hoàn tất tính giá vốn** — báo cáo phải
  hiển thị nhãn "tạm tính" (FR-REP-05b).
- Biên lợi nhuận gộp chỉ tính ở **mức tổng toàn nhà hàng theo tháng** (FR-REP-04), không theo món.
- Mọi truy vấn qua SQLAlchemy, không nối chuỗi SQL.
- Báo cáo không được suy giảm đáng kể thời gian tải ở quy mô 20.000 order/năm (NFR-03); thao tác
  nghiệp vụ khác vẫn phải dưới 2 giây (NFR-01) — nghĩa là truy vấn báo cáo nặng phải dùng index
  §3.2.3, không quét toàn bảng.
- Giao diện báo cáo kiểm thử trên Chrome, Edge, Safari ở máy tính và tablet (NFR-17) — Task 6 Step 1.
- `make gate` xanh trước khi kết thúc mỗi task.

## Hợp đồng dữ liệu test

Các test dưới đây đọc số liệu **từ chính fixture**, không hardcode con số. Fixture nào cũng phải
phơi ra tổng của nó để test khẳng định *quan hệ* (doanh thu − giá vốn = biên), chứ không khẳng định
một hằng số sẽ vỡ ngay khi ai đó sửa fixture. Tầng fixture nằm ở Phase 0 Task 0; bảng này là hợp
đồng mà phase-5 yêu cầu nó phải cung cấp.

| Fixture | Dựng ra gì | Phơi ra |
| --- | --- | --- |
| `invoices_in_september` | Hóa đơn `Đã thanh toán` của 2 bàn, 2 phương thức | `total: Decimal`, `table_ids: set[int]`, `payment_methods: set[str]` |
| `orders_in_september` | Order đủ trạng thái để xếp hạng | `dish_names`, `top_by_quantity`, `top_by_revenue` |
| `september_data` | Một tháng khép kín: doanh thu, giá vốn, hao hụt | `revenue`, `cogs`, `waste`, `margin` (đều là Decimal), `month = 202609` |
| `order_before_recipe_change` | Order trước một lần đổi công thức | `expected_cost: Decimal` — giá vốn tính tay từ `MaCongThuc` ghi trên dòng |
| `order_after_recipe_change` | Order sau lần đổi đó, dùng phiên bản công thức mới | `expected_cost: Decimal` |
| `disputed_payment` | Một giao dịch `Tranh chấp` trên hóa đơn đã phát hành | `total: Decimal` |
| `order_awaiting_reconciliation` | Một order có giao dịch `Chờ đối soát` | `total: Decimal` |
| `cancelled_orders` | Danh sách order `Đã hủy`/`Tự động đóng` có `LyDoHuy` | `list` các đối tượng có `total: Decimal`, `reason: str` |
| `write_off_in_september` | Một phiếu xuất `Hao hụt` đã tính giá vốn | `value: Decimal` |
| `write_off_before_month_close` | Một dòng xuất còn `GiaVonUocTinh = 0` | `count = 1` |
| `write_off_after_backfill` | Cùng dòng đó sau khi `backfill_issue_costs` chạy | — |
| `orders_in_two_months` | Order trải hai tháng liền kề | `left_month`, `right_month` (`"2026-08"`/`"2026-09"`) |
| `order_with_cancelled_line` | Một order có dòng `Đã hủy` | — |
| `order_at_0130` | Một order đặt lúc 01:30 | `business_date: date`, `placed_at: datetime` |
| `two_months` | Hai tháng liền kề có doanh thu khác nhau | `left_revenue`, `right_revenue` (Decimal), `left_month`, `right_month` |

Quy ước, và cả ba đều bắt buộc:

1. Fixture trả **đối tượng có thuộc tính** (dataclass hoặc `SimpleNamespace`), không trả `dict` — test
   đọc `september_data.revenue`, không `september_data["revenue"]`.
2. Test so **giá trị**, không so hằng số: `assert Decimal(body["DoanhThu"]) == september_data.revenue`.
   Không test nào được chứa `Decimal("10000000")` trần — nó sẽ vỡ ngay khi ai đó sửa fixture.
3. JSON trả `Decimal` dưới dạng **chuỗi**, nên phía test luôn bọc `Decimal(body["X"])` trước khi so.
   So `body["total"] == 10000000` (số) sẽ luôn sai vì `"10000000" != 10000000`.

## Cấu trúc file

| File | Trách nhiệm |
| --- | --- |
| `apps/api/src/app/modules/reports/periods.py` | Quy đổi khoảng thời gian (ngày/tuần/tháng/năm) sang `BusinessDate`. |
| `apps/api/src/app/modules/reports/queries.py` | Các truy vấn tổng hợp, thuần đọc. |
| `apps/api/src/app/modules/reports/schemas.py` | Hợp đồng response. |
| `apps/api/src/app/modules/reports/service.py` | Điều phối, gắn nhãn tạm tính. |
| `apps/api/src/app/modules/reports/router.py` | Tầng HTTP, chặn ở `require_roles(MANAGER)`. |
| `apps/web/src/features/reports/` | Màn hình báo cáo + biểu đồ. |
| `apps/api/tests/modules/test_reports_*.py` | Test theo từng nhóm. |

---

## Task 1: Khoảng thời gian và doanh thu (FR-REP-01, 02)

**Files:**
- Create: `apps/api/src/app/modules/reports/periods.py`
- Create: `apps/api/src/app/modules/reports/queries.py`
- Create: `apps/api/src/app/modules/reports/schemas.py`
- Create: `apps/api/src/app/modules/reports/service.py`
- Modify: `apps/api/src/app/modules/reports/router.py`
- Test: `apps/api/tests/modules/test_reports_revenue.py`

**Interfaces:**
- Consumes: `Invoice`, `PaymentTransaction`, `Order`, `business_date_start`;
  `inventory.costing.MonthlyAverageCost` (Phase 3) cho FR-REP-05a/05b;
  `catalog.versions.active_recipe` (Phase 2) khi cần đối chiếu định lượng.
- Produces: `BusinessPeriod` (dataclass: start, end, granularity);
  `resolve_period(granularity, anchor) -> BusinessPeriod`;
  `revenue_by_period(session, period) -> list[RevenueBucket]`;
  `RevenueBucket` (dataclass: `key: str | int`, `DoanhThu: Decimal`, `SoDon: int`);
  `GET /reports/revenue`.

`group_by` nhận đúng ba giá trị và mỗi giá trị quyết định `key` của `RevenueBucket`:

| `group_by` | `key` | Ghi chú |
| --- | --- | --- |
| `period` (mặc định) | Business Date dạng `YYYY-MM-DD` | Một dòng cho mỗi mốc trong kỳ. |
| `table` | `MaBan` (int) | Dòng `key = None` gom order mang về. |
| `payment_method` | `PhuongThucThanhToan` (str) | Giao dịch chưa có hóa đơn gom vào `"Chưa xác định"`. |

- [ ] **Step 1: Viết test**

```python
def test_a_week_runs_on_business_dates_not_calendar_days() -> None:
    """A business date starts at 06:00, so the grouping boundary follows it."""
    period = resolve_period("week", date(2026, 9, 24))

    assert period.start == date(2026, 9, 21)  # Monday
    assert period.end == date(2026, 9, 27)


def test_a_month_covers_every_business_date_in_it() -> None:
    period = resolve_period("month", date(2026, 9, 24))

    assert period.start == date(2026, 9, 1)
    assert period.end == date(2026, 9, 30)


async def test_revenue_counts_settled_invoices(client, manager_token, invoices_in_september):
    body = (await revenue(client, manager_token, granularity="month", anchor="2026-09-01")).json()

    assert Decimal(body["total"]) == invoices_in_september.total


async def test_revenue_can_be_split_by_table_and_by_payment_method(
    client, manager_token, invoices_in_september
):
    """FR-REP-01."""
    by_table = (await revenue(client, manager_token, group_by="table")).json()
    by_method = (await revenue(client, manager_token, group_by="payment_method")).json()

    assert {row["key"] for row in by_table["items"]} == set(invoices_in_september.table_ids)
    assert {row["key"] for row in by_method["items"]} == set(invoices_in_september.payment_methods)


async def test_the_split_by_table_sums_back_to_the_total(client, manager_token, invoices_in_september):
    """A breakdown that does not add up is worse than no breakdown."""
    whole = (await revenue(client, manager_token, granularity="month")).json()
    by_table = (await revenue(client, manager_token, group_by="table")).json()

    assert sum(Decimal(row["DoanhThu"]) for row in by_table["items"]) == Decimal(whole["total"])


async def test_a_transaction_awaiting_reconciliation_is_provisional_revenue(
    client, manager_token, order_awaiting_reconciliation
):
    """FR-REP-02: counted for now, but flagged."""
    body = (await revenue(client, manager_token, granularity="month")).json()

    assert Decimal(body["provisional"]) == order_awaiting_reconciliation.total
    assert Decimal(body["total"]) >= Decimal(body["provisional"])


async def test_marking_a_dispute_subtracts_it_from_revenue(
    client, manager_token, disputed_payment, invoices_in_september
):
    """FR-REP-02: a dispute is deducted retroactively."""
    body = (await revenue(client, manager_token, granularity="month")).json()

    assert Decimal(body["total"]) == invoices_in_september.total - disputed_payment.total


async def test_only_a_manager_may_read_revenue(client, cashier_token, warehouse_token):
    """Table 33."""
    assert (await revenue(client, cashier_token)).status_code == 403
    assert (await revenue(client, warehouse_token)).status_code == 403


async def test_revenue_for_an_empty_period_is_zero_not_an_error(client, manager_token):
    body = (await revenue(client, manager_token, granularity="year", anchor="1999-01-01")).json()

    assert Decimal(body["total"]) == Decimal("0")
    assert body["items"] == []
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_reports_revenue.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

Doanh thu = `SUM(HOA_DON.TongTien)` **cộng** các giao dịch `Chờ đối soát` chưa có hóa đơn, **trừ** các
giao dịch `Tranh chấp`. Trường `provisional` tách riêng phần tạm tính để giao diện dán nhãn.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_reports_revenue.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(reports): report revenue by business date, table and payment method`

---

## Task 2: Xếp hạng món và phân bố khung giờ (FR-REP-03, 07)

**Files:**
- Modify: `apps/api/src/app/modules/reports/queries.py`
- Modify: `apps/api/src/app/modules/reports/service.py`
- Modify: `apps/api/src/app/modules/reports/router.py`
- Test: `apps/api/tests/modules/test_reports_rankings.py`

**Interfaces:**
- Consumes: Task 1.
- Produces: `dish_ranking(session, period, order_by) -> list[DishRank]`
  (`DishRank`: `MaMon`, `TenMon`, `SoLuong`, `DoanhThu`);
  `hourly_distribution(session, period) -> HourDistribution`
  (`HourBucket`: `ThoiDiem: int` 0–23, `SoDon: int`, `DoanhThu: Decimal`;
  `HourDistribution`: `items: list[HourBucket]`, `by_weekday: list[WeekdayBucket]` với
  `WeekdayBucket`: `Thu: int` 2–8 theo ISO, `SoDon: int`);
  `GET /reports/dishes`, `GET /reports/hours`.

- [ ] **Step 1: Viết test**

```python
async def test_the_ranking_can_be_sorted_by_quantity_or_by_revenue(client, manager_token, orders_in_september):
    """FR-REP-03."""
    by_quantity = (await dish_ranking(client, manager_token, order_by="quantity")).json()["items"]
    by_revenue = (await dish_ranking(client, manager_token, order_by="revenue")).json()["items"]

    assert by_quantity[0]["TenMon"] == orders_in_september.top_by_quantity
    assert by_revenue[0]["TenMon"] == orders_in_september.top_by_revenue
    assert by_quantity != by_revenue  # the two orders must actually differ


async def test_cancelled_lines_are_left_out_of_the_ranking(client, manager_token, order_with_cancelled_line):
    """A cancelled line never reached the guest."""
    items = (await dish_ranking(client, manager_token)).json()["items"]

    assert all(item["TenMon"] != "Món đã hủy" for item in items)


async def test_the_ranking_covers_the_selected_period_only(client, manager_token, orders_in_two_months):
    august = (await dish_ranking(client, manager_token, month=orders_in_two_months.left_month)).json()
    september = (await dish_ranking(client, manager_token, month=orders_in_two_months.right_month)).json()

    assert {item["TenMon"] for item in august["items"]} != {
        item["TenMon"] for item in september["items"]
    }


async def test_hours_are_grouped_by_business_hour_and_by_weekday(client, manager_token, orders_in_september):
    """FR-REP-07."""
    body = (await hourly(client, manager_token)).json()

    assert {"ThoiDiem", "SoDon", "DoanhThu"} <= set(body["items"][0])
    assert {"Thu", "SoDon"} <= set(body["by_weekday"][0])


async def test_a_late_night_order_belongs_to_the_previous_business_date(
    client, manager_token, order_at_0130
):
    """Business date runs 06:00 to 06:00, so 01:30 belongs to the day before."""
    body = (await hourly(client, manager_token)).json()

    assert order_at_0130.business_date == order_at_0130.placed_at.date() - timedelta(days=1)
    assert any(row["ThoiDiem"] == 1 for row in body["items"])
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_reports_rankings.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

Xếp hạng gom từ `CHI_TIET_ORDER` nối `ORDER` (loại order `Đã hủy`, `Tự động đóng`) và loại dòng
`Đã hủy`. Khung giờ gom theo **giờ trong Business Date**: `HOUR(ThoiDiem)`, nhưng order đặt sau nửa
đêm thuộc Business Date hôm trước — dùng `business_date_of()` khi gán nhãn.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_reports_rankings.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(reports): rank dishes and chart the hourly distribution`

---

## Task 3: Giá vốn, biên lợi nhuận gộp và nhãn tạm tính (FR-REP-04, 05, 06)

**Files:**
- Modify: `apps/api/src/app/modules/reports/queries.py`
- Modify: `apps/api/src/app/modules/reports/service.py`
- Modify: `apps/api/src/app/modules/reports/router.py`
- Test: `apps/api/tests/modules/test_reports_margin.py`

**Interfaces:**
- Consumes: Task 1, `MonthlyAverageCost`, `RecipeItem`, `StockIssueLine`.
- Produces: `cost_of_goods(session, month) -> CostBreakdown`
  (`CostBreakdown`: `NguyenLieu: Decimal`, `HaoHut: Decimal`, `TongGiaVon: Decimal`,
  `TamTinh: bool`, `SoDongChuaTinhGiaVon: int`);
  `gross_margin(session, month) -> Margin`
  (`Margin`: `DoanhThu`, `GiaVon`, `BienLoiNhuanGop` — cả ba đều `Decimal`);
  `dish_ingredient_cost(session, month) -> list[DishCost]`
  (`DishCost`: `MaMon`, `TenMon`, `GiaVon` — **không** có `HaoHut`, **không** có `BienLoiNhuan`);
  `GET /reports/margin`, `GET /reports/costs`, `GET /reports/costs/dishes`.

- [ ] **Step 1: Viết test**

```python
async def test_the_margin_is_revenue_minus_consumed_ingredients(client, manager_token, september_data):
    """FR-REP-04."""
    body = (await margin(client, manager_token, month=str(september_data.month))).json()

    assert Decimal(body["DoanhThu"]) == september_data.revenue
    assert Decimal(body["GiaVon"]) == september_data.cogs
    assert Decimal(body["BienLoiNhuanGop"]) == september_data.margin
    # The definition, not just the three numbers: margin is what is left of revenue.
    assert september_data.margin == september_data.revenue - september_data.cogs


async def test_the_cost_uses_the_recipe_version_in_force_at_order_time(
    client, manager_token, order_before_recipe_change, order_after_recipe_change
):
    """FR-REP-05a: the recipe snapshot on the line decides, not the current recipe."""
    body = (await costs(client, manager_token, month="2026-09")).json()

    # Both orders use the same ingredient, but each is costed from the recipe version
    # pinned on its own line — so the expected total is the sum of the two snapshots.
    assert Decimal(body["NguyenLieu"]) == (
        order_before_recipe_change.expected_cost + order_after_recipe_change.expected_cost
    )


async def test_waste_is_part_of_the_cost(client, manager_token, september_data, write_off_in_september):
    """FR-REP-05b."""
    body = (await costs(client, manager_token, month=str(september_data.month))).json()

    assert Decimal(body["HaoHut"]) == write_off_in_september.value
    assert Decimal(body["TongGiaVon"]) == Decimal(body["NguyenLieu"]) + Decimal(body["HaoHut"])


async def test_a_month_with_uncosted_waste_rows_is_flagged_as_provisional(
    client, manager_token, write_off_before_month_close
):
    """FR-REP-05b: the manager must know the figure is not final."""
    body = (await costs(client, manager_token, month="2026-09")).json()

    assert body["TamTinh"] is True
    assert body["SoDongChuaTinhGiaVon"] == 1


async def test_the_label_clears_once_the_backfill_has_run(
    client, manager_token, write_off_after_backfill
):
    body = (await costs(client, manager_token, month="2026-09")).json()

    assert body["TamTinh"] is False
    assert body["SoDongChuaTinhGiaVon"] == 0


async def test_the_per_dish_cost_excludes_waste(client, manager_token, september_data):
    """FR-REP-06: reference only, waste is not attributed to a dish."""
    body = (await dish_costs(client, manager_token, month=str(september_data.month))).json()

    assert body["items"]
    assert all("HaoHut" not in item for item in body["items"])


async def test_the_per_dish_cost_is_not_turned_into_a_margin(client, manager_token, september_data):
    """FR-REP-06: no per-dish profit figure, by design."""
    body = (await dish_costs(client, manager_token, month=str(september_data.month))).json()

    assert all("BienLoiNhuan" not in item for item in body["items"])


async def test_the_per_dish_costs_add_up_to_the_ingredient_cost(client, manager_token, september_data):
    """Otherwise the breakdown contradicts the total on the same screen."""
    dishes = (await dish_costs(client, manager_token, month=str(september_data.month))).json()
    costs = (await costs(client, manager_token, month=str(september_data.month))).json()

    assert sum(Decimal(item["GiaVon"]) for item in dishes["items"]) == Decimal(costs["NguyenLieu"])
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_reports_margin.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

Giá vốn nguyên liệu tiêu hao = Σ (`CHI_TIET_ORDER.SoLuong` × `CHI_TIET_CONG_THUC.DinhLuong`) ×
`GIA_BINH_QUAN_THANG.DonGiaBinhQuan`, dùng **`MaCongThuc` ghi trên dòng order** (đã chốt ở Phase 4),
không tra lại công thức hiện hành. Cộng thêm `CHI_TIET_PHIEU_XUAT.GiaVonUocTinh` của tháng.
Đếm số dòng còn `GiaVonUocTinh = 0` để bật cờ `TamTinh`.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_reports_margin.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(reports): compute cost of goods, gross margin and provisional labels`

---

## Task 4: So sánh hai khoảng và báo cáo order bị hủy (FR-REP-08, 10)

**Files:**
- Modify: `apps/api/src/app/modules/reports/queries.py`
- Modify: `apps/api/src/app/modules/reports/service.py`
- Modify: `apps/api/src/app/modules/reports/router.py`
- Test: `apps/api/tests/modules/test_reports_comparison.py`

**Interfaces:**
- Consumes: Task 1–3.
- Produces: `compare_periods(session, left, right) -> Comparison`
  (`Comparison`: `left`, `right` (mỗi cái là `RevenueSummary` với `DoanhThu`, `SoDon`),
  `change_percent: Decimal | None`);
  `cancelled_orders(session, period) -> CancelledReport`
  (`CancelledReport`: `SoLuong: int`, `TongGiaTri: Decimal`,
  `items: list[CancelledOrder]` với `MaOrder`, `MaOrderHienThi`, `TongTien`, `LyDoHuy`);
  `GET /reports/comparison`, `GET /reports/cancelled-orders`.

- [ ] **Step 1: Viết test**

```python
async def test_the_comparison_returns_the_percentage_change(client, manager_token, two_months):
    """FR-REP-08."""
    body = (
        await compare(client, manager_token, left=two_months.left_month, right=two_months.right_month)
    ).json()

    assert Decimal(body["left"]["DoanhThu"]) == two_months.left_revenue
    assert Decimal(body["right"]["DoanhThu"]) == two_months.right_revenue
    expected = (two_months.right_revenue - two_months.left_revenue) / two_months.left_revenue * 100
    assert Decimal(body["change_percent"]).quantize(Decimal("0.01")) == expected.quantize(Decimal("0.01"))


async def test_comparing_against_an_empty_period_does_not_divide_by_zero(client, manager_token):
    body = (await compare(client, manager_token, left="1999-01", right="2026-09")).json()

    assert body["change_percent"] is None


async def test_the_cancelled_report_lists_totals_counts_and_reasons(client, manager_token, cancelled_orders):
    """FR-REP-10."""
    body = (await cancelled(client, manager_token, month="2026-09")).json()

    assert body["SoLuong"] == len(cancelled_orders)
    assert Decimal(body["TongGiaTri"]) == sum(order.total for order in cancelled_orders)
    assert {row["LyDoHuy"] for row in body["items"]} == {order.reason for order in cancelled_orders}
    assert all(order.reason for order in cancelled_orders)  # the fixture sets them


async def test_the_cancelled_value_stays_out_of_revenue(
    client, manager_token, cancelled_orders, invoices_in_september
):
    """FR-REP-10: reported separately, never mixed into revenue."""
    revenue_body = (await revenue(client, manager_token, month="2026-09")).json()
    cancelled_body = (await cancelled(client, manager_token, month="2026-09")).json()

    assert Decimal(cancelled_body["TongGiaTri"]) > 0
    # Revenue only counts settled invoices; a cancelled order never produced one.
    assert Decimal(revenue_body["total"]) == invoices_in_september.total
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_reports_comparison.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

`change_percent` trả `None` khi mẫu số bằng 0 (không trả `inf` hay lỗi). Order bị hủy lấy
`TrangThai = 'Đã hủy'` **và** `'Tự động đóng'` — cả hai đều không phát sinh hóa đơn.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_reports_comparison.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(reports): compare periods and report cancelled orders`

---

## Task 5: Giao diện báo cáo

**Files:**
- Create: `apps/web/src/features/reports/revenue-chart.tsx`
- Create: `apps/web/src/features/reports/report-table.tsx`
- Create: `apps/web/src/features/reports/revenue-chart.test.tsx`
- Create: `apps/web/src/features/reports/test-helpers.ts` (`stubFetch`, dữ liệu mẫu dùng chung)
- Modify: `apps/web/src/app/(app)/reports/page.tsx`

**Interfaces:**
- Consumes: endpoint Task 1–4.
- Produces: `RevenueChart`, `ReportTable`; `stubFetch(body)` trong `test-helpers.ts`.

- [ ] **Step 1: Viết test**

```tsx
// FR-REP-09
it("renders both a table and a chart", async () => {
  stubFetch(revenueResponse);

  render(<RevenueChart />);

  expect(await screen.findByRole("table")).toBeInTheDocument();
  expect(screen.getByRole("img", { name: /biểu đồ doanh thu/i })).toBeInTheDocument();
});

// FR-REP-02 and FR-REP-05b: a provisional figure must be labelled in words, not only coloured.
it("labels provisional figures so the manager knows they are not final", async () => {
  stubFetch({ ...revenueResponse, provisional: "500000" });

  render(<RevenueChart />);

  expect(await screen.findByText(/tạm tính/)).toBeInTheDocument();
});

it("shows the empty state with a hint when the period has no data", async () => {
  stubFetch({ total: "0", items: [], provisional: "0" });

  render(<RevenueChart />);

  expect(await screen.findByText(/Chưa có dữ liệu trong kỳ/)).toBeInTheDocument();
});
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/web && pnpm test`
Expected: FAIL — module chưa tồn tại

- [ ] **Step 3: Cài đặt**

Bộ lọc theo Business Date / tuần / tháng (FR-REP-01). Biểu đồ dùng SVG thuần (không thêm thư viện
ngoài — mỗi phụ thuộc mới là một chuỗi cung ứng mới). Mọi số liệu tạm tính phải có nhãn nhìn thấy
được, không chỉ khác màu.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/web && pnpm test`
Expected: PASS

- [ ] **Step 5: Kiểm tra hiệu năng trên dữ liệu 12 tháng (NFR-01, NFR-03)**

Cổng này **phải có script**, không phải một lệnh gõ tay — nếu không nó lặng lẽ thành "unfinished".
Trước khi chạy bước này, tạo `scripts/bench_reports.py`:

**Files:** Create `scripts/bench_reports.py`

```python
"""Time every reporting endpoint against a seeded database (NFR-01, NFR-03)."""

import argparse
import asyncio
import time
from datetime import date

from app.core.database import get_session_factory
from app.modules.reports import periods, queries

BUDGET_SECONDS = 2.0

# Named entries, so a failure says which endpoint is slow instead of "a query".
BENCHMARKS = {
    "revenue": lambda s, p: queries.revenue_by_period(s, p),
    "dishes": lambda s, p: queries.dish_ranking(s, p, order_by="revenue"),
    "hours": lambda s, p: queries.hourly_distribution(s, p),
    "costs": lambda s, p: queries.cost_of_goods(s, int(p.start.strftime("%Y%m"))),
}


async def main(month: str) -> int:
    period = periods.resolve_period("month", date.fromisoformat(f"{month}-01"))
    over_budget = 0
    async with get_session_factory()() as session:
        for name, run in BENCHMARKS.items():
            started = time.perf_counter()
            await run(session, period)
            elapsed = time.perf_counter() - started
            over_budget += elapsed > BUDGET_SECONDS
            print(f"{name:10s} {elapsed:6.3f}s {'OVER' if elapsed > BUDGET_SECONDS else 'ok'}")
    return over_budget


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True, help="YYYY-MM")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.month)))
```

Chạy bằng **đường dẫn file**, giống `make seed` — `python -m scripts.bench_reports` không resolve vì
`scripts/` không nằm trên `sys.path` của `apps/api`:

Run: `cd apps/api && ./.venv/bin/python ../../scripts/bench_reports.py --month 2026-09`
Expected: bốn dòng, tất cả `ok` (dưới 2 giây) trên bộ dữ liệu 12 tháng của Phase 7. Script thoát khác
0 nếu có dòng `OVER` — nếu một dòng `OVER`, chạy `EXPLAIN` cho truy vấn đó và đối chiếu index §3.2.3
trước khi xem xét thêm index mới.

- [ ] **Step 6: Chạy cổng kiểm tra đầy đủ**

Run: `UV_CACHE_DIR=/tmp/uv-cache make gate`
Expected: xanh. Commit: `feat(web): build the reporting screens with charts`

- [ ] **Step 7: Kiểm thử thủ công trên ba trình duyệt (NFR-17)**

Mở màn hình báo cáo trên Chrome, Edge và Safari, ở cỡ máy tính (≥ 1280px) và tablet (~ 768–1024px).
Kiểm bốn điểm: bảng cuộn ngang không vỡ layout, biểu đồ SVG co giãn đúng, nhãn "tạm tính" nhìn thấy
được (không chỉ khác màu), và bộ lọc kỳ giữ nguyên khi tải lại. Ghi kết quả từng trình duyệt vào PR
description — đây là bằng chứng cho NFR-17, không phải bước tuỳ chọn.

---

## Kiểm chứng

| Cổng | Lệnh | Kỳ vọng |
| --- | --- | --- |
| Doanh thu | `pytest tests/modules/test_reports_revenue.py` | xanh |
| Xếp hạng + khung giờ | `pytest tests/modules/test_reports_rankings.py` | xanh |
| Giá vốn + biên lợi nhuận | `pytest tests/modules/test_reports_margin.py` | xanh |
| So sánh + order hủy | `pytest tests/modules/test_reports_comparison.py` | xanh |
| Giao diện | `cd apps/web && pnpm test` | xanh |
| Hiệu năng | `cd apps/api && ./.venv/bin/python ../../scripts/bench_reports.py --month 2026-09` | mọi endpoint < 2s |
| Ba trình duyệt (NFR-17) | thủ công, ghi vào PR | 4 điểm kiểm đạt |
| Toàn bộ | `make gate` | xanh |

## Rủi ro

- **`BusinessDate` vs `ThoiDiem`** là nguồn sai số lớn nhất. Mọi phép gom nhóm dùng `BusinessDate`;
  test `test_a_late_night_order_belongs_to_the_previous_business_date` là chốt chặn.
- **Doanh thu tạm tính**: nếu quên nhãn, người quản lý đọc số chưa chốt như số cuối cùng. Nhãn là
  yêu cầu của FR-REP-02/05b, không phải trang trí.
- **Biên lợi nhuận chỉ ở mức tổng** (FR-REP-04) — cố ý không tính theo món vì giá vốn dùng bình quân
  tháng, không truy theo lô (§3.2.1 a27). Đừng "cải tiến" thành theo món.
- **Hiệu năng với 20.000 order/năm** (NFR-03): các truy vấn phải dùng index `ORDER(BusinessDate, MaBan)`
  và `CHI_TIET_ORDER(MaMon, MaOrder)` của Phase 0. Kiểm tra bằng `scripts/bench_reports.py`; chỉ
  `EXPLAIN` khi có dòng `OVER`.
- **Fixture trả hằng số cứng**: mọi con số trong test phải đến từ fixture (mục "Hợp đồng dữ liệu
  test"). Nếu thấy `Decimal("10000000")` xuất hiện lại trong một test, đó là lỗi — nó sẽ vỡ ngay khi
  ai đó sửa fixture và không ai biết vì sao.
- **`scripts/bench_reports.py` phải tồn tại trước Step 5.** Nếu bỏ qua, cổng NFR-01/NFR-03 chuyển
  thành "unfinished" một cách im lặng — đúng loại thất bại mà §4 của quy tắc chung cấm coi là xanh.
