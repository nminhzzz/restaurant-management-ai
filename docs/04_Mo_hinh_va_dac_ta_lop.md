Hệ thống quản lý nhà hàng tích hợp AI hỗ trợ hoạt động kinh doanh

Phiên bản tài liệu V33  
Ngày 27 tháng 10 năm 2026

Mô hình lớp, ánh xạ sang lược đồ quan hệ và đặc tả thuộc tính, phương thức của các lớp đối tượng trong hệ thống quản lý nhà hàng.

## 3.2. Mô hình hóa đối tượng (Class Diagram)

Mô hình lớp mô tả các đối tượng nghiệp vụ, thuộc tính và quan hệ của hệ thống theo hướng phân tích thiết kế hướng đối tượng. Các sơ đồ được tổ chức theo module; thuộc tính và phương thức được đặc tả tại Phụ lục D ở cuối báo cáo, còn quan hệ và bội số được ánh xạ sang lược đồ quan hệ tại mục 4.2.2. Bội số trong sơ đồ dùng ký hiệu 1, 0..1, 0..\* và 1..\*. Kiểu dữ liệu trong các sơ đồ lớp là kiểu khái niệm, được định nghĩa tại Phụ lục D và ánh xạ sang kiểu dữ liệu MySQL tại mục 4.2.2.

Các lớp tham chiếu từ module khác được thể hiện bằng khung nét đứt nền xám, tên lớp kèm tên module trong ngoặc (ví dụ “(Module Danh mục)”), chỉ trình bày thông tin cần thiết để nhận diện quan hệ giữa các module.

![Sơ đồ hoặc hình minh họa](images/04_Mo_hinh_va_dac_ta_lop/media/image32.png)

Hình 31. Class Diagram - Module Quản lý danh mục

![Sơ đồ hoặc hình minh họa](images/04_Mo_hinh_va_dac_ta_lop/media/image33.png)

Hình 32. Class Diagram - Module Quản lý bán hàng

![Sơ đồ hoặc hình minh họa](images/04_Mo_hinh_va_dac_ta_lop/media/image34.png)

Hình 33. Class Diagram - Giữ chỗ món (Module Quản lý bán hàng)

![Sơ đồ hoặc hình minh họa](images/04_Mo_hinh_va_dac_ta_lop/media/image35.png)

Hình 34. Class Diagram - Module Quản lý kho

![Sơ đồ hoặc hình minh họa](images/04_Mo_hinh_va_dac_ta_lop/media/image36.png)

Hình 35. Class Diagram - Module Cài đặt hệ thống

![Sơ đồ hoặc hình minh họa](images/04_Mo_hinh_va_dac_ta_lop/media/image37.png)

Hình 36. Class Diagram - Module AI Assistant

Module Quản lý danh mục: NHOM_MON, MON_AN, LICH_SU_GIA_MON, CONG_THUC, CHI_TIET_CONG_THUC, NGUYEN_LIEU, NHA_CUNG_CAP, BAN - MON_AN kết hợp (composition) với CONG_THUC theo từng phiên bản hiệu lực; CONG_THUC kết hợp CHI_TIET_CONG_THUC, mỗi dòng liên kết tới một NGUYEN_LIEU.

Module Quản lý bán hàng: ORDER, CHI_TIET_ORDER, LICH_SU_DOI_BAN, HOA_DON, GIAO_DICH_THANH_TOAN, PHIEU_BEP - ORDER kết hợp nhiều CHI_TIET_ORDER (1--1..\*), mỗi CHI_TIET_ORDER tham chiếu một MON_AN; ORDER liên kết 1--0..\* với GIAO_DICH_THANH_TOAN (mỗi lần thanh toán hoặc thử thanh toán là một giao dịch) và 1--0..1 với HOA_DON sau khi chốt; HOA_DON tham chiếu đúng một giao dịch “Thành công” qua MaGiaoDichThanhToan. GIU_CHO_MON lưu các dòng chưa gửi theo MaLuotChon; CHI_TIET_GIU_CHO lưu nguyên liệu theo lô. Khi gửi thành công, lượt giữ tham chiếu dòng CHI_TIET_ORDER đã tạo.

Module Quản lý kho: PHIEU_NHAP_KHO, CHI_TIET_PHIEU_NHAP, LO_NGUYEN_LIEU, PHIEU_XUAT_KHO, CHI_TIET_PHIEU_XUAT, PHIEU_KIEM_KE, CHI_TIET_KIEM_KE, GIAO_DICH_KHO, GIA_BINH_QUAN_THANG - mỗi CHI_TIET_PHIEU_NHAP sinh ra một LO_NGUYEN_LIEU (lô điều chỉnh kiểm kê là ngoại lệ, không có dòng nhập); mọi lớp biến động (nhập/xuất/kiểm kê) đều phát sinh bản ghi GIAO_DICH_KHO, NGUYEN_LIEU chỉ giữ số tồn dẫn xuất. Lượng đang giữ được tổng hợp từ CHI_TIET_GIU_CHO; phiên kiểm kê được quản lý bằng trạng thái PHIEU_KIEM_KE.

Module Báo cáo thống kê: Không định nghĩa lớp riêng; module đọc (read-only) từ các lớp ở trên thông qua các lớp dịch vụ/truy vấn tổng hợp (report service).

Module Cài đặt hệ thống: VAI_TRO, NGUOI_DUNG, CAU_HINH_HE_THONG, NHAT_KY_HE_THONG - NGUOI_DUNG liên kết 0..\*--1 với VAI_TRO; mọi thao tác rủi ro cao trên các lớp khác đều phát sinh một NHAT_KY_HE_THONG. CAU_HINH_HE_THONG chứa ThoiGianGiuChoPhut để xác định thời hạn cho từng dòng món chưa gửi.

Module AI Assistant: PHIEN_CHAT_AI, TRUY_VAN_AI - PHIEN_CHAT_AI kết hợp nhiều TRUY_VAN_AI (1--0..\*); TRUY_VAN_AI chỉ đọc dữ liệu qua các view phân quyền dựng trên các lớp nghiệp vụ ở trên.

## D. Đặc tả thuộc tính và phương thức của các lớp đối tượng

Mục này đặc tả chi tiết thuộc tính và phương thức của 31 lớp đối tượng đã liệt kê trong Bảng 8 (mục 4.2.1).

Mục này sử dụng các kiểu dữ liệu khái niệm String, int, Long, double, boolean, LocalDate, LocalDateTime và LocalTime. Thuộc tính cho phép rỗng được ghi ở cột “Ràng buộc” (ví dụ “Cho phép NULL”). Việc ánh xạ sang kiểu dữ liệu MySQL, quy tắc NULL/NOT NULL, thuộc tính dẫn xuất và các ràng buộc cơ sở dữ liệu được trình bày tại mục 4.2.2. Chi tiết thuộc tính và phương thức của từng lớp đối tượng được trình bày lần lượt dưới đây. Trong cột “Ràng buộc”: thuộc tính đóng vai trò định danh của đối tượng được ghi “Định danh duy nhất” (hoặc “một phần” nếu là định danh phức hợp); thuộc tính đóng vai trò liên kết (tham chiếu) tới một lớp đối tượng khác được ghi rõ đối tượng được tham chiếu.

**a1. Lớp VAI_TRO**

Lưu ba vai trò cố định: Chủ nhà hàng/Quản lý, Thu ngân/Nhân viên order và Bếp.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                    | **Mô tả**                 |
|----------------|------------------|----------------------------------|---------------------------|
| MaVaiTro       | int              | Định danh duy nhất của đối tượng | Định danh vai trò         |
| TenVaiTro      | String           | Không trùng lặp                  | Tên vai trò               |
| MoTa           | String           | –                                | Mô tả phạm vi trách nhiệm |

