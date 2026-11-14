# 06. TEST CASE VÀ KẾT QUẢ KIỂM TRA

Xây dựng hệ thống quản lý nhà hàng tích hợp AI hỗ trợ hoạt động kinh doanh

Test case chức năng, kết quả thực tế và kiểm tra hiệu năng cơ bản của hệ thống quản lý nhà hàng.

## F. Kiểm tra chức năng

Nhóm không phân công vai trò kiểm thử chuyên trách. Các thành viên tự kiểm tra chức năng đã xây dựng theo test case, đối chiếu kết quả mong đợi và ghi nhận lỗi để sửa. Thực hiện qua giao diện hoặc API phù hợp nội dung từng ca.

**F.1. Cấu trúc test case**

Mỗi ca ghi mã, yêu cầu liên quan, dữ liệu và điều kiện, bước thực hiện, kết quả mong đợi, ưu tiên, kết quả thực tế và trạng thái. Chỉ ghi Đạt khi đã xác nhận đủ đầu ra; các trạng thái khác là Không đạt, Chưa kiểm tra và Chưa kiểm tra đủ.

| **Trường**           | **Cách ghi**                                                                                                          | **Ví dụ**                                                |
|----------------------|-----------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------|
| Mã ca                | TC-\<module\>-\<số nguyên\>; không dùng mã phân nhánh.                                                                | TC-SALE-06                                               |
| FR/NFR               | Liệt kê các yêu cầu được kiểm tra trực tiếp.                                                                          | FR-SALE-03, FR-SALE-04, FR-SALE-31, FR-INV-03, FR-INV-13 |
| Điều kiện và dữ liệu | Trạng thái trước chạy, vai trò và dữ liệu khởi tạo; áp dụng quy ước F.2 nếu không ghi riêng.                          | B1 Trống; giữ 2 suất; L1 200 g, L2 800 g.                |
| Bước thực hiện       | Các thao tác theo thứ tự; chỉ rõ UI/API và cách giả lập lỗi nếu có.                                                   | 1\. Gửi món. 2. Đối chiếu order, kho, bàn, phiếu bếp.    |
| Kết quả mong đợi     | Kết quả kiểm chứng được, gồm trạng thái và số liệu sau thao tác.                                                      | Trừ L1 200 g, L2 100 g; tạo order một lần.               |
| Ưu tiên              | Trọng yếu hoặc Thường.                                                                                                | Trọng yếu                                                |
| Kết quả thực tế      | Ghi kết quả quan sát và thông báo lỗi nếu có; ghi ngày thực hiện. Không bắt buộc kèm ảnh hoặc đường dẫn log.          |                                                          |
| Trạng thái           | Đạt: đúng mọi đầu ra; Không đạt: có sai lệch; Chưa kiểm tra: chưa thực hiện; Chưa kiểm tra đủ: mới kiểm tra một phần. |                                                          |

Bảng 45. Cấu trúc bản ghi test case

**F.2. Bộ ca kiểm thử**

Bộ hiện hành gồm 258 ca chức năng: 51 Danh mục, 101 Bán hàng, 57 Kho, 9 Cài đặt, 15 Báo cáo và 25 điều kiện biên. Bốn bảng dưới gồm 218 ca; phần H trình bày các ca Báo cáo và điều kiện biên.

