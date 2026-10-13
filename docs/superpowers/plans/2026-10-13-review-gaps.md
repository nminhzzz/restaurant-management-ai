# Review gaps: align code with the report (branch `fix/review-gaps`)

Base: `feat/document-alignment` @ 16e5532 (holds, per-user AI quota, lot expiry warnings already done there).
Baseline: `pytest` 521 passed; ruff/mypy/eslint/tsc/vitest green. Never end a task with these red.

## Ground rules

1. **The report (`docs/BaoCao_HeThongQuanLyNhaHang.md`) is the source of truth.** Change code to match it.
   Where the report is silent, wrong, internally inconsistent, or behind reality, fix/extend the **report** and
   say so in the final summary (no silent drift). Keep Vietnamese in docs/UI strings, English in code.
2. Every bug fix ships a regression test that fails before and passes after. New behavior ships tests
   (empty, boundary, permission denied, concurrency where it applies). Never weaken a test; fix wrong ones and say why.
3. Migrations: only **new** revisions; never edit an applied one. Keep a **single alembic head**
   (`alembic heads` must list one). Only the task that owns the migration may create it.
4. No raw SQL string building; all writes check role server-side; AuthN != AuthZ; errors fail closed with no internals.
5. Do not commit. Do not touch the main checkout (`/Users/nmh/work/Mac/NMHx/Personal/KLTN` outside `.worktrees/review-gaps`)
   nor `.worktrees/doc-alignment`. Do not read/print `.env`.
6. Checks (from `apps/api`): `ruff check . && ruff format --check . && mypy .`;
   tests: `PYTHONPATH=$PWD/src /Users/nmh/work/Mac/NMHx/Personal/KLTN/apps/api/.venv/bin/pytest -p no:cacheprovider`
   (needs sandbox disabled because pydantic reads `.env`; user approved this for pytest only).
   Web (from `apps/web`): `pnpm lint && pnpm typecheck && pnpm format:check && pnpm test`.

## Work packages (disjoint file ownership)

### WP-A: AI module (`modules/ai/**`, `db/views/**`, `data/eval/**`, `tests/**/ai*`, `docs` AI parts)
- Guard hardening (security): CTE names must not shadow real tables (reject any CTE that references a relation
  not in the allow-list, incl. self-reference; a CTE named like a core table is rejected); strip/reject comments and
  optimizer hints (`/*+ ... */`, `--`, `#`); reject lock clauses (`FOR UPDATE`, `LOCK IN SHARE MODE`), `@user_vars`,
  `SELECT` without `FROM` that reads system vars; keep one statement, read-only, row cap. Add tests for each shape
  (CTE shadowing, hints, comments, lock clauses, UNION+LIMIT, subquery on a core table).
- Report l.~1130 claims column-level allow-listing: either implement column checking against the role view columns
  (preferred, `scope.py` already knows the views) or correct the report. Decide and state.
- Executor: make the "only via `validate_sql`" rule structural (e.g. executor validates internally or takes a
  `ValidatedSql` type) so `data/eval/harness.py` cannot bypass it; keep gold-SQL execution explicit and separate.
- Retry rules per report l.~1132 (one regeneration on syntax/execution error; out-of-scope request ends immediately);
  stop logging generic errors with the scope-refused text.
- Manager view must inherit the warehouse scope (FR-SET-03): add the lot branch/columns to `vw_ai_quanly.sql`
  or fix README+report; `HanSuDungLo` note must match the SQL; `db/views/README.md` must match all three `.sql` files
  (SoLuongGiu/SoLuongKhaDung must exist in `vw_ai_kho.sql` if README says so; verify the branch already added them).
- `.env.example` AI/LLM/payment variables and comments must match `core/config.py` (DeepSeek default, `LLM_BASE_URL`,
  `LLM_FALLBACK_MODEL`, `LLM_REASONING_EFFORT`, `AI_CONFIG_C_MODEL`, `SEPAY_*`, `PAYMENT_*`; blank `AI_READONLY_URL_*`
  must fail closed, not silently fall back). NOTE: the sandbox cannot read `.env*`; edit via Write and tell the user.
- Eval: few-shot examples must only use real view columns (no `ThanhTien`); `questions.jsonl` = 95 -> report says 80:
  update the report numbers (95; 31/40/24; MANAGER 45/CASHIER 24/WAREHOUSE 26; 6 refusal questions reported separately
  from the denominator, or report that they are included). Add `docs/eval-results.json` results (p95 ~14.5s B / ~20s C vs NFR-02 10s) to the
  report with honest labeling; align the 8s pipeline budget vs the 10s NFR threshold; Config C wording must match code.
