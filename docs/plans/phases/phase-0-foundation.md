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
| `apps/api/src/app/shared/base.py` | Đã có: `Base`, naming convention, `CreatedAtMixin`, `SoftDeleteMixin`. Bổ sung mixin `BusinessDateMixin`. |
| `apps/api/src/app/modules/settings/models.py` | `VAI_TRO`, `NGUOI_DUNG`, `CAU_HINH_HE_THONG`. |
| `apps/api/src/app/shared/audit.py` | Đã có `NHAT_KY_HE_THONG`; chỉnh kiểu cột theo quyết định #3. |
| `apps/api/src/app/modules/catalog/models.py` | `NHOM_MON`, `MON_AN`, `LICH_SU_GIA_MON`, `CONG_THUC`, `CHI_TIET_CONG_THUC`, `NGUYEN_LIEU`, `NHA_CUNG_CAP`, `BAN`. |
| `apps/api/src/app/modules/sales/models.py` | `ORDER`, `CHI_TIET_ORDER`, `LICH_SU_DOI_BAN`, `HOA_DON`, `GIAO_DICH_THANH_TOAN`, `PHIEU_BEP`. |
| `apps/api/src/app/modules/inventory/models.py` | `PHIEU_NHAP_KHO`, `CHI_TIET_PHIEU_NHAP`, `LO_NGUYEN_LIEU`, `PHIEU_XUAT_KHO`, `CHI_TIET_PHIEU_XUAT`, `PHIEU_KIEM_KE`, `CHI_TIET_KIEM_KE`, `GIAO_DICH_KHO`, `GIA_BINH_QUAN_THANG`. |
| `apps/api/src/app/modules/ai/models.py` | `PHIEN_CHAT_AI`, `TRUY_VAN_AI`. |
| `apps/api/migrations/versions/<rev>_initial_schema.py` | Migration đầu tiên: 29 bảng + index §3.2.3. |
| `db/views/vw_ai_quanly.sql`, `vw_ai_thungan.sql`, `vw_ai_kho.sql` | DDL ba view phân quyền. |
| `db/views/grants.sql` | Tạo ba tài khoản chỉ-đọc + `GRANT SELECT` trên đúng view của mình. |
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

## Quyết định cần chốt

| # | Vấn đề | Đề xuất |
| --- | --- | --- |
| 1 | §3.2.1 tả `MON_AN.TrangThai` là cột GENERATED suy từ `AnThuCong`/`HetNLThuCong`/`HetNLTuDong`, nhưng FR-CAT-06/FR-CAT-11 lại nói món mới ở trạng thái **'Nháp'** và chỉ chuyển sang 'Hoạt động'/'Hết nguyên liệu' khi được gán công thức lần đầu. Cột GENERATED chỉ đọc được cột cùng hàng nên **không biểu diễn được 'Nháp'** (phải biết đã có phiên bản `CONG_THUC` hiệu lực hay chưa). | Giữ `TrangThai` là GENERATED với đúng hai giá trị vận hành theo FR-CAT-26 (`Hoạt động` / `Hết nguyên liệu`) cộng giá trị ẩn khi `AnThuCong = 1`; 'Nháp' do **tầng ứng dụng** suy ra = "chưa có `CONG_THUC` hiệu lực", không lưu thành giá trị trong cột. Cách này giữ nguyên báo cáo và không thêm cột ngoài đặc tả. Nếu muốn 'Nháp' nằm hẳn trong cột thì phải bỏ tính GENERATED — nói rõ để tôi đổi. |
| 2 | §3.2.2 yêu cầu thêm `LoDieuChinhKiemKe` cho `LO_NGUYEN_LIEU` (BR-LOT-02) nhưng bảng thuộc tính a21 **không liệt kê cột này**. | Thêm `LoDieuChinhKiemKe TINYINT(1) NOT NULL DEFAULT 0` — BR-LOT-02 không truy vết được nếu thiếu. |
| 3 | §3.2.1 ghi `NHAT_KY_HE_THONG.DuLieuTruoc/DuLieuSau` kiểu `String`, trong khi mã hiện tại (`app/shared/audit.py`) dùng `JSON` và bản báo cáo cũ cũng ghi `JSON`. | Giữ `JSON`: §3.2.1 đã nói rõ cột kiểu ở đó là kiểu mức ngôn ngữ, không phải kiểu vật lý. `JSON` giữ được cấu trúc trước/sau thay vì chuỗi hoá. |

