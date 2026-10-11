# Server-Side Item Holds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Thêm lượt chọn món server-side, giữ nguyên liệu theo lô FIFO và chuyển giữ thành tiêu hao/order nguyên tử khi gửi.

**Architecture:** GIU_CHO_MON lưu từng dòng món; CHI_TIET_GIU_CHO ghi lượng giữ trên từng lô. Service bán hàng phối hợp khóa nguyên liệu, kiểm tra availability, expiry và idempotency; router chỉ kiểm tra quyền/serialize. Giao diện gọi món đồng bộ cart với API trước khi submit.

**Tech Stack:** FastAPI, SQLAlchemy 2 async, Alembic, MySQL 8.4, Next.js 16, React 19, TypeScript, pytest, Vitest.

**Spec:** ../specs/2026-10-11-align-code-with-report-design.md, mục 2.

## Global Constraints

- Tên bảng/cột theo §4.2.2; số lượng dùng Decimal theo đơn vị chuẩn hóa.
- Giữ chỗ không ghi GIAO_DICH_KHO và không đổi tồn sổ sách.
- Kiểm tra availability, ghi giữ, gửi và cập nhật tồn trong transaction.
- Khóa nguyên liệu theo MaNguyenLieu tăng dần trước khi khóa lô/giữ.
- Lô hết hạn không được giữ/bán; expiry được kiểm tra theo giờ server dù chưa dọn trạng thái.
- Bàn chỉ bị chiếm khi lượt gửi đầu tiên thành công; mọi write có role/ownership check.
- `CAU_HINH_HE_THONG` là hàng khóa điều phối chung cho kiểm kê và mọi biến động kho: cùng transaction phải khóa hàng này trước khi kiểm tra phiên `Đang kiểm kê` hoặc bắt đầu ghi kho.
- Một phiếu kiểm kê chuyển thành `Đang kiểm kê` ngay khi tạo; chỉ xác nhận hoặc hủy mới giải phóng phiên. Không cho tạo phiên thứ hai.

---

### Task 1: Models, constraints và migration

**Files:**
- Modify: apps/api/src/app/modules/sales/models.py
- Create: a new Alembic migration `add_item_holds.py` after the effective-system-config revision
- Modify: apps/api/tests/schema/test_sales_models.py
- Modify: apps/api/tests/schema/test_schema_contract.py
- Reference: docs/BaoCao_HeThongQuanLyNhaHang.md, bảng 44–45, ràng buộc giữ chỗ §4.2.2

**Interfaces:**
- ItemHold maps GIU_CHO_MON: owner, selection token, optional table/order, dish, recipe/price snapshot, qty/note, expiry/status, send idempotency fields and optional OrderLine link.
- ItemHoldLot maps CHI_TIET_GIU_CHO, composite key (MaGiuCho, MaLoNguyenLieu), quantity held.
- MaChiTietOrder unique when populated; (MaYeuCauGui, MaDongYeuCau) unique when populated.

- [ ] Step 1: Add schema tests for table/columns/FKs/checks/unique keys and update EXPECTED_TABLES.
- [ ] Step 2: Run cd apps/api && uv run pytest tests/schema/test_sales_models.py tests/schema/test_schema_contract.py -q; Expected: FAIL before models exist.
- [ ] Step 3: Implement mapped models and reversible migration; register models in migration imports.
- [ ] Step 4: Run the same schema tests; Expected: PASS.

### Task 2: Hold allocation, release and stocktake exclusion

**Files:**
- Create: apps/api/src/app/modules/sales/holds.py
- Modify: apps/api/src/app/modules/inventory/stock.py
- Modify: apps/api/src/app/modules/inventory/service.py
- Modify: apps/api/src/app/modules/inventory/router.py
- Modify: apps/api/src/app/shared/enums.py
- Test: apps/api/tests/modules/test_sales_holds.py
- Test: apps/api/tests/modules/test_inventory_stocktake.py
- Test: apps/web/src/features/inventory/stocktake-panel.test.tsx

**Interfaces:**
- upsert_hold(session, actor_id, selection_id, dish_id, quantity, note, table_id, order_id) returns ItemHold.
- list_holds(session, actor_id, selection_id) returns owned selection lines.
- release_hold(session, actor_id, hold_id) ends a hold and returns its held lots.
- Availability per lot = max(0, quantity_remaining - active, unexpired holds).
- Selection groups one user's unsubmitted lines; an add-on selection references an open order.
- A hold expires at the earlier of configured TTL and the earliest expiry among allocated lots. Expired lines remain visible; submit rechecks and may allocate again only if current availability is sufficient.
- `StocktakeStatus` gains `DANG_KIEM_KE`; `create_stocktake` locks the singleton config row, rejects an existing active session, and creates the active session. `record_counts` accepts only the active session; confirm and new cancel action transition it to terminal status.
- Receipt, issue, write-off, stock adjustment, hold create/renew/submit/release and order reversal all lock the same config row before their stock-changing decision and reject while a stocktake is active. Read-only inventory browsing remains available.