Bảng 14. Thuộc tính và phương thức của lớp VAI_TRO

Phương thức chính: layDanhSachQuyenHan(); kiemTraQuyen(maChucNang).

**a2. Lớp NGUOI_DUNG**

Tài khoản đăng nhập của nhân sự nhà hàng.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                    | **Mô tả**               |
|----------------|------------------|----------------------------------|-------------------------|
| MaNguoiDung    | int              | Định danh duy nhất của đối tượng | Định danh người dùng    |
| TenDangNhap    | String           | Không trùng lặp                  | Tên đăng nhập           |
| MatKhauHash    | String           | –                                | Mật khẩu đã băm         |
| HoTen          | String           | –                                | Họ tên nhân sự          |
| SoDienThoai    | String           | –                                | Số liên hệ              |
| MaVaiTro       | int              | Tham chiếu tới đối tượng VAI_TRO | Vai trò được gán        |
| TrangThai      | String           | –                                | Hoạt động / Đã khóa     |
| NgayTao        | LocalDateTime    | –                                | Thời điểm tạo tài khoản |

Bảng 15. Thuộc tính và phương thức của lớp NGUOI_DUNG

Phương thức chính: dangNhap(taiKhoan, matKhau); doiMatKhau(matKhauMoi); khoaTaiKhoan(); capNhatThongTin().

**a3. Lớp CAU_HINH_HE_THONG**

Bảng tham số dùng chung, chỉ có một bản ghi hiệu lực.

| **Thuộc tính**           | **Kiểu dữ liệu** | **Ràng buộc**                                                      | **Mô tả**                                                                                                         |
|--------------------------|------------------|--------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| MaCauHinh                | int              | Định danh duy nhất (đối tượng singleton, chỉ tồn tại một thực thể) | Định danh bản ghi cấu hình                                                                                        |
| TenNhaHang               | String           | –                                                                  | Tên nhà hàng in trên hóa đơn                                                                                      |
| DiaChi                   | String           | –                                                                  | Địa chỉ nhà hàng                                                                                                  |
| MauHoaDon                | String           | –                                                                  | Cấu hình mẫu hóa đơn                                                                                              |
| NguongTonMacDinh         | double           | –                                                                  | Mức tồn tối thiểu mặc định                                                                                        |
| GioBatDauBusinessDate    | LocalTime        | –                                                                  | Mốc bắt đầu Business Date đang áp dụng, do Quản lý cấu hình tại màn hình Cài đặt                                  |
| GioBatDauBusinessDateMoi | LocalTime        | –                                                                  | Mốc giờ mới đang chờ áp dụng, cho phép NULL; khi đến NgayHieuLucGioMoi thì được chuyển sang GioBatDauBusinessDate |
| NgayHieuLucGioMoi        | LocalDate        | –                                                                  | Business Date bắt đầu áp dụng mốc giờ mới (Business Date kế tiếp tại thời điểm thay đổi), cho phép NULL           |
| SoNgayCanhBaoHetHan      | int              | Mặc định 3; số nguyên dương                                        | Lô có hạn sử dụng còn không quá số ngày này được xếp “Sắp hết hạn”.                                               |
| SoCauHoiAIMoiNgay        | int              | Mặc định 50; số nguyên dương                                       | Số câu hỏi AI tối đa của mỗi người dùng trong một ngày.                                                           |
| ThoiGianGiuChoPhut       | int              | Số nguyên dương; mặc định 5                                        | Thời hạn dòng món chưa gửi; áp dụng ở lần tạo/gia hạn.                                                            |

Bảng 16. Thuộc tính và phương thức của lớp CAU_HINH_HE_THONG

Phương thức chính: capNhatCauHinh(thamSo, giaTri); layNguongCanhBaoTon(); layBusinessDateHienTai().

**a4. Lớp NHAT_KY_HE_THONG**

Ghi vết thao tác rủi ro cao, chỉ ghi thêm, không sửa/xóa. Đối với xử lý thanh toán, DoiTuong/MaDoiTuong gắn order; DuLieuTruoc/DuLieuSau lưu dữ liệu có cấu trúc gồm MaOrder, MaGiaoDichTT, trạng thái, nội dung và kết quả xác minh, mã tham chiếu/bằng chứng nếu có, số tiền chưa thu khi đóng. MaNguoiDung và ThoiDiem xác định người xử lý và thời điểm. Mỗi lần bổ sung thông tin hoặc cập nhật kết quả tạo bản ghi mới để tra cứu lịch sử.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                       | **Mô tả**                                                                                                                                                                                                                                                                                                   |
|----------------|------------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| MaNhatKy       | Long             | Định danh duy nhất của đối tượng    | Định danh bản ghi nhật ký                                                                                                                                                                                                                                                                                   |
| MaNguoiDung    | int              | Tham chiếu tới đối tượng NGUOI_DUNG | Người thực hiện                                                                                                                                                                                                                                                                                             |
| ThoiDiem       | LocalDateTime    | –                                   | Thời điểm thao tác                                                                                                                                                                                                                                                                                          |
| LoaiThaoTac    | String           | –                                   | Hủy order, hủy món, xóa danh mục, sửa/hủy phiếu nhập, đổi bàn, giải phóng bàn, quản lý tài khoản; hủy giao dịch QR chủ động, chuyển sang chờ xác minh thanh toán, bổ sung xác minh, xác nhận đã nhận tiền, mở lại thanh toán, đóng order chưa thu được tiền, áp dụng khoản đến muộn, lưu kết quả hoàn tiền. |
| DoiTuong       | String           | –                                   | Tên lớp đối tượng bị tác động                                                                                                                                                                                                                                                                               |
| MaDoiTuong     | String           | –                                   | Định danh của đối tượng bị tác động                                                                                                                                                                                                                                                                         |
| DuLieuTruoc    | String           | –                                   | Giá trị trước khi thay đổi                                                                                                                                                                                                                                                                                  |
| DuLieuSau      | String           | –                                   | Giá trị sau khi thay đổi                                                                                                                                                                                                                                                                                    |
| LyDo           | String           | –                                   | Lý do do người dùng nhập; bắt buộc khi mở lại thanh toán hoặc đóng order chưa thu được tiền.                                                                                                                                                                                                                |

Bảng 17. Thuộc tính và phương thức của lớp NHAT_KY_HE_THONG

Phương thức chính: ghiNhatKy(hanhDong, nguoiThucHien); truyVanNhatKy(boLoc).

**a5. Lớp NHOM_MON**

Nhóm phân loại món ăn, áp dụng xóa mềm.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                    | **Mô tả**          |
|----------------|------------------|----------------------------------|--------------------|
| MaNhomMon      | int              | Định danh duy nhất của đối tượng | Định danh nhóm món |
| TenNhomMon     | String           | –                                | Tên nhóm           |
| ThuTuHienThi   | int              | –                                | Thứ tự sắp xếp     |
| DaXoa          | boolean          | –                                | Cờ xóa mềm         |
| NgayXoa        | LocalDateTime    | –                                | Thời điểm xóa mềm  |

Bảng 18. Thuộc tính và phương thức của lớp NHOM_MON

Phương thức chính: themNhom(); suaNhom(); xoaMemNhom().

**a6. Lớp MON_AN**

Món ăn; giá và công thức hiện hành được suy ra từ hai bảng lịch sử tương ứng. Trạng thái phục vụ của món phụ thuộc HetNguyenLieu suy ra từ tồn khả dụng theo công thức và cờ TamDungThuCong do Quản lý bật/tắt. HetNguyenLieu là giá trị suy ra, không lưu trong MON_AN. ChuaCoCongThuc là cờ hệ thống tự đặt true khi món chưa từng được gán công thức mặc định lần nào và chuyển sang false khi công thức đầu tiên được gán; sau đó không trở lại true. TrangThai là thuộc tính tổng hợp, dùng để hiển thị. Cụ thể, cách hiển thị của một món ăn trên màn hình gọi món được quyết định như sau:

