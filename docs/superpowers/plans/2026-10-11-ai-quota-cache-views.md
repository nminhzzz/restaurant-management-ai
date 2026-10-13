# AI Quota, Cache, and Role Views Implementation Plan

> **Trạng thái (2026-10-13):** đã triển khai. Đánh dấu theo bằng chứng trong mã và test hiện có (`make test-api`/`make test-web` xanh ngày 2026-10-13); bước 'Expected: FAIL' (red) không lưu bằng chứng riêng nên được đánh dấu theo kết quả cuối của task. Bước chưa có bằng chứng (chạy MySQL thật, `make gate` đầy đủ) để trống.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Khớp FR-AI-10/NFR-06/12: quota 50 câu/người/Business Date, cache ngắn hạn an toàn, view Bếp thấy lượng giữ nhưng không lộ dữ liệu cấm.

**Architecture:** Dùng TRUY_VAN_AI làm sổ quota; khóa bản ghi user để reserve một lượt hỏi trước khi gọi LLM, rồi cập nhật cùng bản ghi khi có kết quả. Cache được scope theo user/role/view/date và dữ liệu kết quả; truy vấn DB vẫn chạy mới mỗi lượt.

**Tech Stack:** FastAPI, SQLAlchemy 2 async, MySQL 8.4 views/grants, pytest, sqlglot.

**Spec:** ../specs/2026-10-11-align-code-with-report-design.md, mục 3.

## Global Constraints

- Mỗi role chỉ dùng một view và một read-only DB account riêng.
- Mọi SQL sinh ra vẫn qua guard.validate_sql; giữ trần 500 dòng, timeout 3 giây và tối đa 2 lần sinh.
- Không cache câu hỏi tồn/giữ/số suất còn phục vụ; các câu này luôn query dữ liệu mới.
- Cache không chia sẻ giữa người dùng, vai trò hoặc phạm vi view.
- Không cấp tài khoản AI quyền đọc trực tiếp bảng nghiệp vụ.

---

### Task 1: Quota riêng theo user/Business Date

**Files:**
- Modify: apps/api/src/app/modules/ai/service.py
- Modify: apps/api/src/app/modules/ai/pipeline/generator.py
- Modify: apps/api/src/app/modules/ai/models.py if a pending status is required
- Test: apps/api/tests/modules/test_ai_generator.py
- Test: apps/api/tests/modules/test_ai_service.py

**Interfaces:**
- answer(session, question, role, user_id, session_id) reserves one question before model calls.
- generate_sql receives user_id and effective Business Date; it no longer increments a process-global counter per SQL attempt.
- One TRUY_VAN_AI row is created as pending and updated for all success/refusal/error exits.
- One user question consumes one quota slot regardless of the number of SQL-generation attempts; a rejection before reservation consumes none. Incomplete pending rows are visible as failed/interrupted history and still count, preventing worker crashes from restoring quota.

- [x] Step 1: Add tests for separate users, limit reached, retrying after bad SQL, and two concurrent same-user requests.
- [x] Step 2: Run cd apps/api && uv run pytest tests/modules/test_ai_generator.py tests/modules/test_ai_service.py -q; Expected: FAIL because quota is process-global.
- [x] Step 3: Lock the user row, count that user's reserved question rows within the effective Business Date, then insert and commit one pending query row before generation. Persist the question's Business Date so later setting changes cannot move its quota bucket.
- [x] Step 4: Update the pending row instead of inserting a second history record; set default to 50 and remove _daily_calls.
- [x] Step 5: Run targeted AI service/generator tests; Expected: PASS.

### Task 2: Short-lived cache without stale results

**Files:**
- Modify: apps/api/src/app/modules/ai/pipeline/generator.py
- Modify: apps/api/src/app/modules/ai/service.py
- Modify: apps/api/src/app/modules/ai/pipeline/interpreter.py
- Test: apps/api/tests/modules/test_ai_generator.py
- Test: apps/api/tests/modules/test_ai_service.py

