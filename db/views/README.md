# Views và tài khoản chỉ-đọc (NFR-06, NFR-12)

Ba view `vw_ai_*` là ranh giới dữ liệu của trợ lý AI — mỗi vai trò chỉ thấy view của mình.
Tài khoản CSDL chỉ-đọc tương ứng chỉ được `GRANT SELECT` trên đúng view đó.

Trên MySQL 8.4, file DDL bắt đầu bằng `SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci` và các cột
`CHAR` có `COLLATE` tường minh. Nếu thiếu, MySQL báo lỗi 1271 “Illegal mix of collations” khi tạo
hoặc truy vấn view vì literal mặc định `utf8mb4_0900_ai_ci` khác collation bảng.

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
`DonGiaNhap`, `SoLuongNhap` (giá nhập nguyên liệu — FR-AI-02), `SoLuongGiu`, `SoLuongKhaDung`
(lượng giữ/khả dụng, chỉ có ở nhánh `TON_KHO`).

Nhánh `DONG_MON` chỉ chứa dòng món chưa hủy (`CHI_TIET_ORDER.TrangThai <> 'Đã hủy'`), nhánh
`THANH_TOAN` chỉ chứa giao dịch thành công (`GIAO_DICH_THANH_TOAN.TrangThai = 'Thành công'`), và
nhánh `PHIEU_NHAP` loại phiếu đã hủy, đồng thời quy `NgayNhap` về Business Date bằng mốc 06:00.

Biên lợi nhuận gộp/tháng (FR-REP-04) và chi phí tiêu hao (FR-REP-05) không phải là một cột có sẵn
(view không tự JOIN xuyên nhánh) — trợ lý tính bằng cách tự JOIN hai nhánh của cùng view: doanh
thu từ `HOA_DON`/`THANH_TOAN`, giá vốn tiêu hao từ `GIAO_DICH_KHO` (`LoaiGiaoDich = 'Trừ tự động'`)
nhân `GiaBinhQuanThang` của `GIA_VON_THANG` cùng nguyên liệu/tháng.

### `vw_ai_thungan` — FR-AI-03 (Thu ngân/Nhân viên order; không giá nhập/lợi nhuận theo món)

4 nhánh: `ORDER`, `DONG_MON`, `HOA_DON`, `THANH_TOAN`.

Cột: `LoaiBanGhi`, `MaOrder`, `BusinessDate`, `LoaiDon`, `TrangThaiOrder`, `MaBan`, `MaHoaDon`,
`ThoiDiemXuat`, `TongTien`, `MaGiaoDich`, `PhuongThuc`, `SoTien`, `TenMon`, `TenNhom`,
`SoLuongMon`, `DonGiaMon` (giá bán), `ThanhTienMon`. **Không có** `MaNguyenLieu`,
`GiaBinhQuanThang`, `DonGiaNhap`, hay bất kỳ cột giá vốn/giá nhập nào. Nhánh `DONG_MON` loại dòng
món đã hủy; nhánh `THANH_TOAN` chỉ chứa giao dịch thành công.

### `vw_ai_kho` — FR-AI-04 (Nhân viên kho; không doanh thu/hóa đơn/lợi nhuận)

3 nhánh: `TON_KHO`, `GIAO_DICH_KHO`, `LO_NGUYEN_LIEU`.

Cột: `LoaiBanGhi`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `SoLuongTon`, `SoLuongGiu`
(lượng đang giữ trên các lô đủ điều kiện), `SoLuongKhaDung` (tồn còn dùng được sau khi trừ giữ),
`MucTonToiThieu` (ngưỡng hiệu lực), `CanhBaoTonThap` (cờ cảnh báo tồn thấp — FR-AI-04),
`MaGiaoDichKho`, `BusinessDate`, `SoLuong`, `LoaiGiaoDich`, `MaLo`, `SoLuongConLai`, `TrangThaiLo`,
`NgayNhapLo`, `HanSuDungLo` (hạn sử dụng đã lưu trên lô, tính từ `NgayNhap + SoNgayBaoQuan` khi nhập).
**Không có** `TongTien`, `SoTien`, `DonGia`/`DonGiaNhap`, hay bất kỳ cột doanh thu/hóa đơn/giá nào.

Ở nhánh `TON_KHO`, `SoLuongGiu` chỉ cộng giữ chỗ `Đang giữ` còn hạn trên lô có tồn dương, trạng thái
khác `Hết hạn` và còn trong ngày sử dụng. `SoLuongKhaDung` là tổng `GREATEST(0, SoLuongConLai - lượng
giữ)` trên chính các lô đủ điều kiện. Hai cột được NULL-pad ở nhánh giao dịch và nhánh lô.

### Cột cấm (không bao giờ lộ ở bất kỳ view nào)

`NGUOI_DUNG.MatKhauHash`, `NGUOI_DUNG.SoDienThoai`, mọi token JWT/session, và cột
`CHI_TIET_PHIEU_XUAT.GiaVonUocTinh` (giá vốn xuất kho ước tính nội bộ).

Test: `apps/api/tests/schema/test_ai_views.py` assert `set(view_columns) == expected` trên MySQL
(integration) và assert `vw_ai_thungan`/`vw_ai_kho` không lẫn cột bị cấm (NFR-06/12, FR-AI-03/04).


### Ghi chú cập nhật 21/10/2026

Nhánh `GIAO_DICH_KHO` giờ điền `MaOrder` và `TrangThaiOrder` cho các giao dịch
`Trừ tự động`/`Hoàn kho` (NULL với nhập kho, xuất thủ công và điều chỉnh kiểm kê). Nhờ đó câu hỏi
lợi nhuận gộp tách được giá vốn của order đã thanh toán/hủy/đóng chưa thu theo FR-REP-04–05.