- Nếu ChuaCoCongThuc = true: Món ở trạng thái “Nháp” và bị ẩn hoàn toàn khỏi màn hình gọi món bất kể các cờ khác.

- Nếu ChuaCoCongThuc = false và HetNguyenLieu = true: Món ở trạng thái “Hết nguyên liệu”, vẫn hiển thị nhưng bị vô hiệu hóa và gắn đúng nhãn “Hết nguyên liệu”. Nếu đồng thời TamDungThuCong = true, màn hình quản trị hiển thị thêm lý do tạm dừng thủ công.

- Nếu ChuaCoCongThuc = false, HetNguyenLieu = false và TamDungThuCong = true: Món ở trạng thái “Tạm dừng phục vụ”, hiển thị mờ và không cho gọi. Chỉ khi HetNguyenLieu = false và TamDungThuCong = false, món mới ở trạng thái “Hoạt động” và cho phép gọi.

| **Thuộc tính**           | **Kiểu dữ liệu** | **Ràng buộc**                     | **Mô tả**                                                                                                                                                                                                                                                                |
|--------------------------|------------------|-----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| MaMon                    | int              | Định danh duy nhất của đối tượng  | Định danh món ăn                                                                                                                                                                                                                                                         |
| TenMon                   | String           | –                                 | Tên món                                                                                                                                                                                                                                                                  |
| MaNhomMon                | int              | Tham chiếu tới đối tượng NHOM_MON | Nhóm món (đúng một nhóm)                                                                                                                                                                                                                                                 |
| HinhAnh                  | String           | –                                 | Đường dẫn ảnh món                                                                                                                                                                                                                                                        |
| GiaHienTai               | double           | –                                 | Giá đang áp dụng (suy ra từ phiên bản giá đang hiệu lực trong LICH_SU_GIA_MON)                                                                                                                                                                                           |
| TrangThai                | String           | Giá trị suy ra tự động            | Giá trị suy ra, không ghi trực tiếp: Nháp nếu ChuaCoCongThuc; nếu đã có công thức thì Hết nguyên liệu khi HetNguyenLieu; nếu kho đủ nhưng TamDungThuCong thì Tạm dừng phục vụ; còn lại Hoạt động. Món Nháp bị ẩn; hai trạng thái chặn được hiển thị mờ và không cho gọi. |
| TamDungThuCong           | boolean          | –                                 | Cờ do Quản lý bật/tắt để tạm dừng phục vụ; độc lập với kết quả kiểm tra tồn kho.                                                                                                                                                                                         |
| HetNguyenLieu (dẫn xuất) | boolean          | Giá trị dẫn xuất                  | Suy từ tồn khả dụng của các nguyên liệu theo công thức hiện hành; true nếu không đủ làm một suất. Không lưu trong MON_AN, không bị Quản lý bật thủ công.                                                                                                                 |
| ChuaCoCongThuc           | boolean          | –                                 | Cờ hệ thống tự đặt true khi món chưa được gán công thức                                                                                                                                                                                                                  |
| DaXoa                    | boolean          | –                                 | Cờ xóa mềm                                                                                                                                                                                                                                                               |

Bảng 19. Thuộc tính và phương thức của lớp MON_AN

Phương thức chính: capNhatTrangThai(); tamDungPhucVu(giaTri: boolean); kiemTraConNguyenLieu(); layGiaBanHienTai().

**a7. Lớp LICH_SU_GIA_MON**

Mỗi lần đổi giá sinh một phiên bản; order tham chiếu đúng phiên bản có hiệu lực.

| **Thuộc tính**     | **Kiểu dữ liệu** | **Ràng buộc**                       | **Mô tả**                                          |
|--------------------|------------------|-------------------------------------|----------------------------------------------------|
| MaPhienBanGia      | Long             | Định danh duy nhất của đối tượng    | Định danh phiên bản giá                            |
| MaMon              | int              | Tham chiếu tới đối tượng MON_AN     | Món ăn tương ứng                                   |
| GiaBan             | double           | Phải lớn hơn 0                      | Giá bán của phiên bản                              |
| BusinessDateApDung | LocalDate        | –                                   | Business Date được chọn để áp dụng                 |
| ThoiDiemHieuLuc    | LocalDateTime    | –                                   | Thời điểm bắt đầu hiệu lực                         |
| ThoiDiemHetHieuLuc | LocalDateTime    | –                                   | Thời điểm bị phiên bản sau thay thế                |
| LoaiThayDoi        | String           | –                                   | Theo lịch / Sửa trực tiếp                          |
| TrangThai          | String           | –                                   | Chờ áp dụng / Đang áp dụng / Hết hiệu lực / Đã hủy |
| NguoiTao           | int              | Tham chiếu tới đối tượng NGUOI_DUNG | Người thực hiện thay đổi                           |
| ThoiDiemTao        | LocalDateTime    | –                                   | Thời điểm tạo phiên bản                            |

Bảng 20. Thuộc tính và phương thức của lớp LICH_SU_GIA_MON

Phương thức chính: taoPhienBanGia(giaMoi, thoiDiem); layGiaTaiThoiDiem(t).

**a8. Lớp CONG_THUC**

Phiên bản công thức chế biến của món, cơ chế hiệu lực giống bảng giá.

| **Thuộc tính**     | **Kiểu dữ liệu** | **Ràng buộc**                       | **Mô tả**                                          |
|--------------------|------------------|-------------------------------------|----------------------------------------------------|
| MaCongThuc         | Long             | Định danh duy nhất của đối tượng    | Định danh phiên bản công thức                      |
| MaMon              | int              | Tham chiếu tới đối tượng MON_AN     | Món ăn tương ứng                                   |
| SoPhienBan         | int              | –                                   | Số thứ tự phiên bản                                |
| BusinessDateApDung | LocalDate        | –                                   | Business Date áp dụng                              |
| ThoiDiemHieuLuc    | LocalDateTime    | –                                   | Thời điểm bắt đầu hiệu lực                         |
| ThoiDiemHetHieuLuc | LocalDateTime    | –                                   | Thời điểm bị thay thế                              |
| LoaiThayDoi        | String           | –                                   | Theo lịch / Sửa trực tiếp                          |
| TrangThai          | String           | –                                   | Chờ áp dụng / Đang áp dụng / Hết hiệu lực / Đã hủy |
| NguoiTao           | int              | Tham chiếu tới đối tượng NGUOI_DUNG | Người thực hiện                                    |
| ThoiDiemTao        | LocalDateTime    | –                                   | Thời điểm tạo                                      |

Bảng 21. Thuộc tính và phương thức của lớp CONG_THUC

Phương thức chính: taoPhienBanCongThuc(t); layCongThucHieuLuc(t).

**a9. Lớp CHI_TIET_CONG_THUC**

Lớp đối tượng trung gian giữa CONG_THUC và NGUYEN_LIEU.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                                                                    | **Mô tả**               |
|----------------|------------------|----------------------------------------------------------------------------------|-------------------------|
| MaCongThuc     | Long             | Định danh duy nhất (một phần) - Tham chiếu tới đối tượng CONG_THUC (composition) | Phiên bản công thức     |
| MaNguyenLieu   | int              | Định danh duy nhất (một phần) - Tham chiếu tới đối tượng NGUYEN_LIEU             | Nguyên liệu sử dụng     |
| DinhLuong      | double           | Phải lớn hơn 0                                                                   | Định lượng cho một suất |

Bảng 22. Thuộc tính và phương thức của lớp CHI_TIET_CONG_THUC

Phương thức chính: tinhDinhLuongNguyenLieu().

**a10. Lớp NGUYEN_LIEU**