Ba điểm này là **phát hiện khi đối chiếu báo cáo với chính nó**, không phải bất đồng kỹ thuật —
nêu ra để bạn xác nhận, không tự ý sửa báo cáo.

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
from app.shared.base import Base

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
không có `MaBan` thì `IntegrityError`. Nếu `CHECK` không chạy được trên SQLite, chuyển test này
sang đánh dấu `@pytest.mark.integration` và chạy trên MySQL ở Task 6.

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
- Create: `db/views/grants.sql`
- Modify: `db/views/README.md` (ghi cách chạy)
- Test: `apps/api/tests/schema/test_ai_views.py` (đánh dấu `integration`, cần MySQL)

**Interfaces:**
- Consumes: lược đồ ở Task 6, `app.modules.ai.scope.ROLE_VIEWS`, `app.modules.ai.accounts`.
- Produces: ba view + ba tài khoản, khớp đúng `views_for(role)`.

- [ ] **Step 1: Viết test khẳng định view chỉ chứa bảng thuộc phạm vi vai trò**

Test đọc `information_schema.view_table_usage` và khẳng định:
`vw_ai_thungan` không tham chiếu bảng nào thuộc nhóm kho (`NGUYEN_LIEU`, `LO_NGUYEN_LIEU`,
`GIAO_DICH_KHO`, `GIA_BINH_QUAN_THANG`, `PHIEU_*`);
`vw_ai_kho` không tham chiếu `HOA_DON`, `GIAO_DICH_THANH_TOAN`, `GIA_BINH_QUAN_THANG`;
cả ba không chứa cột `GiaVonUocTinh` khi vai trò không được xem giá vốn.

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_ai_views.py -v`
Expected: FAIL — view chưa tồn tại

- [ ] **Step 3: Viết DDL view và grants**

Ba file `.sql` tạo view **chữ thường** (`vw_ai_*`) đúng như `scope.py`; `grants.sql` tạo ba user
`ai_manager` / `ai_cashier` / `ai_warehouse` và `GRANT SELECT` trên **đúng một view** mỗi user —
không dùng chung tài khoản (NFR-06).

- [ ] **Step 4: Áp view và grants**

Run: `docker compose exec -T db mysql -uroot -prestaurant-root restaurant < db/views/vw_ai_quanly.sql`
(lặp lại cho hai view còn lại và `grants.sql`)
Expected: không lỗi.

- [ ] **Step 5: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/schema/test_ai_views.py -v`
Expected: PASS

- [ ] **Step 6: Kiểm chứng cách ly bằng tay**

Run: `docker compose exec db mysql -uai_cashier -p<pass> restaurant -e "SELECT COUNT(*) FROM vw_ai_kho"`
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
Expected: FAIL nếu `grants.sql` chưa áp, hoặc PASS nếu Task 7 đã xong — ghi lại kết quả thực tế.

- [ ] **Step 3: Áp view và grants nếu chưa**

Run: `for f in db/views/vw_ai_*.sql db/views/grants.sql; do docker compose exec -T db mysql -uroot -p*** restaurant < "$f"; done`
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
- **`CHECK` không chạy trên SQLite**: test hành vi của BR-ORDER-01 phải chạy trên MySQL.
- **`Computed` + `UNIQUE` cho `TenBan_Active`**: chỉ đúng nếu MySQL coi nhiều `NULL` là hợp lệ trong
  unique index (đúng với InnoDB) — Task 6 kiểm chứng bằng `SHOW CREATE TABLE`.
- **Thứ tự tạo bảng**: `GIAO_DICH_KHO` tham chiếu chéo sales/inventory; nếu migration lỗi thứ tự,
  tách thành hai revision (sales trước, inventory sau) thay vì thêm `use_alter`.
- **Prompt của trợ lý AI phụ thuộc lược đồ**: chỉ triển khai `prompt.py` sau khi Task 6 xong.
- **`executor.py` không thuộc phase này**: bước thực thi SQL cần hạn mức, timeout và vòng thử lại —
  để nguyên ở Phase 6 Task 3. Phase 0 chỉ chứng minh lớp `GRANT` đã đúng.