Kết quả chạy trên bản 568ec9f ngày 13/11/2026, môi trường thử riêng với cơ sở dữ liệu QA dựng từ đầu; các ca chạy qua API và script (ca giả lập thời điểm, lỗi hoặc tải đồng thời chạy qua tầng service), ca hiển thị được kiểm thêm trên giao diện: 258 đạt trên tổng 258 ca. Theo nhóm: Danh mục 51/51; Bán hàng 101/101; Kho 57/57; Cài đặt 9/9; Báo cáo 15/15; điều kiện biên 25/25. Kiểm thử tự động của bản này: 873 test API và 223 test web đạt; 25/26 test tích hợp MySQL đạt, test còn lại lỗi do giả định dữ liệu của chính test (người dùng \#1 phải là Quản lý), không do hệ thống.

Các ca Danh mục do Quản lý thực hiện, trừ ca ghi rõ vai trò khác. Các ca gọi món do Nhân viên order thực hiện; ca thanh toán do Thu ngân thực hiện; ca Kho do Bếp thực hiện, trừ ca phân quyền. Mọi tài khoản phải còn hiệu lực. Dữ liệu ngày, giờ dùng thời gian server; mốc Business Date trong ca hiệu lực là 06:00. Bò xào dùng 150 g thịt bò mỗi suất, không có nguyên liệu giới hạn khác, trừ khi ca quy định riêng.

<table>
<colgroup>
<col style="width: 9%" />
<col style="width: 7%" />
<col style="width: 14%" />
<col style="width: 14%" />
<col style="width: 17%" />
<col style="width: 7%" />
<col style="width: 17%" />
<col style="width: 9%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Mã ca</strong></th>
<th><strong>FR/NFR</strong></th>
<th><strong>Điều kiện và dữ liệu</strong></th>
<th><strong>Bước thực hiện</strong></th>
<th><strong>Kết quả mong đợi</strong></th>
<th><strong>Ưu tiên</strong></th>
<th><strong>Kết quả thực tế</strong></th>
<th><strong>Trạng thái</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>TC-CAT-01</td>
<td>FR-CAT-01</td>
<td>Chưa có nhóm Món nướng.</td>
<td>1. Thêm nhóm Món nướng.<br />
2. Lưu và mở lại danh sách.</td>
<td>Nhóm được lưu và hiển thị đúng tên.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Thêm nhóm 'Món nướng' → 201, #1; đọc lại danh sách nhóm: ['Món nướng']</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-02</td>
<td>FR-CAT-01</td>
<td>Có nhóm Món nướng.</td>
<td>1. Đổi tên thành Món nướng than.<br />
2. Lưu, tải lại.</td>
<td>Tên mới được lưu; mã nhóm và các món thuộc nhóm không đổi.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Đổi tên nhóm #1 → 200; đọc lại: #1 'Món nướng than', ThuTuHienThi 1; món Gà nướng thuộc nhóm #1</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-03</td>
<td>FR-CAT-01</td>
<td>Có ba nhóm A, B, C.</td>
<td>1. Chuyển C lên trước A.<br />
2. Lưu, tải lại.</td>
<td>Thứ tự hiển thị là C, A, B.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Sắp lại nhóm → 200; đọc lại thứ tự: ['Món nướng than', 'C', 'A', 'B']</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-04</td>
<td>FR-CAT-02, FR-CAT-06</td>
<td>Có nhóm Món nướng.</td>
<td>1. Thêm Bò nướng, giá 120.000 đ, nhóm Món nướng, ảnh hợp lệ.<br />
2. Lưu.</td>
<td>Món lưu đúng thuộc tính, thuộc một nhóm; ở trạng thái Nháp, chưa hiện khi gọi món.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Thêm Bò nướng 120.000 đ, nhóm #1, ảnh URL → 201, TrangThai 'Nháp', GiaHienTai 120000.0; danh sách món cho Thu ngân: [{"MaMon": 2, "TenMon": "Bò nướng", "MaNhomMon": 1, "HinhAnh": "https://example.com/bo-nuong.jpg", "GiaHienTai": 120000.0, "SoSuatKhaDung":…</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-05</td>
<td>FR-CAT-02</td>
<td>Có món Bò nướng và nhóm Món chính.</td>
<td>1. Sửa tên, ảnh và nhóm thành Món chính.<br />
2. Lưu, tải lại.</td>
<td>Lưu đúng dữ liệu mới; món chỉ thuộc nhóm Món chính.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Sửa tên, ảnh, nhóm → 200; CSDL: {"TenMon": "Bò nướng tảng", "HinhAnh": "https://example.com/bo-tang.jpg", "MaNhomMon": 5}</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-06</td>
<td>FR-CAT-02</td>
<td>Có Bò nướng và Gà nướng.</td>
<td>1. Tìm tên Bò.</td>
<td>Kết quả có Bò nướng, không có Gà nướng.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Tìm 'Bò' → ['Bò nướng tảng']</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-07</td>
<td>FR-CAT-03</td>
<td>Nhóm còn một món chưa xóa mềm.</td>
<td>1. Chọn xóa nhóm.<br />
2. Xác nhận.</td>
<td>Từ chối; nhóm và món không đổi.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Xóa nhóm #1 còn Gà nướng → 422 'Không thể xóa nhóm còn món đang hoạt động.'; DaXoa=0; Gà nướng vẫn thuộc nhóm #1</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-08</td>
<td>FR-CAT-03</td>
<td>Mọi món từng thuộc nhóm đã xóa mềm.</td>
<td>1. Chọn xóa nhóm.<br />
2. Xác nhận.</td>
<td>Xóa mềm nhóm; không cho chọn khi tạo món mới; lịch sử vẫn tham chiếu được; có audit log.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Nhóm A #2 chỉ có Món tạm đã xóa mềm: xóa → 204, DaXoa=1, NgayXoa=2026-11-13 17:07:07.919000; nhật ký {"LoaiThaoTac": "DELETE_GROUP", "DoiTuong": "NHOM_MON", "MaDoiTuong": "2", "DuLieuTruoc": null, "DuLieuSau": "{\"KieuXo…; tạo món mới vào nhóm → 422 'Nhóm món không tồn tại.'; Món tạm vẫn có MaNhomMon=2</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-09</td>
<td>FR-CAT-03</td>
<td>Nhóm chưa từng có món.</td>
<td>1. Chọn xóa nhóm.<br />
2. Xác nhận.</td>
<td>Xóa vĩnh viễn nhóm; có audit log.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Nhóm B #3 chưa từng có món: xóa → 204; còn 0 bản ghi; nhật ký {"LoaiThaoTac": "DELETE_GROUP", "DoiTuong": "NHOM_MON", "MaDoiTuong": "3", "DuLieuTruoc": null, "DuLieuSau": "{\"KieuXo…</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-10</td>
<td>FR-CAT-04, FR-CAT-28</td>
<td>Món đã có trong order lịch sử.</td>
<td>1. Xóa món.<br />
2. Kiểm tra gọi món, quản trị và order cũ.</td>
<td>Món bị xóa mềm, không còn trên màn hình gọi món; quản trị và order cũ vẫn tra cứu được; có audit log; không có thao tác xóa vĩnh viễn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Gà xào 04 #4 đã có trong order #1: xóa → 204, DaXoa=1, nhật ký có; danh sách Thu ngân không còn món; giữ món → 422 'Món không tồn tại hoặc đã bị xóa.'; quản trị (include_deleted) có; chi tiết order cũ hiển thị tên món</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-11</td>
<td>FR-CAT-07, FR-CAT-11</td>
<td>Món Nháp; thịt bò còn hạn 1.000 g.</td>
<td>1. Gán công thức thịt bò 150 g/suất.<br />
2. Lưu.</td>
<td>Công thức có hiệu lực ngay; món rời Nháp, được gọi khi đủ nguyên liệu.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Bò nướng tảng (Nháp), thịt bò còn hạn 1.000 g: gán công thức 150 g/suất → 201 'Đang áp dụng'; danh sách Thu ngân: [{"MaMon": 2, "TenMon": "Bò nướng tảng", "MaNhomMon": 5, "HinhAnh": "https://example.com/bo-tang.jpg", "GiaHienTai": 120000.0, "SoSuatKhaDung": 6, "TrangThai":…; giữ 1 suất → 201</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-12</td>
<td>FR-CAT-12</td>
<td>Chưa có nguyên liệu Thịt bò.</td>
<td>1. Bếp thêm Thịt bò, đơn vị g, ngưỡng riêng 500 g.<br />
2. Lưu.</td>
<td>Lưu đúng tên, đơn vị và ngưỡng riêng.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Bếp thêm Thịt bò, g, ngưỡng 500 → 201; CSDL {"TenNguyenLieu": "Thịt bò", "DonViTinh": "g", "MucTonToiThieu": "500.000000"}</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-13</td>
<td>FR-CAT-12</td>
<td>Ngưỡng mặc định 300 g.</td>
<td>1. Thêm Hành không đặt ngưỡng riêng.</td>
<td>Nguyên liệu dùng ngưỡng mặc định 300 g.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Ngưỡng mặc định 300 → 200; thêm Hành không đặt ngưỡng → 201, CSDL MucTonToiThieu=None; màn tồn kho: [{"MaNguyenLieu": 4, "TenNguyenLieu": "Hành", "DonViTinh": "g", "SoLuongTon": 0.0, "DonGiaBinhQuan": null, "GiaTriTon": null, "SoLuongDuDieuKien": 0.0, "SoLuongGiu": 0.0, "SoLuongKhaDung": 0.0, "MucTonToiThieuApDung": 3…</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-14</td>
<td>FR-CAT-12</td>
<td>Có nguyên liệu Hành.</td>
<td>1. Sửa tên thành Hành lá.<br />
2. Lưu, tìm theo tên mới.</td>
<td>Lưu tên mới và tìm được đúng nguyên liệu.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Đổi tên Hành → 'Hành lá': 200; tìm 'Hành lá' → [4]</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-15</td>
<td>FR-CAT-15</td>
<td>Chưa có nhà cung cấp A.</td>
<td>1. Bếp thêm A kèm thông tin liên hệ.<br />
2. Lưu.</td>
<td>Nhà cung cấp và thông tin liên hệ được lưu.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Bếp thêm NCC A kèm liên hệ → 201; trả {"MaNhaCungCap": 1, "TenNhaCungCap": "NCC A", "SoDienThoai": "0901000001", "Email": "a@example.com", "NguoiLienHe": "Anh Ba", "DiaChi": "Hà Nội", "DaXoa": false, "PhieuNhap": []}</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-16</td>
<td>FR-CAT-15</td>
<td>Nhà cung cấp A đã có một phiếu nhập.</td>
<td>1. Sửa thông tin liên hệ A.<br />
2. Mở lịch sử nhập của A.</td>
<td>Thông tin mới được lưu; lịch sử vẫn hiển thị đúng phiếu nhập của A.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): NCC A có phiếu nhập #3: sửa liên hệ → 200 (PATCH trả 1 phiếu); chi tiết NCC: 0901000009, Chị Tư, lịch sử [{"MaPhieuNhap": 3, "NgayNhap": "2026-11-13T17:07:09.280000", "TrangThai": "Hiệu lực", "TongTien": 200000.0}]</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-17</td>
<td>FR-CAT-14</td>
<td>Nguyên liệu đã có phiếu nhập, chưa có công thức.</td>
<td>1. Thử đổi đơn vị g sang kg.</td>
<td>Từ chối đổi đơn vị; dữ liệu cũ giữ nguyên.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Thịt bò đã có phiếu nhập #3, chưa có công thức: đổi g→kg → 422 'Không thể đổi đơn vị tính sau khi đã được sử dụng.'; CSDL giữ g</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-18</td>
<td>FR-CAT-14</td>
<td>Nguyên liệu đã có trong công thức, chưa có phiếu nhập.</td>
<td>1. Thử đổi đơn vị g sang kg.</td>
<td>Từ chối đổi đơn vị; dữ liệu cũ giữ nguyên.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Tỏi có trong công thức Gà nướng tỏi, chưa có phiếu nhập: đổi g→kg → 422 'Không thể đổi đơn vị tính sau khi đã được sử dụng.'; CSDL giữ g</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-19</td>
<td>FR-CAT-13</td>
<td>Nguyên liệu đã có trong công thức.</td>
<td>1. Xóa nguyên liệu.</td>
<td>Chỉ xóa mềm; dữ liệu tham chiếu lịch sử còn nguyên; có audit log.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Tỏi trong công thức: Bếp xóa → 204, DaXoa=1; dòng công thức {"MaCongThuc": 3, "DinhLuong": "10.000000"}; API công thức vẫn hiển thị tên Tỏi; nhật ký có</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-20</td>
<td>FR-CAT-13</td>
<td>Nguyên liệu đã có phiếu nhập lịch sử.</td>
<td>1. Xóa nguyên liệu.</td>
<td>Chỉ xóa mềm; dữ liệu tham chiếu lịch sử còn nguyên; có audit log.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Nấm có phiếu nhập #4: xóa → 204, DaXoa=1; chi tiết phiếu nhập vẫn hiện tên Nấm; nhật ký có</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-21</td>
<td>FR-CAT-16</td>
<td>Nhà cung cấp có lịch sử nhập hàng.</td>
<td>1. Xóa nhà cung cấp.</td>
<td>Chỉ xóa mềm; phiếu nhập cũ vẫn tham chiếu được; có audit log.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): NCC Z có phiếu nhập #5: xóa → 204, DaXoa=1; phiếu nhập vẫn đọc được, MaNhaCungCap=2; nhật ký có</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-22</td>
<td>FR-CAT-20</td>
<td>Bò xào đang dùng giá 100.000 đ; mốc Business Date 06:00.</td>
<td>1. Lên lịch giá 110.000 đ cho ngày kế tiếp.<br />
2. Gửi món lúc 05:59:59 và 06:00:00, xác nhận phiên bản mới nếu được yêu cầu.</td>
<td>Dòng trước mốc dùng 100.000 đ; dòng từ mốc dùng 110.000 đ; dòng cũ không đổi; lưu phiên bản.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): Bò xào giá 100.000 (#22), lịch 110.000 (#23) cho Business Date 14/11, mốc 06:00. Gửi qua tầng service với đồng hồ 05:59:59 ngày 14/11 → order #8 Business Date 13/11, DonGia 100.000, phiên bản #22; lúc 06:00:00 → order #9 Business Date 14/11, DonGia 110.000, phiên bản #23</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-23</td>
<td>FR-CAT-20</td>
<td>Có món Bò xào.</td>
<td>1. Lên lịch giá vào Business Date đã bắt đầu.</td>
<td>Từ chối lưu lịch; không thay đổi phiên bản đang áp dụng.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Lên lịch giá 95.000 cho Business Date 13/11 (đã bắt đầu) → 422 'BusinessDate áp dụng phải là ngày trong tương lai.'; giá đang áp dụng [100000.0]</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-24</td>
<td>FR-CAT-20</td>
<td>Có món Bò xào.</td>
<td>1. Lên lịch giá vào Business Date đã kết thúc.</td>
<td>Từ chối lưu lịch; không thay đổi phiên bản đang áp dụng.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Lên lịch giá cho Business Date 12/11 (đã kết thúc) → 422 'BusinessDate áp dụng phải là ngày trong tương lai.'; giá đang áp dụng [100000.0]</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-25</td>
<td>FR-CAT-20</td>
<td>Có món Bò xào.</td>
<td>1. Chọn Business Date sau ngày kế tiếp cho giá mới.<br />
2. Lưu.</td>
<td>Lịch được lưu đúng ngày tương lai; chưa áp dụng trước mốc đã chọn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Lên lịch 105.000 cho 18/11 → 201, #7 'Chờ áp dụng' ngày 2026-11-18; giá đang áp dụng [100000.0]</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-26</td>
<td>FR-CAT-21</td>
<td>Có lịch giá A đang chờ.</td>
<td>1. Tạo lịch giá B.<br />
2. Lưu.</td>
<td>B thay A; chỉ còn một lịch chờ của loại đó; có audit log ghi đè.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Có lịch A #7 chờ; tạo lịch B 108.000 ngày 19/11 → 201 #8; lịch chờ còn lại [(8, 108000.0)]; nhật ký {"LoaiThaoTac": "SCHEDULE_PRICE_CHANGE", "DoiTuong": "LICH_SU_GIA_MON", "MaDoiTuong": "8", "DuLieuTruoc": "{\"LichBiGhiDe\": [{\"Gia\": 105000.0, \"NgayHieuLuc\": \"2026-11-18\", \"MaPhienBanGia\": 7}]}", "DuLieuSau": "…</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-27</td>
<td>FR-CAT-22</td>
<td>Có lịch giá đang chờ.</td>
<td>1. Hủy lịch giá.<br />
2. Xác nhận.</td>
<td>Lịch chờ bị hủy; phiên bản đang áp dụng không đổi; có audit log.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Hủy lịch giá #10 (108.000, 16/11) đang chờ → 204; còn [(9, 80000.0, 'Đang áp dụng')]; nhật ký CANCEL_PRICE_CHANGE trước={"Gia": 108000.0, "TrangThai": "Chờ áp dụng", "NgayHieuLuc": "2026-11-16"}</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-28</td>
<td>FR-CAT-23, FR-CAT-24, FR-CAT-25</td>
<td>Có giá hiện tại và lịch thay đổi đang chờ.</td>
<td>1. Sửa trực tiếp giá.<br />
2. Lưu, gửi một dòng mới.</td>
<td>Giá mới có hiệu lực ngay, tạo phiên bản và audit log; dòng cũ giữ nguyên; lịch chờ không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Mực xào 80.000 (#9), lịch 90.000 (#11) chờ. Sửa trực tiếp 85.000 → 201 #12 'Đang áp dụng', #9 'Hết hiệu lực', lịch #11 'Chờ áp dụng'; nhật ký APPLY_PRICE_DIRECTLY có; gửi 1 Mực xào: DonGia 85000.00, phiên bản #12</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-29</td>
<td>FR-CAT-05</td>
<td>Món có lịch giá đang chờ.</td>
<td>1. Xóa mềm món.</td>
<td>Lịch chờ tương ứng bị hủy.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Món thử xóa #8 có lịch giá 55.000 (#14) chờ: xóa mềm → 204; lịch #14 chuyển 'Hết hiệu lực'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-30</td>
<td>FR-CAT-08</td>
<td>Bò xào đang dùng công thức 150 g; mốc Business Date 06:00.</td>
<td>1. Lên lịch công thức 180 g cho ngày kế tiếp.<br />
2. Gửi món lúc 05:59:59 và 06:00:00, xác nhận phiên bản mới nếu được yêu cầu.</td>
<td>Dòng trước mốc dùng 150 g; dòng từ mốc dùng 180 g; dòng cũ không đổi; lưu phiên bản.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): Cùng lượt với TC-CAT-22: công thức 150 g (#19), lịch 180 g (#20) cho 14/11. Dòng gửi 05:59:59 dùng #19, trừ 150 g (GiaTri −30.000 đ); dòng 06:00:00 dùng #20, trừ 180 g (−36.000 đ)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-31</td>
<td>FR-CAT-08</td>
<td>Có món Bò xào.</td>
<td>1. Lên lịch công thức vào Business Date đã bắt đầu.</td>
<td>Từ chối lưu lịch; không thay đổi phiên bản đang áp dụng.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Lên lịch công thức 160 g cho 13/11 (đã bắt đầu) → 422 'BusinessDate áp dụng phải là ngày trong tương lai.'; công thức đang áp dụng [(8, [150.0])]</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-32</td>
<td>FR-CAT-08</td>
<td>Có món Bò xào.</td>
<td>1. Lên lịch công thức vào Business Date đã kết thúc.</td>
<td>Từ chối lưu lịch; không thay đổi phiên bản đang áp dụng.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Lên lịch công thức cho 12/11 (đã kết thúc) → 422 'BusinessDate áp dụng phải là ngày trong tương lai.'; công thức đang áp dụng [(8, [150.0])]</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-33</td>
<td>FR-CAT-08</td>
<td>Có món Bò xào.</td>
<td>1. Chọn Business Date sau ngày kế tiếp cho công thức mới.<br />
2. Lưu.</td>
<td>Lịch được lưu đúng ngày tương lai; chưa áp dụng trước mốc đã chọn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Lên lịch công thức 160 g cho 18/11 → 201 #9 'Chờ áp dụng' ngày 2026-11-18; đang áp dụng [(8, [150.0])]</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-34</td>
<td>FR-CAT-09</td>
<td>Có lịch công thức A đang chờ.</td>
<td>1. Tạo lịch công thức B.<br />
2. Lưu.</td>
<td>B thay A; chỉ còn một lịch chờ của loại đó; có audit log ghi đè.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Có lịch A #9 chờ; tạo lịch B 170 g ngày 19/11 → 201 #10; lịch chờ còn [10]; nhật ký {"LichBiGhiDe": [{"MaCongThuc": 9, "NguyenLieu": [{"SoLuong": 160.0, "MaNguyenLieu": 8}], "NgayHieuLuc": "2026-11-18"}]}</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-35</td>
<td>FR-CAT-10</td>
<td>Có lịch công thức đang chờ.</td>
<td>1. Hủy lịch công thức.<br />
2. Xác nhận.</td>
<td>Lịch chờ bị hủy; phiên bản đang áp dụng không đổi; có audit log.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Hủy lịch công thức #10 → 204; lịch chờ còn []; đang áp dụng [(8, [150.0])]; nhật ký CANCEL_RECIPE_CHANGE có</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-36</td>
<td>FR-CAT-23, FR-CAT-24, FR-CAT-25</td>
<td>Có công thức hiện tại và lịch thay đổi đang chờ.</td>
<td>1. Sửa trực tiếp công thức.<br />
2. Lưu, gửi một dòng mới.</td>
<td>Công thức mới có hiệu lực ngay, tạo phiên bản và audit log; dòng cũ giữ nguyên; lịch chờ không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Mực xào công thức 150 g (#5), lịch 170 g (#11) chờ. Sửa trực tiếp 160 g → 201 #12 'Đang áp dụng', #5 'Hết hiệu lực', lịch #11 'Chờ áp dụng'; nhật ký có; order #3 dùng công thức #12, trừ 160.000000 g</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-37</td>
<td>FR-CAT-05</td>
<td>Món có lịch công thức đang chờ.</td>
<td>1. Xóa mềm món.</td>
<td>Lịch chờ tương ứng bị hủy.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Cùng món #8 có lịch công thức 120 g (#7) chờ; sau khi xóa mềm món, lịch chuyển 'Hết hiệu lực'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-38</td>
<td>FR-CAT-26, FR-CAT-27</td>
<td>Món đủ nguyên liệu, đang phục vụ.</td>
<td>1. Bật tạm dừng thủ công.</td>
<td>Hiển thị Tạm dừng phục vụ; không cho thêm món.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Mực xào đủ nguyên liệu: bật tạm dừng → 200 'Tạm dừng phục vụ'; danh sách Thu ngân 'Tạm dừng phục vụ' (16 suất); giữ món → 422 'Món Mực xào đang tạm dừng phục vụ.'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-39</td>
<td>FR-CAT-26, FR-CAT-27</td>
<td>Món tạm dừng thủ công và đủ nguyên liệu.</td>
<td>1. Tắt tạm dừng thủ công.</td>
<td>Món được mở lại và cho thêm vào lượt chọn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Tắt tạm dừng Mực xào → 'Hoạt động'; Thu ngân giữ 1 suất → 201</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-40</td>
<td>FR-CAT-26, FR-CAT-27</td>
<td>Món vừa tạm dừng thủ công vừa thiếu nguyên liệu.</td>
<td>1. Xem lý do chặn.<br />
2. Tắt tạm dừng thủ công.</td>
<td>Trước khi tắt hiển thị đủ hai lý do; sau khi tắt vẫn Hết nguyên liệu và không cho gọi.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Gà nướng sả (Gà chưa nhập kho) và tạm dừng: danh sách Quản lý {"TrangThai": "Hết nguyên liệu", "TamDungThuCong": true, "SoSuatKhaDung": 0}; giữ món → 422 'Món Gà nướng sả đang hết nguyên liệu và tạm dừng phục vụ.'. Tắt tạm dừng: 'Hết nguyên liệu', giữ món → 422 'Món Gà nướng sả đang hết nguyên liệu.'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-41</td>
<td>FR-CAT-27</td>
<td>Món đã có công thức; khả dụng không đủ một suất.</td>
<td>1. Xem trạng thái và thử thêm món.</td>
<td>Hiển thị Hết nguyên liệu, chặn thêm; thuộc tính này được suy ra, không lưu trong MON_AN.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Gà nướng tỏi, Tỏi 10 g/suất, Tỏi chưa có tồn: danh mục 'Hết nguyên liệu' – 0 suất; giữ món → 422 'Món Gà nướng tỏi C41 đang hết nguyên liệu.'; cột MON_AN: ['MaMon', 'TenMon', 'MaNhomMon', 'DaXoa', 'HinhAnh', 'ChuaCoCongThuc', 'TamDungThuCong']</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-42</td>
<td>FR-CAT-17</td>
<td>Chưa có bàn B1.</td>
<td>1. Thêm bàn B1.<br />
2. Lưu.</td>
<td>Bàn được lưu, hiển thị Trống, chưa gắn order.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Thêm bàn B1 (Tầng 1, 4 chỗ) → 201; CSDL {"TrangThai": "Trống", "MaOrderDangPhucVu": null}</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-43</td>
<td>FR-CAT-17</td>
<td>Bàn B1 đang Trống.</td>
<td>1. Sửa tên thành B01.<br />
2. Lưu.</td>
<td>Tên mới được lưu; mã bàn và trạng thái không đổi.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Sửa B1 → B01: 200; CSDL {"MaBan": 1, "TenBan": "B01", "TrangThai": "Trống"}</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-44</td>
<td>FR-CAT-17, FR-CAT-19</td>
<td>Bàn đang phục vụ order O1.</td>
<td>1. Thử xóa bàn.</td>
<td>Từ chối; bàn vẫn gắn O1.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): B5 đang phục vụ order #4: xóa bàn → 422 'Không thể xóa bàn đang được sử dụng.'; CSDL {"TrangThai": "Đang phục vụ", "MaOrderDangPhucVu": 4, "DaXoa": 0}</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-45</td>
<td>FR-CAT-19</td>
<td>Bàn Trống, đã có order lịch sử.</td>
<td>1. Xóa bàn.</td>
<td>Chỉ xóa mềm; giữ tham chiếu lịch sử và ghi audit log.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): B7 Trống, có order lịch sử #5: xóa bàn → 204; CSDL {"TenBan": "B7", "DaXoa": 1, "TenBan_Active": null}; order #5 vẫn tham chiếu MaBan 3; nhật ký DELETE_TABLE có</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-46</td>
<td>FR-INV-07</td>
<td>Nguyên liệu có ngưỡng riêng 500 g.</td>
<td>1. Nhập ngưỡng -1 g.<br />
2. Lưu.</td>
<td>Từ chối giá trị âm; ngưỡng cũ giữ nguyên.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Ngưỡng riêng 500; PATCH MucTonToiThieu=-1 → 422; CSDL giữ 500.0</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-47</td>
<td>NFR-04</td>
<td>Đăng nhập vai trò Bếp.</td>
<td>1. Gọi trực tiếp API sửa giá món với dữ liệu hợp lệ.</td>
<td>Backend từ chối quyền; dữ liệu không thay đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Bếp gọi apply-now → 403, schedule → 403; LICH_SU_GIA_MON 1 → 1 bản ghi</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-48</td>
<td>NFR-04</td>
<td>Đăng nhập vai trò Thu ngân.</td>
<td>1. Gọi trực tiếp API thêm bàn với dữ liệu hợp lệ.</td>
<td>Backend từ chối quyền; dữ liệu không thay đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Thu ngân tạo bàn B99 → 403; BAN 3 → 3 bản ghi</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-49</td>
<td>FR-CAT-29</td>
<td>Bò xào giá bán 80.000 đ; công thức 150 g bò (đơn giá bình quân 230.000 đ/kg) và 50 g hành (40.000 đ/kg); TyLeGiaVonCanhBao = 40%.</td>
<td>1. Đăng nhập Quản lý, mở danh sách món.2. Chọn Bò xào để xem chi tiết giá vốn.</td>
<td>Giá vốn ước tính 36.500 đ (34.500 + 2.000); tỷ lệ giá vốn 45,6%; lãi gộp 43.500 đ/suất; món được đánh dấu cảnh báo; chi tiết hiển thị hai nguyên liệu với định lượng, đơn giá và thành tiền.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Bò xào hành 80.000, ngưỡng 40.0%: giá vốn 36500.0, tỷ lệ 45.63%, lãi gộp 43500.0, CanhBao=True; chi tiết [('Bò thăn C49', 150.0, 230.0, 34500.0), ('Hành tây C49', 50.0, 40.0, 2000.0)]; Thu ngân xem giá vốn → 403</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-50</td>
<td>FR-CAT-29, FR-INV-02</td>
<td>Như TC-CAT-49 nhưng đơn giá bình quân của bò là 180.000 đ/kg: giá vốn 29.000 đ, tỷ lệ 36,25%, chưa cảnh báo.</td>
<td>1. Nhập kho bò với giá cao hơn để đơn giá bình quân tăng lên 230.000 đ/kg.2. Mở lại danh sách món.</td>
<td>Giá vốn của Bò xào cập nhật thành 36.500 đ, tỷ lệ 45,6% và có cảnh báo; giá bán vẫn 80.000 đ, hệ thống không tự đổi giá bán.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Bò thăn 1.000 g × 180 đ: giá vốn 29000.0, tỷ lệ 36.25%, CanhBao=False. Nhập thêm 1.000 g × 280 đ (bình quân 230): giá vốn 36500.0, tỷ lệ 45.63%, CanhBao=True; giá bán vẫn [80000.0]</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-51</td>
<td>FR-CAT-29</td>
<td>Công thức Gỏi gà có Sả, nguyên liệu chưa có đơn giá bình quân.</td>
<td>1. Mở danh sách món, tìm Gỏi gà.</td>
<td>Cột giá vốn hiển thị “Chưa đủ dữ liệu” kèm tên Sả; không tính Sả bằng 0; không hiển thị tỷ lệ giá vốn hay cảnh báo cho món.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Gỏi gà: Gà 100 g (đơn giá 90) + Sả 10 g (chưa nhập): TinhTrang 'Chưa đủ dữ liệu', GiaVonUocTinh None, TyLe None, CanhBao False, thiếu giá ['Sả C51']; ThanhTien của Sả None</td>
<td>Đạt</td>
</tr>
</tbody>
</table>

Bảng 46. Ca kiểm thử module Quản lý danh mục

Các ca Bán hàng kiểm tra thao tác trên lượt chọn và order, trạng thái món, phiếu bếp và liên kết bàn. Khi ca yêu cầu Bếp xác nhận chưa chế biến, người kiểm thử thực hiện trao đổi trực tiếp trước thao tác hủy hoặc giảm món.

<table>
<colgroup>
<col style="width: 9%" />
<col style="width: 7%" />
<col style="width: 14%" />
<col style="width: 14%" />
<col style="width: 17%" />
<col style="width: 7%" />
<col style="width: 17%" />
<col style="width: 9%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Mã ca</strong></th>
<th><strong>FR/NFR</strong></th>
<th><strong>Điều kiện và dữ liệu</strong></th>
<th><strong>Bước thực hiện</strong></th>
<th><strong>Kết quả mong đợi</strong></th>
<th><strong>Ưu tiên</strong></th>
<th><strong>Kết quả thực tế</strong></th>
<th><strong>Trạng thái</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>TC-SALE-01</td>
<td>FR-SALE-01, FR-INV-10</td>
<td>B1 Trống; bò khả dụng 1.000 g; công thức 150 g/suất.</td>
<td>1. Thêm 2 suất Bò xào.</td>
<td>Giữ 300 g, khả dụng còn 700 g; lưu người/lượt chọn, phiên bản và hạn giữ; chưa tạo order, phiếu bếp hay chiếm bàn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Bàn B01 Trống; giữ 2 suất Bò xào → 201, lượt giữ #12: người dùng #2, mã lượt chọn, bàn #4, MaOrder None, phiên bản giá #24, công thức #21, hạn giữ 299 giây; giữ theo lô [(14, 200.0), (15, 100.0)]; tồn 1000 g, khả dụng 700 g; bàn Trống, chưa có order, phiếu bếp; menu còn 4 suất</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-02</td>
<td>FR-SALE-01, FR-INV-10</td>
<td>Bò khả dụng 149 g; công thức 150 g/suất.</td>
<td>1. Thêm 1 suất Bò xào.</td>
<td>Từ chối, không tạo lượng giữ.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Khả dụng 149 g, công thức 150 g: giữ 1 suất → 422 'Món Bò xào S02 đang hết nguyên liệu.'; lượt giữ 0→0; khả dụng 149</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-03</td>
<td>FR-SALE-01, FR-INV-10</td>
<td>Bò khả dụng 150 g; công thức 150 g/suất.</td>
<td>1. Thêm 1 suất Bò xào.</td>
<td>Giữ thành công 150 g; khả dụng còn 0 g, tồn sổ sách không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Khả dụng 150 g: giữ 1 suất → 201; giữ 150, khả dụng 0, tồn sổ sách 150</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-04</td>
<td>FR-SALE-02</td>
<td>Món hợp lệ, kho đủ.</td>
<td>1. Thêm món.<br />
2. Nhập ghi chú không hành.<br />
3. Gửi và xem phiếu bếp.</td>
<td>Ghi chú in đúng dòng món. Công thức và lượng trừ kho theo định lượng chuẩn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Gà xào tại bàn, giữ 1 suất kèm ghi chú 'không hành', gửi → 201; dòng GhiChu 'không hành'; phiếu bếp {"items": [{"MaPhieuBep": 10, "NoiDung": "Order ORD-131126-008 - B4 S04\nGà xào S04 x1 (không hành) - 80000", "TrangThai": "Chờ in", "TrangThaiIn": "Chờ in", "SoLanIn": 0, "LoiIn": null, "ThoiDiemIn"…; trừ kho -150 g</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-05</td>
<td>FR-SALE-02</td>
<td>Món hợp lệ, kho đủ.</td>
<td>1. Thêm món.<br />
2. Để trống ghi chú.<br />
3. Gửi và xem phiếu bếp.</td>
<td>Gửi được khi không có ghi chú. Công thức và lượng trừ kho theo định lượng chuẩn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Gửi 1 Gà xào mang về, không ghi chú → 201; GhiChu None; phiếu bếp {"items": [{"MaPhieuBep": 11, "NoiDung": "Order ORD-131126-009 - Mang về\nGà xào S04 x1 - 80000", "TrangThai": "Chờ in", "TrangThaiIn": "Chờ in", "SoLanIn": 0,…; trừ -150 g</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-06</td>
<td>FR-SALE-03, FR-SALE-04, FR-SALE-31, FR-INV-03, FR-INV-13</td>
<td>B1 Trống; giữ 2 suất; L1 nhập trước còn 200 g, L2 còn 800 g.</td>
<td>1. Gửi món.<br />
2. Đối chiếu order, kho, bàn và phiếu bếp.</td>
<td>Một transaction tạo order/dòng món; trừ L1 200 g, L2 100 g; ghi giao dịch từng lô; kết thúc giữ; tạo dữ liệu phiếu bếp; B1 gắn order và Đang phục vụ. In sau commit.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Bàn Trống, lượt chọn giữ 2 suất; lô L1 #50 200 g, L2 #51 800 g. Gửi món → 201; 1 order #79, một dòng 2 suất 100000 'Chờ làm'; sổ kho [(50, -200.0, -40000.0), (51, -100.0, -20000.0)]; lượt giữ 'Đã gửi'; bàn 'Đang phục vụ', MaOrderDangPhucVu=79; phiếu bếp #85 'Order ORD-131126-074 - B01 S06<br />
Bò S06 xào x2 - 50000'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-07</td>
<td>FR-SALE-03</td>
<td>Lần gửi đã commit nhưng phía người dùng timeout.</td>
<td>1. Gửi lại cùng mã yêu cầu.</td>
<td>Trả kết quả cũ; chỉ một order, không trừ kho hoặc tạo dòng món lần hai.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Gửi mang về với request_id X → 201 order #12; gửi lại tuần tự cùng X → 201 order #12; 1 ORDER mang mã X, 1 dòng món; giao dịch kho 4→4</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-08</td>
<td>FR-SALE-03, NFR-07</td>
<td>Lượt chọn hợp lệ; ghi lại tồn và lượng giữ trước gửi.</td>
<td>1. Tiêm lỗi sau khi trừ kho, trước commit.<br />
2. Gửi món.</td>
<td>Rollback toàn bộ; không có order mới; tồn và lượng giữ về đúng trạng thái trước gửi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): Lượt chọn giữ 2 suất (300 g). Tiêm lỗi vào bước ghi phiếu bếp — sau khi đã trừ kho trong transaction (trong phiên đã có giao dịch Trừ tự động, nguyên liệu có 2 giao dịch: 1 nhập, 1 trừ), trước commit — rồi gửi: lỗi 'QA tiêm lỗi sau khi trừ kho, trước commit'; sau rollback số giao dịch kho (136→136) và số order (70→70) không đổi; tồn 1000 g, lô 1000 g, lượt giữ vẫn 'Đang giữ'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-09</td>
<td>FR-SALE-04</td>
<td>Business Date mới chưa có order.</td>
<td>1. Gửi hai order hợp lệ liên tiếp.</td>
<td>Mã ORD-ddMMyy-001 và 002 theo Business Date; mã khác nhau.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, Script): Business Date 15/11 chưa có order (0); hai order gửi liên tiếp qua tầng service (đồng hồ 10:00:00 và 10:00:05 ngày 15/11) nhận ORD-151126-001 và ORD-151126-002; phần ngày theo Business Date</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-10</td>
<td>FR-SALE-04</td>
<td>Một mã đã được cấp cho transaction sau đó rollback.</td>
<td>1. Gửi order hợp lệ kế tiếp.</td>
<td>Không dùng lại số đã cấp; mã mới duy nhất.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Lượt gửi bị từ chối 422 do thiếu nguyên liệu giữa hai order, và 3 yêu cầu gửi trùng đồng thời (rollback sau khi cấp số): các mã kế tiếp ['ORD-131126-011', 'ORD-131126-012', 'ORD-131126-013', 'ORD-131126-016']; 14 mã trong ngày, không trùng</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-11</td>
<td>FR-SALE-04</td>
<td>Business Date trước đã có order.</td>
<td>1. Sang Business Date kế tiếp.<br />
2. Gửi order đầu tiên.</td>
<td>Phần ngày theo Business Date mới, số bắt đầu 001; mã không trùng ngày trước.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, Script): Business Date 15/11 đã có order (tới ORD-151126-002); order đầu tiên của Business Date 16/11 (gửi 06:00:00 ngày 16/11) nhận ORD-161126-001, BusinessDate 16/11, số bắt đầu 001</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-12</td>
<td>FR-SALE-05, FR-SET-04</td>
<td>Thời hạn giữ 5 phút; hết hạn nhưng còn đủ nguyên liệu.</td>
<td>1. Đợi qua hạn.<br />
2. Gửi món.</td>
<td>Dòng báo hết thời gian giữ; backend kiểm tra lại và gửi thành công; không tự gia hạn trước gửi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Thời hạn giữ 5 phút; lượt giữ đã quá hạn (lùi hạn 1 giây), kho đủ. Gửi không xác nhận → 422 'Món Gà xào S04 (1 suất): Lượt giữ chỗ đã hết hạn. Xác nhận dùng giá và định lượng hiện tại để gửi món.'; ThoiDiemHetHan giữ nguyên; gửi có xác nhận → 201 order #19</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-13</td>
<td>FR-SALE-05</td>
<td>Giữ đã hết hạn; order khác dùng nguyên liệu, còn thiếu một suất.</td>
<td>1. Gửi lượt chọn cũ.</td>
<td>Từ chối, nêu món và số lượng thiếu; giữ danh sách chọn; không ghi tiêu hao.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Bê tồn 300 g; lượt giữ 2 suất đã hết hạn; Thu ngân 2 gửi 1 suất order khác → 201. Gửi lượt chọn cũ có xác nhận → 422 'Không đủ nguyên liệu cho món Bê xào 13: cần 2 suất, chỉ còn đủ 1 suất (thiếu 1 suất).'; giao dịch 2→2; lượt giữ còn 'Đang giữ' 2 suất</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-14</td>
<td>FR-SALE-05</td>
<td>Giá đổi sau khi giữ món.</td>
<td>1. Gửi mà chưa xác nhận phiên bản mới.</td>
<td>Yêu cầu xác nhận nội dung mới; chưa tạo dòng order hay tiêu hao.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Giữ 1 Vịt xào (90.000), Quản lý sửa giá 95.000. Gửi chưa xác nhận → 422 'Món Vịt xào 14 (1 suất): Giá hoặc công thức món đã thay đổi. Xác nhận dùng giá và định lượng hiện tại để gửi món.'; dòng order 0; giao dịch kho 1→1</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-15</td>
<td>FR-SALE-05</td>
<td>Giá đổi sau khi giữ; kho đủ theo phiên bản mới.</td>
<td>1. Xác nhận nội dung mới.<br />
2. Gửi món.</td>
<td>Gửi thành công với phiên bản mới; trừ đúng công thức mới áp dụng; không trừ lặp.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Gửi có xác nhận → 201; DonGia 95000, phiên bản #31; trừ -150 g (1 giao dịch)</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-16</td>
<td>FR-SALE-05</td>
<td>Công thức đổi sau khi giữ món.</td>
<td>1. Gửi mà chưa xác nhận phiên bản mới.</td>
<td>Yêu cầu xác nhận nội dung mới; chưa tạo dòng order hay tiêu hao.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Giữ 1 Vịt xào, Quản lý sửa công thức 150 → 180 g. Gửi chưa xác nhận → 422 'Món Vịt xào 14 (1 suất): Giá hoặc công thức món đã thay đổi. Xác nhận dùng giá và định lượng hiện tại để gửi món.'; dòng 1→1, giao dịch 2→2</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-17</td>
<td>FR-SALE-05</td>
<td>Công thức đổi sau khi giữ; kho đủ theo phiên bản mới.</td>
<td>1. Xác nhận nội dung mới.<br />
2. Gửi món.</td>
<td>Gửi thành công với phiên bản mới; trừ đúng công thức mới áp dụng; không trừ lặp.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Gửi lại có xác nhận → 201; dòng dùng công thức #28; trừ -180 g (1 giao dịch)</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-18</td>
<td>FR-SALE-06, FR-SALE-31</td>
<td>Order tại chỗ Đang mở còn gắn B1; kho đủ.</td>
<td>1. Thêm 1 suất.<br />
2. Gửi phần gọi thêm.</td>
<td>Tạo dòng và phiếu bếp phần mới; trừ đúng phần thêm; dòng cũ không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order tại chỗ #10 đang mở, còn gắn bàn: giữ thêm 1 suất và gửi phần gọi thêm → 201; dòng mới #21 'Chờ làm'; dòng cũ #10 giữ nguyên giá, công thức; phiếu bếp 1→2, phiếu mới Order ORD-131126-008 - B4 S04<br />
Gà xào S04 x1 - 80000; trừ -150 g</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-19</td>
<td>FR-SALE-06</td>
<td>Order tại chỗ đã rời bàn.</td>
<td>1. Thử gọi thêm vào order.</td>
<td>Từ chối gọi thêm theo phạm vi FR-SALE-06; không giữ hoặc trừ nguyên liệu.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Order tại chỗ #23 đang mở; xác nhận khách rời bàn → 200, bàn Trống, MaOrderDangPhucVu None. Giữ món gọi thêm → 422 'Order đã được giải phóng khỏi bàn, không thể gọi thêm.'; khả dụng 1650→1650; thêm dòng trực tiếp → 422 'Order đã được giải phóng khỏi bàn, không thể gọi thêm.'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-20</td>
<td>FR-SALE-06, FR-SALE-31</td>
<td>Order mang về Đang mở; kho đủ; có món đã gửi.</td>
<td>1. Thêm 1 suất vào lượt gọi thêm. 2. Gửi phần gọi thêm.</td>
<td>Bổ sung dòng món và phiếu bếp vào cùng order; giữ rồi trừ đúng nguyên liệu phần thêm; dòng cũ giữ nguyên giá/công thức; không gắn bàn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order mang về #24 đã có món; giữ thêm 1 suất và gửi phần gọi thêm → 201; 2 dòng trong cùng order, 2 phiếu bếp; lượt giữ 'Đã gửi'; dòng cũ giữ giá 80000, công thức #24; MaBan None</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-21</td>
<td>FR-SALE-08</td>
<td>Đang giữ 2 suất; khả dụng đủ thêm 150 g.</td>
<td>1. Tăng lên 3 suất.</td>
<td>Giữ thêm 150 g, số lượng 3; làm mới thời hạn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Tôm tồn 450 g; giữ 2 suất; tăng lên 3 → 200; SoLuong 3, giữ 450, khả dụng 0; hạn giữ 17:17:09.941000 → 17:17:11.093000</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-22</td>
<td>FR-SALE-08</td>
<td>Đang giữ 2 suất; khả dụng chỉ 100 g.</td>
<td>1. Tăng lên 3 suất.</td>
<td>Từ chối; số lượng, lượng giữ và hạn giữ cũ không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Tôm tồn 400 g; giữ 2 suất (300 g), khả dụng 100; tăng lên 3 → 422 'Không đủ nguyên liệu cho món Tôm 22 rang: cần 3 suất, chỉ còn đủ 2 suất (thiếu 1 suất).'; SoLuong 2, giữ 300, hạn giữ không đổi (True)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-23</td>
<td>FR-SALE-08</td>
<td>Đang giữ 2 suất, 300 g.</td>
<td>1. Giảm xuống 1 suất.</td>
<td>Giải phóng 150 g; còn giữ 150 g; tồn sổ sách không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Lượt giữ 2 suất 300 g; giảm xuống 1 → 200; giữ 150 g, khả dụng 250, tồn 400; giao dịch kho 1→1</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-24</td>
<td>FR-SALE-08</td>
<td>Dòng chưa gửi đang giữ 300 g.</td>
<td>1. Xóa dòng.</td>
<td>Giải phóng đủ 300 g; không có giao dịch hoàn tồn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng chưa gửi giữ 2 suất 300 g; xóa dòng → 200 'Đã giải phóng'; giữ 0, khả dụng 400; giao dịch kho 1→1 (không hoàn tồn)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-25</td>
<td>FR-SALE-08</td>
<td>Lượt chọn có hai dòng đang giữ.</td>
<td>1. Bỏ toàn bộ lượt chọn.</td>
<td>Giải phóng toàn bộ lượng giữ của lượt chọn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Lượt chọn có hai dòng đang giữ; bỏ toàn bộ lượt chọn → 200 {"released": 2}; trạng thái ['Đã giải phóng', 'Đã giải phóng']; lượng giữ còn 0</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-26</td>
<td>FR-SALE-08</td>
<td>Dòng đang giữ còn hiệu lực; ghi lại hạn giữ.</td>
<td>1. Sửa ghi chú.</td>
<td>Ghi chú cập nhật; hạn giữ không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng B đang giữ, hạn 17:19:35.753000; sửa ghi chú 'ít cay' sau 1,2 giây → 200; GhiChu 'ít cay', hạn giữ 17:19:35.753000</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-27</td>
<td>FR-SALE-08</td>
<td>Dòng đang giữ còn hiệu lực; ghi lại hạn giữ.</td>
<td>1. Mở lại màn hình lượt chọn.</td>
<td>Hạn giữ không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Mở lại lượt chọn (GET /sales/holds?selection_code=…) → 200; hạn giữ trả về ['2026-11-13T17:19:35.675000', '2026-11-13T17:19:35.753000'], khớp giá trị đã lưu</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-28</td>
<td>FR-SALE-08</td>
<td>Hai dòng A, B đang giữ; ghi lại hạn giữ A.</td>
<td>1. Sửa ghi chú dòng B.</td>
<td>Hạn giữ dòng A không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Hai dòng A, B; hạn A 17:19:35.675000; sau khi sửa ghi chú dòng B, hạn A 17:19:35.675000</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-29</td>
<td>FR-SALE-08</td>
<td>Lượt giữ còn hiệu lực.</td>
<td>1. Đóng trình duyệt, đợi quá hạn; mở lại bằng phiên hợp lệ.</td>
<td>Giữ hết hiệu lực theo giờ server; khả dụng được giải phóng dù trình duyệt đã đóng.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Lượt giữ 100 g bị bỏ dở (không gửi, không giải phóng, bản ghi vẫn 'Đang giữ'); trước hạn khả dụng 400; sau khi quá ThoiDiemHetHan theo giờ server, khả dụng 500, giữ 0, dù chưa có tác vụ dọn</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-30</td>
<td>FR-SALE-01, FR-SALE-03</td>
<td>Kho đủ; chọn đơn mang về.</td>
<td>1. Thêm món.<br />
2. Gửi.</td>
<td>Tạo order, trừ kho, tạo phiếu bếp; không gắn hay đổi trạng thái bàn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Gửi 1 Gà xào mang về → 201; ORDER MaBan None, LoaiDon 'Mang về'; 1 phiếu bếp; trừ -150 g; trạng thái và liên kết của 7 bàn không đổi</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-31</td>
<td>FR-SALE-07, FR-SALE-10, FR-INV-04</td>
<td>Dòng Chờ làm gồm 2 suất; đã in; Bếp xác nhận trực tiếp chưa làm; đã trừ L1 200 g, L2 100 g.</td>
<td>1. Hủy cả dòng, nhập lý do.</td>
<td>Hoàn L1 200 g và L2 100 g; ghi người, thời gian, số lượng, lý do; không yêu cầu bản ghi xác nhận bếp trong hệ thống.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng #26 2 suất Chờ làm, đã trừ [(27, -200.0), (28, -100.0)]. Hủy cả dòng với lý do → 200; dòng 'Đã hủy'; Hoàn kho [(27, 200.0), (28, 100.0)]; lô còn [200.0, 800.0]; nhật ký CANCEL_ORDER_LINE người #2, lý do 'Khách đổi món, bếp xác nhận chưa làm'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-32</td>
<td>FR-SALE-07, FR-SALE-10, FR-INV-04</td>
<td>Dòng Chờ làm 2 suất, trừ cùng lô 300 g; Bếp xác nhận chưa làm.</td>
<td>1. Giảm 1 suất, nhập lý do.</td>
<td>Còn 1 suất; hoàn đúng 150 g vào lô gốc; có audit log.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng 2 suất Chờ làm, trừ −300 g lô #29. Giảm còn 1 không lý do → 422 'Cần nhập lý do khi giảm số lượng món đã gửi.' (giữ 2); có lý do → 200, còn 1 suất; Hoàn kho [(29, 150.0)]; nhật ký REDUCE_ORDER_LINE có</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-33</td>
<td>FR-SALE-07, FR-SALE-10</td>
<td>Dòng ở trạng thái Đã xác nhận xong.</td>
<td>1. Thử giảm số lượng.</td>
<td>Từ chối; dòng món và tồn kho không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng ở 'Đã xác nhận xong': giảm số lượng → 422 'Chỉ sửa món ở trạng thái Chờ.'; dòng vẫn 2 suất 'Đã xác nhận xong'; giao dịch kho 2→2</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-34</td>
<td>FR-SALE-07, FR-SALE-10</td>
<td>Dòng ở trạng thái Đã xác nhận xong.</td>
<td>1. Thử xóa dòng.</td>
<td>Từ chối; dòng món và tồn kho không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng ở 'Đã xác nhận xong': hủy dòng → 422 'Chỉ hủy món ở trạng thái Chờ.'; dòng vẫn 2 suất 'Đã xác nhận xong'; giao dịch kho 2→2</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-35</td>
<td>FR-SALE-07, FR-SALE-10</td>
<td>Dòng ở trạng thái Đã phục vụ.</td>
<td>1. Thử giảm số lượng.</td>
<td>Từ chối; dòng món và tồn kho không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng ở 'Đã phục vụ': giảm số lượng → 422 'Chỉ sửa món ở trạng thái Chờ.'; dòng vẫn 2 suất 'Đã phục vụ'; giao dịch kho 2→2</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-36</td>
<td>FR-SALE-07, FR-SALE-10</td>
<td>Dòng ở trạng thái Đã phục vụ.</td>
<td>1. Thử xóa dòng.</td>
<td>Từ chối; dòng món và tồn kho không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng ở 'Đã phục vụ': hủy dòng → 422 'Chỉ hủy món ở trạng thái Chờ.'; dòng vẫn 2 suất 'Đã phục vụ'; giao dịch kho 2→2</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-37</td>
<td>FR-SALE-09</td>
<td>Món Chờ làm; đã xác nhận thực tế phù hợp.</td>
<td>1. Nhân viên chuyển sang Đã xác nhận xong.</td>
<td>Lưu đúng trạng thái mới; không trừ hoặc hoàn kho thêm.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Chuyển dòng Chờ làm → 'Đã xác nhận xong': 200, lưu 'Đã xác nhận xong'; giao dịch kho 2→2</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-38</td>
<td>FR-SALE-09</td>
<td>Món Đã xác nhận xong; đã xác nhận thực tế phù hợp.</td>
<td>1. Nhân viên chuyển sang Đã phục vụ.</td>
<td>Lưu đúng trạng thái mới; không trừ hoặc hoàn kho thêm.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Chuyển 'Đã xác nhận xong' → 'Đã phục vụ': 200, lưu 'Đã phục vụ'; giao dịch kho 2→2</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-39</td>
<td>FR-SALE-09</td>
<td>Món Chờ làm.</td>
<td>1. Gọi API chuyển thẳng sang Đã phục vụ.</td>
<td>Từ chối chuyển bỏ qua bước; trạng thái giữ nguyên.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng Chờ làm, chuyển thẳng 'Đã phục vụ' → 422 'Không thể chuyển từ Chờ làm sang Đã phục vụ.'; trạng thái giữ 'Chờ làm'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-40</td>
<td>FR-SALE-09</td>
<td>Món Đã phục vụ.</td>
<td>1. Thử chuyển về Chờ làm.</td>
<td>Từ chối chuyển ngược; trạng thái giữ nguyên.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng 'Đã phục vụ', chuyển về 'Chờ làm' → 422 'Không thể chuyển từ Đã phục vụ sang Chờ làm.'; trạng thái giữ 'Đã phục vụ'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-41</td>
<td>FR-SALE-01, FR-SALE-08</td>
<td>Nhân viên đang chọn món tại bàn Trống; có nhiều dòng giữ hiệu lực; chưa gửi lần đầu.</td>
<td>1. Chọn Hủy lượt chọn (Cancel).<br />
2. Kiểm tra giỏ, lượng giữ, tồn, order và bàn.</td>
<td>Giỏ trống; kết thúc mọi dòng giữ của đúng lượt chọn và giải phóng lượng giữ ngay; tồn sổ sách không đổi; không tạo order, phiếu bếp hoặc hóa đơn; bàn vẫn Trống.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Bàn Trống, lượt chọn 2 dòng giữ (1 và 2 suất, giữ 450 g); Hủy lượt chọn → 200 {"released": 2}; ['Đã giải phóng', 'Đã giải phóng']; giữ 0, tồn 2850→2850; bàn Trống, 0 order</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-42</td>
<td>FR-SALE-08, FR-INV-10</td>
<td>Lượt chọn chưa gửi có 2 suất; mỗi suất cần 150 g nguyên liệu, đang giữ 300 g.</td>
<td>1. Bấm trừ 1 suất.<br />
2. Kiểm tra lượt giữ và lượng khả dụng sau khi yêu cầu thành công.</td>
<td>Còn 1 suất và giữ 150 g; giải phóng 150 g để lượt khác sử dụng ngay; tồn sổ sách không đổi; chưa tạo order hoặc tiêu hao.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Lượt chọn chưa gửi 2 suất (300 g); trừ còn 1 → 200; khả dụng 2550→2700; tồn không đổi; giao dịch kho 2→2</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-43</td>
<td>FR-SALE-12, FR-CAT-18</td>
<td>O1 ở B1; B2 Trống.</td>
<td>1. Đổi O1 sang B2.</td>
<td>Cùng transaction: B1 Trống/bỏ liên kết; B2 Đang phục vụ/gắn O1; có audit log.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): O1 #34 ở B8, B7 Trống: chuyển sang B7 → 200; B8 {"TrangThai": "Trống", "MaOrderDangPhucVu": null}; B7 {"TrangThai": "Đang phục vụ", "MaOrderDangPhucVu": 34}; ORDER.MaBan=11; nhật ký MOVE_ORDER_TABLE người #2</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-44</td>
<td>FR-SALE-12</td>
<td>O1 ở B1; B2 phục vụ O2.</td>
<td>1. Thử chuyển O1 sang B2.</td>
<td>Từ chối; cả hai bàn và order không đổi.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): O1 #34 ở B7, B9 phục vụ O2 #35: chuyển O1 sang B9 → 422 'Bàn đích đang bận.'; B7/34, B9/35</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-45</td>
<td>FR-SALE-12</td>
<td>Order cũ đã giải phóng bàn.</td>
<td>1. Thử đổi order cũ sang bàn Trống.</td>
<td>Từ chối; không gắn lại bàn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): O1 #34 đã giải phóng khỏi B7; chuyển sang B8 (Trống) → 422 'Order không còn gắn với bàn đang phục vụ.'; B8 {"TrangThai": "Trống", "MaOrderDangPhucVu": null}</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-46</td>
<td>FR-CAT-18</td>
<td>B1 phục vụ O1; còn lượt chọn gọi thêm chưa gửi.</td>
<td>1. Xác nhận khách rời B1.</td>
<td>B1 Trống/bỏ liên kết O1; kết thúc lượt chọn, giải phóng lượng giữ; có audit log.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): B9 phục vụ O2 #35, còn lượt chọn gọi thêm chưa gửi (giữ 1 suất); xác nhận khách rời → 200; B9 {"TrangThai": "Trống", "MaOrderDangPhucVu": null}; lượt giữ 'Đã giải phóng'; nhật ký RELEASE_TABLE trước={"MaOrderDangPhucVu": 35} sau={"TrangThai": "Trống"}</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-47</td>
<td>FR-SALE-32</td>
<td>Máy in lỗi; lượt chọn hợp lệ.</td>
<td>1. Gửi món.</td>
<td>Order vẫn được commit, tồn trừ đúng; hiển thị lỗi in.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Máy in thử 127.0.0.1:9109 (không có dịch vụ). Gửi 1 Cá kho mang về → 201, order 'Đang mở', trừ -100 g; phiếu bếp #36 TrangThaiIn 'Thất bại', SoLanIn 3, LoiIn 'Không kết nối được máy in.'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-48</td>
<td>FR-SALE-32, FR-SALE-03</td>
<td>Order đã ghi nhận, in lần đầu lỗi.</td>
<td>1. In lại phiếu bếp hai lần.</td>
<td>In lại cùng nội dung; không tạo thêm order/dòng món hoặc trừ kho thêm.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiếu bếp #36 in lần đầu lỗi; in lại hai lần → 200, 200; vẫn 1 phiếu cùng nội dung, 'Thất bại', SoLanIn 6; dòng order 1→1; giao dịch kho 76→76</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-49</td>
<td>FR-SALE-03, FR-CAT-18</td>
<td>Hai người chọn cùng B1 Trống; kho đủ cả hai.</td>
<td>1. Đồng thời gửi hai lượt chọn khác nhau.</td>
<td>Chỉ một order được gắn B1; yêu cầu còn lại bị từ chối, không tiêu hao cho lượt thất bại.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Bàn Trống; hai Thu ngân gửi đồng thời hai lượt chọn khác nhau: mã [201, 422]; bàn gắn #37; yêu cầu thua 'Bàn đang phục vụ. Hãy giải phóng bàn trước khi mở order mới.'; 1 order cho bàn; giao dịch kho +1</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-50</td>
<td>FR-SALE-03, NFR-04</td>
<td>Đăng nhập Bếp; có dữ liệu gửi món hợp lệ.</td>
<td>1. Gọi API gửi món.</td>
<td>Backend từ chối; không tạo order hoặc tiêu hao.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Bếp gọi POST /sales/orders với dữ liệu hợp lệ → 403; giao dịch kho 5→5</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-51</td>
<td>FR-INV-11, NFR-04</td>
<td>Người B không được phép thao tác lượt chọn của A.</td>
<td>1. B gửi yêu cầu sửa lượt chọn của A.</td>
<td>Từ chối truy cập; lượt chọn và lượng giữ của A không đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Lượt giữ #58 của seed_cashier; seed_cashier2 PATCH tăng số lượng → 404 'Không tìm thấy lượt giữ chỗ.', DELETE → 404; lượt giữ vẫn 1 suất 'Đang giữ'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-52</td>
<td>FR-SALE-14, 33</td>
<td>Thu ngân đăng nhập; QR còn hạn; khách quét lỗi và xác nhận chưa chuyển tiền.</td>
<td>1. Hủy QR.<br />
2. Tạo QR mới.</td>
<td>QR cũ Đã hủy; chỉ có một QR mới còn hiệu lực; chưa phát hành hóa đơn và không chuyển Chờ xác minh.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order mang về có QR #2 còn hạn; hủy QR → 200; tạo QR mới → 201 #3; giao dịch [(2, 'Đã hủy'), (3, 'Chờ xác nhận')]; hóa đơn 0; order 'Chờ xác nhận thanh toán'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-53</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Chờ xác nhận thanh toán; kho đủ.</td>
<td>1. Thử thêm món và gửi phần gọi thêm.</td>
<td>Từ chối gọi thêm; không tạo dòng món, không giữ hoặc trừ thêm nguyên liệu; giữ nguyên trạng thái order.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order mang về ở 'Chờ xác nhận thanh toán' (có QR): giữ món gọi thêm → 422 'Order không còn mở.'; thêm dòng → 422 'Order đã đóng.'; dòng 1→1, giao dịch kho 2→2, trạng thái 'Chờ xác nhận thanh toán'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-54</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Chờ xác minh thanh toán; kho đủ.</td>
<td>1. Thử thêm món và gửi phần gọi thêm.</td>
<td>Từ chối gọi thêm; không tạo dòng món, không giữ hoặc trừ thêm nguyên liệu; giữ nguyên trạng thái order.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order mang về ở 'Chờ xác minh thanh toán' (yêu cầu xác minh → 200): giữ món gọi thêm → 422 'Order không còn mở.'; thêm dòng → 422 'Order đã đóng.'; dòng 1→1, giao dịch kho 3→3, trạng thái 'Chờ xác minh thanh toán'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-55</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Đã thanh toán; kho đủ.</td>
<td>1. Thử gọi thêm vào order đã thanh toán. 2. Tạo order mang về mới cho món khách mua thêm.</td>
<td>Order cũ từ chối gọi thêm, hóa đơn giữ nguyên; món mua thêm tạo order mới với mã riêng và trừ kho đúng một lần khi gửi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order mang về đã thanh toán qua webhook (200, 1 hóa đơn): giữ món gọi thêm → 422 'Order không còn mở.'; order vẫn 1 dòng, 1 hóa đơn. Order mang về mới cho món mua thêm → 201, mã ['ORD-131126-038', 'ORD-131126-039'], trừ kho +1 giao dịch</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-56</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Đã hủy; kho đủ.</td>
<td>1. Thử thêm món và gửi phần gọi thêm.</td>
<td>Từ chối gọi thêm; không tạo dòng món, không giữ hoặc trừ thêm nguyên liệu; giữ nguyên trạng thái order.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order mang về ở 'Đã hủy': giữ món gọi thêm → 422 'Order không còn mở.'; thêm dòng → 422 'Order đã đóng.'; dòng 1→1, giao dịch kho 7→7, trạng thái 'Đã hủy'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-57</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Đóng – chưa thu được tiền; kho đủ.</td>
<td>1. Thử thêm món và gửi phần gọi thêm.</td>
<td>Từ chối gọi thêm; không tạo dòng món, không giữ hoặc trừ thêm nguyên liệu; giữ nguyên trạng thái order.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order mang về ở 'Đóng – chưa thu được tiền' (đóng chưa thu → 200): giữ món gọi thêm → 422 'Order không còn mở.'; thêm dòng → 422 'Order đã đóng.'; dòng 1→1, giao dịch kho 7→7, trạng thái 'Đóng – chưa thu được tiền'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-58</td>
<td>FR-SALE-06, FR-SALE-08</td>
<td>Order mang về Đang mở đã có món; nhân viên có phần gọi thêm chưa gửi.</td>
<td>1. Hủy lượt chọn gọi thêm.<br />
2. Chọn món khác và gửi phần gọi thêm.</td>
<td>Chỉ giải phóng lượt chọn bị hủy; món đã gửi giữ nguyên. Lượt chọn mới được giữ và gửi vào cùng order theo điều kiện gọi thêm; không tạo order mới.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order mang về đang mở có 1 dòng; lượt gọi thêm 2 suất bị hủy ({"released": 1}), order vẫn 1 dòng; chọn món khác và gửi phần gọi thêm → 201; order có ['Chờ làm', 'Chờ làm'], không tạo order mới</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-59</td>
<td>FR-SALE-06, FR-SALE-08, FR-SALE-31</td>
<td>Order tại chỗ Đang mở, còn gắn đúng bàn; kho đủ.</td>
<td>1. Chọn món gọi thêm để giữ nguyên liệu.<br />
2. Gửi phần gọi thêm.</td>
<td>Tạo lượt giữ khi chọn; khi gửi thành công, kết thúc giữ, tạo dòng và phiếu bếp phần mới, trừ FIFO đúng một lần; dòng cũ giữ nguyên giá/công thức.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order tại chỗ có dòng #45 giá 100.000; đổi giá 110.000; giữ 1 suất gọi thêm rồi gửi → 201; dòng mới #46 giá 110000, lượt giữ 'Đã gửi'; giao dịch kho 2→3; 2 phiếu bếp; dòng cũ giữ 100000</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-60</td>
<td>FR-SALE-06, FR-SALE-08, FR-SALE-31</td>
<td>Order mang về Đang mở; kho đủ.</td>
<td>1. Chọn món gọi thêm để giữ nguyên liệu.<br />
2. Gửi phần gọi thêm.</td>
<td>Giữ nguyên liệu rồi chuyển thành tiêu hao đúng một lần; bổ sung món và phiếu bếp vào cùng order; không gắn bàn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order mang về đang mở; giữ 1 suất gọi thêm rồi gửi → 201; order có 2 giao dịch tổng -300 g cho 2 dòng; 2 phiếu bếp; MaBan None</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-61</td>
<td>FR-SALE-06, FR-INV-10</td>
<td>Lượt gọi thêm đã giữ món; trước lúc gửi, lô bị mất khả năng đáp ứng toàn bộ lượt gửi.</td>
<td>1. Gửi phần gọi thêm.</td>
<td>Từ chối toàn bộ lượt gửi, chỉ rõ dòng cần kiểm tra lại; không thêm dòng hoặc phiếu bếp, không trừ kho một phần.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script+API): (1) Lượt gọi thêm giữ QA61 Gà xào × 1 và QA61 Sò hấp × 2; lô Sò được đặt quá hạn trước lúc gửi: gửi → 422 'Món QA61 Sò hấp (2 suất): lô đang giữ không còn đủ số lượng hoặc đã hết hạn, hãy kiểm tra lại dòng này.'; dòng/phiếu bếp/giao dịch (1, 1, 95)→(1, 1, 95). (2) Lượt giữ QA61 Mực xào × 2 bị hủy trước lúc gửi: 422 'Món QA61 Mực xào (2 suất): lượt giữ chỗ không còn hiệu lực, hãy kiểm tra lại dòng này.'; (1, 1, 96)→(1, 1, 96)</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-62</td>
<td>FR-SALE-06, FR-SALE-08</td>
<td>Order tại chỗ Đang mở đã có món; còn nhiều dòng gọi thêm đang giữ; bàn còn phục vụ đúng order.</td>
<td>1. Chọn Hủy lượt chọn gọi thêm.<br />
2. Kiểm tra món đã gửi, trạng thái order và bàn.</td>
<td>Giải phóng toàn bộ lượng giữ của phần gọi thêm chưa gửi; dòng đã gửi và tiêu hao gốc giữ nguyên; order tiếp tục Đang mở, bàn vẫn Đang phục vụ; không tạo phiếu bếp mới.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order tại chỗ #47 có 1 dòng; lượt gọi thêm 2 dòng đang giữ; Hủy lượt chọn → 200 {"released": 2}; còn giữ 0; dòng đã gửi {"SoLuong": 1, "TrangThai": "Chờ làm"} và tiêu hao gốc (1) giữ nguyên; order 'Đang mở'; bàn {"TrangThai": "Đang phục vụ", "MaOrderDangPhucVu": 47}; phiếu bếp 1→1</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-63</td>
<td>FR-SALE-08</td>
<td>Mọi món đã gửi bị hủy; chỉ còn một lượt giữ hiệu lực gắn order.</td>
<td>1. Đợi lượt giữ cuối hết hạn theo giờ server.<br />
2. Kiểm tra order.</td>
<td>Lượng giữ hết hiệu lực, khả dụng được giải phóng; order tiếp tục Đang mở; không hóa đơn, không hoàn kho lặp.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order mang về: dòng duy nhất đã hủy (giao dịch [('Hoàn kho', 1), ('Trừ tự động', 1)]); còn một lượt giữ gắn order đã quá hạn: khả dụng 1000 (không trừ lượt giữ đó); order 'Đang mở'; 0 hóa đơn; không hoàn kho lặp</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-64</td>
<td>FR-SALE-06, FR-SALE-11, FR-INV-04</td>
<td>Mọi món đã gửi bị hủy; order Đang mở; còn phần gọi thêm đang giữ và nguyên liệu vẫn đáp ứng.</td>
<td>1. Gửi phần gọi thêm còn hiệu lực.</td>
<td>Ghi món thay thế và phiếu bếp vào cùng order; chuyển lượng giữ thành tiêu hao đúng một lần; order tiếp tục Đang mở.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Cùng order (mọi món đã gửi bị hủy, đang mở), giữ và gửi phần gọi thêm → 201; dòng ['Đã hủy', 'Chờ làm']; 2 phiếu bếp; order 'Đang mở'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-65</td>
<td>FR-SALE-06, FR-SALE-08, FR-INV-10</td>
<td>Một lô còn 300 g, trong đó lượt khác đang giữ 200 g; món gọi thêm cần 150 g.</td>
<td>1. Thêm món cần 150 g vào lượt chọn gọi thêm.</td>
<td>Từ chối giữ do chỉ còn 100 g khả dụng; lượt giữ của người khác và tồn sổ sách không đổi; không thêm dòng món vào order.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Ốc lô 300 g, Thu ngân 2 giữ 200 g; Thu ngân 1 thêm món 150 g vào lượt gọi thêm → 422 'Món Ốc 65 xào đang hết nguyên liệu.' (khả dụng 100); lượt giữ Thu ngân 2 vẫn 2 suất 'Đang giữ'; tồn 300; order 1 dòng</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-66</td>
<td>FR-SALE-03, FR-SALE-06, FR-SALE-31</td>
<td>Một lượt gọi thêm qua giữ món đã gửi thành công và có mã yêu cầu duy nhất.</td>
<td>1. Gửi lại cùng yêu cầu với cùng mã và nội dung.</td>
<td>Trả kết quả đã ghi nhận; không tạo thêm dòng, phiếu bếp hoặc tiêu hao.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Gửi phần gọi thêm với request_line_id R → 201 dòng #57; gửi lại cùng R và nội dung → 201 dòng #57; dòng/phiếu bếp/giao dịch (2, 2, 14) → (2, 2, 14)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-67</td>
<td>FR-SALE-08</td>
<td>Lượt chọn có một dòng còn giữ và một dòng đã hết hạn; chưa gửi món.</td>
<td>1. Chọn Hủy lượt chọn.<br />
2. Gửi lại cùng yêu cầu hủy.</td>
<td>Bỏ toàn bộ lượt chọn; chỉ giải phóng phần giữ còn hiệu lực đúng một lần; dòng hết hạn không làm tăng khả dụng thêm; không tạo order, phiếu bếp hoặc giao dịch kho.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Lượt chọn Cua: dòng A còn hiệu lực, dòng B đã quá hạn (khả dụng 150). Hủy lượt chọn → {"released": 2}, khả dụng 300; gửi lại yêu cầu hủy → {"released": 0}, khả dụng 300; giao dịch kho 1→1</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-68</td>
<td>FR-SALE-25; NFR-04</td>
<td>Tài khoản Quản lý; có order tại chỗ và mang về ở các trạng thái khác nhau.</td>
<td>1. Đăng nhập Quản lý. 2. Mở mục Quản lý đơn hàng.</td>
<td>Có mục điều hướng riêng; danh sách hiển thị mã, loại đơn, bàn nếu có, ngày kinh doanh, người lập, trạng thái và tổng tiền.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API+UI): Quản lý GET /sales/orders → 200, tổng 54; mỗi dòng có ['MaOrderHienThi', 'LoaiDon', 'TenBan', 'BusinessDate', 'NguoiLap', 'TrangThai', 'TongTien']; ví dụ {"MaOrderHienThi": "ORD-131126-054", "LoaiDon": "Mang về", "TenBan": null, "BusinessDate": "2026-11-13", "NguoiLap": "Thu ngân QA", "TrangThai": "Chờ xác nhận thanh toán", "TongTien": 50000.0}. Giao diện: Quản lý có mục điều hướng riêng 'Quản lý đơn hàng'; bảng có cột Mã order, Loại đơn, Bàn, Ngày kinh doanh, Người lập, Trạng thái, Tổng tiền (ví dụ 'ORD-131126-017 · Mang về · — · 13/11/2026 · Thu ngân QA · Đang mở · 80.000 ₫').</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-69</td>
<td>FR-SALE-25</td>
<td>Có order khác mã, bàn, ngày kinh doanh và trạng thái.</td>
<td>1. Chọn kết hợp mã, bàn, khoảng ngày và trạng thái. 2. Xóa bộ lọc. 3. Lọc tiêu chí không có kết quả.</td>
<td>Chỉ trả order thỏa toàn bộ tiêu chí; xóa lọc khôi phục danh sách theo quyền; tập rỗng hiển thị thông báo, cho thay đổi bộ lọc.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API+UI): Lọc kết hợp mã ORD-131126-049 + bàn + ngày 13/11–13/11 + 'Đang mở' → 1 order; đổi bàn khác với cùng mã → 0; bỏ lọc → 49 order (CSDL 49); mã 'KHONGCO' → 0. Giao diện: gõ mã 'KHONGCO' → 'Không có order phù hợp'.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-70</td>
<td>FR-SALE-25</td>
<td>Quản lý truy cập danh sách; có order lịch sử đã có món, giao dịch và chứng từ.</td>
<td>1. Mở chi tiết order. 2. Đối chiếu món, tổng tiền, lịch sử thanh toán và chứng từ. 3. Quay lại danh sách.</td>
<td>Chi tiết đúng order đã chọn; xem dữ liệu không làm đổi trạng thái, tồn kho hoặc doanh thu; có đường quay lại danh sách.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Chi tiết order #52 → 200 ([{"MaChiTietOrder": 59, "MaMon": 37, "SoLuong": 1, "DonGia": 50000.0, "MaPhienBanGia": 46, "MaCongThuc": 43, "GhiChu": …); lịch sử thanh toán → 200 {"items": [{"MaGiaoDich": 6, "PhuongThuc": "Tiền mặt", "TrangThai": "Thành công", "SoTien": 50000.0, "ThoiDiemTaoQR": n…; hóa đơn → 200; trạng thái, tồn kho, doanh thu không đổi (True)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-71</td>
<td>FR-SALE-25; NFR-04</td>
<td>Có tài khoản Quản lý và Bếp.</td>
<td>1. Quản lý mở danh sách và chi tiết. 2. Bếp thử truy cập trực tiếp màn hình và API quản lý đơn.</td>
<td>Quản lý truy cập được; Bếp không có mục điều hướng và bị từ chối ở cả giao diện và API, không lộ dữ liệu order.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API+UI): Quản lý: danh sách 200, chi tiết #52 200; Bếp: GET /sales/orders → 403, /sales/orders/52 → 403, không trả dữ liệu order. Giao diện: điều hướng của Bếp chỉ có Danh mục, Kho, Trợ lý AI (không có Quản lý đơn hàng); mở thẳng /orders bị chuyển về /inventory.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-72</td>
<td>FR-SALE-13, FR-SALE-21</td>
<td>Order đang mở có món hợp lệ; chưa có giao dịch thành công.</td>
<td>Thu ngân xác nhận đã nhận đủ tiền mặt.</td>
<td>Giao dịch tiền mặt thành công; order Đã thanh toán; có một hóa đơn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order đang mở 50.000 đ; Thu ngân xác nhận nhận đủ tiền mặt → 200; giao dịch {"PhuongThuc": "Tiền mặt", "TrangThai": "Thành công", "SoTien": "50000.00"}; order 'Đã thanh toán'; 1 hóa đơn</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-73</td>
<td>FR-SALE-21</td>
<td>Order đang mở có món đã gửi; chưa thanh toán.</td>
<td>Yêu cầu phiếu tạm tính và kiểm tra bảng hóa đơn.</td>
<td>Có dữ liệu phiếu tạm tính; không tạo hóa đơn đã thanh toán.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order đang mở 2 suất: phiếu tạm tính → 200 {"TieuDe": "PHIẾU TẠM TÍNH - CHƯA THANH TOÁN", "MaOrderHienThi": "ORD-131126-052", "TenNhaHang": "Nhà hàng", "DiaChi": null, "ThoiDiemXuat": "2026-11-13T17:59:01.486193+07:00", "TongTien": 100000.0, …; HOA_DON 0 bản ghi; order 'Đang mở'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-74</td>
<td>FR-SALE-14</td>
<td>Cấu hình SePay thử nghiệm; order hợp lệ chưa thanh toán.</td>
<td>Tạo QR và đọc thông tin thanh toán trả về.</td>
<td>QR chứa thông tin VietQR, ngân hàng, tài khoản và số tiền của giao dịch.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Chế độ SePay thử nghiệm (MBBank, 0123456789, NHA HANG QA). Tạo QR cho order 100.000 → 201: {"MaGiaoDich": 8, "TrangThai": "Chờ xác nhận", "SoTien": 100000.0, "ThoiDiemTaoQR": "2026-11-13T17:59:01.917299+07:00", "qr_image_url": "https://qr.sepay.vn/img?acc=0123456789&amp;bank=MBBank&amp;amount=100000&amp;des=TT8", "payment_code": "TT8", "bank_code": "MBBank", "bank_account": "0123456789", "account_name": "NHA HANG QA"}; CSDL ThoiDiemTaoQR 2026-11-13 17:59:01.917000</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-75</td>
<td>FR-SALE-14</td>
<td>Order đã có QR còn hiệu lực.</td>
<td>Yêu cầu tạo QR thứ hai.</td>
<td>Từ chối tạo thêm QR khi giao dịch trước còn hiệu lực.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order đã có QR còn hiệu lực; yêu cầu tạo QR thứ hai → 422 'Order đã đóng.'; order có 1 giao dịch QR</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-76</td>
<td>FR-SALE-15</td>
<td>Order có QR còn hiệu lực; webhook SePay dùng khóa thử nghiệm hợp lệ.</td>
<td>Gửi thông báo tiền vào đúng mã và đủ số tiền.</td>
<td>Order Đã thanh toán; phát hành một hóa đơn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Webhook SePay Apikey hợp lệ, mã TT8, đủ 100.000 → 200; giao dịch 'Thành công', MaGiaoDichCong sepay:900076; order 'Đã thanh toán'; 1 hóa đơn</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-77</td>
<td>FR-SALE-15, NFR-04</td>
<td>Order có QR; webhook dùng API key sai.</td>
<td>Gửi thông báo tiền vào với API key sai.</td>
<td>Webhook bị từ chối; giao dịch không được xác nhận.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Webhook SePay với Apikey sai → 401 'API key không hợp lệ.'; giao dịch 'Chờ xác nhận', order 'Chờ xác nhận thanh toán'; nhật ký WEBHOOK_REJECTED 1 bản ghi</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-78</td>
<td>FR-SALE-15, NFR-07</td>
<td>Webhook thanh toán đúng đã được xử lý.</td>
<td>Gửi lại cùng mã giao dịch ngân hàng.</td>
<td>Không thu tiền hoặc phát hành hóa đơn lần hai.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Webhook đúng → 200; gửi lại cùng mã giao dịch ngân hàng 970002 → 200; 1 hóa đơn, 1 giao dịch Thành công, 0 ngoại lệ</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-79</td>
<td>FR-SALE-16, FR-SALE-19</td>
<td>Order có QR; webhook hợp lệ nhưng sai số tiền.</td>
<td>Gửi webhook tiền vào sai số tiền.</td>
<td>Chuyển sang xử lý xác minh/ngoại lệ; không coi khoản sai là thanh toán đủ.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Webhook đúng mã QR nhưng chỉ 30.000 (order 50.000) → 200; giao dịch 'Chờ xác nhận', order 'Chờ xác nhận thanh toán', 0 hóa đơn; ngoại lệ {"TrangThai": "Chờ xử lý", "SoTien": "30000.00", "LyDo": "Số tiền không khớp với order"}</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-80</td>
<td>FR-SALE-18</td>
<td>QR được tạo ở thời điểm server xác định.</td>
<td>Đọc thời hạn QR trả về.</td>
<td>Hạn QR là 10 phút kể từ thời điểm tạo.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): QR #12: ThoiDiemTaoQR 18:01:45.113000, ThoiDiemHetHan 18:11:45.113000 — 600 giây</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-81</td>
<td>FR-SALE-18, FR-SALE-15</td>
<td>QR đã hết hạn; API ngân hàng giả lập có giao dịch phù hợp.</td>
<td>Chọn Kiểm tra lại và đối chiếu kết quả.</td>
<td>Hệ thống vẫn đối chiếu giao dịch ngân hàng sau hạn QR và ghi nhận khoản phù hợp.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): QR #25 đã quá hạn (lùi hạn 1 phút, giao dịch 'Hết hạn'); API ngân hàng giả lập trả khoản TT25 đủ 50.000. Kiểm tra lại (payments.check_payment) → giao dịch 'Thành công', order 'Đã thanh toán', 1 hóa đơn</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-82</td>
<td>FR-SALE-19, FR-SALE-22</td>
<td>Order có QR chưa thành công; Thu ngân đăng nhập.</td>
<td>Yêu cầu xác minh; thử thêm món vào order.</td>
<td>Order Chờ xác minh thanh toán; yêu cầu thêm món bị từ chối.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order có QR chưa thành công; Thu ngân yêu cầu xác minh → 200; order 'Chờ xác minh thanh toán'; thêm món → 422 'Order đã đóng.'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-83</td>
<td>FR-SALE-19, FR-SALE-34</td>
<td>Giao dịch QR chưa xác nhận; có mã tham chiếu, bằng chứng và ghi chú.</td>
<td>Gửi yêu cầu xác minh kèm thông tin.</td>
<td>Giữ mã tham chiếu, bằng chứng và ghi chú để đối chiếu.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Yêu cầu xác minh kèm mã FT26314001, ảnh chứng từ, ghi chú → 200; giao dịch lưu {"MaGiaoDichNganHang": "FT26314001", "AnhChungTu": "https://example.com/chung-tu-83.jpg"}; nhật ký REQUEST_PAYMENT_VERIFICATION {"DuLieuSau": "{\"GhiChu\": \"Khách báo đã chuyển\", \"MaOrder\": 61, \"TrangThai\": \"Chờ xác minh thanh toán\", \"AnhChungTu\": \"https://example.com/chung-tu-83.jpg\", \"MaGiaoDichNganHang\": \"FT…</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-84</td>
<td>FR-SALE-20</td>
<td>Order Chờ xác minh; Quản lý đã xác nhận bên ngoài nhận đủ 50.000 đồng.</td>
<td>Quản lý ghi nhận kết quả đã nhận đủ tiền.</td>
<td>Giao dịch Thành công, order Đã thanh toán và có một hóa đơn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order chờ xác minh 50.000; Quản lý ghi nhận đã nhận đủ (received, 50.000, ghi chú) → 200; giao dịch 'Thành công', order 'Đã thanh toán', 1 hóa đơn</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-85</td>
<td>FR-SALE-23, NFR-04</td>
<td>Order Chờ xác minh; có tài khoản Thu ngân và Quản lý.</td>
<td>Thu ngân thử mở lại; Quản lý mở lại với lý do; tạo QR mới.</td>
<td>Thu ngân bị từ chối; Quản lý mở lại được; giao dịch cũ Đã hủy, order Đang mở và cho phép QR mới.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order chờ xác minh: Thu ngân mở lại → 403; Quản lý mở lại với lý do → 200, QR cũ #14 'Đã hủy'; tạo QR mới → 201 #15; order 'Chờ xác nhận thanh toán'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-86</td>
<td>FR-SALE-35</td>
<td>Order Chờ xác minh chưa có tiền thành công; Quản lý quyết định ngừng thu.</td>
<td>Quản lý đóng chưa thu được tiền.</td>
<td>Order ở trạng thái kết thúc Đóng – chưa thu được tiền; không phát hành hóa đơn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order chờ xác minh, chưa có tiền; Quản lý đóng chưa thu với lý do → 200; order 'Đóng – chưa thu được tiền', giao dịch 'Đóng – chưa thu được tiền', 0 hóa đơn</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-87</td>
<td>FR-SALE-17</td>
<td>Order đã đóng chưa thu; có khoản tiền đến muộn được ghi thành ngoại lệ.</td>
<td>Quản lý áp dụng khoản ngoại lệ hợp lệ; thử áp dụng lại.</td>
<td>Chỉ áp dụng một lần và phát hành một hóa đơn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order đã đóng chưa thu; khoản 50.000 đến muộn qua webhook → ngoại lệ {"MaNgoaiLe": 2, "TrangThai": "Chờ xử lý", "LyDo": "Order đã đóng, đã hủy hoặc đã thanh toán bằng giao dịch khác"}. Áp dụng khoản muộn → 200 {"MaGiaoDich": 16, "MaHoaDon": 8, "TrangThai": "Thành công"}, order 'Đã thanh toán'; áp dụng lần hai → 422 'Giao dịch không ở trạng thái đóng chưa thu.'; 1 hóa đơn</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-88</td>
<td>FR-SALE-16, FR-SALE-17</td>
<td>Order đã được thanh toán; phát sinh khoản thu trùng.</td>
<td>Thử áp dụng khoản trùng rồi ghi nhận hoàn tiền.</td>
<td>Khoản trùng không được áp dụng lại; đi qua xử lý hoàn tiền.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order đã thanh toán qua webhook; khoản thứ hai cùng mã QR → ngoại lệ {"MaNgoaiLe": 3, "LyDo": "Thu trùng cho giao dịch đã thanh toán", "SoTien": "50000.00"}; 1 hóa đơn. Thử áp dụng khoản trùng → 422 'Order đã có thanh toán/hóa đơn, chỉ có thể hoàn tiền.'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-89</td>
<td>FR-SALE-17</td>
<td>Có ngoại lệ cần hoàn tiền.</td>
<td>Gửi kết quả hoàn thiếu mã tham chiếu; gửi lại đủ mã và số tiền.</td>
<td>Thiếu mã bị từ chối; kết quả hợp lệ lưu mã tham chiếu và số tiền hoàn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Ngoại lệ #3: ghi hoàn thiếu mã tham chiếu → 422 'Cần nhập mã tham chiếu hoàn tiền của ngân hàng.'; thiếu ghi chú → 422 'Cần ghi chú hoàn tiền ngoài hệ thống.'; gửi đủ mã, số tiền, ghi chú → 200, lưu MaThamChieuHoan HT003 (lần hoàn gần nhất) và SoTienHoan 50000; nhật ký RESOLVE_PAYMENT_EXCEPTION có 2 lần hoàn kèm mã HT002, HT003</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-90</td>
<td>FR-SALE-17</td>
<td>Ngoại lệ có số tiền đã nhận xác định.</td>
<td>Thử ghi số tiền hoàn lớn hơn số nhận.</td>
<td>Từ chối số tiền hoàn vượt số tiền đã nhận.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Ngoại lệ #3 nhận 50.000; ghi hoàn 60.000 → 422 'Số tiền hoàn phải lớn hơn 0 và không vượt số còn lại.'; ngoại lệ 'Chờ xử lý', SoTienHoan None</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-91</td>
<td>FR-SALE-17</td>
<td>Ngoại lệ chưa xử lý hết.</td>
<td>Ghi nhận hoàn một phần số tiền.</td>
<td>Ngoại lệ tiếp tục mở cho số tiền còn lại.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Hoàn một phần 20.000 (HT002) → 200, ngoại lệ 'Chờ xử lý', SoTienHoan 20000; hoàn tiếp 30.000 (HT003) → 200, 'Đã hoàn tiền', SoTienHoan 50000</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-92</td>
<td>FR-SALE-16, FR-SALE-17</td>
<td>Order đã trả tiền mặt; QR cũ nhận tiền sau đó.</td>
<td>Gửi thông báo khoản QR đến muộn.</td>
<td>Order giữ Đã thanh toán; không phát hành thêm hóa đơn cho cùng order.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order đã trả tiền mặt (200, QR cũ #18 đã hủy); khoản QR cũ đến muộn qua webhook → 200; order 'Đã thanh toán', 1 hóa đơn; ngoại lệ {"TrangThai": "Chờ xử lý", "SoTien": "50000.00", "LyDo": "Order đã đóng, đã hủy hoặc đã thanh toán bằng giao dịch khác"}</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-93</td>
<td>FR-SALE-15</td>
<td>Chế độ simulator; order có QR; payload có chữ ký nhưng thiếu số tiền.</td>
<td>Gửi webhook thiếu amount.</td>
<td>HTTP 422; order vẫn Chờ xác nhận thanh toán.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Chế độ simulator; order có QR. Webhook có chữ ký hợp lệ nhưng thiếu amount → 422 'Thiếu số tiền.'; order 'Chờ xác nhận thanh toán', giao dịch 'Chờ xác nhận', 0 hóa đơn. Biến thể chữ ký không khớp → 401</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-94</td>
<td>FR-SALE-15</td>
<td>API ngân hàng giả lập trả 151 giao dịch theo thứ tự giảm dần, có phân trang.</td>
<td>Chạy tác vụ đồng bộ giao dịch.</td>
<td>Đọc đủ các trang, không mất giao dịch cũ nhất.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): API ngân hàng giả lập trả 151 giao dịch, mới nhất trước; giao dịch cũ nhất là khoản TT26 khớp QR đang chờ. Chạy sync_recent_transfers: xác nhận 1 khoản, order 'Đã thanh toán' với 1 hóa đơn; MocDongBoSepay tiến tới 890150</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-95</td>
<td>FR-SALE-15</td>
<td>API ngân hàng giả lập trả danh sách bị cắt, không bảo đảm đọc đủ.</td>
<td>Chạy đồng bộ với danh sách không đầy đủ.</td>
<td>Báo lỗi thay vì bỏ qua các khoản tiền cũ chưa đọc.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): Giả lập trả đúng 5.000 dòng: tác vụ báo lỗi 'Danh sách SePay đạt 5.000 giao dịch; chưa tiến mốc đồng bộ. Cần đối soát lịch sử ngân hàng trước khi tiếp tục.'; MocDongBoSepay giữ nguyên (890150→890150), không bỏ qua khoản cũ</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-96</td>
<td>FR-SALE-24, FR-SALE-27, FR-SALE-28, FR-SALE-30, FR-INV-04</td>
<td>Quản lý. Order tại chỗ Đang mở, chưa thanh toán, bàn B1 Đang phục vụ. Bò xào 3 suất: 2 suất Chờ làm, 1 suất Đã xác nhận xong; đã xuất 450 g từ lô L1.</td>
<td>1. Chọn Hủy toàn bộ order. 2. Nhập lý do. 3. Xác nhận. 4. Đối chiếu order, kho, hóa đơn, bàn, báo cáo.</td>
<td>Order Đã hủy trong cùng một giao dịch. Hoàn đúng 300 g vào L1; 150 g của suất đã xong giữ nguyên tiêu hao và ghi vào hao hụt do hủy order. Không phát sinh hóa đơn. Bàn chưa giải phóng vì khách chưa rời. Có audit log và mốc thời gian chi tiết. Order xuất hiện ở giá trị order bị hủy.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order tại chỗ: 2 suất Chờ làm (−300 g) và 1 suất Đã xác nhận xong (−150 g). Quản lý hủy toàn bộ với lý do → 200 'Đã hủy'; hoàn 300 g vào lô gốc (tổng lô 28200→28500); 150 g suất đã xong giữ tiêu hao (-150); 0 hóa đơn; bàn {"TrangThai": "Đang phục vụ", "MaOrderDangPhucVu": 66}</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-97</td>
<td>FR-SALE-28, FR-SALE-30, FR-INV-04</td>
<td>Quản lý. Order mang về Đang mở; toàn bộ món Chờ làm. Có thêm một lượt chọn gọi thêm chưa gửi đang giữ nguyên liệu.</td>
<td>1. Hủy toàn bộ order kèm lý do. 2. Kiểm tra kho và lượng giữ.</td>
<td>Hoàn toàn bộ nguyên liệu các món Chờ làm về đúng lô gốc. Lượt chọn chưa gửi kết thúc và giải phóng lượng giữ. Không có tiêu hao hay hao hụt phát sinh. Bàn không bị ảnh hưởng.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order mang về 2 suất Chờ làm (−300 g) và một lượt gọi thêm đang giữ; Quản lý hủy toàn bộ → 200 'Đã hủy'; hoàn +300 g về lô gốc; lượt giữ 'Đã giải phóng'; không có phiếu xuất hao hụt; không liên quan bàn</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-98</td>
<td>FR-SALE-29, FR-SALE-27</td>
<td>Thu ngân hoặc Quản lý. Order Đang mở, đã tạo mã QR, đang Chờ xác nhận thanh toán.</td>
<td>1. Thử hủy toàn bộ order. 2. Hủy mã QR. 3. Hủy toàn bộ order lại.</td>
<td>Bước 1 bị từ chối, order và kho không đổi. Sau khi hủy QR (hoặc QR hết hạn), bước 3 được chấp nhận.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order có QR đang 'Chờ xác nhận thanh toán': hủy toàn bộ → 422 'Order đã đóng.'; hủy QR rồi hủy toàn bộ lại → 200 'Đã hủy'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-99</td>
<td>FR-SALE-27</td>
<td>Quản lý. Chuẩn bị hai order: (a) Chờ xác minh thanh toán, (b) Đã thanh toán.</td>
<td>1. Thử hủy toàn bộ từng order.</td>
<td>Cả hai bị từ chối với thông báo lý do. Không đổi trạng thái, kho, hóa đơn hay doanh thu.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order (a) 'Chờ xác minh thanh toán' và (b) 'Đã thanh toán': hủy toàn bộ → 422 'Order đã đóng.', 422 'Order đã đóng.'; (b) 1 hóa đơn</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-100</td>
<td>FR-SALE-27, NFR-04</td>
<td>Tài khoản Thu ngân và tài khoản Quản lý; order Đang mở hợp lệ.</td>
<td>1. Thu ngân thử hủy toàn bộ (giao diện và gọi API trực tiếp). 2. Quản lý hủy nhưng để trống lý do. 3. Quản lý nhập lý do và hủy.</td>
<td>Thu ngân bị từ chối ở cả giao diện và API. Bước 2 bị từ chối vì thiếu lý do. Bước 3 thành công.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Thu ngân gọi API hủy toàn bộ → 403; Quản lý hủy với lý do rỗng → 422 'Cần lý do hủy order.', order 'Đang mở'; Quản lý nhập lý do → 200 'Đã hủy'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-101</td>
<td>FR-SALE-26</td>
<td>Order đã thanh toán, đã có hóa đơn chốt; tài khoản Thu ngân và Quản lý.</td>
<td>1. Mở hóa đơn đã chốt và chọn in lại hai lần. 2. Đối chiếu nội dung với hóa đơn gốc. 3. Thử chỉnh sửa nội dung khi in lại.</td>
<td>Nội dung in lại đúng nguyên nội dung hóa đơn gốc; không cho chỉnh sửa; không tạo thêm hóa đơn hoặc giao dịch, không đổi doanh thu.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Order đã thanh toán, hóa đơn HD-20261113-0012 100000. In lại hai lần (Thu ngân, rồi Quản lý gửi kèm TongTien=1) → 200, 200; vẫn 1 hóa đơn, TongTien 100000, NoiDungChup không đổi (True), SoLanIn 1→3; 1 giao dịch</td>
<td>Đạt</td>
</tr>
</tbody>
</table>