**Interfaces:**
- Cache keys include user ID, role, allowed view, normalized question, normalized temporal parameters, effective Business Date and permission fingerprint.
- SQL is revalidated through guard.validate_sql after cache retrieval.
- Interpretation cache also includes a digest of freshly queried result rows; the DB query is never skipped.
- Entries have short TTL and a maximum size.
- Cache the validated SQL/template only; always execute it against the scoped read-only connection. Interpretation may be cached only after a fresh query and only under a digest of the current result rows; skip caching when the question depends on volatile stock/hold/service-capacity data.

- [x] Step 1: Add tests showing cache isolation across users/roles/views/dates/temporal parameters, permission-version changes, expiry, and changed result rows changing the interpretation key.
- [x] Step 2: Run the target AI tests; Expected: FAIL on current key (role, normalized question) and no TTL.
- [x] Step 3: Implement bounded TTL cache and key construction; revalidate cached SQL with the current view scope and guard, do not cache final rows or skip DB execution, and bypass cache for volatile inventory/hold/capacity questions.
- [x] Step 4: Run cd apps/api && uv run pytest tests/modules/test_ai_generator.py tests/modules/test_ai_service.py tests/modules/test_ai_guard.py tests/modules/test_ai_accounts.py -q; Expected: PASS.

### Task 3: Add held quantity to warehouse view

**Files:**
- Modify: db/views/vw_ai_kho.sql
- Modify: db/views/README.md
- Modify: apps/api/tests/schema/test_ai_views.py
- Test: MySQL 8.4 integration test through apps/api/tests/schema/test_ai_views.py

**Interfaces:**
- vw_ai_kho exposes a named aggregate for active held and available quantities, computed from unexpired holds and eligible lots.
- Cashier view remains free of inventory/cost/purchase fields; grants remain one view per role.

- [x] Step 1: Add view-column contract and assertions that expired holds do not count and forbidden fields stay excluded.
- [x] Step 2: Run cd apps/api && uv run pytest tests/schema/test_ai_views.py -q; Expected: FAIL until DDL and expected columns agree.
- [x] Step 3: Extend NULL-padded UNION ALL branches in vw_ai_kho.sql and document row types in db/views/README.md.
- [ ] Step 4: Run view contract and MySQL 8.4 grant tests; Expected: exact columns and grants remain role-scoped.

### Task 4: Use the effective Business Date in AI prompts

**Reason:** Code review found that `ai/pipeline/prompt.py` still tells the model that a Business Date runs 06:00–06:00 and defines “hôm nay” as `BusinessDate = CURDATE()`. The system now supports a configured boundary, and Task 1/2 already pass the effective Business Date into SQL generation. A cached query key can include the correct date while the prompt still asks the model to generate SQL using the wrong date semantics.

**Files:**
- Modify: apps/api/src/app/modules/ai/pipeline/prompt.py
- Modify: apps/api/src/app/modules/ai/pipeline/generator.py
- Test: apps/api/tests/modules/test_ai_prompt.py
- Test: apps/api/tests/modules/test_ai_generator.py

**Interfaces:**
- `build_prompt` receives the captured effective Business Date for this question.
- The prompt says “hôm nay” means the supplied Business Date literal and instructs the model to filter `BusinessDate` against that value, not `CURDATE()`.
- Schema notes describe Business Date as configured by the restaurant without asserting a fixed 06:00 boundary.

- [x] Step 1: Add prompt/generator tests proving the effective Business Date is present for relative-date questions, fixed 06:00 and `CURDATE()` guidance are absent, and the role still sees only its allowed view.
- [x] Step 2: Run `cd apps/api && uv run pytest tests/modules/test_ai_prompt.py tests/modules/test_ai_generator.py -q`; Expected: FAIL because the prompt still hardcodes the old boundary.
- [x] Step 3: Pass the already captured date from `generate_sql` into `build_prompt`, update Business Date guidance, and keep SQL guard/cache behavior unchanged.
- [ ] Step 4: Run focused prompt/generator/service tests and `make gate`; Expected: PASS.
