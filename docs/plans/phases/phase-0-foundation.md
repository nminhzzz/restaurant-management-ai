# Phase 0 — Lược đồ CSDL, view phân quyền và tài khoản chỉ-đọc

> **Cho người thực thi:** dùng skill `executing-plans` (hoặc `subagent-driven-development`) để chạy
> kế hoạch này theo từng task. Các bước có ô `- [ ]` để đánh dấu tiến độ.

**Mục tiêu:** Dựng lược đồ quan hệ 29 bảng theo §3.2 của báo cáo, kèm ba view `vw_ai_*` và ba tài
khoản CSDL chỉ-đọc — mở khoá cho cả sáu module nghiệp vụ.

**Kiến trúc:** ORM model SQLAlchemy 2 (khai báo theo module) là nguồn sự thật cho bảng; Alembic
sinh migration từ metadata. Ba view `vw_ai_*` và `GRANT` không thuộc ORM nên nằm ở `db/views/` dưới
dạng DDL thủ công, chạy sau migration.

**Spec:** `docs/BaoCao_HeThongQuanLyNhaHang.md` §3.2.1 (thuộc tính từng lớp), §3.2.2 (ánh xạ +
quy ước vật lý), §3.2.3 (index), §3.4.1 (ma trận quyền dữ liệu).

**Lộ trình:** `docs/plans/2026-09-24-master-roadmap.md`

**Nhánh:** `feat/phase-0-schema` · **Cổng người duyệt:** G1 (xem master roadmap)

---

## Ràng buộc chung

- MySQL **8.4**, `utf8mb4` / `utf8mb4_unicode_ci`, `TZ=Asia/Ho_Chi_Minh`.
- Định danh CSDL **tiếng Việt** theo đúng báo cáo (`NGUYEN_LIEU`, `MaNguyenLieu`, `DaXoa`);
  tên lớp/hàm/biến Python là tiếng Anh.
- Khoá chính là **surrogate key số tự tăng** → `ON UPDATE` của mọi FK là `RESTRICT`.
- `ON DELETE`: `RESTRICT` cho FK trỏ tới danh mục/định danh/chứng từ đã bị dữ liệu lịch sử tham
  chiếu; `CASCADE` chỉ cho dòng chi tiết phụ thuộc hoàn toàn vào chứng từ cha; **không dùng SET NULL**.
- Kiểu cột theo §3.2.2: `int`→`INT`, `Long`→`BIGINT`, `double`→`DECIMAL(18,4)` (tiền/định lượng),
  `String`→`VARCHAR`, `boolean`→`TINYINT(1)`, `LocalDate`→`DATE`, `LocalDateTime`→`DATETIME`.
- Business Date là 06:00 → 06:00 hôm sau, dùng `app.shared.business_date`, không tự tính lại.
- Không nối chuỗi SQL; mọi truy vấn qua SQLAlchemy.
- `make gate` phải xanh trước khi kết thúc.

## Cấu trúc file

| File | Trách nhiệm |
| --- | --- |
| `apps/api/src/app/shared/enums.py` | Toàn bộ trạng thái nghiệp vụ dùng chung (đơn, món, giao dịch, lô, phiếu…). |
| `apps/api/src/app/shared/base.py` | Đã có: `Base`, naming convention, `CreatedAtMixin`, `SoftDeleteMixin`. Bổ sung khoá `ck` vào naming convention và mixin `BusinessDateMixin`. |
| `apps/api/src/app/shared/business_date.py` | Đã có: `business_date_of`, `business_date_start`, `business_date_range`, `next_business_date`. Bổ sung `now()` — seam đồng hồ duy nhất (Task 0 Step 4). |
| `apps/api/src/app/modules/settings/models.py` | `VAI_TRO`, `NGUOI_DUNG`, `CAU_HINH_HE_THONG`. |
| `apps/api/src/app/shared/audit.py` | Đã có `NHAT_KY_HE_THONG`; chỉnh kiểu cột theo quyết định #3. |
| `apps/api/src/app/modules/catalog/models.py` | `NHOM_MON`, `MON_AN`, `LICH_SU_GIA_MON`, `CONG_THUC`, `CHI_TIET_CONG_THUC`, `NGUYEN_LIEU`, `NHA_CUNG_CAP`, `BAN`. |
| `apps/api/src/app/modules/sales/models.py` | `ORDER`, `CHI_TIET_ORDER`, `LICH_SU_DOI_BAN`, `HOA_DON`, `GIAO_DICH_THANH_TOAN`, `PHIEU_BEP`. |
| `apps/api/src/app/modules/inventory/models.py` | `PHIEU_NHAP_KHO`, `CHI_TIET_PHIEU_NHAP`, `LO_NGUYEN_LIEU`, `PHIEU_XUAT_KHO`, `CHI_TIET_PHIEU_XUAT`, `PHIEU_KIEM_KE`, `CHI_TIET_KIEM_KE`, `GIAO_DICH_KHO`, `GIA_BINH_QUAN_THANG`. |
| `apps/api/src/app/modules/ai/models.py` | `PHIEN_CHAT_AI`, `TRUY_VAN_AI`. |
| `apps/api/migrations/versions/<rev>_initial_schema.py` | Migration đầu tiên: 29 bảng + index §3.2.3. |
| `db/views/vw_ai_quanly.sql`, `vw_ai_thungan.sql`, `vw_ai_kho.sql` | DDL ba view phân quyền. |
| `db/views/grants.sql.template` | Mẫu `CREATE USER` + `GRANT SELECT`; mật khẩu là placeholder, **không** chứa giá trị thật. |
| `scripts/apply_grants.sh` | Sinh SQL từ template + biến môi trường rồi pipe vào `mysql`; không ghi mật khẩu ra file. |
| `apps/api/tests/schema/test_schema_contract.py` | Kiểm thử ràng buộc lược đồ (§3.2.2) trên metadata. |

## Thứ tự phụ thuộc khi tạo bảng

```
1. VAI_TRO, CAU_HINH_HE_THONG, NGUOI_DUNG, NHAT_KY_HE_THONG
2. NHOM_MON, NGUYEN_LIEU, NHA_CUNG_CAP, BAN
3. MON_AN, LICH_SU_GIA_MON, CONG_THUC, CHI_TIET_CONG_THUC
4. ORDER, CHI_TIET_ORDER, LICH_SU_DOI_BAN, GIAO_DICH_THANH_TOAN, HOA_DON, PHIEU_BEP
5. PHIEU_NHAP_KHO, CHI_TIET_PHIEU_NHAP, LO_NGUYEN_LIEU, PHIEU_XUAT_KHO,
   CHI_TIET_PHIEU_XUAT, PHIEU_KIEM_KE, CHI_TIET_KIEM_KE, GIAO_DICH_KHO, GIA_BINH_QUAN_THANG
6. PHIEN_CHAT_AI, TRUY_VAN_AI
```

`GIAO_DICH_KHO` là bảng duy nhất vượt biên module: nó tham chiếu `CHI_TIET_ORDER` (sales) và
`CHI_TIET_PHIEU_NHAP`/`CHI_TIET_PHIEU_XUAT`/`CHI_TIET_KIEM_KE` (inventory). Model của nó nằm ở
`inventory/models.py` theo nhóm lớp của báo cáo; FK khai báo bằng chuỗi `"CHI_TIET_ORDER.MaChiTietOrder"`
để không phải import chéo module.