Nguyên liệu kho; SoLuongTon được cập nhật bởi mọi giao dịch kho.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                    | **Mô tả**                                                                                                         |
|----------------|------------------|----------------------------------|-------------------------------------------------------------------------------------------------------------------|
| MaNguyenLieu   | int              | Định danh duy nhất của đối tượng | Định danh nguyên liệu                                                                                             |
| TenNguyenLieu  | String           | –                                | Tên nguyên liệu                                                                                                   |
| DonViTinh      | String           | –                                | Đơn vị tính chuẩn hóa                                                                                             |
| DaKhoaDonVi    | boolean          | –                                | Khóa sửa đơn vị sau khi đã tham chiếu                                                                             |
| MucTonToiThieu | double           | Không nhỏ hơn 0                  | Ngưỡng cảnh báo tồn riêng của nguyên liệu; nếu để trống thì dùng mức tồn tối thiểu mặc định của CAU_HINH_HE_THONG |
| SoNgayBaoQuan  | int              | –                                | Số ngày bảo quản chuẩn kể từ ngày nhập; để trống nếu nguyên liệu không quản lý hạn sử dụng                        |
| SoLuongTon     | double           | Không nhỏ hơn 0                  | Tổng tồn sổ sách của các lô, kể cả lô hết hạn. Lượng khả dụng được tính từ lô còn hạn sau khi trừ giữ món.        |
| Version        | int              | Tăng mỗi lần ghi nhận thay đổi   | Số phiên bản của bản ghi (NFR-07)                                                                                 |
| DaXoa          | boolean          | –                                | Cờ xóa mềm                                                                                                        |

Bảng 23. Thuộc tính và phương thức của lớp NGUYEN_LIEU

Phương thức chính: capNhatTonKho(soLuong); kiemTraDuoiMucToiThieu(); quyDoiDonVi().

**a11. Lớp NHA_CUNG_CAP**

Nhà cung cấp nguyên liệu, áp dụng xóa mềm khi đã có lịch sử nhập.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                    | **Mô tả**              |
|----------------|------------------|----------------------------------|------------------------|
| MaNCC          | int              | Định danh duy nhất của đối tượng | Định danh nhà cung cấp |
| TenNCC         | String           | –                                | Tên nhà cung cấp       |
| NguoiLienHe    | String           | –                                | Người liên hệ          |
| DienThoai      | String           | –                                | Số điện thoại          |
| Email          | String           | –                                | Thư điện tử            |
| DiaChi         | String           | –                                | Địa chỉ                |
| DaXoa          | boolean          | –                                | Cờ xóa mềm             |

Bảng 24. Thuộc tính và phương thức của lớp NHA_CUNG_CAP

Phương thức chính: capNhatThongTinLienHe().

**a12. Lớp BAN**

Bàn trong sơ đồ nhà hàng; hệ thống cập nhật trạng thái khi ghi nhận order, đổi bàn hoặc nhân viên xác nhận khách đã rời đi. Thanh toán không tự giải phóng bàn.

| **Thuộc tính**    | **Kiểu dữ liệu** | **Ràng buộc**                                                     | **Mô tả**                                                                                          |
|-------------------|------------------|-------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| MaBan             | int              | Định danh duy nhất của đối tượng                                  | Định danh bàn                                                                                      |
| TenBan            | String           | –                                                                 | Tên/số hiệu bàn                                                                                    |
| TenBan_Active     | String           | Giá trị suy ra tự động, không trùng lặp trong số các bàn chưa xóa | Tên hiển thị khi bàn chưa xóa mềm; cho phép đặt lại tên của một bàn đã xóa                         |
| SoChoNgoi         | int              | –                                                                 | Sức chứa (thông tin hiển thị tham khảo; không dùng để chặn order hay gợi ý xếp bàn)                |
| TrangThai         | String           | –                                                                 | Trống / Đang phục vụ; phản ánh khách còn sử dụng bàn, không phản ánh order đã thanh toán hay chưa. |
| MaOrderDangPhucVu | Long             | Tham chiếu tới ORDER đang chiếm bàn, NULL khi bàn Trống           | Chỉ order này được giải phóng bàn; thanh toán/đối soát của order cũ không ảnh hưởng order mới.     |
| DaXoa             | boolean          | –                                                                 | Cờ xóa mềm                                                                                         |

Bảng 25. Thuộc tính và phương thức của lớp BAN

Phương thức chính: giaiPhongBan(maOrder: Long); kiemTraTrangThaiHoatDong().

**a13. Lớp ORDER**

Đơn gọi món; chỉ được ghi nhận khi gửi món lần đầu.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                                                                                 | **Mô tả**                                                                                                                                  |
|----------------|------------------|-----------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| MaOrder        | Long             | Định danh duy nhất của đối tượng                                                              | Định danh order                                                                                                                            |
| MaOrderHienThi | String           | Không trùng lặp                                                                               | Mã tra cứu dạng ORD-ddMMyy-nnn                                                                                                             |
| BusinessDate   | LocalDate        | –                                                                                             | Business Date tại thời điểm gửi món đầu tiên của order; là ngày kinh doanh chuẩn cho hóa đơn, giao dịch thanh toán và báo cáo của order đó |
| MaBan          | int              | Tham chiếu tới đối tượng BAN (bắt buộc khi LoaiDon = Tại chỗ, để trống khi LoaiDon = Mang về) | Bàn phục vụ                                                                                                                                |
| LoaiDon        | String           | –                                                                                             | Tại chỗ / Mang về                                                                                                                          |
| TrangThai      | String           | –                                                                                             | Đang mở / Chờ xác nhận thanh toán / Đã thanh toán / Chờ xác minh thanh toán / Đóng – chưa thu được tiền / Đã hủy                           |
| TongTien       | double           | –                                                                                             | Tổng tiền order; nguồn in phiếu tạm tính trước khi thanh toán, chưa ghi nhận doanh thu                                                     |
| NguoiTao       | int              | Tham chiếu tới đối tượng NGUOI_DUNG                                                           | Nhân viên tạo order                                                                                                                        |
| ThoiDiemTao    | LocalDateTime    | –                                                                                             | Thời điểm gửi món đầu tiên                                                                                                                 |
| ThoiDiemDong   | LocalDateTime    | –                                                                                             | Thời điểm tất toán hoặc đóng                                                                                                               |
| LyDoHuy        | String           | –                                                                                             | Lý do hủy toàn bộ order                                                                                                                    |

Bảng 26. Thuộc tính và phương thức của lớp ORDER

Phương thức chính: taoOrder(maBan); themMonVaoOrder(maMon, soLuong); doiBan(maBanMoi); tinhTongTien(); huyOrder(lyDo); moLaiThanhToan(lyDo); dongOrderKhongThuDuocTien(lyDo, ketQuaXuLy).

**a14. Lớp CHI_TIET_ORDER**

Dòng món trong order, neo vào phiên bản giá và công thức tại thời điểm tạo.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                                                      | **Mô tả**                                                                           |
|----------------|------------------|--------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| MaChiTietOrder | Long             | Định danh duy nhất của đối tượng                                   | Định danh dòng món                                                                  |
| MaOrder        | Long             | Tham chiếu tới đối tượng ORDER                                     | Order chứa dòng món                                                                 |
| MaMon          | int              | Tham chiếu tới đối tượng MON_AN                                    | Món được gọi                                                                        |
| MaPhienBanGia  | Long             | Tham chiếu tới đối tượng LICH_SU_GIA_MON (cùng món với dòng order) | Phiên bản giá có hiệu lực khi dòng món được gửi; giữ nguyên về sau                  |
| MaCongThuc     | Long             | Tham chiếu tới đối tượng CONG_THUC (cùng món với dòng order)       | Phiên bản công thức có hiệu lực khi dòng món được gửi, dùng trừ kho và tính giá vốn |
| SoLuong        | int              | Phải lớn hơn 0                                                     | Số suất                                                                             |
| DonGia         | double           | –                                                                  | Đơn giá tại thời điểm gọi                                                           |
| ThanhTien      | double           | –                                                                  | Thành tiền dòng món                                                                 |
| GhiChu         | String           | –                                                                  | Yêu cầu đặc biệt                                                                    |
| TrangThai      | String           | –                                                                  | Chờ làm / Đã xác nhận xong / Đã phục vụ / Đã hủy                                    |
| ThoiDiemThem   | LocalDateTime    | –                                                                  | Thời điểm thêm vào order                                                            |

