# Phase 1 — Module 5: Cài đặt hệ thống

> **Cho người thực thi:** dùng skill `executing-plans` để chạy kế hoạch này theo từng task.

**Mục tiêu:** Xác thực thật, quản lý tài khoản, phân quyền theo vai trò, cấu hình hệ thống và
audit log cho thao tác rủi ro cao (FR-SET-01…09) — đây là thứ mọi module khác cần để có người dùng
và token thật thay vì token giả lập.

**Kiến trúc:** Module `settings` sở hữu `VAI_TRO`, `NGUOI_DUNG`, `CAU_HINH_HE_THONG`; `NHAT_KY_HE_THONG`
nằm ở `app/shared/audit.py` vì mọi module đều ghi vào. Xác thực dùng JWT đã có sẵn ở
`app/core/security.py`; `app/core/dependencies.py` đã có `get_current_user` và `require_roles`.

**Spec:** báo cáo §2.4.5 (FR-SET-01…09), §3.4.2 (ma trận quyền chức năng), §3.4.3 (trách nhiệm vai trò).

**Phụ thuộc:** Phase 0 (bảng + lược đồ). **Lộ trình:** `docs/plans/2026-09-24-master-roadmap.md`

**Nhánh:** `feat/phase-1-settings` · **Cổng người duyệt:** G2

## Ràng buộc chung

- Mật khẩu băm bằng argon2 (NFR-04), **không bao giờ** trả `MatKhauHash` ra API.
- `NGUOI_DUNG` **không có** xóa cứng: khóa tài khoản = đổi `TrangThai` sang `'Đã khóa'`.
- Mọi thao tác trong danh sách FR-SET-08 phải ghi `NHAT_KY_HE_THONG` với người thực hiện thật.
- Quản lý kế thừa toàn bộ quyền của hai vai trò còn lại (FR-SET-03) — kiểm tra ở tầng API.
- Audit log **append-only**: không có API sửa/xóa (NFR-07).
- Mọi thao tác ghi nằm trong **một transaction** cùng bản ghi audit của nó (NFR-10) — không có nhật
  ký mồ côi khi rollback.
- Lỗi backend ghi log đủ chi tiết để điều tra, nhưng **không** lộ chi tiết kỹ thuật ra response
  (NFR-15, §5 của quy tắc chung).
- Sao lưu thủ công (FR-SET-06) phải đạt RPO ≤ 24 giờ (NFR-09) — ghi cách chạy vào README.
- `make gate` xanh trước khi kết thúc mỗi task.

## Cấu trúc file

| File | Trách nhiệm |
| --- | --- |
| `apps/api/src/app/modules/settings/schemas.py` | Hợp đồng request/response của module. |
| `apps/api/src/app/modules/settings/service.py` | Logic nghiệp vụ: đăng nhập, tài khoản, cấu hình, truy vấn audit. |
| `apps/api/src/app/modules/settings/router.py` | Tầng HTTP, gắn `require_roles`. |
| `apps/api/src/app/core/dependencies.py` | Bổ sung `require_any_role` cho Quản lý kế thừa quyền. |
| `apps/web/src/features/auth/` | Form đăng nhập, lưu token, đăng xuất, đổi mật khẩu. |
| `apps/web/src/lib/session.ts` | Đọc/ghi token, chuyển hướng khi 401. |
| `apps/web/src/app/login/page.tsx` | Thay placeholder bằng form thật. |
| `apps/web/src/app/(app)/settings/` | Màn hình tài khoản, cấu hình, nhật ký. |

---

## Task 1: Đăng nhập và cấp token (FR-SET-02)

**Files:**
- Create: `apps/api/src/app/modules/settings/schemas.py`
- Create: `apps/api/src/app/modules/settings/service.py`
- Modify: `apps/api/src/app/modules/settings/router.py`
- Test: `apps/api/tests/modules/test_settings_auth.py`

**Interfaces:**
- Consumes: `User`, `RoleTable` (Phase 0), `hash_password`/`verify_password`/`create_access_token`.
- Produces: `LoginRequest`, `TokenResponse`; `authenticate(session, username, password) -> User`;
  `POST /settings/auth/login`, `GET /settings/auth/me`.

- [ ] **Step 1: Viết test cho luồng đăng nhập**

