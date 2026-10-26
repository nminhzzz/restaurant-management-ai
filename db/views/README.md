# Tập view và tài khoản chỉ đọc của AI

Mỗi vai trò có một tài khoản MySQL 8.4 riêng, chỉ được SELECT trên tập view theo chủ đề của vai trò. Các view union cũ `vw_ai_quanly`, `vw_ai_thungan`, `vw_ai_kho` được giữ làm tài liệu tương thích migration, không được cấp quyền hay đưa vào prompt/allowlist.

Chạy migration trước, sau đó đặt các biến `AI_READONLY_PASSWORD_MANAGER`, `AI_READONLY_PASSWORD_CASHIER`, `AI_READONLY_PASSWORD_WAREHOUSE` rồi chạy `scripts/apply_grants.sh` (Windows: `scripts/apply_grants.ps1`). Các script thu hồi toàn bộ quyền cũ trước khi cấp lại tập SELECT. `AI_READONLY_URL_*` bắt buộc ở mọi môi trường, không dùng chung người dùng CSDL với nhau hoặc với tài khoản ghi nghiệp vụ.

## Hợp đồng cột

Các view theo chủ đề có mức chi tiết riêng: order, dòng món, hóa đơn, thanh toán, nguyên liệu, lô và giao dịch. Trước khi kết hợp nhiều chủ đề bằng JOIN, phải tổng hợp riêng các quan hệ một-nhiều theo khóa phù hợp để không nhân doanh thu hay số lượng. `LoaiBanGhi` nếu có là hằng cố định của view, không còn là nhánh UNION. Không JOIN trực tiếp hóa đơn với cả dòng món lẫn giao dịch thanh toán.

`*_ton` tổng hợp lượng giữ trước khi tính lượng khả dụng trên từng lô còn hạn. Mỗi nguyên liệu xuất hiện một lần, gồm tồn sổ sách, đủ điều kiện, đang giữ, khả dụng và thời điểm tính. `*_suat` chỉ trả `MaMon`, `TenMon`, `SoSuatKhaDung`, `ThoiDiemTinh`, tính bằng công thức hiện hành và lượng khả dụng mới nhất; không trả công thức, định lượng hoặc giá vốn cho Bếp. Món bị xóa, Nháp hoặc tạm dừng thủ công không có số suất có thể bán; thiếu nguyên liệu trả 0. Thời hạn giữ, hạn lô và phiên bản công thức được xét lại trong mỗi SELECT. Bộ nhớ đệm chỉ lưu SQL, không lưu kết quả tồn hay số suất.

Ngày kinh doanh của phiếu nhập/xuất/kiểm kê và công thức/giá hiện hành dựa vào `LICH_GIO_BUSINESS_DATE`, gồm giờ hiệu lực theo phút và thời điểm chuyển lịch; không suy ra ngày bằng mốc cố định. Cột BusinessDate đã lưu trên order, hóa đơn, thanh toán và giao dịch kho được giữ nguyên.

