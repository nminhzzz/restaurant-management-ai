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
- Giao diện báo cáo kiểm thử trên Chrome, Edge, Safari ở máy tính và tablet (NFR-17).
- `make gate` xanh trước khi kết thúc mỗi task.

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
  `GET /reports/revenue`.

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

    assert body["total"] == Decimal("1500000")


async def test_revenue_can_be_split_by_table_and_by_payment_method(
    client, manager_token, invoices_in_september
):
    """FR-REP-01."""
    by_table = (await revenue(client, manager_token, group_by="table")).json()
    by_method = (await revenue(client, manager_token, group_by="payment_method")).json()

    assert {row["MaBan"] for row in by_table["items"]} == {1, 2}
    assert {row["PhuongThucThanhToan"] for row in by_method["items"]} == {"Tiền mặt", "QR"}


async def test_a_transaction_awaiting_reconciliation_is_provisional_revenue(
    client, manager_token, order_awaiting_reconciliation
):
    """FR-REP-02: counted for now, but flagged."""
    body = (await revenue(client, manager_token, granularity="month")).json()

    assert body["total"] > 0
    assert body["provisional"] == Decimal(str(order_awaiting_reconciliation.total))


async def test_marking_a_dispute_subtracts_it_from_revenue(
    client, manager_token, disputed_payment
):
    """FR-REP-02: a dispute is deducted retroactively."""
    body = (await revenue(client, manager_token, granularity="month")).json()

    assert body["total"] == Decimal("0")


async def test_only_a_manager_may_read_revenue(client, cashier_token, warehouse_token):
    """Table 33."""
    assert (await revenue(client, cashier_token)).status_code == 403
    assert (await revenue(client, warehouse_token)).status_code == 403


async def test_revenue_for_an_empty_period_is_zero_not_an_error(client, manager_token):
    body = (await revenue(client, manager_token, granularity="year", anchor="1999-01-01")).json()

    assert body["total"] == Decimal("0")
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
- Produces: `dish_ranking(session, period, order_by) -> list[DishRank]`;
  `hourly_distribution(session, period) -> list[HourBucket]`;
  `GET /reports/dishes`, `GET /reports/hours`.

- [ ] **Step 1: Viết test**

```python
async def test_the_ranking_can_be_sorted_by_quantity_or_by_revenue(client, manager_token, orders_in_september):
    """FR-REP-03."""
    by_quantity = (await dish_ranking(client, manager_token, order_by="quantity")).json()["items"]
    by_revenue = (await dish_ranking(client, manager_token, order_by="revenue")).json()["items"]

    assert by_quantity[0]["TenMon"] == "Phở bò"
    assert by_revenue[0]["TenMon"] == "Bò nướng"


async def test_cancelled_lines_are_left_out_of_the_ranking(client, manager_token, order_with_cancelled_line):
    """A cancelled line never reached the guest."""
    items = (await dish_ranking(client, manager_token)).json()["items"]

    assert all(item["TenMon"] != "Món đã hủy" for item in items)


async def test_the_ranking_covers_the_selected_period_only(client, manager_token, orders_in_two_months):
    august = (await dish_ranking(client, manager_token, month="2026-08")).json()["items"]
    september = (await dish_ranking(client, manager_token, month="2026-09")).json()["items"]

    assert {item["TenMon"] for item in august} != {item["TenMon"] for item in september}


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
- Produces: `cost_of_goods(session, month) -> CostBreakdown`; `gross_margin(session, month) -> Margin`;
  `dish_ingredient_cost(session, month) -> list[DishCost]`;
  `GET /reports/margin`, `GET /reports/costs`, `GET /reports/costs/dishes`.

- [ ] **Step 1: Viết test**

```python
async def test_the_margin_is_revenue_minus_consumed_ingredients(client, manager_token, september_data):
    """FR-REP-04."""
    body = (await margin(client, manager_token, month="2026-09")).json()

    assert body["DoanhThu"] == Decimal("10000000")
    assert body["GiaVon"] == Decimal("4000000")
    assert body["BienLoiNhuanGop"] == Decimal("6000000")


async def test_the_cost_uses_the_recipe_version_in_force_at_order_time(
    client, manager_token, order_before_recipe_change, order_after_recipe_change
):
    """FR-REP-05a: the recipe snapshot on the line decides, not the current recipe."""
    body = (await costs(client, manager_token, month="2026-09")).json()

    assert body["items"][0]["GiaVon"] == expected_from_snapshots


async def test_waste_is_part_of_the_cost(client, manager_token, september_data, write_off_in_september):
    """FR-REP-05b."""
    body = (await costs(client, manager_token, month="2026-09")).json()

    assert body["HaoHut"] == Decimal(str(write_off_in_september.value))


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


async def test_the_per_dish_cost_excludes_waste(client, manager_token, september_data):
    """FR-REP-06: reference only, waste is not attributed to a dish."""
    body = (await dish_costs(client, manager_token, month="2026-09")).json()

    assert all("HaoHut" not in item for item in body["items"])