## Quy ước vật lý bắt buộc (§3.2.2)

1. **Cột GENERATED**: `MON_AN.TrangThai`, `BAN.TenBan_Active`, `CHI_TIET_KIEM_KE.ChenhLech`.
2. **`BAN.TenBan_Active`** = `IF(DaXoa = 1, NULL, TenBan)` + `UNIQUE`. MySQL cho phép nhiều `NULL`
   trong unique index, nên bàn đã xoá mềm giải phóng tên — đúng ý đồ "cho phép đặt lại tên của một
   bàn đã xóa" ở §3.2.1.
3. **`CHI_TIET_KIEM_KE.ChenhLech`** = `TonThucTe - TonHeThong`.
4. **CHECK constraint** (MySQL 8.0.16+):
   - `ORDER`: `MaBan IS NOT NULL` khi `LoaiDon = 'Tại chỗ'`, `MaBan IS NULL` khi `LoaiDon = 'Mang về'`
     (BR-ORDER-01).
   - `GIAO_DICH_KHO`: `LoaiGiaoDich` phải khớp đúng cột FK chứng từ nguồn — `Nhập` → `MaChiTietNhap`
     khác NULL; `Trừ tự động`/`Hoàn kho` → `MaChiTietOrder` khác NULL; `Xuất thủ công` →
     `MaChiTietXuat` khác NULL; `Điều chỉnh kiểm kê` → `MaChiTietKiemKe` khác NULL.
     `MaLoNguyenLieu` nằm ngoài ràng buộc "đúng một trong bốn" nhưng bắt buộc khác NULL khi
     `LoaiGiaoDich = Nhập`.
5. **`BusinessDate` denormalize** trên `HOA_DON`, `GIAO_DICH_THANH_TOAN`, `GIAO_DICH_KHO`: ghi lúc
   tạo dòng theo cutoff đang áp dụng, **không** suy diễn lại từ `ThoiDiem` khi truy vấn.
6. **Index §3.2.3**: `ORDER(BusinessDate, MaBan)`, `CHI_TIET_ORDER(MaMon, MaOrder)`,
   `GIAO_DICH_KHO(MaNguyenLieu, ThoiDiem)`, `LO_NGUYEN_LIEU(MaNguyenLieu, TrangThai, NgayNhap)`,
   `GIAO_DICH_THANH_TOAN(MaOrder, TrangThai)`, `NGUOI_DUNG(MaVaiTro)`, `NHAT_KY_HE_THONG(ThoiDiem)`,
   `HOA_DON(ThoiDiemXuat)`, `TRUY_VAN_AI(MaPhien, ThoiDiem)`.
7. **`GIA_BINH_QUAN_THANG`**: khoá chính ghép `(MaNguyenLieu, Thang)`, `Thang` lưu `YYYYMM` dạng `INT`.
8. **Naming convention phải có khoá `ck`**: `NAMING_CONVENTION` hiện tại ở `shared/base.py` chỉ có
   `ix`/`uq`/`fk`/`pk`, nên `CheckConstraint` không được đặt tên và SQL sinh ra là `CHECK (...)` trần.
   Thêm `"ck": "ck_%(table_name)s_%(constraint_name)s"` và **đặt tên cho mọi CHECK** khi khai báo
   (`CheckConstraint(..., name="dine_in_needs_a_table")`). Không có bước này thì mọi test lọc
   constraint theo tiền tố `ck_` sẽ nhận tập rỗng và pass một cách vô nghĩa.

## Quyết định cần chốt

| # | Vấn đề | Đề xuất |
| --- | --- | --- |
| 1 | §3.2.1 tả `MON_AN.TrangThai` là cột GENERATED suy từ `AnThuCong`/`HetNLThuCong`/`HetNLTuDong`, nhưng FR-CAT-06/FR-CAT-11 lại nói món mới ở trạng thái **'Nháp'** và chỉ chuyển sang 'Hoạt động'/'Hết nguyên liệu' khi được gán công thức lần đầu. Cột GENERATED chỉ đọc được cột cùng hàng nên **không biểu diễn được 'Nháp'** (phải biết đã có phiên bản `CONG_THUC` hiệu lực hay chưa). | Giữ `TrangThai` là GENERATED với đúng hai giá trị vận hành theo FR-CAT-26 (`Hoạt động` / `Hết nguyên liệu`) cộng giá trị ẩn khi `AnThuCong = 1`; 'Nháp' do **tầng ứng dụng** suy ra = "chưa có `CONG_THUC` hiệu lực", không lưu thành giá trị trong cột. Cách này giữ nguyên báo cáo và không thêm cột ngoài đặc tả. Nếu muốn 'Nháp' nằm hẳn trong cột thì phải bỏ tính GENERATED — nói rõ để tôi đổi. |
| 2 | §3.2.2 yêu cầu thêm `LoDieuChinhKiemKe` cho `LO_NGUYEN_LIEU` (BR-LOT-02) nhưng bảng thuộc tính a21 **không liệt kê cột này**. | Thêm `LoDieuChinhKiemKe TINYINT(1) NOT NULL DEFAULT 0` — BR-LOT-02 không truy vết được nếu thiếu. |
| 3 | §3.2.1 ghi `NHAT_KY_HE_THONG.DuLieuTruoc/DuLieuSau` kiểu `String`, trong khi mã hiện tại (`app/shared/audit.py`) dùng `JSON` và bản báo cáo cũ cũng ghi `JSON`. | Giữ `JSON`: §3.2.1 đã nói rõ cột kiểu ở đó là kiểu mức ngôn ngữ, không phải kiểu vật lý. `JSON` giữ được cấu trúc trước/sau thay vì chuỗi hoá. |

Ba điểm này là **phát hiện khi đối chiếu báo cáo với chính nó**, không phải bất đồng kỹ thuật —
nêu ra để bạn xác nhận, không tự ý sửa báo cáo.

---

## Task 0: Hạ tầng kiểm thử (fixture, dependency, marker)

**Files:**
- Modify: `apps/api/pyproject.toml`
- Modify: `apps/api/src/app/shared/business_date.py` (thêm `now()` — seam duy nhất cho đồng hồ)
- Modify: `apps/api/tests/conftest.py`
- Create: `apps/api/tests/factories.py`
- Create: `apps/api/tests/helpers.py`

**Interfaces:**
- Consumes: `Base.metadata` (Task 1–5 mới đăng ký bảng, nên fixture ở đây phải chịu được metadata rỗng).
- Produces: fixture `engine`, `session`, `session_factory`, `db_session`, `client`, `manager_token`,
  `cashier_token`, `warehouse_token`, `active_user`, `locked_user`, `fake_llm`, `seed_views`,
  `mysql_engine_factory`, `mysql_session_factory`, `freeze_clock` (autouse); `factories.py` (hàm tạo
  dữ liệu dùng chung);
  `helpers.py` (`today`, `tomorrow`, `reload`, `active_recipe`, `active_price`, `counter_for`,
  `audit_count`, `latest_audit`, `monthly_cost_count`, `ingredient_total`…).

