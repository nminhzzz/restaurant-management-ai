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

## Hợp đồng cột (column set)

Mỗi view là một `UNION ALL` NULL-padded trên một danh sách cột dùng chung; cột `LoaiBanGhi`
phân biệt các nhánh để LLM lọc bằng `WHERE LoaiBanGhi = '...'` thay vì đoán cột nào có dữ liệu.
Bám sát phạm vi FR-AI-02/03/04 (đặc tả §2.4.6) và nguyên tắc kế thừa FR-SET-03 (Quản lý kế thừa
toàn bộ phạm vi Thu ngân + Nhân viên kho).

### `vw_ai_quanly` — FR-AI-02 (Quản lý; đầy đủ phạm vi của cả ba vai trò)

8 nhánh `LoaiBanGhi`: `ORDER`, `DONG_MON`, `HOA_DON`, `THANH_TOAN`, `TON_KHO`, `GIA_VON_THANG`,
`GIAO_DICH_KHO`, `PHIEU_NHAP`.

Cột: `LoaiBanGhi`, `MaOrder`, `BusinessDate`, `LoaiDon`, `TrangThaiOrder`, `MaBan`,
`LyDoHuyOrder` (lý do hủy order — FR-REP-10), `MaHoaDon`, `ThoiDiemXuat`, `TongTien`,
`MaGiaoDich`, `PhuongThuc`, `SoTien`, `TenMon`, `TenNhom`, `SoLuongMon`, `DonGiaMon`,
`ThanhTienMon` (dòng bán món — FR-REP-03/06), `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`,
`SoLuongTon`, `MucTonToiThieu` (ngưỡng hiệu lực — cột nếu > 0, ngược lại `NguongTonMacDinh`),
`Thang`, `GiaBinhQuanThang`, `TongSoLuongNhapThang` (giá vốn bình quân tháng — FR-REP-04/05),
`MaGiaoDichKho`, `SoLuong`, `LoaiGiaoDich` (giao dịch kho), `MaPhieuNhap`, `TenNhaCungCap`,
`DonGiaNhap`, `SoLuongNhap` (giá nhập nguyên liệu — FR-AI-02).

Biên lợi nhuận gộp/tháng (FR-REP-04) và chi phí tiêu hao (FR-REP-05) không phải là một cột có sẵn
(view không tự JOIN xuyên nhánh) — trợ lý tính bằng cách tự JOIN hai nhánh của cùng view: doanh
thu từ `HOA_DON`/`THANH_TOAN`, giá vốn tiêu hao từ `GIAO_DICH_KHO` (`LoaiGiaoDich = 'Trừ tự động'`)
nhân `GiaBinhQuanThang` của `GIA_VON_THANG` cùng nguyên liệu/tháng.

### `vw_ai_thungan` — FR-AI-03 (Thu ngân/Nhân viên order; không giá nhập/lợi nhuận theo món)

4 nhánh: `ORDER`, `DONG_MON`, `HOA_DON`, `THANH_TOAN`.

Cột: `LoaiBanGhi`, `MaOrder`, `BusinessDate`, `LoaiDon`, `TrangThaiOrder`, `MaBan`, `MaHoaDon`,
`ThoiDiemXuat`, `TongTien`, `MaGiaoDich`, `PhuongThuc`, `SoTien`, `TenMon`, `TenNhom`,
`SoLuongMon`, `DonGiaMon` (giá bán), `ThanhTienMon`. **Không có** `MaNguyenLieu`,
`GiaBinhQuanThang`, `DonGiaNhap`, hay bất kỳ cột giá vốn/giá nhập nào.

### `vw_ai_kho` — FR-AI-04 (Nhân viên kho; không doanh thu/hóa đơn/lợi nhuận)

3 nhánh: `TON_KHO`, `GIAO_DICH_KHO`, `LO_NGUYEN_LIEU`.

Cột: `LoaiBanGhi`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `SoLuongTon`, `MucTonToiThieu`
(ngưỡng hiệu lực), `CanhBaoTonThap` (cờ cảnh báo tồn thấp — FR-AI-04), `MaGiaoDichKho`,
`BusinessDate`, `SoLuong`, `LoaiGiaoDich`, `MaLo`, `SoLuongConLai`, `TrangThaiLo`, `NgayNhapLo`,
`HanSuDungLo` (hạn sử dụng tính từ `NgayNhap + SoNgayBaoQuan`). **Không có** `TongTien`, `SoTien`,
`DonGia`/`DonGiaNhap`, hay bất kỳ cột doanh thu/hóa đơn/giá nào.

### Cột cấm (không bao giờ lộ ở bất kỳ view nào)

`NGUOI_DUNG.MatKhauHash`, `NGUOI_DUNG.SoDienThoai`, mọi token JWT/session, và cột
`CHI_TIET_PHIEU_XUAT.GiaVonUocTinh` (giá vốn xuất kho ước tính nội bộ).

Test: `apps/api/tests/schema/test_ai_views.py` assert `set(view_columns) == expected` trên MySQL
(integration) và assert `vw_ai_thungan`/`vw_ai_kho` không lẫn cột bị cấm (NFR-06/12, FR-AI-03/04).

