# Phase 0 — Bằng chứng nghiệm thu MySQL 8.4

> Ngày: 2026-09-24 · Máy: Apple M4 Pro 24GB/12 CPU · MySQL 8.4 (docker `restaurant-db` healthy)
> Migration: `890db4fbb8b6` (op.create_table tường minh, generate từ `--autogenerate` trên MySQL thật)
> Lệnh: `make db-up && make migrate && ./scripts/apply_grants.sh`

## 1. Migration

```
INFO [alembic.runtime.migration] Running upgrade  -> 890db4fbb8b6, initial schema
```

- `alembic downgrade base` → chỉ còn `alembic_version` (0 bảng), `alembic upgrade head` → 29 bảng, chạy lại sạch.
- `001_initial_schema (create_all)` đã xóa, thay bằng `890db4fbb8b6` (op.create_table + op.create_index, downgrade chỉ op.drop_table ngược thứ tự).

## 2. SHOW TABLES (29 bảng)

```
BAN, CAU_HINH_HE_THONG, CHI_TIET_CONG_THUC, CHI_TIET_KIEM_KE, CHI_TIET_ORDER,
CHI_TIET_PHIEU_NHAP, CHI_TIET_PHIEU_XUAT, CONG_THUC, GIAO_DICH_KHO, GIAO_DICH_THANH_TOAN,
GIA_BINH_QUAN_THANG, HOA_DON, LICH_SU_DOI_BAN, LICH_SU_GIA_MON, LO_NGUYEN_LIEU, MON_AN,
NGUOI_DUNG, NGUYEN_LIEU, NHAT_KY_HE_THONG, NHA_CUNG_CAP, NHOM_MON, ORDER, PHIEN_CHAT_AI,
PHIEU_BEP, PHIEU_KIEM_KE, PHIEU_NHAP_KHO, PHIEU_XUAT_KHO, TRUY_VAN_AI, VAI_TRO
+ alembic_version + 3 views
```

## 3. SHOW CREATE TABLE (trích)

### BAN — TenBan_Active generated + UNIQUE (B3: IF → CASE)

```sql
CREATE TABLE `BAN` (
  `MaBan` bigint NOT NULL AUTO_INCREMENT,
  `TenBan` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `DaXoa` tinyint(1) NOT NULL,
  `TenBan_Active` varchar(50) COLLATE utf8mb4_unicode_ci
    GENERATED ALWAYS AS ((case when (`DaXoa` = 1) then NULL else `TenBan` end)) STORED,
  PRIMARY KEY (`MaBan`),
  UNIQUE KEY `uq_BAN_TenBan_Active` (`TenBan_Active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

Kiểm chứng: `INSERT BAN ('Ban 1',0)` + `INSERT BAN ('Ban 1',1)` → 2 rows (`Ban 1` / `NULL`), `INSERT BAN ('Ban 1',0)` lần 2 → `1062 Duplicate entry 'Ban 1'` (DaXoa=1 cho phép trùng tên, DaXoa=0 chặn).

### MON_AN — TrangThai generated

```sql
`TrangThai` varchar(20) GENERATED ALWAYS AS (
  (case when (`AnThuCong` = 1) then 'An'
        when ((`HetNLThuCong` = 1) or (`HetNLTuDong` = 1)) then 'Hết nguyên liệu'
        else 'Hoạt động' end)
) STORED
```

Nháp là suy ra ở tầng ứng dụng (chưa có CONG_THUC hiệu lực), không lưu trong cột — theo quyết định #1.

### GIAO_DICH_KHO — 7 FK + CHECK 4 nhánh + BusinessDate DATE (C4)

```sql
`BusinessDate` date NOT NULL,
CONSTRAINT `ck_GIAO_DICH_KHO_movement_source_matches_kind`
  CHECK (((LoaiGiaoDich='Nhập' AND MaChiTietNhap IS NOT NULL)
      OR (LoaiGiaoDich IN ('Trừ tự động','Hoàn kho') AND MaChiTietOrder IS NOT NULL)
      OR (LoaiGiaoDich='Xuất thủ công' AND MaChiTietXuat IS NOT NULL)
      OR (LoaiGiaoDich='Điều chỉnh kiểm kê' AND MaChiTietKiemKe IS NOT NULL)))
-- 7 FK: MaNguyenLieu, MaLoNguyenLieu, MaChiTietNhap/Order/Xuat/KiemKe, NguoiThucHien — đều RESTRICT
KEY `ix_GIAO_DICH_KHO_MaNguyenLieu_ThoiDiem` (`MaNguyenLieu`,`ThoiDiem`)
```