**Vì sao task này đứng trước tất cả:** 272 test trong bảy phase sau đều dùng các fixture và helper ở
trên. `tests/conftest.py` hiện chỉ có `client` và `token_for`, nên nếu không dựng tầng này trước thì
bước "Chạy test cho đỏ" ở mọi task sẽ đỏ vì `fixture 'db_session' not found` chứ không phải vì thiếu
code — vòng red→green mất giá trị ngay từ task đầu tiên.

**Ba nhóm phải có đủ, nếu thiếu một nhóm là cả bảy phase sau đứng:**

1. **Fixture CSDL** (`engine`, `session`, `db_session`, `session_factory`, `mysql_*`).
2. **Fixture xác thực** (`client`, `manager_token`, `cashier_token`, `warehouse_token`, `active_user`,
   `locked_user`).
3. **Helper đọc dữ liệu** (`reload`, `active_recipe`, `active_price`, `counter_for`, `audit_count`,
   `latest_audit`, `monthly_cost_count`, `ingredient_total`, `negative_stock_count`…). Đây là nhóm dễ
   bị bỏ sót nhất: test gọi chúng như thể chúng có sẵn, nhưng chúng là **hàm của tầng test**, không
   phải của tầng ứng dụng.

**Đồng hồ phải cắm được, và phải là *một* seam.** Không test nào được gọi `date.today()`/
`datetime.now()`, và **không service nào** được gọi chúng trực tiếp. Thêm vào
`app/shared/business_date.py`:

```python
def now() -> datetime:
    """The single clock seam. Every service reads 'now' through this function, so a
    test can pin it without patching the stdlib."""
    return datetime.now()
```

`business_date_of(now())` là cách duy nhất để biết Business Date hôm nay. Nếu một service gọi
`datetime.now()` trực tiếp, `today()` trong test sẽ **không** khớp với giá trị service tính ra —
`test_the_counter_starts_at_one_for_each_business_date` (Phase 4) sẽ đỏ một cách khó hiểu, và mọi
test quanh Business Date trở thành phụ thuộc đồng hồ thật.

`helpers.py` neo vào một mốc cố định:

```python
FIXED_NOW = datetime(2026, 9, 24, 10, 0)  # a Thursday, inside the business day


def today() -> date:
    return business_date_of(FIXED_NOW)


def tomorrow() -> date:
    return today() + timedelta(days=1)
```

Chỉ hai hàm. `next_business_date` **không** có ở đây — xem ghi chú về va chạm tên bên dưới.

Và `conftest.py` có một fixture **autouse** cắm seam đó cho mọi test (`FIXED_NOW` import từ
`tests/helpers.py`):

```python
@pytest.fixture(autouse=True)
def freeze_clock(monkeypatch):
    """Pin the clock for every test. A suite on the real clock goes red between
    05:59 and 06:01, and again whenever a run crosses midnight."""
    monkeypatch.setattr(business_date, "now", lambda: FIXED_NOW)
```

Vì sao mốc `2026-09-24 10:00`: nó nằm giữa Business Date, cách xa ranh giới 06:00, nên không bao giờ
rơi vào vùng mập mờ. Test nào cần một mốc khác thì `monkeypatch` lại seam này tại chỗ, chứ **không**
gọi đồng hồ thật — vi phạm §4 của quy tắc chung ("no real clock without a controllable seam").

Endpoint nhận `anchor`/`on` trong test luôn truyền mốc lấy từ `today()`/`tomorrow()`; endpoint không
nhận tham số ngày thì đọc `business_date.now()` bên trong.

- [ ] **Step 1: Thêm dependency và cấu hình pytest**

Thêm vào `[dependency-groups] dev` của `apps/api/pyproject.toml`: `aiosqlite>=0.20` (test ràng buộc
`CHECK` trên CSDL tạm) và `asgi-lifespan>=2.1` (chạy app trong test async). Thêm vào
`[tool.pytest.ini_options]`:

```toml
markers = [
    "integration: needs a real MySQL instance (make db-up)",
    "slow: seeds a full year of data; run explicitly, not in the gate",
]
pythonpath = ["../.."]  # so `import data.eval.harness` resolves from tests/
addopts = "-q --strict-markers -m 'not integration and not slow'"
```

Ba việc cùng lúc, và cả ba đều cần:

1. **Đăng ký marker.** Thiếu bước này thì `@pytest.mark.integration` sinh `PytestUnknownMarkWarning`.
2. **`--strict-markers`.** Một marker gõ sai (`@pytest.mark.integraton`) sẽ bị bắt ngay thay vì lặng
   lẽ bỏ qua cả bài test — đúng loại thất bại im lặng mà §4 của quy tắc chung cấm coi là xanh.
3. **`-m 'not integration and not slow'`.** `make gate` không được đòi MySQL đang chạy, cũng không
   được seed 12 tháng dữ liệu. Chạy đầy đủ bằng tay:
   `./.venv/bin/pytest -m integration` (sau `make db-up`) và `./.venv/bin/pytest -m slow`.

`addopts` hiện tại trong `apps/api/pyproject.toml` là `"-q"`; thay bằng dòng trên.

- [ ] **Step 2: Viết test khẳng định fixture chạy được**

```python
def test_the_async_session_fixture_yields_a_working_session(session) -> None:
    assert session is not None


async def test_the_session_can_execute_a_statement(session) -> None:
    result = await session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1


def test_each_role_gets_its_own_token(manager_token, cashier_token, warehouse_token) -> None:
    assert len({manager_token, cashier_token, warehouse_token}) == 3


def test_the_fake_llm_returns_what_it_was_told(fake_llm) -> None:
    fake_llm.reply("SELECT 1")

    assert fake_llm.complete("bất kỳ") == "SELECT 1"
    assert fake_llm.calls == 1


def test_the_fake_llm_replays_a_sequence_then_repeats_the_last(fake_llm) -> None:
    fake_llm.reply_sequence(["a", "b"])

    assert [fake_llm.complete("x") for _ in range(3)] == ["a", "b", "b"]


def test_the_test_clock_is_pinned_to_a_fixed_instant() -> None:
    """A suite on the real clock goes red between 05:59 and 06:01."""
    assert today() == date(2026, 9, 24)
    assert tomorrow() == date(2026, 9, 25)


def test_the_test_clock_is_inside_a_business_day() -> None:
    """The anchor must not sit on the 06:00 boundary, or the date it maps to is ambiguous."""
    assert FIXED_NOW.hour > 6


def test_the_autouse_fixture_pins_the_production_clock() -> None:
    """`freeze_clock` must reach the seam the services actually read."""
    assert business_date.now() == FIXED_NOW
    assert business_date_of(business_date.now()) == today()


async def test_the_two_mysql_fixtures_agree(mysql_engine_factory, mysql_session_factory) -> None:
    """integration: both point at the same DATABASE_URL, or the isolation tests lie."""
    async with mysql_session_factory() as session:
        assert await session.scalar(text("SELECT 1")) == 1
```