async def test_the_per_dish_cost_is_not_turned_into_a_margin(client, manager_token, september_data):
    """FR-REP-06: no per-dish profit figure, by design."""
    body = (await dish_costs(client, manager_token, month="2026-09")).json()

    assert all("BienLoiNhuan" not in item for item in body["items"])
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
- Produces: `compare_periods(session, left, right) -> Comparison`;
  `cancelled_orders(session, period) -> CancelledReport`;
  `GET /reports/comparison`, `GET /reports/cancelled-orders`.

- [ ] **Step 1: Viết test**

```python
async def test_the_comparison_returns_the_percentage_change(client, manager_token, two_months):
    """FR-REP-08."""
    body = (await compare(client, manager_token, left="2026-08", right="2026-09")).json()

    assert body["left"]["DoanhThu"] == Decimal("8000000")
    assert body["right"]["DoanhThu"] == Decimal("10000000")
    assert body["change_percent"] == Decimal("25")


async def test_comparing_against_an_empty_period_does_not_divide_by_zero(client, manager_token):
    body = (await compare(client, manager_token, left="1999-01", right="2026-09")).json()

    assert body["change_percent"] is None


async def test_the_cancelled_report_lists_totals_counts_and_reasons(client, manager_token, cancelled_orders):
    """FR-REP-10."""
    body = (await cancelled(client, manager_token, month="2026-09")).json()

    assert body["SoLuong"] == 2
    assert body["TongGiaTri"] == sum(order.total for order in cancelled_orders)
    assert {row["LyDoHuy"] for row in body["items"]} == {"khách bỏ về", "hết nguyên liệu"}


async def test_the_cancelled_value_stays_out_of_revenue(client, manager_token, cancelled_orders):
    """FR-REP-10: reported separately, never mixed into revenue."""
    revenue_body = (await revenue(client, manager_token, month="2026-09")).json()
    cancelled_body = (await cancelled(client, manager_token, month="2026-09")).json()

    assert cancelled_body["TongGiaTri"] > 0
    assert revenue_body["total"] == revenue_without_cancellations
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
- Modify: `apps/web/src/app/(app)/reports/page.tsx`

**Interfaces:**
- Consumes: endpoint Task 1–4.
- Produces: `RevenueChart`, `ReportTable`.

- [ ] **Step 1: Viết test**

```tsx
it("renders both a table and a chart", async () => {
  """FR-REP-09."""
  stubFetch(revenueResponse);

  render(<RevenueChart />);

  expect(await screen.findByRole("table")).toBeInTheDocument();
  expect(screen.getByRole("img", { name: /biểu đồ doanh thu/i })).toBeInTheDocument();
});

it("labels provisional figures so the manager knows they are not final", async () => {
  """FR-REP-02 and FR-REP-05b."""
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

- [ ] **Step 5: Kiểm tra hiệu năng trên dữ liệu thật**

Run: `cd apps/api && ./.venv/bin/python -m scripts.bench_reports --month 2026-09`
Expected: mỗi endpoint báo cáo dưới 2 giây trên bộ dữ liệu 12 tháng (NFR-01, NFR-03). Nếu vượt, chạy
`EXPLAIN` và đối chiếu với index ở §3.2.3 trước khi xem xét thêm index mới.

- [ ] **Step 6: Chạy cổng kiểm tra đầy đủ**

Run: `UV_CACHE_DIR=/tmp/uv-cache make gate`
Expected: xanh. Commit: `feat(web): build the reporting screens with charts`

---

## Kiểm chứng

| Cổng | Lệnh | Kỳ vọng |
| --- | --- | --- |
| Doanh thu | `pytest tests/modules/test_reports_revenue.py` | xanh |
| Xếp hạng + khung giờ | `pytest tests/modules/test_reports_rankings.py` | xanh |
| Giá vốn + biên lợi nhuận | `pytest tests/modules/test_reports_margin.py` | xanh |
| So sánh + order hủy | `pytest tests/modules/test_reports_comparison.py` | xanh |
| Giao diện | `cd apps/web && pnpm test` | xanh |
| Toàn bộ | `make gate` | xanh |

## Rủi ro

- **`BusinessDate` vs `ThoiDiem`** là nguồn sai số lớn nhất. Mọi phép gom nhóm dùng `BusinessDate`;
  test `test_a_late_night_order_belongs_to_the_previous_business_date` là chốt chặn.
- **Doanh thu tạm tính**: nếu quên nhãn, người quản lý đọc số chưa chốt như số cuối cùng. Nhãn là
  yêu cầu của FR-REP-02/05b, không phải trang trí.
- **Biên lợi nhuận chỉ ở mức tổng** (FR-REP-04) — cố ý không tính theo món vì giá vốn dùng bình quân
  tháng, không truy theo lô (§3.2.1 a27). Đừng "cải tiến" thành theo món.
- **Hiệu năng với 20.000 order/năm** (NFR-03): các truy vấn phải dùng index `ORDER(BusinessDate, MaBan)`
  và `CHI_TIET_ORDER(MaMon, MaOrder)` của Phase 0. Kiểm tra bằng `EXPLAIN` nếu thấy chậm.