```python
async def test_login_returns_a_token_for_an_active_account(db_session, active_user) -> None:
    response = await login(client, "thungan01", "mat-khau-dung")

    assert response.status_code == 200
    assert response.json()["role"] == "CASHIER"
    assert "MatKhauHash" not in response.text


async def test_locked_account_cannot_log_in(client, locked_user) -> None:
    response = await login(client, "thungan01", "mat-khau-dung")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_wrong_password_is_rejected_without_revealing_which_field_failed(
    client, active_user
) -> None:
    response = await login(client, "thungan01", "sai-mat-khau")

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Tên đăng nhập hoặc mật khẩu không đúng."
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_settings_auth.py -v`
Expected: FAIL — route chưa tồn tại (404)

- [ ] **Step 3: Cài đặt service + router**

`authenticate()` tra `TenDangNhap`, kiểm `TrangThai == 'Hoạt động'` và `verify_password`. Sai tên
hoặc sai mật khẩu trả **cùng một** thông báo để không lộ tài khoản nào tồn tại. Token chứa `sub`,
`role`, `username` — đúng shape mà `app/core/dependencies.py` đang đọc.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_settings_auth.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(settings): authenticate users and issue access tokens`

---

## Task 2: Quản lý tài khoản, gán vai trò và xuất bản sao (FR-SET-01, 03, 06)

**Files:**
- Modify: `apps/api/src/app/modules/settings/service.py`
- Modify: `apps/api/src/app/modules/settings/router.py`
- Modify: `apps/api/src/app/core/dependencies.py`
- Test: `apps/api/tests/modules/test_settings_accounts.py`

**Interfaces:**
- Consumes: Task 1, `audit.record`, `require_roles`.
- Produces: `require_any_role`; `create_user`, `update_user`, `lock_user`, `reset_password`;
  `GET/POST/PATCH /settings/users`.

- [ ] **Step 1: Viết test cho phân quyền và audit**

```python
async def test_only_a_manager_may_create_accounts(client, cashier_token, manager_token) -> None:
    forbidden = await create_user(client, cashier_token, username="moi01")
    allowed = await create_user(client, manager_token, username="moi01")

    assert forbidden.status_code == 403
    assert allowed.status_code == 201


async def test_manager_inherits_cashier_permissions(client, manager_token) -> None:
    """FR-SET-03: the manager keeps every cashier capability."""
    response = await get_table_status(client, manager_token)

    assert response.status_code == 200


async def test_account_creation_is_audited(client, manager_token, db_session) -> None:
    await create_user(client, manager_token, username="moi01")

    entry = await latest_audit(db_session)
    assert entry.action == "CREATE_USER"
    assert entry.target_entity == "NGUOI_DUNG"


async def test_locking_an_account_keeps_the_row(client, manager_token, db_session) -> None:
    """NGUOI_DUNG has no hard delete: locking only flips TrangThai."""
    await lock_user(client, manager_token, user_id=2)

    user = await get_user(db_session, 2)
    assert user is not None
    assert user.status == "Đã khóa"


async def test_a_locked_account_can_no_longer_sign_in(client, manager_token, active_user) -> None:
    """FR-SET-01."""
    await lock_user(client, manager_token, user_id=active_user.id)

    assert (await login(client, active_user.username, "mat-khau-dung")).status_code == 401


async def test_a_user_is_given_exactly_one_of_the_three_roles(client, manager_token) -> None:
    """FR-SET-01: one account, one role."""
    assert (await create_user(client, manager_token, username="a01", role="CASHIER")).status_code == 201
    assert (await create_user(client, manager_token, username="a02", role="BEP")).status_code == 422


async def test_a_cashier_cannot_touch_accounts(client, cashier_token) -> None:
    """FR-SET-01 and Table 33."""
    assert (await list_users(client, cashier_token)).status_code == 403
    assert (await lock_user(client, cashier_token, user_id=1)).status_code == 403


async def test_a_manual_backup_export_is_audited(client, manager_token, db_session) -> None:
    """FR-SET-06."""
    assert (await export_backup(client, manager_token)).status_code == 200

    assert (await latest_audit(db_session)).action == "EXPORT_BACKUP"


async def test_the_backup_can_restore_the_previous_day(client, manager_token, seeded_data) -> None:
    """NFR-09: RPO of at most 24 hours for the manual backup form."""
    dump = await export_backup(client, manager_token)

    assert dump.json()["created_at"] is not None
    assert dump.json()["covers_until"] - dump.json()["created_at"] <= timedelta(hours=24)
    assert dump.json()["table_count"] == 29