Bảng 27. Thuộc tính và phương thức của lớp CHI_TIET_ORDER

Phương thức chính: capNhatTrangThaiCheBien(); huyDongMon(lyDo).

**a15. Lớp LICH_SU_DOI_BAN**

Vết chuyển bàn của order đang mở.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                       | **Mô tả**         |
|----------------|------------------|-------------------------------------|-------------------|
| MaLichSuDoiBan | Long             | Định danh duy nhất của đối tượng    | Định danh bản ghi |
| MaOrder        | Long             | Tham chiếu tới đối tượng ORDER      | Order được chuyển |
| MaBanNguon     | int              | Tham chiếu tới đối tượng BAN        | Bàn nguồn         |
| MaBanDich      | int              | Tham chiếu tới đối tượng BAN        | Bàn đích          |
| ThoiDiem       | LocalDateTime    | –                                   | Thời điểm đổi bàn |
| NguoiThucHien  | int              | Tham chiếu tới đối tượng NGUOI_DUNG | Người thực hiện   |

Bảng 28. Thuộc tính và phương thức của lớp LICH_SU_DOI_BAN

Phương thức chính: ghiLichSuDoiBan(banCu, banMoi).

**a16. Lớp HOA_DON**

Hóa đơn chốt sau thanh toán thành công; order bị khóa sau khi phát sinh.

| **Thuộc tính**      | **Kiểu dữ liệu** | **Ràng buộc**                                      | **Mô tả**                                                                                                                                                         |
|---------------------|------------------|----------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| MaHoaDon            | Long             | Định danh duy nhất của đối tượng                   | Định danh hóa đơn                                                                                                                                                 |
| MaOrder             | Long             | Tham chiếu tới đối tượng ORDER, không trùng lặp    | Order tương ứng                                                                                                                                                   |
| MaGiaoDichThanhToan | Long             | Tham chiếu tới đối tượng GIAO_DICH_THANH_TOAN      | Giao dịch thanh toán thành công đã chốt hóa đơn này (truy vết khi có nhiều lần thử)                                                                               |
| SoHoaDon            | String           | Không trùng lặp                                    | Số hóa đơn                                                                                                                                                        |
| ThoiDiemXuat        | LocalDateTime    | –                                                  | Thời điểm xuất hóa đơn                                                                                                                                            |
| TongTien            | double           | –                                                  | Tổng tiền thanh toán                                                                                                                                              |
| PhuongThucThanhToan | String           | –                                                  | Tiền mặt / QR                                                                                                                                                     |
| NguoiLap            | int              | Tham chiếu tới đối tượng NGUOI_DUNG, cho phép NULL | Người xác nhận thanh toán dẫn đến hóa đơn (Thu ngân hoặc Quản lý); NULL khi hệ thống tự phát hành do webhook xác nhận                                             |
| SoLanIn             | int              | –                                                  | Số lần in                                                                                                                                                         |
| BusinessDate        | LocalDate        | –                                                  | Kế thừa BusinessDate của ORDER (không tính lại theo thời điểm xuất hóa đơn), để order đặt trước mốc giờ và thanh toán sau mốc giờ vẫn thuộc cùng một ngày báo cáo |

Bảng 29. Thuộc tính và phương thức của lớp HOA_DON

Phương thức chính: phatHanhHoaDon(); inLaiHoaDon().

**a17. Lớp GIAO_DICH_THANH_TOAN**

Lần thanh toán của order bằng tiền mặt hoặc QR; với QR gồm vòng đời mã QR và kết quả webhook.

| **Thuộc tính**      | **Kiểu dữ liệu** | **Ràng buộc**                        | **Mô tả**                                                                                                                                                                                 |
|---------------------|------------------|--------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| MaGiaoDichTT        | Long             | Định danh duy nhất của đối tượng     | Định danh giao dịch                                                                                                                                                                       |
| MaOrder             | Long             | Tham chiếu tới đối tượng ORDER       | Order được thanh toán                                                                                                                                                                     |
| PhuongThuc          | String           | –                                    | Tiền mặt / QR                                                                                                                                                                             |
| SoTien              | double           | –                                    | Số tiền giao dịch                                                                                                                                                                         |
| TrangThai           | String           | –                                    | Chờ xác nhận / Thành công / Hết hạn / Chờ xác minh thanh toán / Đóng – chưa thu được tiền / Đã hủy                                                                                        |
| MaQR                | String           | –                                    | Nội dung mã QR động; NULL khi thanh toán tiền mặt                                                                                                                                         |
| ThoiDiemTaoQR       | LocalDateTime    | –                                    | Thời điểm sinh mã QR; NULL khi thanh toán tiền mặt                                                                                                                                        |
| ThoiDiemHetHan      | LocalDateTime    | –                                    | Mốc hết hạn 10 phút; NULL khi thanh toán tiền mặt                                                                                                                                         |
| MaGiaoDichCong      | String           | –                                    | Mã giao dịch phía cổng thanh toán; duy nhất khi khác NULL, dùng chống ghi nhận webhook lặp; NULL khi thanh toán tiền mặt hoặc khi chưa có webhook                                         |
| NoiDungWebhook      | String           | –                                    | Dữ liệu webhook nhận được; NULL khi thanh toán tiền mặt                                                                                                                                   |
| MaGiaoDichNganHang  | String           | –                                    | Mã giao dịch của ngân hàng/ví điện tử mà khách dùng để quét QR, do Thu ngân nhập khi đối soát thủ công; duy nhất khi khác NULL, dùng đối chiếu webhook lặp của khoản đã xác nhận thủ công |
| AnhChungTu          | String           | –                                    | Đường dẫn ảnh chụp xác nhận giao dịch đính kèm khi đối soát, không bắt buộc                                                                                                               |
| BusinessDate        | LocalDate        | –                                    | Kế thừa BusinessDate của ORDER (không tính lại theo thời điểm tạo giao dịch), để mọi giao dịch của một order thuộc cùng một ngày báo cáo                                                  |
| TrangThaiNgoaiLe    | String           | Cho phép NULL                        | Chờ xử lý / Đã hoàn tiền / Đã áp dụng cho order; chỉ dùng khi có tiền QR đến muộn cần đối soát                                                                                            |
| SoTienNgoaiLe       | double           | Cho phép NULL                        | Số tiền cổng báo đã nhận trong tình huống ngoại lệ, không tự cộng doanh thu                                                                                                               |
| MaThamChieuHoan     | String           | Cho phép NULL                        | Mã tham chiếu hoàn tiền từ cổng/ngân hàng, khi kết quả là Đã hoàn tiền                                                                                                                    |
| ThoiDiemXuLyNgoaiLe | LocalDateTime    | Cho phép NULL                        | Thời điểm Quản lý chốt cách xử lý ngoại lệ                                                                                                                                                |
| NguoiXuLyNgoaiLe    | int              | Tham chiếu NGUOI_DUNG, cho phép NULL | Quản lý quyết định xử lý ngoại lệ; ghi audit log                                                                                                                                          |

Bảng 30. Thuộc tính và phương thức của lớp GIAO_DICH_THANH_TOAN

