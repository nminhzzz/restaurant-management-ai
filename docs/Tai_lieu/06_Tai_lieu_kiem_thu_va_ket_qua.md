# 06. TEST CASE VÀ KẾT QUẢ KIỂM TRA

Hệ thống quản lý nhà hàng tích hợp AI hỗ trợ hoạt động kinh doanh

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

Kết quả chạy trên bản 099191e (commit 099191e0ecde95bfc209280f55826360e29d0c3c) ngày 03–04/11/2026, môi trường thử riêng (MySQL 8.4.13, FastAPI, giao diện Next.js bản build): 202 đạt, 21 không đạt, 1 bị chặn và 34 chưa kiểm tra trên tổng 258 ca. Theo nhóm: Danh mục 48/51 (44 đạt, 4 không đạt); Bán hàng 101/101 (96 đạt, 5 không đạt); Kho 41/57 (39 đạt, 2 không đạt); Cài đặt 9/9 (7 đạt, 2 không đạt); Báo cáo 9/15 (6 đạt, 3 không đạt); điều kiện biên 16/25 (10 đạt, 5 không đạt, 1 bị chặn). Các ca chưa kiểm tra thuộc ba nhóm: định giá theo bình quân gia quyền di động, xem trước và xác nhận điều chỉnh kiểm kê, xem trước phiếu xuất hủy và hiển thị đơn giá bình quân trên màn hình tồn kho, giá vốn ước tính của món.

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
<td>03/11/2026 (bản 099191e, UI): Quản lý thêm nhóm 'Món nướng' trên tab Nhóm món: báo 'Đã thêm nhóm món.'; tải lại trang, danh sách hiển thị đúng tên Món nướng.</td>
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
<td>03/11/2026 (bản 099191e, UI): Đổi tên nhóm Món nướng thành 'Món nướng than': báo 'Đã cập nhật nhóm món.'; tải lại, danh sách nhóm và cột Nhóm của Bò nướng hiện tên mới; CSDL giữ MaNhomMon=1, Bò nướng vẫn MaNhomMon=1.</td>
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
<td>03/11/2026 (bản 099191e, UI): Có nhóm A, B, C; bấm Di chuyển lên ở nhóm C: toast 'Yêu cầu không thực hiện được.', PUT /catalog/groups/order trả HTTP 422 (giao diện gửi mảng mã nhóm, API yêu cầu đối tượng {MaNhomMon: [...]}); thứ tự hiển thị và ThuTuHienThi trong CSDL không đổi (A, B, C).</td>
<td>Không đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-04</td>
<td>FR-CAT-02, FR-CAT-06</td>
<td>Có nhóm Món nướng.</td>
<td>1. Thêm Bò nướng, giá 120.000 đ, nhóm Món nướng, ảnh hợp lệ.<br />
2. Lưu.</td>
<td>Món lưu đúng thuộc tính, thuộc một nhóm; ở trạng thái Nháp, chưa hiện khi gọi món.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI): Thêm Bò nướng giá 120.000 đ, nhóm Món nướng, ảnh URL hợp lệ: báo 'Đã thêm món.', danh sách hiện đúng nhóm, 120.000 ₫, trạng thái Nháp, 0 suất khả dụng; CSDL lưu đúng tên/nhóm/ảnh, giá 120000; màn hình gọi món của Thu ngân không hiển thị món ('Không có món nào bán được').</td>
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
<td>03/11/2026 (bản 099191e, UI): Sửa món thành 'Bò nướng lá lốt', đổi ảnh và nhóm sang Món chính: báo 'Đã cập nhật món.'; tải lại hiển thị tên, nhóm mới; CSDL MaNhomMon=2 (Món chính), HinhAnh mới; món chỉ gắn một nhóm.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-06</td>
<td>FR-CAT-02</td>
<td>Có Bò nướng và Gà nướng.</td>
<td>1. Tìm tên Bò.</td>
<td>Kết quả có Bò nướng, không có Gà nướng.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI): Có Bò nướng (đã đổi tên thành Bò nướng lá lốt ở CAT-05) và Gà nướng; gõ 'Bò' vào ô Tìm món: danh sách chỉ còn Bò nướng lá lốt, không có Gà nướng.</td>
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
<td>03/11/2026 (bản 099191e, UI): Xóa nhóm Món nướng than (còn Gà nướng chưa xóa mềm) và xác nhận: bị từ chối 'Không thể xóa nhóm còn món đang hoạt động.'; CSDL nhóm DaXoa=0, Gà nướng vẫn thuộc nhóm.</td>
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
<td>03/11/2026 (bản 099191e, UI): Nhóm Món tạm chỉ có món đã xóa mềm; xóa nhóm và xác nhận: báo 'Đã xóa nhóm món.'; CSDL DaXoa=1 (xóa mềm); hộp thoại Thêm món không còn nhóm này, API tạo món vào nhóm bị từ chối; món cũ vẫn giữ MaNhomMon=6; nhật ký DELETE_GROUP KieuXoa 'Xóa mềm'. Ghi chú: NgayXoa để NULL; danh sách quản trị 'Hiện món đã xóa' để trống cột Nhóm của món thuộc nhóm đã xóa.</td>
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
<td>03/11/2026 (bản 099191e, UI): Xóa nhóm A chưa từng có món và xác nhận: báo 'Đã xóa nhóm món.', nhóm biến khỏi danh sách; bản ghi NHOM_MON MaNhomMon=3 không còn trong CSDL (xóa vĩnh viễn); nhật ký DELETE_GROUP ghi KieuXoa 'Vĩnh viễn'.</td>
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
<td>04/11/2026 (bản 099191e, UI): Chạy lại trên 099191e: Quản lý xóa Ốc xào (đã có trong order ORD-031126-007 đã thanh toán) → 'Đã xóa món.', DaXoa=1, có nhật ký xóa; món không còn trong danh sách bán của Thu ngân; danh mục quản trị (bao gồm món đã xóa) vẫn trả Ốc xào; hóa đơn HD-20261103-0001 vẫn ghi tên 'Ốc xào' và số tiền. Sai lệch: màn hình Chi tiết order cũ hiển thị 'Món #13' thay cho tên món ở các dòng order.</td>
<td>Không đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-11</td>
<td>FR-CAT-07, FR-CAT-11</td>
<td>Món Nháp; thịt bò còn hạn 1.000 g.</td>
<td>1. Gán công thức thịt bò 150 g/suất.<br />
2. Lưu.</td>
<td>Công thức có hiệu lực ngay; món rời Nháp, được gọi khi đủ nguyên liệu.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI): Bò xào ở trạng thái Nháp, Thịt bò còn hạn 1.000 g: Quản lý mở chi tiết món, chọn Thịt bò 150 g, bấm 'Gán công thức lần đầu' → 'Đã gán công thức.'; công thức có hiệu lực ngay; món chuyển Hoạt động, 6 suất khả dụng, xuất hiện trên màn hình gọi món ('Còn 6 suất').</td>
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
<td>03/11/2026 (bản 099191e, UI): Bếp thêm Thịt bò, đơn vị g, mức tồn tối thiểu riêng 500, bảo quản 5 ngày: báo 'Đã thêm nguyên liệu.', danh sách hiện đúng tên, đơn vị g, ngưỡng 500.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-13</td>
<td>FR-CAT-12</td>
<td>Ngưỡng mặc định 300 g.</td>
<td>1. Thêm Hành không đặt ngưỡng riêng.</td>
<td>Nguyên liệu dùng ngưỡng mặc định 300 g.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI): Ngưỡng mặc định 300. Bếp thêm Hành ngay sau khi thêm Thịt bò, không nhập ngưỡng: hộp thoại Thêm nguyên liệu không được làm trống mà giữ giá trị lần trước (mức tồn 500), nên Hành bị lưu MucTonToiThieu=500 thay vì dùng mặc định. Khi tải lại trang rồi thêm Tỏi với form trống, ngưỡng để trống được lưu NULL và hiển thị 'Mặc định'. Nguyên nhân: IngredientFormDialog chỉ reset giá trị trong onOpenChange(true), không chạy khi nút ngoài mở hộp thoại.</td>
<td>Không đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-14</td>
<td>FR-CAT-12</td>
<td>Có nguyên liệu Hành.</td>
<td>1. Sửa tên thành Hành lá.<br />
2. Lưu, tìm theo tên mới.</td>
<td>Lưu tên mới và tìm được đúng nguyên liệu.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI): Bếp sửa tên Hành thành 'Hành lá': báo 'Đã cập nhật nguyên liệu.'; gõ 'Hành lá' vào ô Tìm nguyên liệu trả đúng một dòng Hành lá.</td>
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
<td>03/11/2026 (bản 099191e, UI): Bếp thêm nhà cung cấp A với số điện thoại, email, người liên hệ và địa chỉ: báo 'Đã thêm nhà cung cấp.', danh sách hiện A; CSDL lưu đủ các trường liên hệ đã nhập.</td>
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
<td>03/11/2026 (bản 099191e, UI): NCC A đã có phiếu nhập #1. Bếp sửa SĐT và người liên hệ: báo 'Đã cập nhật nhà cung cấp.', CSDL lưu thông tin mới. Mở Xem lịch sử nhập hàng: hiện đúng 'Phiếu nhập #1 · 03/11/2026 · Hiệu lực' nhưng tổng tiền '0 ₫' trong khi phiếu có 1.000 g × 200 đ = 200.000 đ. Nguyên nhân: PHIEU_NHAP_KHO.TongTien không được tính khi tạo phiếu (lưu 0,00; dòng chi tiết ThanhTien 200.000).</td>
<td>Không đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-17</td>
<td>FR-CAT-14</td>
<td>Nguyên liệu đã có phiếu nhập, chưa có công thức.</td>
<td>1. Thử đổi đơn vị g sang kg.</td>
<td>Từ chối đổi đơn vị; dữ liệu cũ giữ nguyên.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI+API): Thịt bò đã có phiếu nhập #1, chưa có công thức: hộp thoại Sửa nguyên liệu khóa trường Đơn vị tính ở 'g' (disabled); gọi API đổi sang kg bị từ chối 422 'Không thể đổi đơn vị tính sau khi đã được sử dụng.'; CSDL giữ g.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-18</td>
<td>FR-CAT-14</td>
<td>Nguyên liệu đã có trong công thức, chưa có phiếu nhập.</td>
<td>1. Thử đổi đơn vị g sang kg.</td>
<td>Từ chối đổi đơn vị; dữ liệu cũ giữ nguyên.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI+API): Tỏi đã có trong công thức Gà nướng, chưa có phiếu nhập: hộp thoại Sửa nguyên liệu khóa trường Đơn vị tính ở 'g'; gọi API đổi sang kg bị từ chối 422 'Không thể đổi đơn vị tính sau khi đã được sử dụng.'; CSDL giữ g.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-19</td>
<td>FR-CAT-13</td>
<td>Nguyên liệu đã có trong công thức.</td>
<td>1. Xóa nguyên liệu.</td>
<td>Chỉ xóa mềm; dữ liệu tham chiếu lịch sử còn nguyên; có audit log.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI): Tỏi đã có trong công thức Gà nướng: Bếp bấm Xóa nguyên liệu, xác nhận → 'Đã xóa nguyên liệu.'; CSDL DaXoa=1 (xóa mềm); CHI_TIET_CONG_THUC #1 vẫn tham chiếu Tỏi 10 g, API công thức vẫn hiển thị tên Tỏi; nhật ký DELETE_INGREDIENT.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-20</td>
<td>FR-CAT-13</td>
<td>Nguyên liệu đã có phiếu nhập lịch sử.</td>
<td>1. Xóa nguyên liệu.</td>
<td>Chỉ xóa mềm; dữ liệu tham chiếu lịch sử còn nguyên; có audit log.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI): Gừng đã có phiếu nhập #24: xóa trên giao diện → 'Đã xóa nguyên liệu.'; DaXoa=1; phiếu #24 vẫn trả dòng Gừng 200 g; nhật ký DELETE_INGREDIENT.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-21</td>
<td>FR-CAT-16</td>
<td>Nhà cung cấp có lịch sử nhập hàng.</td>
<td>1. Xóa nhà cung cấp.</td>
<td>Chỉ xóa mềm; phiếu nhập cũ vẫn tham chiếu được; có audit log.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI): NCC B có phiếu nhập #24: xóa trên tab Nhà cung cấp → 'Đã xóa nhà cung cấp.', biến khỏi danh sách; DaXoa=1; phiếu #24 vẫn giữ MaNhaCungCap=2; nhật ký DELETE_SUPPLIER.</td>
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
<td>04/11/2026 (bản 099191e, API): Mốc Business Date thật 06:00 ngày 04/11: lịch giá 110.000 (#5) và công thức 180 g (#3) đặt cho Business Date 04/11 từ 05:23. Gửi lúc 05:59:59.247 → ORD-031126-036, BD 03/11, giá 100.000 (phiên bản #4), trừ 150 g; gửi lúc 06:00:00.458 → ORD-041126-001, BD 04/11, giá 110.000 (#5), trừ 180 g (công thức #3); dòng cũ giữ nguyên. Kết luận cho giá: trước mốc 100.000, từ mốc 110.000, có lưu phiên bản.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-23</td>
<td>FR-CAT-20</td>
<td>Có món Bò xào.</td>
<td>1. Lên lịch giá vào Business Date đã bắt đầu.</td>
<td>Từ chối lưu lịch; không thay đổi phiên bản đang áp dụng.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI+API): Business Date hiện tại 04/11 (đã bắt đầu): nhập giá 95.000 ngày 04/11 cho Gà xào → giao diện báo 'Business Date phải là một Business Date trong tương lai', không gửi yêu cầu; API cùng dữ liệu → 422 'BusinessDate áp dụng phải là ngày trong tương lai.'; giá đang áp dụng 85.000 không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-24</td>
<td>FR-CAT-20</td>
<td>Có món Bò xào.</td>
<td>1. Lên lịch giá vào Business Date đã kết thúc.</td>
<td>Từ chối lưu lịch; không thay đổi phiên bản đang áp dụng.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI+API): Lên lịch giá cho Business Date 03/11 (đã kết thúc): giao diện chặn cùng thông báo; API 422; phiên bản đang áp dụng không đổi.</td>
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
<td>04/11/2026 (bản 099191e, UI): Chọn Business Date 09/11 (sau ngày kế tiếp), giá 95.000, bấm Lưu → 'Đã lên lịch giá mới.'; phiên bản #16 'Chờ áp dụng' từ 09/11; giá hiện tại vẫn 85.000.</td>
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
<td>04/11/2026 (bản 099191e, UI): Đang có lịch A (95.000 từ 09/11), tạo lịch B 99.000 từ 10/11 → 'Đã lên lịch giá mới.'; chỉ còn 1 lịch chờ (B, #17); nhật ký SCHEDULE_PRICE_CHANGE ghi LichBiGhiDe là lịch A. Ghi chú: bản ghi lịch A bị xóa khỏi LICH_SU_GIA_MON, chỉ còn vết trong nhật ký.</td>
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
<td>04/11/2026 (bản 099191e, UI): Lịch chờ 99.000 từ 10/11: bấm Hủy lịch → 'Đã hủy giá đang chờ áp dụng.'; giá đang áp dụng vẫn 90.000; nhật ký CANCEL_PRICE_CHANGE lưu dữ liệu lịch bị hủy. Ghi chú: bản ghi lịch bị xóa khỏi bảng phiên bản thay vì chuyển trạng thái Đã hủy.</td>
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
<td>04/11/2026 (bản 099191e, UI): Gà xào giá 85.000, có lịch chờ 99.000 từ 10/11: nhập 90.000 ở Áp dụng giá ngay → 'Đã áp dụng giá mới ngay lập tức.'; phiên bản #18 Đang áp dụng, #9 Hết hiệu lực; nhật ký APPLY_PRICE_DIRECTLY có trước/sau; lịch chờ 99.000 không đổi; dòng cũ (order #6, #35) giữ 85.000, dòng gửi mới (order #44) dùng 90.000.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-29</td>
<td>FR-CAT-05</td>
<td>Món có lịch giá đang chờ.</td>
<td>1. Xóa mềm món.</td>
<td>Lịch chờ tương ứng bị hủy.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI): Cua hấp có lịch giá chờ 140.000 từ 08/11 (#19): Quản lý xóa món → 'Đã xóa món.', DaXoa=1; lịch giá #19 không còn ở trạng thái Chờ áp dụng (chuyển 'Hết hiệu lực'). Ghi chú: trạng thái ghi là 'Hết hiệu lực' thay vì 'Đã hủy'.</td>
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
<td>04/11/2026 (bản 099191e, API): Mốc Business Date thật 06:00 ngày 04/11: lịch giá 110.000 (#5) và công thức 180 g (#3) đặt cho Business Date 04/11 từ 05:23. Gửi lúc 05:59:59.247 → ORD-031126-036, BD 03/11, giá 100.000 (phiên bản #4), trừ 150 g; gửi lúc 06:00:00.458 → ORD-041126-001, BD 04/11, giá 110.000 (#5), trừ 180 g (công thức #3); dòng cũ giữ nguyên. Kết luận cho công thức: trước mốc 150 g, từ mốc 180 g.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-31</td>
<td>FR-CAT-08</td>
<td>Có món Bò xào.</td>
<td>1. Lên lịch công thức vào Business Date đã bắt đầu.</td>
<td>Từ chối lưu lịch; không thay đổi phiên bản đang áp dụng.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, API): Lên lịch công thức Vịt xào cho Business Date 04/11 (đã bắt đầu) → 422 'BusinessDate áp dụng phải là ngày trong tương lai.'; công thức đang áp dụng #8 không đổi. (Thực hiện qua API.)</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-32</td>
<td>FR-CAT-08</td>
<td>Có món Bò xào.</td>
<td>1. Lên lịch công thức vào Business Date đã kết thúc.</td>
<td>Từ chối lưu lịch; không thay đổi phiên bản đang áp dụng.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, API): Lên lịch công thức cho Business Date 03/11 (đã kết thúc) → 422 cùng thông báo; công thức đang áp dụng không đổi. (Thực hiện qua API.)</td>
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
<td>04/11/2026 (bản 099191e, UI): Vịt xào (công thức đang áp dụng Vịt 150 g): chọn Vịt 170 g, Business Date 09/11, bấm Lên lịch thay đổi → 'Đã lên lịch thay đổi công thức.'; lịch chờ áp dụng từ 09/11, công thức hiện tại vẫn 150 g.</td>
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
<td>04/11/2026 (bản 099191e, UI): Có lịch công thức A (170 g từ 09/11), tạo lịch B 190 g từ 10/11 → thông báo thành công; chỉ còn 1 lịch chờ (B, #15); nhật ký SCHEDULE_RECIPE_CHANGE ghi LichBiGhiDe là lịch A (#14).</td>
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
<td>04/11/2026 (bản 099191e, UI): Bấm Hủy lịch ở công thức chờ 190 g và xác nhận → 'Đã hủy công thức đang chờ áp dụng.'; công thức hiện tại vẫn 160 g; có nhật ký hủy lịch.</td>
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
<td>04/11/2026 (bản 099191e, UI): Đang có lịch chờ 190 g: Áp dụng ngay công thức Vịt 160 g → 'Đã áp dụng công thức ngay.'; công thức #16 Đang áp dụng, #8 Hết hiệu lực; nhật ký APPLY_RECIPE_DIRECTLY có trước/sau; lịch chờ #15 giữ nguyên; dòng cũ (order #45) giữ tiêu hao 150 g, dòng gửi mới (order #47) dùng công thức #16 trừ 160 g.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-37</td>
<td>FR-CAT-05</td>
<td>Món có lịch công thức đang chờ.</td>
<td>1. Xóa mềm món.</td>
<td>Lịch chờ tương ứng bị hủy.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI): Cua hấp có lịch công thức chờ 160 g từ 08/11 (#17): sau khi xóa mềm món, lịch #17 chuyển 'Hết hiệu lực', không còn chờ áp dụng.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-38</td>
<td>FR-CAT-26, FR-CAT-27</td>
<td>Món đủ nguyên liệu, đang phục vụ.</td>
<td>1. Bật tạm dừng thủ công.</td>
<td>Hiển thị Tạm dừng phục vụ; không cho thêm món.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI+API): Bò xào đủ nguyên liệu (6 suất): Quản lý bấm Tạm dừng món → 'Đã tạm dừng món.', danh sách hiện 'Tạm dừng phục vụ – Tạm dừng thủ công'. Chạm Bò xào trên màn hình gọi món: báo 'Món đang tạm dừng phục vụ.', không tạo lượt giữ; API giữ món cũng 422 cùng thông báo. Ghi chú: ô món trên màn hình gọi món vẫn hiện 'Còn 6 suất', không gắn nhãn tạm dừng.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-39</td>
<td>FR-CAT-26, FR-CAT-27</td>
<td>Món tạm dừng thủ công và đủ nguyên liệu.</td>
<td>1. Tắt tạm dừng thủ công.</td>
<td>Món được mở lại và cho thêm vào lượt chọn.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI): Bò xào đang tạm dừng thủ công, đủ nguyên liệu: bấm Mở lại món → 'Đã mở lại món.', trạng thái Hoạt động, 6 suất khả dụng; trên màn hình gọi món chạm Bò xào thêm được vào lượt chọn (giỏ có 1 dòng 100.000 ₫); sau đó Hủy lượt chọn giải phóng lượng giữ.</td>
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
<td>03/11/2026 (bản 099191e, UI+API): Gà nướng thiếu nguyên liệu (Tỏi 0 g) và được bấm Tạm dừng món: danh sách hiện đồng thời 'Hết nguyên liệu' và 'Tạm dừng thủ công'; API giữ món trả 'Món đang hết nguyên liệu và tạm dừng phục vụ.'. Bấm Mở lại món: 'Đã mở lại món.', trạng thái vẫn 'Hết nguyên liệu', 0 suất; API giữ món vẫn 422 'Món đang hết nguyên liệu.'.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-41</td>
<td>FR-CAT-27</td>
<td>Món đã có công thức; khả dụng không đủ một suất.</td>
<td>1. Xem trạng thái và thử thêm món.</td>
<td>Hiển thị Hết nguyên liệu, chặn thêm; thuộc tính này được suy ra, không lưu trong MON_AN.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI+API): Gà nướng có công thức Tỏi 10 g/suất, khả dụng 0: danh mục hiện 'Hết nguyên liệu – 0 suất khả dụng'; màn hình gọi món không đưa món vào danh sách bán; API giữ món bị chặn 422 'Món đang hết nguyên liệu.'; bảng MON_AN không có cột HetNguyenLieu (chỉ MaMon, TenMon, MaNhomMon, DaXoa, HinhAnh, ChuaCoCongThuc, TamDungThuCong) – trạng thái được suy ra.</td>
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
<td>03/11/2026 (bản 099191e, UI): Quản lý thêm bàn B1 (Tầng 1, 4 chỗ): báo 'Đã thêm bàn.'; danh sách hiện B1 trạng thái Trống; CSDL TrangThai='Trống', MaOrderDangPhucVu NULL.</td>
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
<td>03/11/2026 (bản 099191e, UI): Sửa tên B1 thành B01: báo 'Đã cập nhật bàn.'; danh sách hiện B01, Trống; CSDL giữ MaBan=3 và TrangThai='Trống'.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-44</td>
<td>FR-CAT-17, FR-CAT-19</td>
<td>Bàn đang phục vụ order O1.</td>
<td>1. Thử xóa bàn.</td>
<td>Từ chối; bàn vẫn gắn O1.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI): B01 đang phục vụ order O1 (ORD-031126-001): Quản lý bấm Xóa bàn B01 và xác nhận → bị từ chối 'Không thể xóa bàn đang được sử dụng.'; CSDL B01 DaXoa=0, Đang phục vụ, MaOrderDangPhucVu=1.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-45</td>
<td>FR-CAT-19</td>
<td>Bàn Trống, đã có order lịch sử.</td>
<td>1. Xóa bàn.</td>
<td>Chỉ xóa mềm; giữ tham chiếu lịch sử và ghi audit log.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI): B01 Trống, đã có order lịch sử O1 (LICH_SU_DOI_BAN B01→B3): Quản lý bấm Xóa bàn B01 và xác nhận → 'Đã xóa bàn.', bàn biến khỏi danh sách; CSDL B01 DaXoa=1 (xóa mềm), bản ghi và lịch sử đổi bàn còn nguyên; có nhật ký xóa bàn. Ghi chú: hộp xác nhận vẫn hiện thông báo cũ 'Không thể xóa bàn đang được sử dụng.' còn sót từ lần thử ở CAT-44.</td>
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
<td>03/11/2026 (bản 099191e, UI): Thịt bò có ngưỡng riêng 500; nhập -1 trên hộp thoại Sửa nguyên liệu và Lưu: API trả 422, giao diện báo 'Yêu cầu không thực hiện được.' (thông báo chung, không nêu lý do); ngưỡng trong CSDL giữ 500.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-47</td>
<td>NFR-04</td>
<td>Đăng nhập vai trò Bếp.</td>
<td>1. Gọi trực tiếp API sửa giá món với dữ liệu hợp lệ.</td>
<td>Backend từ chối quyền; dữ liệu không thay đổi.</td>
<td>Trọng yếu</td>
<td>03/11/2026 (bản 099191e, API): Bếp gọi trực tiếp POST /catalog/dishes/4/prices/apply-now và /prices/schedule với dữ liệu hợp lệ: 403; LICH_SU_GIA_MON của Bò xào vẫn 1 phiên bản, giá đang áp dụng 100.000.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-48</td>
<td>NFR-04</td>
<td>Đăng nhập vai trò Thu ngân.</td>
<td>1. Gọi trực tiếp API thêm bàn với dữ liệu hợp lệ.</td>
<td>Backend từ chối quyền; dữ liệu không thay đổi.</td>
<td>Trọng yếu</td>
<td>03/11/2026 (bản 099191e, API): Thu ngân gọi trực tiếp POST /catalog/tables tạo bàn B99 hợp lệ: 403; bảng BAN vẫn 0 bản ghi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-49</td>
<td>FR-CAT-29</td>
<td>Bò xào giá bán 80.000 đ; công thức 150 g bò (đơn giá bình quân 230.000 đ/kg) và 50 g hành (40.000 đ/kg); TyLeGiaVonCanhBao = 40%.</td>
<td>1. Đăng nhập Quản lý, mở danh sách món.2. Chọn Bò xào để xem chi tiết giá vốn.</td>
<td>Giá vốn ước tính 36.500 đ (34.500 + 2.000); tỷ lệ giá vốn 45,6%; lãi gộp 43.500 đ/suất; món được đánh dấu cảnh báo; chi tiết hiển thị hai nguyên liệu với định lượng, đơn giá và thành tiền.</td>
<td>Trọng yếu</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="even">
<td>TC-CAT-50</td>
<td>FR-CAT-29, FR-INV-02</td>
<td>Như TC-CAT-49 nhưng đơn giá bình quân của bò là 180.000 đ/kg: giá vốn 29.000 đ, tỷ lệ 36,25%, chưa cảnh báo.</td>
<td>1. Nhập kho bò với giá cao hơn để đơn giá bình quân tăng lên 230.000 đ/kg.2. Mở lại danh sách món.</td>
<td>Giá vốn của Bò xào cập nhật thành 36.500 đ, tỷ lệ 45,6% và có cảnh báo; giá bán vẫn 80.000 đ, hệ thống không tự đổi giá bán.</td>
<td>Trọng yếu</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="odd">
<td>TC-CAT-51</td>
<td>FR-CAT-29</td>
<td>Công thức Gỏi gà có Sả, nguyên liệu chưa có đơn giá bình quân.</td>
<td>1. Mở danh sách món, tìm Gỏi gà.</td>
<td>Cột giá vốn hiển thị “Chưa đủ dữ liệu” kèm tên Sả; không tính Sả bằng 0; không hiển thị tỷ lệ giá vốn hay cảnh báo cho món.</td>
<td>Thường</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
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
<td>03/11/2026 (bản 099191e, UI): Thu ngân chọn bàn B01 (bàn B1 đã đổi tên ở CAT-43), chạm Bò xào 2 lần: giỏ 2 suất 200.000 ₫. CSDL: 1 lượt giữ 2 suất, giữ 300 g trên lô #1, người dùng #2, mã lượt chọn, phiên bản công thức #2 và giá #4, có hạn giữ; tồn 1.000 g, khả dụng 700 g; chưa có ORDER/PHIEU_BEP; B01 vẫn Trống, chưa gắn order. Ghi chú: ô món vẫn hiện 'Còn 6 suất' sau khi giữ 2 suất.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-02</td>
<td>FR-SALE-01, FR-INV-10</td>
<td>Bò khả dụng 149 g; công thức 150 g/suất.</td>
<td>1. Thêm 1 suất Bò xào.</td>
<td>Từ chối, không tạo lượng giữ.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI+API): Mực 149 g, công thức Mực xào 150 g/suất: màn hình gọi món không liệt kê Mực xào (khả dụng 0 suất); gọi API giữ 1 suất → 422 'Món đang hết nguyên liệu.'; không tạo lượt giữ nào.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-03</td>
<td>FR-SALE-01, FR-INV-10</td>
<td>Bò khả dụng 150 g; công thức 150 g/suất.</td>
<td>1. Thêm 1 suất Bò xào.</td>
<td>Giữ thành công 150 g; khả dụng còn 0 g, tồn sổ sách không đổi.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Tôm 150 g (một lô), Tôm xào 150 g/suất: chạm Tôm xào → giỏ 1 suất; CSDL giữ 150 g trên lô Tôm; khả dụng 0 g, tồn sổ sách 150 g không đổi.</td>
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
<td>03/11/2026 (bản 099191e, UI): Thêm Bò xào ở B01, nhập ghi chú 'không hành', bấm Gửi bếp: báo 'Đã gửi món của B01 xuống bếp.'; dòng order lưu GhiChu 'không hành', công thức phiên bản #2; phiếu bếp #1 có nội dung 'Bò xào x1 (không hành) - 100000' (màn hình thanh toán hiển thị dòng kèm ghi chú và phiếu bếp #1 Chờ in); sổ kho trừ đúng 150 g từ lô #1.</td>
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
<td>04/11/2026 (bản 099191e, UI): Gửi Ốc xào để trống ghi chú: gửi thành công, dòng order GhiChu NULL, phiếu bếp in 'Ốc xào x1 - 60000' không kèm ghi chú; trừ đúng 150 g theo công thức.</td>
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
<td>04/11/2026 (bản 099191e, UI): B3 Trống, Heo L1 200 g (nhập 01/11), L2 800 g (nhập 02/11); chạm Heo xào 2 lần, Gửi bếp → 'Đã gửi món của B3 xuống bếp.'; một order ORD-031126-004 với dòng 2 suất; sổ kho 2 giao dịch: L1 -200 g, L2 -100 g; lượt giữ 'Đã gửi'; B3 Đang phục vụ, gắn order; phiếu bếp #4 được gửi tới máy in thử sau commit (log máy in ghi 'Heo xao x2').</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-07</td>
<td>FR-SALE-03</td>
<td>Lần gửi đã commit nhưng phía người dùng timeout.</td>
<td>1. Gửi lại cùng mã yêu cầu.</td>
<td>Trả kết quả cũ; chỉ một order, không trừ kho hoặc tạo dòng món lần hai.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Gửi order mang về với request_id X → 201 ORD-031126-026; gửi lại đúng nội dung và X (giả lập phía client timeout) → 201 trả cùng MaOrder 26; order chỉ có 1 dòng, số giao dịch kho giữ 61 (không trừ lần hai), chỉ 1 ORDER mang mã yêu cầu X.</td>
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
<td>04/11/2026 (bản 099191e, Script): Lượt chọn hợp lệ 1 suất Sò nướng; tiêm lỗi vào bước ghi phiếu bếp (sau khi trừ kho, trước commit) → gửi thất bại 'QA injected failure…'; rollback toàn bộ: tồn 1.250 g, số ORDER 241 và giao dịch kho 342 như trước; lượt giữ vẫn 'Đang giữ' với hạn cũ.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-09</td>
<td>FR-SALE-04</td>
<td>Business Date mới chưa có order.</td>
<td>1. Gửi hai order hợp lệ liên tiếp.</td>
<td>Mã ORD-ddMMyy-001 và 002 theo Business Date; mã khác nhau.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, API): Business Date 04/11 mới bắt đầu, chưa có order: hai order hợp lệ liên tiếp nhận ORD-041126-001 và ORD-041126-002, khác nhau.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-10</td>
<td>FR-SALE-04</td>
<td>Một mã đã được cấp cho transaction sau đó rollback.</td>
<td>1. Gửi order hợp lệ kế tiếp.</td>
<td>Không dùng lại số đã cấp; mã mới duy nhất.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, API): Lần gửi Tôm xào ở INV-09 bị từ chối trong transaction sau khi đã cấp số ORD-031126-003; order hợp lệ kế tiếp nhận ORD-031126-004 (không dùng lại 003); mã duy nhất trong bảng ORDER.</td>
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
<td>04/11/2026 (bản 099191e, API): Order đầu tiên của Business Date 04/11 có mã ORD-041126-001 (ngày trước đã tới ORD-031126-036), không trùng ngày trước.</td>
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
<td>04/11/2026 (bản 099191e, UI): Thời hạn giữ 5 phút; Quản lý giữ 1 Gà xào lúc 05:45:30, để quá hạn (05:50:30), đủ nguyên liệu. Giỏ hiện 'Hết thời gian giữ — gửi lại để dùng giá hiện tại'; bấm Gửi bếp → hộp xác nhận 'Lượt giữ chỗ đã hết hạn…' → đồng ý → 'Đã gửi món của Mang về xuống bếp.'; backend kiểm tra lại và ghi 1 lần tiêu hao 150 g; hạn giữ không bị tự gia hạn trước khi gửi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-13</td>
<td>FR-SALE-05</td>
<td>Giữ đã hết hạn; order khác dùng nguyên liệu, còn thiếu một suất.</td>
<td>1. Gửi lượt chọn cũ.</td>
<td>Từ chối, nêu món và số lượng thiếu; giữ danh sách chọn; không ghi tiêu hao.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Lượt giữ A 2 Bê xào (300 g) hết hạn lúc 05:50:44; order khác dùng 1 suất (còn 150 g, thiếu 1 suất). Gửi lượt chọn cũ của A (xác nhận hết hạn) → bị từ chối, không ghi tiêu hao, lượt chọn còn nguyên. Sai lệch: thông báo chỉ là 'Không đủ tồn kho khả dụng.', không nêu món và số lượng thiếu như kỳ vọng.</td>
<td>Không đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-14</td>
<td>FR-SALE-05</td>
<td>Giá đổi sau khi giữ món.</td>
<td>1. Gửi mà chưa xác nhận phiên bản mới.</td>
<td>Yêu cầu xác nhận nội dung mới; chưa tạo dòng order hay tiêu hao.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Lượt giữ Bò xào tạo lúc 05:59:57 (giá #4/công thức #2), sau 06:00 giá và công thức đổi. Gửi không xác nhận → 422 'Giá hoặc công thức món đã thay đổi. Xác nhận…'; không tạo dòng/tiêu hao.</td>
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
<td>04/11/2026 (bản 099191e, API): Lượt giữ Bò xào tạo lúc 05:59:57 (giá #4/công thức #2), sau 06:00 giá và công thức đổi. Gửi lại có xác nhận → ORD-041126-002, giá 110.000 phiên bản #5, tiêu hao một lần.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-16</td>
<td>FR-SALE-05</td>
<td>Công thức đổi sau khi giữ món.</td>
<td>1. Gửi mà chưa xác nhận phiên bản mới.</td>
<td>Yêu cầu xác nhận nội dung mới; chưa tạo dòng order hay tiêu hao.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Lượt giữ Bò xào tạo lúc 05:59:57 (giá #4/công thức #2), sau 06:00 giá và công thức đổi. Gửi không xác nhận → 422 yêu cầu xác nhận nội dung mới (công thức đổi 150→180 g); không tạo dòng/tiêu hao.</td>
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
<td>04/11/2026 (bản 099191e, API): Lượt giữ Bò xào tạo lúc 05:59:57 (giá #4/công thức #2), sau 06:00 giá và công thức đổi. Gửi lại có xác nhận → dòng dùng công thức #3, trừ đúng 180 g một lần, không trừ lặp.</td>
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
<td>03/11/2026 (bản 099191e, UI): Order ORD-031126-001 tại chỗ Đang mở gắn B01: trên màn hình thanh toán bấm Thêm món → Bò xào, số lượng 1 → 'Đã thêm Bò xào.'; tạo dòng #2 Chờ làm và phiếu bếp #2 'Bò xào x1'; lượt giữ #4 chuyển Đã gửi; chỉ trừ thêm 150 g từ lô #1 (850 → 700 g); dòng #1 giữ nguyên ghi chú, giá và trạng thái.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-19</td>
<td>FR-SALE-06</td>
<td>Order tại chỗ đã rời bàn.</td>
<td>1. Thử gọi thêm vào order.</td>
<td>Từ chối gọi thêm theo phạm vi FR-SALE-06; không giữ hoặc trừ nguyên liệu.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI+API): O1 tại chỗ đã rời bàn (B3 được giải phóng). Trên màn hình thanh toán, Thêm món bị chặn đúng ('Order đã được giải phóng khỏi bàn, không thể gọi thêm.'). Nhưng API giữ món cho phần gọi thêm (POST /sales/holds với order_id=1 và bàn cũ B3 – đường của màn hình Gọi thêm) vẫn trả 201 và giữ 150 g Thịt bò; bước gửi sau đó bị chặn 422 nên không thêm dòng/trừ kho, song lượng giữ chiếm khả dụng tới khi hết hạn/giải phóng. Kỳ vọng: từ chối ngay, không giữ nguyên liệu. Nguyên nhân: reservations.create_hold không kiểm tra BAN.MaOrderDangPhucVu.</td>
<td>Không đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-20</td>
<td>FR-SALE-06, FR-SALE-31</td>
<td>Order mang về Đang mở; kho đủ; có món đã gửi.</td>
<td>1. Thêm 1 suất vào lượt gọi thêm. 2. Gửi phần gọi thêm.</td>
<td>Bổ sung dòng món và phiếu bếp vào cùng order; giữ rồi trừ đúng nguyên liệu phần thêm; dòng cũ giữ nguyên giá/công thức; không gắn bàn.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Đơn mang về ORD-031126-007 Đang mở đã có 1 Ốc xào: trên màn hình thanh toán bấm Thêm món → Ốc xào, 1 suất → 'Đã thêm Ốc xào.'; cùng order có thêm dòng mới và phiếu bếp thứ 2; lượt giữ chuyển Đã gửi rồi trừ đúng 150 g; dòng cũ giữ giá 60.000; order vẫn không gắn bàn.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-21</td>
<td>FR-SALE-08</td>
<td>Đang giữ 2 suất; khả dụng đủ thêm 150 g.</td>
<td>1. Tăng lên 3 suất.</td>
<td>Giữ thêm 150 g, số lượng 3; làm mới thời hạn.</td>
<td>Trọng yếu</td>
<td>03/11/2026 (bản 099191e, UI): Đang giữ 2 suất (300 g), khả dụng đủ: bấm 'Thêm một Bò xào' → giỏ 3 suất 300.000 ₫; CSDL lượt giữ SoLuong=3, giữ 450 g trên lô #1, hạn giữ làm mới từ 21:58:45 lên 21:59:38; tồn sổ sách 1.000 g không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-22</td>
<td>FR-SALE-08</td>
<td>Đang giữ 2 suất; khả dụng chỉ 100 g.</td>
<td>1. Tăng lên 3 suất.</td>
<td>Từ chối; số lượng, lượng giữ và hạn giữ cũ không đổi.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Vịt 400 g, giữ 2 suất (300 g), khả dụng còn 100 g: bấm Thêm một Vịt xào → báo 'Món đang hết nguyên liệu.'; giỏ vẫn 2 suất; CSDL lượt giữ #13 vẫn SoLuong 2, giữ 300 g, hạn giữ 05:33:09 không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-23</td>
<td>FR-SALE-08</td>
<td>Đang giữ 2 suất, 300 g.</td>
<td>1. Giảm xuống 1 suất.</td>
<td>Giải phóng 150 g; còn giữ 150 g; tồn sổ sách không đổi.</td>
<td>Trọng yếu</td>
<td>03/11/2026 (bản 099191e, UI): Đang giữ 2 suất/300 g: bấm 'Bớt một Bò xào' → 1 suất; CSDL giữ 150 g, khả dụng tăng từ 700 lên 850 g, tồn sổ sách 1.000 g, không phát sinh giao dịch kho.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-24</td>
<td>FR-SALE-08</td>
<td>Dòng chưa gửi đang giữ 300 g.</td>
<td>1. Xóa dòng.</td>
<td>Giải phóng đủ 300 g; không có giao dịch hoàn tồn.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Dòng Vịt xào chưa gửi giữ 300 g: gọi DELETE /sales/holds/13 (giao diện chỉ hiện nút xóa khi dòng còn 1 suất) → lượt giữ 'Đã giải phóng', khả dụng về 400 g, tồn 400 g; số giao dịch kho của Vịt không đổi (chỉ có giao dịch nhập), không có hoàn kho.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-25</td>
<td>FR-SALE-08</td>
<td>Lượt chọn có hai dòng đang giữ.</td>
<td>1. Bỏ toàn bộ lượt chọn.</td>
<td>Giải phóng toàn bộ lượng giữ của lượt chọn.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Lượt chọn 2 dòng giữ ở B4: Hủy lượt chọn giải phóng cả hai lượt giữ (#14, #15 Đã giải phóng), khả dụng trở lại đầy đủ.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-26</td>
<td>FR-SALE-08</td>
<td>Dòng đang giữ còn hiệu lực; ghi lại hạn giữ.</td>
<td>1. Sửa ghi chú.</td>
<td>Ghi chú cập nhật; hạn giữ không đổi.</td>
<td>Trọng yếu</td>
<td>03/11/2026 (bản 099191e, UI): Dòng Bò xào đang giữ, hạn 21:59:38: nhập ghi chú 'không hành' trên giỏ → ô ghi chú cập nhật; hạn giữ trong CSDL vẫn 21:59:38. Ghi chú: ghi chú chỉ lưu ở trạng thái giao diện tới khi gửi (GIU_CHO_MON.GhiChu vẫn NULL), tải lại trang thì mất.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-27</td>
<td>FR-SALE-08</td>
<td>Dòng đang giữ còn hiệu lực; ghi lại hạn giữ.</td>
<td>1. Mở lại màn hình lượt chọn.</td>
<td>Hạn giữ không đổi.</td>
<td>Trọng yếu</td>
<td>03/11/2026 (bản 099191e, UI): Tải lại màn hình gọi món của B01: lượt chọn được khôi phục (1 suất Bò xào); hạn giữ trong CSDL vẫn 21:59:38, không gia hạn.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-28</td>
<td>FR-SALE-08</td>
<td>Hai dòng A, B đang giữ; ghi lại hạn giữ A.</td>
<td>1. Sửa ghi chú dòng B.</td>
<td>Hạn giữ dòng A không đổi.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): B4 có hai dòng giữ: A Heo xào (hạn 05:34:14), B Ốc xào (hạn 05:34:16); nhập ghi chú 'ít cay' cho dòng B → hạn giữ dòng A (và B) không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-29</td>
<td>FR-SALE-08</td>
<td>Lượt giữ còn hiệu lực.</td>
<td>1. Đóng trình duyệt, đợi quá hạn; mở lại bằng phiên hợp lệ.</td>
<td>Giữ hết hiệu lực theo giờ server; khả dụng được giải phóng dù trình duyệt đã đóng.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Màn Bán hàng (Quản lý), Đơn mới: chọn 'INV08 cua món 6c19' → lượt giữ #1021 (100 g, hết hạn 11:35:31); tồn kho: giữ 100 g, khả dụng 500 g. Đóng hẳn trình duyệt (đóng tab cuối, pane đóng), đợi 5 phút. Mở lại trình duyệt bằng phiên đăng nhập còn hiệu lực (không phải đăng nhập lại): giữ #1021 'Hết hạn' theo giờ server (11:36:03 &gt; 11:35:31), không gia hạn; giữ 0 g, khả dụng 600 g; màn Bán hàng hiển thị 'Còn 6 suất', giỏ không khôi phục lượt chọn cũ.</td>
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
<td>04/11/2026 (bản 099191e, UI): Đơn mang về: chạm Ốc xào, Gửi bếp → 'Đã gửi món của Mang về xuống bếp.'; ORDER ORD-031126-007 loại Mang về, MaBan NULL; trừ 150 g; phiếu bếp #6 'Ốc xào x1' gửi máy in thử; không bàn nào thay đổi trạng thái.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-31</td>
<td>FR-SALE-07, FR-SALE-10, FR-INV-04</td>
<td>Dòng Chờ làm gồm 2 suất; đã in; Bếp xác nhận trực tiếp chưa làm; đã trừ L1 200 g, L2 100 g.</td>
<td>1. Hủy cả dòng, nhập lý do.</td>
<td>Hoàn L1 200 g và L2 100 g; ghi người, thời gian, số lượng, lý do; không yêu cầu bản ghi xác nhận bếp trong hệ thống.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Dòng Heo xào 2 suất Chờ làm, phiếu đã in, đã trừ L1 200/L2 100: bấm Hủy món, nhập lý do 'Khách đổi món, bếp xác nhận chưa làm' → 'Đã hủy món.'; dòng Đã hủy; giao dịch Hoàn kho +200 g vào L1 và +100 g vào L2 (lô về 200/800 g); nhật ký CANCEL_ORDER_LINE ghi người #2, thời điểm, SoLuong 2 và lý do; không yêu cầu bản ghi xác nhận bếp.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-32</td>
<td>FR-SALE-07, FR-SALE-10, FR-INV-04</td>
<td>Dòng Chờ làm 2 suất, trừ cùng lô 300 g; Bếp xác nhận chưa làm.</td>
<td>1. Giảm 1 suất, nhập lý do.</td>
<td>Còn 1 suất; hoàn đúng 150 g vào lô gốc; có audit log.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Chạy lại trên 099191e: dòng Gà xào 2 suất Chờ làm, đã trừ 300 g cùng lô #8. Màn hình thanh toán chỉ cho sửa số lượng tại chỗ (ô số + Lưu), không có bước nhập lý do; giảm còn 1 → 'Đã cập nhật số lượng.', hoàn đúng 150 g vào lô #8, nhật ký REDUCE_ORDER_LINE có trước/sau 2→1 nhưng LyDo NULL. Kỳ vọng: có nhập lý do khi giảm. (Ghi chú điều kiện: lần gửi đầu bị chặn do lỗi INV-09 vì lượt giữ chiếm hết 300 g khả dụng; đã nhập thêm lô 300 g để gửi được.)</td>
<td>Không đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-33</td>
<td>FR-SALE-07, FR-SALE-10</td>
<td>Dòng ở trạng thái Đã xác nhận xong.</td>
<td>1. Thử giảm số lượng.</td>
<td>Từ chối; dòng món và tồn kho không đổi.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Dòng Bò xào 2 suất của order #28 ở Đã xác nhận xong: gửi giảm còn 1 → 422 'Chỉ sửa món ở trạng thái Chờ.'; dòng vẫn 2 suất, không có hoàn kho.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-34</td>
<td>FR-SALE-07, FR-SALE-10</td>
<td>Dòng ở trạng thái Đã xác nhận xong.</td>
<td>1. Thử xóa dòng.</td>
<td>Từ chối; dòng món và tồn kho không đổi.</td>
<td>Trọng yếu</td>
<td>03/11/2026 (bản 099191e, UI+API): Dòng ở Đã xác nhận xong: giao diện không còn nút Hủy món; gọi API hủy dòng → 422 'Chỉ hủy món ở trạng thái Chờ.'; dòng giữ trạng thái, SoLuong 1; lô #1 850 g, không có giao dịch kho mới.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-35</td>
<td>FR-SALE-07, FR-SALE-10</td>
<td>Dòng ở trạng thái Đã phục vụ.</td>
<td>1. Thử giảm số lượng.</td>
<td>Từ chối; dòng món và tồn kho không đổi.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Cùng dòng sau khi chuyển Đã phục vụ: giảm còn 1 → 422 'Chỉ sửa món ở trạng thái Chờ.'; dòng vẫn 2 suất, không có hoàn kho.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-36</td>
<td>FR-SALE-07, FR-SALE-10</td>
<td>Dòng ở trạng thái Đã phục vụ.</td>
<td>1. Thử xóa dòng.</td>
<td>Từ chối; dòng món và tồn kho không đổi.</td>
<td>Trọng yếu</td>
<td>03/11/2026 (bản 099191e, UI+API): Dòng #1 Đã phục vụ: giao diện không có nút Hủy món; gọi API hủy dòng → 422 'Chỉ hủy món ở trạng thái Chờ.'; dòng và lô #1 (850 g) không đổi, không có giao dịch kho mới.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-37</td>
<td>FR-SALE-09</td>
<td>Món Chờ làm; đã xác nhận thực tế phù hợp.</td>
<td>1. Nhân viên chuyển sang Đã xác nhận xong.</td>
<td>Lưu đúng trạng thái mới; không trừ hoặc hoàn kho thêm.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI): Dòng Bò xào #1 Chờ làm: bấm 'Đã xác nhận xong' trên màn hình thanh toán → 'Đã chuyển sang Đã xác nhận xong.'; CSDL trạng thái mới; lô #1 vẫn 850 g, số giao dịch kho không đổi (3).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-38</td>
<td>FR-SALE-09</td>
<td>Món Đã xác nhận xong; đã xác nhận thực tế phù hợp.</td>
<td>1. Nhân viên chuyển sang Đã phục vụ.</td>
<td>Lưu đúng trạng thái mới; không trừ hoặc hoàn kho thêm.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI): Dòng #1 Đã xác nhận xong: bấm 'Đã phục vụ' → 'Đã chuyển sang Đã phục vụ.'; CSDL trạng thái Đã phục vụ; lô #1 vẫn 850 g, không phát sinh giao dịch kho.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-39</td>
<td>FR-SALE-09</td>
<td>Món Chờ làm.</td>
<td>1. Gọi API chuyển thẳng sang Đã phục vụ.</td>
<td>Từ chối chuyển bỏ qua bước; trạng thái giữ nguyên.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, API): Dòng Bò xào #1 đang Chờ làm: gọi PATCH /sales/orders/1/lines/1/status chuyển thẳng 'Đã phục vụ' → 422 'Không thể chuyển từ Chờ làm sang Đã phục vụ.'; trạng thái vẫn Chờ làm, lô #1 vẫn 850 g.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-40</td>
<td>FR-SALE-09</td>
<td>Món Đã phục vụ.</td>
<td>1. Thử chuyển về Chờ làm.</td>
<td>Từ chối chuyển ngược; trạng thái giữ nguyên.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI+API): Dòng #1 Đã phục vụ: giao diện không có thao tác chuyển ngược; gọi API chuyển về 'Chờ làm' → 422 'Không thể chuyển từ Đã phục vụ sang Chờ làm.'; trạng thái giữ Đã phục vụ.</td>
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
<td>04/11/2026 (bản 099191e, UI): B4 Trống, lượt chọn chưa gửi có 2 dòng giữ: bấm Hủy lượt chọn, xác nhận → 'Đã hủy lượt chọn và giải phóng nguyên liệu đang giữ.'; giỏ trống; lượt giữ #14, #15 'Đã giải phóng'; không có ORDER, phiếu bếp hay hóa đơn mới; B4 vẫn Trống; không có giao dịch kho ngoài phiếu nhập (tồn sổ sách không đổi).</td>
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
<td>03/11/2026 (bản 099191e, UI): Lượt chọn chưa gửi 2 suất (300 g): bấm trừ 1 suất → còn 1 suất, giữ 150 g, khả dụng 850 g (150 g được giải phóng ngay cho lượt khác), tồn 1.000 g; chưa có ORDER hay giao dịch tiêu hao.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-43</td>
<td>FR-SALE-12, FR-CAT-18</td>
<td>O1 ở B1; B2 Trống.</td>
<td>1. Đổi O1 sang B2.</td>
<td>Cùng transaction: B1 Trống/bỏ liên kết; B2 Đang phục vụ/gắn O1; có audit log.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI): O1 (ORD-031126-001) ở B01, B3 Trống: bấm Chuyển bàn, chọn B3 → 'Đã chuyển bàn.'; CSDL B01 Trống, MaOrderDangPhucVu NULL; B3 Đang phục vụ, gắn O1; ORDER.MaBan=B3; LICH_SU_DOI_BAN ghi B01→B3; nhật ký MOVE_ORDER_TABLE của người dùng #2. Ghi chú: LICH_SU_DOI_BAN.NguoiThucHien để NULL; audit không lưu dữ liệu trước/sau (bàn nguồn/đích).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-44</td>
<td>FR-SALE-12</td>
<td>O1 ở B1; B2 phục vụ O2.</td>
<td>1. Thử chuyển O1 sang B2.</td>
<td>Từ chối; cả hai bàn và order không đổi.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI+API): O1 ở B01, B2 đang phục vụ O2: hộp Chuyển bàn chỉ liệt kê bàn trống (B3), không có B2; gọi API chuyển O1 sang B2 → 422 'Bàn đích đang bận.'; trạng thái hai bàn và MaBan của O1/O2 không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-45</td>
<td>FR-SALE-12</td>
<td>Order cũ đã giải phóng bàn.</td>
<td>1. Thử đổi order cũ sang bàn Trống.</td>
<td>Từ chối; không gắn lại bàn.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI+API): O1 đã được giải phóng khỏi B3: trên màn hình thanh toán của O1 bấm Chuyển bàn, chọn B01 (Trống) → bị từ chối 'Order không còn gắn với bàn đang phục vụ.'; API cùng kết quả 422; B01 vẫn Trống, không gắn lại O1.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-46</td>
<td>FR-CAT-18</td>
<td>B1 phục vụ O1; còn lượt chọn gọi thêm chưa gửi.</td>
<td>1. Xác nhận khách rời B1.</td>
<td>B1 Trống/bỏ liên kết O1; kết thúc lượt chọn, giải phóng lượng giữ; có audit log.</td>
<td>Thường</td>
<td>03/11/2026 (bản 099191e, UI): B3 phục vụ O1, có phần gọi thêm chưa gửi (lượt giữ #6, 150 g): bấm Giải phóng bàn → B3 về Trống, MaOrderDangPhucVu NULL; lượt giữ #6 'Đã giải phóng'; O1 vẫn Đang mở, 2 dòng đã gửi và tiêu hao giữ nguyên (lô #1 550 g); nhật ký RELEASE_TABLE trước {MaOrderDangPhucVu:1}, sau {TrangThai:Trống}.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-47</td>
<td>FR-SALE-32</td>
<td>Máy in lỗi; lượt chọn hợp lệ.</td>
<td>1. Gửi món.</td>
<td>Order vẫn được commit, tồn trừ đúng; hiển thị lỗi in.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI): Dừng máy in thử (cổng 9109 không nghe), gửi 1 Bò xào mang về → order ORD-031126-031 commit, trừ kho bình thường; phiếu bếp #33 'Thất bại', 'Đã thử gửi 3 lần', 'Không kết nối được máy in.' hiển thị trên màn hình thanh toán (lỗi kết nối TCP thật, không dùng máy in vật lý).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-48</td>
<td>FR-SALE-32, FR-SALE-03</td>
<td>Order đã ghi nhận, in lần đầu lỗi.</td>
<td>1. In lại phiếu bếp hai lần.</td>
<td>In lại cùng nội dung; không tạo thêm order/dòng món hoặc trừ kho thêm.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Phiếu bếp #33 của ORD-031126-031 in lỗi lần đầu; bật lại máy in thử và bấm In lại hai lần → 'Đã gửi in lại phiếu bếp.'; bộ nhận TCP nhận 2 lần cùng dữ liệu ESC/POS (cùng SHA1 27a20ef61254, 'Bo xao x1 - 100000'); order vẫn 1 dòng, 1 giao dịch kho. (Lần bấm thứ hai trong cùng một lượt tự động không phát sinh yêu cầu, đã bấm lại; chưa kiểm tra giấy in thực.)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-49</td>
<td>FR-SALE-03, FR-CAT-18</td>
<td>Hai người chọn cùng B1 Trống; kho đủ cả hai.</td>
<td>1. Đồng thời gửi hai lượt chọn khác nhau.</td>
<td>Chỉ một order được gắn B1; yêu cầu còn lại bị từ chối, không tiêu hao cho lượt thất bại.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): B5 Trống; seed_cashier và seed_cashier2 mỗi người giữ 1 Bò xào cho B5 rồi gửi đồng thời: một yêu cầu 201 (ORD-031126-027 gắn B5), yêu cầu còn lại 422 'Bàn đang phục vụ. Hãy giải phóng bàn trước khi mở order mới.'; chỉ 1 order trên B5, chỉ phát sinh 1 giao dịch tiêu hao.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-50</td>
<td>FR-SALE-03, NFR-04</td>
<td>Đăng nhập Bếp; có dữ liệu gửi món hợp lệ.</td>
<td>1. Gọi API gửi món.</td>
<td>Backend từ chối; không tạo order hoặc tiêu hao.</td>
<td>Trọng yếu</td>
<td>03/11/2026 (bản 099191e, API): Bếp gọi POST /sales/holds và POST /sales/orders với dữ liệu gửi món hợp lệ: cả hai 403; số ORDER (2) và số giao dịch kho (5) không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-51</td>
<td>FR-INV-11, NFR-04</td>
<td>Người B không được phép thao tác lượt chọn của A.</td>
<td>1. B gửi yêu cầu sửa lượt chọn của A.</td>
<td>Từ chối truy cập; lượt chọn và lượng giữ của A không đổi.</td>
<td>Trọng yếu</td>
<td>03/11/2026 (bản 099191e, API): Thu ngân A (seed_cashier) giữ 1 suất Bò xào (lượt giữ #9). Người B (seed_cashier2) gọi PATCH/DELETE /sales/holds/9 và gửi order dùng hold_id=9 → 404 'Không tìm thấy lượt giữ chỗ.'; POST /holds/release theo mã lượt chọn của A → released 0. Lượt giữ của A vẫn 1 suất/150 g, Đang giữ.</td>
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
<td>04/11/2026 (bản 099191e, UI): Order #17 có QR SIM12 còn hạn: bấm Hủy QR → giao dịch #12 Đã hủy (audit CANCEL_QR_TRANSACTION); bấm Tạo mã QR → QR SIM13 Chờ xác nhận, còn hiệu lực 10 phút. Chỉ một QR còn hiệu lực; chưa có hóa đơn; order ở Chờ xác nhận thanh toán, không chuyển Chờ xác minh.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-53</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Chờ xác nhận thanh toán; kho đủ.</td>
<td>1. Thử thêm món và gửi phần gọi thêm.</td>
<td>Từ chối gọi thêm; không tạo dòng món, không giữ hoặc trừ thêm nguyên liệu; giữ nguyên trạng thái order.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Đơn mang về #17 Chờ xác nhận thanh toán: giữ món gọi thêm 422 'Order không còn mở.', thêm dòng 422 'Order đã đóng.'; số dòng (1) và trạng thái không đổi, không có lượt giữ.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-54</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Chờ xác minh thanh toán; kho đủ.</td>
<td>1. Thử thêm món và gửi phần gọi thêm.</td>
<td>Từ chối gọi thêm; không tạo dòng món, không giữ hoặc trừ thêm nguyên liệu; giữ nguyên trạng thái order.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Đơn mang về #21 Chờ xác minh thanh toán: giữ món và thêm dòng đều 422; số dòng 1, trạng thái giữ nguyên, không có lượt giữ.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-55</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Đã thanh toán; kho đủ.</td>
<td>1. Thử gọi thêm vào order đã thanh toán. 2. Tạo order mang về mới cho món khách mua thêm.</td>
<td>Order cũ từ chối gọi thêm, hóa đơn giữ nguyên; món mua thêm tạo order mới với mã riêng và trừ kho đúng một lần khi gửi.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Đơn mang về #7 Đã thanh toán: giữ/thêm món 422, vẫn 2 dòng và 1 hóa đơn; món mua thêm tạo order mang về mới #25 (mã ORD-031126-025) và trừ kho một lần khi gửi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-56</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Đã hủy; kho đủ.</td>
<td>1. Thử thêm món và gửi phần gọi thêm.</td>
<td>Từ chối gọi thêm; không tạo dòng món, không giữ hoặc trừ thêm nguyên liệu; giữ nguyên trạng thái order.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Đơn mang về #23 Đã hủy: giữ/thêm món 422; số dòng và trạng thái không đổi, không giữ hay trừ nguyên liệu.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-57</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Đóng – chưa thu được tiền; kho đủ.</td>
<td>1. Thử thêm món và gửi phần gọi thêm.</td>
<td>Từ chối gọi thêm; không tạo dòng món, không giữ hoặc trừ thêm nguyên liệu; giữ nguyên trạng thái order.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Đơn mang về #20 Đóng – chưa thu được tiền: giữ/thêm món 422; số dòng và trạng thái không đổi, không có lượt giữ.</td>
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
<td>04/11/2026 (bản 099191e, API): Đơn mang về #25 Đang mở (1 dòng đã gửi): tạo lượt gọi thêm Bò xào rồi hủy lượt chọn → chỉ lượt giữ đó 'Đã giải phóng', dòng đã gửi và tiêu hao (-150 g) giữ nguyên; chọn Ốc xào gọi thêm rồi gửi → 201, cùng order có thêm dòng #33 và phiếu bếp thứ 2, tiêu hao tăng đúng 150 g; không tạo order mới.</td>
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
<td>04/11/2026 (bản 099191e, API): Order tại chỗ #27 ở B5 Đang mở: giữ 1 Bò xào gọi thêm rồi gửi → 201; lượt giữ 'Đã gửi', thêm dòng #34 và phiếu bếp thứ 2, trừ thêm đúng 150 g; dòng cũ #31 giữ nguyên.</td>
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
<td>04/11/2026 (bản 099191e, UI): Như SALE-20: món gọi thêm vào đơn mang về đang mở được giữ (lượt giữ Đã gửi) và chuyển thành tiêu hao đúng một lần (-150 g lô #13), bổ sung dòng và phiếu bếp vào cùng order, không gắn bàn.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-61</td>
<td>FR-SALE-06, FR-INV-10</td>
<td>Lượt gọi thêm đã giữ món; trước lúc gửi, lô bị mất khả năng đáp ứng toàn bộ lượt gửi.</td>
<td>1. Gửi phần gọi thêm.</td>
<td>Từ chối toàn bộ lượt gửi, chỉ rõ dòng cần kiểm tra lại; không thêm dòng hoặc phiếu bếp, không trừ kho một phần.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, Script): Order 380 đang mở; giữ cho phần gọi thêm 2 dòng cùng lượt chọn: món 20 × 1 (giữ #1019) và món 29 × 2 (NL 47, giữ #1020). Lô NL 47 hạn 04/11/2026; gửi phần gọi thêm tại thời điểm mô phỏng 05/11/2026 07:00 (lô đã quá hạn, mất khả năng đáp ứng). Kết quả: từ chối toàn bộ lượt gửi; dòng order 1 → 1, phiếu bếp 1 → 1, giao dịch kho 526 → 526, tồn NL 47 và NL 32 không đổi (dòng món 20 còn đủ cũng không được thêm — không trừ một phần). Lệch: thông báo chỉ là 'Món đang hết nguyên liệu.', không chỉ rõ dòng/món nào cần kiểm tra lại.</td>
<td>Không đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-62</td>
<td>FR-SALE-06, FR-SALE-08</td>
<td>Order tại chỗ Đang mở đã có món; còn nhiều dòng gọi thêm đang giữ; bàn còn phục vụ đúng order.</td>
<td>1. Chọn Hủy lượt chọn gọi thêm.<br />
2. Kiểm tra món đã gửi, trạng thái order và bàn.</td>
<td>Giải phóng toàn bộ lượng giữ của phần gọi thêm chưa gửi; dòng đã gửi và tiêu hao gốc giữ nguyên; order tiếp tục Đang mở, bàn vẫn Đang phục vụ; không tạo phiếu bếp mới.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Order #27 tại B5 còn 2 lượt giữ gọi thêm chưa gửi (Bò xào, Ốc xào): hủy lượt chọn gọi thêm → released 2, cả hai 'Đã giải phóng'; 2 dòng đã gửi, 2 phiếu bếp và tiêu hao -300 g giữ nguyên; order Đang mở, B5 vẫn Đang phục vụ order #27.</td>
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
<td>04/11/2026 (bản 099191e, API): Order tại chỗ #29 ở B6: món đã gửi bị hủy (trừ -150 g rồi hoàn +150 g), chỉ còn lượt giữ gọi thêm #54 hạn 05:53:41. Sau mốc hết hạn theo giờ server: lô #3 Thịt bò SoLuongGiu 0 (khả dụng được giải phóng); order vẫn Đang mở, B6 vẫn phục vụ order; không có hóa đơn; không có giao dịch hoàn lặp (chỉ 1 Trừ + 1 Hoàn).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-64</td>
<td>FR-SALE-06, FR-SALE-11, FR-INV-04</td>
<td>Mọi món đã gửi bị hủy; order Đang mở; còn phần gọi thêm đang giữ và nguyên liệu vẫn đáp ứng.</td>
<td>1. Gửi phần gọi thêm còn hiệu lực.</td>
<td>Ghi món thay thế và phiếu bếp vào cùng order; chuyển lượng giữ thành tiêu hao đúng một lần; order tiếp tục Đang mở.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Order #4 tại B3 có mọi món đã gửi bị hủy (dòng #5 Đã hủy), order Đang mở: giữ và gửi 1 Bò xào gọi thêm → 201; cùng order có dòng thay thế #35 Chờ làm và phiếu bếp mới; tiêu hao đúng 150 g một lần; order tiếp tục Đang mở.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-65</td>
<td>FR-SALE-06, FR-SALE-08, FR-INV-10</td>
<td>Một lô còn 300 g, trong đó lượt khác đang giữ 200 g; món gọi thêm cần 150 g.</td>
<td>1. Thêm món cần 150 g vào lượt chọn gọi thêm.</td>
<td>Từ chối giữ do chỉ còn 100 g khả dụng; lượt giữ của người khác và tồn sổ sách không đổi; không thêm dòng món vào order.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Cua 300 g; seed_cashier2 giữ 1 Cua rang (200 g); thêm Cua hấp (150 g) vào lượt gọi thêm của order tại chỗ #27 → 422 'Món đang hết nguyên liệu.' (khả dụng 100 g); lượt giữ của người kia vẫn Đang giữ 1 suất, tồn 300 g không đổi, order không có dòng mới.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-66</td>
<td>FR-SALE-03, FR-SALE-06, FR-SALE-31</td>
<td>Một lượt gọi thêm qua giữ món đã gửi thành công và có mã yêu cầu duy nhất.</td>
<td>1. Gửi lại cùng yêu cầu với cùng mã và nội dung.</td>
<td>Trả kết quả đã ghi nhận; không tạo thêm dòng, phiếu bếp hoặc tiêu hao.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Gọi thêm 1 suất vào order #26 qua lines/bulk với request_line_id duy nhất → 201; gửi lại cùng mã và nội dung → 201 trả lại dòng #30 đã ghi; số dòng (2), phiếu bếp (2), giao dịch kho (62) không tăng.</td>
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
<td>04/11/2026 (bản 099191e, API): Lượt chọn sel-67 có dòng Vịt xào đã hết hạn (#46, 05:50:44; khả dụng Vịt vẫn 400 g, không tính phần hết hạn) và dòng Bò xào còn giữ (#58). Hủy lượt chọn → released 2, cả hai 'Đã giải phóng'; gửi lại yêu cầu hủy → released 0, khả dụng không tăng thêm; không có order, phiếu bếp hay giao dịch kho mới.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-68</td>
<td>FR-SALE-25; NFR-04</td>
<td>Tài khoản Quản lý; có order tại chỗ và mang về ở các trạng thái khác nhau.</td>
<td>1. Đăng nhập Quản lý. 2. Mở mục Quản lý đơn hàng.</td>
<td>Có mục điều hướng riêng; danh sách hiển thị mã, loại đơn, bàn nếu có, ngày kinh doanh, người lập, trạng thái và tổng tiền.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Quản lý có mục điều hướng riêng 'Quản lý đơn hàng' (/orders); danh sách 24 order có đủ cột Mã order, Loại đơn, Bàn (— với mang về), Ngày kinh doanh, Người lập, Trạng thái, Tổng tiền; có cả tại chỗ/mang về và các trạng thái Đang mở, Chờ xác nhận, Chờ xác minh, Đã thanh toán, Đóng – chưa thu, Đã hủy. Ghi chú: order Đã hủy hiển thị tổng 0 ₫ trong khi báo cáo order hủy ghi giá trị 200.000–300.000.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-69</td>
<td>FR-SALE-25</td>
<td>Có order khác mã, bàn, ngày kinh doanh và trạng thái.</td>
<td>1. Chọn kết hợp mã, bàn, khoảng ngày và trạng thái. 2. Xóa bộ lọc. 3. Lọc tiêu chí không có kết quả.</td>
<td>Chỉ trả order thỏa toàn bộ tiêu chí; xóa lọc khôi phục danh sách theo quyền; tập rỗng hiển thị thông báo, cho thay đổi bộ lọc.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI): Kết hợp Mã ORD-031126-027 + Bàn B5 + ngày 03/11–03/11 + Đang mở → đúng 1 order; mã không tồn tại → 'Không có order phù hợp', bộ lọc vẫn sửa được; Xóa bộ lọc → các ô trống, danh sách về 24 order. Ghi chú: ô Mã order chỉ khớp nguyên mã, gõ một phần '027' trả rỗng.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-70</td>
<td>FR-SALE-25</td>
<td>Quản lý truy cập danh sách; có order lịch sử đã có món, giao dịch và chứng từ.</td>
<td>1. Mở chi tiết order. 2. Đối chiếu món, tổng tiền, lịch sử thanh toán và chứng từ. 3. Quay lại danh sách.</td>
<td>Chi tiết đúng order đã chọn; xem dữ liệu không làm đổi trạng thái, tồn kho hoặc doanh thu; có đường quay lại danh sách.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Quản lý mở Xem ORD-031126-018 (đã qua QR → khách báo chuyển → Quản lý xác nhận nhận tiền): chi tiết hiện đúng món, tổng 80.000, phiếu bếp và hóa đơn HD-20261103-0007; có nút Quay lại danh sách; xem không làm đổi trạng thái/hóa đơn/giao dịch. Sai lệch: màn hình không hiển thị lịch sử thanh toán (giao dịch QR, mã FT-QA-18, yêu cầu xác minh, kết quả xử lý) – chỉ có dòng 'Phương thức: QR' trên hóa đơn; dữ liệu có trong API /payments.</td>
<td>Không đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-71</td>
<td>FR-SALE-25; NFR-04</td>
<td>Có tài khoản Quản lý và Bếp.</td>
<td>1. Quản lý mở danh sách và chi tiết. 2. Bếp thử truy cập trực tiếp màn hình và API quản lý đơn.</td>
<td>Quản lý truy cập được; Bếp không có mục điều hướng và bị từ chối ở cả giao diện và API, không lộ dữ liệu order.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI+API): Quản lý mở danh sách và chi tiết order được. Bếp: menu không có Quản lý đơn hàng; mở thẳng /orders bị chuyển về /inventory, không hiển thị mã order nào; API GET /sales/orders và /sales/orders/18 đều 403.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-72</td>
<td>FR-SALE-13, FR-SALE-21</td>
<td>Order đang mở có món hợp lệ; chưa có giao dịch thành công.</td>
<td>Thu ngân xác nhận đã nhận đủ tiền mặt.</td>
<td>Giao dịch tiền mặt thành công; order Đã thanh toán; có một hóa đơn.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Đơn ORD-031126-007 Đang mở, chưa có giao dịch: chọn Tiền mặt, Vừa đủ, bấm 'Xác nhận đã thu 120.000 ₫' → màn hình Đã thanh toán, hóa đơn HD-20261103-0001, tiền thối 0; CSDL ORDER Đã thanh toán (TongTien 120.000), 1 giao dịch tiền mặt Thành công, đúng 1 HOA_DON.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-73</td>
<td>FR-SALE-21</td>
<td>Order đang mở có món đã gửi; chưa thanh toán.</td>
<td>Yêu cầu phiếu tạm tính và kiểm tra bảng hóa đơn.</td>
<td>Có dữ liệu phiếu tạm tính; không tạo hóa đơn đã thanh toán.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Đơn ORD-031126-007 Đang mở có 2 dòng đã gửi: bấm In phiếu tạm tính → trả dữ liệu 'PHIẾU TẠM TÍNH - CHƯA THANH TOÁN', tổng 120.000 và các dòng; bảng HOA_DON vẫn 0 bản ghi, order vẫn Đang mở.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-74</td>
<td>FR-SALE-14</td>
<td>Cấu hình SePay thử nghiệm; order hợp lệ chưa thanh toán.</td>
<td>Tạo QR và đọc thông tin thanh toán trả về.</td>
<td>QR chứa thông tin VietQR, ngân hàng, tài khoản và số tiền của giao dịch.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Chế độ SePay thử nghiệm (tài khoản 0123456789 MBBank, webhook Apikey thử nghiệm). Tạo QR cho order #39 → payment_code TT19, ngân hàng MBBank, tài khoản 0123456789, tên NHA HANG QA, số tiền 110.000, ảnh VietQR https://qr.sepay.vn/img?acc=0123456789&amp;bank=MBBank&amp;amount=110000&amp;des=TT19; hạn 10 phút. Ghi chú: cột ThoiDiemTaoQR trong CSDL để NULL.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-75</td>
<td>FR-SALE-14</td>
<td>Order đã có QR còn hiệu lực.</td>
<td>Yêu cầu tạo QR thứ hai.</td>
<td>Từ chối tạo thêm QR khi giao dịch trước còn hiệu lực.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Order #14 đã có QR #8 còn hiệu lực (Chờ xác nhận, hạn 05:43:12): yêu cầu tạo QR thứ hai → 422; chỉ có 1 giao dịch QR. Ghi chú: thông báo trả về 'Order đã đóng.' không đúng tình trạng (order đang Chờ xác nhận thanh toán).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-76</td>
<td>FR-SALE-15</td>
<td>Order có QR còn hiệu lực; webhook SePay dùng khóa thử nghiệm hợp lệ.</td>
<td>Gửi thông báo tiền vào đúng mã và đủ số tiền.</td>
<td>Order Đã thanh toán; phát hành một hóa đơn.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Chế độ SePay thử nghiệm (tài khoản 0123456789 MBBank, webhook Apikey thử nghiệm). Webhook tiền vào đúng mã TT19 và đủ 110.000 → 200; order Đã thanh toán, giao dịch Thành công, đúng 1 hóa đơn.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-77</td>
<td>FR-SALE-15, NFR-04</td>
<td>Order có QR; webhook dùng API key sai.</td>
<td>Gửi thông báo tiền vào với API key sai.</td>
<td>Webhook bị từ chối; giao dịch không được xác nhận.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Chế độ SePay thử nghiệm (tài khoản 0123456789 MBBank, webhook Apikey thử nghiệm). Webhook TT19 với API key sai → 401 'API key không hợp lệ.'; giao dịch vẫn Chờ xác nhận, chưa có hóa đơn.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-78</td>
<td>FR-SALE-15, NFR-07</td>
<td>Webhook thanh toán đúng đã được xử lý.</td>
<td>Gửi lại cùng mã giao dịch ngân hàng.</td>
<td>Không thu tiền hoặc phát hành hóa đơn lần hai.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Chế độ SePay thử nghiệm (tài khoản 0123456789 MBBank, webhook Apikey thử nghiệm). Gửi lại webhook cùng mã giao dịch ngân hàng đã xử lý → 200 (bỏ qua trùng); vẫn 1 hóa đơn, không ngoại lệ mới.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-79</td>
<td>FR-SALE-16, FR-SALE-19</td>
<td>Order có QR; webhook hợp lệ nhưng sai số tiền.</td>
<td>Gửi webhook tiền vào sai số tiền.</td>
<td>Chuyển sang xử lý xác minh/ngoại lệ; không coi khoản sai là thanh toán đủ.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Chế độ SePay thử nghiệm (tài khoản 0123456789 MBBank, webhook Apikey thử nghiệm). Webhook đúng mã TT20 nhưng 1.000 đ → ghi ngoại lệ thanh toán #1 'Chờ xử lý' 1.000; order #40 vẫn Chờ xác nhận thanh toán, không hóa đơn.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-80</td>
<td>FR-SALE-18</td>
<td>QR được tạo ở thời điểm server xác định.</td>
<td>Đọc thời hạn QR trả về.</td>
<td>Hạn QR là 10 phút kể từ thời điểm tạo.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): QR #8 tạo lúc 05:33:12.199 có ThoiDiemHetHan 05:43:12.199 – đúng 10 phút kể từ thời điểm tạo theo giờ server.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-81</td>
<td>FR-SALE-18, FR-SALE-15</td>
<td>QR đã hết hạn; API ngân hàng giả lập có giao dịch phù hợp.</td>
<td>Chọn Kiểm tra lại và đối chiếu kết quả.</td>
<td>Hệ thống vẫn đối chiếu giao dịch ngân hàng sau hạn QR và ghi nhận khoản phù hợp.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Chế độ SePay thử nghiệm: QR #20 (order #40) đã Hết hạn lúc 07:53:46; API ngân hàng giả lập có khoản TT20 đúng 110.000. Gọi 'Kiểm tra lại' (POST /payments/20/check) → giao dịch Thành công, order Đã thanh toán, 1 hóa đơn.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-82</td>
<td>FR-SALE-19, FR-SALE-22</td>
<td>Order có QR chưa thành công; Thu ngân đăng nhập.</td>
<td>Yêu cầu xác minh; thử thêm món vào order.</td>
<td>Order Chờ xác minh thanh toán; yêu cầu thêm món bị từ chối.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI+API): Order #17 có QR chưa thành công: Thu ngân bấm 'Khách báo đã chuyển tiền', gửi yêu cầu → order và giao dịch #13 'Chờ xác minh thanh toán'; giao diện báo không thể thêm món/thu tiền mặt; API thêm món 422 'Order đã đóng.', giữ món gọi thêm 422 'Order không còn mở.'.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-83</td>
<td>FR-SALE-19, FR-SALE-34</td>
<td>Giao dịch QR chưa xác nhận; có mã tham chiếu, bằng chứng và ghi chú.</td>
<td>Gửi yêu cầu xác minh kèm thông tin.</td>
<td>Giữ mã tham chiếu, bằng chứng và ghi chú để đối chiếu.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Yêu cầu xác minh kèm mã FT26110400017, ảnh chứng từ PNG và ghi chú 'Khách gửi lúc 05:38…': giao dịch lưu MaGiaoDichNganHang và AnhChungTu (giao diện có 'Xem ảnh xác nhận'); ghi chú lưu trong nhật ký REQUEST_PAYMENT_VERIFICATION cùng mã và ảnh.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-84</td>
<td>FR-SALE-20</td>
<td>Order Chờ xác minh; Quản lý đã xác nhận bên ngoài nhận đủ 50.000 đồng.</td>
<td>Quản lý ghi nhận kết quả đã nhận đủ tiền.</td>
<td>Giao dịch Thành công, order Đã thanh toán và có một hóa đơn.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Order #18 Chờ xác minh: Quản lý bấm 'Xác nhận đã nhận tiền', nhập số tiền thực nhận 80.000 (hộp nhập của trình duyệt) → màn hình Đã thanh toán, hóa đơn HD-20261103-0007; CSDL giao dịch Thành công, order Đã thanh toán, đúng 1 hóa đơn, audit RESOLVE_RECONCILIATION. (Đơn thử dùng giá 80.000 thay cho 50.000 trong ca.)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-85</td>
<td>FR-SALE-23, NFR-04</td>
<td>Order Chờ xác minh; có tài khoản Thu ngân và Quản lý.</td>
<td>Thu ngân thử mở lại; Quản lý mở lại với lý do; tạo QR mới.</td>
<td>Thu ngân bị từ chối; Quản lý mở lại được; giao dịch cũ Đã hủy, order Đang mở và cho phép QR mới.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI+API): Order #17 Chờ xác minh: màn hình Thu ngân không có nút Mở lại; Thu ngân gọi API reopen → 403. Quản lý bấm Mở lại thanh toán, nhập lý do và kết quả xử lý bên ngoài → order Đang mở, giao dịch #13 Đã hủy và vẫn giữ mã FT26110400017; audit REOPEN_PAYMENT có lý do; tạo QR mới #17 thành công.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-86</td>
<td>FR-SALE-35</td>
<td>Order Chờ xác minh chưa có tiền thành công; Quản lý quyết định ngừng thu.</td>
<td>Quản lý đóng chưa thu được tiền.</td>
<td>Order ở trạng thái kết thúc Đóng – chưa thu được tiền; không phát hành hóa đơn.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Order #20 Chờ xác minh, chưa có tiền thành công: Quản lý bấm Đóng chưa thu, nhập lý do/kết quả → CSDL order và giao dịch 'Đóng – chưa thu được tiền', ThoiDiemDong ghi nhận; không phát hành hóa đơn. Ghi chú: ngay sau khi lưu, tiêu đề màn hình còn hiện 'Chờ xác minh thanh toán' tới lần làm mới kế tiếp.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-87</td>
<td>FR-SALE-17</td>
<td>Order đã đóng chưa thu; có khoản tiền đến muộn được ghi thành ngoại lệ.</td>
<td>Quản lý áp dụng khoản ngoại lệ hợp lệ; thử áp dụng lại.</td>
<td>Chỉ áp dụng một lần và phát hành một hóa đơn.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Order #20 Đóng – chưa thu được tiền; khoản 100.000 đến muộn qua webhook → ngoại lệ #3 Chờ xử lý; Quản lý áp dụng → Đã áp dụng, order Đã thanh toán, 1 hóa đơn; áp dụng lại → 422 'Khoản ngoại lệ đã được xử lý.'.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-88</td>
<td>FR-SALE-16, FR-SALE-17</td>
<td>Order đã được thanh toán; phát sinh khoản thu trùng.</td>
<td>Thử áp dụng khoản trùng rồi ghi nhận hoàn tiền.</td>
<td>Khoản trùng không được áp dụng lại; đi qua xử lý hoàn tiền.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Order #39 đã thanh toán nhận thêm khoản 110.000 mới → ngoại lệ #2; Quản lý áp dụng → 422 'Order đã có thanh toán/hóa đơn, chỉ có thể hoàn tiền.'; vẫn 1 hóa đơn; xử lý tiếp bằng hoàn tiền.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-89</td>
<td>FR-SALE-17</td>
<td>Có ngoại lệ cần hoàn tiền.</td>
<td>Gửi kết quả hoàn thiếu mã tham chiếu; gửi lại đủ mã và số tiền.</td>
<td>Thiếu mã bị từ chối; kết quả hợp lệ lưu mã tham chiếu và số tiền hoàn.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Ngoại lệ #2: ghi hoàn thiếu mã tham chiếu → 422 'Cần nhập mã tham chiếu hoàn tiền của ngân hàng.'; ghi hoàn có mã RF-3 và số tiền → lưu MaThamChieuHoan RF-3, SoTienHoan 110.000, trạng thái Đã hoàn tiền. Ghi chú: lần hoàn một phần trước (RF-2) bị ghi đè mã tham chiếu, chỉ còn mã cuối.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-90</td>
<td>FR-SALE-17</td>
<td>Ngoại lệ có số tiền đã nhận xác định.</td>
<td>Thử ghi số tiền hoàn lớn hơn số nhận.</td>
<td>Từ chối số tiền hoàn vượt số tiền đã nhận.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Ngoại lệ #2 nhận 110.000: ghi hoàn 110.001 → 422 'Số tiền hoàn phải lớn hơn 0 và không vượt số còn lại.'; ngoại lệ giữ nguyên.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-91</td>
<td>FR-SALE-17</td>
<td>Ngoại lệ chưa xử lý hết.</td>
<td>Ghi nhận hoàn một phần số tiền.</td>
<td>Ngoại lệ tiếp tục mở cho số tiền còn lại.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Ghi hoàn một phần 55.000 (RF-2) cho ngoại lệ #2 → vẫn 'Chờ xử lý', SoTienHoan 55.000, còn lại 55.000 tiếp tục mở.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-92</td>
<td>FR-SALE-16, FR-SALE-17</td>
<td>Order đã trả tiền mặt; QR cũ nhận tiền sau đó.</td>
<td>Gửi thông báo khoản QR đến muộn.</td>
<td>Order giữ Đã thanh toán; không phát hành thêm hóa đơn cho cùng order.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Order #16 có QR #10; Thu ngân hủy QR rồi thu tiền mặt → Đã thanh toán, 1 hóa đơn. Gửi webhook đúng số tiền cho QR cũ (đến muộn) → 422 'Giao dịch không ở trạng thái chờ.'; order giữ Đã thanh toán, vẫn 1 hóa đơn. Ghi chú: ở chế độ simulator khoản đến muộn bị từ chối, không ghi thành ngoại lệ để hoàn tiền.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-93</td>
<td>FR-SALE-15</td>
<td>Chế độ simulator; order có QR; payload có chữ ký nhưng thiếu số tiền.</td>
<td>Gửi webhook thiếu amount.</td>
<td>HTTP 422; order vẫn Chờ xác nhận thanh toán.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Chế độ simulator, order #14 có QR #8: gửi webhook có chữ ký nhưng thiếu amount → 422 'Thiếu số tiền.'; order vẫn 'Chờ xác nhận thanh toán', giao dịch vẫn Chờ xác nhận, chưa có hóa đơn.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-94</td>
<td>FR-SALE-15</td>
<td>API ngân hàng giả lập trả 151 giao dịch theo thứ tự giảm dần, có phân trang.</td>
<td>Chạy tác vụ đồng bộ giao dịch.</td>
<td>Đọc đủ các trang, không mất giao dịch cũ nhất.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, Script): API ngân hàng giả lập trả 151 giao dịch, mới nhất trước; giao dịch cũ nhất (id 700000) là khoản TT22 khớp QR đang chờ. Chạy tác vụ sync_recent_transfers: đọc đủ 151 dòng, xác nhận 1 khoản, order #42 Đã thanh toán với 1 hóa đơn; mốc đồng bộ MocDongBoSepay = 700150. Ghi chú: hệ thống gọi một lần với limit 5000 và since_id thay vì lật trang, nên giả lập trả cả 151 dòng trong một trang.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-95</td>
<td>FR-SALE-15</td>
<td>API ngân hàng giả lập trả danh sách bị cắt, không bảo đảm đọc đủ.</td>
<td>Chạy đồng bộ với danh sách không đầy đủ.</td>
<td>Báo lỗi thay vì bỏ qua các khoản tiền cũ chưa đọc.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, Script): API giả lập trả đúng 5.000 dòng (bằng giới hạn, không bảo đảm đủ): tác vụ báo lỗi 'Danh sách SePay đạt 5.000 giao dịch; chưa tiến mốc đồng bộ. Cần đối soát…'; MocDongBoSepay giữ 700150, không bỏ qua khoản cũ.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-96</td>
<td>FR-SALE-24, FR-SALE-27, FR-SALE-28, FR-SALE-30, FR-INV-04</td>
<td>Quản lý. Order tại chỗ Đang mở, chưa thanh toán, bàn B1 Đang phục vụ. Bò xào 3 suất: 2 suất Chờ làm, 1 suất Đã xác nhận xong; đã xuất 450 g từ lô L1.</td>
<td>1. Chọn Hủy toàn bộ order. 2. Nhập lý do. 3. Xác nhận. 4. Đối chiếu order, kho, hóa đơn, bàn, báo cáo.</td>
<td>Order Đã hủy trong cùng một giao dịch. Hoàn đúng 300 g vào L1; 150 g của suất đã xong giữ nguyên tiêu hao và ghi vào hao hụt do hủy order. Không phát sinh hóa đơn. Bàn chưa giải phóng vì khách chưa rời. Có audit log và mốc thời gian chi tiết. Order xuất hiện ở giá trị order bị hủy.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Order tại chỗ #22 ở B4 Đang mở: 2 suất Bò xào Chờ làm (đã trừ 250 g lô #1 + 50 g lô #3 vì lô #1 chỉ còn 250 g) và 1 suất Đã xác nhận xong (150 g). Quản lý nhập lý do, bấm Hủy toàn bộ order → order Đã hủy; hoàn +250 g lô #1, +50 g lô #3; suất đã xong giữ tiêu hao; không có hóa đơn; B4 vẫn Đang phục vụ (khách chưa rời); audit CANCEL_ORDER có lý do; báo cáo order hủy có ORD-031126-022 giá trị 300.000, giá vốn 30.000. Ghi chú: giao diện không báo thành công và tiêu đề vẫn 'Đang mở' tới lần làm mới; ORDER.ThoiDiemDong để NULL.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-97</td>
<td>FR-SALE-28, FR-SALE-30, FR-INV-04</td>
<td>Quản lý. Order mang về Đang mở; toàn bộ món Chờ làm. Có thêm một lượt chọn gọi thêm chưa gửi đang giữ nguyên liệu.</td>
<td>1. Hủy toàn bộ order kèm lý do. 2. Kiểm tra kho và lượng giữ.</td>
<td>Hoàn toàn bộ nguyên liệu các món Chờ làm về đúng lô gốc. Lượt chọn chưa gửi kết thúc và giải phóng lượng giữ. Không có tiêu hao hay hao hụt phát sinh. Bàn không bị ảnh hưởng.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Đơn mang về #23 Đang mở, 2 suất Chờ làm (trừ 250 g lô #1 + 50 g lô #3) và 1 lượt giữ gọi thêm chưa gửi (#35): Quản lý hủy toàn bộ kèm lý do → Đã hủy; hoàn +250 g lô #1, +50 g lô #3 về đúng lô gốc; lượt giữ #35 'Đã giải phóng'; không có tiêu hao còn lại; không liên quan bàn.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-98</td>
<td>FR-SALE-29, FR-SALE-27</td>
<td>Thu ngân hoặc Quản lý. Order Đang mở, đã tạo mã QR, đang Chờ xác nhận thanh toán.</td>
<td>1. Thử hủy toàn bộ order. 2. Hủy mã QR. 3. Hủy toàn bộ order lại.</td>
<td>Bước 1 bị từ chối, order và kho không đổi. Sau khi hủy QR (hoặc QR hết hạn), bước 3 được chấp nhận.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Order #24 đã tạo QR #18 (Chờ xác nhận thanh toán): Quản lý hủy toàn bộ → 422, order và kho không đổi; Thu ngân hủy QR → Đã hủy; hủy toàn bộ lần nữa → Đã hủy. Ghi chú: thông báo từ chối là 'Order đã đóng.' thay vì nêu QR đang chờ.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-99</td>
<td>FR-SALE-27</td>
<td>Quản lý. Chuẩn bị hai order: (a) Chờ xác minh thanh toán, (b) Đã thanh toán.</td>
<td>1. Thử hủy toàn bộ từng order.</td>
<td>Cả hai bị từ chối với thông báo lý do. Không đổi trạng thái, kho, hóa đơn hay doanh thu.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Quản lý hủy toàn bộ order #21 (Chờ xác minh thanh toán) và #18 (Đã thanh toán): cả hai 422; trạng thái, hóa đơn (#18 vẫn 1 hóa đơn), kho không đổi. Ghi chú: cả hai trả cùng thông báo 'Order đã đóng.', chưa phân biệt lý do theo trạng thái.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-100</td>
<td>FR-SALE-27, NFR-04</td>
<td>Tài khoản Thu ngân và tài khoản Quản lý; order Đang mở hợp lệ.</td>
<td>1. Thu ngân thử hủy toàn bộ (giao diện và gọi API trực tiếp). 2. Quản lý hủy nhưng để trống lý do. 3. Quản lý nhập lý do và hủy.</td>
<td>Thu ngân bị từ chối ở cả giao diện và API. Bước 2 bị từ chối vì thiếu lý do. Bước 3 thành công.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI+API): Order #22 Đang mở: màn hình Thu ngân không có nút Hủy toàn bộ order, Thu ngân gọi API hủy → 403; Quản lý để trống lý do → nút bị vô hiệu, API trả 422 'Cần lý do hủy order.'; Quản lý nhập lý do và hủy → thành công.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-101</td>
<td>FR-SALE-26</td>
<td>Order đã thanh toán, đã có hóa đơn chốt; tài khoản Thu ngân và Quản lý.</td>
<td>1. Mở hóa đơn đã chốt và chọn in lại hai lần. 2. Đối chiếu nội dung với hóa đơn gốc. 3. Thử chỉnh sửa nội dung khi in lại.</td>
<td>Nội dung in lại đúng nguyên nội dung hóa đơn gốc; không cho chỉnh sửa; không tạo thêm hóa đơn hoặc giao dịch, không đổi doanh thu.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI+API): Hóa đơn HD-20261103-0001 (order #7) đã chốt: Thu ngân bấm In lại 2 lần → 2 lệnh in, nội dung trên màn hình giữ nguyên (2 × Ốc xào 60.000, tổng 120.000), không có ô nào chỉnh sửa; Quản lý gọi reprint kèm dữ liệu sửa tổng tiền → vẫn trả nội dung gốc. CSDL: vẫn 1 hóa đơn, TongTien 120.000, SoLanIn tăng 1→4, 1 giao dịch thanh toán, doanh thu không đổi.</td>
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
<td>03/11/2026 (bản 099191e, UI): Bếp tạo phiếu nhập #1 (NCC A, Thịt bò 1.000 g × 200 đ/g, ngày nhập 03/11/2026): báo 'Đã tạo phiếu nhập.'; tab Lô hiển thị lô #1 còn 1.000 g, hạn dùng 08/11/2026 (5 ngày bảo quản), Còn hạn; tồn sổ sách và khả dụng 1.000 g; sổ kho có 1 giao dịch Nhập +1.000 g tham chiếu lô #1 và dòng nhập #1. Ghi chú: giao dịch nhập ghi BusinessDate 02/11/2026 vì giao diện gửi ngày nhập lúc 00:00 (trước mốc 06:00) – xem phần nhập lùi ngày.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-02</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô chưa có xuất hoặc giữ hiệu lực.</td>
<td>1. Bếp sửa phiếu thành 1.200 g.</td>
<td>Cho phép; tồn và lô cập nhật đúng 1.200 g; có audit log.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Phiếu nhập 1.000 g Nấm, lô chưa xuất/giữ: Bếp sửa thành 1.200 g → 200; lô #28 và tồn 1.200 g; có nhật ký UPDATE_RECEIPT. Ghi chú: bản ghi nhật ký không lưu dữ liệu trước/sau.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-03</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô đã có xuất.</td>
<td>1. Bếp sửa phiếu thành 1.200 g.</td>
<td>Từ chối; phiếu, lô và tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Phiếu nhập 1.000 g có lô đã xuất 100 g: sửa thành 1.200 g → 422 'Phiếu nhập đã phát sinh xuất kho, phải điều chỉnh qua kiểm kê…'; phiếu, lô (900 g) và tồn không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-04</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô đang có giữ hiệu lực.</td>
<td>1. Bếp sửa phiếu thành 1.200 g.</td>
<td>Từ chối; phiếu, lô và tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Phiếu 1.200 g có lô đang được giữ 100 g: sửa → 422 'Lô của phiếu đang được giữ chỗ, không thể sửa/hủy phiếu.'; phiếu, lô, tồn không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-05</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô chưa có xuất hoặc giữ hiệu lực.</td>
<td>1. Bếp hủy phiếu.</td>
<td>Cho phép; tồn và lô cập nhật đúng lượng bị hủy; có audit log.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI+API): Phiếu nhập #35 (Nấm 1.000 g, lô chưa xuất/giữ): Bếp bấm Hủy phiếu và xác nhận → giao diện báo 'Không thực hiện được. Kiểm tra kết nối rồi thử lại.', phiếu vẫn Hiệu lực, lô và tồn không đổi. API DELETE /inventory/receipts trả HTTP 500 (MySQL 3819: vi phạm ràng buộc ck_GIAO_DICH_KHO_movement_source_matches_kind khi ghi giao dịch đảo nhập). Tái hiện 2 lần (phiếu #30 và #35).</td>
<td>Không đạt</td>
</tr>
<tr class="even">
<td>TC-INV-06</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô đã có xuất.</td>
<td>1. Bếp hủy phiếu.</td>
<td>Từ chối; phiếu, lô và tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Phiếu có lô đã xuất: hủy → 422 'Phiếu nhập đã phát sinh xuất kho…'; phiếu Hiệu lực, lô không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-07</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô đang có giữ hiệu lực.</td>
<td>1. Bếp hủy phiếu.</td>
<td>Từ chối; phiếu, lô và tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Phiếu có lô đang giữ 100 g: hủy → 422 'Lô của phiếu đang được giữ chỗ…'; phiếu vẫn Hiệu lực, tồn không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-08</td>
<td>FR-INV-10</td>
<td>Lô A còn hạn 600 g; B hết hạn 400 g; giữ hiệu lực 200 g trên A, giữ hết hạn 100 g.</td>
<td>1. Tra cứu trước khi tác vụ dọn giữ chạy.</td>
<td>Sổ sách 1.000 g; đủ điều kiện bán 600 g; khả dụng 400 g; không tính giữ hết hạn.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, Script+API): NL 45 (bảo quản 30 ngày): lô B #87 nhập lùi ngày 01/09/2026 400 g, hạn 01/10/2026 → 'Hết hạn'; lô A #88 nhập 04/11/2026 600 g 'Còn hạn'. Giữ hiệu lực #1013 (2 suất × 100 g = 200 g) và giữ đã quá hạn #1012 (100 g, hết hạn 11:20:47, vẫn 'Đang giữ' vì tác vụ dọn chưa chạy). Tra cứu tồn kho (GET /inventory/stock, nguồn của màn Kho) ngay lúc đó: Sổ sách 1.000 g, Đủ điều kiện bán 600 g, Giữ 200 g, Khả dụng 400 g, 1 lô hết hạn — không tính giữ đã quá hạn 100 g.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-09</td>
<td>FR-INV-10, FR-INV-13</td>
<td>Lô còn hạn 150 g; một dòng giữ đủ 150 g còn hiệu lực; khả dụng chung 0.</td>
<td>1. Gửi chính dòng đang giữ.</td>
<td>Gửi được; tiêu hao 150 g đúng lô; kết thúc giữ, không tự từ chối do khả dụng chung bằng 0.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Chạy lại trên 099191e: lô Tôm còn hạn 150 g, chính lượt giữ #10 đủ 150 g còn hiệu lực, khả dụng chung 0. Bấm Gửi bếp: bị từ chối 'Món đang hết nguyên liệu.' (API POST /sales/orders 422); không tạo order, lô vẫn 150 g, lượt giữ vẫn Đang giữ. Kỳ vọng: gửi được, tiêu hao 150 g đúng lô, kết thúc giữ.</td>
<td>Không đạt</td>
</tr>
<tr class="even">
<td>TC-INV-10</td>
<td>FR-INV-03, FR-INV-13</td>
<td>Lô hết hạn nhập sớm còn 300 g; lô còn hạn 700 g.</td>
<td>1. Gửi 1 suất cần 150 g.</td>
<td>Trừ 150 g từ lô còn hạn; lô hết hạn giữ nguyên trong tồn sổ sách.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, UI): Ốc: lô #12 nhập 20/10 hết hạn 25/10 còn 300 g, lô #13 còn hạn 700 g. Gửi 1 suất Ốc xào (150 g): sổ kho chỉ trừ lô #13 (-150 g, còn 550 g); lô hết hạn #12 giữ nguyên 300 g trong tồn sổ sách.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-11</td>
<td>FR-INV-14, FR-SET-04</td>
<td>Ngưỡng 3 ngày; lô còn hàng; hạn dùng cách ngày tham chiếu 2 ngày.</td>
<td>1. Mở màn hình kho.</td>
<td>Trạng thái Sắp hết hạn; cảnh báo hạn dùng tách khỏi cảnh báo tồn.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI+API): Ngày tham chiếu 04/11/2026, ngưỡng cảnh báo hạn 3 ngày; Bếp mở màn hình Kho → Tồn kho. Rau hạn 2 ngày (lô hạn 06/11): cột chi tiết '1 lô sắp hết hạn', lô ở trạng thái Sắp hết hạn; cảnh báo hạn tách riêng với trạng thái tồn.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-12</td>
<td>FR-INV-14, FR-SET-04</td>
<td>Ngưỡng 3 ngày; lô còn hàng; hạn dùng cách ngày tham chiếu 3 ngày.</td>
<td>1. Mở màn hình kho.</td>
<td>Trạng thái Sắp hết hạn; cảnh báo hạn dùng tách khỏi cảnh báo tồn.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI+API): Ngày tham chiếu 04/11/2026, ngưỡng cảnh báo hạn 3 ngày; Bếp mở màn hình Kho → Tồn kho. Rau hạn 3 ngày (lô hạn 07/11): '1 lô sắp hết hạn', lô Sắp hết hạn.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-13</td>
<td>FR-INV-14, FR-SET-04</td>
<td>Ngưỡng 3 ngày; lô còn hàng; hạn dùng cách ngày tham chiếu 4 ngày.</td>
<td>1. Mở màn hình kho.</td>
<td>Trạng thái Còn hạn; cảnh báo hạn dùng tách khỏi cảnh báo tồn.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI+API): Ngày tham chiếu 04/11/2026, ngưỡng cảnh báo hạn 3 ngày; Bếp mở màn hình Kho → Tồn kho. Rau hạn 4 ngày (lô hạn 08/11): không có cảnh báo hạn, lô Còn hạn.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-14</td>
<td>FR-INV-14, FR-SET-04</td>
<td>Ngưỡng 3 ngày; lô còn hàng; hạn dùng cách ngày tham chiếu -1 ngày.</td>
<td>1. Mở màn hình kho.</td>
<td>Trạng thái Hết hạn; cảnh báo hạn dùng tách khỏi cảnh báo tồn.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI+API): Ngày tham chiếu 04/11/2026, ngưỡng cảnh báo hạn 3 ngày; Bếp mở màn hình Kho → Tồn kho. Rau quá hạn (lô hạn 03/11): '1 lô hết hạn', lô Hết hạn; đủ điều kiện bán 0 trong khi tồn sổ sách 100.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-15</td>
<td>FR-INV-07</td>
<td>Ngưỡng riêng 500 g; khả dụng 499 g.</td>
<td>1. Xem cảnh báo tồn.</td>
<td>Có cảnh báo tồn tối thiểu.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI+API): Đường ngưỡng riêng 500, khả dụng 499: trạng thái 'Sắp hết' (CanhBaoTonThap=true).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-16</td>
<td>FR-INV-07</td>
<td>Ngưỡng riêng 500 g; khả dụng 500 g.</td>
<td>1. Xem cảnh báo tồn.</td>
<td>Không cảnh báo tồn tối thiểu.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, API): Nhập thêm 1 g Đường → khả dụng 500, ngưỡng 500: CanhBaoTonThap=false.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-17</td>
<td>FR-INV-07</td>
<td>Ngưỡng riêng 500 g; khả dụng 501 g.</td>
<td>1. Xem cảnh báo tồn.</td>
<td>Không cảnh báo tồn tối thiểu.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, API): Nhập thêm 1 g → khả dụng 501, ngưỡng 500: CanhBaoTonThap=false.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-18</td>
<td>FR-INV-07, FR-SET-05</td>
<td>Không có ngưỡng riêng; mặc định 300 g; khả dụng 299 g.</td>
<td>1. Xem cảnh báo tồn.</td>
<td>Áp dụng ngưỡng 300 g, hiển thị cảnh báo.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI+API): Bột ngọt không đặt ngưỡng riêng, ngưỡng mặc định 300, khả dụng 299: mức tối thiểu hiển thị 300, trạng thái 'Sắp hết'.</td>
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
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="even">
<td>TC-INV-20</td>
<td>FR-INV-06</td>
<td>Lô được chọn còn 100 g.</td>
<td>1. Yêu cầu xuất hủy 101 g.</td>
<td>Từ chối; không có giao dịch xuất, tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Lô còn 100 g: yêu cầu xuất hủy 101 g → 422 'Không đủ tồn kho khả dụng.'; không có giao dịch mới, lô giữ 100 g.</td>
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
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="even">
<td>TC-INV-22</td>
<td>FR-INV-06, FR-INV-11</td>
<td>Phần hỏng thuộc lô đang giữ cho một dòng món.</td>
<td>1. Xuất hủy phần hỏng.<br />
2. Kiểm tra bản xem trước và xác nhận.</td>
<td>Bản xem trước nêu lượt giữ bị ảnh hưởng; sau khi xác nhận, trong transaction: giải phóng toàn bộ lượng giữ của dòng bị ảnh hưởng, xuất đúng lượng hỏng; thông báo nhân viên kiểm tra lại.</td>
<td>Trọng yếu</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
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
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="even">
<td>TC-INV-24</td>
<td>FR-INV-06</td>
<td>Dòng 2 suất đã ghi xuất hủy món 1 suất.</td>
<td>1. Yêu cầu xuất hủy thêm 2 suất.</td>
<td>Từ chối vì chỉ còn 1 suất chưa ghi nhận; không tạo thêm chứng từ hay giao dịch kho.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Dòng 2 suất đã ghi xuất hủy 1 suất: yêu cầu thêm 2 suất → 422 'Số suất hủy vượt quá số suất đã tiêu hao chưa ghi nhận.'; không tạo thêm chứng từ.</td>
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
<td>04/11/2026 (bản 099191e, Script): Sò 150 g, món cần 150 g; 100 vòng hai Thu ngân phát đồng thời yêu cầu giữ cùng món: mỗi vòng đúng 1 yêu cầu 201 và 1 yêu cầu 422; tổng giữ tối đa 150 g; tồn 150 g không âm.</td>
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
<td>04/11/2026 (bản 099191e, Script): Hai món khác nhau (Sò nướng, Sò hấp) cùng cần 150 g Sò, khả dụng 150 g; 100 vòng giữ đồng thời: mỗi vòng đúng 1 thành công, 1 bị từ chối thiếu nguyên liệu; không cấp trùng, không khóa chết.</td>
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
<td>04/11/2026 (bản 099191e, Script): Script gọi tầng service trên MySQL QA, đặt giờ server đúng bằng ThoiDiemHetHan đã lưu của lượt giữ (at_time), khả dụng đủ 150 g: 100/100 lượt gửi (có xác nhận dùng giá/định lượng hiện tại) thành công, mỗi lượt tiêu hao đúng 150 g một lần (100 dòng, mỗi dòng 1 giao dịch -150 g).</td>
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
<td>04/11/2026 (bản 099191e, Script): Mỗi lượt: A giữ 150 g Sò (tồn 250 g); tại đúng mốc hết hạn của A, B giữ 150 g (còn 100 g) rồi A gửi → 100/100 lượt bị từ chối 'Món đang hết nguyên liệu.', không tạo ORDER hay giao dịch kho; lượt chọn của A còn nguyên.</td>
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
<td>04/11/2026 (bản 099191e, Script): 100 vòng: mỗi lượt gửi order mang về được phát lại đồng thời 3 lần với cùng request_id (giả lập phản hồi timeout): mỗi vòng chỉ 1 ORDER mang mã yêu cầu, 1 dòng món, tổng tiêu hao đúng -180 g/dòng (một số dòng chia qua 2–3 lô theo FIFO); các yêu cầu trùng còn lại trả 201 cùng order hoặc 422, không trừ lặp.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-30</td>
<td>FR-INV-12</td>
<td>Có dữ liệu lô, giữ và cảnh báo.</td>
<td>1. Mở màn hình kho.</td>
<td>Đủ tên, đơn vị, sổ sách, đủ điều kiện bán, đang giữ, khả dụng, ngưỡng, cảnh báo và thời điểm cập nhật.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI): Màn hình Tồn kho có đủ cột Nguyên liệu, Đơn vị, Tồn sổ sách, Đủ điều kiện, Đang giữ, Khả dụng, Mức tối thiểu, Hạn dùng gần nhất, Trạng thái, Chi tiết cảnh báo và dòng 'Dữ liệu lúc …' (thời điểm cập nhật).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-31</td>
<td>FR-INV-12</td>
<td>Có Thịt bò và Hành.</td>
<td>1. Tìm Thịt bò.</td>
<td>Chỉ trả nguyên liệu phù hợp tên tìm.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI): Có Thịt bò, Hành lá và 20 nguyên liệu khác: gõ 'Thịt bò' vào ô Tìm nguyên liệu → chỉ còn dòng Thịt bò.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-32</td>
<td>FR-INV-12</td>
<td>Có nguyên liệu cảnh báo và không cảnh báo.</td>
<td>1. Lọc theo cảnh báo tồn.</td>
<td>Chỉ hiển thị nguyên liệu đang có cảnh báo tồn.</td>
<td>Thường</td>
<td>04/11/2026 (bản 099191e, UI): Bấm bộ lọc 'Cần nhập thêm' → chỉ hiện 15 nguyên liệu có khả dụng dưới mức tối thiểu (Sắp hết/Hết hàng); các nguyên liệu không cảnh báo như Đường 501/500, Sữa không hạn 1.000/300, Nấm bị ẩn.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-33</td>
<td>FR-INV-08, NFR-07</td>
<td>Còn lượt chọn chưa gửi dù giữ đã hết hạn.</td>
<td>1. Thử mở phiên kiểm kê.</td>
<td>Từ chối và yêu cầu xử lý hết lượt chọn/giữ trước khi mở.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Không còn lượt giữ hiệu lực, chỉ còn 5 lượt chọn chưa gửi ở trạng thái 'Hết hạn': Bếp mở kiểm kê → 422 'Còn lượt giữ chỗ chưa gửi, hãy xử lý trước khi kiểm kê.'; không tạo phiên.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-34</td>
<td>FR-INV-08, NFR-07</td>
<td>Còn lượt giữ hiệu lực.</td>
<td>1. Thử mở phiên kiểm kê.</td>
<td>Từ chối và yêu cầu xử lý hết lượt chọn/giữ trước khi mở.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Còn 1 lượt giữ hiệu lực (Bò xào): mở kiểm kê → 422 'Còn lượt giữ chỗ chưa gửi…'; không có phiên mở.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-35</td>
<td>FR-INV-08, NFR-07</td>
<td>Đã kết thúc phục vụ; món đã chế biến/hủy; không còn lượt chọn hay giữ hiệu lực.</td>
<td>1. Bếp mở kiểm kê.</td>
<td>Tạo phiên trên server, chốt dữ liệu đối chiếu và khóa nghiệp vụ kho.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Không còn lượt chọn/giữ và món Chờ làm (các dòng đã xác nhận xong): Bếp mở kiểm kê → 201 phiên #2, trạng thái Đang kiểm kê; các nghiệp vụ kho bị khóa (INV-36..40). Ghi chú: muốn mở phải xử lý hết món Chờ làm ('Còn món Chờ làm, hãy xử lý trước khi kiểm kê.').</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-36</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API giữ món bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Phiên kiểm kê #2 đang mở: gọi API giữ món bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tồn Thịt bò (840 g), số giao dịch kho (117) và lượng giữ không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-37</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API gửi món bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Phiên kiểm kê #2 đang mở: gọi API gửi món bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tồn Thịt bò (840 g), số giao dịch kho (117) và lượng giữ không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-38</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API nhập kho bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Phiên kiểm kê #2 đang mở: gọi API nhập kho bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tồn Thịt bò (840 g), số giao dịch kho (117) và lượng giữ không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-39</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API xuất kho bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Phiên kiểm kê #2 đang mở: gọi API xuất kho bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tồn Thịt bò (840 g), số giao dịch kho (117) và lượng giữ không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-40</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API hoàn kho bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Phiên #2 đang mở: Quản lý gọi API hủy món (hoàn kho) → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; không có giao dịch hoàn. (Dòng dùng thử ở trạng thái Đã xác nhận xong vì điều kiện mở phiên yêu cầu không còn món Chờ làm.)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-41</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở; đã nhập số lượng thực tế, chưa xác nhận.</td>
<td>1. Hủy phiên.2. Thực hiện nhập kho hợp lệ.</td>
<td>Phiên kết thúc, không điều chỉnh tồn do kiểm kê; nhập kho được thực hiện bình thường.</td>
<td>Trọng yếu</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="even">
<td>TC-INV-42</td>
<td>FR-INV-08, FR-INV-09, FR-INV-05</td>
<td>Kiểm kê bò: sổ sách 500 g, thực tế 450 g; lô nhập trước còn 200 g.</td>
<td>1. Nhập 450 g và lý do, chọn Xem trước.2. Kiểm tra bản xem trước và xác nhận.</td>
<td>Bản xem trước hiển thị tồn trước 500 g, tồn sau 450 g, chênh lệch −50 g; sau khi xác nhận, điều chỉnh giảm 50 g từ lô nhập trước; sinh một phiếu xuất hủy nguồn Kiểm kê; phiếu không trừ kho thêm; có audit log.</td>
<td>Trọng yếu</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="odd">
<td>TC-INV-43</td>
<td>FR-INV-08, FR-INV-09</td>
<td>Kiểm kê hành: sổ sách 100 g, thực tế 120 g.</td>
<td>1. Nhập 120 g và lý do, chọn Xem trước.2. Xác nhận.</td>
<td>Điều chỉnh tăng 20 g theo BR-LOT-02, giá trị theo đơn giá bình quân hiện hành; không có phiếu xuất hủy cho phần tăng; có audit log.</td>
<td>Trọng yếu</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="even">
<td>TC-INV-44</td>
<td>FR-INV-08, FR-INV-09</td>
<td>Sổ sách và thực tế đều 500 g.</td>
<td>1. Nhập 500 g, chọn Xem trước.2. Xác nhận.</td>
<td>Chênh lệch 0; tồn không đổi, không tạo chứng từ hao hụt; phiên kết thúc.</td>
<td>Trọng yếu</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="odd">
<td>TC-INV-45</td>
<td>FR-INV-06, FR-INV-08, FR-INV-09</td>
<td>Phiếu chênh lệch âm đã xác nhận thành công.</td>
<td>1. Gửi lại yêu cầu xác nhận cùng phiếu.</td>
<td>Không điều chỉnh tồn lần hai, không tạo thêm phiếu xuất hủy nguồn Kiểm kê.</td>
<td>Trọng yếu</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="even">
<td>TC-INV-46</td>
<td>FR-INV-08, NFR-07</td>
<td>Đã kết thúc phục vụ, không giữ hiệu lực; chuẩn bị mở kiểm kê và một yêu cầu nhập.</td>
<td>1. Phát đồng thời mở kiểm kê và nhập kho.<br />
2. Đối chiếu thứ tự commit; lặp 100 lượt.</td>
<td>Nếu nhập commit trước chốt thì số chốt gồm lượng nhập; nếu khóa kiểm kê có trước thì nhập bị chặn. Tồn không đổi giữa chốt và xác nhận do giao dịch cạnh tranh.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, Script): 100 vòng phát đồng thời mở kiểm kê và nhập 7 g Sữa: 100 lần mở phiên thành công; 2 vòng phiếu nhập commit trước (tồn gồm lượng nhập), 98 vòng nhập bị chặn 422 với tồn không đổi; không vòng nào lệch tồn.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-47</td>
<td>FR-INV-04, FR-INV-13</td>
<td>Món Chờ làm đã tiêu hao 150 g; lô gốc vừa hết hạn; Bếp xác nhận chưa làm.</td>
<td>1. Hủy món.</td>
<td>Hoàn 150 g đúng lô gốc; tăng tồn sổ sách nhưng không tăng tồn đủ điều kiện bán.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, Script): NL 46 (bảo quản 1 ngày): lô #89 nhập 03/11/2026 1.000 g, hạn 04/11/2026. Order 376 (món 150 g) gửi 04/11 khi lô còn hạn → 'Trừ tự động' lô #89 −150, dòng 384 'Chờ làm'. Tại thời điểm mô phỏng 05/11/2026 07:00 (lô đã quá hạn), khả dụng 0; Quản lý hủy món (Bếp xác nhận chưa làm) → 'Hoàn kho' +150 đúng lô #89 (BD 05/11), tồn sổ sách 850 → 1.000 g, lô #89 1.000 g 'Hết hạn'; khả dụng sau hoàn vẫn 0 (không tăng tồn đủ điều kiện bán).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-48</td>
<td>NFR-04</td>
<td>Đăng nhập Thu ngân; phiếu nhập có dữ liệu hợp lệ.</td>
<td>1. Gọi API xác nhận nhập kho.</td>
<td>Backend từ chối quyền; không tạo lô hoặc tăng tồn.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Thu ngân gọi POST /inventory/receipts với dữ liệu hợp lệ → 403; số lô (34) không đổi.</td>
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
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="even">
<td>TC-INV-50</td>
<td>FR-INV-05, FR-INV-06</td>
<td>Một suất món đã tiêu hao 150 g nguyên liệu.</td>
<td>1. Gửi yêu cầu hủy một suất, kèm định lượng 999 g.</td>
<td>Phiếu ghi nhận 150 g nguyên liệu theo tiêu hao gốc, liên kết đúng dòng món; tồn kho không thay đổi.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Gửi yêu cầu hủy 1 suất kèm định lượng 999 g: phiếu vẫn ghi 150 g/50 g theo tiêu hao gốc, liên kết đúng dòng #55; tồn kho không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-51</td>
<td>FR-INV-05, FR-INV-06</td>
<td>Dòng order đã gửi theo công thức 150 g/suất; công thức hiện hành đã đổi thành 200 g/suất.</td>
<td>1. Chọn dòng order cũ và hủy 1 suất đã chế biến.</td>
<td>Chứng từ dùng 150 g theo tiêu hao gốc, không dùng 200 g của công thức hiện hành; không trừ kho lần hai.</td>
<td>Trọng yếu</td>
<td>04/11/2026 (bản 099191e, API): Sau khi công thức Bò bơ đổi thành 200 g Bơ/suất, hủy 1 suất đã chế biến của dòng cũ #55 → phiếu #8 ghi 150 g Bơ (tiêu hao gốc), không dùng 200 g; tồn không trừ lần hai.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-52</td>
<td>FR-INV-08, FR-INV-09</td>
<td>Phiên kiểm kê đang mở; bò sổ sách 500 g, thực tế 470 g.</td>
<td>1. Nhập 470 g và chọn Xem trước.2. Chưa xác nhận, kiểm tra tồn kho và sổ kho.</td>
<td>Bản xem trước hiển thị tồn trước 500 g, tồn sau 470 g, chênh lệch −30 g; tồn và sổ kho chưa thay đổi; phiếu vẫn Đang kiểm kê, kho vẫn khóa.</td>
<td>Trọng yếu</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="odd">
<td>TC-INV-53</td>
<td>FR-INV-08</td>
<td>Phiên kiểm kê đang mở; hành sổ sách 100 g.</td>
<td>1. Nhập 80 g và chọn Xem trước.2. Chọn Quay lại sửa, nhập 100 g.3. Xem trước và xác nhận.</td>
<td>Lần xem trước đầu không ghi điều chỉnh; sau khi sửa, chênh lệch bằng 0, không tạo giao dịch điều chỉnh; phiếu Đã xác nhận.</td>
<td>Thường</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="even">
<td>TC-INV-54</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở; bản xem trước có chênh lệch âm, chưa xác nhận.</td>
<td>1. Hủy phiên.2. Kiểm tra tồn, sổ kho và trạng thái khóa.</td>
<td>Phiếu Đã hủy; không có giao dịch điều chỉnh hay phiếu xuất hủy nguồn Kiểm kê; kho được mở khóa.</td>
<td>Trọng yếu</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
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
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="even">
<td>TC-INV-56</td>
<td>FR-INV-12</td>
<td>Bò chưa xuất: lô 1 nhập 10 kg giá 200.000 đ/kg, sau đó lô 2 nhập 10 kg giá 260.000 đ/kg.</td>
<td>1. Mở màn hình tồn kho, tìm Bò.2. Chọn Bò để xem lịch sử đơn giá bình quân.</td>
<td>Đơn giá bình quân hiện hành 230.000 đ/kg; giá trị tồn 4.600.000 đ; lịch sử có hai dòng: 200.000 đ/kg sau phiếu nhập lô 1 và 230.000 đ/kg sau phiếu nhập lô 2, kèm thời điểm, chứng từ và tồn sau giao dịch.</td>
<td>Thường</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
<tr class="odd">
<td>TC-INV-57</td>
<td>FR-INV-12, FR-INV-09</td>
<td>Sả chưa có phiếu nhập; kiểm kê thừa 200 g đã được xác nhận.</td>
<td>1. Mở màn hình tồn kho, tìm Sả.</td>
<td>Tồn sổ sách 200 g; đơn giá bình quân và giá trị tồn hiển thị “Chưa xác định”, không hiển thị 0.</td>
<td>Thường</td>
<td>Chưa thực hiện.</td>
<td>Chưa kiểm tra</td>
</tr>
</tbody>
</table>