async def test_a_failed_write_leaves_no_audit_row(client, manager_token, db_session, monkeypatch) -> None:
    """NFR-10: the change and its audit entry share one transaction."""
    monkeypatch.setattr(settings_service, "flush_user", fail)

    with pytest.raises(Exception):
        await create_user(client, manager_token, username="moi01")

    assert await audit_count(db_session) == 0
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_settings_accounts.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt `require_any_role` và các endpoint**

`require_any_role(*allowed)` mở rộng `require_roles` để Quản lý luôn lọt qua (FR-SET-03 kế thừa).
Mọi thao tác ghi gọi `audit.record(...)` trong **cùng transaction** với thay đổi dữ liệu, để không
có bản ghi nhật ký mồ côi khi rollback.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_settings_accounts.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(settings): manage accounts, roles and the audit trail`

---

## Task 3: Đổi mật khẩu và cấu hình hệ thống (FR-SET-02, 04, 05)

**Files:**
- Modify: `apps/api/src/app/modules/settings/service.py`
- Modify: `apps/api/src/app/modules/settings/router.py`
- Test: `apps/api/tests/modules/test_settings_config.py`

**Interfaces:**
- Consumes: Task 1–2, `SystemConfig`.
- Produces: `change_own_password`, `reset_password` (Quản lý), `get_config`, `update_config`;
  `POST /settings/auth/change-password`, `GET/PUT /settings/config`.

- [ ] **Step 1: Viết test**

```python
async def test_changing_own_password_requires_the_current_one(client, cashier_token) -> None:
    wrong = await change_password(client, cashier_token, old="sai", new="moi-123456")
    right = await change_password(client, cashier_token, old="mat-khau-dung", new="moi-123456")

    assert wrong.status_code == 422
    assert right.status_code == 204


async def test_self_service_password_change_is_not_audited(client, cashier_token, db_session) -> None:
    """FR-SET-02: only a manager resetting someone else's password is audited."""
    await change_password(client, cashier_token, old="mat-khau-dung", new="moi-123456")

    assert await audit_count(db_session) == 0


async def test_manager_reset_is_audited(client, manager_token, db_session) -> None:
    await reset_password(client, manager_token, user_id=2, new="dat-lai-123456")

    entry = await latest_audit(db_session)
    assert entry.action == "RESET_PASSWORD"


async def test_config_is_a_singleton(client, manager_token) -> None:
    first = await update_config(client, manager_token, name="Quán A")
    second = await update_config(client, manager_token, name="Quán B")

    assert first.json()["MaCauHinh"] == second.json()["MaCauHinh"]


async def test_the_manager_sets_the_restaurant_name_address_and_invoice_template(
    client, manager_token
) -> None:
    """FR-SET-04."""
    body = (await update_config(
        client, manager_token, name="Quán A", address="12 Lê Lợi", invoice_template="mau-01"
    )).json()

    assert body["TenNhaHang"] == "Quán A"
    assert body["DiaChi"] == "12 Lê Lợi"
    assert body["MauHoaDon"] == "mau-01"


async def test_the_default_stock_threshold_can_be_configured(client, manager_token) -> None:
    """FR-SET-05."""
    body = (await update_config(client, manager_token, default_min_stock="5")).json()

    assert body["NguongTonMacDinh"] == Decimal("5")


async def test_a_negative_default_threshold_is_refused(client, manager_token) -> None:
    """FR-INV-07: the threshold is never below zero."""
    assert (await update_config(client, manager_token, default_min_stock="-1")).status_code == 422


async def test_the_business_day_start_cannot_be_edited_from_the_api(client, manager_token) -> None:
    """Section 3.2.1: fixed at 06:00, not shown to the user."""
    await update_config(client, manager_token, business_day_start="08:00")

    assert (await get_config(client, manager_token)).json()["GioBatDauBusinessDate"] == "06:00:00"


async def test_a_non_manager_cannot_read_the_config(client, cashier_token, warehouse_token) -> None:
    """Table 33."""
    assert (await get_config(client, cashier_token)).status_code == 403
    assert (await get_config(client, warehouse_token)).status_code == 403
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_settings_config.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt**