Phương thức chính: xacNhanTienMat(); xacNhanThanhToan(); xuLyWebhook(duLieu); kiemTraTrangThai(); luuKetQuaXacMinh(noiDung, bangChung); apDungKhoanTienDenMuon(); ghiNhanKetQuaHoanTien(maThamChieu, soTien).

**a18. Lớp PHIEU_BEP**

Các lượt in phiếu bếp, phục vụ in lại khi máy in lỗi.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                    | **Mô tả**                                |
|----------------|------------------|----------------------------------|------------------------------------------|
| MaPhieuBep     | Long             | Định danh duy nhất của đối tượng | Định danh phiếu bếp                      |
| MaOrder        | Long             | Tham chiếu tới đối tượng ORDER   | Order tương ứng                          |
| ThoiDiemIn     | LocalDateTime    | –                                | Thời điểm gửi lệnh in                    |
| TrangThaiIn    | String           | –                                | Thành công / Thất bại                    |
| SoLanIn        | int              | –                                | Số lần in lại                            |
| NoiDung        | String           | –                                | Danh sách món, số lượng, ghi chú được in |

Bảng 31. Thuộc tính và phương thức của lớp PHIEU_BEP

Phương thức chính: inPhieuBep(); ghiKetQuaIn(trangThai).

**a19. Lớp PHIEU_NHAP_KHO**

Phiếu nhập hàng từ nhà cung cấp.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                         | **Mô tả**            |
|----------------|------------------|---------------------------------------|----------------------|
| MaPhieuNhap    | Long             | Định danh duy nhất của đối tượng      | Định danh phiếu nhập |
| MaNCC          | int              | Tham chiếu tới đối tượng NHA_CUNG_CAP | Nhà cung cấp         |
| NgayNhap       | LocalDate        | –                                     | Ngày nhập hàng       |
| TongTien       | double           | –                                     | Tổng giá trị phiếu   |
| TrangThai      | String           | –                                     | Hiệu lực / Đã hủy    |
| NguoiLap       | int              | Tham chiếu tới đối tượng NGUOI_DUNG   | Bếp lập phiếu        |
| GhiChu         | String           | –                                     | Ghi chú              |

Bảng 32. Thuộc tính và phương thức của lớp PHIEU_NHAP_KHO

Phương thức chính: taoPhieuNhap(maNCC); xacNhanNhapKho().

**a20. Lớp CHI_TIET_PHIEU_NHAP**

Dòng nguyên liệu của phiếu nhập, là nguồn tính đơn giá bình quân.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                           | **Mô tả**                                                               |
|----------------|------------------|-----------------------------------------|-------------------------------------------------------------------------|
| MaChiTietNhap  | Long             | Định danh duy nhất của đối tượng        | Định danh dòng nhập                                                     |
| MaPhieuNhap    | Long             | Tham chiếu tới đối tượng PHIEU_NHAP_KHO | Phiếu nhập                                                              |
| MaNguyenLieu   | int              | Tham chiếu tới đối tượng NGUYEN_LIEU    | Nguyên liệu nhập                                                        |
| SoLuong        | double           | Phải lớn hơn 0                          | Số lượng theo đơn vị chuẩn                                              |
| DonViMuaGoc    | String           | –                                       | Đơn vị tính ghi trên hóa đơn nhà cung cấp (trước quy đổi)               |
| HeSoQuyDoi     | double           | Phải lớn hơn 0                          | Hệ số quy đổi từ DonViMuaGoc sang đơn vị tính chuẩn hóa của NGUYEN_LIEU |
| DonGia         | double           | –                                       | Đơn giá nhập                                                            |
| ThanhTien      | double           | –                                       | Thành tiền dòng nhập                                                    |

Bảng 33. Thuộc tính và phương thức của lớp CHI_TIET_PHIEU_NHAP

Phương thức chính: tinhThanhTien().

**a21. Lớp LO_NGUYEN_LIEU**

Từng lô nguyên liệu, tạo tự động khi ghi nhận một dòng nhập; theo dõi số lượng còn lại và hạn sử dụng riêng cho từng lô, làm căn cứ để xuất kho theo nguyên tắc nhập trước xuất trước (FIFO) và cảnh báo khi sắp/đã hết hạn.

| **Thuộc tính**    | **Kiểu dữ liệu** | **Ràng buộc**                                                                                                | **Mô tả**                                                                                                                                     |
|-------------------|------------------|--------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| MaLoNguyenLieu    | Long             | Định danh duy nhất của đối tượng                                                                             | Định danh lô nguyên liệu                                                                                                                      |
| MaNguyenLieu      | int              | Tham chiếu tới đối tượng NGUYEN_LIEU                                                                         | Nguyên liệu của lô                                                                                                                            |
| MaChiTietNhap     | Long             | Tham chiếu tới đối tượng CHI_TIET_PHIEU_NHAP, không trùng lặp; NULL khi LoDieuChinhKiemKe = true (BR-LOT-02) | Dòng nhập đã tạo ra lô này                                                                                                                    |
| LoDieuChinhKiemKe | boolean          | Mặc định false                                                                                               | Đánh dấu lô điều chỉnh do kiểm kê phát hiện thừa, không có dòng nhập nguồn (BR-LOT-02)                                                        |
| NgayNhap          | LocalDate        | –                                                                                                            | Ngày nhập của lô - lấy tự động từ PHIEU_NHAP_KHO.NgayNhap tại thời điểm ghi nhận dòng nhập, dùng để sắp xếp thứ tự xuất theo FIFO             |
| HanSuDung         | LocalDate        | –                                                                                                            | Hạn sử dụng của lô - hệ thống tự tính bằng NgayNhap cộng số ngày bảo quản của nguyên liệu; để trống nếu nguyên liệu đó không quản lý hạn dùng |
| SoLuongNhap       | double           | Phải lớn hơn 0                                                                                               | Số lượng ban đầu của lô                                                                                                                       |
| SoLuongConLai     | double           | Không nhỏ hơn 0                                                                                              | Số lượng còn lại chưa xuất dùng của lô                                                                                                        |
| DonGia            | double           | –                                                                                                            | Đơn giá nhập của lô                                                                                                                           |
| TrangThai         | String           | –                                                                                                            | Còn hạn / Sắp hết hạn (còn không quá SoNgayCanhBaoHetHan ngày) / Hết hạn / Đã dùng hết                                                        |

Bảng 34. Thuộc tính và phương thức của lớp LO_NGUYEN_LIEU

Phương thức chính: capNhatSoLuongConLai(sl); kiemTraHanSuDung(); apDungFIFO().

**a22. Lớp PHIEU_XUAT_KHO**

Phiếu xuất hủy cho hao hụt, hư hỏng, hết hạn.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                                         | **Mô tả**                                                                           |
|----------------|------------------|-------------------------------------------------------|-------------------------------------------------------------------------------------|
| MaPhieuXuat    | Long             | Định danh duy nhất của đối tượng                      | Định danh phiếu xuất                                                                |
| MaPhieuKiemKe  | Long             | Tham chiếu tới đối tượng PHIEU_KIEM_KE, cho phép NULL | Phiếu kiểm kê sinh ra phiếu xuất hủy tự động; NULL với phiếu xuất hủy do Bếp tự lập |
| LyDo           | String           | –                                                     | Hao hụt / Hư hỏng / Hết hạn                                                         |
| NgayXuat       | LocalDate        | –                                                     | Ngày xuất                                                                           |
| NguoiLap       | int              | Tham chiếu tới đối tượng NGUOI_DUNG                   | Bếp thực hiện                                                                       |
| GhiChu         | String           | –                                                     | Diễn giải                                                                           |
| NguonXuat      | String           | Nguyên liệu / Món đã chế biến / Kiểm kê               | Xác định nguồn chứng từ và cách ghi nhận giao dịch.                                 |