Bảng 47. Ca kiểm thử module Quản lý bán hàng

Các ca Kho kiểm tra tồn sổ sách, lượng lô, lượng giữ và lịch sử nhập, xuất hoặc hoàn. Với nhiều người cùng thao tác, ghi rõ dữ liệu ban đầu và kết quả sau thao tác.

<table>
<colgroup>
<col style="width: 9%" />
<col style="width: 7%" />
<col style="width: 14%" />
<col style="width: 14%" />
<col style="width: 17%" />
<col style="width: 7%" />
<col style="width: 17%" />
<col style="width: 9%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Mã ca</strong></th>
<th><strong>FR/NFR</strong></th>
<th><strong>Điều kiện và dữ liệu</strong></th>
<th><strong>Bước thực hiện</strong></th>
<th><strong>Kết quả mong đợi</strong></th>
<th><strong>Ưu tiên</strong></th>
<th><strong>Kết quả thực tế</strong></th>
<th><strong>Trạng thái</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>TC-INV-01</td>
<td>FR-INV-01, FR-INV-13</td>
<td>Bếp; nhà cung cấp A; Thịt bò đơn vị g.</td>
<td>1. Nhập 1.000 g, giá 200 đ/g, ngày nhập và hạn dùng hợp lệ.<br />
2. Xác nhận.</td>
<td>Tạo lô từ dòng nhập; tồn tăng 1.000 g; ghi giao dịch đúng lô.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Bếp nhập Tôm 1.000 g × 200 đ/g từ NCC A (phiếu #51): lô #52 từ dòng nhập #52, NgayNhap 13/11, HanSuDung 20/11 (7 ngày), còn 1000, 'Còn hạn'; tồn 1000 g; sổ kho 'Nhập' +1000 g lô #52, GiaTri 200000; đơn giá bình quân 200</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-02</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô chưa có xuất hoặc giữ hiệu lực.</td>
<td>1. Bếp sửa phiếu thành 1.200 g.</td>
<td>Cho phép; tồn và lô cập nhật đúng 1.200 g; có audit log.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiếu #51 Tôm 1.000 g, lô chưa xuất, không giữ; Bếp sửa thành 1.200 g → 200; lô SoLuongNhap 1200, còn 1200; tồn 1200; nhật ký UPDATE_RECEIPT trước={"ChiTiet": [{"DonGia": 200.0, "SoLuong": 1000.0, "MaChiTietNhap": 52}], "NgayN…</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-03</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô đã có xuất.</td>
<td>1. Bếp sửa phiếu thành 1.200 g.</td>
<td>Từ chối; phiếu, lô và tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiếu #52 Vịt 1.000 g, lô đã xuất hủy 100 g; sửa thành 1.200 g → 422 'Phiếu nhập đã phát sinh xuất kho, phải điều chỉnh qua kiểm kê định kỳ.'; phiếu 'Hiệu lực', lô 1000/900, tồn 900 giữ nguyên</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-04</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô đang có giữ hiệu lực.</td>
<td>1. Bếp sửa phiếu thành 1.200 g.</td>
<td>Từ chối; phiếu, lô và tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiếu #53 Bê 1.000 g, lô đang có lượt giữ #118 còn hiệu lực; sửa thành 1.200 g → 422 'Lô của phiếu đang được giữ chỗ, không thể sửa/hủy phiếu.'; phiếu 'Hiệu lực', lô 1000/1000, tồn 1000 giữ nguyên</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-05</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô chưa có xuất hoặc giữ hiệu lực.</td>
<td>1. Bếp hủy phiếu.</td>
<td>Cho phép; tồn và lô cập nhật đúng lượng bị hủy; có audit log.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Ốc: phiếu 10.000 g × 200 đ, phiếu #55 10.000 g × 260 đ → đơn giá bình quân 230, tồn 20.000. Hủy phiếu #55 → 200; phiếu 'Đã hủy', lô về 0 'Đã hủy', tồn 10000; sổ kho 'Hủy nhập' -10000 g (GiaTri -2.6e+06); đơn giá bình quân về 200; nhật ký CANCEL_RECEIPT có dữ liệu trước</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-06</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô đã có xuất.</td>
<td>1. Bếp hủy phiếu.</td>
<td>Từ chối; phiếu, lô và tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiếu #56 Vịt 1.000 g, lô đã xuất hủy 100 g; hủy phiếu → 422 'Phiếu nhập đã phát sinh xuất kho, phải điều chỉnh qua kiểm kê định kỳ.'; phiếu 'Hiệu lực', lô 1000/900, tồn 900 giữ nguyên</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-07</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô đang có giữ hiệu lực.</td>
<td>1. Bếp hủy phiếu.</td>
<td>Từ chối; phiếu, lô và tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiếu #57 Bê 1.000 g, lô đang có lượt giữ #119 còn hiệu lực; hủy phiếu → 422 'Lô của phiếu đang được giữ chỗ, không thể sửa/hủy phiếu.'; phiếu 'Hiệu lực', lô 1000/1000, tồn 1000 giữ nguyên</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-08</td>
<td>FR-INV-10</td>
<td>Lô A còn hạn 600 g; B hết hạn 400 g; giữ hiệu lực 200 g trên A, giữ hết hạn 100 g.</td>
<td>1. Tra cứu trước khi tác vụ dọn giữ chạy.</td>
<td>Sổ sách 1.000 g; đủ điều kiện bán 600 g; khả dụng 400 g; không tính giữ hết hạn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Cá: lô #60 còn hạn 600 g, lô #59 hết hạn 400 g; lượt giữ #120 còn hiệu lực 200 g, lượt giữ #121 100 g đã quá hạn (lùi hạn bằng SQL) chưa được dọn. GET /inventory/stock: sổ sách 1000, đủ điều kiện 600, giữ 200, khả dụng 400</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-09</td>
<td>FR-INV-10, FR-INV-13</td>
<td>Lô còn hạn 150 g; một dòng giữ đủ 150 g còn hiệu lực; khả dụng chung 0.</td>
<td>1. Gửi chính dòng đang giữ.</td>
<td>Gửi được; tiêu hao 150 g đúng lô; kết thúc giữ, không tự từ chối do khả dụng chung bằng 0.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Lô #61 còn hạn 150 g; lượt giữ #122 giữ đủ 150 g, khả dụng chung 0. Gửi chính lượt chọn với hold_id → 201 order #80; 'Trừ tự động' -150 g lô #61; lượt giữ 'Đã gửi'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-10</td>
<td>FR-INV-03, FR-INV-13</td>
<td>Lô hết hạn nhập sớm còn 300 g; lô còn hạn 700 g.</td>
<td>1. Gửi 1 suất cần 150 g.</td>
<td>Trừ 150 g từ lô còn hạn; lô hết hạn giữ nguyên trong tồn sổ sách.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Cá: lô #59 nhập sớm đã hết hạn còn 400 g, lô #60 còn hạn 600 g (dùng 400/600 thay 300/700). Gửi 1 Cá chiên cần 100 g → 201; trừ -100 g từ lô #60; lô hết hạn giữ 400 g 'Hết hạn', vẫn trong tồn sổ sách (900 g)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-11</td>
<td>FR-INV-14, FR-SET-04</td>
<td>Ngưỡng 3 ngày; lô còn hàng; hạn dùng cách ngày tham chiếu 2 ngày.</td>
<td>1. Mở màn hình kho.</td>
<td>Trạng thái Sắp hết hạn; cảnh báo hạn dùng tách khỏi cảnh báo tồn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Ngưỡng cảnh báo 3 ngày, Business Date tham chiếu 13/11; lô #62 còn 100 g, hạn dùng 15/11 (cách 2 ngày): /inventory/lots 'Sắp hết hạn'; /inventory/stock CanhBaoHanSuDung=True, SoLoHetHan=0, tách riêng khỏi CanhBaoTonThap=False</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-12</td>
<td>FR-INV-14, FR-SET-04</td>
<td>Ngưỡng 3 ngày; lô còn hàng; hạn dùng cách ngày tham chiếu 3 ngày.</td>
<td>1. Mở màn hình kho.</td>
<td>Trạng thái Sắp hết hạn; cảnh báo hạn dùng tách khỏi cảnh báo tồn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Ngưỡng cảnh báo 3 ngày, Business Date tham chiếu 13/11; lô #63 còn 100 g, hạn dùng 16/11 (cách 3 ngày): /inventory/lots 'Sắp hết hạn'; /inventory/stock CanhBaoHanSuDung=True, SoLoHetHan=0, tách riêng khỏi CanhBaoTonThap=False</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-13</td>
<td>FR-INV-14, FR-SET-04</td>
<td>Ngưỡng 3 ngày; lô còn hàng; hạn dùng cách ngày tham chiếu 4 ngày.</td>
<td>1. Mở màn hình kho.</td>
<td>Trạng thái Còn hạn; cảnh báo hạn dùng tách khỏi cảnh báo tồn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Ngưỡng cảnh báo 3 ngày, Business Date tham chiếu 13/11; lô #64 còn 100 g, hạn dùng 17/11 (cách 4 ngày): /inventory/lots 'Còn hạn'; /inventory/stock CanhBaoHanSuDung=False, SoLoHetHan=0, tách riêng khỏi CanhBaoTonThap=False</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-14</td>
<td>FR-INV-14, FR-SET-04</td>
<td>Ngưỡng 3 ngày; lô còn hàng; hạn dùng cách ngày tham chiếu -1 ngày.</td>
<td>1. Mở màn hình kho.</td>
<td>Trạng thái Hết hạn; cảnh báo hạn dùng tách khỏi cảnh báo tồn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Ngưỡng cảnh báo 3 ngày, Business Date tham chiếu 13/11; lô #65 còn 100 g, hạn dùng 12/11 (cách -1 ngày): /inventory/lots 'Hết hạn'; /inventory/stock CanhBaoHanSuDung=True, SoLoHetHan=1, tách riêng khỏi CanhBaoTonThap=False</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-15</td>
<td>FR-INV-07</td>
<td>Ngưỡng riêng 500 g; khả dụng 499 g.</td>
<td>1. Xem cảnh báo tồn.</td>
<td>Có cảnh báo tồn tối thiểu.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): T499: ngưỡng riêng 500, khả dụng 499 → MucTonToiThieuApDung 500, CanhBaoTonThap=True</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-16</td>
<td>FR-INV-07</td>
<td>Ngưỡng riêng 500 g; khả dụng 500 g.</td>
<td>1. Xem cảnh báo tồn.</td>
<td>Không cảnh báo tồn tối thiểu.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): T500: ngưỡng riêng 500, khả dụng 500 → MucTonToiThieuApDung 500, CanhBaoTonThap=False</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-17</td>
<td>FR-INV-07</td>
<td>Ngưỡng riêng 500 g; khả dụng 501 g.</td>
<td>1. Xem cảnh báo tồn.</td>
<td>Không cảnh báo tồn tối thiểu.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): T501: ngưỡng riêng 500, khả dụng 501 → MucTonToiThieuApDung 500, CanhBaoTonThap=False</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-18</td>
<td>FR-INV-07, FR-SET-05</td>
<td>Không có ngưỡng riêng; mặc định 300 g; khả dụng 299 g.</td>
<td>1. Xem cảnh báo tồn.</td>
<td>Áp dụng ngưỡng 300 g, hiển thị cảnh báo.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): T299: không đặt ngưỡng riêng, mặc định 300, khả dụng 299 → MucTonToiThieuApDung 300, CanhBaoTonThap=True</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-19</td>
<td>FR-INV-05, FR-INV-06</td>
<td>Lô bò còn 500 g, không giữ; 100 g hỏng.</td>
<td>1. Xuất hủy nguồn Nguyên liệu, chọn lô và 100 g, nhập lý do.<br />
2. Kiểm tra bản xem trước và xác nhận.</td>
<td>Bản xem trước hiển thị lô, 100 g, tồn còn lại 400 g và giá trị hủy theo đơn giá bình quân hiện hành; sau khi xác nhận, trừ đúng 100 g từ lô, ghi nguồn, người, thời gian, lý do, giá trị và audit log.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Lô #70 còn 500 g, không giữ. Xem trước xuất hủy 100 g lý do Hư hỏng → 200: {"MaNguyenLieu": 69, "TenNguyenLieu": "Thịt bò I19", "DonViTinh": "g", "MaLoNguyenLieu": 70, "HanSuDung": "2026-11-20", "SoLuongHuy": 100.0, "TonLoConLai": 400…, tổng 20000.0; chưa ghi gì (phiếu 2→2, lô 500). Xác nhận → 201 phiếu #3 {"LyDo": "Hư hỏng", "NguonXuat": "Nguyên liệu", "NguoiLap": 3, "NgayXuat": "2026-11-13 18:06:46.387000", "TrangThai": "Đã xác nhận"}; sổ kho 'Xuất thủ công' -100 g lô #70, GiaTri -20000</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-20</td>
<td>FR-INV-06</td>
<td>Lô được chọn còn 100 g.</td>
<td>1. Yêu cầu xuất hủy 101 g.</td>
<td>Từ chối; không có giao dịch xuất, tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Lô #71 còn 100 g; xem trước và ghi xuất hủy 101 g → 422, 422 'Không đủ tồn kho khả dụng.'; giao dịch 1→1; lô giữ 100 g</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-21</td>
<td>FR-INV-06</td>
<td>Lô được chọn còn 100 g, không bị giữ.</td>
<td>1. Xuất hủy đúng 100 g.<br />
2. Xác nhận bản xem trước.</td>
<td>Lô còn 0 g; ghi một giao dịch xuất 100 g.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Lô #71 còn 100 g, không giữ; xem trước 100 g: TonLoConLai 0, GiaTri 1000.0, lượt giữ bị ảnh hưởng []; xác nhận → 201: lô còn 0 'Đã dùng hết'; sổ kho 1 giao dịch 'Xuất thủ công' [-100.0] g</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-22</td>
<td>FR-INV-06, FR-INV-11</td>
<td>Phần hỏng thuộc lô đang giữ cho một dòng món.</td>
<td>1. Xuất hủy phần hỏng.<br />
2. Kiểm tra bản xem trước và xác nhận.</td>
<td>Bản xem trước nêu lượt giữ bị ảnh hưởng; sau khi xác nhận, trong transaction: giải phóng toàn bộ lượng giữ của dòng bị ảnh hưởng, xuất đúng lượng hỏng; thông báo nhân viên kiểm tra lại.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Cá lô #72 còn 500 g; lượt giữ #124 (Cá chiên 2 suất) giữ 200 g trên lô. Xem trước xuất hủy 450 g: TonLoConLai 50, GiaTri 45000.0, LuotGiuBiGiaiPhong [{"MaGiuCho": 124, "MaLuotChon": "3dcd1278-8601-4732-8e9c-b0c79a0c1d4a", "MaLoNguyenLieu": 72, "SoLuongGiu": 200.0}]. Xác nhận → 201: lượt giữ 'Đã giải phóng', xuất -450 g, lô còn 50 g</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-23</td>
<td>FR-INV-05, FR-INV-06</td>
<td>Dòng đã chế biến 2 suất, tiêu hao 300 g; chưa xuất hủy món.</td>
<td>1. Chọn nguồn Món đã chế biến.<br />
2. Chọn dòng order và 1 suất hủy.<br />
3. Kiểm tra bản xem trước và xác nhận.</td>
<td>Hệ thống tự xác định nguyên liệu và 150 g từ tiêu hao gốc, hiển thị chỉ đọc; ghi 1 suất và liên kết giao dịch gốc; tồn không giảm lần hai.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Order Heo xào 2 suất, tiêu hao 300 g, dòng #90 'Đã xác nhận xong'. Xem trước nguồn Món đã chế biến, 1 suất → 200 {"order_line_id": 90, "servings": 1, "written_servings": 0, "eligible_servings": 2, "lines": [{"ingredient_id": 72, "ingredient_name": "Heo I23", "unit": "g", "quantity": 150.0, "value": 15000.0, "or…. Xác nhận → 201 phiếu #7: dòng xuất Heo 150 g, giá trị 15000.00; tồn 2700→2700, giao dịch kho 2→2 (không trừ lần hai)</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-24</td>
<td>FR-INV-06</td>
<td>Dòng 2 suất đã ghi xuất hủy món 1 suất.</td>
<td>1. Yêu cầu xuất hủy thêm 2 suất.</td>
<td>Từ chối vì chỉ còn 1 suất chưa ghi nhận; không tạo thêm chứng từ hay giao dịch kho.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng #90 đã ghi xuất hủy 1 suất; yêu cầu thêm 2 suất: xem trước → 422, ghi → 422 'Số suất hủy vượt quá số suất đã tiêu hao chưa ghi nhận.'; phiếu xuất 6→6, giao dịch kho 178→178</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-25</td>
<td>FR-INV-11, NFR-07</td>
<td>Khả dụng 150 g, mỗi suất cần 150 g; hai lượt chọn của hai bàn.</td>
<td>1. Phát đồng thời hai yêu cầu giữ.<br />
2. Lặp 100 lượt theo quy trình F.2.</td>
<td>Mỗi lượt đúng một yêu cầu thành công; tổng giữ 150 g, khả dụng 0; không tồn âm.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): Tồn 150 g, món cần 150 g/suất. 100 vòng hai Thu ngân phát đồng thời yêu cầu giữ 1 suất qua API: 100/100 vòng đúng một 201 và một 422, tổng giữ không vượt 150 g, khả dụng không âm; 0 lỗi 5xx; lượt giữ thành công được giải phóng sau mỗi vòng</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-26</td>
<td>FR-INV-11, NFR-07</td>
<td>Hai món cùng cần 150 g bò; khả dụng chỉ 150 g.</td>
<td>1. Phát đồng thời yêu cầu giữ mỗi món.<br />
2. Lặp 100 lượt.</td>
<td>Chỉ một lượt giữ thành công; lượt kia báo thiếu; không cấp trùng hoặc khóa chết.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): Tồn 150 g, hai món cùng cần 150 g. 100 vòng phát đồng thời giữ mỗi món: 100/100 vòng đúng một 201 và một 422 (báo thiếu); 0 lỗi 5xx; không cấp trùng, không khóa chết</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-27</td>
<td>FR-INV-10, FR-INV-11, NFR-07</td>
<td>Giờ server bằng thời điểm hết hạn; khả dụng đủ 150 g.</td>
<td>1. Gửi món tại mốc hết hạn.<br />
2. Lặp 100 lượt.</td>
<td>Giữ cũ không còn hiệu lực; kiểm tra lại và ghi tiêu hao 150 g đúng một lần.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): Tồn 15.000 g, món 150 g. 100 vòng: tạo lượt giữ qua tầng service, rồi gửi với đồng hồ đặt đúng bằng ThoiDiemHetHan đã lưu (at_time), có xác nhận hết hạn: 100/100 lượt gửi thành công; 100 dòng món, 100 giao dịch 'Trừ tự động' tổng -15000 g (mỗi suất trừ đúng một lần)</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-28</td>
<td>FR-INV-10, FR-INV-11, NFR-07</td>
<td>Giờ server bằng thời điểm hết hạn; khả dụng chỉ 100 g.</td>
<td>1. Gửi món tại mốc hết hạn.<br />
2. Lặp 100 lượt.</td>
<td>Từ chối gửi; không tạo dòng order hoặc tiêu hao; danh sách chọn còn nguyên.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): Tồn 150 g, món A 150 g, món B 50 g. 100 vòng: tạo lượt giữ A 150 g; đặt đồng hồ đúng bằng ThoiDiemHetHan đã lưu của A, tạo lượt giữ B 50 g (A đã hết hiệu lực nên khả dụng còn 100 g), rồi gửi A có xác nhận hết hạn: 100/100 bị từ chối 'Món Gan I28 A đang hết nguyên liệu.'; 0 dòng order, 0 giao dịch tiêu hao; lượt giữ A vẫn 'Đang giữ' trong danh sách chọn (dọn sau mỗi vòng)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-29</td>
<td>FR-INV-11, NFR-07</td>
<td>Lượt gửi đã commit nhưng phản hồi timeout.</td>
<td>1. Gửi lại đồng thời cùng mã yêu cầu.<br />
2. Lặp 100 lượt.</td>
<td>Chỉ một kết quả nghiệp vụ; không trừ tồn lặp hoặc tạo thêm dòng món.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): Tồn 18.000 g, món 180 g/suất. 100 vòng, mỗi vòng phát đồng thời 3 lần POST /sales/orders mang về với cùng request_id: 100 ORDER, 100 dòng món, 100 giao dịch 'Trừ tự động' tổng -18000 g, tồn về 0; mỗi dòng trừ đúng một lần</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-30</td>
<td>FR-INV-12</td>
<td>Có dữ liệu lô, giữ và cảnh báo.</td>
<td>1. Mở màn hình kho.</td>
<td>Đủ tên, đơn vị, sổ sách, đủ điều kiện bán, đang giữ, khả dụng, ngưỡng, cảnh báo và thời điểm cập nhật.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API+UI): GET /inventory/stock, dòng Cá: {"TenNguyenLieu": "Cá I08", "DonViTinh": "g", "SoLuongTon": 900.0, "DonGiaBinhQuan": 100.0, "GiaTriTon": 90000.0, "SoLuongDuDieuKien": 500.0, "SoLuongGiu": 0.0, "SoLuongKhaDung": 500.0, "MucTonToiThieuApDung": 300.0, "HanSuDungGanNhat": "2026-11-11", "CanhBaoTonThap": false, "CanhBaoHanSuDung": true, "ThoiDiemTinh": "2026-11-13…. Giao diện: màn Tồn kho có cột Nguyên liệu, Đơn vị, Tồn sổ sách, Đơn giá bình quân, Giá trị tồn, Đủ điều kiện, Đang giữ, Khả dụng, Mức tối thiểu, Hạn dùng gần nhất, Trạng thái; dòng 'Dữ liệu lúc 18:24 13/11/2026'.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-31</td>
<td>FR-INV-12</td>
<td>Có Thịt bò và Hành.</td>
<td>1. Tìm Thịt bò.</td>
<td>Chỉ trả nguyên liệu phù hợp tên tìm.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Có Thịt bò KK và Hành lá KK; tìm 'Thịt bò' → ['Thịt bò KK']</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-32</td>
<td>FR-INV-12</td>
<td>Có nguyên liệu cảnh báo và không cảnh báo.</td>
<td>1. Lọc theo cảnh báo tồn.</td>
<td>Chỉ hiển thị nguyên liệu đang có cảnh báo tồn.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Lọc cảnh báo tồn (alerting=true) → ['Hành lá KK']; toàn bộ (khả dụng, ngưỡng): [('Thịt bò KK', 500.0, 100.0), ('Hành lá KK', 100.0, 500.0), ('T500 KK', 500.0, 100.0)]</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-33</td>
<td>FR-INV-08, NFR-07</td>
<td>Còn lượt chọn chưa gửi dù giữ đã hết hạn.</td>
<td>1. Thử mở phiên kiểm kê.</td>
<td>Từ chối và yêu cầu xử lý hết lượt chọn/giữ trước khi mở.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Lượt chọn chưa gửi, lượt giữ #1 đã quá hạn (lùi ThoiDiemHetHan): mở kiểm kê → 422 'Còn lượt giữ chỗ chưa gửi, hãy xử lý trước khi kiểm kê.'; PHIEU_KIEM_KE 0 bản ghi</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-34</td>
<td>FR-INV-08, NFR-07</td>
<td>Còn lượt giữ hiệu lực.</td>
<td>1. Thử mở phiên kiểm kê.</td>
<td>Từ chối và yêu cầu xử lý hết lượt chọn/giữ trước khi mở.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Lượt giữ #2 còn hiệu lực: mở kiểm kê → 422 'Còn lượt giữ chỗ chưa gửi, hãy xử lý trước khi kiểm kê.'; PHIEU_KIEM_KE 0 bản ghi</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-35</td>
<td>FR-INV-08, NFR-07</td>
<td>Đã kết thúc phục vụ; món đã chế biến/hủy; không còn lượt chọn hay giữ hiệu lực.</td>
<td>1. Bếp mở kiểm kê.</td>
<td>Tạo phiên trên server, chốt dữ liệu đối chiếu và khóa nghiệp vụ kho.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Mọi dòng order 'Đã xác nhận xong', không còn lượt chọn/giữ hiệu lực; Bếp mở kiểm kê → 201 phiếu #1 'Đang kiểm kê', người thực hiện #3, thời điểm server 2026-11-13 18:13:13.752000; các thao tác kho sau đó bị chặn (TC-INV-36–40)</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-36</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API giữ món bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiên kiểm kê #1 đang mở: giữ món (POST /sales/holds) bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tổng tồn (1050), số giao dịch kho (5) và số lượt giữ (3) không đổi</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-37</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API gửi món bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiên kiểm kê #1 đang mở: gửi món (POST /sales/orders) bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tổng tồn (1050), số giao dịch kho (5) và số lượt giữ (3) không đổi</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-38</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API nhập kho bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiên kiểm kê #1 đang mở: nhập kho (POST /inventory/receipts) bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tổng tồn (1050), số giao dịch kho (5) và số lượt giữ (3) không đổi</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-39</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API xuất kho bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiên kiểm kê #1 đang mở: xuất kho (POST /inventory/issues) bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tổng tồn (1050), số giao dịch kho (5) và số lượt giữ (3) không đổi</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-40</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API hoàn kho bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiên kiểm kê #1 đang mở: gọi API hủy dòng món (đường hoàn kho) cho dòng #1 bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tổng tồn (1050), số giao dịch kho (5) và số lượt giữ (3) không đổi</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-41</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở; đã nhập số lượng thực tế, chưa xác nhận.</td>
<td>1. Hủy phiên.2. Thực hiện nhập kho hợp lệ.</td>
<td>Phiên kết thúc, không điều chỉnh tồn do kiểm kê; nhập kho được thực hiện bình thường.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiên #1 đang mở, đã nhập số thực tế Thịt bò 400 g (chưa xác nhận); hủy phiên → 200, phiếu 'Đã hủy'; tồn giữ 450 g, 0 giao dịch 'Điều chỉnh kiểm kê'; nhập kho 10 g ngay sau đó → 201, tồn 460 g</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-42</td>
<td>FR-INV-08, FR-INV-09, FR-INV-05</td>
<td>Kiểm kê bò: sổ sách 500 g, thực tế 450 g; lô nhập trước còn 200 g.</td>
<td>1. Nhập 450 g và lý do, chọn Xem trước.2. Kiểm tra bản xem trước và xác nhận.</td>
<td>Bản xem trước hiển thị tồn trước 500 g, tồn sau 450 g, chênh lệch −50 g; sau khi xác nhận, điều chỉnh giảm 50 g từ lô nhập trước; sinh một phiếu xuất hủy nguồn Kiểm kê; phiếu không trừ kho thêm; có audit log.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Thịt bò sổ sách 450 g (lô nhập trước #1 ngày 12/11 còn 140 g), thực tế 400 g. Xem trước: tồn trước 450, tồn sau 400, chênh lệch -50; xác nhận → 200: 'Điều chỉnh kiểm kê' -50 g lô #1; phiếu xuất [{"MaPhieuXuat": 2, "NguonXuat": "Kiểm kê", "TrangThai": "Đã xác nhận"}]</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-43</td>
<td>FR-INV-08, FR-INV-09</td>
<td>Kiểm kê hành: sổ sách 100 g, thực tế 120 g.</td>
<td>1. Nhập 120 g và lý do, chọn Xem trước.2. Xác nhận.</td>
<td>Điều chỉnh tăng 20 g theo BR-LOT-02, giá trị theo đơn giá bình quân hiện hành; không có phiếu xuất hủy cho phần tăng; có audit log.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Cùng phiên #2: Hành lá sổ sách 100 g, thực tế 120 g; sau xác nhận: 'Điều chỉnh kiểm kê' +20 g vào lô #3, GiaTri 800 theo đơn giá bình quân 40; 0 dòng phiếu xuất cho phần tăng; nhật ký kiểm kê 2 bản ghi</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-44</td>
<td>FR-INV-08, FR-INV-09</td>
<td>Sổ sách và thực tế đều 500 g.</td>
<td>1. Nhập 500 g, chọn Xem trước.2. Xác nhận.</td>
<td>Chênh lệch 0; tồn không đổi, không tạo chứng từ hao hụt; phiên kết thúc.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Cùng phiên #2: T500 KK nhập thực tế bằng sổ sách (500/500), xem trước chênh lệch 0; sau xác nhận chỉ có 2 giao dịch điều chỉnh (Thịt bò KK, Hành lá KK), không có giao dịch hay chứng từ hao hụt cho dòng bằng nhau (1 dòng); phiên 'Đã xác nhận'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-45</td>
<td>FR-INV-06, FR-INV-08, FR-INV-09</td>
<td>Phiếu chênh lệch âm đã xác nhận thành công.</td>
<td>1. Gửi lại yêu cầu xác nhận cùng phiếu.</td>
<td>Không điều chỉnh tồn lần hai, không tạo thêm phiếu xuất hủy nguồn Kiểm kê.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Gửi lại xác nhận phiếu #2 đã xác nhận → 422 'Phiếu kiểm kê đã được xác nhận trước đó.'; giao dịch kho 9→9; 1 phiếu xuất nguồn Kiểm kê</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-46</td>
<td>FR-INV-08, NFR-07</td>
<td>Đã kết thúc phục vụ, không giữ hiệu lực; chuẩn bị mở kiểm kê và một yêu cầu nhập.</td>
<td>1. Phát đồng thời mở kiểm kê và nhập kho.<br />
2. Đối chiếu thứ tự commit; lặp 100 lượt.</td>
<td>Nếu nhập commit trước chốt thì số chốt gồm lượng nhập; nếu khóa kiểm kê có trước thì nhập bị chặn. Tồn không đổi giữa chốt và xác nhận do giao dịch cạnh tranh.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): 100 vòng phát đồng thời qua API: mở kiểm kê (Bếp) và nhập 7 g Sữa (tồn 1.000 g); sau mỗi vòng hủy phiên. 100/100 lần mở phiên thành công; 100 lần nhập bị chặn 422 (phiên có trước), 0 lần nhập commit trước được tính vào số chốt; 0 vòng tồn lệch giữa lúc chốt và đọc lại</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-47</td>
<td>FR-INV-04, FR-INV-13</td>
<td>Món Chờ làm đã tiêu hao 150 g; lô gốc vừa hết hạn; Bếp xác nhận chưa làm.</td>
<td>1. Hủy món.</td>
<td>Hoàn 150 g đúng lô gốc; tăng tồn sổ sách nhưng không tăng tồn đủ điều kiện bán.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, Script): Lòng (bảo quản 1 ngày): lô #84 nhập 13/11 1.000 g, hạn 14/11. Order #869 gửi 13/11 → trừ 150 g lô #84, dòng #421 'Chờ làm'. Tại thời điểm mô phỏng 15/11 07:00 (lô đã quá hạn), Quản lý hủy món: 'Hoàn kho' +150 g vào lô #84; tồn sổ sách 850→1000, tồn đủ điều kiện bán 0→0</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-48</td>
<td>NFR-04</td>
<td>Đăng nhập Thu ngân; phiếu nhập có dữ liệu hợp lệ.</td>
<td>1. Gọi API xác nhận nhập kho.</td>
<td>Backend từ chối quyền; không tạo lô hoặc tăng tồn.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Thu ngân gọi POST /inventory/receipts với dữ liệu hợp lệ → 403; số lô 6→6</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-49</td>
<td>FR-INV-05, FR-INV-06</td>
<td>Dòng món 2 suất đã tiêu hao 300 g bò và 100 g hành; chưa ghi nhận xuất hủy món.</td>
<td>1. Chọn dòng món và hủy 1 suất.<br />
2. Kiểm tra bản xem trước và xác nhận.</td>
<td>Tự xác định 150 g bò và 50 g hành theo tiêu hao gốc, hiển thị chỉ đọc; lưu một suất hủy, không đếm thành hai suất; không trừ kho lần hai.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng #2 Bò xào hành 2 suất đã tiêu hao 300 g Bò thăn + 100 g Hành tây, 'Đã xác nhận xong'. Xem trước nguồn Món đã chế biến 1 suất: {"order_line_id": 2, "servings": 1, "written_servings": 0, "eligible_servings": 2, "lines": [{"ingredient_id": 5, "ingredient_name": "Bò thăn I49", "unit": "g", "quantity": 150.0, "value": 34500.0, "order_line_id": 2, "…. Xác nhận → 201 phiếu #3: dòng xuất [(50.0, 6), (150.0, 5)] (g, mã nguyên liệu), một suất hủy; giao dịch kho 14→14</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-50</td>
<td>FR-INV-05, FR-INV-06</td>
<td>Một suất món đã tiêu hao 150 g nguyên liệu.</td>
<td>1. Gửi yêu cầu hủy một suất, kèm định lượng 999 g.</td>
<td>Phiếu ghi nhận 150 g nguyên liệu theo tiêu hao gốc, liên kết đúng dòng món; tồn kho không thay đổi.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Cùng yêu cầu ở TC-INV-49 gửi kèm ingredient_id Bò thăn, quantity 999 g: phiếu #3 vẫn ghi [(50.0, 6), (150.0, 5)] theo tiêu hao gốc, liên kết đúng dòng #2 (1 dòng); 999 g bị bỏ qua; giao dịch kho 14→14</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-51</td>
<td>FR-INV-05, FR-INV-06</td>
<td>Dòng order đã gửi theo công thức 150 g/suất; công thức hiện hành đã đổi thành 200 g/suất.</td>
<td>1. Chọn dòng order cũ và hủy 1 suất đã chế biến.</td>
<td>Chứng từ dùng 150 g theo tiêu hao gốc, không dùng 200 g của công thức hiện hành; không trừ kho lần hai.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Dòng #3 Heo xào gửi theo công thức 150 g/suất; công thức hiện hành đổi thành 200 g (#4). Xem trước 1 suất: {"order_line_id": 3, "servings": 1, "written_servings": 0, "eligible_servings": 2, "lines": [{"ingredient_id": 7, "ingr…; xác nhận phiếu #4 ghi 150 g, không dùng 200 g; giao dịch kho 16→16</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-52</td>
<td>FR-INV-08, FR-INV-09</td>
<td>Phiên kiểm kê đang mở; bò sổ sách 500 g, thực tế 470 g.</td>
<td>1. Nhập 470 g và chọn Xem trước.2. Chưa xác nhận, kiểm tra tồn kho và sổ kho.</td>
<td>Bản xem trước hiển thị tồn trước 500 g, tồn sau 470 g, chênh lệch −30 g; tồn và sổ kho chưa thay đổi; phiếu vẫn Đang kiểm kê, kho vẫn khóa.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiên #103 đang mở; Thịt bò sổ sách 400 g, nhập thực tế 370 g, Xem trước: tồn trước 400, tồn sau 370, chênh lệch -30. Chưa xác nhận: CHI_TIET_KIEM_KE 0 dòng, giao dịch kho 16→16, phiếu 'Đang kiểm kê'; nhập kho thử → 422 (kho vẫn khóa)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-53</td>
<td>FR-INV-08</td>
<td>Phiên kiểm kê đang mở; hành sổ sách 100 g.</td>
<td>1. Nhập 80 g và chọn Xem trước.2. Chọn Quay lại sửa, nhập 100 g.3. Xem trước và xác nhận.</td>
<td>Lần xem trước đầu không ghi điều chỉnh; sau khi sửa, chênh lệch bằng 0, không tạo giao dịch điều chỉnh; phiếu Đã xác nhận.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Phiên #103: Hành lá sổ sách 120 g; xem trước với 80 g → chênh lệch -40, không ghi gì; quay lại sửa, xem trước với 120 g → chênh lệch 0; ghi số đếm bằng sổ sách và xác nhận → 200, phiếu 'Đã xác nhận', giao dịch kho 16→16, 0 phiếu xuất</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-54</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở; bản xem trước có chênh lệch âm, chưa xác nhận.</td>
<td>1. Hủy phiên.2. Kiểm tra tồn, sổ kho và trạng thái khóa.</td>
<td>Phiếu Đã hủy; không có giao dịch điều chỉnh hay phiếu xuất hủy nguồn Kiểm kê; kho được mở khóa.</td>
<td>Trọng yếu</td>
<td>13/11/2026 (bản 568ec9f, API): Phiên #104 mở, xem trước Thịt bò 400→350 (chênh lệch -50), chưa xác nhận; hủy phiên → 200, phiếu 'Đã hủy'; giao dịch kho 16→16, 0 phiếu xuất nguồn Kiểm kê; nhập kho ngay sau đó → 201 (kho đã mở khóa)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-55</td>
<td>FR-INV-05, FR-INV-06</td>
<td>Lô bò còn 500 g, không giữ.</td>
<td>1. Xuất hủy nguồn Nguyên liệu 100 g.<br />
2. Trên bản xem trước, chọn Quay lại sửa và đổi thành 80 g.<br />
3. Xác nhận.</td>
<td>Lần xem trước đầu không ghi phiếu hay giao dịch; sau khi xác nhận chỉ có một phiếu 80 g và một giao dịch xuất 80 g; lô còn 420 g.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Lô #11 còn 500 g, không giữ. Xem trước 100 g: 100 · tồn lô còn lại 400 · 20000.0; chưa có phiếu mới (4→4). Quay lại sửa thành 80 g, xem trước: 80 · 420 · 16000.0; xác nhận → 201: 1 phiếu, giao dịch xuất [-80.0], lô còn 420 g</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-56</td>
<td>FR-INV-12</td>
<td>Bò chưa xuất: lô 1 nhập 10 kg giá 200.000 đ/kg, sau đó lô 2 nhập 10 kg giá 260.000 đ/kg.</td>
<td>1. Mở màn hình tồn kho, tìm Bò.2. Chọn Bò để xem lịch sử đơn giá bình quân.</td>
<td>Đơn giá bình quân hiện hành 230.000 đ/kg; giá trị tồn 4.600.000 đ; lịch sử có hai dòng: 200.000 đ/kg sau phiếu nhập lô 1 và 230.000 đ/kg sau phiếu nhập lô 2, kèm thời điểm, chứng từ và tồn sau giao dịch.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API): Bò bình quân chưa xuất: 10.000 g × 200 đ rồi 10.000 g × 260 đ. Tồn kho: 20000 g, đơn giá bình quân 230, giá trị tồn 4.6e+06; lịch sử đơn giá [{"ThoiDiemHieuLuc": "2026-11-13T18:13:36.674000", "DonGiaBinhQuan": 230.0, "SoLuongTon": 20000.0, "MaGiaoDichKho": 21, "ChungTu": "Phiếu nhập #13"}, {"ThoiDiemHieuLuc": "2026-11-13T18:13:36.639000", "DonGiaBinhQuan": 200.0, "SoLuongTon": 10000.0, "MaGiaoDichKho": 20, "ChungTu": "Phiếu nhập #12"}]</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-57</td>
<td>FR-INV-12, FR-INV-09</td>
<td>Sả chưa có phiếu nhập; kiểm kê thừa 200 g đã được xác nhận.</td>
<td>1. Mở màn hình tồn kho, tìm Sả.</td>
<td>Tồn sổ sách 200 g; đơn giá bình quân và giá trị tồn hiển thị “Chưa xác định”, không hiển thị 0.</td>
<td>Thường</td>
<td>13/11/2026 (bản 568ec9f, API+UI): Sả chưa từng có phiếu nhập; phiên kiểm kê #105 ghi thực tế 200 g (thừa), xác nhận → 200. Tồn kho: sổ sách 200, DonGiaBinhQuan None, GiaTriTon None (chưa xác định, không phải 0). Giao diện: dòng Sả 57 hiện tồn sổ sách 200, Đơn giá bình quân và Giá trị tồn đều 'Chưa xác định'.</td>
<td>Đạt</td>
</tr>
</tbody>
</table>