- [ ] **Step 3: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/test_conftest.py -v`
Expected: FAIL — `fixture 'session' not found` (và `ModuleNotFoundError: tests.helpers`)

- [ ] **Step 4: Viết `conftest.py` và `factories.py`**

`engine` dựng engine SQLite in-memory **async** (`sqlite+aiosqlite:///:memory:`) và tạo schema từ
`Base.metadata`. Vì SQLite không có `SELECT ... FOR UPDATE` và bỏ qua nhiều `CHECK`, mọi test cần
hành vi MySQL thật phải đánh dấu `@pytest.mark.integration` và dùng `mysql_engine_factory` (đọc
`DATABASE_URL`).

`session` là `AsyncSession` trong một transaction được **rollback** khi hết test — để test không
nhiễm dữ liệu của nhau. `db_session` là alias của `session` cho những test cần truy vấn kiểm chứng
sau khi gọi API.

`freeze_clock` là **autouse**: mọi test đều chạy trên `FIXED_NOW`. Nó `monkeypatch`
`app.shared.business_date.now` — seam mà service đọc — chứ không chỉ sửa helper của tầng test. Thiếu
autouse thì `today()` trong test và Business Date mà service tính ra sẽ là hai giá trị khác nhau.

`fake_llm` là đối tượng ghi lại prompt và trả về kịch bản đã định; nó thoả `LlmClient` của Phase 6
nên Phase 6 chỉ cần `monkeypatch` `get_client` để trả về nó. Khai báo ở đây (không phải Phase 6) vì
Phase 2–5 không dùng, nhưng Phase 6 dùng xuyên suốt và tầng fixture phải nằm một chỗ.

`seed_views` tạo ba view rỗng trên SQLite để test prompt/guard chạy được mà không cần MySQL.

`mysql_session_factory` (khác `mysql_engine_factory`) trả về **session** trên MySQL thật — Phase 3
Task 1 và Phase 0 Task 8 cần nó để mở hai transaction song song và thử khoá dòng. Cả hai fixture đọc
cùng `DATABASE_URL`, nên không có chuyện test cách ly chạy nhầm vào CSDL khác với test khoá dòng.

**`active_user` cần một dòng `VAI_TRO` để trỏ tới**, mà bảng đó mới có model ở Task 1 của phase này
và chưa có hàm seed nào (Phase 1 Task 1 mới thêm `seed_reference_data()`). Nên ở đây `conftest.py`
tự chèn thẳng ba dòng vai trò bằng ORM:

```python
@pytest.fixture
async def active_user(session):
    """A signed-in cashier. Phase 1 Task 1 replaces this direct insert with
    settings.service.seed_reference_data() once that function exists."""
    session.add_all([
        RoleTable(ma_vai_tro=role.value, ten_vai_tro=label) for role, label in ROLE_LABELS.items()
    ])
    await session.flush()
    ...
```

Đây là **ngoại lệ có chủ đích** cho quy tắc "mọi thao tác ghi qua service": tầng test phải tự dựng
được dữ liệu tham chiếu trước khi tầng service của Phase 1 tồn tại. Khi Phase 1 Task 1 xong, sửa
fixture này gọi `seed_reference_data(session)` và xoá phần chèn tay — để hai đường không tồn tại
song song. Ghi việc đó vào Step 0 của Phase 1 Task 1 (đã có).

`helpers.py` gom các hàm đọc dữ liệu mà test dùng ở nhiều phase. Chúng là **hàm thuần đọc**, không
chứa logic nghiệp vụ — nếu một helper bắt đầu có nhánh `if`, nó đã trở thành code sản phẩm và phải
nằm trong `src/`.

Đây là **danh sách đầy đủ** mà bảy phase sau gọi tên; thiếu một hàm là một test không viết được:

| Nhóm | Hàm |
| --- | --- |
| Đồng hồ | `today`, `tomorrow`, `FIXED_NOW` (không có `next_business_date` — trùng tên với hàm ứng dụng) |
| Nạp lại | `reload`, `reload_lot`, `reload_issue_line` |
| Danh mục | `active_recipe`, `active_price`, `display_status`, `pending_price_versions`, `pending_recipe_versions`, `recipe_items` |
| Kho | `ingredient_total`, `lot_total`, `ledger_total`, `lots_for`, `lot_of`, `movements_for`, `negative_stock_count`, `negative_lot_count`, `record_counts`, `monthly_cost_count`, `ingredient_ids` |
| Bán hàng | `counter_for`, `payment_status`, `payment_row`, `order_status`, `line_status`, `invoice_count`, `invoice_business_date`, `payment_business_date`, `order_count`, `order_table`, `order_updated_at`, `tickets_for`, `ticket_by_id`, `rejected_webhook_count` |
| Cài đặt | `audit_count`, `latest_audit`, `role_count`, `role_codes`, `config_count`, `get_config_row` |
| AI | `latest_query`, `session_count` |
| Seed | `ingredient_ids`, `order_status_counts`, `order_count_between`, `lot_cache_mismatch_count`, `ledger_mismatch_count` |

Quy ước: mọi hàm nhận `session` là tham số **đầu tiên**; không hàm nào nhận `client`. Nếu một test
gọi helper không có trong bảng này, đó là helper cần bổ sung vào `helpers.py`, không phải một hàm mới
của tầng ứng dụng.

**Một va chạm tên cần xử lý ngay.** `app.shared.business_date.next_business_date(moment, start_hour)`
đã tồn tại và **nhận tham số**; helper trong test lại không nhận tham số nào. Đừng để hai cái cùng
tên trong một file test.

**Quyết định: bỏ `next_business_date()` khỏi `helpers.py`.** Test Phase 2 dùng `tomorrow()` —
`test_the_default_target_is_the_next_business_date` khẳng định `BusinessDateApDung == tomorrow()`,
đúng nghĩa "Business Date kế tiếp" và không tạo ra cái bẫy hai hàm cùng tên. Nếu sau này cần phân
biệt (ví dụ Business Date kế tiếp của một mốc bất kỳ), gọi thẳng hàm của ứng dụng với tham số.

Sửa ở Phase 2: `assert created.json()["BusinessDateApDung"] == tomorrow().isoformat()`.

Fixture của từng phase nằm ở `apps/api/tests/modules/conftest.py` (Phase 2–6) và
`apps/api/tests/seed/conftest.py` (Phase 7) — **không** dồn hết vào `tests/conftest.py`. Chỉ những
fixture dùng ở ba phase trở lên mới thuộc file gốc; còn lại để gần chỗ dùng.

- [ ] **Step 5: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/test_conftest.py -v`
Expected: PASS. Test `mysql_*` bị `addopts` loại khỏi lượt mặc định; chạy riêng bằng
`./.venv/bin/pytest tests/test_conftest.py -v -m integration` sau `make db-up`, và ghi rõ kết quả
trong báo cáo.

- [ ] **Step 6: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `test(api): add the shared fixture layer and pytest markers`

---

## Task 1: Bảng nhóm Cài đặt + enum dùng chung

**Files:**
- Create: `apps/api/src/app/shared/enums.py`
- Create: `apps/api/src/app/modules/settings/models.py`
- Test: `apps/api/tests/schema/test_settings_models.py`

**Interfaces:**
- Produces: `UserStatus`, `DishStatus`, `OrderStatus`, `OrderLineStatus`, `PaymentStatus`,
  `PrintStatus`, `VersionStatus`, `ChangeType`, `ReceiptStatus`, `LotStatus`, `StocktakeStatus`,
  `StockMovementType`, `WriteOffReason`, `TableStatus`, `AssistantTurnStatus`,
  `StockMovementKind` (StrEnum, giá trị là chuỗi tiếng Việt lưu trong CSDL).
- Produces: `RoleTable`, `User`, `SystemConfig` (SQLAlchemy model).

- [ ] **Step 1: Viết test khẳng định tên bảng và cột**

```python
from app.modules.settings.models import SystemConfig, User
from app.shared.base import NAMING_CONVENTION, Base

