# Configurable Business Date Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Khớp FR-SET-04 với cấu hình Business Date có hiệu lực, cảnh báo hạn dùng, thời gian giữ chỗ và quota AI.

**Architecture:** Mở rộng singleton CAU_HINH_HE_THONG bằng migration có giá trị mặc định tương thích. Settings service trả giờ bắt đầu hiệu lực; app.shared.business_date giữ toàn bộ phép tính ngày thuần. Cấu hình được validate, audit và hiển thị ở màn hình Cài đặt.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 async, Alembic, MySQL 8.4, Next.js 16, React 19, TypeScript, pytest, Vitest.

**Spec:** ../specs/2026-10-11-align-code-with-report-design.md, mục 1.

## Global Constraints

- MySQL 8.4; tên cột theo §4.2.2, không suy kiểu vật lý từ §3.2.1.
- Migration có upgrade/downgrade; không sửa migration đã chạy.
- Tính toán Business Date tập trung ở app.shared.business_date.
- Thay đổi cấu hình chỉ Manager, validate ở backend và audit trước/sau.
- Giờ mới có hiệu lực từ Business Date kế tiếp; không đổi ngày nghiệp vụ đang chạy.

---

### Task 1: Thêm cột cấu hình, schema và migration

**Files:**
- Modify: apps/api/src/app/modules/settings/models.py
- Modify: apps/api/src/app/modules/settings/schemas.py
- Modify: apps/api/src/app/modules/settings/service.py
- Create: a new Alembic migration `effective_system_config.py` whose generated revision points to current head `b7c9d3e1f420`
- Test: apps/api/tests/schema/test_settings_models.py
- Test: apps/api/tests/schema/test_schema_contract.py
- Test: apps/api/tests/modules/test_settings_config.py

**Interfaces:**
- SystemConfig thêm GioBatDauBusinessDateMoi, NgayHieuLucGioMoi, SoNgayCanhBaoHetHan, SoCauHoiAIMoiNgay, ThoiGianGiuChoPhut.
- ConfigOut trả các trường; ConfigUpdate nhận giờ mới và tham số số nguyên dương.
- Giá trị mặc định: 06:00, giờ chờ/ngày hiệu lực NULL, cảnh báo 3 ngày, quota 50, giữ 5 phút.

- [ ] Step 1: Cập nhật EXPECTED trong test_settings_models.py và EXPECTED_TABLES trong test_schema_contract.py; thêm test seed mặc định.
- [ ] Step 2: Chạy cd apps/api && uv run pytest tests/schema/test_settings_models.py tests/schema/test_schema_contract.py tests/modules/test_settings_config.py -q; Expected: FAIL vì metadata/API chưa có cột.
- [ ] Step 3: Thêm model/schema/validation/service và migration mới nối revision hiện hành `b7c9d3e1f420`; migration giữ dữ liệu cũ và đặt mặc định đã nêu. Audit `UPDATE_CONFIG` lưu đủ snapshot before/after của các giá trị cấu hình đã đổi.
- [ ] Step 4: Chạy lại nhóm test trên; Expected: PASS.

### Task 2: Tính Business Date theo chính sách có hiệu lực

**Files:**
- Modify: apps/api/src/app/shared/business_date.py
- Modify: apps/api/src/app/modules/settings/service.py
- Modify: apps/api/src/app/modules/catalog/router.py
- Modify: apps/api/src/app/modules/sales/orders.py
- Modify: apps/api/src/app/modules/sales/payments.py
- Modify: apps/api/src/app/modules/inventory/stock.py
- Modify: apps/api/src/app/modules/inventory/service.py
- Modify: apps/api/src/app/modules/reports/service.py
- Modify: apps/api/src/app/modules/ai/pipeline/generator.py
- Test: apps/api/tests/core/test_business_date.py and affected module tests

**Interfaces:**
- business_date.business_date_of(moment, start_time=...) accepts datetime.time, including minute precision; default remains 06:00 for pure/default calls.
- settings.service.effective_business_day_start(session, moment) returns the configured time effective at that moment.
- Each async operation resolves one policy and passes it to the shared calculation helper.
- Replacing a pending time recalculates the next effective Business Date from the currently active policy.

**Decision gate before implementation:** FR-SET-04 and bảng 17 say the new time applies from the next Business Date and does not affect the current one, but do not specify the transition instant when the new time is earlier/later than the active time. Do not implement a guessed boundary. Before Task 2, agree whether activation occurs at the current schedule's next boundary or at the new time on `NgayHieuLucGioMoi`; encode the selected rule in before/at/after tests and keep it in the report/AGENTS guidance.

- [ ] Step 1: Add tests for default 06:00, minute precision (08:30), immediately before/at/after effective instant, moving the start earlier and later, replacing a pending change, and keeping one resolved policy within a transaction.
- [ ] Step 2: Run cd apps/api && uv run pytest tests/core/test_business_date.py tests/modules/test_settings_config.py -q; Expected: FAIL on minute precision and missing resolver behavior.
- [ ] Step 3: Implement resolver in settings.service; update every Business Date caller found by `rg "business_date\.(now|business_date_of)" apps/api/src/app` (including catalog price versioning, order/payment, inventory, reports and AI). Keep one resolved policy for the whole transaction; background work must receive a policy snapshot instead of silently reverting to 06:00.
- [ ] Step 4: Run cd apps/api && uv run pytest tests/core/test_business_date.py tests/modules/test_settings_config.py tests/modules/test_catalog_dish_prices.py tests/modules/test_sales_orders.py tests/modules/test_inventory_stock_list.py tests/modules/test_reports_revenue.py tests/modules/test_ai_generator.py -q; Expected: PASS.

### Task 3: Update configuration UI

**Files:**
- Modify: apps/web/src/features/settings/config-panel.tsx
- Test: apps/web/src/features/settings/config-panel.test.tsx

**Interfaces:**
- UI displays current hour and any pending hour/effective date, expiry warning days, AI quota and hold TTL.
- Save sends GioBatDauBusinessDateMoi, never direct writes to the currently active value.
- The UI makes the pending effective Business Date visible and explains that an existing hold keeps its recorded expiration when hold TTL changes.

- [ ] Step 1: Add component tests for rendering values, validation of positive integers and submitted payload.
- [ ] Step 2: Run cd apps/web && pnpm test -- config-panel.test.tsx; Expected: FAIL because current UI has no fields/payload.
- [ ] Step 3: Add form state, validation and pending-effective-date copy in Vietnamese.
- [ ] Step 4: Run cd apps/web && pnpm test -- config-panel.test.tsx; Expected: PASS.