Bảng 48. Ca kiểm thử module Quản lý kho

Lỗi tạo tài khoản ở UC 5.1 được ghi nhận thành ca TC-SET-01. Các ca TC-SET-02–09 kiểm tra FR-SET-02, 03, 04, 06 và 07 (phân quyền, thay đổi cấu hình, audit log). Bảng 49 chưa bao phủ FR-SET-05 ngoài các ca ngưỡng tồn kho thuộc module Kho.

| **Mã ca** | **FR/NFR**                   | **Điều kiện và dữ liệu**                                                          | **Bước thực hiện**                                                                                                           | **Kết quả mong đợi**                                                                                                                     | **Ưu tiên** | **Kết quả thực tế**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | **Trạng thái** |
|-----------|------------------------------|-----------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| TC-SET-01 | FR-SET-01                    | Đăng nhập Quản lý; thông tin tài khoản mới hợp lệ, tên đăng nhập chưa tồn tại.    | 1\. Gửi yêu cầu tạo tài khoản mới.                                                                                           | Tạo thành công; phản hồi trả về thông tin tài khoản và bản ghi được lưu.                                                                 | Thường      | 03/11/2026 (bản 099191e, UI): Quản lý tạo tài khoản Thu ngân seed_cashier và Bếp seed_warehouse trên giao diện: cả hai lần API trả HTTP 500 (MissingGreenlet khi đọc NgayTao để trả UserOut); giao diện báo 'Không thực hiện được. Kiểm tra kết nối rồi thử lại.', hộp thoại không đóng. Bản ghi NGUOI_DUNG và nhật ký CREATE_USER vẫn được lưu; tải lại trang mới thấy tài khoản.                                                                                                                                                   | Không đạt      |
| TC-SET-02 | FR-SET-02                    | Tài khoản Thu ngân đang hoạt động; biết mật khẩu hiện tại.                        | 1\. Đăng nhập. 2. Tự đổi mật khẩu với mật khẩu hiện tại đúng. 3. Đăng xuất, đăng nhập lại bằng mật khẩu cũ rồi mật khẩu mới. | Đổi thành công; mật khẩu cũ bị từ chối, mật khẩu mới đăng nhập được; không phát sinh bản ghi audit log (ngoài phạm vi theo FR-SET-02).   | Thường      | 03/11/2026 (bản 099191e, UI): seed_cashier2 đổi mật khẩu với mật khẩu hiện tại đúng: báo 'Đã đổi mật khẩu. Vui lòng đăng nhập lại.', tự đăng xuất; đăng nhập bằng mật khẩu cũ bị từ chối ('Tên đăng nhập hoặc mật khẩu không đúng.'), mật khẩu mới vào được /sales; nhật ký hệ thống không phát sinh bản ghi mới (vẫn 4 bản ghi).                                                                                                                                                                                                    | Đạt            |
| TC-SET-03 | FR-SET-02                    | Tài khoản Thu ngân đang hoạt động.                                                | 1\. Gửi yêu cầu tự đổi mật khẩu với mật khẩu hiện tại sai.                                                                   | Bị từ chối kèm thông báo tiếng Việt; mật khẩu không đổi; đăng nhập bằng mật khẩu cũ vẫn thành công.                                      | Thường      | 03/11/2026 (bản 099191e, UI): seed_cashier2 nhập mật khẩu hiện tại sai trên hộp thoại Đổi mật khẩu: bị từ chối với thông báo 'Mật khẩu hiện tại không đúng.' (HTTP 422); hash mật khẩu không đổi; đăng xuất và đăng nhập lại bằng mật khẩu cũ thành công.                                                                                                                                                                                                                                                                            | Đạt            |
| TC-SET-04 | FR-SET-02; FR-SET-06         | Đăng nhập Quản lý; có người dùng quên mật khẩu.                                   | 1\. Quản lý đặt lại mật khẩu hộ người dùng. 2. Người dùng đăng nhập bằng mật khẩu mới. 3. Quản lý mở nhật ký.                | Đặt lại thành công; người dùng đăng nhập được; có bản ghi audit log gồm người thực hiện, thời điểm, loại thao tác.                       | Trọng yếu   | 03/11/2026 (bản 099191e, UI): Quản lý bấm Đặt lại mật khẩu cho seed_cashier2 và nhập mật khẩu mới: báo 'Đã đặt lại mật khẩu cho Thu ngân QA 2.'; phiên cũ của người dùng bị thu hồi ('Phiên đăng nhập đã hết hạn hoặc bị thu hồi'); người dùng đăng nhập bằng mật khẩu mới vào được /sales; Nhật ký thao tác có bản ghi 'Đặt lại mật khẩu – NGUOI_DUNG \#4 – Quản lý QA – 21:21 03/11/2026'.                                                                                                                                         | Đạt            |
| TC-SET-05 | FR-SET-02; FR-SET-03; NFR-04 | Có tài khoản Thu ngân và Bếp; một người dùng khác làm đối tượng.                  | 1\. Thu ngân gọi trực tiếp API đặt lại mật khẩu của người dùng khác. 2. Bếp làm tương tự.                                    | Cả hai bị từ chối (HTTP 403); mật khẩu không đổi; không có bản ghi audit log mới.                                                        | Trọng yếu   | 03/11/2026 (bản 099191e, API): Thu ngân gọi POST /settings/users/1/reset-password và Bếp gọi POST /settings/users/2/reset-password: cả hai 403 'Bạn không có quyền thực hiện chức năng này.'; hash mật khẩu của hai người dùng không đổi; số bản ghi nhật ký giữ nguyên (4).                                                                                                                                                                                                                                                         | Đạt            |
| TC-SET-06 | FR-SET-03; NFR-04            | Đăng nhập Thu ngân.                                                               | 1\. Kiểm tra mục điều hướng. 2. Truy cập trực tiếp màn hình và API Cài đặt, Báo cáo.                                         | Không có mục điều hướng Cài đặt và Báo cáo; truy cập trực tiếp bị chặn ở cả giao diện và API (HTTP 403), không lộ dữ liệu.               | Trọng yếu   | 03/11/2026 (bản 099191e, UI+API): Thu ngân: menu chỉ có Danh mục, Bán hàng, Trợ lý AI (không có Cài đặt, Báo cáo); mở thẳng /settings và /reports đều bị chuyển về /sales; 13 API Cài đặt/Báo cáo (users, config, audit-log, revenue, dishes, hours, margin, costs, comparison, cancelled-orders, closed-unpaid, pending-payments, backup) đều 403 không kèm dữ liệu; PUT config 403, cấu hình không đổi.                                                                                                                            | Đạt            |
| TC-SET-07 | FR-SET-03; NFR-04            | Có tài khoản Bếp và Quản lý.                                                      | 1\. Bếp truy cập trực tiếp API Cài đặt và API thanh toán. 2. Quản lý dùng chức năng của Thu ngân và của Bếp.                 | Bếp bị từ chối (HTTP 403) với chức năng ngoài phạm vi; Quản lý truy cập được cả hai nhóm chức năng (kế thừa quyền).                      | Trọng yếu   | 03/11/2026 (bản 099191e, UI+API): Bếp gọi trực tiếp API Cài đặt (users, config, audit-log, backup) và API thanh toán (pay/cash, pay/qr, payments, payment-exceptions): đều 403. Quản lý dùng chức năng Thu ngân trên giao diện Bán hàng (chạm Bò xào tạo lượt giữ, Hủy lượt chọn) và chức năng Bếp trên giao diện Kho (tạo phiếu nhập \#2 Hành lá 100 g): đều thành công.                                                                                                                                                            | Đạt            |
| TC-SET-08 | FR-SET-04; FR-SET-06         | Đăng nhập Quản lý; thời hạn giữ món hiện là 5 phút.                               | 1\. Đổi thời hạn giữ món thành 10 phút. 2. Thử nhập 0 và giá trị âm. 3. Mở nhật ký.                                          | 10 phút được lưu và áp dụng cho lượt giữ món mới; 0 và giá trị âm bị từ chối; audit log ghi dữ liệu trước (5) và sau (10).               | Trọng yếu   | 03/11/2026 (bản 099191e, UI): Quản lý nhập 0 và -1 cho Thời gian giữ chỗ: giao diện chặn 'Thời gian giữ chỗ phải là số nguyên dương.' (API cũng trả 422), cấu hình giữ 5. Lưu 10: báo 'Đã lưu cấu hình.'; nhật ký UPDATE_CONFIG xem được TRƯỚC ThoiGianGiuChoPhut=5, SAU=10; lượt giữ mới tạo sau đó có ThoiDiemHetHan – NgayTao = 599,98 giây (10 phút).                                                                                                                                                                            | Đạt            |
| TC-SET-09 | FR-SET-07; NFR-04            | Nhật ký có bản ghi từ nhiều loại thao tác; có tài khoản Quản lý, Thu ngân và Bếp. | 1\. Quản lý mở nhật ký. 2. Thu ngân và Bếp truy cập trực tiếp màn hình và API nhật ký.                                       | Quản lý xem toàn bộ; mỗi bản ghi có người thực hiện, thời điểm, loại thao tác, dữ liệu trước/sau; Thu ngân và Bếp bị từ chối (HTTP 403). | Trọng yếu   | 03/11/2026 (bản 099191e, UI+API): Quản lý mở Nhật ký thao tác: thấy đủ bản ghi với thời điểm, loại thao tác, đối tượng, người thực hiện; bản ghi cấu hình xem được TRƯỚC/SAU (5→10). Thu ngân và Bếp: không có mục Cài đặt, mở thẳng /settings bị chuyển về màn hình của vai trò, API /settings/audit-log trả 403. Sai lệch (mức nhẹ): một số loại bản ghi không lưu dữ liệu trước/sau theo FR-SET-07 – RESET_PASSWORD (trước/sau đều trống), UPDATE_GROUP đổi tên nhóm (không lưu tên cũ/mới), CREATE_GROUP (không có dữ liệu sau). | Không đạt      |

Bảng 49. Ca kiểm thử module Cài đặt hệ thống

## G. Hiệu năng cơ bản

### G.1. Môi trường và dữ liệu

Môi trường đo: máy Intel Core i7-11850H, RAM 16 GB, Windows 11 Pro, MySQL 8.4.13 chạy trong Docker, FastAPI (uvicorn) một tiến trình; công cụ tạo tải, API và CSDL chạy chung máy. Dữ liệu theo Phụ lục B.2 của báo cáo gồm khoảng 4.800 order trong 2 tháng, 30 món, 35 nguyên liệu và 12 bàn; trước mỗi lượt, CSDL được khôi phục từ cùng một bản sao và API được khởi động mới; cổng thanh toán và trợ lý AI dùng bộ giả lập.

### G.2. Kịch bản kiểm tra

Bốn nhóm đo gồm nghiệp vụ với 5, 10 và 20 người dùng đồng thời, cùng đọc báo cáo với 5 người dùng. Mỗi nhóm gồm 1 phút khởi động và 5 phút đo. Nghiệp vụ gồm giữ món, sửa lượng giữ, gửi món, đọc order, đọc thực đơn, xem danh mục và nhập kho; báo cáo gồm doanh thu ngày, doanh thu tháng và xếp hạng món.

### G.3. Chỉ tiêu

Ghi thời gian phản hồi p95 và số lỗi. p95 là thời gian mà 95% yêu cầu trong mẫu hoàn thành không vượt quá. Ngưỡng đối chiếu: nghiệp vụ không quá 1 giây, báo cáo dưới 10 giây; lỗi được thống kê riêng.

### G.4. Kết quả

Bảng dưới là mẫu tổng hợp kết quả cho từng nhóm đo. Kết quả trên bộ dữ liệu 2 tháng chưa được đo. p95 tính trên các yêu cầu trong pha đo; không bao gồm thời gian cổng ngân hàng hoặc máy in vật lý.

Bảng 50. Kết quả hiệu năng cơ bản

| **Chỉ tiêu**             | **Kết quả** | **Phạm vi kết luận**                                                |
|--------------------------|-------------|---------------------------------------------------------------------|
| Nghiệp vụ, 5 người dùng  | Chưa đo     | Ngưỡng 1 giây                                                       |
| Nghiệp vụ, 10 người dùng | Chưa đo     | Ngưỡng 1 giây                                                       |
| Nghiệp vụ, 20 người dùng | Chưa đo     | Ngưỡng 1 giây                                                       |
| Báo cáo, 5 người dùng    | Chưa đo     | Ngưỡng 10 giây                                                      |
| Bất biến sau chạy        | Chưa đo     | Sổ cái, tồn, gửi trùng và doanh thu lịch sử phải khớp bản đối chứng |

## H. Kiểm thử báo cáo và điều kiện biên

Phần này gồm các ca của module Báo cáo và các điều kiện biên nghiệp vụ liên quan đến nhiều module.

### H.1. Module Báo cáo

Đối chiếu dữ liệu trả về và hiển thị theo kỳ, bộ lọc và trạng thái. Ca chưa được kiểm tra đủ giữ trạng thái tương ứng.

| **Ca**    | **FR** | **Dữ liệu và thao tác**                                                                       | **Kết quả mong đợi**                                                                                                                                                                       | **Kết quả**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|-----------|--------|-----------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TC-REP-01 | 01     | Order thành công 100.000 tiền mặt, 200.000 QR; chờ 50.000; hủy 80.000.                        | Doanh thu 300.000; lọc tiền mặt 100.000, QR 200.000; loại chờ/hủy.                                                                                                                         | 04/11/2026 (bản 099191e, UI+Script): Dữ liệu riêng Business Date 10/12/2026 (món 10.000đ): order 352 tiền mặt 100.000, order 353 QR 200.000 đã xác nhận, order 354 QR chờ 50.000, order 355 hủy 80.000. Màn Báo cáo (Quản lý) chọn Ngày 10/12/2026: Doanh thu 300.000 ₫, 2 đơn, 'Đã đối soát đầy đủ'; nhóm theo Phương thức thanh toán: QR 200.000, Tiền mặt 100.000. Order chờ không vào doanh thu, order hủy chỉ ở báo cáo Order hủy (80.000). Ghi chú: khung 'Món bán chạy' trên tab Doanh thu không gửi mốc kỳ nên hiện món của hôm nay (xem TC-REP-09).                                                                                                               |
| TC-REP-02 | 02     | Tạo chờ xác minh → mở lại → nhận tiền thành công.                                             | Danh sách khoản chưa thu theo đúng trạng thái; trước thành công doanh thu 0; sau thành công ghi một lần.                                                                                   | 04/11/2026 (bản 099191e, UI+Script): Order 356 (30.000, BD 11/12/2026): QR \#28 → Chờ xác minh. Trước khi thu: báo cáo ngày 11/12 Doanh thu 0, tạm tính 30.000 tách riêng; danh sách chờ xác minh tháng 12 có order 356 đúng trạng thái 'Chờ xác minh thanh toán'. Quản lý mở lại (QR \#28 → Đã hủy), tạo QR \#29 và xác nhận Thành công: doanh thu 11/12 = 30.000, 1 đơn, 1 hóa đơn 30.000 (ghi một lần), order rời danh sách chờ (tháng 12 rỗng). Màn Báo cáo hiển thị 30.000 cho 11/12.                                                                                                                                                                                 |
| TC-REP-03 | 03     | Món A/B đồng số lượng, khác tiền; lọc đổi kỳ.                                                 | Thứ hạng khớp tổng lượng/tiền và quy tắc đồng hạng; không mất món do LIMIT.                                                                                                                | 04/11/2026 (bản 099191e, UI+Script): BD 21/12/2026: món A 'QA Báo cáo 10k' 5 phần = 50.000, món B 'QA Báo cáo 20k' 5 phần = 100.000; 22/12 thêm A 1 phần. Tab Món ăn, Ngày 21/12: theo Số lượng A 5 / B 5 (đồng hạng, xếp ổn định theo mã món), theo Doanh thu B 100.000 trước A 50.000. Đổi kỳ Tháng 12/2026: A 49 phần/490.000, B 5/100.000 — khớp tổng dòng order đã thanh toán; tuần 21–27/12: A 6, B 5. Tháng 11/2026 API trả đủ 4/4 món đã bán (không mất món do LIMIT). Ghi chú: tài liệu không quy định cách hiển thị đồng hạng; hệ thống không gộp cùng hạng mà xếp theo mã món.                                                                                  |
| TC-REP-04 | 04     | Doanh thu 1.000.000; giá vốn bán 300.000; hao hụt 50.000; hủy/đóng 20.000.                    | Lợi nhuận gộp 630.000; không trừ lương/thuê và không gộp giá trị order chưa thu vào doanh thu.                                                                                             | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-REP-05 | 05     | Một chênh lệch âm kiểm kê có giao dịch kho và phiếu xuất hủy tự sinh.                         | Chi phí chỉ tính một lần; không cộng cả sổ cái và chứng từ cho cùng biến động.                                                                                                             | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-REP-06 | 06     | Thay giá/công thức sau bán; có hao hụt kho chung.                                             | Chi phí món dùng phiên bản của dòng bán; không phân bổ hao hụt chung tùy ý.                                                                                                                | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-REP-07 | 07     | Order sát cutoff và qua nửa đêm; ngày/giờ biên.                                               | Bucket khung giờ theo quy tắc; kỳ Business Date khớp order, không lẫn ngày lịch.                                                                                                           | 04/11/2026 (bản 099191e, UI+Script): Order tiền mặt lúc 05:59:59 26/12 (10.000), 06:00 26/12 (20.000), 23:59 26/12 (30.000), 00:30 27/12 (40.000), 05:59 27/12 (50.000). Business Date đúng: BD 25/12 = 1 đơn 10.000; BD 26/12 = 4 đơn 140.000; BD 27/12 rỗng. Khung giờ BD 26/12: 6h 20.000, 23h 30.000, 0h 40.000, 5h 50.000, trục bắt đầu 6h — đúng. Lệch: 'Chi tiết theo ngày trong tuần' của BD 26/12 tách thành Thứ 7: 2 đơn và Chủ nhật: 2 đơn (theo ngày lịch, lẫn với Business Date) và cột Doanh thu theo ngày trong tuần luôn 0 ₫ (API by_weekday DoanhThu 0.0).                                                                                                |
| TC-REP-08 | 08     | Kỳ gốc 0, kỳ sau 100.000; thêm cặp 100.000 → 120.000.                                         | Cặp đầu không chia 0; cặp sau tăng 20%; chênh lệch tuyệt đối đúng.                                                                                                                         | 04/11/2026 (bản 099191e, UI+API): Dữ liệu: 01/2027 không có đơn, 02/2027 100.000; 03/2027 100.000, 04/2027 120.000 (mỗi kỳ 1 đơn tiền mặt). Màn So sánh 01/2027–02/2027: 0 ₫ → 100.000 ₫, 'Không xác định tỷ lệ phần trăm', +100.000 ₫ (không chia 0, đúng). 03/2027–04/2027: 100.000 → 120.000, hiển thị 'Tăng 20%' (API change_percent 20.00) nhưng KHÔNG hiển thị chênh lệch tuyệt đối +20.000 ₫ (tìm trên trang không có). Lệch so với kỳ vọng 'chênh lệch tuyệt đối đúng'.                                                                                                                                                                                            |
| TC-REP-09 | 09     | Cùng bộ lọc có dữ liệu, rỗng, đổi kỳ.                                                         | Bảng/biểu đồ cùng tổng và đơn vị; rỗng không vẽ số liệu giả.                                                                                                                               | 04/11/2026 (bản 099191e, UI): Tab Doanh thu tháng 12/2026: thẻ Doanh thu 590.000 ₫, 8 đơn, bảng chi tiết 6 mốc (300.000 + 30.000 + 60.000 + 40.000 + 150.000 + 10.000 = 590.000), biểu đồ cao nhất 300.000 — bảng/biểu đồ/thẻ cùng tổng và đơn vị. Kỳ rỗng 01/2027: 0 ₫ và 'Chưa có dữ liệu trong kỳ', không vẽ số giả. Lệch: khung 'Món bán chạy' trên tab Doanh thu gọi /reports/dishes không kèm mốc kỳ nên luôn hiện dữ liệu kỳ hiện tại (Bò xào 6, Heo xào 3, Cá kho 3, Ốc xào 2) trong khi kỳ đang xem 12/2026 chỉ bán 2 món QA (cũng gặp ở ngày 10/12/2026).                                                                                                        |
| TC-REP-10 | 10     | Order hủy, đóng chưa thu; sau đó áp khoản muộn hợp lệ cho order đóng.                         | Hai nhóm tách; khi nhận tiền rời tổng đóng, giữ lịch sử, doanh thu ghi một lần.                                                                                                            | 04/11/2026 (bản 099191e, UI+Script): BD 12/12/2026: order 357 (40.000) hủy; order 358 (60.000) QR \#30 → chờ xác minh → Quản lý đóng chưa thu. Báo cáo: Order hủy 1 đơn/40.000, Đóng chưa thu 1 đơn/60.000 (lý do, người đóng) — hai nhóm tách; doanh thu ngày 0. Áp khoản muộn cho QR \#30: order 358 → Đã thanh toán, 1 hóa đơn 60.000; nhóm Đóng chưa thu về 0, doanh thu 12/12 = 60.000 (ghi một lần), Order hủy vẫn 40.000; nhật ký giữ CLOSE_UNPAID_ORDER và APPLY_LATE_PAYMENT. Màn Báo cáo tab Order hủy ngày 12/12 hiển thị đúng 40.000 và 'Không có order đóng chưa thu tiền trong kỳ'.                                                                          |
| TC-REP-11 | 11     | Tồn 100 đơn vị giá 10.000 đ; nhập 100 × 20.000 đ, xuất 50; nhập tiếp 100 × 30.000 đ, xuất 50. | Đơn giá bình quân sau hai lần nhập là 15.000 đ và 21.000 đ; giá vốn hai lần xuất lần lượt 750.000 đ và 1.050.000 đ theo công thức lưu trên dòng; giá trị đã ghi không đổi khi có nhập sau. | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-REP-12 | 12     | Xuất hủy nguyên liệu, thiếu kiểm kê, phiếu món đã chế biến.                                   | Hai nguồn đầu vào hao hụt; nguồn món giữ nhóm giá vốn order, không cộng lặp.                                                                                                               | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-REP-13 | 13     | Order hủy có món Chờ làm hoàn kho và món đã chế biến không hoàn.                              | Chỉ phần không hoàn vào chi phí hủy/đóng; nhận muộn chuyển giá vốn đúng một lần.                                                                                                           | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-REP-14 | 01–13  | Gọi trực tiếp API Báo cáo bằng Thu ngân và Bếp.                                               | 403 và không có dữ liệu, dù người dùng sửa URL hoặc tham số vai trò.                                                                                                                       | 04/11/2026 (bản 099191e, API): Thu ngân (seed_cashier) và Bếp (vai trò Kho – seed_warehouse; hệ thống có ba vai trò, phân hệ Kho dành cho Nhân viên bếp) gọi 10 API báo cáo (doanh thu, món, giờ, biên lợi nhuận, giá vốn món, chi phí, so sánh, order hủy, đóng chưa thu, chờ thanh toán), kể cả thêm tham số role=MANAGER/as_role: 20/20 lượt trả 403 FORBIDDEN, không lộ dữ liệu.                                                                                                                                                                                                                                                                                       |
| TC-REP-15 | 01, 11 | Đổi ngày kinh doanh cấu hình sau khi đã phát sinh order.                                      | Không tính lại BusinessDate cũ; tổng doanh thu/giá vốn lịch sử không tự dịch kỳ.                                                                                                           | 04/11/2026 (bản 099191e, UI+API): Đã có dữ liệu tháng 11 và 12/2026 (gồm order sát mốc 26–27/12). Ghi trước: doanh thu 25/12 = 10.000, 26/12 = 140.000 (4 đơn), tháng 12 = 805.000 (15 đơn), tháng 11 = 1.220.000; giá vốn tháng 12 = 2.266,78, tháng 11 = 416.000; băm BusinessDate của ORDER/HOA_DON/GIAO_DICH_KHO. Màn Cài đặt › Cấu hình đổi giờ bắt đầu Business Date 06:00 → 04:00: hệ thống tạo lịch chờ 'từ ngày kinh doanh 2026-11-05', ngày hiện tại vẫn 06:00. Sau khi lưu: toàn bộ tổng doanh thu/giá vốn và cả ba băm BusinessDate giống hệt trước (không tính lại BusinessDate cũ, không dịch kỳ). Sau đó đặt lại 06:00 qua giao diện, lịch chờ bị thay thế. |

### H.2. Điều kiện biên nghiệp vụ

Các tình huống giữ món hết hạn, kiểm kê, lô bị hủy, giá vốn và làm tròn thuộc kiểm tra chức năng. Kiểm tra liên quan đạt chưa có nghĩa toàn bộ ca đạt.

| **Mã**   | **Yêu cầu liên quan**                 | **Dữ liệu / sự kiện**                                                                                                | **Kết quả mong đợi**                                                                                                                                                                         | **Kết quả thực tế**                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
|----------|---------------------------------------|----------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TC-BR-01 | FR-SALE-05; FR-INV-10                 | Giờ server bằng hạn giữ; tồn đủ, giá/công thức không đổi; gửi toàn lượt chọn                                         | Không coi giữ cũ còn hiệu lực; kiểm tra lại đủ rồi gửi một lần; không tự gia hạn                                                                                                             | 04/11/2026 (bản 099191e, Script): Giờ server bằng hạn giữ, tồn đủ, giá/công thức không đổi: lượt giữ cũ không được coi là còn hiệu lực, hệ thống kiểm tra lại rồi gửi đúng một lần (100/100 lượt, tiêu hao 150 g mỗi lượt). Ghi chú: sau khi gửi, bản ghi giữ (đã chuyển 'Đã gửi') có ThoiDiemHetHan mới do bước giữ lại khi gửi; không có lượt giữ nào được gia hạn trước khi gửi.                                                                                        |
| TC-BR-02 | FR-INV-08; TC-INV-33                  | Chỉ còn dòng hết hạn chưa gửi/hủy; yêu cầu mở kiểm kê                                                                | Từ chối; phần hết hạn không chiếm khả dụng nhưng lượt chọn chưa kết thúc                                                                                                                     | 04/11/2026 (bản 099191e, API): Chỉ còn dòng giữ đã hết hạn, chưa gửi/hủy (5 lượt): mở kiểm kê bị từ chối 422; phần hết hạn không chiếm khả dụng nhưng lượt chọn vẫn được coi là chưa kết thúc; hệ thống không tự hủy.                                                                                                                                                                                                                                                      |
| TC-BR-03 | FR-INV-08                             | Hủy lượt chọn trong BR-02 rồi yêu cầu mở; không còn trở ngại khác                                                    | Giải phóng/đánh dấu xử lý một lần; mở phiên duy nhất, khóa kho                                                                                                                               | 04/11/2026 (bản 099191e, API): Hủy các lượt chọn đó (Đã giải phóng), xử lý hết món Chờ làm, rồi mở kiểm kê → 201 phiên \#2; mở lần nữa → 422 'Đang có phiên kiểm kê chưa chốt.' (chỉ 1 phiên); trong phiên, giữ/gửi/nhập/xuất đều bị chặn 'Đang kiểm kê, không thể thay đổi tồn kho.'.                                                                                                                                                                                     |
| TC-BR-04 | FR-SALE-16                            | QR cũ hết hạn; tạo QR mới chưa nhận tiền; khoản cũ đúng tiền đến; chưa quyết định mở lại của Quản lý                 | Xác nhận khoản cũ, hủy QR mới trong một transaction; một hóa đơn, không đổi bàn                                                                                                              | 04/11/2026 (bản 099191e, API): Order mang về \#43: QR cũ \#23 đã hết hạn; tạo QR mới \#24 chưa nhận tiền; webhook khoản cũ TT23 đúng số tiền đến → \#23 Thành công, \#24 Đã hủy, order Đã thanh toán, đúng 1 hóa đơn, không phát sinh ngoại lệ, không liên quan bàn (đơn mang về).                                                                                                                                                                                         |
| TC-BR-05 | FR-SALE-17, 23                        | Quản lý đã Mở lại thanh toán; khoản cũ đúng tiền đến khi chưa thu lại                                                | Ghi ngoại lệ, không tự thanh toán; chỉ Quản lý áp dụng hợp lệ                                                                                                                                | 04/11/2026 (bản 099191e, API): Order \#17 đã được Quản lý Mở lại thanh toán (giao dịch \#13 Đã hủy); khoản cũ 80.000 TT13 đến → ghi ngoại lệ \#4 Chờ xử lý, không tự thanh toán (order Đang mở, 0 hóa đơn); Thu ngân áp dụng ngoại lệ → 403.                                                                                                                                                                                                                               |
| TC-BR-06 | FR-SALE-15–17                         | Cùng khoản nhận được webhook lặp trước/sau xác nhận thủ công                                                         | Một lần thu, một hóa đơn; không tạo thêm ngoại lệ cho cùng khoản                                                                                                                             | 04/11/2026 (bản 099191e, API): Order \#41 có QR \#21: Thu ngân báo khách chuyển (mã FT9000187), Quản lý xác nhận đã nhận → Thành công, 1 hóa đơn. Sau đó webhook SePay của cùng khoản (referenceCode FT9000187) đến 2 lần: lần 1 tạo ngoại lệ \#5 'Chờ xử lý' 110.000 (coi như tiền thừa), lần 2 bỏ qua trùng. Vẫn 1 hóa đơn nhưng sinh thêm ngoại lệ cho cùng khoản, trái kỳ vọng 'không tạo thêm ngoại lệ cho cùng khoản'.                                               |
| TC-BR-07 | FR-SALE-09, 22; FR-CAT-18             | Order đã trả tiền nhưng món chưa phục vụ; khách còn ngồi                                                             | Cho cập nhật phục vụ; không đổi món/tiền; bàn chưa tự trống                                                                                                                                  | 04/11/2026 (bản 099191e, API): Bàn QA-BR07 (#7): order 377 tại chỗ 2 phần, Thu ngân thu tiền mặt → 'Đã thanh toán', hóa đơn HD-20261104-0006 20.000; dòng món vẫn 'Chờ làm', bàn vẫn 'Đang phục vụ' (không tự trống). Thu ngân cập nhật món Chờ làm → Đã xác nhận xong → Đã phục vụ: 200. Thêm món, sửa số lượng 2 → 5 và hủy dòng đều bị từ chối 422 'Order đã đóng.'; sau cùng dòng món 2 phần × 10.000 'Đã phục vụ', 1 hóa đơn 20.000 không đổi, bàn vẫn gắn order 377. |
| TC-BR-08 | FR-SALE-06, 12; FR-CAT-18             | Giải phóng bàn order cũ; bàn nhận order mới; khoản cũ được xác nhận                                                  | Không gắn lại/giải phóng bàn của order mới; không gọi thêm hoặc đổi bàn cho order cũ                                                                                                         | 04/11/2026 (bản 099191e, API+SePay mô phỏng): Bàn QA-BR08 (#8): order A 378 (30.000) tạo QR \#48 chờ tiền; Thu ngân giải phóng bàn (bàn → Trống); order B 379 mở trên bàn \#8 (bàn gắn 379). Webhook SePay khoản TT48 30.000 về: A → 'Đã thanh toán', 1 hóa đơn 30.000; bàn \#8 vẫn 'Đang phục vụ' gắn order 379 (không gắn lại cho A, không giải phóng bàn của B). Gọi thêm món cho A: 422 'Order đã đóng.'; đổi A sang bàn \#7 hoặc \#8: 422 'Order đã đóng.'.           |
| TC-BR-09 | FR-INV-05–06; FR-REP-11–13            | Bỏ 1 suất có 2 dòng nguyên liệu; ghi phiếu Món đã chế biến                                                           | Ghi 1 suất bỏ; lượng khớp tiêu hao gốc, không trừ hoặc tính chi phí lần hai                                                                                                                  | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-BR-10 | FR-INV-09; FR-REP-12                  | Kiểm kê thiếu, tạo giao dịch điều chỉnh và phiếu xuất hủy tham chiếu                                                 | Tồn giảm theo chênh lệch đúng một lần; hao hụt không cộng cả hai nguồn                                                                                                                       | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-BR-11 | FR-REP-11; tài liệu 04 G.1            | Thiếu giá tham chiếu; sau đó bổ sung dữ liệu hợp lệ cho phép tính                                                    | Trước khi có đơn giá: giá trị chưa xác định; khi có phiếu nhập hợp lệ đầu tiên, phần chưa xác định được định giá theo đơn giá bình quân đầu tiên; 0 chỉ hiển thị khi phép tính hợp lệ bằng 0 | 04/11/2026 (bản 099191e, Script+API): NL 42 chưa từng nhập (không có giá tham chiếu): kiểm kê \#105 thừa 5 → lô điều chỉnh \#82 DonGia NULL. Bán 1 suất món 24 (1 g NL 42) ngày 21/06/2027. Báo cáo chi phí không đổi, TamTinh false, SoDongChuaTinhGiaVon 0 và món 24 không có trong giá vốn theo món — không hiển thị 'chưa xác định' mà ngầm tính 0.                                                                                                                    |
| TC-BR-12 | FR-INV-03; tài liệu 04 G.1            | Xuất kho nhiều lần giữa hai phiếu nhập khác giá                                                                      | Mỗi lần xuất dùng đơn giá bình quân hiện hành tại thời điểm xuất; xuất không làm đổi đơn giá và không tạo bản ghi lịch sử giá                                                                | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-BR-13 | FR-INV-02; FR-REP-11                  | Đã có phiếu xuất hủy định giá theo đơn giá hiện hành; sau đó thêm phiếu nhập hợp lệ khác giá                         | Đơn giá bình quân cập nhật theo phiếu mới; giá trị phiếu xuất hủy đã ghi giữ nguyên; chi phí của phần đã xuất không đổi                                                                      | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-BR-14 | FR-INV-02; FR-REP-11                  | Phiếu nhập ghi nhầm ngày, lô chưa xuất/không giữ hiệu lực; sửa ngày nhập                                             | Cập nhật ngày lô, hạn dùng và thứ tự FIFO; đơn giá bình quân không đổi; giữ audit trước/sau                                                                                                  | 04/11/2026 (bản 099191e, Script): NL 35: phiếu \#73 ngày 15/06/2027 100 × 6 (lô chưa xuất, không giữ) và phiếu 03/07/2027 100 × 10. Sửa ngày phiếu \#73 sang 01/07/2027: thành công; lô \#74 NgayNhap đổi sang 2027-07-01 (thứ tự FIFO trước lô \#75). Lệch: nhật ký UPDATE_RECEIPT (#407) có DuLieuTruoc và DuLieuSau đều NULL — không giữ audit trước/sau. (NL không có số ngày bảo quản nên không có hạn dùng để đổi.)                                                  |
| TC-BR-15 | FR-INV-02; FR-REP-11                  | Hủy phiếu đủ điều kiện khi nguyên liệu đã có xuất từ lô khác                                                         | Không bị khóa; đơn giá bình quân hiện hành được tính lại sau khi đảo phiếu; giá trị đã xuất, hóa đơn và doanh thu giữ nguyên                                                                 | 04/11/2026 (bản 099191e, Script): Hủy phiếu nhập đủ điều kiện (phiếu hai dòng ở TC-BR-19, lô chưa xuất) thất bại do lỗi MySQL 3819 (ck_GIAO_DICH_KHO_movement_source_matches_kind, cùng lỗi TC-INV-05): phiếu không hủy được. Hóa đơn/doanh thu không bị ảnh hưởng.                                                                                                                                                                                                        |
| TC-BR-16 | FR-INV-02                             | Sửa phiếu khi lô đã có xuất hoặc còn giữ hiệu lực                                                                    | Từ chối toàn bộ, phiếu/lô/giá vốn không bị cập nhật dở                                                                                                                                       | 04/11/2026 (bản 099191e, Script): Phiếu NL 36 (50 × 4) đã xuất 5 → sửa thành 80 × 9 bị từ chối 'Phiếu nhập đã phát sinh xuất kho, phải điều chỉnh qua kiểm kê định kỳ.'; lô 45/50, tồn 45, bình quân 4,00 và dòng phiếu 50 × 4,00 giữ nguyên. Phiếu NL 37 (50 × 4) có lô đang được giữ (món dùng NL 37) → sửa bị từ chối 'Lô của phiếu đang được giữ chỗ, không thể sửa/hủy phiếu.'; lô/tồn không đổi.                                                                     |
| TC-BR-17 | FR-INV-09; BR-LOT-02                  | Kiểm kê thừa, không còn lô còn hạn và không có giá tham chiếu                                                        | Vẫn tạo lô điều chỉnh và tăng lượng đúng; DonGia NULL, không yêu cầu nhập giá, không tạo phiếu nhập mua; phần giá trị chưa xác định                                                          | 04/11/2026 (bản 099191e, API): Lá chanh chưa có lô và chưa có giá; kiểm kê thực tế 50 g → tạo lô điều chỉnh \#47 LoDieuChinhKiemKe=1, MaChiTietNhap NULL, HanSuDung NULL, DonGia NULL, tồn 50 g; không yêu cầu nhập giá, không tạo phiếu nhập mua.                                                                                                                                                                                                                         |
| TC-BR-18 | FR-INV-09; FR-REP-11                  | Điều chỉnh thừa khi nguyên liệu đã có đơn giá bình quân                                                              | Giá trị phần thừa = lượng thừa × đơn giá bình quân hiện hành, do hệ thống tính; không cộng lượng thừa vào nhập mua; đơn giá bình quân không đổi                                              | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-BR-19 | FR-INV-02; tài liệu 04 F.21           | Phiếu có hai dòng tạo hai lô chưa xuất, không còn giữ hiệu lực; hủy phiếu                                            | Đảo đúng lượng nhập của cả hai lô, lượng còn lại bằng 0, trạng thái Đã hủy; phiếu/lô/lịch sử còn truy vết; đơn giá bình quân hiện hành được tính lại                                         | 04/11/2026 (bản 099191e, Script): Phiếu hai dòng (NL 39: 20 × 7, NL 40: 30 × 8) tạo lô \#78, \#79 chưa xuất, không còn giữ. Hủy phiếu: lỗi MySQL 3819 vi phạm ràng buộc ck_GIAO_DICH_KHO_movement_source_matches_kind (cùng lỗi TC-INV-05); phiếu vẫn 'Hiệu lực', hai lô giữ 20/20 và 30/30 'Còn hạn'.                                                                                                                                                                     |
| TC-BR-20 | FR-INV-05; BR-LOT-01                  | Lô còn hạn có 10 đơn vị; xuất hủy 3 đơn vị nguyên liệu                                                               | Lô còn 7 đơn vị, không mang trạng thái Đã hủy; 7 đơn vị tiếp tục đủ điều kiện phân bổ nếu không bị giữ; hao hụt ghi đúng một lần                                                             | 04/11/2026 (bản 099191e, Script+API): NL 38: lô \#72 nhập 10 × 5 (06/2027); phiếu xuất hủy 3 đơn vị → lô còn 7/10, trạng thái 'Còn hạn' (không Đã hủy), tồn 7; 1 giao dịch xuất; GiaVonUocTinh 15,00; Hao hụt tháng 06/2027 10,50 → 25,50 (tăng đúng 15 một lần). 7 đơn vị còn lại vẫn là lô hợp lệ (được dùng tiếp ở BR-13).                                                                                                                                              |
| TC-BR-21 | FR-INV-02, FR-INV-09; F.21            | Thử giữ món, xuất FIFO hoặc cộng chênh lệch kiểm kê vào lô Đã hủy                                                    | Không chọn lô Đã hủy; kiểm kê thừa dùng lô hợp lệ khác hoặc tạo lô điều chỉnh theo BR-LOT-02, không khôi phục lô đã hủy                                                                      | 04/11/2026 (bản 099191e, Script): Không tạo được lô 'Đã hủy' qua ứng dụng: hủy phiếu nhập (đường duy nhất sinh lô Đã hủy) lỗi MySQL 3819 ở TC-INV-05/TC-BR-19, nên không có dữ liệu đầu vào để thử giữ món, xuất FIFO hay cộng chênh lệch kiểm kê vào lô Đã hủy. Chặn bởi lỗi TC-INV-05; chạy lại khi lỗi hủy phiếu được sửa.                                                                                                                                              |
| TC-BR-22 | FR-REP-11; tài liệu 04 G.1            | Hai lần nhập 1 × 4 và 2 × 3 cho đơn giá bình quân trước làm tròn 10/3; xuất 3 đơn vị chuẩn                           | Lưu đơn giá 3,33; giá vốn dòng xuất 9,99 theo ROUND_HALF_UP; lượng vẫn theo độ chính xác sáu chữ số                                                                                          | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-BR-23 | FR-REP-11; tài liệu 04 G.1            | Đơn giá bình quân 1,01; xuất 0,5 đơn vị; giá trị trước làm tròn 0,505                                                | GiaVonUocTinh bằng 0,51 theo ROUND_HALF_UP; đơn giá lưu giữ 1,01; không tạo thêm biến động kho                                                                                               | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-BR-24 | FR-INV-04; tài liệu 04 G.1            | Tồn 150 đơn vị, đơn giá bình quân 15.000 đ; dòng Chờ làm đã tiêu hao 20 đơn vị khi đơn giá là 12.000 đ; hủy dòng món | Hoàn 20 đơn vị về lô gốc theo đơn giá 12.000 đ; đơn giá bình quân mới = (150 × 15.000 + 20 × 12.000)/170 = 14.647,06 đ; một bản ghi lịch sử giá mới                                          | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| TC-BR-25 | FR-INV-09; FR-REP-11; tài liệu 04 G.1 | Nguyên liệu chưa có đơn giá: lô điều chỉnh 5 đơn vị, một dòng tiêu hao 1 đơn vị; sau đó nhập 5 × 6                   | Trước khi nhập: giá trị chưa xác định; sau khi nhập: đơn giá bình quân 6,00, dòng tiêu hao trước đó được định giá 6,00 một lần; không tạo biến động kho mới                                  | Chưa kiểm tra.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |

## I. Nhận xét

Trên bản 099191e: 202 đạt, 21 không đạt, 1 bị chặn (TC-BR-21) và 34 chưa kiểm tra trên tổng 258 ca. Các ca không đạt: TC-INV-09, TC-SALE-19, TC-CAT-03, TC-CAT-10, TC-SALE-32, TC-SET-01, TC-SET-09, TC-CAT-13, TC-CAT-16, TC-SALE-13, TC-SALE-70, TC-BR-06, TC-INV-05, TC-REP-08, TC-REP-09, TC-REP-07, TC-BR-14, TC-BR-19, TC-BR-15, TC-BR-11, TC-SALE-61. Các ca chưa kiểm tra gồm TC-CAT-49–51; TC-INV-19, 21–23, 41–45, 49, 52–57; TC-REP-04–06, 11–13; TC-BR-09, 10, 12, 13, 18, 22–25. Hiệu năng cơ bản chưa được đo trên bộ dữ liệu 2 tháng (mục G).

## J. Lỗi chức năng đang ghi nhận

Các lỗi dưới đây được ghi nhận khi chạy trên bản 099191e ngày 03–04/11/2026; cần kiểm tra lại sau khi dev sửa.

| **Mã ca**  | **Lỗi ghi nhận**                                                                                                                                                                                                        | **Trạng thái** |
|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| TC-INV-09  | Lượt giữ đủ 150 g của chính dòng món vẫn bị từ chối khi gửi nếu khả dụng chung còn lại bằng 0 ("Món đang hết nguyên liệu."). Lỗi cũng chặn gửi ở các món có lượt giữ chiếm hết phần khả dụng (Gà xào, Ốc xào, Vịt xào). | Không đạt      |
| TC-SALE-19 | Order tại chỗ đã rời bàn vẫn tạo được lượt giữ gọi thêm qua API giữ món (giữ nguyên liệu tới khi hết hạn); bước gửi bị chặn.                                                                                            | Không đạt      |
| TC-CAT-03  | Sắp xếp nhóm món bị từ chối (HTTP 422) do giao diện gửi mảng mã nhóm thay vì đối tượng {MaNhomMon}; thứ tự không đổi.                                                                                                   | Không đạt      |
| TC-CAT-10  | Sau khi xóa mềm món, chi tiết order cũ hiển thị "Món \#13" thay cho tên món; hóa đơn vẫn đúng tên.                                                                                                                      | Không đạt      |
| TC-SALE-32 | Giảm suất món Chờ làm hoàn đúng nguyên liệu nhưng giao diện không có bước nhập lý do; nhật ký không có lý do.                                                                                                           | Không đạt      |
| TC-SET-01  | Tạo tài khoản trả HTTP 500 dù bản ghi đã lưu; giao diện báo lỗi kết nối, hộp thoại không đóng.                                                                                                                          | Không đạt      |
| TC-SET-09  | Một số loại bản ghi nhật ký không lưu dữ liệu trước/sau (đặt lại mật khẩu, tạo/đổi tên nhóm món).                                                                                                                       | Không đạt      |
| TC-CAT-13  | Hộp thoại Thêm nguyên liệu giữ giá trị lần thêm trước; nguyên liệu mới bị lưu ngưỡng 500 thay vì dùng mặc định.                                                                                                         | Không đạt      |
| TC-CAT-16  | Tổng tiền phiếu nhập (PHIEU_NHAP_KHO.TongTien) không được tính, lịch sử nhập của nhà cung cấp hiện 0 ₫.                                                                                                                 | Không đạt      |
| TC-SALE-13 | Gửi lượt chọn đã hết hạn khi thiếu nguyên liệu bị từ chối đúng nhưng thông báo không nêu món và số lượng thiếu.                                                                                                         | Không đạt      |
| TC-SALE-70 | Chi tiết order trong Quản lý đơn hàng không hiển thị lịch sử thanh toán (QR, mã tham chiếu, xác minh).                                                                                                                  | Không đạt      |
| TC-BR-06   | Sau khi Quản lý xác nhận đã nhận tiền, webhook của cùng khoản vẫn tạo thêm một ngoại lệ thanh toán.                                                                                                                     | Không đạt      |
| TC-INV-05  | Hủy phiếu nhập chưa xuất/giữ trả HTTP 500 (vi phạm ràng buộc ck_GIAO_DICH_KHO_movement_source_matches_kind); giao diện báo lỗi kết nối, phiếu không hủy được.                                                           | Không đạt      |
| TC-REP-08  | Màn So sánh không hiển thị chênh lệch doanh thu tuyệt đối khi có tỷ lệ phần trăm (100.000 → 120.000 chỉ ghi "Tăng 20%", thiếu +20.000 ₫).                                                                               | Không đạt      |
| TC-REP-09  | Khung "Món bán chạy" trên tab Doanh thu không gửi mốc kỳ đang chọn, luôn hiện món của kỳ hiện tại nên không khớp với doanh thu kỳ đang xem.                                                                             | Không đạt      |
| TC-REP-07  | Báo cáo theo ngày trong tuần tính theo ngày lịch (một Business Date bị tách thành hai thứ) và doanh thu theo ngày trong tuần luôn bằng 0 ₫.                                                                             | Không đạt      |
| TC-BR-14   | Sửa ngày phiếu nhập ghi nhật ký UPDATE_RECEIPT nhưng không lưu dữ liệu trước/sau.                                                                                                                                       | Không đạt      |
| TC-BR-19   | Hủy phiếu nhập hai dòng thất bại (MySQL 3819), cùng nguyên nhân TC-INV-05; lô không được đảo.                                                                                                                           | Không đạt      |
| TC-BR-15   | Hủy phiếu nhập đủ điều kiện thất bại (MySQL 3819), cùng nguyên nhân TC-INV-05.                                                                                                                                          | Không đạt      |
| TC-BR-11   | Khi nguyên liệu chưa có giá tham chiếu, báo cáo không đánh dấu giá trị chưa xác định (ngầm tính 0, không đếm dòng chưa tính).                                                                                           | Không đạt      |
| TC-SALE-61 | Lượt gửi phần gọi thêm bị từ chối đúng nhưng thông báo "Món đang hết nguyên liệu." không chỉ rõ dòng/món cần kiểm tra lại.                                                                                              | Không đạt      |