Bảng 35. Thuộc tính và phương thức của lớp PHIEU_XUAT_KHO

Phương thức chính: taoPhieuXuat(lyDo); xacNhanXuatKho().

**a23. Lớp CHI_TIET_PHIEU_XUAT**

Dòng nguyên liệu xuất thủ công, tính vào chi phí hao hụt.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                           | **Mô tả**                                                                                                                                                                            |
|----------------|------------------|-----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| MaChiTietXuat  | Long             | Định danh duy nhất của đối tượng        | Định danh dòng xuất                                                                                                                                                                  |
| MaPhieuXuat    | Long             | Tham chiếu tới đối tượng PHIEU_XUAT_KHO | Phiếu xuất                                                                                                                                                                           |
| MaNguyenLieu   | int              | Tham chiếu tới đối tượng NGUYEN_LIEU    | Nguyên liệu xuất                                                                                                                                                                     |
| SoLuong        | double           | Phải lớn hơn 0                          | Lượng nguyên liệu; nguồn Món đã chế biến được tự tính từ số suất hủy và tiêu hao gốc, hiển thị chỉ đọc.                                                                              |
| GiaVonUocTinh  | double           | –                                       | Giá trị hao hụt theo đơn giá bình quân; tạm thời bằng 0 khi GIA_BINH_QUAN_THANG của tháng phát sinh chưa được chốt, khi đó dòng dữ liệu được nhận diện là chưa hoàn tất tính giá vốn |
| MaChiTietOrder | Long             | FK; NULL theo nguồn                     | Dòng món đã chế biến bị bỏ; chỉ điền cho nguồn Món đã chế biến.                                                                                                                      |
| SoSuatHuy      | int              | Dương khi nguồn là món                  | Số suất người lập chọn để hủy; hệ thống tự tính lượng nguyên liệu theo tiêu hao gốc và kiểm tra cộng dồn theo dòng món.                                                              |

Bảng 36. Thuộc tính và phương thức của lớp CHI_TIET_PHIEU_XUAT

Phương thức chính: ghiLyDoXuat().

**a24. Lớp PHIEU_KIEM_KE**

Phiếu kiểm kê định kỳ, cơ chế điều chỉnh sai lệch tồn chính.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                       | **Mô tả**                                                    |
|----------------|------------------|-------------------------------------|--------------------------------------------------------------|
| MaPhieuKiemKe  | Long             | Định danh duy nhất của đối tượng    | Định danh phiếu kiểm kê                                      |
| NgayKiemKe     | LocalDate        | –                                   | Ngày kiểm kê                                                 |
| NguoiThucHien  | int              | Tham chiếu tới đối tượng NGUOI_DUNG | Người kiểm kê                                                |
| GhiChu         | String           | –                                   | Ghi chú                                                      |
| TrangThai      | String           | Đang kiểm kê / Đã xác nhận / Đã hủy | Chỉ một phiên Đang kiểm kê; dùng khóa nghiệp vụ trên server. |

Bảng 37. Thuộc tính và phương thức của lớp PHIEU_KIEM_KE

Phương thức chính: taoPhieuKiemKe(); doiChieuTon().

**a25. Lớp CHI_TIET_KIEM_KE**

Chênh lệch tồn của từng nguyên liệu trong một lần kiểm kê.

| **Thuộc tính** | **Kiểu dữ liệu** | **Ràng buộc**                          | **Mô tả**                               |
|----------------|------------------|----------------------------------------|-----------------------------------------|
| MaChiTietKK    | Long             | Định danh duy nhất của đối tượng       | Định danh dòng kiểm kê                  |
| MaPhieuKiemKe  | Long             | Tham chiếu tới đối tượng PHIEU_KIEM_KE | Phiếu kiểm kê                           |
| MaNguyenLieu   | int              | Tham chiếu tới đối tượng NGUYEN_LIEU   | Nguyên liệu đối chiếu                   |
| TonHeThong     | double           | –                                      | Tồn theo hệ thống                       |
| TonThucTe      | double           | –                                      | Tồn đếm thực tế                         |
| ChenhLech      | double           | Giá trị suy ra tự động                 | Chênh lệch giữa TonThucTe và TonHeThong |

Bảng 38. Thuộc tính và phương thức của lớp CHI_TIET_KIEM_KE

Phương thức chính: tinhChenhLech().

**a26. Lớp GIAO_DICH_KHO**

Sổ cái biến động kho; mọi thay đổi tồn đều sinh một bản ghi tại đây.

| **Thuộc tính**  | **Kiểu dữ liệu** | **Ràng buộc**                                                                       | **Mô tả**                                                                                                                  |
|-----------------|------------------|-------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| MaGiaoDichKho   | Long             | Định danh duy nhất của đối tượng                                                    | Định danh giao dịch kho                                                                                                    |
| MaNguyenLieu    | int              | Tham chiếu tới đối tượng NGUYEN_LIEU                                                | Nguyên liệu biến động                                                                                                      |
| LoaiGiaoDich    | String           | –                                                                                   | Nhập / Trừ tự động / Hoàn kho / Xuất thủ công / Điều chỉnh kiểm kê                                                         |
| SoLuongThayDoi  | double           | –                                                                                   | Lượng tăng (+) hoặc giảm (−)                                                                                               |
| TonSauGiaoDich  | double           | –                                                                                   | Tồn sau khi ghi nhận                                                                                                       |
| MaChiTietNhap   | Long             | Tham chiếu tới đối tượng CHI_TIET_PHIEU_NHAP (khi LoaiGiaoDich = Nhập)              | Dòng nhập nguồn                                                                                                            |
| MaChiTietOrder  | Long             | Tham chiếu tới đối tượng CHI_TIET_ORDER (khi LoaiGiaoDich = Trừ tự động / Hoàn kho) | Dòng order nguồn                                                                                                           |
| MaChiTietXuat   | Long             | Tham chiếu tới đối tượng CHI_TIET_PHIEU_XUAT (khi LoaiGiaoDich = Xuất thủ công)     | Dòng xuất thủ công nguồn                                                                                                   |
| MaChiTietKiemKe | Long             | Tham chiếu tới đối tượng CHI_TIET_KIEM_KE (khi LoaiGiaoDich = Điều chỉnh kiểm kê)   | Dòng chênh lệch kiểm kê nguồn                                                                                              |
| MaLoNguyenLieu  | Long             | Tham chiếu tới đối tượng LO_NGUYEN_LIEU                                             | Lô nguyên liệu bị ảnh hưởng - gắn lô mới tạo khi Nhập, hoặc lô bị trừ theo FIFO khi Trừ tự động / Xuất thủ công / Hoàn kho |
| ThoiDiem        | LocalDateTime    | –                                                                                   | Thời điểm phát sinh                                                                                                        |
| NguoiThucHien   | int              | Tham chiếu tới đối tượng NGUOI_DUNG (để trống nếu do hệ thống tự động ghi)          | Người thực hiện                                                                                                            |
| BusinessDate    | LocalDate        | –                                                                                   | Ngày kinh doanh, ghi tại thời điểm phát sinh giao dịch theo cutoff đang áp dụng                                            |

Bảng 39. Thuộc tính và phương thức của lớp GIAO_DICH_KHO

Phương thức chính: ghiGiaoDich(loai, soLuong); tinhTonTuSoCai().

**a27. Lớp GIA_BINH_QUAN_THANG**

Đơn giá bình quân gia quyền theo tháng được sử dụng để tính giá vốn và lợi nhuận gộp theo chi phí nguyên liệu. Quản lý tồn kho và định giá nguyên liệu sử dụng hai cơ chế: xuất kho theo lô FIFO để theo dõi hạn sử dụng; tính giá vốn theo đơn giá bình quân tháng để hạn chế biến động giữa các đơn do chênh lệch giá nhập của từng lô.