### LO_NGUYEN_LIEU

```sql
`MaChiTietNhap` bigint NOT NULL,
UNIQUE KEY `uq_LO_NGUYEN_LIEU_MaChiTietNhap` (`MaChiTietNhap`),
KEY `ix_LO_NGUYEN_LIEU_MaNguyenLieu_TrangThai_NgayNhap` (`MaNguyenLieu`,`TrangThai`,`NgayNhap`),
`LoDieuChinhKiemKe` tinyint(1) NOT NULL
```

### BusinessDate là DATE (không còn DATETIME)

```sql
SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.COLUMNS
WHERE COLUMN_NAME='BusinessDate' AND TABLE_NAME IN ('ORDER','HOA_DON','GIAO_DICH_KHO');
-- BusinessDate | date (cả 3 bảng)
```

### CHECK ORDER BR-01 + JSON

```
INSERT ORDER (BusinessDate, LoaiDon='Tại chỗ', TrangThai, MaBan=NULL)
→ 3819 Check constraint 'ck_ORDER_dine_in_needs_a_table' is violated (đúng)

INSERT NHAT_KY_HE_THONG (DuLieuTruoc=JSON_OBJECT('a',1)) → {"a": 1} (JSON OK)
```

## 4. Views (stub có TODO phase-6, đã khóa phạm vi)

```
vw_ai_quanly  — Manager:  SELECT MaOrder,BusinessDate,LoaiDon,TrangThai,MaBan FROM ORDER
vw_ai_thungan — Cashier:  SELECT MaOrder,BusinessDate,LoaiDon,TrangThai,MaBan FROM ORDER (không GiaVonUocTinh, không MatKhauHash)
vw_ai_kho     — Warehouse: SELECT MaNguyenLieu,TenNguyenLieu,DonViTinh,SoLuongTon FROM NGUYEN_LIEU
```

```sql
SHOW CREATE VIEW vw_ai_quanly --
  AS select `ORDER`.`MaOrder` AS `MaOrder`, ... from `ORDER`
SHOW CREATE VIEW vw_ai_kho --
  AS select `NGUYEN_LIEU`.`MaNguyenLieu` AS `MaNguyenLieu`, ... from `NGUYEN_LIEU`
```

## 5. Grants (NFR-06)

```
Grants for ai_manager@%   — GRANT SELECT ON restaurant.vw_ai_quanly TO ai_manager@%
Grants for ai_cashier@%   — GRANT SELECT ON restaurant.vw_ai_thungan TO ai_cashier@%
Grants for ai_warehouse@% — GRANT SELECT ON restaurant.vw_ai_kho TO ai_warehouse@%
```

- Negative: `ai_cashier SELECT vw_ai_kho` → `1142 SELECT command denied` ✓
- Positive: `ai_manager SELECT vw_ai_quanly COUNT(*)` → `0` ✓

## 6. Gate

```
[check-resources] OK — proceeding (ncpu=12)
BAN count 2, views 3, db sanity OK
ruff: All checks passed
mypy: Success: no issues found in 65 source files
pytest: 75 passed (2 warnings) — unit gate
pnpm typecheck: pass
pnpm build: 11 routes static (/, /login, /catalog, /sales, /inventory, /reports, /settings, /assistant, ...)
```

## 7. Ghi chú

- B1 (make db-up && make migrate) đã xong trên máy này; bằng chứng trên copy từ terminal thật ngày 2026-09-24.
- B2 (migration tường minh) đã xong: 890db4fbb8b6 thay 001.
- B3 (IF→CASE) đã xong, verify trên MySQL.
- View stub vẫn còn TODO phase-6 — sẽ thay bằng column set thật trước Phase 6.