Bảng 48. Ca kiểm thử module Quản lý kho

Lỗi tạo tài khoản ở UC 5.1 được ghi nhận thành ca TC-SET-01. Các ca TC-SET-02–09 kiểm tra FR-SET-02, 03, 04, 06 và 07 (phân quyền, thay đổi cấu hình, audit log). Bảng 49 chưa bao phủ FR-SET-05 ngoài các ca ngưỡng tồn kho thuộc module Kho.

| **Mã ca** | **FR/NFR**                   | **Điều kiện và dữ liệu**                                                          | **Bước thực hiện**                                                                                                           | **Kết quả mong đợi**                                                                                                                     | **Ưu tiên** | **Kết quả thực tế**                                                                                                                                                                                                                                                                                                                                                                                                                                                     | **Trạng thái** |
|-----------|------------------------------|-----------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| TC-SET-01 | FR-SET-01                    | Đăng nhập Quản lý; thông tin tài khoản mới hợp lệ, tên đăng nhập chưa tồn tại.    | 1\. Gửi yêu cầu tạo tài khoản mới.                                                                                           | Tạo thành công; phản hồi trả về thông tin tài khoản và bản ghi được lưu.                                                                 | Thường      | 13/11/2026 (bản 568ec9f, API): Quản lý tạo tài khoản Thu ngân mới qa_new_cashier → 201, trả {"MaNguoiDung": 5, "TenDangNhap": "qa_new_cashier", "HoTen": "Thu ngân mới", "SoDienThoai": null, "MaVaiTro": "CASHIER", "TrangThai": "Hoạt động", "NgayTao": "…; NGUOI_DUNG \#5 {"TenDangNhap": "qa_new_cashier", "MaVaiTro": "CASHIER", "TrangThai": "Hoạt động"}; nhật ký CREATE_USER người \#1                                                                          | Đạt            |
| TC-SET-02 | FR-SET-02                    | Tài khoản Thu ngân đang hoạt động; biết mật khẩu hiện tại.                        | 1\. Đăng nhập. 2. Tự đổi mật khẩu với mật khẩu hiện tại đúng. 3. Đăng xuất, đăng nhập lại bằng mật khẩu cũ rồi mật khẩu mới. | Đổi thành công; mật khẩu cũ bị từ chối, mật khẩu mới đăng nhập được; không phát sinh bản ghi audit log (ngoài phạm vi theo FR-SET-02).   | Thường      | 13/11/2026 (bản 568ec9f, API): seed_cashier2 tự đổi mật khẩu với mật khẩu hiện tại đúng → 204. Đăng nhập lại: mật khẩu cũ 401, mật khẩu mới 200; NHAT_KY_HE_THONG 346→346 bản ghi                                                                                                                                                                                                                                                                                       | Đạt            |
| TC-SET-03 | FR-SET-02                    | Tài khoản Thu ngân đang hoạt động.                                                | 1\. Gửi yêu cầu tự đổi mật khẩu với mật khẩu hiện tại sai.                                                                   | Bị từ chối kèm thông báo tiếng Việt; mật khẩu không đổi; đăng nhập bằng mật khẩu cũ vẫn thành công.                                      | Thường      | 13/11/2026 (bản 568ec9f, API): seed_cashier đổi mật khẩu với mật khẩu hiện tại sai → 422 'Mật khẩu hiện tại không đúng.'; đăng nhập bằng mật khẩu cũ 200, mật khẩu định đổi 401                                                                                                                                                                                                                                                                                         | Đạt            |
| TC-SET-04 | FR-SET-02; FR-SET-06         | Đăng nhập Quản lý; có người dùng quên mật khẩu.                                   | 1\. Quản lý đặt lại mật khẩu hộ người dùng. 2. Người dùng đăng nhập bằng mật khẩu mới. 3. Quản lý mở nhật ký.                | Đặt lại thành công; người dùng đăng nhập được; có bản ghi audit log gồm người thực hiện, thời điểm, loại thao tác.                       | Trọng yếu   | 13/11/2026 (bản 568ec9f, API): Quản lý đặt lại mật khẩu cho seed_cashier2 → 204; đăng nhập bằng mật khẩu mới 200, mật khẩu trước đó 401; nhật ký RESET_PASSWORD người \#1, 18:22:46 13/11, đối tượng NGUOI_DUNG \#4, PhienBanToken 1→2, không lưu mật khẩu (không lộ)                                                                                                                                                                                                   | Đạt            |
| TC-SET-05 | FR-SET-02; FR-SET-03; NFR-04 | Có tài khoản Thu ngân và Bếp; một người dùng khác làm đối tượng.                  | 1\. Thu ngân gọi trực tiếp API đặt lại mật khẩu của người dùng khác. 2. Bếp làm tương tự.                                    | Cả hai bị từ chối (HTTP 403); mật khẩu không đổi; không có bản ghi audit log mới.                                                        | Trọng yếu   | 13/11/2026 (bản 568ec9f, API): Thu ngân và Bếp gọi POST /settings/users/4/reset-password → 403, 403 'Bạn không có quyền thực hiện chức năng này.'; mật khẩu giữ nguyên (mật khẩu thử 401); nhật ký 347→347                                                                                                                                                                                                                                                              | Đạt            |
| TC-SET-06 | FR-SET-03; NFR-04            | Đăng nhập Thu ngân.                                                               | 1\. Kiểm tra mục điều hướng. 2. Truy cập trực tiếp màn hình và API Cài đặt, Báo cáo.                                         | Không có mục điều hướng Cài đặt và Báo cáo; truy cập trực tiếp bị chặn ở cả giao diện và API (HTTP 403), không lộ dữ liệu.               | Trọng yếu   | 13/11/2026 (bản 568ec9f, API+UI): Thu ngân gọi trực tiếp \['/settings/config', '/settings/users', '/settings/audit-log', '/reports/revenue?month=2026-11', '/reports/margin?month=2026-11'\] → \[403, 403, 403, 403, 403\], không trả dữ liệu. Giao diện: thanh điều hướng của Thu ngân chỉ có Danh mục, Bán hàng, Trợ lý AI; mở thẳng /settings và /reports đều bị chuyển về /sales.                                                                                   | Đạt            |
| TC-SET-07 | FR-SET-03; NFR-04            | Có tài khoản Bếp và Quản lý.                                                      | 1\. Bếp truy cập trực tiếp API Cài đặt và API thanh toán. 2. Quản lý dùng chức năng của Thu ngân và của Bếp.                 | Bếp bị từ chối (HTTP 403) với chức năng ngoài phạm vi; Quản lý truy cập được cả hai nhóm chức năng (kế thừa quyền).                      | Trọng yếu   | 13/11/2026 (bản 568ec9f, API): Bếp gọi /settings/config, /settings/users, POST pay/cash, pay/qr, payments/check, GET /sales/orders → \[403, 403, 403, 403, 403, 403\]; Quản lý gọi chức năng Thu ngân (/sales/orders, /sales/floor) và Bếp (/inventory/stock, /inventory/lots) → \[200, 200, 200, 200\]                                                                                                                                                                 | Đạt            |
| TC-SET-08 | FR-SET-04; FR-SET-06         | Đăng nhập Quản lý; thời hạn giữ món hiện là 5 phút.                               | 1\. Đổi thời hạn giữ món thành 10 phút. 2. Thử nhập 0 và giá trị âm. 3. Mở nhật ký.                                          | 10 phút được lưu và áp dụng cho lượt giữ món mới; 0 và giá trị âm bị từ chối; audit log ghi dữ liệu trước (5) và sau (10).               | Trọng yếu   | 13/11/2026 (bản 568ec9f, API): Cấu hình ThoiGianGiuChoPhut=5. PUT 0 và -1 → 422, 422, cấu hình giữ 5; PUT 10 → 200; nhật ký UPDATE_CONFIG ghi ThoiGianGiuChoPhut trước 5, sau 10. Lượt giữ mới tạo sau đó có ThoiDiemHetHan − NgayTao = 599.99 giây (đặt lại 5 phút sau khi kiểm)                                                                                                                                                                                       | Đạt            |
| TC-SET-09 | FR-SET-07; NFR-04            | Nhật ký có bản ghi từ nhiều loại thao tác; có tài khoản Quản lý, Thu ngân và Bếp. | 1\. Quản lý mở nhật ký. 2. Thu ngân và Bếp truy cập trực tiếp màn hình và API nhật ký.                                       | Quản lý xem toàn bộ; mỗi bản ghi có người thực hiện, thời điểm, loại thao tác, dữ liệu trước/sau; Thu ngân và Bếp bị từ chối (HTTP 403). | Trọng yếu   | 13/11/2026 (bản 568ec9f, API): Quản lý GET /settings/audit-log → 200, 365 bản ghi, mỗi bản ghi có MaNguoiDung, ThoiDiem, LoaiThaoTac, DoiTuong, MaDoiTuong, DuLieuTruoc, DuLieuSau, LyDo. Sau khi sửa món, nguyên liệu, nhà cung cấp, bàn và chuyển bàn: \['MOVE_ORDER_TABLE', 'UPDATE_DISH', 'UPDATE_INGREDIENT', 'UPDATE_SUPPLIER', 'UPDATE_TABLE'\] đều có dữ liệu trước và sau (ví dụ MOVE_ORDER_TABLE trước {'MaBan': 4}, sau {'MaBan': 5}); Thu ngân 403, Bếp 403 | Đạt            |

Bảng 49. Ca kiểm thử module Cài đặt hệ thống

## G. Hiệu năng cơ bản

### G.1. Môi trường và dữ liệu

Môi trường đo: máy Intel Core i7-11850H, RAM 16 GB, Windows 11 Pro, MySQL 8.4.13 chạy trong Docker, FastAPI (uvicorn) một tiến trình; công cụ tạo tải, API và CSDL chạy chung máy. Dữ liệu theo Phụ lục B.2 của báo cáo gồm khoảng 4.800 order trong 2 tháng, 30 món, 35 nguyên liệu và 12 bàn; trước mỗi lượt, CSDL được khôi phục từ cùng một bản sao và API được khởi động mới; cổng thanh toán và trợ lý AI dùng bộ giả lập.

### G.2. Kịch bản kiểm tra

Bốn nhóm đo gồm nghiệp vụ với 5, 10 và 20 người dùng đồng thời, cùng đọc báo cáo với 5 người dùng. Mỗi nhóm gồm 1 phút khởi động và 5 phút đo. Nghiệp vụ gồm giữ món, sửa lượng giữ, gửi món, đọc order, đọc thực đơn, xem danh mục và nhập kho; báo cáo gồm doanh thu ngày, doanh thu tháng và xếp hạng món.

### G.3. Chỉ tiêu

Ghi thời gian phản hồi p95 và số lỗi. p95 là thời gian mà 95% yêu cầu trong mẫu hoàn thành không vượt quá. Ngưỡng đối chiếu: nghiệp vụ không quá 1 giây, báo cáo dưới 10 giây; lỗi được thống kê riêng.

### G.4. Kết quả

Bảng dưới tổng hợp kết quả đo ngày 11/11/2026 trên bản 6985565 với bộ dữ liệu theo Phụ lục B.2. Bốn thao tác chính gồm giữ và sửa lượng giữ món, gửi món, cập nhật danh mục và nhập kho. p95 tính trên các yêu cầu trong pha đo; không bao gồm thời gian cổng ngân hàng hoặc máy in vật lý.

Bảng 50. Kết quả hiệu năng cơ bản

| **Chỉ tiêu**             | **Kết quả**                                                                                                                  | **Phạm vi kết luận**                                                |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| Nghiệp vụ, 5 người dùng  | Đạt. 738 yêu cầu, 0 lỗi; p95 lớn nhất 297 ms (đọc thực đơn), bốn thao tác chính không quá 170 ms; yêu cầu chậm nhất 390 ms   | Ngưỡng 1 giây                                                       |
| Nghiệp vụ, 10 người dùng | Đạt. 1.453 yêu cầu, 0 lỗi; p95 lớn nhất 319 ms (đọc thực đơn), bốn thao tác chính không quá 163 ms; yêu cầu chậm nhất 642 ms | Ngưỡng 1 giây                                                       |
| Nghiệp vụ, 20 người dùng | Đạt. 2.849 yêu cầu, 0 lỗi; p95 lớn nhất 417 ms (đọc thực đơn), bốn thao tác chính không quá 238 ms; yêu cầu chậm nhất 690 ms | Ngưỡng 1 giây                                                       |
| Báo cáo, 5 người dùng    | Đạt. 752 yêu cầu, 0 lỗi; p95 lớn nhất 25 ms (xếp hạng món); doanh thu ngày và tháng khớp bản đối chứng ở mọi yêu cầu         | Ngưỡng 10 giây                                                      |
| Bất biến sau chạy        | Đạt. Sau mỗi nhóm đo: không sai lệch sổ cái, tồn theo lô, giữ món hay gửi trùng; doanh thu lịch sử 707.334.000 đ không đổi   | Sổ cái, tồn, gửi trùng và doanh thu lịch sử phải khớp bản đối chứng |

## H. Kiểm thử báo cáo và điều kiện biên

Phần này gồm các ca của module Báo cáo và các điều kiện biên nghiệp vụ liên quan đến nhiều module.

### H.1. Module Báo cáo

Đối chiếu dữ liệu trả về và hiển thị theo kỳ, bộ lọc và trạng thái. Ca chưa được kiểm tra đủ giữ trạng thái tương ứng.

| **Ca**    | **FR** | **Dữ liệu và thao tác**                                                                       | **Kết quả mong đợi**                                                                                                                                                                       | **Kết quả**                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|-----------|--------|-----------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TC-REP-01 | 01     | Order thành công 100.000 tiền mặt, 200.000 QR; chờ 50.000; hủy 80.000.                        | Doanh thu 300.000; lọc tiền mặt 100.000, QR 200.000; loại chờ/hủy.                                                                                                                         | 13/11/2026 (bản 568ec9f, Script+API): Dữ liệu riêng Business Date 10/12/2026 (món 10.000 đ): order 10 suất tiền mặt 100.000, 20 suất QR 200.000 đã xác nhận, 5 suất QR chờ 50.000, 8 suất hủy 80.000. /reports/revenue ngày 10/12: total 300000, 2 đơn, provisional 0; theo phương thức: {'QR': 200000.0, 'Tiền mặt': 100000.0}                                                                                                                                     |
| TC-REP-02 | 02     | Tạo chờ xác minh → mở lại → nhận tiền thành công.                                             | Danh sách khoản chưa thu theo đúng trạng thái; trước thành công doanh thu 0; sau thành công ghi một lần.                                                                                   | 13/11/2026 (bản 568ec9f, Script+API): BD 11/12/2026: order 30.000, QR → Chờ xác minh: doanh thu ngày 0, tạm tính 30000; danh sách khoản chờ: {"TrangThai": "Chờ xác minh thanh toán", "SoTien": "30000.00", "KetQuaGanNhat": "Chờ xác minh thanh toán"}. Quản lý mở lại, tạo QR mới và xác nhận Thành công: doanh thu 11/12 = 30000, order không còn trong danh sách chờ                                                                                            |
| TC-REP-03 | 03     | Món A/B đồng số lượng, khác tiền; lọc đổi kỳ.                                                 | Thứ hạng khớp tổng lượng/tiền và quy tắc đồng hạng; không mất món do LIMIT.                                                                                                                | 13/11/2026 (bản 568ec9f, Script+UI): BD 21/12/2026: Món 10k 5 suất (50.000) và Món 20k 5 suất (100.000), ngày 22/12 thêm Món 10k 1 suất. Theo số lượng ngày 21/12: {'Món 10k REP03': 5, 'Món 20k REP03': 5} (đồng hạng); theo doanh thu: \['Món 20k REP03', 'Món 10k REP03'\]; đổi kỳ sang tuần: Món 10k (6, 60000.0); 2 món trong kỳ, không mất món. Giao diện: kỳ ngày 21/12/2026, khung 'Món bán chạy' hiện đúng hai món Món 10k REP03 (5) và Món 20k REP03 (5). |
| TC-REP-04 | 04     | Doanh thu 1.000.000; giá vốn bán 300.000; hao hụt 50.000; hủy/đóng 20.000.                    | Lợi nhuận gộp 630.000; không trừ lương/thuê và không gộp giá trị order chưa thu vào doanh thu.                                                                                             | 13/11/2026 (bản 568ec9f, Script+API): Tháng 01/2027: doanh thu 100 suất × 10.000 (giá vốn 300.000); xuất hủy 100 g × 500 = 50.000; order đóng chưa thu 50.000 có giá vốn 20.000. /reports/costs: NguyenLieu 300000, HaoHut 50000, DonHuyChuaThu 20000, Tổng 370000; /reports/margin: DoanhThu 1000000, BienLoiNhuanGop 630000 (không cộng order chưa thu vào doanh thu, không trừ lương/thuê)                                                                       |
| TC-REP-05 | 05     | Một chênh lệch âm kiểm kê có giao dịch kho và phiếu xuất hủy tự sinh.                         | Chi phí chỉ tính một lần; không cộng cả sổ cái và chứng từ cho cùng biến động.                                                                                                             | 13/11/2026 (bản 568ec9f, Script+API): Tháng 02/2027: kiểm kê thiếu 50 g (đơn giá 100) → 'Điều chỉnh kiểm kê' -50 g GiaTri -5000 và phiếu xuất tự sinh {"NguonXuat": "Kiểm kê", "SoLuong": "50.000000", "GiaVonUocTinh": "5000.00"}. /reports/costs 02/2027: HaoHut 5000 (chỉ tính một lần)                                                                                                                                                                          |
| TC-REP-06 | 06     | Thay giá/công thức sau bán; có hao hụt kho chung.                                             | Chi phí món dùng phiên bản của dòng bán; không phân bổ hao hụt chung tùy ý.                                                                                                                | 13/11/2026 (bản 568ec9f, Script+API): Tháng 03/2027: bán 10 suất Món REP06 (10 g/suất, 10.000 đ) rồi đổi công thức 30 g, giá 25.000; xuất hủy hao hụt chung 200 g. Giá vốn món: \[{"MaMon": 10, "TenMon": "Món REP06", "GiaVon": "10000.00"}\]; doanh thu 100000; HaoHut 20000, không phân bổ vào giá vốn món                                                                                                                                                       |
| TC-REP-07 | 07     | Order sát cutoff và qua nửa đêm; ngày/giờ biên.                                               | Bucket khung giờ theo quy tắc; kỳ Business Date khớp order, không lẫn ngày lịch.                                                                                                           | 13/11/2026 (bản 568ec9f, Script+API): Order tiền mặt 05:59:59 26/03/2027 (10.000), 06:00 (20.000), 23:59 (30.000), 00:30 27/03 (40.000), 05:59 27/03 (50.000), mỗi mốc 2 đơn. BD 25/03: 2 đơn; BD 26/03: 8 đơn, 280000; BD 27/03: 0 đơn. Khung giờ BD 26/03: {0: 80000.0, 5: 100000.0, 6: 40000.0, 23: 60000.0}. Theo thứ trong tuần tháng 03/2027 (Business Date): \[(3, 1, 100000.0), (4, 2, 20000.0), (5, 8, 280000.0)\]                                         |
| TC-REP-08 | 08     | Kỳ gốc 0, kỳ sau 100.000; thêm cặp 100.000 → 120.000.                                         | Cặp đầu không chia 0; cặp sau tăng 20%; chênh lệch tuyệt đối đúng.                                                                                                                         | 13/11/2026 (bản 568ec9f, Script+API): 04/2027 không có đơn, 05/2027 100.000, 06/2027 120.000. So sánh 04→05: 0 → 100000, change_percent None (không chia 0); 05→06: 100000 → 120000, change_percent 20.00, chênh lệch +20000                                                                                                                                                                                                                                        |
| TC-REP-09 | 09     | Cùng bộ lọc có dữ liệu, rỗng, đổi kỳ.                                                         | Bảng/biểu đồ cùng tổng và đơn vị; rỗng không vẽ số liệu giả.                                                                                                                               | 13/11/2026 (bản 568ec9f, Script+UI): Kỳ ngày 21/12/2026: tổng 150000, 2 đơn, các cột biểu đồ \[('2026-12-21', 150000.0)\] cùng tổng và đơn vị; kỳ rỗng 15/07/2027: 0, 0 đơn, cột có giá trị \[\] (không có số giả). Giao diện: kỳ ngày 21/12/2026 thẻ 150.000 ₫, 2 đơn, biểu đồ cột 21/12 và bảng chi tiết '21/12 · 2 · 150.000 ₫' cùng tổng; kỳ rỗng 15/07/2027: 0 ₫, 0 đơn, 'Chưa có dữ liệu trong kỳ'.                                                           |
| TC-REP-10 | 10     | Order hủy, đóng chưa thu; sau đó áp khoản muộn hợp lệ cho order đóng.                         | Hai nhóm tách; khi nhận tiền rời tổng đóng, giữ lịch sử, doanh thu ghi một lần.                                                                                                            | 13/11/2026 (bản 568ec9f, Script+API): BD 12/12/2026: order 40.000 hủy; order 60.000 QR → chờ xác minh → Quản lý đóng chưa thu. Báo cáo: Order hủy 1 đơn/40000; Đóng chưa thu 1 đơn/60000 ({"MaOrder": 10, "MaOrderHienThi": "ORD-121226-002", "TongTien": "60000.00", "GiaVon": "600.00", "LyDo": "Không nhận được tiền", "NguoiDong"…); doanh thu ngày 0. Áp khoản muộn: order 'Đã thanh toán', 1 hóa đơn; đóng chưa thu còn 0; doanh thu ngày 60000               |
| TC-REP-11 | 11     | Tồn 100 đơn vị giá 10.000 đ; nhập 100 × 20.000 đ, xuất 50; nhập tiếp 100 × 30.000 đ, xuất 50. | Đơn giá bình quân sau hai lần nhập là 15.000 đ và 21.000 đ; giá vốn hai lần xuất lần lượt 750.000 đ và 1.050.000 đ theo công thức lưu trên dòng; giá trị đã ghi không đổi khi có nhập sau. | 13/11/2026 (bản 568ec9f, Script): NL REP11: tồn 100 × 10.000 đ; nhập 100 × 20.000 → đơn giá 15000 (tồn 200); xuất 50 → GiaTri -750000, dòng xuất GiaVonUocTinh 750000; nhập 100 × 30.000 → (150 × 15.000 + 100 × 30.000)/250 = 21000; xuất 50 → -1050000. Giá trị lần xuất đầu vẫn -750000 sau lần nhập sau                                                                                                                                                         |
| TC-REP-12 | 12     | Xuất hủy nguyên liệu, thiếu kiểm kê, phiếu món đã chế biến.                                   | Hai nguồn đầu vào hao hụt; nguồn món giữ nhóm giá vốn order, không cộng lặp.                                                                                                               | 13/11/2026 (bản 568ec9f, Script+API): Tháng 04/2027: xuất hủy nguyên liệu 100 g (10.000), xuất hủy món đã chế biến 1 suất (10.000), kiểm kê thiếu 30 g (3.000); cùng tháng còn hai lần xuất của TC-REP-11 (750.000 + 1.050.000). /reports/costs: HaoHut 1813000 = 10.000 + 3.000 + 1.800.000 (nguồn Nguyên liệu và Kiểm kê); NguyenLieu 20000 (phần món đã chế biến giữ trong giá vốn order, không cộng lặp)                                                        |
| TC-REP-13 | 13     | Order hủy có món Chờ làm hoàn kho và món đã chế biến không hoàn.                              | Chỉ phần không hoàn vào chi phí hủy/đóng; nhận muộn chuyển giá vốn đúng một lần.                                                                                                           | 13/11/2026 (bản 568ec9f, Script+API): Tháng 05/2027: order Món REP13 3 suất Chờ làm (−300 g) + 1 suất đã xác nhận xong (−100 g); hủy toàn bộ: hoàn +300 g; báo cáo order hủy \[{"MaOrder": 30, "MaOrderHienThi": "ORD-200527-001", "TongTien": "200000.00", "GiaVon": "10000.00", "LyDoHuy": "Khách hủy"}\]; /reports/costs DonHuyChuaThu 10000 (chỉ phần không hoàn)                                                                                               |
| TC-REP-14 | 01–13  | Gọi trực tiếp API Báo cáo bằng Thu ngân và Bếp.                                               | 403 và không có dữ liệu, dù người dùng sửa URL hoặc tham số vai trò.                                                                                                                       | 13/11/2026 (bản 568ec9f, API): Thu ngân và Bếp gọi /reports/revenue, /reports/margin, kể cả thêm role=MANAGER trên URL: \[403, 403, 403, 403\], không trả dữ liệu                                                                                                                                                                                                                                                                                                   |
| TC-REP-15 | 01, 11 | Đổi ngày kinh doanh cấu hình sau khi đã phát sinh order.                                      | Không tính lại BusinessDate cũ; tổng doanh thu/giá vốn lịch sử không tự dịch kỳ.                                                                                                           | 13/11/2026 (bản 568ec9f, API): Doanh thu trước khi đổi: \[('2026-12-10', 300000.0, 2), ('2027-03-26', 280000.0, 8), ('2027-03-25', 20000.0, 2)\]. Quản lý đổi giờ bắt đầu Business Date sang 07:00 → 200 (lịch hiệu lực: 07:00:00, None); đọc lại: \[('2026-12-10', 300000.0, 2), ('2027-03-26', 280000.0, 8), ('2027-03-25', 20000.0, 2)\] — không đổi; đặt lại 06:00 → 200                                                                                        |

### H.2. Điều kiện biên nghiệp vụ

Các tình huống giữ món hết hạn, kiểm kê, lô bị hủy, giá vốn và làm tròn thuộc kiểm tra chức năng. Kiểm tra liên quan đạt chưa có nghĩa toàn bộ ca đạt.

| **Mã**   | **Yêu cầu liên quan**                 | **Dữ liệu / sự kiện**                                                                                                | **Kết quả mong đợi**                                                                                                                                                                         | **Kết quả thực tế**                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|----------|---------------------------------------|----------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TC-BR-01 | FR-SALE-05; FR-INV-10                 | Giờ server bằng hạn giữ; tồn đủ, giá/công thức không đổi; gửi toàn lượt chọn                                         | Không coi giữ cũ còn hiệu lực; kiểm tra lại đủ rồi gửi một lần; không tự gia hạn                                                                                                             | 13/11/2026 (bản 568ec9f, Script): Lượt giữ 2 suất; đặt giờ server đúng bằng ThoiDiemHetHan đã lưu; tồn đủ, giá/công thức không đổi. Gửi không xác nhận → 'Món Món BR01 (2 suất): Lượt giữ chỗ đã hết hạn. Xác nhận dùng giá và định lượng hiện tại để gửi món.' (giữ cũ không được coi là còn hiệu lực, hạn không tự gia hạn: True); gửi có xác nhận → order \#44, tiêu hao đúng một lần (giao dịch 1→2), lượt giữ 'Đã gửi'                                            |
| TC-BR-02 | FR-INV-08; TC-INV-33                  | Chỉ còn dòng hết hạn chưa gửi/hủy; yêu cầu mở kiểm kê                                                                | Từ chối; phần hết hạn không chiếm khả dụng nhưng lượt chọn chưa kết thúc                                                                                                                     | 13/11/2026 (bản 568ec9f, API): Không còn món Chờ làm; lượt chọn có 2 dòng đã hết hạn chưa gửi/hủy. Mở kiểm kê → 422 'Còn lượt giữ chỗ chưa gửi, hãy xử lý trước khi kiểm kê.'; khả dụng 30000 = tồn 30000 (phần hết hạn không chiếm khả dụng); 0 phiên kiểm kê đang mở                                                                                                                                                                                                 |
| TC-BR-03 | FR-INV-08                             | Hủy lượt chọn trong BR-02 rồi yêu cầu mở; không còn trở ngại khác                                                    | Giải phóng/đánh dấu xử lý một lần; mở phiên duy nhất, khóa kho                                                                                                                               | 13/11/2026 (bản 568ec9f, API): Hủy lượt chọn ở TC-BR-02 → {"released": 2}; hủy lại → {"released": 0} (xử lý một lần). Mở kiểm kê → 201 phiên \#108; mở lần nữa → 422 'Đang có phiên kiểm kê chưa chốt.'; giữ món lúc này → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'. Sau đó hủy phiên                                                                                                                                                                           |
| TC-BR-04 | FR-SALE-16                            | QR cũ hết hạn; tạo QR mới chưa nhận tiền; khoản cũ đúng tiền đến; chưa quyết định mở lại của Quản lý                 | Xác nhận khoản cũ, hủy QR mới trong một transaction; một hóa đơn, không đổi bàn                                                                                                              | 13/11/2026 (bản 568ec9f, API): Order mang về: QR cũ \#26 đã hết hạn; tạo QR mới \#27 chưa nhận tiền; webhook khoản cũ TT26 đủ 30.000 → 200; QR cũ 'Thành công', QR mới 'Đã hủy'; order 'Đã thanh toán', 1 hóa đơn, 0 ngoại lệ; không liên quan bàn                                                                                                                                                                                                                     |
| TC-BR-05 | FR-SALE-17, 23                        | Quản lý đã Mở lại thanh toán; khoản cũ đúng tiền đến khi chưa thu lại                                                | Ghi ngoại lệ, không tự thanh toán; chỉ Quản lý áp dụng hợp lệ                                                                                                                                | 13/11/2026 (bản 568ec9f, API): Order đã được Quản lý mở lại thanh toán (QR cũ \#28 đã hủy); khoản cũ 30.000 đến → ngoại lệ {"MaNgoaiLe": 1, "TrangThai": "Chờ xử lý", "LyDo": "Order đã mở lại thanh toán; quản lý cần áp dụng khoản cũ"}, không tự thanh toán (order 'Đang mở', 0 hóa đơn); Thu ngân gọi áp dụng → 403                                                                                                                                                |
| TC-BR-06 | FR-SALE-15–17                         | Cùng khoản nhận được webhook lặp trước/sau xác nhận thủ công                                                         | Một lần thu, một hóa đơn; không tạo thêm ngoại lệ cho cùng khoản                                                                                                                             | 13/11/2026 (bản 568ec9f, API): Order có QR; Thu ngân báo khách chuyển (mã FTBR0633), Quản lý xác nhận đã nhận → 200. Sau đó webhook SePay cùng khoản (referenceCode trùng, SePay gửi lặp cùng mã giao dịch 996001) gửi hai lần → 200, 200; 1 hóa đơn, 1 giao dịch Thành công (nối với sepay:996001), 0 ngoại lệ                                                                                                                                                        |
| TC-BR-07 | FR-SALE-09, 22; FR-CAT-18             | Order đã trả tiền nhưng món chưa phục vụ; khách còn ngồi                                                             | Cho cập nhật phục vụ; không đổi món/tiền; bàn chưa tự trống                                                                                                                                  | 13/11/2026 (bản 568ec9f, API): Order tại chỗ 2 suất, thu tiền mặt → 200 'Đã thanh toán'; dòng món vẫn cập nhật Chờ làm → Đã xác nhận xong → Đã phục vụ (200, 200); sửa số lượng → 422 'Order đã đóng.'; tổng tiền 60000; bàn {"TrangThai": "Đang phục vụ", "MaOrderDangPhucVu": 34} (không tự trống)                                                                                                                                                                   |
| TC-BR-08 | FR-SALE-06, 12; FR-CAT-18             | Giải phóng bàn order cũ; bàn nhận order mới; khoản cũ được xác nhận                                                  | Không gắn lại/giải phóng bàn của order mới; không gọi thêm hoặc đổi bàn cho order cũ                                                                                                         | 13/11/2026 (bản 568ec9f, API): Bàn: order A \#35 tạo QR chờ tiền, Thu ngân giải phóng bàn (200); order B \#36 mở trên cùng bàn. Khoản QR của A đến → A 'Đã thanh toán'; bàn vẫn {"TrangThai": "Đang phục vụ", "MaOrderDangPhucVu": 36}; gọi thêm cho A → 422 'Order không còn mở.'; đổi bàn A → 422 'Order đã đóng.'                                                                                                                                                   |
| TC-BR-09 | FR-INV-05–06; FR-REP-11–13            | Bỏ 1 suất có 2 dòng nguyên liệu; ghi phiếu Món đã chế biến                                                           | Ghi 1 suất bỏ; lượng khớp tiêu hao gốc, không trừ hoặc tính chi phí lần hai                                                                                                                  | 13/11/2026 (bản 568ec9f, API): Món BR09 (BR09a 150 g + BR09b 50 g/suất), dòng 2 suất đã tiêu hao, 'Đã xác nhận xong'. Xuất hủy nguồn Món đã chế biến 1 suất → 201 phiếu \#14: dòng xuất \[(23, 150.0, 15000.0), (24, 50.0, 2000.0)\] (mã, g, đ); giao dịch kho của hai nguyên liệu 4→4 (không trừ lần hai)                                                                                                                                                             |
| TC-BR-10 | FR-INV-09; FR-REP-12                  | Kiểm kê thiếu, tạo giao dịch điều chỉnh và phiếu xuất hủy tham chiếu                                                 | Tồn giảm theo chênh lệch đúng một lần; hao hụt không cộng cả hai nguồn                                                                                                                       | 13/11/2026 (bản 568ec9f, API): BR10 tồn 500 g (đơn giá 100); kiểm kê thực tế 450 → 200: 1 giao dịch 'Điều chỉnh kiểm kê' \[(-50.0, -5000.0)\] và phiếu xuất nguồn Kiểm kê {"SoLuong": "50.000000", "GiaVonUocTinh": "5000.00"}; tồn còn 450 (giảm đúng một lần); hao hụt chỉ tính một nguồn (xem TC-REP-05)                                                                                                                                                            |
| TC-BR-11 | FR-REP-11; tài liệu 04 G.1            | Thiếu giá tham chiếu; sau đó bổ sung dữ liệu hợp lệ cho phép tính                                                    | Trước khi có đơn giá: giá trị chưa xác định; khi có phiếu nhập hợp lệ đầu tiên, phần chưa xác định được định giá theo đơn giá bình quân đầu tiên; 0 chỉ hiển thị khi phép tính hợp lệ bằng 0 | 13/11/2026 (bản 568ec9f, API): Như TC-BR-25: trước khi có đơn giá, giao dịch \[('Điều chỉnh kiểm kê', None), ('Trừ tự động', None)\], tồn kho DonGiaBinhQuan None, giá vốn món 'Chưa đủ dữ liệu' (không hiển thị 0); khi có phiếu nhập hợp lệ đầu tiên: bình quân 6.0, phần chưa xác định được định giá \[('Điều chỉnh kiểm kê', 30.0), ('Trừ tự động', -6.0)\], giá vốn món 6.0                                                                                       |
| TC-BR-12 | FR-INV-03; tài liệu 04 G.1            | Xuất kho nhiều lần giữa hai phiếu nhập khác giá                                                                      | Mỗi lần xuất dùng đơn giá bình quân hiện hành tại thời điểm xuất; xuất không làm đổi đơn giá và không tạo bản ghi lịch sử giá                                                                | 13/11/2026 (bản 568ec9f, API): BR12: nhập 10 × 100 (bình quân 100); xuất 2, xuất 3 → \[-200.0, -300.0\]; nhập 10 × 200 → bình quân (5 × 100 + 10 × 200)/15 = 166.67; xuất 4 → \[-666.68\]. Lịch sử giá \[100.0, 166.67\] (chỉ hai lần nhập, các lần xuất không tạo bản ghi)                                                                                                                                                                                            |
| TC-BR-13 | FR-INV-02; FR-REP-11                  | Đã có phiếu xuất hủy định giá theo đơn giá hiện hành; sau đó thêm phiếu nhập hợp lệ khác giá                         | Đơn giá bình quân cập nhật theo phiếu mới; giá trị phiếu xuất hủy đã ghi giữ nguyên; chi phí của phần đã xuất không đổi                                                                      | 13/11/2026 (bản 568ec9f, API): BR13: nhập 10 × 100; xuất hủy 4 → GiaVonUocTinh 400; nhập tiếp 10 × 300 → bình quân (6 × 100 + 10 × 300)/16 = 225; giá trị phiếu xuất hủy vẫn 400, giao dịch xuất vẫn -400                                                                                                                                                                                                                                                              |
| TC-BR-14 | FR-INV-02; FR-REP-11                  | Phiếu nhập ghi nhầm ngày, lô chưa xuất/không giữ hiệu lực; sửa ngày nhập                                             | Cập nhật ngày lô, hạn dùng và thứ tự FIFO; đơn giá bình quân không đổi; giữ audit trước/sau                                                                                                  | 13/11/2026 (bản 568ec9f, API): BR14 (bảo quản 10 ngày): phiếu A 100 × 6 ngày 05/11, phiếu B 100 × 10 ngày 08/11 (bình quân 8). Sửa ngày phiếu A sang 09/11 → 200; lô A \#35 NgayNhap 09/11, hạn 19/11; thứ tự FIFO \[36, 35\] (lô B đứng trước); lịch sử đơn giá \[6.0, 8.0\] → \[6.0, 8.0\]; nhật ký UPDATE_RECEIPT trước/sau \["{\\"ChiTiet\\": \[{\\"DonGia\\": 6.0, \\"SoLuong\\": 100.0, \\"MaChiTietNhap\\": 34}\], \\"NgayNhap\\": \\"2026-11-05T08:00:00\\"}"… |
| TC-BR-15 | FR-INV-02; FR-REP-11                  | Hủy phiếu đủ điều kiện khi nguyên liệu đã có xuất từ lô khác                                                         | Không bị khóa; đơn giá bình quân hiện hành được tính lại sau khi đảo phiếu; giá trị đã xuất, hóa đơn và doanh thu giữ nguyên                                                                 | 13/11/2026 (bản 568ec9f, API): BR15: phiếu A 10 × 100, xuất hủy 4 từ lô A (-400); phiếu B 10 × 200 (bình quân 162.5). Hủy phiếu B (lô B chưa xuất, không giữ) → 200, không bị khóa; đơn giá bình quân tính lại 100 (tồn 6); giá trị đã xuất giữ -400                                                                                                                                                                                                                   |
| TC-BR-16 | FR-INV-02                             | Sửa phiếu khi lô đã có xuất hoặc còn giữ hiệu lực                                                                    | Từ chối toàn bộ, phiếu/lô/giá vốn không bị cập nhật dở                                                                                                                                       | 13/11/2026 (bản 568ec9f, API): Phiếu hai dòng BR16a 50 × 4 và BR16b 30 × 5; BR16a đã xuất 5. Sửa cả hai dòng thành 80 × 9 → 422 'Phiếu nhập đã phát sinh xuất kho, phải điều chỉnh qua kiểm kê định kỳ.'; dòng phiếu \[(50.0, 4.0), (30.0, 5.0)\], lô (còn/nhập) \[(45.0, 50.0), (30.0, 30.0)\], lịch sử đơn giá không đổi (True) — không cập nhật dở                                                                                                                  |
| TC-BR-17 | FR-INV-09; BR-LOT-02                  | Kiểm kê thừa, không còn lô còn hạn và không có giá tham chiếu                                                        | Vẫn tạo lô điều chỉnh và tăng lượng đúng; DonGia NULL, không yêu cầu nhập giá, không tạo phiếu nhập mua; phần giá trị chưa xác định                                                          | 13/11/2026 (bản 568ec9f, API): BR17 chưa có lô và chưa có giá; kiểm kê thực tế 50 g → lô điều chỉnh {"MaLoNguyenLieu": 53, "LoDieuChinhKiemKe": 1, "MaChiTietNhap": null, "HanSuDung": null, "SoLuongConLai": "50.000000", "DonGia": null}; giao dịch 'Điều chỉnh kiểm kê' +50 GiaTri None; không yêu cầu nhập giá, 0 dòng nhập mua, lịch sử đơn giá \[\]                                                                                                              |
| TC-BR-18 | FR-INV-09; FR-REP-11                  | Điều chỉnh thừa khi nguyên liệu đã có đơn giá bình quân                                                              | Giá trị phần thừa = lượng thừa × đơn giá bình quân hiện hành, do hệ thống tính; không cộng lượng thừa vào nhập mua; đơn giá bình quân không đổi                                              | 13/11/2026 (bản 568ec9f, API): BR18 tồn 100 g, bình quân 40; kiểm kê thực tế 120 → giao dịch +20 GiaTri 800 (20 × 40, hệ thống tính); dòng nhập mua vẫn 1; lịch sử đơn giá \[40.0\]                                                                                                                                                                                                                                                                                    |
| TC-BR-19 | FR-INV-02; tài liệu 04 F.21           | Phiếu có hai dòng tạo hai lô chưa xuất, không còn giữ hiệu lực; hủy phiếu                                            | Đảo đúng lượng nhập của cả hai lô, lượng còn lại bằng 0, trạng thái Đã hủy; phiếu/lô/lịch sử còn truy vết; đơn giá bình quân hiện hành được tính lại                                         | 13/11/2026 (bản 568ec9f, API): Phiếu hai dòng BR19a 20 × 7 và BR19b 30 × 8 (mỗi nguyên liệu đã có 10 × 5), hai lô chưa xuất, không giữ; hủy phiếu → 200, phiếu 'Đã hủy', lô \[(43, 0.0, 'Đã hủy'), (44, 0.0, 'Đã hủy')\] (vẫn truy vết được); đơn giá bình quân tính lại: BR19b 7.25 → 5; BR19a 6.33 → 4.99 (lệch 0,01 do đảo theo đơn giá đã làm tròn, đúng tài liệu 04 mục G.1)                                                                                      |
| TC-BR-20 | FR-INV-05; BR-LOT-01                  | Lô còn hạn có 10 đơn vị; xuất hủy 3 đơn vị nguyên liệu                                                               | Lô còn 7 đơn vị, không mang trạng thái Đã hủy; 7 đơn vị tiếp tục đủ điều kiện phân bổ nếu không bị giữ; hao hụt ghi đúng một lần                                                             | 13/11/2026 (bản 568ec9f, API): BR20 lô còn hạn 10; xuất hủy 3 → lô còn 7, 'Còn hạn'; khả dụng 7; giữ món cần 7 → 201; 1 giao dịch xuất                                                                                                                                                                                                                                                                                                                                 |
| TC-BR-21 | FR-INV-02, FR-INV-09; F.21            | Thử giữ món, xuất FIFO hoặc cộng chênh lệch kiểm kê vào lô Đã hủy                                                    | Không chọn lô Đã hủy; kiểm kê thừa dùng lô hợp lệ khác hoặc tạo lô điều chỉnh theo BR-LOT-02, không khôi phục lô đã hủy                                                                      | 13/11/2026 (bản 568ec9f, API): BR21: lô \#51 50 còn hạn và lô \#52 30 đã hủy (hủy phiếu). Kiểm kê thừa 10 → lô \#51 (60.0, 'Còn hạn'), lô \#52 (0.0, 'Đã hủy') (không khôi phục); gửi 2 suất (20 g) → FIFO trừ \[51\], không chọn lô Đã hủy                                                                                                                                                                                                                            |
| TC-BR-22 | FR-REP-11; tài liệu 04 G.1            | Hai lần nhập 1 × 4 và 2 × 3 cho đơn giá bình quân trước làm tròn 10/3; xuất 3 đơn vị chuẩn                           | Lưu đơn giá 3,33; giá vốn dòng xuất 9,99 theo ROUND_HALF_UP; lượng vẫn theo độ chính xác sáu chữ số                                                                                          | 13/11/2026 (bản 568ec9f, API): BR22: nhập 1 × 4 và 2 × 3 → bình quân 10/3 lưu 3.33; xuất 3 đơn vị (giao dịch theo lô \[-3.33, -6.66\]) → GiaVonUocTinh 9.99 (ROUND_HALF_UP); lượng 3.000000                                                                                                                                                                                                                                                                            |
| TC-BR-23 | FR-REP-11; tài liệu 04 G.1            | Đơn giá bình quân 1,01; xuất 0,5 đơn vị; giá trị trước làm tròn 0,505                                                | GiaVonUocTinh bằng 0,51 theo ROUND_HALF_UP; đơn giá lưu giữ 1,01; không tạo thêm biến động kho                                                                                               | 13/11/2026 (bản 568ec9f, API): BR23: bình quân 1.01; xuất 0,5 → GiaVonUocTinh 0.51 (0,505 làm tròn ROUND_HALF_UP); đơn giá lưu giữ 1.01; 1 giao dịch xuất                                                                                                                                                                                                                                                                                                              |
| TC-BR-24 | FR-INV-04; tài liệu 04 G.1            | Tồn 150 đơn vị, đơn giá bình quân 15.000 đ; dòng Chờ làm đã tiêu hao 20 đơn vị khi đơn giá là 12.000 đ; hủy dòng món | Hoàn 20 đơn vị về lô gốc theo đơn giá 12.000 đ; đơn giá bình quân mới = (150 × 15.000 + 20 × 12.000)/170 = 14.647,06 đ; một bản ghi lịch sử giá mới                                          | 13/11/2026 (bản 568ec9f, API): BR24: nhập 100 × 12.000; dòng Chờ làm tiêu hao 20 (−240.000); nhập 70 × 18.428,57 → tồn 150, bình quân 15000.0. Hủy dòng món → 200: 'Hoàn kho' +20, GiaTri 240000 (đơn giá 12.000 của giao dịch gốc); bình quân mới 14647.06 (= (150 × 15.000 + 20 × 12.000)/170), tồn 170; lịch sử đơn giá thêm 1 bản ghi                                                                                                                              |
| TC-BR-25 | FR-INV-09; FR-REP-11; tài liệu 04 G.1 | Nguyên liệu chưa có đơn giá: lô điều chỉnh 5 đơn vị, một dòng tiêu hao 1 đơn vị; sau đó nhập 5 × 6                   | Trước khi nhập: giá trị chưa xác định; sau khi nhập: đơn giá bình quân 6,00, dòng tiêu hao trước đó được định giá 6,00 một lần; không tạo biến động kho mới                                  | 13/11/2026 (bản 568ec9f, API): BR25 chưa có đơn giá: kiểm kê thừa tạo lô điều chỉnh \#54 5 đơn vị, một dòng tiêu hao 1: giao dịch \[('Điều chỉnh kiểm kê', None), ('Trừ tự động', None)\]; màn tồn: DonGiaBinhQuan None, GiaTriTon None. Nhập 5 × 6: bình quân 6.0; giao dịch sau khi nhập \[('Điều chỉnh kiểm kê', 30.0), ('Trừ tự động', -6.0), ('Nhập', 30.0)\]; số giao dịch 2→3 (chỉ thêm giao dịch nhập)                                                         |

## I. Nhận xét

Trên bản 568ec9f (ngày 13/11/2026): 258 đạt trên tổng 258 ca. Mười lỗi phát hiện ngoài test case ở lượt ngày 10/11/2026 đã được xử lý (8 lỗi đã sửa, 2 lỗi giữ theo thiết kế). Hiệu năng cơ bản đo ngày 11/11/2026 trên bộ dữ liệu 2 tháng đạt ngưỡng ở cả bốn nhóm, không có lỗi và dữ liệu giữ đúng bất biến (mục G).

## J. Lỗi chức năng đang ghi nhận

### J.1. Ca không đạt

Trên bản 568ec9f ngày 13/11/2026 không có ca không đạt. Hai ca dưới đây không đạt ở lượt ngày 10/11/2026 trên bản 6985565 và đạt sau khi sửa.

| **Mã ca**  | **Lỗi ghi nhận**                                                                                                                                                                                                                                       | **Trạng thái**   |
|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|
| TC-SALE-61 | Lượt gửi phần gọi thêm bị từ chối toàn bộ đúng (không trừ một phần, dòng order, phiếu bếp và giao dịch kho không đổi) nhưng thông báo 'Món đang hết nguyên liệu.' hoặc 'Lượt giữ chỗ không còn hiệu lực.' không chỉ rõ dòng hoặc món cần kiểm tra lại. | Đạt khi kiểm lại |
| TC-SET-09  | Nhật ký có đủ người thực hiện, thời điểm, loại thao tác và đối tượng, phân quyền đúng (Thu ngân và Bếp bị 403), nhưng UPDATE_DISH, UPDATE_INGREDIENT, UPDATE_SUPPLIER, UPDATE_TABLE và MOVE_ORDER_TABLE vẫn có DuLieuTruoc và DuLieuSau NULL.          | Đạt khi kiểm lại |

### J.2. Lỗi phát hiện ngoài test case

PH-01 đến PH-10 được phát hiện ngày 10/11/2026 trên bản 6985565. Cột Trạng thái ghi kết quả trên bản 568ec9f:

PH-01: bộ B.1 sinh lại có 48.155 giao dịch kho, TonSauGiaoDich khớp tồn cộng dồn của từng nguyên liệu và khớp tồn cuối; giao dịch mới nhập, trừ tự động, xuất thủ công ghi đúng 100.000 → 99.700 → 99.600 g. PH-02: PATCH nhà cung cấp trả danh sách phiếu nhập. PH-03: xóa mềm nhóm món ghi NgayXoa. PH-04: nhật ký CANCEL_RECEIPT có dữ liệu trước; trên bản 568ec9f, hủy phiếu nhập ghi giao dịch loại 'Hủy nhập' (−1.000 g, gắn MaChiTietNhap của dòng bị hủy); migration đổi giao dịch 'Hoàn kho' cũ gắn dòng nhập sang 'Hủy nhập'; ràng buộc CHECK từ chối 'Hoàn kho' gắn dòng nhập và 'Hủy nhập' gắn dòng order. PH-05: phiếu xuất mới và 40 phiếu xuất của bộ B.1 đều có TrangThai 'Đã xác nhận'. PH-06: màn Tồn kho và Chi tiết lô hiển thị ngày giờ dạng hh:mm dd/mm/yyyy. PH-07: 20 vòng, mỗi vòng 3 yêu cầu đồng thời cùng request_id, đều nhận HTTP 201 với order đã tạo, mỗi vòng đúng một order. PH-08: giữ mã tham chiếu của lần hoàn gần nhất; mã và số tiền của từng lần hoàn nằm trong nhật ký. PH-09: order hủy có ThoiDiemDong; 212 order hủy của bộ B.1 đều có giá trị. PH-10: giữ quy tắc làm tròn tại tài liệu 04 mục G.1. Các kết quả trên được kiểm lại trong lượt 258 ca ngày 13/11/2026.

| **Mã** | **Phát hiện**                                                                                                                                                                                                                                                                                                                                                  | **Trạng thái**    |
|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|
| PH-01  | Cột GIAO_DICH_KHO.TonSauGiaoDich luôn bằng 0 ở mọi giao dịch kho, kể cả 48.493 giao dịch của bộ dữ liệu seed. Code không gán balance_after (models.py để mặc định 0, không chỗ nào gán). Tài liệu 04 F.26 mô tả là 'Tồn sau khi ghi nhận'.                                                                                                                     | Đã sửa            |
| PH-02  | PATCH /catalog/suppliers/{id} trả PhieuNhap rỗng dù nhà cung cấp có phiếu nhập; GET trả đúng.                                                                                                                                                                                                                                                                  | Đã sửa            |
| PH-03  | NHOM_MON.NgayXoa để NULL khi xóa mềm nhóm món.                                                                                                                                                                                                                                                                                                                 | Đã sửa            |
| PH-04  | Hủy phiếu nhập ghi giao dịch đảo với LoaiGiaoDich 'Hoàn kho', trùng tên với hoàn kho khi hủy món nên dễ nhầm khi lọc sổ kho hoặc báo cáo. Nhật ký CANCEL_RECEIPT có DuLieuTruoc NULL.                                                                                                                                                                          | Đã sửa            |
| PH-05  | Phiếu xuất đã xác nhận (đã trừ tồn) vẫn có TrangThai 'Nháp' trong cơ sở dữ liệu và trên danh sách Phiếu xuất, dễ hiểu nhầm là chưa ghi. Giá trị trạng thái của PHIEU_XUAT_KHO chưa được quy định trong tài liệu 04.                                                                                                                                            | Đã sửa            |
| PH-06  | Ngày giờ hiển thị dạng ISO thô ở màn Tồn kho ('Dữ liệu lúc 2026-11-10T18:53:07.579223+07:00') và cột Ngày nhập trong Chi tiết lô ('2026-11-10T18:57:13.171000'), thay vì định dạng dd/mm/yyyy hh:mm.                                                                                                                                                           | Đã sửa            |
| PH-07  | Gửi lặp đồng thời cùng request_id (POST /sales/orders): yêu cầu đầu trả 201, các yêu cầu trùng trả HTTP 500 do IntegrityError 1062 trên uq_ORDER_MaYeuCauGui không được bắt (99/100 vòng). Dữ liệu vẫn đúng (1 order, 1 dòng, trừ kho 1 lần) nhưng máy khách nhận lỗi máy chủ thay vì order đã tạo hoặc 422. Gửi lặp tuần tự sau khi commit trả đúng order cũ. | Đã sửa            |
| PH-08  | Hoàn tiền ngoại lệ nhiều lần: cột NGOAI_LE_THANH_TOAN.MaThamChieuHoan chỉ giữ mã tham chiếu của lần hoàn cuối (HT002 bị thay bằng HT003) trong khi SoTienHoan cộng dồn; mã tham chiếu các lần trước không còn trên bản ghi ngoại lệ.                                                                                                                           | Giữ theo thiết kế |
| PH-09  | Hủy toàn bộ order: ORDER.ThoiDiemDong vẫn NULL sau khi order chuyển 'Đã hủy'.                                                                                                                                                                                                                                                                                  | Đã sửa            |
| PH-10  | Đơn giá bình quân lệch do làm tròn khi đảo phiếu: BR19a (10 × 5 và 20 × 7, bình quân 6,33) sau khi hủy phiếu 20 × 7 về 4,99 thay vì 5,00, vì công thức đảo dùng đơn giá đã làm tròn 2 chữ số. Đúng với quy tắc làm tròn tại tài liệu 04 mục G.1.                                                                                                               | Giữ theo thiết kế |