# NGUOI_DUNG deliberately has no DaXoa column: accounts are locked, never deleted
# (FR-SET-01), so the soft-delete mixin does not apply here.
EXPECTED = {
    "VAI_TRO": {"MaVaiTro", "TenVaiTro", "MoTa"},
    "NGUOI_DUNG": {"MaNguoiDung", "TenDangNhap", "MatKhauHash", "HoTen",
                   "SoDienThoai", "MaVaiTro", "TrangThai", "NgayTao"},
    "CAU_HINH_HE_THONG": {"MaCauHinh", "TenNhaHang", "DiaChi", "MauHoaDon",
                          "NguongTonMacDinh", "GioBatDauBusinessDate"},
}


def test_table_and_column_names_follow_the_report() -> None:
    for table, columns in EXPECTED.items():
        assert table in Base.metadata.tables
        assert {c.name for c in Base.metadata.tables[table].columns} == columns


def test_user_is_restricted_by_role() -> None:
    fk = next(iter(User.__table__.foreign_keys))
    assert fk.target_fullname == "VAI_TRO.MaVaiTro"
    assert fk.ondelete == "RESTRICT"


def test_check_constraints_get_a_name_from_the_convention() -> None:
    """Without the ck key every CHECK is anonymous and cannot be asserted on."""
    assert "ck" in NAMING_CONVENTION
    assert NAMING_CONVENTION["ck"].startswith("ck_")
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_settings_models.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.settings.models`

- [ ] **Step 3: Viết `enums.py` và `models.py`**

`enums.py`: mỗi trạng thái một `StrEnum`, giá trị là chuỗi tiếng Việt đúng như báo cáo
(`OrderStatus.PENDING_PAYMENT = "Chờ xác nhận thanh toán"`, `LotStatus.EXPIRED = "Hết hạn"`, …).
`models.py`: `RoleTable` (`__tablename__ = "VAI_TRO"`), `User` (`NGUOI_DUNG`, FK `RESTRICT`,
`TrangThai` kiểu `String(20)`), `SystemConfig` (`CAU_HINH_HE_THONG`, singleton,
`GioBatDauBusinessDate` kiểu `Time`).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_settings_models.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu và lint**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: `All checks passed!` và `Success: no issues found`

---

## Task 2: Bảng nhóm Danh mục

**Files:**
- Create: `apps/api/src/app/modules/catalog/models.py`
- Modify: `apps/api/src/app/shared/base.py` (thêm `BusinessDateMixin`)
- Test: `apps/api/tests/schema/test_catalog_models.py`

**Interfaces:**
- Consumes: `User`, `SystemConfig`, các enum ở Task 1.
- Produces: `DishGroup`, `Dish`, `DishPriceVersion`, `Recipe`, `RecipeItem`, `Ingredient`,
  `Supplier`, `DiningTable`.
  `NHOM_MON.ThuTuHienThi` là `int` **không UNIQUE** — `reorder_groups` (Phase 2 Task 1) gán lại 1..n
  trong một transaction, nên giữa chừng có hai nhóm cùng số; `UNIQUE` sẽ làm thao tác đó fail.

- [ ] **Step 1: Viết test cho các ràng buộc đặc thù của nhóm này**

```python
from app.modules.catalog.models import DiningTable, Dish, RecipeItem


def test_dish_status_is_a_generated_column() -> None:
    column = Dish.__table__.c.TrangThai
    assert column.computed is not None
    assert column.computed.persisted is True


def test_table_active_name_frees_the_name_of_a_soft_deleted_table() -> None:
    column = DiningTable.__table__.c.TenBan_Active
    assert column.computed is not None
    assert "DaXoa" in str(column.computed.sqltext)


def test_recipe_items_carry_no_unit_of_their_own() -> None:
    """§3.2.2: the unit is always derived from NGUYEN_LIEU.DonViTinh."""
    assert "DonViTinh" not in {c.name for c in RecipeItem.__table__.columns}


def test_recipe_item_primary_key_is_composite() -> None:
    assert {c.name for c in RecipeItem.__table__.primary_key} == {"MaCongThuc", "MaNguyenLieu"}
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_catalog_models.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.catalog.models`

- [ ] **Step 3: Viết `models.py` theo đặc tả a5–a12**

Điểm bắt buộc: `MON_AN.TrangThai` là `Computed(...)` persisted với ba giá trị như Quyết định #1;
`BAN.TenBan_Active` là `Computed("IF(DaXoa = 1, NULL, TenBan)")` + `unique=True`;
`CHI_TIET_CONG_THUC` khoá chính ghép `(MaCongThuc, MaNguyenLieu)`, FK `MaCongThuc` dùng `CASCADE`;
`NGUYEN_LIEU` có `SoLuongTon`, `Version`, `DaKhoaDonVi`, `MucTonToiThieu`, `SoNgayBaoQuan` với
`CHECK` cho `SoLuongTon >= 0` và `MucTonToiThieu >= 0`; `LICH_SU_GIA_MON`/`CONG_THUC` có
`BusinessDateApDung`, `ThoiDiemHieuLuc`, `ThoiDiemHetHieuLuc`, `LoaiThayDoi`, `TrangThai`,
`NguoiTao` (`RESTRICT`).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_catalog_models.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu và lint**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh

---

## Task 3: Bảng nhóm Bán hàng

**Files:**
- Create: `apps/api/src/app/modules/sales/models.py`
- Test: `apps/api/tests/schema/test_sales_models.py`

**Interfaces:**
- Consumes: `DiningTable`, `Dish`, `DishPriceVersion`, `Recipe`, `User`.
- Produces: `Order`, `OrderLine`, `TableMoveLog`, `Invoice`, `PaymentTransaction`, `KitchenTicket`.

- [ ] **Step 1: Viết test cho BR-ORDER-01 và `BusinessDate` denormalize**

```python
import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.sales.models import Invoice, Order


def test_takeaway_order_must_not_carry_a_table() -> None:
    checks = {c.name: str(c.sqltext) for c in Order.__table__.constraints
              if c.name and c.name.startswith("ck_")}
    joined = " ".join(checks.values())
    assert "MaBan" in joined and "Mang về" in joined


def test_invoice_copies_the_business_date() -> None:
    assert "BusinessDate" in {c.name for c in Invoice.__table__.columns}


def test_order_lines_reference_a_price_and_a_recipe_version() -> None:
    columns = {c.name for c in Order.__table__.columns}
    assert {"BusinessDate", "MaBan", "LoaiDon", "TrangThai", "NguoiTao"} <= columns