`GioBatDauBusinessDate` cố định 06:00 và **không** nhận từ client (§3.2.1: "không hiển thị cho
người dùng chỉnh sửa"). `NguongTonMacDinh` là mức tồn tối thiểu mặc định dùng khi nguyên liệu không
có mức riêng (FR-INV-07).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_settings_config.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(settings): self-service password change and system configuration`

---

## Task 4: Xem nhật ký audit (FR-SET-08, 09)

**Files:**
- Modify: `apps/api/src/app/modules/settings/service.py`
- Modify: `apps/api/src/app/modules/settings/router.py`
- Test: `apps/api/tests/modules/test_settings_audit_log.py`

**Interfaces:**
- Consumes: `SystemAuditLog`, `Page`/`PageParams`.
- Produces: `list_audit_entries`; `GET /settings/audit-log` (chỉ Quản lý).

- [ ] **Step 1: Viết test**

```python
async def test_only_a_manager_can_read_the_audit_log(client, cashier_token, warehouse_token) -> None:
    assert (await get_audit(client, cashier_token)).status_code == 403
    assert (await get_audit(client, warehouse_token)).status_code == 403
    assert (await get_audit(client, manager_token)).status_code == 200


async def test_entries_carry_actor_time_action_and_before_after(
    client, manager_token, db_session
) -> None:
    """FR-SET-09: minimum content of an audit entry."""
    await create_user(client, manager_token, username="moi01")

    entry = (await get_audit(client, manager_token)).json()["items"][0]
    assert {"MaNguoiDung", "ThoiDiem", "LoaiThaoTac", "DuLieuTruoc", "DuLieuSau"} <= set(entry)


async def test_the_log_cannot_be_edited_or_deleted(client, manager_token) -> None:
    """NFR-07: append-only."""
    deleted = await client.delete("/api/v1/settings/audit-log/1", headers=manager_headers)
    patched = await client.patch("/api/v1/settings/audit-log/1", headers=manager_headers)

    assert deleted.status_code == 405
    assert patched.status_code == 405
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_settings_audit_log.py -v`
Expected: FAIL — route chưa tồn tại

- [ ] **Step 3: Cài đặt endpoint chỉ-đọc**

Chỉ đăng ký `GET`. Lọc theo `LoaiThaoTac`, `MaNguoiDung`, khoảng `ThoiDiem`; phân trang bằng
`PageParams` có sẵn.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_settings_audit_log.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(settings): read the append-only audit log`

---

## Task 5: Giao diện đăng nhập và phiên làm việc

**Files:**
- Create: `apps/web/src/lib/session.ts`
- Create: `apps/web/src/features/auth/login-form.tsx`
- Create: `apps/web/src/features/auth/login-form.test.tsx`
- Modify: `apps/web/src/app/login/page.tsx`
- Modify: `apps/web/src/lib/api-client.ts` (gắn token tự động)

**Interfaces:**
- Consumes: `POST /settings/auth/login`, `apiFetch`.
- Produces: `saveSession`, `loadSession`, `clearSession`, `authHeaders`; `LoginForm`.

- [ ] **Step 1: Viết test**

```tsx
it("stores the token and redirects after a successful login", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ access_token: "abc", role: "CASHIER", username: "thungan01" }),
  }));

  render(<LoginForm />);
  fireEvent.change(screen.getByLabelText("Tên đăng nhập"), { target: { value: "thungan01" } });
  fireEvent.change(screen.getByLabelText("Mật khẩu"), { target: { value: "mat-khau-dung" } });
  fireEvent.click(screen.getByRole("button", { name: "Đăng nhập" }));

  expect(await screen.findByText("Đăng nhập thành công")).toBeInTheDocument();
  expect(loadSession()?.role).toBe("CASHIER");
});

it("shows the server message when the password is wrong", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: false, status: 401,
    json: async () => ({
      error: { code: "UNAUTHENTICATED", message: "Tên đăng nhập hoặc mật khẩu không đúng." },
    }),
  }));

  render(<LoginForm />);
  fireEvent.click(screen.getByRole("button", { name: "Đăng nhập" }));

  expect(await screen.findByText("Tên đăng nhập hoặc mật khẩu không đúng.")).toBeInTheDocument();
});
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/web && pnpm test`
Expected: FAIL — `Cannot find module '@/features/auth/login-form'`

- [ ] **Step 3: Cài đặt**

Token lưu ở `sessionStorage` (không phải `localStorage`) để đóng tab là hết phiên — máy dùng chung
ở quầy thu ngân. `apiFetch` tự gắn `Authorization` khi có phiên, và xóa phiên khi nhận 401.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/web && pnpm test`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/web && pnpm format:check && pnpm lint && pnpm typecheck`
Expected: xanh. Commit: `feat(web): sign in and keep the session token`

---

## Task 6: Ẩn menu theo vai trò và màn hình Cài đặt (FR-SET-03)

**Files:**
- Modify: `apps/web/src/components/app-shell.tsx`
- Modify: `apps/web/src/lib/modules.ts` (thêm danh sách vai trò được phép cho mỗi module)
- Create: `apps/web/src/app/(app)/settings/users/page.tsx`
- Create: `apps/web/src/app/(app)/settings/audit-log/page.tsx`
- Test: `apps/web/src/components/app-shell.test.tsx`

**Interfaces:**
- Consumes: `loadSession`, `MODULE_LIST`.
- Produces: `ModuleDescriptor.allowedRoles: Role[]`; `AppShell` lọc menu theo phiên.

- [ ] **Step 1: Viết test**

```tsx
it("hides modules the signed-in role cannot reach", () => {
  saveSession({ token: "t", role: "WAREHOUSE", username: "kho01" });

  render(<AppShell><p>nội dung</p></AppShell>);

  expect(screen.queryByRole("link", { name: "Báo cáo thống kê" })).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Quản lý kho" })).toBeInTheDocument();
});

it("shows every module to the manager", () => {
  saveSession({ token: "t", role: "MANAGER", username: "quanly01" });

  render(<AppShell><p>nội dung</p></AppShell>);

  expect(screen.getAllByRole("link")).toHaveLength(MODULE_LIST.length + 1);
});
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/web && pnpm test`
Expected: FAIL — `allowedRoles` chưa tồn tại

- [ ] **Step 3: Cài đặt**

`allowedRoles` lấy từ Bảng 33 (§3.4.2). Đây **chỉ là lớp giao diện** — mọi endpoint vẫn phải tự
kiểm tra quyền (NFR-05); ghi rõ điều này trong comment của `modules.ts`.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/web && pnpm test`
Expected: PASS

- [ ] **Step 5: Chạy cổng kiểm tra đầy đủ**

Run: `UV_CACHE_DIR=/tmp/uv-cache make gate`
Expected: xanh. Commit: `feat(web): gate the navigation by role and add the settings screens`

---

## Kiểm chứng

| Cổng | Lệnh | Kỳ vọng |
| --- | --- | --- |
| Đăng nhập | `pytest tests/modules/test_settings_auth.py` | xanh |
| Tài khoản + audit | `pytest tests/modules/test_settings_accounts.py` | xanh |
| Cấu hình | `pytest tests/modules/test_settings_config.py` | xanh |
| Nhật ký chỉ-đọc | `pytest tests/modules/test_settings_audit_log.py` | xanh |
| Giao diện | `cd apps/web && pnpm test` | xanh |
| Toàn bộ | `make gate` | xanh |

## Rủi ro

- **Token trong `sessionStorage`**: mất phiên khi tải lại tab ở chế độ khôi phục. Chấp nhận được cho
  quầy thu ngân; nếu cần giữ phiên lâu hơn thì chuyển sang refresh token — nằm ngoài phạm vi MVP.
- **Quản lý kế thừa quyền**: dễ viết sai thành "chỉ MANAGER" ở một endpoint. Test
  `test_manager_inherits_cashier_permissions` là mẫu; mỗi module sau cần test tương tự.
- **FR-SET-07 (sao lưu tự động theo lịch) là mở rộng** — không làm ở phase này. FR-SET-06 (xuất bản
  sao thủ công) làm ở Task 2: endpoint kết xuất dữ liệu và **ghi audit**; phần phục hồi (restore) của
  FR-SET-07 để sau vì nó là thao tác phá huỷ, cần bàn riêng trước khi làm.
- **`GioBatDauBusinessDate` cố định 06:00**: nếu sau này muốn cấu hình được thì phải sửa cả
  `app.shared.business_date` và các cột `BusinessDate` đã denormalize — mọi dòng cũ sẽ mang cutoff cũ.
  Đây là lý do §3.2.2 chọn ghi `BusinessDate` lúc tạo dòng thay vì suy diễn lại.
