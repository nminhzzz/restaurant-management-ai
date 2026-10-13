# Stabilize API Gate Implementation Plan

> **Trạng thái (2026-10-13):** đã triển khai. Đánh dấu theo bằng chứng trong mã và test hiện có (`make test-api`/`make test-web` xanh ngày 2026-10-13); bước 'Expected: FAIL' (red) không lưu bằng chứng riêng nên được đánh dấu theo kết quả cuối của task. Bước chưa có bằng chứng (chạy MySQL thật, `make gate` đầy đủ) để trống.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Làm test API độc lập với cấu hình cá nhân và sửa việc chốt giá vốn bỏ sót phiếu xuất trong kỳ.

**Architecture:** Fixture test đặt rõ payment gateway mặc định và credential rỗng để file .env không quyết định test. Backfill chi phí lọc theo thời điểm nghiệp vụ PHIEU_XUAT_KHO.NgayXuat thay vì timestamp tạo bản ghi NgayTao.

**Tech Stack:** Python 3.12, pytest, FastAPI, SQLAlchemy 2 async, SQLite test DB, uv.

**Spec:** ../specs/2026-10-11-align-code-with-report-design.md, mục 4.

## Global Constraints

- Không in hoặc ghi giá trị secret trong test output.
- Dùng app.shared.business_date cho ngày nghiệp vụ.
- Không sửa các file chưa commit của workspace chính.
- Baseline sau merge hiện có 7 pytest failures đã ghi nhận: một lỗi chốt giá vốn và sáu lỗi adapter/webhook thanh toán; xác minh lại tên lỗi và nguyên nhân trước khi sửa, không đọc/in giá trị credential.

---

### Task 1: Làm test thanh toán hermetic

**Files:**
- Modify: apps/api/tests/conftest.py
- Modify: apps/api/tests/modules/test_sales_sepay_adapter.py
- Test: apps/api/tests/modules/test_sales_payments.py
- Test: apps/api/tests/modules/test_sales_sepay_webhook.py

**Interfaces:**
- Fixture mặc định đặt PAYMENT_GATEWAY=simulator và các credential SePay thành chuỗi rỗng.
- Fixture sepay_env đặt gateway SePay và credential cụ thể cho từng test.
- get_settings.cache_clear() chạy trước và sau test như hiện tại.

- [x] Step 1: Trong test_selecting_sepay_without_credentials_fails_at_startup, đặt PAYMENT_GATEWAY=sepay và đặt SEPAY_BANK_ACCOUNT, SEPAY_BANK_CODE, SEPAY_WEBHOOK_API_KEY thành rỗng; giữ assertion RuntimeError khớp SEPAY.
- [x] Step 1a: Ghi nhận từng failure đã xác minh: `test_selecting_sepay_without_credentials_fails_at_startup`, `test_webhook_settles`, `test_webhook_idempotent`, `test_webhook_bad_sig`, `test_the_sepay_hook_is_absent_under_the_simulator`, `test_the_simulator_hook_refuses_a_signed_body_without_an_amount`; không đưa nội dung `.env` vào log.
- [x] Step 2: Chạy test thanh toán để xác nhận ảnh hưởng config.
  Run: cd apps/api && uv run pytest tests/modules/test_sales_sepay_adapter.py::test_selecting_sepay_without_credentials_fails_at_startup tests/modules/test_sales_payments.py tests/modules/test_sales_sepay_webhook.py -q
  Expected: trước fixture mới có thể fail vì .env cung cấp credential/gateway; lỗi chỉ là cài đặt test.
- [x] Step 3: Thêm autouse fixture dùng monkeypatch.setenv để mặc định simulator và override credential bằng chuỗi rỗng; fixture sepay_env vẫn phải override được giá trị đó.
- [x] Step 4: Chạy lại cùng nhóm test; Expected: PASS cả simulator và SePay tests.

### Task 2: Backfill chi phí theo ngày nghiệp vụ xuất

**Files:**
- Modify: apps/api/src/app/modules/inventory/costing.py
- Test: apps/api/tests/modules/test_inventory_costing.py
- Reference: apps/api/src/app/modules/inventory/models.py, StockIssue.issue_date và created_at

**Interfaces:**
- backfill_issue_costs(session, month) giữ tham số tháng YYYYMM.
- Kỳ xuất dùng ngày nghiệp vụ `StockIssue.issue_date`; dòng cũ có `issue_date IS NULL` dùng `StockIssue.created_at` làm fallback.

- [x] Step 1: Thêm regression test với issue_date trong tháng được chốt, created_at ngoài tháng; sau API close, expected estimated_cost == 3000 và có audit CLOSE_COSTING_MONTH.
- [x] Step 2: Chạy cd apps/api && uv run pytest tests/modules/test_inventory_costing.py::test_closing_a_month_prices_its_write_offs_and_is_audited -q; Expected: FAIL vì query hiện lọc created_at.
- [x] Step 3: Trong backfill_issue_costs, dùng `coalesce(StockIssue.issue_date, StockIssue.created_at)` với khoảng nửa mở `[start, end)` và giữ lọc `estimated_cost == 0`.
- [x] Step 4: Thêm regression test cho bản ghi di trú cũ có `issue_date IS NULL`, bảo đảm fallback `created_at` vẫn được chốt đúng tháng.
- [x] Step 5: Chạy cd apps/api && uv run pytest tests/modules/test_inventory_costing.py -q; Expected: PASS.

### Task 3: Baseline API sạch

**Files:**
- No production files.

- [x] Step 1: Chạy cd apps/api && uv run pytest -q.
- [x] Step 2: Nếu còn failure ngoài các test ở Task 1–2, ghi test name, nguyên nhân đã xác minh và bổ sung task sửa bằng TDD trước khi qua plan kế.
- [x] Step 3: Expected: 0 failed. Ghi số pass/skip làm baseline cho phần tiếp theo.