- Persisted/logged fields: report vs `TRUY_VAN_AI`/`PHIEN_CHAT_AI` (token/cost columns, `MaVaiTro`, `KetQuaTomTat`):
  implement the report's columns (migration owner is WP-C; request columns from WP-C in your final notes) or amend report.
- `scripts/seed/README.md` "Chưa triển khai" -> describe the real seed.

### WP-C: Core/auth, settings, catalog, inventory (`core/**`, `shared/**`, `modules/{settings,catalog,inventory,reports}/**`, `migrations/**`)
Owns **the one new migration** for this effort (schema alignment) and runs first.
- Security: `get_current_user` must re-check the user in DB on each request (exists, not locked/deleted, current role);
  locked or role-changed users lose access immediately (NFR-19, FR-SET-01). Keep token claims minimal. Tests for locked user,
  role change, deleted user, forged role claim.
- Audit: `AuditEntryOut.MaNguoiDung` optional (system entries have `user_id=None`; endpoint must not 500);
  audit entries for config/catalog/inventory/sales mutations carry before/after (FR-SET-09); pending-change overwrite
  leaves an audit record instead of silent hard delete (FR-CAT-21).
- Settings per report: `CAU_HINH_HE_THONG` fields (`GioBatDauBusinessDateMoi`, `NgayHieuLucGioMoi`, `SoNgayCanhBaoHetHan`,
  `SoCauHoiAIMoiNgay`, `ThoiGianGiuChoPhut`, ...) — check which the branch already added; add the rest, validate ranges,
  Business Date start must come from config (via `app.shared.business_date`), user update + role change + lock endpoints (Manager only,
  cannot lock/demote the last Manager or self), default min-stock applies live (0 != unset).
- Catalog: GET endpoints restricted per Tables 9/10 (no blanket authenticated access); scheduled price/recipe versions are
  promoted when due (lazy promotion at read/write in `versions.py` inside a transaction, idempotent, audited);
  manual pause vs derived out-of-stock are independent (`TamDungThuCong` per report FR-CAT-26/27 — check branch); dish group required if the
  report says "đúng một nhóm"; table rules FR-CAT-17/18 (release table, `MaOrderDangPhucVu`, status values) per report.
- Inventory: lot status evaluated by expiry (`Hết hạn`/`Sắp hết hạn`, FEFO must skip expired lots, `SoNgayCanhBaoHetHan`);
  `cancel_receipt` forbidden when any lot of the receipt is partly consumed (FR-INV-02); stocktake locks writers for the
  ingredient during the session or recomputes safely (NFR-20), BR-LOT-02: positive diff adds to latest valid lot or creates
  a lot with `MaChiTietNhap` NULL (no fake receipt), negative diff consumes lots and creates the stock issue per report;
  `costing.close_month` excludes cancelled receipts and zero-price stocktake receipts.
- Schema alignment migration: add the missing FKs (`LICH_SU_DOI_BAN.NguoiThucHien`, `PHIEU_XUAT_KHO.NguoiLap`, `PHIEU_KIEM_KE.NguoiThucHien`,
  `HOA_DON.MaGiaoDichThanhToan`, `HOA_DON.NguoiLap`, `PHIEN_CHAT_AI.MaVaiTro`) with ON DELETE/UPDATE per report; `GIAO_DICH_KHO` CHECK
  so model == migration == report; declare ON DELETE/UPDATE on `NHAT_KY_HE_THONG.MaNguoiDung`; `TRUY_VAN_AI` FK action per report;
  unique `HOA_DON.SoHoaDon`, `GIAO_DICH_THANH_TOAN.MaGiaoDichCong/MaGiaoDichNganHang`, `VAI_TRO.TenVaiTro`; positive CHECKs the report names.
  Add the columns WP-A and WP-B request (token/cost columns on `TRUY_VAN_AI`; payment-exception columns). Provide `upgrade` AND `downgrade`.
  Verify on a throwaway local MySQL only if one is running; otherwise verify with alembic offline SQL (`--sql`) and report that it was not applied.
- Where the report differs from reality in a way that is a *report* error (e.g. `DEM_ORDER` table missing, `NgayTao` vs `ThoiDiemTao`,
  `MaChiTietKK` vs `MaChiTietKiemKe`, duplicated `TrangThai` in PHIEU_KIEM_KE, `VAI_TRO.MaVaiTro` type, date types, status string lists),
  fix the report + class diagram note, not the code. Remove or use dead enums in `shared/enums.py` so they match the report.
- Report (FR-REP-01/08/10, NFR-01/03): implement what the report says (breakdown by order type and payment method, cost comparison with
  "Không xác định tỷ lệ phần trăm" when the base is 0, cancelled report by day/week/month) or correct the report; update
  `scripts/bench_reports.py` and Makefile text so the benchmark measures NFR-01/NFR-03 as defined (HTTP, concurrent virtual users, p95).