```

Kèm một test hành vi trên SQLite in-memory (dùng `aiosqlite`) khẳng định chèn order "Tại chỗ"
không có `MaBan` thì `IntegrityError`. SQLite **có** thực thi `CHECK` (đã kiểm chứng bằng
`sqlite3` cục bộ), nên test này chạy được trong `session` mặc định; nhưng `IntegrityError` của
SQLAlchemy chỉ ném ra ở `flush()`, nên test phải `await session.flush()` trong `pytest.raises` chứ
không chỉ `session.add()`.

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_sales_models.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.sales.models`

- [ ] **Step 3: Viết `models.py` theo đặc tả a13–a18**

`CHI_TIET_ORDER` FK tới `LICH_SU_GIA_MON` và `CONG_THUC` đều `RESTRICT`;
`HOA_DON.MaOrder` là `unique=True`; `PHIEU_BEP`, `LICH_SU_DOI_BAN`, `CHI_TIET_ORDER` theo `ORDER`
dùng `CASCADE`; `LICH_SU_DOI_BAN` có hai FK tới `BAN` (`MaBanNguon`, `MaBanDich`) nên phải đặt
`foreign_keys=` tường minh trên relationship; `GIAO_DICH_THANH_TOAN` và `HOA_DON` có cột
`BusinessDate` (Quy ước #5).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_sales_models.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu và lint**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh

---

## Task 4: Bảng nhóm Kho

**Files:**
- Create: `apps/api/src/app/modules/inventory/models.py`
- Test: `apps/api/tests/schema/test_inventory_models.py`

**Interfaces:**
- Consumes: `Ingredient`, `Supplier`, `OrderLine`, `User`.
- Produces: `GoodsReceipt`, `GoodsReceiptLine`, `IngredientLot`, `StockIssue`, `StockIssueLine`,
  `Stocktake`, `StocktakeLine`, `StockMovement`, `MonthlyAverageCost`.

- [ ] **Step 1: Viết test cho các ràng buộc phức tạp nhất**

```python
from app.modules.inventory.models import IngredientLot, StockMovement, StocktakeLine


def test_stocktake_difference_is_generated() -> None:
    column = StocktakeLine.__table__.c.ChenhLech
    assert column.computed is not None
    assert "TonThucTe" in str(column.computed.sqltext)


def test_movement_must_name_the_source_document_matching_its_kind() -> None:
    checks = [str(c.sqltext) for c in StockMovement.__table__.constraints
              if c.name and c.name.startswith("ck_")]
    joined = " ".join(checks)
    for column in ("MaChiTietNhap", "MaChiTietOrder", "MaChiTietXuat", "MaChiTietKiemKe"):
        assert column in joined


def test_every_movement_carries_the_business_date() -> None:
    assert "BusinessDate" in {c.name for c in StockMovement.__table__.columns}


def test_lot_can_be_flagged_as_a_stocktake_adjustment() -> None:
    assert "LoDieuChinhKiemKe" in {c.name for c in IngredientLot.__table__.columns}


def test_one_lot_per_receipt_line() -> None:
    assert IngredientLot.__table__.c.MaChiTietNhap.unique is True


def test_monthly_cost_is_keyed_by_ingredient_and_month() -> None:
    from app.modules.inventory.models import MonthlyAverageCost
    assert {c.name for c in MonthlyAverageCost.__table__.primary_key} == {
        "MaNguyenLieu", "Thang"
    }
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_inventory_models.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.inventory.models`

- [ ] **Step 3: Viết `models.py` theo đặc tả a19–a27**

Điểm bắt buộc: `LO_NGUYEN_LIEU.MaChiTietNhap` `unique=True` (1–1 với dòng nhập) và `RESTRICT`;
`GIAO_DICH_KHO` có bốn FK rời rạc đều nullable + `RESTRICT`, `MaLoNguyenLieu` nullable + `RESTRICT`,
`NguoiThucHien` nullable + `RESTRICT`, cột `BusinessDate`; `CHI_TIET_PHIEU_XUAT.GiaVonUocTinh`
`default=0`; `GIA_BINH_QUAN_THANG` khoá chính ghép; `CHI_TIET_KIEM_KE.ChenhLech` là `Computed`.
FK chéo module tới `CHI_TIET_ORDER` khai báo bằng chuỗi.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_inventory_models.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu và lint**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh

---

## Task 5: Bảng nhóm AI + migration đầu tiên

**Files:**
- Create: `apps/api/src/app/modules/ai/models.py`
- Modify: `apps/api/migrations/env.py` (import mọi model để đăng ký metadata)
- Create: `apps/api/migrations/versions/<rev>_initial_schema.py`
- Test: `apps/api/tests/schema/test_schema_contract.py`

**Interfaces:**
- Consumes: toàn bộ model ở Task 1–4.
- Produces: `ChatSession`, `AssistantQuery`.

- [ ] **Step 1: Viết test khẳng định đủ 29 bảng và index §3.2.3**

```python
from app.shared.base import Base

EXPECTED_TABLES = {
    "VAI_TRO", "NGUOI_DUNG", "CAU_HINH_HE_THONG", "NHAT_KY_HE_THONG",
    "NHOM_MON", "MON_AN", "LICH_SU_GIA_MON", "CONG_THUC", "CHI_TIET_CONG_THUC",
    "NGUYEN_LIEU", "NHA_CUNG_CAP", "BAN",
    "ORDER", "CHI_TIET_ORDER", "LICH_SU_DOI_BAN", "HOA_DON",
    "GIAO_DICH_THANH_TOAN", "PHIEU_BEP",
    "PHIEU_NHAP_KHO", "CHI_TIET_PHIEU_NHAP", "LO_NGUYEN_LIEU", "PHIEU_XUAT_KHO",
    "CHI_TIET_PHIEU_XUAT", "PHIEU_KIEM_KE", "CHI_TIET_KIEM_KE", "GIAO_DICH_KHO",
    "GIA_BINH_QUAN_THANG", "PHIEN_CHAT_AI", "TRUY_VAN_AI",
}

EXPECTED_INDEXES = {
    ("ORDER", ("BusinessDate", "MaBan")),
    ("CHI_TIET_ORDER", ("MaMon", "MaOrder")),
    ("GIAO_DICH_KHO", ("MaNguyenLieu", "ThoiDiem")),
    ("LO_NGUYEN_LIEU", ("MaNguyenLieu", "TrangThai", "NgayNhap")),
    ("GIAO_DICH_THANH_TOAN", ("MaOrder", "TrangThai")),
    ("NGUOI_DUNG", ("MaVaiTro",)),
    ("NHAT_KY_HE_THONG", ("ThoiDiem",)),
    ("HOA_DON", ("ThoiDiemXuat",)),
    ("TRUY_VAN_AI", ("MaPhien", "ThoiDiem")),
}


def test_the_schema_has_exactly_the_29_tables_of_the_report() -> None:
    """Phase 4 Task 1 adds DEM_ORDER (the order-number counter) to this set — it is
    not in the report, so it is not listed here until that task lands."""
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_the_index_strategy_of_section_3_2_3_is_present() -> None:
    for table, columns in EXPECTED_INDEXES:
        indexes = Base.metadata.tables[table].indexes
        assert any(tuple(c.name for c in index.columns) == columns for index in indexes), table
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_schema_contract.py -v`
Expected: FAIL — `PHIEN_CHAT_AI` chưa có trong metadata

- [ ] **Step 3: Viết `ai/models.py`, cập nhật `migrations/env.py`, sinh migration**

`TRUY_VAN_AI` có `PhamViDuLieu`, `CauHoi`, `CauSQLSinhRa`, `TrangThai`, `KetQuaTomTat`,
`ThoiGianPhanHoi`, `ThoiDiem`; FK `MaPhien` dùng `CASCADE`.
`env.py` phải import cả bảy module model (kể cả `app.modules.settings.models`) để autogenerate
nhìn thấy đủ bảng.

Run: `cd apps/api && ./.venv/bin/alembic revision --autogenerate -m "initial schema"`
Sau đó **đọc lại file sinh ra** và bổ sung thủ công những gì autogenerate bỏ sót: `CHECK` constraint,
cột `Computed`, `ON DELETE`/`ON UPDATE`, index composite.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest -v`
Expected: toàn bộ test PASS

- [ ] **Step 5: Kiểm tra kiểu, lint và build**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh

---

## Task 6: Chạy migration thật trên MySQL 8.4

**Files:**
- Modify: `apps/api/migrations/versions/<rev>_initial_schema.py` (sửa lỗi phát hiện khi chạy thật)

**Interfaces:**
- Consumes: migration ở Task 5.
- Produces: CSDL `restaurant` đúng lược đồ — điều kiện để Task 7 chạy được.

- [ ] **Step 1: Bật MySQL và tạo `.env`**

Run: `make db-up && make env`
Expected: container `restaurant-db` healthy.

- [ ] **Step 2: Áp migration**

Run: `make migrate`
Expected: `Running upgrade -> <rev>, initial schema`, không lỗi.

- [ ] **Step 3: Kiểm chứng lược đồ đã tạo đúng**

Run: `docker compose exec db mysql -urestaurant -prestaurant restaurant -e "SHOW TABLES; SHOW CREATE TABLE GIAO_DICH_KHO\G"`
Expected: 29 bảng; `GIAO_DICH_KHO` có bốn FK rời rạc, CHECK, và cột `BusinessDate`.

- [ ] **Step 4: Chạy lại test trên CSDL thật**

Run: `cd apps/api && ./.venv/bin/pytest -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra downgrade rồi upgrade lại**

Run: `cd apps/api && ./.venv/bin/alembic downgrade base && ./.venv/bin/alembic upgrade head`
Expected: cả hai chiều chạy sạch — migration lùi được là điều kiện để không mắc kẹt sau này.

---

## Task 7: Ba view phân quyền + ba tài khoản chỉ-đọc

**Files:**
- Create: `db/views/vw_ai_quanly.sql`, `db/views/vw_ai_thungan.sql`, `db/views/vw_ai_kho.sql`
- Create: `db/views/grants.sql.template`
- Create: `scripts/apply_grants.sh`
- Modify: `db/views/README.md` (ghi cách chạy)
- Test: `apps/api/tests/schema/test_ai_views.py` (đánh dấu `integration`, cần MySQL)

**Interfaces:**
- Consumes: lược đồ ở Task 6, `app.modules.ai.scope.ROLE_VIEWS`, `app.modules.ai.accounts`.
- Produces: ba view + ba tài khoản, khớp đúng `views_for(role)`.

- [ ] **Step 1: Viết test khẳng định view chỉ chứa bảng thuộc phạm vi vai trò (NFR-12)**

Test đọc `information_schema.view_table_usage` và khẳng định:
`vw_ai_thungan` không tham chiếu bảng nào thuộc nhóm kho (`NGUYEN_LIEU`, `LO_NGUYEN_LIEU`,
`GIAO_DICH_KHO`, `GIA_BINH_QUAN_THANG`, `PHIEU_*`);
`vw_ai_kho` không tham chiếu `HOA_DON`, `GIAO_DICH_THANH_TOAN`, `GIA_BINH_QUAN_THANG`;
cả ba không chứa cột `GiaVonUocTinh` khi vai trò không được xem giá vốn.

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_ai_views.py -v`
Expected: FAIL — view chưa tồn tại

- [ ] **Step 3: Viết DDL view và grants**

Ba file `.sql` tạo view **chữ thường** (`vw_ai_*`) đúng như `scope.py`.

**Không commit mật khẩu tài khoản CSDL.** §0 và §5 của quy tắc chung cấm commit credential, nên
`db/views/grants.sql` **không tồn tại** dưới dạng file có mật khẩu thật. Thay vào đó:

`db/views/grants.sql.template` — placeholder, commit được:

```sql
-- Rendered by scripts/apply_grants.sh; the passwords never touch a file on disk.
CREATE USER IF NOT EXISTS 'ai_manager'@'%' IDENTIFIED BY '__AI_READONLY_PASSWORD_MANAGER__';
CREATE USER IF NOT EXISTS 'ai_cashier'@'%' IDENTIFIED BY '__AI_READONLY_PASSWORD_CASHIER__';
CREATE USER IF NOT EXISTS 'ai_warehouse'@'%' IDENTIFIED BY '__AI_READONLY_PASSWORD_WAREHOUSE__';

GRANT SELECT ON restaurant.vw_ai_quanly TO 'ai_manager'@'%';
GRANT SELECT ON restaurant.vw_ai_thungan TO 'ai_cashier'@'%';
GRANT SELECT ON restaurant.vw_ai_kho TO 'ai_warehouse'@'%';

-- Belt and braces: the account must not reach anything else, now or later.
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'ai_manager'@'%';
GRANT SELECT ON restaurant.vw_ai_quanly TO 'ai_manager'@'%';
```

`scripts/apply_grants.sh` đọc ba biến môi trường `AI_READONLY_PASSWORD_MANAGER` / `_CASHIER` /
`_WAREHOUSE`, thay vào template bằng `sed` trong ống dẫn, rồi pipe thẳng vào `mysql`:

```bash
#!/usr/bin/env bash
# Applies the view grants without ever writing a password to disk.
set -euo pipefail

: "${AI_READONLY_PASSWORD_MANAGER:?set this in your shell profile}"
: "${AI_READONLY_PASSWORD_CASHIER:?set this in your shell profile}"
: "${AI_READONLY_PASSWORD_WAREHOUSE:?set this in your shell profile}"

for view in db/views/vw_ai_quanly.sql db/views/vw_ai_thungan.sql db/views/vw_ai_kho.sql; do
  docker compose exec -T db mysql -uroot -p"$MYSQL_ROOT_PASSWORD" restaurant < "$view"
done

sed -e "s|__AI_READONLY_PASSWORD_MANAGER__|$AI_READONLY_PASSWORD_MANAGER|" \
    -e "s|__AI_READONLY_PASSWORD_CASHIER__|$AI_READONLY_PASSWORD_CASHIER|" \
    -e "s|__AI_READONLY_PASSWORD_WAREHOUSE__|$AI_READONLY_PASSWORD_WAREHOUSE|" \
    db/views/grants.sql.template \
  | docker compose exec -T db mysql -uroot -p"$MYSQL_ROOT_PASSWORD" restaurant
```

Ba biến này khai báo trong shell profile (không nằm trong repo), và **cùng giá trị** phải điền vào
`AI_READONLY_URL_*` của `.env` để tầng ứng dụng đăng nhập được bằng chúng.

- [ ] **Step 4: Áp view và grants**

Run: `./scripts/apply_grants.sh`
Expected: không lỗi. Nếu script báo `set this in your shell profile`, đặt ba biến rồi chạy lại — không
điền giá trị vào file trong repo.

- [ ] **Step 5: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_ai_views.py -v`
Expected: PASS

- [ ] **Step 6: Kiểm chứng cách ly bằng tay**

Run: `docker compose exec db mysql -uai_cashier -p"$AI_READONLY_PASSWORD_CASHIER" restaurant -e "SELECT COUNT(*) FROM vw_ai_kho"`
Expected: `SELECT command denied` — chứng minh tài khoản của Thu ngân không chạm được view của Kho.

---

## Task 8: Kiểm chứng cách ly end-to-end và chốt gate

**Files:**
- Test: `apps/api/tests/schema/test_ai_isolation.py` (đánh dấu `integration`, cần MySQL)

**Interfaces:**
- Consumes: ba view và ba tài khoản ở Task 7, `app.modules.ai.accounts`.
- Produces: bằng chứng cách ly ba lớp (prompt · guard · `GRANT`) chạy được trên CSDL thật.

Task này **không** viết `executor.py` — bước thực thi SQL thuộc Phase 6 Task 3, nơi có đủ ngữ cảnh về
hạn mức, timeout và vòng thử lại. Ở đây chỉ chứng minh lớp cách ly dữ liệu đã đúng.

**NFR-12 (tách biệt tập view AI khỏi bảng lõi)** có ba lớp, và phase này chứng minh hai lớp ngoài:
view chỉ được `SELECT` từ bảng lõi (Task 7 Step 1, đọc `information_schema.view_table_usage`) và
`GRANT` không cho tài khoản vai trò chạm bảng lõi (Task 8). Lớp thứ ba — prompt chỉ chứa đúng một
view — thuộc Phase 6 Task 1. Ba lớp độc lập nhau: hỏng một lớp thì hai lớp còn lại vẫn chặn.

- [ ] **Step 1: Viết test cách ly ba lớp**

```python
async def test_a_role_account_cannot_read_another_roles_view(mysql_engine_factory) -> None:
    """NFR-06: the GRANT is the outer layer, independent of the guard."""
    engine = mysql_engine_factory(accounts.readonly_url_for(Role.CASHIER))

    with pytest.raises(OperationalError, match="denied"):
        await run(engine, "SELECT COUNT(*) FROM vw_ai_kho")


async def test_a_role_account_cannot_read_the_core_tables(mysql_engine_factory) -> None:
    engine = mysql_engine_factory(accounts.readonly_url_for(Role.MANAGER))

    with pytest.raises(OperationalError, match="denied"):
        await run(engine, "SELECT COUNT(*) FROM NGUOI_DUNG")


async def test_a_role_account_cannot_write_anything(mysql_engine_factory) -> None:
    engine = mysql_engine_factory(accounts.readonly_url_for(Role.MANAGER))

    for statement in ("INSERT INTO vw_ai_quanly VALUES (1)", "DROP VIEW vw_ai_quanly"):
        with pytest.raises(OperationalError, match="denied"):
            await run(engine, statement)


async def test_every_role_account_can_read_its_own_view(mysql_engine_factory) -> None:
    for role, view in ROLE_VIEWS.items():
        engine = mysql_engine_factory(accounts.readonly_url_for(role))
        assert await run(engine, f"SELECT COUNT(*) FROM {view}") is not None
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_ai_isolation.py -v`
Expected: FAIL nếu grants chưa áp, hoặc PASS nếu Task 7 đã xong — ghi lại kết quả thực tế.

- [ ] **Step 3: Áp view và grants nếu chưa**

Run: `./scripts/apply_grants.sh`
Expected: không lỗi.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_ai_isolation.py -v`
Expected: PASS

- [ ] **Step 5: Chạy cổng kiểm tra đầy đủ**

Run: `UV_CACHE_DIR=/tmp/uv-cache make gate`
Expected: xanh cả bốn cổng (format · lint · typecheck · test · build). Nếu cổng báo **unfinished**
do chạm `GATE_BUDGET`, chạy lại bằng tay và nói rõ — không coi unfinished là xanh.

---

## Kiểm chứng

| Cổng | Lệnh | Kỳ vọng |
| --- | --- | --- |
| Lược đồ đủ 29 bảng | `pytest tests/schema/` | xanh |
| Index §3.2.3 | `pytest tests/schema/test_schema_contract.py` | xanh |
| Migration hai chiều | `alembic downgrade base && alembic upgrade head` | sạch |
| Cách ly view | `pytest tests/schema/test_ai_views.py` | xanh |
| Cách ly ba lớp (view · guard · GRANT) | `pytest tests/schema/test_ai_isolation.py` | xanh |
| Toàn bộ | `make gate` | xanh |

## Rủi ro

- **Autogenerate không sinh `CHECK`/`Computed`/`ON DELETE`**: Alembic bỏ qua những thứ này. Phải soát
  tay file migration; test ở Task 5 chỉ kiểm tra metadata, nên Task 6 chạy trên MySQL thật mới là
  cổng kiểm chứng thực sự.
- **`CHECK` và `IntegrityError` trên SQLite**: SQLite thực thi `CHECK`, nhưng `IntegrityError` chỉ
  ném ra ở `flush()`/`commit()`, không phải ở `session.add()`. Nếu một test ràng buộc "pass" mà không
  hề flush, nó đang pass rỗng. Task 6 vẫn là cổng kiểm chứng thật vì `ON DELETE`/`Computed` chỉ đúng
  trên MySQL.
- **`Computed` + `UNIQUE` cho `TenBan_Active`**: chỉ đúng nếu MySQL coi nhiều `NULL` là hợp lệ trong
  unique index (đúng với InnoDB) — Task 6 kiểm chứng bằng `SHOW CREATE TABLE`.
- **Thứ tự tạo bảng**: `GIAO_DICH_KHO` tham chiếu chéo sales/inventory; nếu migration lỗi thứ tự,
  tách thành hai revision (sales trước, inventory sau) thay vì thêm `use_alter`.
- **Prompt của trợ lý AI phụ thuộc lược đồ**: chỉ triển khai `prompt.py` sau khi Task 6 xong.
- **`executor.py` không thuộc phase này**: bước thực thi SQL cần hạn mức, timeout và vòng thử lại —
  để nguyên ở Phase 6 Task 3. Phase 0 chỉ chứng minh lớp `GRANT` đã đúng.
- **Mật khẩu tài khoản chỉ-đọc không được vào repo.** `grants.sql.template` chỉ chứa placeholder;
  `scripts/apply_grants.sh` thay bằng biến môi trường trong ống dẫn. Đừng "cho tiện" mà render ra
  `grants.sql` rồi commit — §0 của quy tắc chung cấm commit credential, và hook pre-commit sẽ chặn.
