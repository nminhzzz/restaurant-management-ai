# Views và tài khoản chỉ-đọc (NFR-06, NFR-12)

Ba view `vw_ai_*` là ranh giới dữ liệu của trợ lý AI — mỗi vai trò chỉ thấy view của mình.
Tài khoản CSDL chỉ-đọc tương ứng chỉ được `GRANT SELECT` trên đúng view đó.

## Áp dụng

### macOS / Linux
```bash
export AI_READONLY_PASSWORD_MANAGER=...
export AI_READONLY_PASSWORD_CASHIER=...
export AI_READONLY_PASSWORD_WAREHOUSE=...
./scripts/apply_grants.sh
```

### Windows (PowerShell)
```powershell
$env:AI_READONLY_PASSWORD_MANAGER="..."
$env:AI_READONLY_PASSWORD_CASHIER="..."
$env:AI_READONLY_PASSWORD_WAREHOUSE="..."
powershell -ExecutionPolicy Bypass -File scripts/apply_grants.ps1
```

Mật khẩu không được commit — `grants.sql.template` chỉ chứa placeholder.

Điền cùng giá trị vào `AI_READONLY_URL_*` trong `.env` để API đăng nhập bằng các tài khoản này.

## Hợp đồng cột (column set) — khóa trước Phase 6

| View | Cột được phép | Cột cấm (không bao giờ lộ) |
|------|---------------|----------------------------|
| `vw_ai_quanly` | `ORDER`: MaOrder, BusinessDate, LoaiDon, TrangThai, MaBan; `HOA_DON`: MaHoaDon, MaOrder, BusinessDate, ThoiDiemXuat, TongTien; `GIAO_DICH_THANH_TOAN`: MaOrder, BusinessDate, SoTien (tổng hợp); `NGUYEN_LIEU`: MaNguyenLieu, TenNguyenLieu, DonViTinh, SoLuongTon | `NGUOI_DUNG.MatKhauHash`, `CHI_TIET_PHIEU_XUAT.GiaVonUocTinh` chi tiết, `BAN.TenBan_Active` nội bộ |
| `vw_ai_thungan` | `ORDER` + `HOA_DON` + `GIAO_DICH_THANH_TOAN` như trên, chỉ 3 nhóm này | `NGUYEN_LIEU`, `LO_NGUYEN_LIEU`, `GIAO_DICH_KHO`, `GIA_BINH_QUAN_THANG`, `GiaVonUocTinh`, `MatKhauHash`, mọi `PHIEU_*` kho |
| `vw_ai_kho` | `NGUYEN_LIEU`, `LO_NGUYEN_LIEU`, `GIAO_DICH_KHO.BusinessDate/SoLuong/LoaiGiaoDich` (không đơn giá) | `HOA_DON.TongTien`, `GIAO_DICH_THANH_TOAN.SoTien`, `MatKhauHash`, `GiaVonUocTinh` chi tiết |

> Hiện stub chỉ giữ hợp đồng tối thiểu để test `information_schema` pass; Phase 6 thay bằng `SELECT` đúng set trên.
> Test: `apps/api/tests/schema/test_ai_views.py` assert `set(view_columns) == expected` trên MySQL (integration).