### WP-B: Sales (`modules/sales/**`, `apps/web/src/features/sales/**`, `apps/web/src/app/(app)/sales/**`, `tests/**/sales*`) — runs after WP-C's migration lands
- Bugs: `cancel_line` crashes with >=2 remaining lines (use an `exists`/`first()` query); route bodies typed `dict` -> real Pydantic
  models so `ge=1` etc. apply; line routes must verify the line belongs to the `order_id` in the URL (authz, IDOR); `add_line` prices by
  the order's current effective version per report; `_return_line_stock` dict keyed by ingredient id mis-skips lots (key by lot) and calls
  `recompute_automatic_out_of_stock`.
- Ordering enforcement: reject deleted/draft/paused/out-of-stock dishes and dishes with no active price/recipe; table must be free
  (`Trống`) for dine-in; submit is all-or-nothing per report FR-SALE-08; expired lots never counted as available.
- Roles: WAREHOUSE must not read orders/tickets (Tables 9/10) unless the report says so; every write endpoint has `require_roles`.
- QR / exception flow exactly per report FR-SALE-14..23, 26, 31, 35, FR-REP-02: order -> `Chờ xác nhận thanh toán` and **locked** (no add/update/cancel/move
  line while a QR is live); `Chờ xác minh thanh toán`; `Đóng – chưa thu được tiền`; reopen payment; mark for verification while QR still valid;
  late full payment auto-confirm; wrong amount handling and refund record (`TrangThaiNgoaiLe`, `SoTienNgoaiLe`, `MaThamChieuHoan`, ...);
  exception list endpoint + UI (Manager/Cashier per report); provisional bill (FR-SALE-21); close order unpaid; cash payment while a QR is live
  must cancel/lock the QR atomically. Replace code states `Chờ đối soát`/`Tranh chấp` by the report's states (migrate existing values
  in the migration owned by WP-C coordination: ask for a data-migration step). Reports must exclude unverified payments from revenue per FR-REP-02.
- Payments security: webhook signature compared in constant time, body size/length limits, replay/duplicate protection by gateway txn id (unique),
  amount + account + content validation, lost-update safe row locks, simulator endpoint disabled outside `local`, no secret in logs.
- Invoice/ticket: unique `SoHoaDon` sequence and `NguoiLap` set; reprint renders the stored snapshot; kitchen ticket prints dish and table names.
- Audit entries for sales mutations (before/after). Session/DB timezone: every explicit timestamp uses `Asia/Ho_Chi_Minh` and `server_default` columns
  must not mix server tz (use app-side value).
- Web: UI for exception list, reopen/close-unpaid, provisional bill, locked-order states; Vietnamese strings; role-gated; vitest for new components.
- Add the missing **SePay section** to the report (spec `docs/superpowers/specs/2026-09-26-sales-steps-sepay-design.md` §7).

### WP-D: Docs, tests catalogue, repo hygiene (runs last; read-only on source)
- `docs/testing/test-cases.md`: renumber FR/NFR references to the report's current numbering; add cases for FR-SALE-30..35, FR-INV-13/14,
  FR-AI-10, FR-REP-05c, NFR-18..20 and every new behavior above; fix 4 broken test references; TC ids two-digit convention; `VW_AI_KHO` casing.
- `docs/testing/uat.md`, `sus.md`, `compatibility-checklist.md` consistent with the new states/flows.
- Root `README.md` (95 questions; Q5/Q6 closed; migration count; `fmt-check` in gate), `apps/web/README.md` (project-specific; **do not touch `apps/web/AGENTS.md`**),
  `apps/api/README.md` (reports module has no `models.py`), `AGENTS.md` repository map (`components/` list), `docs/design/tokens.md` (type scale + toast duration vs code),
  `docs/evidence/phase-0-mysql.md` stale TODO, Makefile `.PHONY` add `gate-full`.
- Plans/roadmap: tick checkboxes that are done (verify against code/tests), delete or mark obsolete the ones not applicable, fix stale references
  (`test_ai_isolation.py`, `require_any_role`, "guard.py 20 test"). Remove dead tests (`assert True` placeholder, empty `tests/factories.py` if unused).
- The report: final consistency pass over every item the other WPs flagged as "report fix"; table/column counts, class diagram note, FR/NFR numbering.

## Finish
1. `/security-review` on the whole diff; fix findings.
2. Full local gate (`make fmt-check lint typecheck test build` equivalents) green; unfinished checks are reported as unfinished.
3. Summary: files changed, tests added, report edits, items deliberately not done and why, items needing the user (uncommitted `.env.example`, running `make gate-integration` with MySQL).