| View | Cột công khai |
| --- | --- |
| `vw_ai_kho_giaodich` | `LoaiBanGhi`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `MaGiaoDichKho`, `BusinessDate`, `SoLuong`, `LoaiGiaoDich` |
| `vw_ai_kho_kiemke` | `MaPhieuKiemKe`, `BusinessDate`, `TrangThai`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `TonHeThong`, `TonThucTe`, `ChenhLech` |
| `vw_ai_kho_lo` | `LoaiBanGhi`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `MaLo`, `SoLuongConLai`, `TrangThaiLo`, `NgayNhapLo`, `HanSuDungLo` |
| `vw_ai_kho_nguyenlieu` | `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `SoNgayBaoQuan`, `MucTonToiThieu` |
| `vw_ai_kho_nhap` | `MaPhieuNhap`, `BusinessDate`, `TrangThai`, `TenNhaCungCap`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `SoLuongNhap` |
| `vw_ai_kho_suat` | `MaMon`, `TenMon`, `SoSuatKhaDung`, `ThoiDiemTinh` |
| `vw_ai_kho_ton` | `LoaiBanGhi`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `SoLuongTon`, `ThoiDiemTinh`, `SoLuongDuDieuKien`, `SoLuongGiu`, `SoLuongKhaDung`, `MucTonToiThieu`, `CanhBaoTonThap` |
| `vw_ai_kho_xuat` | `MaPhieuXuat`, `BusinessDate`, `TrangThai`, `LyDo`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `SoLuong` |
| `vw_ai_quanly_ban` | `MaBan`, `TenBan`, `TrangThai`, `SoChoNgoi` |
| `vw_ai_quanly_congthuc` | `MaCongThuc`, `MaMon`, `TenMon`, `BusinessDateApDung`, `TrangThai`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `DinhLuong` |
| `vw_ai_quanly_dongmon` | `LoaiBanGhi`, `MaOrder`, `BusinessDate`, `TrangThaiOrder`, `TenMon`, `TenNhom`, `SoLuongMon`, `DonGiaMon`, `ThanhTienMon` |
| `vw_ai_quanly_giaodich` | `LoaiBanGhi`, `MaOrder`, `BusinessDate`, `TrangThaiOrder`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `MaGiaoDichKho`, `SoLuong`, `LoaiGiaoDich` |
| `vw_ai_quanly_giavon` | `LoaiBanGhi`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `Thang`, `GiaBinhQuanThang`, `TongSoLuongNhapThang` |
| `vw_ai_quanly_hoadon` | `LoaiBanGhi`, `MaOrder`, `BusinessDate`, `MaHoaDon`, `ThoiDiemXuat`, `TongTien` |
| `vw_ai_quanly_kiemke` | `MaPhieuKiemKe`, `BusinessDate`, `TrangThai`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `TonHeThong`, `TonThucTe`, `ChenhLech` |
| `vw_ai_quanly_lo` | `LoaiBanGhi`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `MaLo`, `SoLuongConLai`, `TrangThaiLo`, `NgayNhapLo`, `HanSuDungLo` |
| `vw_ai_quanly_mon` | `MaMon`, `TenMon`, `TenNhom`, `TrangThai`, `GiaBan` |
| `vw_ai_quanly_nguyenlieu` | `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `SoNgayBaoQuan`, `MucTonToiThieu` |
| `vw_ai_quanly_nhacungcap` | `MaNCC`, `TenNCC` |
| `vw_ai_quanly_nhap` | `LoaiBanGhi`, `BusinessDate`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `MaPhieuNhap`, `TenNhaCungCap`, `DonGiaNhap`, `SoLuongNhap` |
| `vw_ai_quanly_order` | `LoaiBanGhi`, `MaOrder`, `BusinessDate`, `LoaiDon`, `TrangThaiOrder`, `MaBan`, `LyDoHuyOrder` |
| `vw_ai_quanly_suat` | `MaMon`, `TenMon`, `SoSuatKhaDung`, `ThoiDiemTinh` |
| `vw_ai_quanly_thanhtoan` | `LoaiBanGhi`, `MaOrder`, `BusinessDate`, `MaGiaoDich`, `PhuongThuc`, `SoTien` |
| `vw_ai_quanly_ton` | `LoaiBanGhi`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `SoLuongTon`, `ThoiDiemTinh`, `SoLuongDuDieuKien`, `MucTonToiThieu`, `SoLuongGiu`, `SoLuongKhaDung` |
| `vw_ai_quanly_xuat` | `MaPhieuXuat`, `BusinessDate`, `TrangThai`, `LyDo`, `MaNguyenLieu`, `TenNguyenLieu`, `DonViTinh`, `SoLuong` |
| `vw_ai_thungan_ban` | `MaBan`, `TenBan`, `TrangThai`, `SoChoNgoi` |
| `vw_ai_thungan_dongmon` | `LoaiBanGhi`, `MaOrder`, `BusinessDate`, `TrangThaiOrder`, `TenMon`, `TenNhom`, `SoLuongMon`, `DonGiaMon`, `ThanhTienMon` |
| `vw_ai_thungan_hoadon` | `LoaiBanGhi`, `MaOrder`, `BusinessDate`, `MaHoaDon`, `ThoiDiemXuat`, `TongTien` |
| `vw_ai_thungan_mon` | `MaMon`, `TenMon`, `TenNhom`, `TrangThai`, `GiaBan` |
| `vw_ai_thungan_order` | `LoaiBanGhi`, `MaOrder`, `BusinessDate`, `LoaiDon`, `TrangThaiOrder`, `MaBan` |
| `vw_ai_thungan_thanhtoan` | `LoaiBanGhi`, `MaOrder`, `BusinessDate`, `MaGiaoDich`, `PhuongThuc`, `SoTien` |

## Nhật ký nhà cung cấp

`TRUY_VAN_AI` ghi model/phiên bản thực tế trả về, tổng token đầu vào/đầu ra (output_tokens đã gồm token suy luận), số lần gọi gồm SQL/thử lại/diễn giải/fallback. `ChiTietSuDung` lưu từng lần gọi và đơn giá USD/triệu token tại lượt hỏi. Khi lỗi/timeout không có usage từ nhà cung cấp, `ChiPhiUSD` để NULL; JSON đánh dấu `cost_complete=false` cùng `known_cost_usd` là phần chi phí đã biết, không giả định tổng chi phí bằng 0. Các trường token khi thiếu chỉ phản ánh usage đã nhận, kèm cờ `usage_reported` cho từng lần gọi. Chỉ được kết luận chi phí chính xác khi `cost_complete=true`.

FK từ truy vấn tới phiên chat dùng RESTRICT; trigger MySQL cấm UPDATE/DELETE nhật ký tiếp tục được giữ nguyên. Không xóa phiên để xóa gián tiếp nhật ký.