- [ ] Step 1: Write tests for FIFO across multiple lots, expiry-capped TTL, expired-line display and reallocation-at-submit, competing holds, release restoring availability, only-one-active-stocktake, and rejection of each stock-changing path during an active stocktake.
- [ ] Step 2: Run cd apps/api && uv run pytest tests/modules/test_sales_holds.py -q; Expected: FAIL because module does not exist.
- [ ] Step 3: Implement the shared config-row lock/check in every stock mutation service, sorted ingredient locks, FIFO lot allocation and transactional writes; keep stock ledger unchanged for holds.
- [ ] Step 4: Change stocktake lifecycle to `Đang kiểm kê` on create; record stable system quantities while the active-session guard blocks stock writes; add authorized cancel route/UI, require active status for count/confirm, and transition to `Đã chốt` or `Đã hủy` atomically.
- [ ] Step 5: Add MySQL 8.4 integration tests proving a competing stock mutation waits for the config-row lock and then observes the active session; verify rollback releases locks and no partial stock changes remain.
- [ ] Step 6: Run `cd apps/api && uv run pytest tests/modules/test_sales_holds.py tests/modules/test_inventory_stocktake.py -q` and `cd apps/web && pnpm test -- stocktake-panel.test.tsx`; Expected: PASS.

### Task 3: API send and idempotency

**Files:**
- Modify: apps/api/src/app/modules/sales/orders.py
- Modify: apps/api/src/app/modules/sales/router.py
- Modify: apps/api/src/app/modules/sales/schemas.py
- Modify: apps/api/src/app/modules/inventory/service.py if stock movement conversion is exposed there
- Test: apps/api/tests/modules/test_sales_holds.py
- Test: apps/api/tests/modules/test_sales_orders.py
- Test: apps/api/tests/modules/test_sales_locking_and_search.py

**Interfaces:**
- POST /sales/selections creates/reuses a selection token.
- PUT /sales/selections/{selection_id}/lines/{dish_id} creates or updates a held line.
- DELETE /sales/holds/{hold_id} releases one line.
- POST /sales/selections/{selection_id}/submit accepts unique MaYeuCauGui and returns the same outcome on retry.
- Submit converts held quantities to exact FIFO StockMovement rows and links each hold to one OrderLine.
- Submit locks/checks the stocktake guard and rejects while an active stocktake exists; stale price/recipe response releases the hold atomically and asks the cashier to reconfirm.

- [ ] Step 1: Write tests for cashier/manager permissions, non-owner denial, stale recipe/price, duplicate submission and rollback after a failed line.
- [ ] Step 2: Run cd apps/api && uv run pytest tests/modules/test_sales_holds.py -q; Expected: FAIL.
- [ ] Step 3: Add request schemas/routes; preserve existing order endpoint compatibility until all repository consumers use the selection flow; keep handlers thin and transactional orchestration in service functions.
- [ ] Step 4: Run hold/order/locking tests; Expected: PASS.

### Task 4: Server-backed cart UI

**Files:**
- Modify: apps/web/src/features/sales/order-step.tsx
- Modify: apps/web/src/features/sales/types.ts
- Modify: apps/web/src/features/sales/sales-workspace.tsx if selection ID must persist between steps
- Test: apps/web/src/features/sales/order-step.test.tsx

**Interfaces:**
- UI retains a selection token and server hold IDs; each edit syncs quantity/note.
- Submit reuses one stable request key after timeout/retry.
- UI shows expiry and requires confirmation when server reports stale price/recipe.
- Expired rows remain visible with an expiry label; retry/submit displays per-line availability failures without discarding the rest of the user's selection.

- [ ] Step 1: Add tests asserting selection and hold endpoints are called, expiry is rendered, and retry uses the same request key.
- [ ] Step 2: Run cd apps/web && pnpm test -- order-step.test.tsx; Expected: FAIL because current cart is browser-local.
- [ ] Step 3: Replace direct create/send flow with hold API while preserving existing error messages and navigation.
- [ ] Step 4: Run cd apps/web && pnpm test -- order-step.test.tsx sales-workspace.test.tsx; Expected: PASS.