| **Thuộc tính**  | **Kiểu dữ liệu** | **Ràng buộc**                                                        | **Mô tả**                               |
|-----------------|------------------|----------------------------------------------------------------------|-----------------------------------------|
| MaNguyenLieu    | int              | Định danh duy nhất (một phần) - Tham chiếu tới đối tượng NGUYEN_LIEU | Nguyên liệu                             |
| Thang           | int              | Định danh duy nhất (một phần), định dạng YYYYMM (ví dụ 202609)       | Tháng tính giá                          |
| DonGiaBinhQuan  | double           | –                                                                    | Đơn giá bình quân gia quyền trong tháng |
| TongSoLuongNhap | double           | –                                                                    | Tổng lượng nhập trong tháng             |
| ThoiDiemTinh    | LocalDateTime    | –                                                                    | Thời điểm tính toán gần nhất            |

Bảng 40. Thuộc tính và phương thức của lớp GIA_BINH_QUAN_THANG

Phương thức chính: tinhGiaBinhQuanGiaQuyen(thang).

**a28. Lớp PHIEN_CHAT_AI**

Phiên hội thoại với trợ lý AI, gắn với vai trò để giới hạn phạm vi dữ liệu.

| **Thuộc tính**  | **Kiểu dữ liệu** | **Ràng buộc**                       | **Mô tả**                  |
|-----------------|------------------|-------------------------------------|----------------------------|
| MaPhien         | Long             | Định danh duy nhất của đối tượng    | Định danh phiên chat       |
| MaNguoiDung     | int              | Tham chiếu tới đối tượng NGUOI_DUNG | Người dùng của phiên       |
| MaVaiTro        | int              | Tham chiếu tới đối tượng VAI_TRO    | Vai trò tại thời điểm chat |
| ThoiDiemBatDau  | LocalDateTime    | –                                   | Thời điểm mở phiên         |
| ThoiDiemKetThuc | LocalDateTime    | –                                   | Thời điểm kết thúc phiên   |

Bảng 41. Thuộc tính và phương thức của lớp PHIEN_CHAT_AI

Phương thức chính: taoPhien(); dongPhien().

**a29. Lớp TRUY_VAN_AI**

Nhật ký từng lượt hỏi–đáp, phục vụ chức năng “Xem chi tiết” và đánh giá thực nghiệm.

| **Thuộc tính**  | **Kiểu dữ liệu** | **Ràng buộc**                          | **Mô tả**                                                                                                                        |
|-----------------|------------------|----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| MaTruyVan       | Long             | Định danh duy nhất của đối tượng       | Định danh lượt truy vấn                                                                                                          |
| MaPhien         | Long             | Tham chiếu tới đối tượng PHIEN_CHAT_AI | Phiên chat tương ứng                                                                                                             |
| PhamViDuLieu    | String           | –                                      | Danh sách view thực tế được dùng để sinh SQL, thuộc phạm vi cho phép của vai trò; phục vụ audit quyền truy cập dữ liệu (NFR-05). |
| CauHoi          | String           | –                                      | Câu hỏi tiếng Việt của người dùng                                                                                                |
| CauSQLSinhRa    | String           | –                                      | Câu SQL do LLM sinh sau kiểm duyệt                                                                                               |
| TrangThai       | String           | –                                      | Thành công / Yêu cầu làm rõ / Từ chối / Lỗi                                                                                      |
| KetQuaTomTat    | String           | –                                      | Bảng số liệu trả về (rút gọn)                                                                                                    |
| ThoiGianPhanHoi | int              | –                                      | Thời gian phản hồi (ms), phục vụ NFR về hiệu năng                                                                                |
| ThoiDiem        | LocalDateTime    | –                                      | Thời điểm đặt câu hỏi                                                                                                            |
| ModelPhienBan   | String           | Bắt buộc khi gọi LLM                   | Định danh model thực tế.                                                                                                         |
| TokenDauVao     | int              | Không âm                               | Tổng token đầu vào của các lần gọi.                                                                                              |
| TokenDauRa      | int              | Không âm                               | Tổng token đầu ra được tính phí, gồm token suy luận nếu có.                                                                      |
| ChiPhiUSD       | double           | Không âm                               | Chi phí theo đơn giá ghi nhận tại lần chạy.                                                                                      |
| SoLanGoi        | int              | Không âm                               | Gồm sinh SQL, thử lại và diễn giải.                                                                                              |

Bảng 42. Thuộc tính và phương thức của lớp TRUY_VAN_AI

Phương thức chính: sinhCauSQL(cauHoi); thucThiTruyVan(); ghiThoiGianPhanHoi().

**a30. Lớp GIU_CHO_MON**

Dòng món chưa gửi, lưu trên server và tách khỏi trạng thái chế biến của CHI_TIET_ORDER.

| **Thuộc tính** | **Kiểu**      | **Ràng buộc**                               | **Mô tả**                         |
|----------------|---------------|---------------------------------------------|-----------------------------------|
| MaGiuCho       | Long          | PK                                          | Định danh dòng giữ.               |
| MaLuotChon     | String        | Bắt buộc                                    | Nhóm dòng của một lượt chọn.      |
| MaNguoiDung    | int           | FK NGUOI_DUNG                               | Người được thao tác lượt chọn.    |
| MaBan          | int           | FK BAN; NULL với mang về                    | Bàn dự kiến, chưa chiếm bàn.      |
| MaOrder        | Long          | FK ORDER; có thể NULL                       | Order của phần gọi thêm.          |
| MaMon          | int           | FK MON_AN                                   | Món được chọn.                    |
| MaCongThuc     | Long          | FK CONG_THUC                                | Phiên bản dùng tính giữ.          |
| MaPhienBanGia  | Long          | FK LICH_SU_GIA_MON                          | Giá hiển thị lúc giữ.             |
| SoLuong        | int           | Lớn hơn 0                                   | Số suất chưa gửi.                 |
| GhiChu         | String        | Cho phép rỗng                               | Yêu cầu chế biến.                 |
| ThoiDiemHetHan | LocalDateTime | Bắt buộc                                    | Mốc hết hiệu lực theo giờ server. |
| TrangThai      | String        | Đang giữ / Hết hạn / Đã giải phóng / Đã gửi | Vòng đời giữ món.                 |
| MaYeuCauGui    | String        | Có thể NULL                                 | Mã chống xử lý lặp của lượt gửi.  |
| MaDongYeuCau   | String        | Có thể NULL                                 | Định danh dòng trong lần gửi.     |
| MaChiTietOrder | Long          | FK; UNIQUE; có thể NULL                     | Dòng món sinh sau khi gửi.        |

Bảng 43. Thuộc tính của lớp GIU_CHO_MON

Phương thức chính: taoGiuCho(); dieuChinhGiuCho(); giaiPhong(); guiMon().

**a31. Lớp CHI_TIET_GIU_CHO**

Mỗi dòng lưu lượng nguyên liệu giữ trên một lô; tổng các dòng của cùng nguyên liệu bằng số suất nhân định lượng công thức.

| **Thuộc tính** | **Kiểu** | **Ràng buộc**                    | **Mô tả**                                    |
|----------------|----------|----------------------------------|----------------------------------------------|
| MaGiuCho       | Long     | PK thành phần; FK GIU_CHO_MON    | Dòng món chưa gửi.                           |
| MaLoNguyenLieu | Long     | PK thành phần; FK LO_NGUYEN_LIEU | Lô được giữ theo FIFO.                       |
| SoLuongGiu     | double   | Lớn hơn 0                        | Lượng giữ theo đơn vị chuẩn của nguyên liệu. |

Bảng 44. Thuộc tính của lớp CHI_TIET_GIU_CHO

Phương thức chính: phanBoTheoLo(); tinhLuongGiuHieuLuc().
