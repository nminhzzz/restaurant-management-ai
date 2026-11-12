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

Kết quả chạy trên bản 6985565 ngày 10/11/2026, môi trường thử riêng với cơ sở dữ liệu QA riêng; ca giao diện được thao tác trực tiếp trên giao diện, các ca còn lại qua API và script: 256 đạt, 2 không đạt trên tổng 258 ca. Theo nhóm: Danh mục 51/51 (51 đạt); Bán hàng 101/101 (100 đạt, 1 không đạt); Kho 57/57 (57 đạt); Cài đặt 9/9 (8 đạt, 1 không đạt); Báo cáo 15/15 (15 đạt); điều kiện biên 25/25 (25 đạt).

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
<td>10/11/2026 (bản 6985565, UI): Quản lý mở Danh mục → Nhóm món → Thêm nhóm, nhập 'Món nướng', Lưu; tải lại trang, tab Nhóm món hiển thị đúng 'Món nướng' (1 nhóm).</td>
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
<td>10/11/2026 (bản 6985565, API): Đổi tên nhóm #1 'Món nướng' thành 'Món nướng than': 200; đọc lại danh sách, mã nhóm vẫn #1, ThuTuHienThi giữ 1; món Gà nướng thêm vào nhóm sau đó vẫn thuộc nhóm #1.</td>
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
<td>10/11/2026 (bản 6985565, UI): Nhóm theo thứ tự Món nướng than, A, B, C, Món chính; bấm 'Di chuyển lên' ở nhóm C hai lần: danh sách thành Món nướng than, C, A, B, Món chính; CSDL ThuTuHienThi C=2, A=3, B=4 (lưu bền).</td>
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
<td>10/11/2026 (bản 6985565, API): Thêm Bò nướng giá 120.000 đ, nhóm Món nướng than, ảnh URL hợp lệ: 201, trạng thái Nháp, ChuaCoCongThuc=1, thuộc đúng một nhóm (#1). API danh sách món cho Thu ngân trả TrangThai 'Nháp', 0 suất; màn gọi món loại món Nháp khỏi danh sách bán.</td>
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
<td>10/11/2026 (bản 6985565, API): Sửa Bò nướng thành 'Bò nướng tảng', ảnh mới, nhóm Món chính (#5): 200; đọc lại đúng tên, ảnh, MaNhomMon=5; món chỉ thuộc nhóm #5.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-06</td>
<td>FR-CAT-02</td>
<td>Có Bò nướng và Gà nướng.</td>
<td>1. Tìm tên Bò.</td>
<td>Kết quả có Bò nướng, không có Gà nướng.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Có Bò nướng tảng và Gà nướng; tìm 'Bò' (search): chỉ trả Bò nướng tảng, không có Gà nướng.</td>
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
<td>10/11/2026 (bản 6985565, API): Nhóm #1 còn Gà nướng chưa xóa: xóa nhóm → 422 'Không thể xóa nhóm còn món đang hoạt động.'; nhóm DaXoa=0, món giữ nguyên nhóm.</td>
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
<td>10/11/2026 (bản 6985565, API): Nhóm A (#2) chỉ có Món tạm đã xóa mềm: xóa nhóm → 204, NHOM_MON DaXoa=1 (xóa mềm), nhật ký DELETE_GROUP KieuXoa 'Xóa mềm'; tạo món mới vào nhóm #2 bị từ chối 422 'Nhóm món không tồn tại.'; Món tạm vẫn tra cứu được với MaNhomMon=2. Ghi chú: NgayXoa để NULL (PH-03).</td>
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
<td>10/11/2026 (bản 6985565, API): Nhóm B (#3) chưa từng có món: xóa → 204, bản ghi NHOM_MON #3 bị xóa vĩnh viễn; nhật ký DELETE_GROUP đối tượng NHOM_MON #3.</td>
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
<td>10/11/2026 (bản 6985565, UI+API): Gà xào 04 (#26) đã có trong order lịch sử ORD-101126-407: Quản lý xóa món → 204, MON_AN DaXoa=1 (xóa mềm), nhật ký DELETE_DISH; danh sách món cho Thu ngân không còn món; giữ món bị 422 'Món không tồn tại hoặc đã bị xóa.'; danh sách quản trị có 'Hiện món đã xóa' vẫn tra cứu được; chi tiết order cũ trên màn Quản lý đơn hàng hiển thị đúng tên 'Gà xào 04' ở dòng món và hóa đơn (không còn hiện mã như đợt 03/11). Không có thao tác xóa vĩnh viễn.</td>
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
<td>10/11/2026 (bản 6985565, API): Bò nướng tảng ở trạng thái Nháp; Thịt bò còn hạn 490 g. Gán công thức Thịt bò 150 g/suất → 201 #53 'Đang áp dụng' ngay; ChuaCoCongThuc=0; danh sách món cho Thu ngân hiện 'Hoạt động', 3 suất khả dụng; giữ 1 suất thành công (201).</td>
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
<td>10/11/2026 (bản 6985565, UI): Bếp mở Danh mục → Nguyên liệu → Thêm nguyên liệu, nhập Thịt bò, đơn vị g, mức tồn tối thiểu 500, bảo quản 5 ngày, Lưu: báo 'Đã thêm nguyên liệu.'; danh sách và CSDL đúng tên, đơn vị g, ngưỡng 500.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-13</td>
<td>FR-CAT-12</td>
<td>Ngưỡng mặc định 300 g.</td>
<td>1. Thêm Hành không đặt ngưỡng riêng.</td>
<td>Nguyên liệu dùng ngưỡng mặc định 300 g.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, UI): Ngưỡng mặc định cấu hình 300. Ngay sau khi thêm Thịt bò, mở lại Thêm nguyên liệu: các ô đều trống (đã reset). Thêm Hành, đơn vị g, bỏ trống ngưỡng: báo 'Đã thêm nguyên liệu.'; danh sách hiện 'Mặc định', CSDL MucTonToiThieu NULL nên dùng ngưỡng mặc định 300.</td>
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
<td>10/11/2026 (bản 6985565, API): Bếp đổi tên Hành thành 'Hành lá': 200; tìm 'Hành lá' trả đúng nguyên liệu #2.</td>
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
<td>10/11/2026 (bản 6985565, API): Bếp thêm NCC A kèm số điện thoại, email, người liên hệ, địa chỉ: 201, trả đủ thông tin đã nhập.</td>
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
<td>10/11/2026 (bản 6985565, UI+API): NCC A có phiếu nhập #1 (Thịt bò 1.000 g × 200 đ). Sửa số điện thoại và người liên hệ: 200, lưu đúng. Mở 'Xem lịch sử nhập hàng' trên tab Nhà cung cấp: 'Phiếu nhập #1 · 10/11/2026 · Hiệu lực · 200.000 ₫' (tổng tiền đúng). Ghi chú: phản hồi của lệnh PATCH trả PhieuNhap rỗng, GET chi tiết trả đúng (PH-02).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-17</td>
<td>FR-CAT-14</td>
<td>Nguyên liệu đã có phiếu nhập, chưa có công thức.</td>
<td>1. Thử đổi đơn vị g sang kg.</td>
<td>Từ chối đổi đơn vị; dữ liệu cũ giữ nguyên.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Thịt bò đã có phiếu nhập #1, chưa có công thức: đổi đơn vị g→kg bị 422 'Không thể đổi đơn vị tính sau khi đã được sử dụng.'; CSDL giữ g.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-18</td>
<td>FR-CAT-14</td>
<td>Nguyên liệu đã có trong công thức, chưa có phiếu nhập.</td>
<td>1. Thử đổi đơn vị g sang kg.</td>
<td>Từ chối đổi đơn vị; dữ liệu cũ giữ nguyên.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Tỏi có trong công thức Gà nướng tỏi (#1), chưa có phiếu nhập: đổi đơn vị g→kg bị 422 cùng thông báo; CSDL giữ g.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-19</td>
<td>FR-CAT-13</td>
<td>Nguyên liệu đã có trong công thức.</td>
<td>1. Xóa nguyên liệu.</td>
<td>Chỉ xóa mềm; dữ liệu tham chiếu lịch sử còn nguyên; có audit log.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Tỏi có trong công thức Gà nướng tỏi: Bếp xóa nguyên liệu → 204; NGUYEN_LIEU DaXoa=1 (xóa mềm); CHI_TIET_CONG_THUC #1 vẫn tham chiếu Tỏi 10 g, API công thức vẫn hiển thị tên Tỏi; nhật ký DELETE_INGREDIENT.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-20</td>
<td>FR-CAT-13</td>
<td>Nguyên liệu đã có phiếu nhập lịch sử.</td>
<td>1. Xóa nguyên liệu.</td>
<td>Chỉ xóa mềm; dữ liệu tham chiếu lịch sử còn nguyên; có audit log.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Nấm (#11) có phiếu nhập #2: xóa nguyên liệu → 204, DaXoa=1; dòng nhập #2 còn nguyên, chi tiết phiếu nhập #2 vẫn hiện tên Nấm; nhật ký DELETE_INGREDIENT.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-21</td>
<td>FR-CAT-16</td>
<td>Nhà cung cấp có lịch sử nhập hàng.</td>
<td>1. Xóa nhà cung cấp.</td>
<td>Chỉ xóa mềm; phiếu nhập cũ vẫn tham chiếu được; có audit log.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): NCC Z có phiếu nhập #3: xóa nhà cung cấp → 204; NHA_CUNG_CAP DaXoa=1 (xóa mềm); phiếu nhập #3 vẫn đọc được với MaNhaCungCap=2; nhật ký DELETE_SUPPLIER.</td>
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
<td>10/11/2026 (bản 6985565, Script): Bò xào giá 100.000 (#5), lịch 110.000 (#8) cho Business Date 11/11, mốc 06:00. Gửi order mang về qua tầng service với đồng hồ đặt 05:59:59 ngày 11/11 → order #1 Business Date 10/11, DonGia 100.000, MaPhienBanGia #5; lúc 06:00:00 → order #2 Business Date 11/11, DonGia 110.000, phiên bản #8. Dòng cũ giữ nguyên. Ghi chú: mốc 06:00 được giả lập bằng business_date.at_time, không chờ giờ thật.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-23</td>
<td>FR-CAT-20</td>
<td>Có món Bò xào.</td>
<td>1. Lên lịch giá vào Business Date đã bắt đầu.</td>
<td>Từ chối lưu lịch; không thay đổi phiên bản đang áp dụng.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Business Date hiện tại 10/11 đã bắt đầu: lên lịch giá 95.000 cho Bò xào ngày 10/11 → 422 'BusinessDate áp dụng phải là ngày trong tương lai.'; giá đang áp dụng 100.000 (#5) không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-24</td>
<td>FR-CAT-20</td>
<td>Có món Bò xào.</td>
<td>1. Lên lịch giá vào Business Date đã kết thúc.</td>
<td>Từ chối lưu lịch; không thay đổi phiên bản đang áp dụng.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Lên lịch giá cho Business Date 09/11 (đã kết thúc) → 422 cùng thông báo; phiên bản đang áp dụng không đổi.</td>
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
<td>10/11/2026 (bản 6985565, API): Lên lịch giá 105.000 cho Business Date 15/11 (sau ngày kế tiếp): 201, phiên bản #6 'Chờ áp dụng' đúng ngày 15/11; giá đang áp dụng vẫn 100.000 (#5).</td>
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
<td>10/11/2026 (bản 6985565, API): Có lịch A (#6, 105.000, 15/11) đang chờ; tạo lịch B 108.000 ngày 16/11: 201 #7; danh sách chỉ còn một lịch chờ (#7), #6 bị ghi đè; nhật ký SCHEDULE_PRICE_CHANGE ghi LichBiGhiDe [#6, 105.000, 15/11].</td>
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
<td>10/11/2026 (bản 6985565, API): Hủy lịch giá #7 đang chờ: 204; chỉ còn phiên bản đang áp dụng #5 (100.000); nhật ký CANCEL_PRICE_CHANGE ghi dữ liệu trước (108.000, 16/11, Chờ áp dụng).</td>
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
<td>10/11/2026 (bản 6985565, API): Mực xào giá 80.000 (#10), lịch 90.000 cho 14/11 (#11) đang chờ. Sửa trực tiếp giá 85.000: 201 #12 'Đang áp dụng', #10 Hết hiệu lực, lịch #11 vẫn 'Chờ áp dụng'; nhật ký APPLY_PRICE_DIRECTLY. Gửi 1 Mực xào mang về (order #3): DonGia 85.000, phiên bản #12. Ghi chú: trên Bò xào, lịch #8 đã bị dòng gửi giả lập lúc 06:00 ngày 11/11 sử dụng nên bị thay thế khi sửa trực tiếp; phép thử sạch được làm lại trên Mực xào.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-29</td>
<td>FR-CAT-05</td>
<td>Món có lịch giá đang chờ.</td>
<td>1. Xóa mềm món.</td>
<td>Lịch chờ tương ứng bị hủy.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Món thử xóa (#7) có lịch giá 55.000 cho 14/11 (#14) đang chờ; xóa mềm món → 204; lịch #14 chuyển 'Hết hiệu lực' (bị hủy), phiên bản đang áp dụng không đổi; nhật ký DELETE_DISH.</td>
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
<td>10/11/2026 (bản 6985565, Script): Cùng lượt với CAT-22: công thức 150 g (#2), lịch 180 g (#5) cho Business Date 11/11. Dòng gửi lúc 05:59:59 dùng công thức #2, trừ 150 g (GiaTri −30.000 đ); dòng gửi lúc 06:00:00 dùng #5, trừ 180 g (−36.000 đ); dòng cũ không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-31</td>
<td>FR-CAT-08</td>
<td>Có món Bò xào.</td>
<td>1. Lên lịch công thức vào Business Date đã bắt đầu.</td>
<td>Từ chối lưu lịch; không thay đổi phiên bản đang áp dụng.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Lên lịch công thức Bò xào 160 g cho Business Date 10/11 (đã bắt đầu) → 422 'BusinessDate áp dụng phải là ngày trong tương lai.'; công thức đang áp dụng #2 (150 g) không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-32</td>
<td>FR-CAT-08</td>
<td>Có món Bò xào.</td>
<td>1. Lên lịch công thức vào Business Date đã kết thúc.</td>
<td>Từ chối lưu lịch; không thay đổi phiên bản đang áp dụng.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Lên lịch công thức cho Business Date 09/11 (đã kết thúc) → 422 cùng thông báo; công thức đang áp dụng không đổi.</td>
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
<td>10/11/2026 (bản 6985565, API): Lên lịch công thức Bò xào 160 g cho Business Date 15/11: 201 #3 'Chờ áp dụng' đúng ngày; công thức đang áp dụng vẫn #2 (150 g).</td>
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
<td>10/11/2026 (bản 6985565, API): Có lịch công thức A (#3, 15/11) đang chờ; tạo lịch B 170 g ngày 16/11: 201 #4; chỉ còn một lịch chờ (#4), #3 không còn trong danh sách; nhật ký SCHEDULE_RECIPE_CHANGE ghi LichBiGhiDe [#3, 160 g, 15/11].</td>
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
<td>10/11/2026 (bản 6985565, API): Hủy lịch công thức #4 đang chờ: 204; chỉ còn công thức đang áp dụng #2 (150 g); nhật ký CANCEL_RECIPE_CHANGE.</td>
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
<td>10/11/2026 (bản 6985565, API): Mực xào công thức 150 g (#7), lịch 170 g cho 14/11 (#8) đang chờ. Sửa trực tiếp công thức 160 g: 201 #9 'Đang áp dụng', #7 Hết hiệu lực, lịch #8 vẫn 'Chờ áp dụng'; nhật ký APPLY_RECIPE_DIRECTLY. Order #3 dùng công thức #9, trừ 160 g.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-37</td>
<td>FR-CAT-05</td>
<td>Món có lịch công thức đang chờ.</td>
<td>1. Xóa mềm món.</td>
<td>Lịch chờ tương ứng bị hủy.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Cùng món #7 có lịch công thức 120 g cho 14/11 (#11) đang chờ; sau khi xóa mềm món, lịch #11 chuyển 'Hết hiệu lực'.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-38</td>
<td>FR-CAT-26, FR-CAT-27</td>
<td>Món đủ nguyên liệu, đang phục vụ.</td>
<td>1. Bật tạm dừng thủ công.</td>
<td>Hiển thị Tạm dừng phục vụ; không cho thêm món.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Mực xào đủ nguyên liệu (5 suất): Quản lý bật tạm dừng thủ công → 200, TrangThai 'Tạm dừng phục vụ'; danh sách cho Thu ngân hiện 'Tạm dừng phục vụ' (vẫn 5 suất); giữ món bị 422 'Món đang tạm dừng phục vụ.'.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-39</td>
<td>FR-CAT-26, FR-CAT-27</td>
<td>Món tạm dừng thủ công và đủ nguyên liệu.</td>
<td>1. Tắt tạm dừng thủ công.</td>
<td>Món được mở lại và cho thêm vào lượt chọn.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Tắt tạm dừng thủ công Mực xào → TrangThai 'Hoạt động'; Thu ngân giữ 1 suất được (201, lượt giữ #4).</td>
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
<td>10/11/2026 (bản 6985565, UI+API): Gà nướng sả (công thức Gà 200 g, Gà chưa nhập kho) và bật tạm dừng thủ công: danh sách món của Quản lý hiện đồng thời 'Hết nguyên liệu' và 'Tạm dừng thủ công'; giữ món bị 422 'Món đang hết nguyên liệu và tạm dừng phục vụ.'. Tắt tạm dừng: TrangThai vẫn 'Hết nguyên liệu', giữ món vẫn 422 'Món đang hết nguyên liệu.'.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-41</td>
<td>FR-CAT-27</td>
<td>Món đã có công thức; khả dụng không đủ một suất.</td>
<td>1. Xem trạng thái và thử thêm món.</td>
<td>Hiển thị Hết nguyên liệu, chặn thêm; thuộc tính này được suy ra, không lưu trong MON_AN.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, UI+API): Gà nướng tỏi có công thức Tỏi 10 g/suất, Tỏi chưa có tồn (khả dụng 0): danh mục hiện 'Hết nguyên liệu – 0 suất khả dụng'; giữ món bị 422 'Món đang hết nguyên liệu.'; MON_AN chỉ có MaMon, TenMon, MaNhomMon, DaXoa, HinhAnh, ChuaCoCongThuc, TamDungThuCong — trạng thái hết nguyên liệu được suy ra, không lưu.</td>
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
<td>10/11/2026 (bản 6985565, API): Thêm bàn B1 (Tầng 1, 4 chỗ): 201, TrangThai 'Trống', MaOrderDangPhucVu NULL.</td>
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
<td>10/11/2026 (bản 6985565, API): Sửa tên B1 thành B01: 200; MaBan vẫn #1, trạng thái Trống.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-44</td>
<td>FR-CAT-17, FR-CAT-19</td>
<td>Bàn đang phục vụ order O1.</td>
<td>1. Thử xóa bàn.</td>
<td>Từ chối; bàn vẫn gắn O1.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): B5 đang phục vụ order #412; xóa bàn → 422 'Không thể xóa bàn đang được sử dụng.'; B5 vẫn Đang phục vụ, gắn #412, DaXoa=0.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-45</td>
<td>FR-CAT-19</td>
<td>Bàn Trống, đã có order lịch sử.</td>
<td>1. Xóa bàn.</td>
<td>Chỉ xóa mềm; giữ tham chiếu lịch sử và ghi audit log.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): B7 Trống, đã có order lịch sử #421; xóa bàn → 204; BAN DaXoa=1, TenBan_Active NULL (cho phép dùng lại tên), TenBan giữ 'B7'; order #421 vẫn tham chiếu MaBan 7; nhật ký DELETE_TABLE.</td>
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
<td>10/11/2026 (bản 6985565, API): Thịt bò ngưỡng riêng 500; PATCH MucTonToiThieu=-1 → 422 (phải ≥ 0); CSDL giữ 500.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-47</td>
<td>NFR-04</td>
<td>Đăng nhập vai trò Bếp.</td>
<td>1. Gọi trực tiếp API sửa giá món với dữ liệu hợp lệ.</td>
<td>Backend từ chối quyền; dữ liệu không thay đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Bếp gọi trực tiếp POST /catalog/dishes/5/prices/apply-now và /prices/schedule với dữ liệu hợp lệ: 403; LICH_SU_GIA_MON của Bò xào không thêm phiên bản (3 bản ghi như trước).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-48</td>
<td>NFR-04</td>
<td>Đăng nhập vai trò Thu ngân.</td>
<td>1. Gọi trực tiếp API thêm bàn với dữ liệu hợp lệ.</td>
<td>Backend từ chối quyền; dữ liệu không thay đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Thu ngân gọi POST /catalog/tables tạo B99: 403; bảng BAN vẫn 1 bản ghi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-49</td>
<td>FR-CAT-29</td>
<td>Bò xào giá bán 80.000 đ; công thức 150 g bò (đơn giá bình quân 230.000 đ/kg) và 50 g hành (40.000 đ/kg); TyLeGiaVonCanhBao = 40%.</td>
<td>1. Đăng nhập Quản lý, mở danh sách món.2. Chọn Bò xào để xem chi tiết giá vốn.</td>
<td>Giá vốn ước tính 36.500 đ (34.500 + 2.000); tỷ lệ giá vốn 45,6%; lãi gộp 43.500 đ/suất; món được đánh dấu cảnh báo; chi tiết hiển thị hai nguyên liệu với định lượng, đơn giá và thành tiền.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, UI+API): Bò xào hành giá 80.000, công thức Bò thăn 150 g (bình quân 230 đ/g) + Hành tây 50 g (40 đ/g), ngưỡng 40%. Danh sách món (Quản lý): giá vốn 36.500 ₫, tỷ lệ 45,6%, lãi gộp 43.500 ₫, nhãn 'Vượt 40,0%'. Chi tiết món: bảng nguyên liệu 150 g × 230 ₫ = 34.500 ₫; 50 g × 40 ₫ = 2.000 ₫. Nhập giá mới 100.000 trong ô Giá mới: hiển thị ngay tỷ lệ 36,5%. API danh sách món cho Thu ngân không có trường giá vốn; /catalog/dishes/costs và /dishes/9/cost với Thu ngân, Bếp trả 403.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-CAT-50</td>
<td>FR-CAT-29, FR-INV-02</td>
<td>Như TC-CAT-49 nhưng đơn giá bình quân của bò là 180.000 đ/kg: giá vốn 29.000 đ, tỷ lệ 36,25%, chưa cảnh báo.</td>
<td>1. Nhập kho bò với giá cao hơn để đơn giá bình quân tăng lên 230.000 đ/kg.2. Mở lại danh sách món.</td>
<td>Giá vốn của Bò xào cập nhật thành 36.500 đ, tỷ lệ 45,6% và có cảnh báo; giá bán vẫn 80.000 đ, hệ thống không tự đổi giá bán.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API+UI): Bò thăn nhập 1.000 g × 180 đ (bình quân 180): Bò xào hành giá vốn 29.000, tỷ lệ 36,25%, CanhBao=false. Nhập tiếp 1.000 g × 280 đ: bình quân (1.000×180 + 1.000×280)/2.000 = 230; mở lại danh sách món: 36.500, 45,63% (hiển thị 45,6%), CanhBao=true, nhãn 'Vượt 40,0%'.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-CAT-51</td>
<td>FR-CAT-29</td>
<td>Công thức Gỏi gà có Sả, nguyên liệu chưa có đơn giá bình quân.</td>
<td>1. Mở danh sách món, tìm Gỏi gà.</td>
<td>Cột giá vốn hiển thị “Chưa đủ dữ liệu” kèm tên Sả; không tính Sả bằng 0; không hiển thị tỷ lệ giá vốn hay cảnh báo cho món.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, UI+API): Gỏi gà: công thức Gà 100 g (đã có đơn giá 90) + Sả 10 g (chưa từng nhập): danh sách hiện 'Chưa đủ dữ liệu: Sả', cột tỷ lệ và lãi gộp '—', không có nhãn cảnh báo; API TinhTrang 'Chưa đủ dữ liệu', GiaVonUocTinh null, ThanhTien của Sả null (không tính 0).</td>
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
<td>10/11/2026 (bản 6985565, UI): Thu ngân chọn bàn B01 (Trống), chạm Bò xào S 2 lần: lượt chọn 2 suất. CSDL: lượt giữ #815, người dùng #2, mã lượt chọn, bàn #1, chưa có MaOrder, phiên bản giá #30 và công thức #28, hạn giữ 5 phút; giữ 300 g (lô #41 200 g + lô #42 100 g); tồn 1.000 g, khả dụng 700 g; B01 vẫn Trống, chưa gắn order, chưa có phiếu bếp. Ghi chú: ô món vẫn hiện 'Còn 6 suất' sau khi giữ 2 suất.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-02</td>
<td>FR-SALE-01, FR-INV-10</td>
<td>Bò khả dụng 149 g; công thức 150 g/suất.</td>
<td>1. Thêm 1 suất Bò xào.</td>
<td>Từ chối, không tạo lượng giữ.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Bò 02 khả dụng 149 g, công thức 150 g: giữ 1 suất → 422 'Món đang hết nguyên liệu.'; không tạo lượt giữ (0), khả dụng vẫn 149.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-03</td>
<td>FR-SALE-01, FR-INV-10</td>
<td>Bò khả dụng 150 g; công thức 150 g/suất.</td>
<td>1. Thêm 1 suất Bò xào.</td>
<td>Giữ thành công 150 g; khả dụng còn 0 g, tồn sổ sách không đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Bò 03 khả dụng 150 g: giữ 1 suất → 201; SoLuongGiu 150, khả dụng 0, tồn sổ sách vẫn 150.</td>
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
<td>10/11/2026 (bản 6985565, API): Gà xào 04 tại B4, giữ 1 suất kèm ghi chú 'không hành', gửi: dòng món GhiChu 'không hành'; phiếu bếp in 'Gà xào 04 x1 (không hành)'; trừ kho −150 g đúng định lượng chuẩn.</td>
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
<td>10/11/2026 (bản 6985565, API): Gửi 1 Gà xào 04 mang về, không ghi chú: 201; GhiChu NULL; phiếu bếp 'Gà xào 04 x1'; trừ −150 g theo định lượng chuẩn.</td>
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
<td>10/11/2026 (bản 6985565, UI): B01, lượt chọn giữ 2 suất; Bò S lô L1 #41 (nhập 09/11) 200 g, L2 #42 800 g. Bấm Gửi bếp: báo 'Đã gửi món của B01 xuống bếp.'; một order #407 ORD-101126-406, một dòng 2 suất 100.000 'Chờ làm'; sổ kho 'Trừ tự động' −200 g lô #41 và −100 g lô #42 (giá trị −40.000, −20.000); lượt giữ 'Đã gửi'; B01 'Đang phục vụ', MaOrderDangPhucVu=407; phiếu bếp #209 nội dung 'Bò xào S x2', trạng thái 'Chờ in' (môi trường QA không cấu hình máy in).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-07</td>
<td>FR-SALE-03</td>
<td>Lần gửi đã commit nhưng phía người dùng timeout.</td>
<td>1. Gửi lại cùng mã yêu cầu.</td>
<td>Trả kết quả cũ; chỉ một order, không trừ kho hoặc tạo dòng món lần hai.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Gửi order mang về với request_id X → 201 order #410; gửi lại tuần tự đúng nội dung và X (giả lập timeout) → 201 trả cùng MaOrder 410; chỉ 1 ORDER mang mã X, 1 dòng món; số giao dịch kho của nguyên liệu không đổi (4→4).</td>
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
<td>10/11/2026 (bản 6985565, Script): Lượt chọn giữ 2 suất (300 g). Tiêm lỗi vào bước ghi phiếu bếp — sau khi đã trừ kho trong transaction (thấy 2 giao dịch kho trong phiên), trước commit — rồi gửi: lỗi 'QA tiêm lỗi…'; sau rollback số giao dịch kho (438) và số order (302) không đổi; tồn 1.000 g, lô 1.000 g, lượt giữ vẫn 'Đang giữ' 300 g như trước khi gửi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-09</td>
<td>FR-SALE-04</td>
<td>Business Date mới chưa có order.</td>
<td>1. Gửi hai order hợp lệ liên tiếp.</td>
<td>Mã ORD-ddMMyy-001 và 002 theo Business Date; mã khác nhau.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Business Date 10/11 bắt đầu: order đầu tiên (gửi 05:59:59 ngày 11/11, thuộc BD 10/11) nhận ORD-101126-001, order kế tiếp ORD-101126-002; mã khác nhau, phần ngày theo Business Date.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-10</td>
<td>FR-SALE-04</td>
<td>Một mã đã được cấp cho transaction sau đó rollback.</td>
<td>1. Gửi order hợp lệ kế tiếp.</td>
<td>Không dùng lại số đã cấp; mã mới duy nhất.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Ở INV-29, các yêu cầu trùng bị rollback sau khi đã cấp số (dãy mã nhảy ORD-101126-007 → 010 → 013…); các order hợp lệ kế tiếp không dùng lại số đã cấp. Lượt gửi bị từ chối 422 do thiếu nguyên liệu ngay trước order #410 không làm trùng mã: các mã gần nhất ORD-101126-408, 409, 410 đều duy nhất.</td>
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
<td>10/11/2026 (bản 6985565, Script): Business Date 10/11 đã có order (tới ORD-101126-001…); order đầu tiên của Business Date 11/11 (gửi 06:00:00 ngày 11/11, CAT-22) nhận ORD-111126-001, phần ngày theo BD mới, số bắt đầu 001.</td>
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
<td>10/11/2026 (bản 6985565, API): Thời hạn giữ 5 phút; lượt giữ Gà xào 04 tại B5 đã quá hạn (đặt lùi hạn 1 giây), kho còn đủ. Gửi không xác nhận → 422 'Lượt giữ chỗ đã hết hạn. Xác nhận dùng giá và định lượng hiện tại để gửi món.' (không tự gia hạn: ThoiDiemHetHan giữ nguyên); gửi lại có xác nhận → backend kiểm tra lại và tạo order #412 tại B5; lượt giữ 'Đã gửi'.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-13</td>
<td>FR-SALE-05</td>
<td>Giữ đã hết hạn; order khác dùng nguyên liệu, còn thiếu một suất.</td>
<td>1. Gửi lượt chọn cũ.</td>
<td>Từ chối, nêu món và số lượng thiếu; giữ danh sách chọn; không ghi tiêu hao.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Bê 13 tồn 300 g; lượt giữ 2 suất (300 g) đã hết hạn; Thu ngân 2 gửi 1 suất cho order khác (còn 150 g). Gửi lượt chọn cũ có xác nhận → 422 'Không đủ nguyên liệu cho món Bê xào 13: cần 2 suất, chỉ còn đủ 1 suất (thiếu 1 suất).'; không ghi tiêu hao (số giao dịch 2→2); lượt chọn còn nguyên (lượt giữ vẫn ở trạng thái chưa gửi). Thông báo nêu món và số lượng thiếu.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-14</td>
<td>FR-SALE-05</td>
<td>Giá đổi sau khi giữ món.</td>
<td>1. Gửi mà chưa xác nhận phiên bản mới.</td>
<td>Yêu cầu xác nhận nội dung mới; chưa tạo dòng order hay tiêu hao.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Giữ 1 Vịt xào 14 (90.000), sau đó Quản lý sửa trực tiếp giá 95.000. Gửi chưa xác nhận → 422 'Giá hoặc công thức món đã thay đổi. Xác nhận…'; không tạo dòng order (0), không có tiêu hao (1→1).</td>
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
<td>10/11/2026 (bản 6985565, API): Cùng lượt giữ, gửi có xác nhận nội dung mới: 201; dòng DonGia 95.000, phiên bản giá #36; trừ −150 g một lần (1 giao dịch).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-16</td>
<td>FR-SALE-05</td>
<td>Công thức đổi sau khi giữ món.</td>
<td>1. Gửi mà chưa xác nhận phiên bản mới.</td>
<td>Yêu cầu xác nhận nội dung mới; chưa tạo dòng order hay tiêu hao.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Giữ 1 Vịt xào 14, sau đó Quản lý sửa trực tiếp công thức 150 g → 180 g. Gửi chưa xác nhận → 422 cùng thông báo yêu cầu xác nhận; không tạo dòng hay tiêu hao (2→2).</td>
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
<td>10/11/2026 (bản 6985565, API): Gửi lại có xác nhận: 201; dòng dùng công thức mới #34; trừ đúng −180 g một lần (1 giao dịch).</td>
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
<td>10/11/2026 (bản 6985565, API): Order tại chỗ #408 ở B4 Đang mở, còn gắn bàn: giữ thêm 1 Gà xào 04 (order_id 408) và gửi phần gọi thêm: 201 dòng mới #214 'Chờ làm' với giá và công thức hiện hành; dòng cũ #210 giữ nguyên; phiếu bếp mới #214 chỉ chứa phần thêm.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-19</td>
<td>FR-SALE-06</td>
<td>Order tại chỗ đã rời bàn.</td>
<td>1. Thử gọi thêm vào order.</td>
<td>Từ chối gọi thêm theo phạm vi FR-SALE-06; không giữ hoặc trừ nguyên liệu.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Order tại chỗ #416 ở B6 (Đang mở); xác nhận khách rời B6 → B6 Trống, MaOrderDangPhucVu NULL. Giữ món gọi thêm cho order #416 (POST /sales/holds với order_id 416, bàn B6) → 422 'Order đã được giải phóng khỏi bàn, không thể gọi thêm.'; khả dụng Gà 04 không đổi (1.950), không có lượng giữ; thêm dòng trực tiếp cũng 422, order vẫn 1 dòng.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-20</td>
<td>FR-SALE-06, FR-SALE-31</td>
<td>Order mang về Đang mở; kho đủ; có món đã gửi.</td>
<td>1. Thêm 1 suất vào lượt gọi thêm. 2. Gửi phần gọi thêm.</td>
<td>Bổ sung dòng món và phiếu bếp vào cùng order; giữ rồi trừ đúng nguyên liệu phần thêm; dòng cũ giữ nguyên giá/công thức; không gắn bàn.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order mang về #(dòng #220) Đang mở đã có món; giữ thêm 1 Gà xào 04 với order_id và gửi phần gọi thêm: dòng mới #221 'Chờ làm' trong cùng order, phiếu bếp thứ hai; lượt giữ 'Đã gửi' (giữ rồi trừ); dòng cũ #220 giữ nguyên giá 80.000 và công thức #31.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-21</td>
<td>FR-SALE-08</td>
<td>Đang giữ 2 suất; khả dụng đủ thêm 150 g.</td>
<td>1. Tăng lên 3 suất.</td>
<td>Giữ thêm 150 g, số lượng 3; làm mới thời hạn.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Tôm 21 tồn 450 g; đang giữ 2 suất (300 g); tăng lên 3 suất → 200; SoLuong 3, SoLuongGiu 450, khả dụng 0; ThoiDiemHetHan làm mới (19:10:24.351 → 19:10:25.608).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-22</td>
<td>FR-SALE-08</td>
<td>Đang giữ 2 suất; khả dụng chỉ 100 g.</td>
<td>1. Tăng lên 3 suất.</td>
<td>Từ chối; số lượng, lượng giữ và hạn giữ cũ không đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Tôm 22 tồn 400 g; đang giữ 2 suất (300 g), khả dụng 100; tăng lên 3 → 422 'Không đủ nguyên liệu cho món Tôm 22 rang: cần 3 suất…'; số lượng 2, lượng giữ 300 và hạn giữ (19:10:25.807) không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-23</td>
<td>FR-SALE-08</td>
<td>Đang giữ 2 suất, 300 g.</td>
<td>1. Giảm xuống 1 suất.</td>
<td>Giải phóng 150 g; còn giữ 150 g; tồn sổ sách không đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Cùng lượt giữ 2 suất 300 g; giảm xuống 1 → 200; còn giữ 150 g (khả dụng 250); tồn sổ sách 400 không đổi; không có giao dịch kho mới (chỉ giao dịch nhập).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-24</td>
<td>FR-SALE-08</td>
<td>Dòng chưa gửi đang giữ 300 g.</td>
<td>1. Xóa dòng.</td>
<td>Giải phóng đủ 300 g; không có giao dịch hoàn tồn.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Tôm 24: dòng chưa gửi giữ 2 suất 300 g (khả dụng 100); xóa dòng (DELETE /sales/holds/832) → 'Đã giải phóng'; giữ về 0, khả dụng 400; không có giao dịch hoàn tồn (chỉ giao dịch nhập).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-25</td>
<td>FR-SALE-08</td>
<td>Lượt chọn có hai dòng đang giữ.</td>
<td>1. Bỏ toàn bộ lượt chọn.</td>
<td>Giải phóng toàn bộ lượng giữ của lượt chọn.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Lượt chọn có hai dòng đang giữ (Tôm 24 rang và Gà xào 04); bỏ toàn bộ lượt chọn (POST /sales/holds/release) → released 2; cả hai lượt giữ 'Đã giải phóng', lượng giữ về 0.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-26</td>
<td>FR-SALE-08</td>
<td>Dòng đang giữ còn hiệu lực; ghi lại hạn giữ.</td>
<td>1. Sửa ghi chú.</td>
<td>Ghi chú cập nhật; hạn giữ không đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Dòng B đang giữ hạn 19:10:40.969; sửa ghi chú 'ít cay' sau 1,2 giây → 200; GhiChu cập nhật, hạn giữ vẫn 19:10:40.969.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-27</td>
<td>FR-SALE-08</td>
<td>Dòng đang giữ còn hiệu lực; ghi lại hạn giữ.</td>
<td>1. Mở lại màn hình lượt chọn.</td>
<td>Hạn giữ không đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Mở lại lượt chọn (GET /sales/holds?selection_code=…): hạn giữ hai dòng trả về đúng giá trị đã lưu (…40.926 và …40.969), không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-28</td>
<td>FR-SALE-08</td>
<td>Hai dòng A, B đang giữ; ghi lại hạn giữ A.</td>
<td>1. Sửa ghi chú dòng B.</td>
<td>Hạn giữ dòng A không đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Hai dòng A, B; hạn A 19:10:40.926; sửa ghi chú dòng B → hạn A vẫn 19:10:40.926.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-29</td>
<td>FR-SALE-08</td>
<td>Lượt giữ còn hiệu lực.</td>
<td>1. Đóng trình duyệt, đợi quá hạn; mở lại bằng phiên hợp lệ.</td>
<td>Giữ hết hiệu lực theo giờ server; khả dụng được giải phóng dù trình duyệt đã đóng.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Lượt giữ bị bỏ dở (không gửi, không giải phóng) sau khi quá ThoiDiemHetHan theo giờ server: khả dụng tính lại không trừ lượt giữ đó dù chưa có tác vụ dọn (INV-08: giữ hết hạn 100 g không bị tính, khả dụng 400); khi gửi lại phải xác nhận và kiểm tra lại kho (SALE-12).</td>
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
<td>10/11/2026 (bản 6985565, API): Gửi 1 Gà xào 04 mang về: 201; ORDER MaBan NULL, LoaiDon 'Mang về'; 1 phiếu bếp; trừ −150 g; trạng thái và liên kết của mọi bàn không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-31</td>
<td>FR-SALE-07, FR-SALE-10, FR-INV-04</td>
<td>Dòng Chờ làm gồm 2 suất; đã in; Bếp xác nhận trực tiếp chưa làm; đã trừ L1 200 g, L2 100 g.</td>
<td>1. Hủy cả dòng, nhập lý do.</td>
<td>Hoàn L1 200 g và L2 100 g; ghi người, thời gian, số lượng, lý do; không yêu cầu bản ghi xác nhận bếp trong hệ thống.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Dòng #209 (order #407, B01) 2 suất Chờ làm, phiếu bếp đã tạo, đã trừ L1 #41 200 g và L2 #42 100 g. Hủy cả dòng với lý do 'Khách đổi món, bếp xác nhận chưa làm': dòng 'Đã hủy'; 'Hoàn kho' +200 g vào #41 và +100 g vào #42 (lô về 200/800); nhật ký CANCEL_ORDER_LINE người #2, SoLuong 2, lý do; không yêu cầu bản ghi xác nhận của Bếp.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-32</td>
<td>FR-SALE-07, FR-SALE-10, FR-INV-04</td>
<td>Dòng Chờ làm 2 suất, trừ cùng lô 300 g; Bếp xác nhận chưa làm.</td>
<td>1. Giảm 1 suất, nhập lý do.</td>
<td>Còn 1 suất; hoàn đúng 150 g vào lô gốc; có audit log.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Dòng Gà 32 xào 2 suất Chờ làm, trừ −300 g cùng lô #51. Giảm còn 1 suất không nhập lý do → 422 'Cần nhập lý do khi giảm số lượng món đã gửi.' (số lượng giữ 2). Giảm với lý do → 200; còn 1 suất; 'Hoàn kho' +150 g vào lô gốc #51; nhật ký REDUCE_ORDER_LINE người #2, lý do, SoLuong sau 1.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-33</td>
<td>FR-SALE-07, FR-SALE-10</td>
<td>Dòng ở trạng thái Đã xác nhận xong.</td>
<td>1. Thử giảm số lượng.</td>
<td>Từ chối; dòng món và tồn kho không đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Dòng ở 'Đã xác nhận xong': giảm số lượng → 422 'Chỉ sửa món ở trạng thái Chờ.'; dòng vẫn 2 suất, không có giao dịch kho mới.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-34</td>
<td>FR-SALE-07, FR-SALE-10</td>
<td>Dòng ở trạng thái Đã xác nhận xong.</td>
<td>1. Thử xóa dòng.</td>
<td>Từ chối; dòng món và tồn kho không đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Dòng ở 'Đã xác nhận xong': hủy dòng → 422 'Chỉ hủy món ở trạng thái Chờ.'; dòng và tồn không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-35</td>
<td>FR-SALE-07, FR-SALE-10</td>
<td>Dòng ở trạng thái Đã phục vụ.</td>
<td>1. Thử giảm số lượng.</td>
<td>Từ chối; dòng món và tồn kho không đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Dòng ở 'Đã phục vụ': giảm số lượng → 422 'Chỉ sửa món ở trạng thái Chờ.'; dòng giữ 2 suất.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-36</td>
<td>FR-SALE-07, FR-SALE-10</td>
<td>Dòng ở trạng thái Đã phục vụ.</td>
<td>1. Thử xóa dòng.</td>
<td>Từ chối; dòng món và tồn kho không đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Dòng ở 'Đã phục vụ': hủy dòng → 422 'Chỉ hủy món ở trạng thái Chờ.'; dòng và tồn không đổi (2 giao dịch trừ ban đầu).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-37</td>
<td>FR-SALE-09</td>
<td>Món Chờ làm; đã xác nhận thực tế phù hợp.</td>
<td>1. Nhân viên chuyển sang Đã xác nhận xong.</td>
<td>Lưu đúng trạng thái mới; không trừ hoặc hoàn kho thêm.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Chuyển dòng Chờ làm → 'Đã xác nhận xong': 200, trạng thái lưu đúng; số giao dịch kho của nguyên liệu không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-38</td>
<td>FR-SALE-09</td>
<td>Món Đã xác nhận xong; đã xác nhận thực tế phù hợp.</td>
<td>1. Nhân viên chuyển sang Đã phục vụ.</td>
<td>Lưu đúng trạng thái mới; không trừ hoặc hoàn kho thêm.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Chuyển 'Đã xác nhận xong' → 'Đã phục vụ': 200; không trừ hay hoàn kho thêm (dòng vẫn chỉ có giao dịch trừ ban đầu).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-39</td>
<td>FR-SALE-09</td>
<td>Món Chờ làm.</td>
<td>1. Gọi API chuyển thẳng sang Đã phục vụ.</td>
<td>Từ chối chuyển bỏ qua bước; trạng thái giữ nguyên.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Dòng Chờ làm, gọi API chuyển thẳng 'Đã phục vụ' → 422 'Không thể chuyển từ Chờ làm sang Đã phục vụ.'; trạng thái giữ Chờ làm.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-40</td>
<td>FR-SALE-09</td>
<td>Món Đã phục vụ.</td>
<td>1. Thử chuyển về Chờ làm.</td>
<td>Từ chối chuyển ngược; trạng thái giữ nguyên.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Dòng 'Đã phục vụ', chuyển về 'Chờ làm' → 422 'Không thể chuyển từ Đã phục vụ sang Chờ làm.'; trạng thái giữ nguyên.</td>
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
<td>10/11/2026 (bản 6985565, API): Bàn B7 Trống, lượt chọn có 2 dòng giữ (1 và 2 suất) chưa gửi; Hủy lượt chọn (POST /sales/holds/release) → released 2; cả hai lượt giữ 'Đã giải phóng', lượng giữ 0, khả dụng trở lại; B7 vẫn Trống, không gắn order, không có ORDER nào cho B7.</td>
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
<td>10/11/2026 (bản 6985565, API): Lượt chọn chưa gửi 2 suất (300 g); trừ còn 1 suất (PATCH quantity 1) → 200; còn 1 suất, giữ 150 g, khả dụng tăng 150; tồn sổ sách không đổi, không có giao dịch kho (cùng phép thử SALE-23).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-43</td>
<td>FR-SALE-12, FR-CAT-18</td>
<td>O1 ở B1; B2 Trống.</td>
<td>1. Đổi O1 sang B2.</td>
<td>Cùng transaction: B1 Trống/bỏ liên kết; B2 Đang phục vụ/gắn O1; có audit log.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): O1 (#421) ở B8, B7 Trống: chuyển O1 sang B7 → 200; B8 Trống/MaOrderDangPhucVu NULL, B7 Đang phục vụ/421, ORDER.MaBan=7; nhật ký MOVE_ORDER_TABLE người #2.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-44</td>
<td>FR-SALE-12</td>
<td>O1 ở B1; B2 phục vụ O2.</td>
<td>1. Thử chuyển O1 sang B2.</td>
<td>Từ chối; cả hai bàn và order không đổi.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): O1 ở B8, B9 đang phục vụ O2 (#422): chuyển O1 sang B9 → 422 'Bàn đích đang bận.'; B8/421 và B9/422 không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-45</td>
<td>FR-SALE-12</td>
<td>Order cũ đã giải phóng bàn.</td>
<td>1. Thử đổi order cũ sang bàn Trống.</td>
<td>Từ chối; không gắn lại bàn.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): O1 đã giải phóng khỏi B7; chuyển O1 sang B8 (Trống) → 422 'Order không còn gắn với bàn đang phục vụ.'; B8 vẫn Trống, không gắn lại.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-46</td>
<td>FR-CAT-18</td>
<td>B1 phục vụ O1; còn lượt chọn gọi thêm chưa gửi.</td>
<td>1. Xác nhận khách rời B1.</td>
<td>B1 Trống/bỏ liên kết O1; kết thúc lượt chọn, giải phóng lượng giữ; có audit log.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): B9 phục vụ O2, còn lượt chọn gọi thêm chưa gửi (giữ 1 suất); xác nhận khách rời B9 → 200; B9 Trống, bỏ liên kết O2; lượt giữ gọi thêm 'Đã giải phóng'; nhật ký RELEASE_TABLE (trước MaOrderDangPhucVu 422, sau Trống).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-47</td>
<td>FR-SALE-32</td>
<td>Máy in lỗi; lượt chọn hợp lệ.</td>
<td>1. Gửi món.</td>
<td>Order vẫn được commit, tồn trừ đúng; hiển thị lỗi in.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Cấu hình máy in thử 127.0.0.1:9109 (không có dịch vụ lắng nghe). Gửi 1 Cá 72 kho mang về: order commit 'Đang mở', trừ kho −100 g bình thường; phiếu bếp #248 TrangThaiIn 'Thất bại', SoLanIn 3, LoiIn 'Không kết nối được máy in.' (lỗi kết nối TCP thật).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-48</td>
<td>FR-SALE-32, FR-SALE-03</td>
<td>Order đã ghi nhận, in lần đầu lỗi.</td>
<td>1. In lại phiếu bếp hai lần.</td>
<td>In lại cùng nội dung; không tạo thêm order/dòng món hoặc trừ kho thêm.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Phiếu bếp #248 in lần đầu lỗi; gọi in lại hai lần (POST …/tickets/248/reprint): cả hai 200; vẫn một phiếu bếp với cùng nội dung 'Cá 72 kho x1'; số dòng order (1) và tổng giao dịch kho (326) không đổi; phiếu chuyển lại 'Chờ in', SoLanIn tăng lên 5 (máy in vẫn tắt).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-49</td>
<td>FR-SALE-03, FR-CAT-18</td>
<td>Hai người chọn cùng B1 Trống; kho đủ cả hai.</td>
<td>1. Đồng thời gửi hai lượt chọn khác nhau.</td>
<td>Chỉ một order được gắn B1; yêu cầu còn lại bị từ chối, không tiêu hao cho lượt thất bại.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): B8 Trống; hai Thu ngân gửi đồng thời hai lượt chọn khác nhau vào B8: một yêu cầu 201 (order #423 gắn B8), yêu cầu còn lại 422 'Bàn đang phục vụ. Hãy giải phóng…'; B8 chỉ gắn #423; lượt thất bại không tạo order hay tiêu hao.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-50</td>
<td>FR-SALE-03, NFR-04</td>
<td>Đăng nhập Bếp; có dữ liệu gửi món hợp lệ.</td>
<td>1. Gọi API gửi món.</td>
<td>Backend từ chối; không tạo order hoặc tiêu hao.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Bếp gọi POST /sales/orders với dữ liệu hợp lệ → 403; số giao dịch kho không đổi (7→7).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-51</td>
<td>FR-INV-11, NFR-04</td>
<td>Người B không được phép thao tác lượt chọn của A.</td>
<td>1. B gửi yêu cầu sửa lượt chọn của A.</td>
<td>Từ chối truy cập; lượt chọn và lượng giữ của A không đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Lượt giữ #847 của seed_cashier; seed_cashier2 gửi PATCH tăng số lượng và DELETE lượt giữ đó → cả hai 404 'Không tìm thấy lượt giữ chỗ.' (không lộ dữ liệu của người khác); lượt giữ vẫn 1 suất, 'Đang giữ'.</td>
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
<td>10/11/2026 (bản 6985565, API): Order mang về có QR #15 còn hạn; hủy QR → 200, QR #15 'Đã hủy'; tạo QR mới → 201 #16 'Chờ xác nhận'; chỉ một QR còn hiệu lực; chưa có hóa đơn; order vẫn 'Chờ xác nhận thanh toán' (không chuyển Chờ xác minh).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-53</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Chờ xác nhận thanh toán; kho đủ.</td>
<td>1. Thử thêm món và gửi phần gọi thêm.</td>
<td>Từ chối gọi thêm; không tạo dòng món, không giữ hoặc trừ thêm nguyên liệu; giữ nguyên trạng thái order.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order mang về ở 'Chờ xác nhận thanh toán' (có QR): giữ món gọi thêm → 422 'Order không còn mở.'; thêm dòng → 422 'Order đã đóng.'; order vẫn 1 dòng, trạng thái giữ nguyên, không giữ hay trừ nguyên liệu.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-54</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Chờ xác minh thanh toán; kho đủ.</td>
<td>1. Thử thêm món và gửi phần gọi thêm.</td>
<td>Từ chối gọi thêm; không tạo dòng món, không giữ hoặc trừ thêm nguyên liệu; giữ nguyên trạng thái order.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order mang về ở 'Chờ xác minh thanh toán': giữ món gọi thêm → 422 'Order không còn mở.'; thêm dòng → 422 'Order đã đóng.'; order vẫn 1 dòng, trạng thái giữ nguyên.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-55</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Đã thanh toán; kho đủ.</td>
<td>1. Thử gọi thêm vào order đã thanh toán. 2. Tạo order mang về mới cho món khách mua thêm.</td>
<td>Order cũ từ chối gọi thêm, hóa đơn giữ nguyên; món mua thêm tạo order mới với mã riêng và trừ kho đúng một lần khi gửi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order mang về đã thanh toán qua webhook (1 hóa đơn): giữ món gọi thêm → 422 'Order không còn mở.'; order vẫn 1 dòng, 1 hóa đơn. Tạo order mang về mới cho món mua thêm → 201, order mới 'Đang mở'.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-56</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Đã hủy; kho đủ.</td>
<td>1. Thử thêm món và gửi phần gọi thêm.</td>
<td>Từ chối gọi thêm; không tạo dòng món, không giữ hoặc trừ thêm nguyên liệu; giữ nguyên trạng thái order.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order mang về 'Đã hủy': giữ món gọi thêm → 422 'Order không còn mở.'; thêm dòng → 422 'Order đã đóng.'; order vẫn 1 dòng, trạng thái 'Đã hủy'.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-57</td>
<td>FR-SALE-06, FR-SALE-22</td>
<td>Order mang về ở trạng thái Đóng – chưa thu được tiền; kho đủ.</td>
<td>1. Thử thêm món và gửi phần gọi thêm.</td>
<td>Từ chối gọi thêm; không tạo dòng món, không giữ hoặc trừ thêm nguyên liệu; giữ nguyên trạng thái order.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order ở 'Đóng – chưa thu được tiền': giữ món gọi thêm → 422 'Order không còn mở.'; order vẫn 1 dòng, trạng thái giữ nguyên.</td>
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
<td>10/11/2026 (bản 6985565, API): Order mang về Đang mở có 1 dòng Heo 58 xào; lượt chọn gọi thêm 2 suất bị hủy (released 1), order vẫn 1 dòng; chọn Heo 58 nướng và gửi phần gọi thêm vào cùng order: 201, order có 2 dòng 'Chờ làm', không tạo order mới.</td>
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
<td>10/11/2026 (bản 6985565, API): Order tại chỗ ở B2 có dòng #231 giá 100.000; Quản lý đổi giá 110.000; giữ 1 suất gọi thêm (lượt giữ tạo khi chọn) rồi gửi: dòng mới #232 giá 110.000, lượt giữ 'Đã gửi'; số giao dịch kho tăng đúng 1 (4→5); thêm 1 phiếu bếp (tổng 2); dòng cũ giữ giá 100.000.</td>
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
<td>10/11/2026 (bản 6985565, API): Order mang về Đang mở; giữ 1 suất gọi thêm rồi gửi: tiêu hao một lần (order có 2 giao dịch, tổng −300 g cho 2 dòng); thêm phiếu bếp (2); ORDER.MaBan NULL.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-61</td>
<td>FR-SALE-06, FR-INV-10</td>
<td>Lượt gọi thêm đã giữ món; trước lúc gửi, lô bị mất khả năng đáp ứng toàn bộ lượt gửi.</td>
<td>1. Gửi phần gọi thêm.</td>
<td>Từ chối toàn bộ lượt gửi, chỉ rõ dòng cần kiểm tra lại; không thêm dòng hoặc phiếu bếp, không trừ kho một phần.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, Script+API): (1) Order mang về đang mở; lượt gọi thêm giữ 2 dòng: Gà 61b × 1 và Sò 61b × 2 (Sò bảo quản 1 ngày, hạn 11/11). Gửi phần gọi thêm tại thời điểm mô phỏng 12/11 07:00 (lô Sò đã quá hạn): từ chối toàn bộ; dòng order 1→1, phiếu bếp 1→1, giao dịch kho 318→318 — không trừ một phần. (2) Trên API thật: giữ Mực 61 xào và Heo 58 xào trong cùng lượt gọi thêm, xuất hủy làm lượt giữ Mực bị giải phóng; gửi bulk → 422 'Lượt giữ chỗ không còn hiệu lực.', không thêm dòng/phiếu/giao dịch. Lệch: cả hai thông báo ('Món đang hết nguyên liệu.' / 'Lượt giữ chỗ không còn hiệu lực.') không chỉ rõ dòng/món cần kiểm tra lại.</td>
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
<td>10/11/2026 (bản 6985565, API): Order tại chỗ #429 ở B3 đã có 1 dòng; lượt gọi thêm 2 dòng đang giữ; Hủy lượt chọn → released 2; dòng đã gửi (1 suất, Chờ làm) và tiêu hao gốc giữ nguyên; order 'Đang mở'; B3 'Đang phục vụ' (429); phiếu bếp 1→1.</td>
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
<td>10/11/2026 (bản 6985565, API): Order mang về: dòng duy nhất đã hủy (Trừ tự động + Hoàn kho, mỗi loại 1 giao dịch); còn một lượt giữ gắn order đã quá hạn (đặt lùi hạn): lượt giữ không được tính vào khả dụng; order vẫn 'Đang mở'; không có hóa đơn; không phát sinh hoàn kho lặp.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-64</td>
<td>FR-SALE-06, FR-SALE-11, FR-INV-04</td>
<td>Mọi món đã gửi bị hủy; order Đang mở; còn phần gọi thêm đang giữ và nguyên liệu vẫn đáp ứng.</td>
<td>1. Gửi phần gọi thêm còn hiệu lực.</td>
<td>Ghi món thay thế và phiếu bếp vào cùng order; chuyển lượng giữ thành tiêu hao đúng một lần; order tiếp tục Đang mở.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Cùng order (mọi món đã gửi bị hủy, Đang mở), giữ và gửi phần gọi thêm: 201; order có dòng mới 'Chờ làm' bên cạnh dòng 'Đã hủy'; phiếu bếp thêm 1 (tổng 2); order tiếp tục 'Đang mở'.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-65</td>
<td>FR-SALE-06, FR-SALE-08, FR-INV-10</td>
<td>Một lô còn 300 g, trong đó lượt khác đang giữ 200 g; món gọi thêm cần 150 g.</td>
<td>1. Thêm món cần 150 g vào lượt chọn gọi thêm.</td>
<td>Từ chối giữ do chỉ còn 100 g khả dụng; lượt giữ của người khác và tồn sổ sách không đổi; không thêm dòng món vào order.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Ốc 65 lô 300 g, Thu ngân 2 đang giữ 200 g (2 suất món 100 g); Thu ngân 1 thêm món 150 g vào lượt gọi thêm của order khác → 422 'Món đang hết nguyên liệu.' (khả dụng 100); lượt giữ của Thu ngân 2 vẫn 2 suất 'Đang giữ'; tồn 300 không đổi; order không thêm dòng.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-66</td>
<td>FR-SALE-03, FR-SALE-06, FR-SALE-31</td>
<td>Một lượt gọi thêm qua giữ món đã gửi thành công và có mã yêu cầu duy nhất.</td>
<td>1. Gửi lại cùng yêu cầu với cùng mã và nội dung.</td>
<td>Trả kết quả đã ghi nhận; không tạo thêm dòng, phiếu bếp hoặc tiêu hao.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Gửi phần gọi thêm với request_line_id R → 201 dòng #240; gửi lại cùng R và nội dung → 201 trả lại dòng #240; số dòng (2), phiếu bếp (2), giao dịch kho (14) không đổi giữa hai lần.</td>
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
<td>10/11/2026 (bản 6985565, API): Lượt chọn Cua 67: dòng A còn hiệu lực, dòng B đã quá hạn (khả dụng 150, giữ 150). Hủy lượt chọn → released 2, khả dụng 300 (chỉ tăng đúng phần A); gửi lại yêu cầu hủy → released 0, khả dụng vẫn 300; không tạo order, phiếu bếp hay giao dịch kho (chỉ giao dịch nhập).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-68</td>
<td>FR-SALE-25; NFR-04</td>
<td>Tài khoản Quản lý; có order tại chỗ và mang về ở các trạng thái khác nhau.</td>
<td>1. Đăng nhập Quản lý. 2. Mở mục Quản lý đơn hàng.</td>
<td>Có mục điều hướng riêng; danh sách hiển thị mã, loại đơn, bàn nếu có, ngày kinh doanh, người lập, trạng thái và tổng tiền.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, UI): Quản lý: thanh điều hướng có mục riêng 'Quản lý đơn hàng'; danh sách cột Mã order, Loại đơn, Bàn, Ngày kinh doanh, Người lập, Trạng thái, Tổng tiền (ví dụ 'ORD-101126-462 · Mang về · — · 10/11/2026 · Thu ngân QA · Đã thanh toán · 100.000 ₫').</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-69</td>
<td>FR-SALE-25</td>
<td>Có order khác mã, bàn, ngày kinh doanh và trạng thái.</td>
<td>1. Chọn kết hợp mã, bàn, khoảng ngày và trạng thái. 2. Xóa bộ lọc. 3. Lọc tiêu chí không có kết quả.</td>
<td>Chỉ trả order thỏa toàn bộ tiêu chí; xóa lọc khôi phục danh sách theo quyền; tập rỗng hiển thị thông báo, cho thay đổi bộ lọc.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, UI+API): Lọc kết hợp mã ORD-101126-425 + bàn B2 + ngày 10/11–10/11 + trạng thái Đang mở → đúng 1 order; đổi bàn thành B3 với cùng mã → 0; bỏ lọc → 266 order; khoảng ngày 11/11 → chỉ ORD-111126-001. Trên giao diện, gõ mã 'KHONGCO' → 'Không có order phù hợp — Bỏ bớt điều kiện lọc hoặc chọn khoảng ngày kinh doanh rộng hơn.', bộ lọc và nút 'Xóa bộ lọc' vẫn dùng được.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-70</td>
<td>FR-SALE-25</td>
<td>Quản lý truy cập danh sách; có order lịch sử đã có món, giao dịch và chứng từ.</td>
<td>1. Mở chi tiết order. 2. Đối chiếu món, tổng tiền, lịch sử thanh toán và chứng từ. 3. Quay lại danh sách.</td>
<td>Chi tiết đúng order đã chọn; xem dữ liệu không làm đổi trạng thái, tồn kho hoặc doanh thu; có đường quay lại danh sách.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, UI): Mở chi tiết ORD-101126-462: đúng món Bò 96 xào × 1, 100.000 ₫; trạng thái Đã thanh toán, 'Order đã khóa, không thể sửa'; phiếu bếp #274 (lỗi máy in); hóa đơn HD-20261110-0013, phương thức Tiền mặt; bảng 'Lịch sử thanh toán' có giao dịch #28 · 19:14 10/11/2026 · Tiền mặt · 100.000 ₫ · — · Thành công; có nút 'Quay lại danh sách' trở về danh sách.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-71</td>
<td>FR-SALE-25; NFR-04</td>
<td>Có tài khoản Quản lý và Bếp.</td>
<td>1. Quản lý mở danh sách và chi tiết. 2. Bếp thử truy cập trực tiếp màn hình và API quản lý đơn.</td>
<td>Quản lý truy cập được; Bếp không có mục điều hướng và bị từ chối ở cả giao diện và API, không lộ dữ liệu order.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, UI+API): Quản lý mở được danh sách và chi tiết. Bếp: điều hướng chỉ có Danh mục, Kho, Trợ lý AI (không có Quản lý đơn hàng); API GET /sales/orders và /sales/orders/426 với token Bếp đều 403, không trả dữ liệu order.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-72</td>
<td>FR-SALE-13, FR-SALE-21</td>
<td>Order đang mở có món hợp lệ; chưa có giao dịch thành công.</td>
<td>Thu ngân xác nhận đã nhận đủ tiền mặt.</td>
<td>Giao dịch tiền mặt thành công; order Đã thanh toán; có một hóa đơn.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order đang mở 50.000 đ; Thu ngân xác nhận nhận đủ tiền mặt: 200; giao dịch 'Tiền mặt' 'Thành công' 50.000; order 'Đã thanh toán'; đúng 1 hóa đơn.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-73</td>
<td>FR-SALE-21</td>
<td>Order đang mở có món đã gửi; chưa thanh toán.</td>
<td>Yêu cầu phiếu tạm tính và kiểm tra bảng hóa đơn.</td>
<td>Có dữ liệu phiếu tạm tính; không tạo hóa đơn đã thanh toán.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order đang mở 2 suất: GET phiếu tạm tính → 200, tiêu đề 'PHIẾU TẠM TÍNH - CHƯA THANH TOÁN', mã order, tổng 100.000; HOA_DON không có bản ghi cho order; order vẫn 'Đang mở'.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-74</td>
<td>FR-SALE-14</td>
<td>Cấu hình SePay thử nghiệm; order hợp lệ chưa thanh toán.</td>
<td>Tạo QR và đọc thông tin thanh toán trả về.</td>
<td>QR chứa thông tin VietQR, ngân hàng, tài khoản và số tiền của giao dịch.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Chế độ SePay thử nghiệm (MBBank, tài khoản 0123456789, tên NHA HANG QA). Tạo QR cho order 100.000: 201, payment_code TT9, bank_code MBBank, bank_account 0123456789, account_name NHA HANG QA, SoTien 100.000, ảnh VietQR https://qr.sepay.vn/img?acc=0123456789&amp;bank=MBBank&amp;amount=100000&amp;des=TT9, hạn 10 phút. Ghi chú: cột ThoiDiemTaoQR trong CSDL vẫn NULL (API trả có giá trị).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-75</td>
<td>FR-SALE-14</td>
<td>Order đã có QR còn hiệu lực.</td>
<td>Yêu cầu tạo QR thứ hai.</td>
<td>Từ chối tạo thêm QR khi giao dịch trước còn hiệu lực.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order đã có QR #9 còn hiệu lực; yêu cầu tạo QR thứ hai → 422 (thông báo 'Order đã đóng.'); order vẫn chỉ 1 giao dịch QR.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-76</td>
<td>FR-SALE-15</td>
<td>Order có QR còn hiệu lực; webhook SePay dùng khóa thử nghiệm hợp lệ.</td>
<td>Gửi thông báo tiền vào đúng mã và đủ số tiền.</td>
<td>Order Đã thanh toán; phát hành một hóa đơn.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Webhook SePay Apikey hợp lệ, mã TT…, đủ 100.000 → 200; giao dịch 'Thành công', MaGiaoDichCong sepay:&lt;id&gt;; order 'Đã thanh toán'; đúng 1 hóa đơn.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-77</td>
<td>FR-SALE-15, NFR-04</td>
<td>Order có QR; webhook dùng API key sai.</td>
<td>Gửi thông báo tiền vào với API key sai.</td>
<td>Webhook bị từ chối; giao dịch không được xác nhận.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Webhook với 'Apikey sai' → 401 'API key không hợp lệ.'; giao dịch vẫn 'Chờ xác nhận', order 'Chờ xác nhận thanh toán'; nhật ký WEBHOOK_REJECTED.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-78</td>
<td>FR-SALE-15, NFR-07</td>
<td>Webhook thanh toán đúng đã được xử lý.</td>
<td>Gửi lại cùng mã giao dịch ngân hàng.</td>
<td>Không thu tiền hoặc phát hành hóa đơn lần hai.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Gửi lại webhook cùng mã giao dịch ngân hàng: 200; vẫn 1 hóa đơn, 1 giao dịch Thành công, không tạo ngoại lệ.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-79</td>
<td>FR-SALE-16, FR-SALE-19</td>
<td>Order có QR; webhook hợp lệ nhưng sai số tiền.</td>
<td>Gửi webhook tiền vào sai số tiền.</td>
<td>Chuyển sang xử lý xác minh/ngoại lệ; không coi khoản sai là thanh toán đủ.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Webhook đúng mã QR nhưng chỉ 30.000 (order 50.000): giao dịch vẫn 'Chờ xác nhận', order không thanh toán, không có hóa đơn; tạo ngoại lệ 'Chờ xử lý' 30.000 lý do 'Số tiền không khớp với order'.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-80</td>
<td>FR-SALE-18</td>
<td>QR được tạo ở thời điểm server xác định.</td>
<td>Đọc thời hạn QR trả về.</td>
<td>Hạn QR là 10 phút kể từ thời điểm tạo.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): QR #9: NgayTao 19:11:50.934, ThoiDiemHetHan 19:21:50.934 — đúng 600 giây (10 phút).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-81</td>
<td>FR-SALE-18, FR-SALE-15</td>
<td>QR đã hết hạn; API ngân hàng giả lập có giao dịch phù hợp.</td>
<td>Chọn Kiểm tra lại và đối chiếu kết quả.</td>
<td>Hệ thống vẫn đối chiếu giao dịch ngân hàng sau hạn QR và ghi nhận khoản phù hợp.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): QR #12 đã quá hạn (đặt lùi hạn 1 phút); API ngân hàng giả lập trả khoản TT12 đủ 50.000. Kiểm tra lại (POST /payments/12/check) → 200, giao dịch 'Thành công', order 'Đã thanh toán', 1 hóa đơn.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-82</td>
<td>FR-SALE-19, FR-SALE-22</td>
<td>Order có QR chưa thành công; Thu ngân đăng nhập.</td>
<td>Yêu cầu xác minh; thử thêm món vào order.</td>
<td>Order Chờ xác minh thanh toán; yêu cầu thêm món bị từ chối.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order có QR chưa thành công; Thu ngân yêu cầu xác minh → 200; order 'Chờ xác minh thanh toán'; thêm món vào order bị 422.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-83</td>
<td>FR-SALE-19, FR-SALE-34</td>
<td>Giao dịch QR chưa xác nhận; có mã tham chiếu, bằng chứng và ghi chú.</td>
<td>Gửi yêu cầu xác minh kèm thông tin.</td>
<td>Giữ mã tham chiếu, bằng chứng và ghi chú để đối chiếu.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Yêu cầu xác minh kèm mã tham chiếu FT26314001, ảnh chứng từ và ghi chú 'Khách báo đã chuyển': GIAO_DICH_THANH_TOAN lưu MaGiaoDichNganHang và AnhChungTu; nhật ký REQUEST_PAYMENT_VERIFICATION lưu ghi chú, mã tham chiếu, ảnh.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-84</td>
<td>FR-SALE-20</td>
<td>Order Chờ xác minh; Quản lý đã xác nhận bên ngoài nhận đủ 50.000 đồng.</td>
<td>Quản lý ghi nhận kết quả đã nhận đủ tiền.</td>
<td>Giao dịch Thành công, order Đã thanh toán và có một hóa đơn.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order Chờ xác minh 50.000; Quản lý ghi nhận outcome received, 50.000, ghi chú đối chiếu: 200; giao dịch 'Thành công', order 'Đã thanh toán', 1 hóa đơn.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-85</td>
<td>FR-SALE-23, NFR-04</td>
<td>Order Chờ xác minh; có tài khoản Thu ngân và Quản lý.</td>
<td>Thu ngân thử mở lại; Quản lý mở lại với lý do; tạo QR mới.</td>
<td>Thu ngân bị từ chối; Quản lý mở lại được; giao dịch cũ Đã hủy, order Đang mở và cho phép QR mới.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order Chờ xác minh: Thu ngân mở lại → 403; Quản lý mở lại với lý do → 200, QR cũ #19 'Đã hủy'; tạo QR mới #20 'Chờ xác nhận'; order 'Chờ xác nhận thanh toán'.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-86</td>
<td>FR-SALE-35</td>
<td>Order Chờ xác minh chưa có tiền thành công; Quản lý quyết định ngừng thu.</td>
<td>Quản lý đóng chưa thu được tiền.</td>
<td>Order ở trạng thái kết thúc Đóng – chưa thu được tiền; không phát hành hóa đơn.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order Chờ xác minh, chưa có tiền; Quản lý đóng chưa thu với lý do → 200; order 'Đóng – chưa thu được tiền', giao dịch cùng trạng thái, không có hóa đơn.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-87</td>
<td>FR-SALE-17</td>
<td>Order đã đóng chưa thu; có khoản tiền đến muộn được ghi thành ngoại lệ.</td>
<td>Quản lý áp dụng khoản ngoại lệ hợp lệ; thử áp dụng lại.</td>
<td>Chỉ áp dụng một lần và phát hành một hóa đơn.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order đã đóng chưa thu; khoản 50.000 đến muộn qua webhook → ngoại lệ #4 'Chờ xử lý' ('Order đã đóng, đã hủy hoặc đã thanh toán bằng giao dịch khác'). Quản lý áp dụng khoản muộn → 200, giao dịch #21 Thành công, hóa đơn #9, order 'Đã thanh toán'; áp dụng lần hai → 422 'Giao dịch không ở trạng thái đóng chưa thu…'; vẫn 1 hóa đơn.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-88</td>
<td>FR-SALE-16, FR-SALE-17</td>
<td>Order đã được thanh toán; phát sinh khoản thu trùng.</td>
<td>Thử áp dụng khoản trùng rồi ghi nhận hoàn tiền.</td>
<td>Khoản trùng không được áp dụng lại; đi qua xử lý hoàn tiền.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order đã thanh toán qua webhook; khoản thứ hai cùng mã QR đến → ngoại lệ #5 'Thu trùng cho giao dịch đã thanh toán' 50.000; order vẫn 1 hóa đơn. Thử áp dụng khoản trùng → 422 'Order đã có thanh toán/hóa đơn, chỉ có thể hoàn tiền.'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-89</td>
<td>FR-SALE-17</td>
<td>Có ngoại lệ cần hoàn tiền.</td>
<td>Gửi kết quả hoàn thiếu mã tham chiếu; gửi lại đủ mã và số tiền.</td>
<td>Thiếu mã bị từ chối; kết quả hợp lệ lưu mã tham chiếu và số tiền hoàn.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Ngoại lệ #5: ghi hoàn thiếu mã tham chiếu → 422 'Cần nhập mã tham chiếu hoàn tiền của ngân hàng.' (thiếu ghi chú → 'Cần ghi chú hoàn tiền ngoài hệ thống.'); gửi đủ mã HT003, số tiền, ghi chú → 200, lưu MaThamChieuHoan và SoTienHoan. Ghi chú: mã tham chiếu chỉ lưu lần cuối (PH-08).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-90</td>
<td>FR-SALE-17</td>
<td>Ngoại lệ có số tiền đã nhận xác định.</td>
<td>Thử ghi số tiền hoàn lớn hơn số nhận.</td>
<td>Từ chối số tiền hoàn vượt số tiền đã nhận.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Ngoại lệ #5 nhận 50.000; ghi hoàn 60.000 → 422 'Số tiền hoàn phải lớn hơn 0 và không vượt số còn lại.'</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-91</td>
<td>FR-SALE-17</td>
<td>Ngoại lệ chưa xử lý hết.</td>
<td>Ghi nhận hoàn một phần số tiền.</td>
<td>Ngoại lệ tiếp tục mở cho số tiền còn lại.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Hoàn một phần 20.000 (HT002) → 200, ngoại lệ vẫn 'Chờ xử lý', SoTienHoan 20.000; hoàn tiếp 30.000 → 'Đã hoàn tiền', SoTienHoan 50.000.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-92</td>
<td>FR-SALE-16, FR-SALE-17</td>
<td>Order đã trả tiền mặt; QR cũ nhận tiền sau đó.</td>
<td>Gửi thông báo khoản QR đến muộn.</td>
<td>Order giữ Đã thanh toán; không phát hành thêm hóa đơn cho cùng order.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order đã trả tiền mặt (QR cũ đã hủy); khoản QR cũ đến muộn qua webhook → 200; order giữ 'Đã thanh toán', vẫn 1 hóa đơn; khoản tiền ghi thành ngoại lệ 'Chờ xử lý'.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-93</td>
<td>FR-SALE-15</td>
<td>Chế độ simulator; order có QR; payload có chữ ký nhưng thiếu số tiền.</td>
<td>Gửi webhook thiếu amount.</td>
<td>HTTP 422; order vẫn Chờ xác nhận thanh toán.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Chế độ simulator; order có QR (Chờ xác nhận thanh toán). Webhook /sales/webhooks/payment có chữ ký hợp lệ nhưng thiếu amount → HTTP 422 'Thiếu số tiền.'; order vẫn 'Chờ xác nhận thanh toán', giao dịch 'Chờ xác nhận', không có hóa đơn. (Biến thể chữ ký không khớp → 401.)</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-94</td>
<td>FR-SALE-15</td>
<td>API ngân hàng giả lập trả 151 giao dịch theo thứ tự giảm dần, có phân trang.</td>
<td>Chạy tác vụ đồng bộ giao dịch.</td>
<td>Đọc đủ các trang, không mất giao dịch cũ nhất.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, Script): API ngân hàng giả lập trả 151 giao dịch, mới nhất trước; giao dịch cũ nhất là khoản TT… khớp QR đang chờ. Chạy sync_recent_transfers: đọc đủ 151 dòng, xác nhận 1 khoản, order 'Đã thanh toán' với 1 hóa đơn; MocDongBoSepay tiến tới id mới nhất. Ghi chú: hệ thống gọi một lần với limit 5000 và since_id, giả lập trả 151 dòng trong một trang.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-95</td>
<td>FR-SALE-15</td>
<td>API ngân hàng giả lập trả danh sách bị cắt, không bảo đảm đọc đủ.</td>
<td>Chạy đồng bộ với danh sách không đầy đủ.</td>
<td>Báo lỗi thay vì bỏ qua các khoản tiền cũ chưa đọc.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, Script): Giả lập trả đúng 5.000 dòng: tác vụ báo lỗi 'Danh sách SePay đạt 5.000 giao dịch; chưa tiến mốc đồng bộ. Cần đối soát…'; MocDongBoSepay giữ nguyên, không bỏ qua khoản cũ.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-96</td>
<td>FR-SALE-24, FR-SALE-27, FR-SALE-28, FR-SALE-30, FR-INV-04</td>
<td>Quản lý. Order tại chỗ Đang mở, chưa thanh toán, bàn B1 Đang phục vụ. Bò xào 3 suất: 2 suất Chờ làm, 1 suất Đã xác nhận xong; đã xuất 450 g từ lô L1.</td>
<td>1. Chọn Hủy toàn bộ order. 2. Nhập lý do. 3. Xác nhận. 4. Đối chiếu order, kho, hóa đơn, bàn, báo cáo.</td>
<td>Order Đã hủy trong cùng một giao dịch. Hoàn đúng 300 g vào L1; 150 g của suất đã xong giữ nguyên tiêu hao và ghi vào hao hụt do hủy order. Không phát sinh hóa đơn. Bàn chưa giải phóng vì khách chưa rời. Có audit log và mốc thời gian chi tiết. Order xuất hiện ở giá trị order bị hủy.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order tại chỗ #459 (ORD-101126-458) ở B6: Bò 96 xào 2 suất Chờ làm (−300 g) và 1 suất Đã xác nhận xong (−150 g), cùng lô. Quản lý hủy toàn bộ với lý do 'Khách hủy do chờ lâu' → 200 'Đã hủy'; hoàn +300 g vào lô gốc (1.550 → 1.850); 150 g của suất đã xong giữ nguyên tiêu hao; không có hóa đơn; B6 vẫn 'Đang phục vụ' (khách chưa rời); nhật ký CANCEL_ORDER có lý do; báo cáo order hủy ngày 10/11 có ORD-101126-458 giá trị 300.000, giá vốn 30.000. Ghi chú: ORDER.ThoiDiemDong NULL (PH-09).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-97</td>
<td>FR-SALE-28, FR-SALE-30, FR-INV-04</td>
<td>Quản lý. Order mang về Đang mở; toàn bộ món Chờ làm. Có thêm một lượt chọn gọi thêm chưa gửi đang giữ nguyên liệu.</td>
<td>1. Hủy toàn bộ order kèm lý do. 2. Kiểm tra kho và lượng giữ.</td>
<td>Hoàn toàn bộ nguyên liệu các món Chờ làm về đúng lô gốc. Lượt chọn chưa gửi kết thúc và giải phóng lượng giữ. Không có tiêu hao hay hao hụt phát sinh. Bàn không bị ảnh hưởng.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order mang về Đang mở, 2 suất Chờ làm (−300 g) và một lượt gọi thêm đang giữ 1 suất. Quản lý hủy toàn bộ kèm lý do → 'Đã hủy'; hoàn +300 g về lô gốc; lượt giữ gọi thêm 'Đã giải phóng'; không có dòng xuất hao hụt; không liên quan bàn.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-98</td>
<td>FR-SALE-29, FR-SALE-27</td>
<td>Thu ngân hoặc Quản lý. Order Đang mở, đã tạo mã QR, đang Chờ xác nhận thanh toán.</td>
<td>1. Thử hủy toàn bộ order. 2. Hủy mã QR. 3. Hủy toàn bộ order lại.</td>
<td>Bước 1 bị từ chối, order và kho không đổi. Sau khi hủy QR (hoặc QR hết hạn), bước 3 được chấp nhận.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order có QR đang 'Chờ xác nhận thanh toán': hủy toàn bộ → 422 'Order đã đóng.', order giữ trạng thái; hủy QR rồi hủy toàn bộ lại → 200 'Đã hủy'.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-99</td>
<td>FR-SALE-27</td>
<td>Quản lý. Chuẩn bị hai order: (a) Chờ xác minh thanh toán, (b) Đã thanh toán.</td>
<td>1. Thử hủy toàn bộ từng order.</td>
<td>Cả hai bị từ chối với thông báo lý do. Không đổi trạng thái, kho, hóa đơn hay doanh thu.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Order (a) 'Chờ xác minh thanh toán' và (b) 'Đã thanh toán': Quản lý hủy toàn bộ từng order → cả hai 422 'Order đã đóng.'; trạng thái giữ nguyên, (b) vẫn 1 hóa đơn.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-SALE-100</td>
<td>FR-SALE-27, NFR-04</td>
<td>Tài khoản Thu ngân và tài khoản Quản lý; order Đang mở hợp lệ.</td>
<td>1. Thu ngân thử hủy toàn bộ (giao diện và gọi API trực tiếp). 2. Quản lý hủy nhưng để trống lý do. 3. Quản lý nhập lý do và hủy.</td>
<td>Thu ngân bị từ chối ở cả giao diện và API. Bước 2 bị từ chối vì thiếu lý do. Bước 3 thành công.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Thu ngân gọi API hủy toàn bộ → 403; Quản lý hủy với lý do rỗng → 422 'Cần lý do hủy order.', order vẫn 'Đang mở'; Quản lý nhập lý do 'Khách đổi ý' → 200 'Đã hủy'. (Phần giao diện: nút Hủy toàn bộ chỉ có ở màn Quản lý đơn hàng của Quản lý.)</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-SALE-101</td>
<td>FR-SALE-26</td>
<td>Order đã thanh toán, đã có hóa đơn chốt; tài khoản Thu ngân và Quản lý.</td>
<td>1. Mở hóa đơn đã chốt và chọn in lại hai lần. 2. Đối chiếu nội dung với hóa đơn gốc. 3. Thử chỉnh sửa nội dung khi in lại.</td>
<td>Nội dung in lại đúng nguyên nội dung hóa đơn gốc; không cho chỉnh sửa; không tạo thêm hóa đơn hoặc giao dịch, không đổi doanh thu.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Order (b) đã thanh toán, hóa đơn HD-20261110-0013 100.000. In lại hai lần (Thu ngân, rồi Quản lý gửi kèm TongTien=1): đều 200, nội dung trả về đúng hóa đơn gốc; vẫn 1 hóa đơn, TongTien 100.000, NoiDungChup không đổi, SoLanIn tăng lên 3; tham số sửa nội dung bị bỏ qua; số giao dịch thanh toán không đổi (1).</td>
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
<td>10/11/2026 (bản 6985565, API): Bếp nhập Tôm 1.000 g × 200 đ/g từ NCC A (phiếu #7): tạo lô #9 từ dòng nhập #9, NgayNhap 10/11, HanSuDung 17/11 (7 ngày), SoLuongConLai 1.000, Còn hạn; tồn Tôm 1.000 g; GIAO_DICH_KHO #12 'Nhập' +1.000 g đúng lô #9, GiaTri 200.000; LICH_SU_GIA_BINH_QUAN đơn giá 200, tồn 1.000. Ghi chú: TonSauGiaoDich của giao dịch = 0 (PH-01).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-02</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô chưa có xuất hoặc giữ hiệu lực.</td>
<td>1. Bếp sửa phiếu thành 1.200 g.</td>
<td>Cho phép; tồn và lô cập nhật đúng 1.200 g; có audit log.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Phiếu #7 Tôm 1.000 g, lô chưa xuất, không giữ; Bếp sửa thành 1.200 g: 200; lô #9 SoLuongNhap và SoLuongConLai 1.200, tồn 1.200; sổ kho thêm giao dịch Nhập +200 g (GiaTri 40.000); lịch sử đơn giá ghi dòng mới 200 đ, tồn 1.200; nhật ký UPDATE_RECEIPT có dữ liệu trước (1.000) và sau (1.200).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-03</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô đã có xuất.</td>
<td>1. Bếp sửa phiếu thành 1.200 g.</td>
<td>Từ chối; phiếu, lô và tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Phiếu #8 Vịt 1.000 g, lô #10 đã xuất hủy 100 g (phiếu xuất #1); sửa thành 1.200 g → 422 'Phiếu nhập đã phát sinh xuất kho, phải điều chỉnh qua kiểm kê định kỳ.'; phiếu Hiệu lực, lô 1.000/900, tồn 900 giữ nguyên.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-04</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô đang có giữ hiệu lực.</td>
<td>1. Bếp sửa phiếu thành 1.200 g.</td>
<td>Từ chối; phiếu, lô và tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Phiếu #9 Bê 1.000 g, lô đang có lượt giữ #5 còn hiệu lực (Bê xào 150 g); sửa thành 1.200 g → 422 'Lô của phiếu đang được giữ chỗ, không thể sửa/hủy phiếu.'; phiếu, lô 1.000/1.000, tồn giữ nguyên.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-05</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô chưa có xuất hoặc giữ hiệu lực.</td>
<td>1. Bếp hủy phiếu.</td>
<td>Cho phép; tồn và lô cập nhật đúng lượng bị hủy; có audit log.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Ốc: phiếu #10 10.000 g × 200 đ, phiếu #11 10.000 g × 260 đ → đơn giá bình quân 230, tồn 20.000. Hủy phiếu #11 (lô chưa xuất, không giữ): 200; phiếu 'Đã hủy', lô #13 về 0 và 'Đã hủy', tồn 10.000; sổ kho ghi giao dịch đảo −10.000 g (GiaTri −2.600.000); đơn giá bình quân quay về (20.000×230 − 10.000×260)/10.000 = 200; nhật ký CANCEL_RECEIPT. Ghi chú: giao dịch đảo phiếu nhập dùng LoaiGiaoDich 'Hoàn kho' (PH-04).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-06</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô đã có xuất.</td>
<td>1. Bếp hủy phiếu.</td>
<td>Từ chối; phiếu, lô và tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Cùng phiếu #8 (lô đã xuất): hủy phiếu → 422 cùng thông báo; phiếu vẫn Hiệu lực, lô và tồn giữ nguyên.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-07</td>
<td>FR-INV-02</td>
<td>Phiếu nhập 1.000 g; lô đang có giữ hiệu lực.</td>
<td>1. Bếp hủy phiếu.</td>
<td>Từ chối; phiếu, lô và tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Cùng phiếu #9 khi lô đang giữ: hủy phiếu → 422 cùng thông báo; phiếu Hiệu lực, lô và tồn giữ nguyên.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-08</td>
<td>FR-INV-10</td>
<td>Lô A còn hạn 600 g; B hết hạn 400 g; giữ hiệu lực 200 g trên A, giữ hết hạn 100 g.</td>
<td>1. Tra cứu trước khi tác vụ dọn giữ chạy.</td>
<td>Sổ sách 1.000 g; đủ điều kiện bán 600 g; khả dụng 400 g; không tính giữ hết hạn.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Cá: lô #15 còn hạn 600 g, lô #14 hết hạn (nhập 01/11, hạn 08/11) 400 g; lượt giữ #6 còn hiệu lực 200 g trên lô #15, lượt giữ #7 100 g đã quá ThoiDiemHetHan (đặt lùi hạn bằng SQL để giả lập) nhưng chưa được tác vụ dọn. GET /inventory/stock: SoLuongTon 1.000, SoLuongDuDieuKien 600, SoLuongGiu 200, SoLuongKhaDung 400 — không tính lượt giữ hết hạn; SoLoHetHan 1.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-09</td>
<td>FR-INV-10, FR-INV-13</td>
<td>Lô còn hạn 150 g; một dòng giữ đủ 150 g còn hiệu lực; khả dụng chung 0.</td>
<td>1. Gửi chính dòng đang giữ.</td>
<td>Gửi được; tiêu hao 150 g đúng lô; kết thúc giữ, không tự từ chối do khả dụng chung bằng 0.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Tôm khô lô #16 còn hạn 150 g; lượt giữ #8 (Tôm xào 1 suất) giữ đủ 150 g, khả dụng chung 0. Gửi chính lượt chọn qa-inv09 với hold_id #8: 201 order #4; tiêu hao 'Trừ tự động' −150 g đúng lô #16; lượt giữ chuyển 'Đã gửi'.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-10</td>
<td>FR-INV-03, FR-INV-13</td>
<td>Lô hết hạn nhập sớm còn 300 g; lô còn hạn 700 g.</td>
<td>1. Gửi 1 suất cần 150 g.</td>
<td>Trừ 150 g từ lô còn hạn; lô hết hạn giữ nguyên trong tồn sổ sách.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Cá: lô #14 nhập sớm 01/11 đã hết hạn còn 400 g, lô #15 còn hạn 600 g (dùng 400/600 thay cho 300/700). Gửi 1 Cá chiên cần 100 g (order #5): trừ −100 g từ lô #15; lô #14 giữ 400 g, trạng thái Hết hạn, vẫn nằm trong tồn sổ sách (900 g).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-11</td>
<td>FR-INV-14, FR-SET-04</td>
<td>Ngưỡng 3 ngày; lô còn hàng; hạn dùng cách ngày tham chiếu 2 ngày.</td>
<td>1. Mở màn hình kho.</td>
<td>Trạng thái Sắp hết hạn; cảnh báo hạn dùng tách khỏi cảnh báo tồn.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Ngưỡng cảnh báo 3 ngày, Business Date tham chiếu 10/11; lô #17 còn 100 g, hạn dùng 12/11 (cách 2 ngày): /inventory/lots trạng thái 'Sắp hết hạn'; /inventory/stock CanhBaoHanSuDung=true tách riêng khỏi CanhBaoTonThap=false.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-12</td>
<td>FR-INV-14, FR-SET-04</td>
<td>Ngưỡng 3 ngày; lô còn hàng; hạn dùng cách ngày tham chiếu 3 ngày.</td>
<td>1. Mở màn hình kho.</td>
<td>Trạng thái Sắp hết hạn; cảnh báo hạn dùng tách khỏi cảnh báo tồn.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Ngưỡng cảnh báo 3 ngày, Business Date tham chiếu 10/11; lô #18 còn 100 g, hạn dùng 13/11 (cách 3 ngày): /inventory/lots trạng thái 'Sắp hết hạn'; /inventory/stock CanhBaoHanSuDung=true tách riêng khỏi CanhBaoTonThap=false.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-13</td>
<td>FR-INV-14, FR-SET-04</td>
<td>Ngưỡng 3 ngày; lô còn hàng; hạn dùng cách ngày tham chiếu 4 ngày.</td>
<td>1. Mở màn hình kho.</td>
<td>Trạng thái Còn hạn; cảnh báo hạn dùng tách khỏi cảnh báo tồn.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Ngưỡng cảnh báo 3 ngày, Business Date tham chiếu 10/11; lô #19 còn 100 g, hạn dùng 14/11 (cách 4 ngày): /inventory/lots trạng thái 'Còn hạn'; /inventory/stock CanhBaoHanSuDung=false tách riêng khỏi CanhBaoTonThap=false.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-14</td>
<td>FR-INV-14, FR-SET-04</td>
<td>Ngưỡng 3 ngày; lô còn hàng; hạn dùng cách ngày tham chiếu -1 ngày.</td>
<td>1. Mở màn hình kho.</td>
<td>Trạng thái Hết hạn; cảnh báo hạn dùng tách khỏi cảnh báo tồn.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Lô #20 nhập 04/11, bảo quản 5 ngày, hạn 09/11 (−1 ngày so với 10/11), còn 100 g: trạng thái 'Hết hạn'; CanhBaoHanSuDung=true, SoLoHetHan=1, tách khỏi CanhBaoTonThap=false.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-15</td>
<td>FR-INV-07</td>
<td>Ngưỡng riêng 500 g; khả dụng 499 g.</td>
<td>1. Xem cảnh báo tồn.</td>
<td>Có cảnh báo tồn tối thiểu.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): T499: ngưỡng riêng 500, khả dụng 499 → CanhBaoTonThap=true.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-16</td>
<td>FR-INV-07</td>
<td>Ngưỡng riêng 500 g; khả dụng 500 g.</td>
<td>1. Xem cảnh báo tồn.</td>
<td>Không cảnh báo tồn tối thiểu.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): T500: ngưỡng riêng 500, khả dụng 500 → CanhBaoTonThap=false.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-17</td>
<td>FR-INV-07</td>
<td>Ngưỡng riêng 500 g; khả dụng 501 g.</td>
<td>1. Xem cảnh báo tồn.</td>
<td>Không cảnh báo tồn tối thiểu.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): T501: ngưỡng riêng 500, khả dụng 501 → CanhBaoTonThap=false.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-18</td>
<td>FR-INV-07, FR-SET-05</td>
<td>Không có ngưỡng riêng; mặc định 300 g; khả dụng 299 g.</td>
<td>1. Xem cảnh báo tồn.</td>
<td>Áp dụng ngưỡng 300 g, hiển thị cảnh báo.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): T299: không đặt ngưỡng riêng, mặc định 300, khả dụng 299 → MucTonToiThieuApDung 300, CanhBaoTonThap=true.</td>
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
<td>10/11/2026 (bản 6985565, UI): Thịt bò lô #1 còn 670 g, không giữ (thay cho 500 g). Bếp mở Kho → Phiếu xuất → Tạo phiếu xuất, lý do Hỏng, nguồn Nguyên liệu, chọn Thịt bò lô #1, 100 g, bấm Xem trước: bảng 'Thịt bò (g) · #1 · HSD 2026-11-15 · 100 · tồn lô còn lại 570 · 20.000 ₫', tổng 20.000 ₫, ghi chú 'Chưa có gì được ghi'; lúc này CSDL chưa có phiếu mới, lô vẫn 670. Bấm Xác nhận: báo 'Đã ghi nhận xuất kho…'; phiếu #2 nguồn Nguyên liệu, người lập #3, lý do Hỏng; dòng xuất GiaVonUocTinh 20.000; giao dịch 'Xuất thủ công' −100 g lô #1, GiaTri −20.000; lô còn 570; nhật ký MANUAL_STOCK_ISSUE. Ghi chú: phiếu hiển thị trạng thái 'Nháp' (PH-05).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-20</td>
<td>FR-INV-06</td>
<td>Lô được chọn còn 100 g.</td>
<td>1. Yêu cầu xuất hủy 101 g.</td>
<td>Từ chối; không có giao dịch xuất, tồn giữ nguyên.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Lô HSD+4 (#19) còn 100 g; xem trước và ghi xuất hủy 101 g: đều 422 'Không đủ tồn kho khả dụng.'; không có giao dịch xuất, lô giữ 100 g.</td>
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
<td>10/11/2026 (bản 6985565, API): Lô #19 còn 100 g, không giữ; xem trước 100 g: TonLoConLai 0, GiaTri 1.000, không lượt giữ bị ảnh hưởng; xác nhận (phiếu #4): lô còn 0 g, 'Đã dùng hết'; sổ kho đúng một giao dịch 'Xuất thủ công' −100 g (GiaTri −1.000).</td>
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
<td>10/11/2026 (bản 6985565, API+UI): Cá lô #15 còn 500 g; lượt giữ #10 (Cá chiên 2 suất) giữ 200 g trên lô #15. Xem trước xuất hủy 450 g: TonLoConLai 50, GiaTri 45.000, LuotGiuBiGiaiPhong nêu lượt giữ #10 (qa-inv22, 200 g). Xác nhận (phiếu #5): lượt giữ #10 'Đã giải phóng' toàn bộ, xuất đúng −450 g, lô còn 50 g. Thông báo trên giao diện sau khi xác nhận: 'Nếu lô đang được giữ, hệ thống đã giải phóng lượt giữ — kiểm tra lại dòng món liên quan.'</td>
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
<td>10/11/2026 (bản 6985565, API): Order #6 Heo xào 2 suất, tiêu hao 300 g, dòng #6 chuyển 'Đã xác nhận xong'. Xem trước nguồn Món đã chế biến, dòng #6, 1 suất: hệ thống tự xác định Heo 150 g, giá trị 15.000 (written 0, eligible 2). Xác nhận (phiếu #6): dòng xuất Heo 150 g, SoSuatHuy 1, liên kết MaChiTietOrder #6, GiaVonUocTinh 15.000; tồn Heo giữ 800 g, không phát sinh giao dịch kho mới (không trừ lần hai).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-24</td>
<td>FR-INV-06</td>
<td>Dòng 2 suất đã ghi xuất hủy món 1 suất.</td>
<td>1. Yêu cầu xuất hủy thêm 2 suất.</td>
<td>Từ chối vì chỉ còn 1 suất chưa ghi nhận; không tạo thêm chứng từ hay giao dịch kho.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Dòng #6 đã ghi xuất hủy 1 suất; yêu cầu thêm 2 suất (xem trước và ghi): đều 422 'Số suất hủy vượt quá số suất đã tiêu hao chưa ghi nhận.'; số phiếu xuất và giao dịch kho không đổi.</td>
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
<td>10/11/2026 (bản 6985565, Script): Sò 25 tồn 150 g, Sò hấp cần 150 g/suất. 100 vòng hai Thu ngân (seed_cashier, seed_cashier2) phát đồng thời yêu cầu giữ 1 suất qua API: mỗi vòng đúng một 201 và một 422; không có lỗi 500 hay khóa chết; lượt giữ thành công được giải phóng sau mỗi vòng, tồn không âm.</td>
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
<td>10/11/2026 (bản 6985565, Script): Bò 26 tồn 150 g, hai món Bò 26 xào và Bò 26 nướng cùng cần 150 g. 100 vòng phát đồng thời giữ mỗi món: mỗi vòng đúng một 201, một 422 (báo thiếu); không cấp trùng, không khóa chết.</td>
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
<td>10/11/2026 (bản 6985565, Script): Gan 27 tồn 15.000 g, món 150 g. 100 vòng: tạo lượt giữ qua tầng service, rồi gửi với đồng hồ đặt đúng bằng ThoiDiemHetHan đã lưu (at_time), có xác nhận hết hạn: 100/100 lượt gửi thành công; 100 dòng món, 100 giao dịch 'Trừ tự động' tổng −15.000 g (mỗi dòng đúng −150 g một lần).</td>
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
<td>10/11/2026 (bản 6985565, Script): Gan 28 tồn 150 g, món A 150 g, món B 50 g. 100 vòng: tạo lượt giữ A 150 g; đặt đồng hồ đúng bằng ThoiDiemHetHan đã lưu của A, tạo lượt giữ B 50 g (A đã hết hiệu lực nên khả dụng còn 100 g), rồi gửi A có xác nhận hết hạn: 100/100 bị từ chối 'Món đang hết nguyên liệu.'; không tạo dòng order, không có giao dịch tiêu hao (0), tồn giữ 150 g; lượt chọn của A còn nguyên cho tới khi script dọn.</td>
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
<td>10/11/2026 (bản 6985565, Script): Thịt 29 tồn 18.000 g, món 180 g/suất. 100 vòng, mỗi vòng phát đồng thời 3 lần POST /sales/orders mang về với cùng request_id: CSDL có đúng 100 ORDER, 100 dòng món, 100 giao dịch 'Trừ tự động' tổng −18.000 g (mỗi dòng trừ đúng một lần), tồn về 0. Ghi chú lỗi: ở 99/100 vòng hai yêu cầu trùng nhận HTTP 500 (IntegrityError trùng uq_ORDER_MaYeuCauGui chưa được xử lý), 1 vòng nhận 422; kỳ vọng nghiệp vụ đạt nhưng phản hồi cho client sai (PH-07).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-30</td>
<td>FR-INV-12</td>
<td>Có dữ liệu lô, giữ và cảnh báo.</td>
<td>1. Mở màn hình kho.</td>
<td>Đủ tên, đơn vị, sổ sách, đủ điều kiện bán, đang giữ, khả dụng, ngưỡng, cảnh báo và thời điểm cập nhật.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, UI): Bếp mở Kho → Tồn kho: bảng có Nguyên liệu, Đơn vị, Tồn sổ sách, Đơn giá bình quân, Giá trị tồn, Đủ điều kiện, Đang giữ, Khả dụng, Mức tối thiểu, Hạn dùng gần nhất, Trạng thái/cảnh báo; dòng Cá: 450 · 100 ₫ · 45.000 ₫ · 50 · 0 · 50 · 300 · 2026-11-08 · '1 lô hết hạn' · 'Sắp hết'; có dòng 'Dữ liệu lúc …' và nút Làm mới. Ghi chú: thời điểm hiển thị dạng ISO thô (PH-06).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-31</td>
<td>FR-INV-12</td>
<td>Có Thịt bò và Hành.</td>
<td>1. Tìm Thịt bò.</td>
<td>Chỉ trả nguyên liệu phù hợp tên tìm.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, UI): Gõ 'Thịt bò' vào ô Tìm nguyên liệu: chỉ còn dòng Thịt bò (không có Hành lá).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-32</td>
<td>FR-INV-12</td>
<td>Có nguyên liệu cảnh báo và không cảnh báo.</td>
<td>1. Lọc theo cảnh báo tồn.</td>
<td>Chỉ hiển thị nguyên liệu đang có cảnh báo tồn.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, UI): Chọn bộ lọc 'Cần nhập thêm': chỉ hiện Hành lá, Sả, Cá, Tôm khô, T499, T299 — các nguyên liệu có khả dụng dưới ngưỡng; T500, T501, Thịt bò, Ốc… không hiện.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-33</td>
<td>FR-INV-08, NFR-07</td>
<td>Còn lượt chọn chưa gửi dù giữ đã hết hạn.</td>
<td>1. Thử mở phiên kiểm kê.</td>
<td>Từ chối và yêu cầu xử lý hết lượt chọn/giữ trước khi mở.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Lượt chọn qa-inv33 chưa gửi, lượt giữ #12 đã quá hạn (đặt lùi ThoiDiemHetHan): mở kiểm kê → 422 'Còn lượt giữ chỗ chưa gửi, hãy xử lý trước khi kiểm kê.'; không tạo phiếu kiểm kê.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-34</td>
<td>FR-INV-08, NFR-07</td>
<td>Còn lượt giữ hiệu lực.</td>
<td>1. Thử mở phiên kiểm kê.</td>
<td>Từ chối và yêu cầu xử lý hết lượt chọn/giữ trước khi mở.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Lượt giữ #13 còn hiệu lực: mở kiểm kê → 422 cùng thông báo; PHIEU_KIEM_KE vẫn 0 bản ghi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-35</td>
<td>FR-INV-08, NFR-07</td>
<td>Đã kết thúc phục vụ; món đã chế biến/hủy; không còn lượt chọn hay giữ hiệu lực.</td>
<td>1. Bếp mở kiểm kê.</td>
<td>Tạo phiên trên server, chốt dữ liệu đối chiếu và khóa nghiệp vụ kho.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Mọi dòng order đã chuyển 'Đã xác nhận xong', không còn lượt chọn/giữ hiệu lực; Bếp mở kiểm kê → 201 phiếu #1 'Đang kiểm kê', người thực hiện #3, tạo trên server; ngay sau đó giữ món, gửi món, nhập kho, xuất kho đều bị chặn (INV-36–40). Lần mở trước đó khi còn dòng Chờ làm bị từ chối 'Còn món Chờ làm, hãy xử lý trước khi kiểm kê.'</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-36</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API giữ món bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Phiên kiểm kê #1 đang mở: giữ món (POST /sales/holds) bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tổng tồn (21.959), số giao dịch kho (38) và số lượt giữ (13) không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-37</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API gửi món bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Phiên kiểm kê #1 đang mở: gửi món (POST /sales/orders) bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tổng tồn (21.959), số giao dịch kho (38) và số lượt giữ (13) không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-38</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API nhập kho bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Phiên kiểm kê #1 đang mở: nhập kho (POST /inventory/receipts) bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tổng tồn (21.959), số giao dịch kho (38) và số lượt giữ (13) không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-39</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API xuất kho bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Phiên kiểm kê #1 đang mở: xuất kho (POST /inventory/issues) bằng vai trò hợp lệ → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tổng tồn (21.959), số giao dịch kho (38) và số lượt giữ (13) không đổi.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-40</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở.</td>
<td>1. Gọi API hoàn kho bằng vai trò hợp lệ.</td>
<td>Backend chặn trong transaction; tồn và lượng giữ không thay đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Phiên kiểm kê #1 đang mở: gọi API hủy dòng món (đường hoàn kho) cho dòng #5, #6 → 422 'Đang kiểm kê, không thể thay đổi tồn kho.'; tồn và sổ kho không đổi. Ghi chú: điều kiện mở kiểm kê buộc không còn món Chờ làm nên không có dòng Chờ làm để hoàn; kiểm tra khóa được chặn trước điều kiện trạng thái.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-41</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở; đã nhập số lượng thực tế, chưa xác nhận.</td>
<td>1. Hủy phiên.2. Thực hiện nhập kho hợp lệ.</td>
<td>Phiên kết thúc, không điều chỉnh tồn do kiểm kê; nhập kho được thực hiện bình thường.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Phiên #1 đang mở, đã nhập số thực tế Heo 700 g (chưa xác nhận); hủy phiên → 200, phiếu 'Đã hủy'; tồn Heo giữ 800 g, không có giao dịch 'Điều chỉnh kiểm kê'; nhập kho Heo 10 g ngay sau đó thành công (phiếu #22), tồn 810 g.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-42</td>
<td>FR-INV-08, FR-INV-09, FR-INV-05</td>
<td>Kiểm kê bò: sổ sách 500 g, thực tế 450 g; lô nhập trước còn 200 g.</td>
<td>1. Nhập 450 g và lý do, chọn Xem trước.2. Kiểm tra bản xem trước và xác nhận.</td>
<td>Bản xem trước hiển thị tồn trước 500 g, tồn sau 450 g, chênh lệch −50 g; sau khi xác nhận, điều chỉnh giảm 50 g từ lô nhập trước; sinh một phiếu xuất hủy nguồn Kiểm kê; phiếu không trừ kho thêm; có audit log.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, UI): Bò KK sổ sách 500 g (lô #27 nhập 09/11 còn 200 g, lô #28 300 g), thực tế 450 g. Trên màn Kiểm kê nhập 450 g, lý do, bấm Xem trước: 'Tồn trước 500 · Tồn sau 450 · Chênh lệch −50 · Hao hụt khi sơ chế', ghi chú 'Tồn kho chỉ thay đổi khi bạn chọn Xác nhận; kho vẫn đang khóa'; lúc này CSDL chưa có chi tiết kiểm kê hay giao dịch mới, phiếu vẫn Đang kiểm kê. Xác nhận: báo 'Đã xác nhận kiểm kê, cập nhật tồn kho.'; giao dịch 'Điều chỉnh kiểm kê' −50 g trên lô nhập trước #27 (200→150), GiaTri −11.500 (50 × 230); tự sinh phiếu xuất #7 nguồn Kiểm kê, lý do 'Hủy do kiểm kê', tham chiếu phiếu kiểm kê #2, không trừ tồn lần hai; tồn 450 g; nhật ký CONFIRM_STOCKTAKE.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-43</td>
<td>FR-INV-08, FR-INV-09</td>
<td>Kiểm kê hành: sổ sách 100 g, thực tế 120 g.</td>
<td>1. Nhập 120 g và lý do, chọn Xem trước.2. Xác nhận.</td>
<td>Điều chỉnh tăng 20 g theo BR-LOT-02, giá trị theo đơn giá bình quân hiện hành; không có phiếu xuất hủy cho phần tăng; có audit log.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, UI): Cùng phiên #2: Hành KK sổ sách 100 g, nhập thực tế 120 g và lý do; xem trước hiện chênh lệch +20; sau xác nhận: giao dịch 'Điều chỉnh kiểm kê' +20 g vào lô #29 (100→120), GiaTri 800 theo đơn giá bình quân 40; không có phiếu xuất hủy cho phần tăng; đơn giá bình quân không đổi; nhật ký CONFIRM_STOCKTAKE.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-44</td>
<td>FR-INV-08, FR-INV-09</td>
<td>Sổ sách và thực tế đều 500 g.</td>
<td>1. Nhập 500 g, chọn Xem trước.2. Xác nhận.</td>
<td>Chênh lệch 0; tồn không đổi, không tạo chứng từ hao hụt; phiên kết thúc.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, UI): Cùng phiên #2: 22 nguyên liệu nhập thực tế bằng sổ sách (ví dụ T500: 500/500): xem trước chênh lệch 0; sau xác nhận không có giao dịch điều chỉnh hay chứng từ hao hụt cho các dòng này (chỉ 2 giao dịch của Bò KK và Hành KK); phiên chuyển 'Đã xác nhận'.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-45</td>
<td>FR-INV-06, FR-INV-08, FR-INV-09</td>
<td>Phiếu chênh lệch âm đã xác nhận thành công.</td>
<td>1. Gửi lại yêu cầu xác nhận cùng phiếu.</td>
<td>Không điều chỉnh tồn lần hai, không tạo thêm phiếu xuất hủy nguồn Kiểm kê.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Gửi lại xác nhận phiếu kiểm kê #2 đã xác nhận: 422 'Phiếu kiểm kê đã được xác nhận trước đó.'; số giao dịch kho giữ 44, chỉ một phiếu xuất nguồn Kiểm kê (#7), tồn Bò KK vẫn 450.</td>
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
<td>10/11/2026 (bản 6985565, Script): 100 vòng phát đồng thời qua API: mở kiểm kê (Bếp) và nhập 7 g Sữa 46 (tồn 1.000 g); sau mỗi vòng hủy phiên. Kết quả: 100/100 lần mở phiên thành công, 100/100 lần nhập bị chặn 422 (phiên commit trước); tồn đọc lại sau mỗi vòng luôn 1.000 g, không vòng nào lệch tồn. Không có vòng nào nhập commit trước chốt.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-47</td>
<td>FR-INV-04, FR-INV-13</td>
<td>Món Chờ làm đã tiêu hao 150 g; lô gốc vừa hết hạn; Bếp xác nhận chưa làm.</td>
<td>1. Hủy món.</td>
<td>Hoàn 150 g đúng lô gốc; tăng tồn sổ sách nhưng không tăng tồn đủ điều kiện bán.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, Script): Lòng 47 (bảo quản 1 ngày): lô #40 nhập 10/11 1.000 g, hạn 11/11. Order #406 (Lòng xào 150 g) gửi 10/11 20:00 → 'Trừ tự động' −150 g lô #40, dòng #208 'Chờ làm'. Tại thời điểm mô phỏng 12/11 07:00 (lô đã quá hạn), Quản lý hủy món, lý do 'Bếp xác nhận chưa làm' → 'Hoàn kho' +150 g đúng lô #40 (Business Date 12/11, GiaTri 15.000 theo đơn giá giao dịch xuất gốc); tồn sổ sách 850 → 1.000 g, lô #40 'Hết hạn'; khả dụng tính tại 12/11 vẫn 0 (không tăng tồn đủ điều kiện bán).</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-48</td>
<td>NFR-04</td>
<td>Đăng nhập Thu ngân; phiếu nhập có dữ liệu hợp lệ.</td>
<td>1. Gọi API xác nhận nhập kho.</td>
<td>Backend từ chối quyền; không tạo lô hoặc tăng tồn.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Thu ngân gọi POST /inventory/receipts với dữ liệu hợp lệ: 403; số lô giữ 29, tồn không tăng.</td>
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
<td>10/11/2026 (bản 6985565, API): Dòng #7 Bò xào hành 2 suất đã tiêu hao 300 g Bò thăn + 100 g Hành tây, chuyển 'Đã xác nhận xong'. Xem trước nguồn Món đã chế biến 1 suất: tự xác định Bò thăn 150 g (34.500 đ) và Hành tây 50 g (2.000 đ) theo tiêu hao gốc. Xác nhận (phiếu #8): hai dòng xuất 150 g và 50 g, SoSuatHuy 1, liên kết dòng order #7; số giao dịch kho không đổi (46→46), tồn không giảm lần hai.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-50</td>
<td>FR-INV-05, FR-INV-06</td>
<td>Một suất món đã tiêu hao 150 g nguyên liệu.</td>
<td>1. Gửi yêu cầu hủy một suất, kèm định lượng 999 g.</td>
<td>Phiếu ghi nhận 150 g nguyên liệu theo tiêu hao gốc, liên kết đúng dòng món; tồn kho không thay đổi.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Cùng yêu cầu ở INV-49 gửi kèm ingredient_id Bò thăn, quantity 999 g: phiếu #8 vẫn ghi 150 g Bò thăn và 50 g Hành tây theo tiêu hao gốc, liên kết đúng dòng #7; định lượng 999 g bị bỏ qua; tồn kho không thay đổi.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-51</td>
<td>FR-INV-05, FR-INV-06</td>
<td>Dòng order đã gửi theo công thức 150 g/suất; công thức hiện hành đã đổi thành 200 g/suất.</td>
<td>1. Chọn dòng order cũ và hủy 1 suất đã chế biến.</td>
<td>Chứng từ dùng 150 g theo tiêu hao gốc, không dùng 200 g của công thức hiện hành; không trừ kho lần hai.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Dòng #6 Heo xào gửi theo công thức 150 g/suất; công thức hiện hành đổi thành 200 g (#19). Xem trước hủy 1 suất đã chế biến: Heo 150 g (theo tiêu hao gốc); xác nhận phiếu #9 ghi 150 g, SoSuatHuy 1, không dùng 200 g; không phát sinh giao dịch kho.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-52</td>
<td>FR-INV-08, FR-INV-09</td>
<td>Phiên kiểm kê đang mở; bò sổ sách 500 g, thực tế 470 g.</td>
<td>1. Nhập 470 g và chọn Xem trước.2. Chưa xác nhận, kiểm tra tồn kho và sổ kho.</td>
<td>Bản xem trước hiển thị tồn trước 500 g, tồn sau 470 g, chênh lệch −30 g; tồn và sổ kho chưa thay đổi; phiếu vẫn Đang kiểm kê, kho vẫn khóa.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Phiên #3 đang mở; Bò KK sổ sách 450 g, nhập thực tế 420 g, gọi Xem trước: TonTruocDieuChinh 450, TonSauDieuChinh 420, ChenhLech −30. Chưa xác nhận: CHI_TIET_KIEM_KE của phiên #3 = 0, tồn vẫn 450, số giao dịch kho giữ 46; nhập kho thử bị chặn 'Đang kiểm kê…' (kho vẫn khóa).</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-53</td>
<td>FR-INV-08</td>
<td>Phiên kiểm kê đang mở; hành sổ sách 100 g.</td>
<td>1. Nhập 80 g và chọn Xem trước.2. Chọn Quay lại sửa, nhập 100 g.3. Xem trước và xác nhận.</td>
<td>Lần xem trước đầu không ghi điều chỉnh; sau khi sửa, chênh lệch bằng 0, không tạo giao dịch điều chỉnh; phiếu Đã xác nhận.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, API): Phiên #3: Hành KK sổ sách 120 g; xem trước với 80 g → chênh lệch −40, không ghi gì; xem trước lại với 120 g → chênh lệch 0; ghi số đếm toàn bộ bằng sổ sách và xác nhận: phiếu 'Đã xác nhận', không có giao dịch điều chỉnh (46→46), không có phiếu xuất nguồn Kiểm kê. Ghi chú: bước 'Quay lại sửa giữ số đã nhập' trên giao diện đã thấy nút ở INV-42, lần này thực hiện qua API.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-54</td>
<td>FR-INV-08, NFR-07</td>
<td>Phiên kiểm kê đang mở; bản xem trước có chênh lệch âm, chưa xác nhận.</td>
<td>1. Hủy phiên.2. Kiểm tra tồn, sổ kho và trạng thái khóa.</td>
<td>Phiếu Đã hủy; không có giao dịch điều chỉnh hay phiếu xuất hủy nguồn Kiểm kê; kho được mở khóa.</td>
<td>Trọng yếu</td>
<td>10/11/2026 (bản 6985565, API): Phiên #4 mở, xem trước Bò KK 450→400 (chênh lệch −50), chưa xác nhận; hủy phiên: phiếu 'Đã hủy'; số giao dịch kho giữ 46, không có phiếu xuất nguồn Kiểm kê cho phiên #4, tồn 450; nhập kho ngay sau đó thành công (phiếu #25) — kho đã mở khóa.</td>
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
<td>10/11/2026 (bản 6985565, UI): Thịt bò lô #1 còn 570 g, không giữ. Tạo phiếu xuất Hỏng 100 g, Xem trước: 100 · tồn lô còn lại 470 · 20.000 ₫; lúc này CSDL không có phiếu mới, lô vẫn 570. Bấm Quay lại sửa: ô số lượng vẫn giữ 100; đổi thành 80, Xem trước: 80 · 490 · 16.000 ₫. Xác nhận: chỉ có một phiếu mới #10 với 80 g; lô còn 490.</td>
<td>Đạt</td>
</tr>
<tr class="even">
<td>TC-INV-56</td>
<td>FR-INV-12</td>
<td>Bò chưa xuất: lô 1 nhập 10 kg giá 200.000 đ/kg, sau đó lô 2 nhập 10 kg giá 260.000 đ/kg.</td>
<td>1. Mở màn hình tồn kho, tìm Bò.2. Chọn Bò để xem lịch sử đơn giá bình quân.</td>
<td>Đơn giá bình quân hiện hành 230.000 đ/kg; giá trị tồn 4.600.000 đ; lịch sử có hai dòng: 200.000 đ/kg sau phiếu nhập lô 1 và 230.000 đ/kg sau phiếu nhập lô 2, kèm thời điểm, chứng từ và tồn sau giao dịch.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, UI): Bò bình quân chưa xuất: phiếu #26 10.000 g × 200 đ, phiếu #27 10.000 g × 260 đ. Màn Tồn kho, tìm 'Bò bình quân': tồn 20.000 g, đơn giá bình quân 230 ₫, giá trị tồn 4.600.000 ₫. Chọn Lô và lịch sử: bảng 'Lịch sử đơn giá bình quân' có 2 dòng — Phiếu nhập #26, 200 ₫/g, tồn sau 10.000; Phiếu nhập #27, 230 ₫/g, tồn sau 20.000.</td>
<td>Đạt</td>
</tr>
<tr class="odd">
<td>TC-INV-57</td>
<td>FR-INV-12, FR-INV-09</td>
<td>Sả chưa có phiếu nhập; kiểm kê thừa 200 g đã được xác nhận.</td>
<td>1. Mở màn hình tồn kho, tìm Sả.</td>
<td>Tồn sổ sách 200 g; đơn giá bình quân và giá trị tồn hiển thị “Chưa xác định”, không hiển thị 0.</td>
<td>Thường</td>
<td>10/11/2026 (bản 6985565, UI+API): Sả 57 chưa từng có phiếu nhập; phiên kiểm kê #5 ghi thực tế 200 g (thừa), xác nhận. Màn Tồn kho: tồn sổ sách 200; Đơn giá bình quân và Giá trị tồn đều hiển thị 'Chưa xác định' (không hiện 0).</td>
<td>Đạt</td>
</tr>
</tbody>
</table>

Bảng 48. Ca kiểm thử module Quản lý kho

Lỗi tạo tài khoản ở UC 5.1 được ghi nhận thành ca TC-SET-01. Các ca TC-SET-02–09 kiểm tra FR-SET-02, 03, 04, 06 và 07 (phân quyền, thay đổi cấu hình, audit log). Bảng 49 chưa bao phủ FR-SET-05 ngoài các ca ngưỡng tồn kho thuộc module Kho.

| **Mã ca** | **FR/NFR**                   | **Điều kiện và dữ liệu**                                                          | **Bước thực hiện**                                                                                                           | **Kết quả mong đợi**                                                                                                                     | **Ưu tiên** | **Kết quả thực tế**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | **Trạng thái** |
|-----------|------------------------------|-----------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| TC-SET-01 | FR-SET-01                    | Đăng nhập Quản lý; thông tin tài khoản mới hợp lệ, tên đăng nhập chưa tồn tại.    | 1\. Gửi yêu cầu tạo tài khoản mới.                                                                                           | Tạo thành công; phản hồi trả về thông tin tài khoản và bản ghi được lưu.                                                                 | Thường      | 10/11/2026 (bản 6985565, UI): Quản lý mở Cài đặt → Thêm tài khoản, nhập Thu ngân QA / seed_cashier / Thu ngân / mật khẩu ban đầu, bấm Tạo tài khoản: hộp thoại đóng, danh sách cập nhật ngay 2 tài khoản; NGUOI_DUNG \#2 CASHIER Hoạt động; nhật ký CREATE_USER người thực hiện \#1. Tạo thêm seed_warehouse và seed_cashier2 qua API: 201 trả đủ thông tin tài khoản.                                                                                                                                                | Đạt            |
| TC-SET-02 | FR-SET-02                    | Tài khoản Thu ngân đang hoạt động; biết mật khẩu hiện tại.                        | 1\. Đăng nhập. 2. Tự đổi mật khẩu với mật khẩu hiện tại đúng. 3. Đăng xuất, đăng nhập lại bằng mật khẩu cũ rồi mật khẩu mới. | Đổi thành công; mật khẩu cũ bị từ chối, mật khẩu mới đăng nhập được; không phát sinh bản ghi audit log (ngoài phạm vi theo FR-SET-02).   | Thường      | 10/11/2026 (bản 6985565, API): seed_cashier2 tự đổi mật khẩu với mật khẩu hiện tại đúng: 204. Đăng nhập lại: mật khẩu cũ 401, mật khẩu mới 200. NHAT_KY_HE_THONG không phát sinh bản ghi (4→4).                                                                                                                                                                                                                                                                                                                       | Đạt            |
| TC-SET-03 | FR-SET-02                    | Tài khoản Thu ngân đang hoạt động.                                                | 1\. Gửi yêu cầu tự đổi mật khẩu với mật khẩu hiện tại sai.                                                                   | Bị từ chối kèm thông báo tiếng Việt; mật khẩu không đổi; đăng nhập bằng mật khẩu cũ vẫn thành công.                                      | Thường      | 10/11/2026 (bản 6985565, API): seed_cashier đổi mật khẩu với mật khẩu hiện tại sai: 422 'Mật khẩu hiện tại không đúng.'; đăng nhập bằng mật khẩu cũ vẫn 200, mật khẩu mới định đổi 401.                                                                                                                                                                                                                                                                                                                               | Đạt            |
| TC-SET-04 | FR-SET-02; FR-SET-06         | Đăng nhập Quản lý; có người dùng quên mật khẩu.                                   | 1\. Quản lý đặt lại mật khẩu hộ người dùng. 2. Người dùng đăng nhập bằng mật khẩu mới. 3. Quản lý mở nhật ký.                | Đặt lại thành công; người dùng đăng nhập được; có bản ghi audit log gồm người thực hiện, thời điểm, loại thao tác.                       | Trọng yếu   | 10/11/2026 (bản 6985565, API): Quản lý đặt lại mật khẩu cho seed_cashier2: 204; đăng nhập bằng mật khẩu mới 200, mật khẩu trước đó 401; nhật ký RESET_PASSWORD người thực hiện \#1, thời điểm, đối tượng NGUOI_DUNG \#4, PhienBanToken 1→2, không lưu mật khẩu.                                                                                                                                                                                                                                                       | Đạt            |
| TC-SET-05 | FR-SET-02; FR-SET-03; NFR-04 | Có tài khoản Thu ngân và Bếp; một người dùng khác làm đối tượng.                  | 1\. Thu ngân gọi trực tiếp API đặt lại mật khẩu của người dùng khác. 2. Bếp làm tương tự.                                    | Cả hai bị từ chối (HTTP 403); mật khẩu không đổi; không có bản ghi audit log mới.                                                        | Trọng yếu   | 10/11/2026 (bản 6985565, API): Thu ngân và Bếp gọi POST /settings/users/4/reset-password: cả hai 403 'Bạn không có quyền thực hiện chức năng này.'; mật khẩu giữ nguyên (mật khẩu thử bị 401); không có bản ghi nhật ký mới.                                                                                                                                                                                                                                                                                          | Đạt            |
| TC-SET-06 | FR-SET-03; NFR-04            | Đăng nhập Thu ngân.                                                               | 1\. Kiểm tra mục điều hướng. 2. Truy cập trực tiếp màn hình và API Cài đặt, Báo cáo.                                         | Không có mục điều hướng Cài đặt và Báo cáo; truy cập trực tiếp bị chặn ở cả giao diện và API (HTTP 403), không lộ dữ liệu.               | Trọng yếu   | 10/11/2026 (bản 6985565, UI+API): Đăng nhập seed_cashier: thanh điều hướng chỉ có Danh mục, Bán hàng, Trợ lý AI (không có Cài đặt, Báo cáo); mở thẳng /settings và /reports đều bị chuyển về /sales, không hiện dữ liệu. API /settings/config, /settings/users, /settings/audit-log, /reports/revenue với token Thu ngân đều 403.                                                                                                                                                                                     | Đạt            |
| TC-SET-07 | FR-SET-03; NFR-04            | Có tài khoản Bếp và Quản lý.                                                      | 1\. Bếp truy cập trực tiếp API Cài đặt và API thanh toán. 2. Quản lý dùng chức năng của Thu ngân và của Bếp.                 | Bếp bị từ chối (HTTP 403) với chức năng ngoài phạm vi; Quản lý truy cập được cả hai nhóm chức năng (kế thừa quyền).                      | Trọng yếu   | 10/11/2026 (bản 6985565, API): Bếp gọi API Cài đặt (/settings/config, /settings/users) và API thanh toán (POST /sales/orders/1/pay/cash, /pay/qr, /sales/payments/1/check) và danh sách order: đều 403 trước khi xét dữ liệu. Quản lý gọi chức năng Thu ngân (GET /sales/orders, /catalog/tables) và Bếp (GET /inventory/stock, /inventory/receipts): đều 200.                                                                                                                                                        | Đạt            |
| TC-SET-08 | FR-SET-04; FR-SET-06         | Đăng nhập Quản lý; thời hạn giữ món hiện là 5 phút.                               | 1\. Đổi thời hạn giữ món thành 10 phút. 2. Thử nhập 0 và giá trị âm. 3. Mở nhật ký.                                          | 10 phút được lưu và áp dụng cho lượt giữ món mới; 0 và giá trị âm bị từ chối; audit log ghi dữ liệu trước (5) và sau (10).               | Trọng yếu   | 10/11/2026 (bản 6985565, API): Cấu hình ThoiGianGiuChoPhut=5. PUT 0 và -1 → 422 (phải lớn hơn 0), cấu hình giữ 5; PUT 10 → 200; nhật ký UPDATE_CONFIG ghi TRƯỚC ThoiGianGiuChoPhut=5, SAU=10. Lượt giữ mới tạo sau đó (#4) có ThoiDiemHetHan − NgayTao = 599,99 giây (10 phút).                                                                                                                                                                                                                                       | Đạt            |
| TC-SET-09 | FR-SET-07; NFR-04            | Nhật ký có bản ghi từ nhiều loại thao tác; có tài khoản Quản lý, Thu ngân và Bếp. | 1\. Quản lý mở nhật ký. 2. Thu ngân và Bếp truy cập trực tiếp màn hình và API nhật ký.                                       | Quản lý xem toàn bộ; mỗi bản ghi có người thực hiện, thời điểm, loại thao tác, dữ liệu trước/sau; Thu ngân và Bếp bị từ chối (HTTP 403). | Trọng yếu   | 10/11/2026 (bản 6985565, API): Nhật ký có 469 bản ghi từ nhiều loại thao tác. Quản lý GET /settings/audit-log → 200, mỗi bản ghi có MaNguoiDung, ThoiDiem, LoaiThaoTac, DoiTuong, MaDoiTuong, DuLieuTruoc, DuLieuSau, LyDo; Thu ngân và Bếp gọi API nhật ký → 403. Lệch: nhiều thao tác sửa vẫn không lưu dữ liệu trước/sau — UPDATE_DISH, UPDATE_INGREDIENT, UPDATE_SUPPLIER, UPDATE_TABLE, MOVE_ORDER_TABLE đều có DuLieuTruoc và DuLieuSau NULL (các thao tác UPDATE_CONFIG, UPDATE_RECEIPT, UPDATE_GROUP… đã có). | Không đạt      |

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

| **Ca**    | **FR** | **Dữ liệu và thao tác**                                                                       | **Kết quả mong đợi**                                                                                                                                                                       | **Kết quả**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
|-----------|--------|-----------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TC-REP-01 | 01     | Order thành công 100.000 tiền mặt, 200.000 QR; chờ 50.000; hủy 80.000.                        | Doanh thu 300.000; lọc tiền mặt 100.000, QR 200.000; loại chờ/hủy.                                                                                                                         | 10/11/2026 (bản 6985565, Script+API): Dữ liệu riêng Business Date 10/12/2026 (món 10.000 đ): order 10 suất tiền mặt 100.000, 20 suất QR 200.000 đã xác nhận, 5 suất QR chờ 50.000, 8 suất hủy 80.000. /reports/revenue ngày 10/12: total 300.000, 2 đơn, provisional 0 (khoản chờ không tính); nhóm theo phương thức thanh toán: QR 200.000, Tiền mặt 100.000; loại khoản chờ và order hủy.                                                                                                                                                                                                                 |
| TC-REP-02 | 02     | Tạo chờ xác minh → mở lại → nhận tiền thành công.                                             | Danh sách khoản chưa thu theo đúng trạng thái; trước thành công doanh thu 0; sau thành công ghi một lần.                                                                                   | 10/11/2026 (bản 6985565, Script+API): BD 11/12/2026: order 30.000, QR → Chờ xác minh: doanh thu ngày 0, tạm tính 30.000 tách riêng; danh sách khoản chờ có order đúng trạng thái 'Chờ xác minh thanh toán' kèm lịch sử. Quản lý mở lại, tạo QR mới và xác nhận Thành công: doanh thu 11/12 = 30.000 (ghi một lần), order không còn trong danh sách chờ.                                                                                                                                                                                                                                                     |
| TC-REP-03 | 03     | Món A/B đồng số lượng, khác tiền; lọc đổi kỳ.                                                 | Thứ hạng khớp tổng lượng/tiền và quy tắc đồng hạng; không mất món do LIMIT.                                                                                                                | 10/11/2026 (bản 6985565, Script+API): BD 21/12/2026: Món 10k 5 suất (50.000) và Món 20k 5 suất (100.000), ngày 22/12 thêm Món 10k 1 suất. Xếp theo số lượng ngày 21/12: hai món đồng hạng 5 suất; theo doanh thu: Món 20k (100.000) trước Món 10k (50.000); đổi kỳ sang tuần: Món 10k 6 suất/60.000; đủ món, không mất món do LIMIT. Màn Báo cáo kỳ ngày 21/12, khung 'Món bán chạy' hiện đúng hai món của kỳ.                                                                                                                                                                                              |
| TC-REP-04 | 04     | Doanh thu 1.000.000; giá vốn bán 300.000; hao hụt 50.000; hủy/đóng 20.000.                    | Lợi nhuận gộp 630.000; không trừ lương/thuê và không gộp giá trị order chưa thu vào doanh thu.                                                                                             | 10/11/2026 (bản 6985565, Script+API): Tháng 01/2027: doanh thu 1.000.000 (100 suất × 10.000, giá vốn 300.000); xuất hủy 100 g × 500 = 50.000; order đóng chưa thu 50.000 có giá vốn 20.000. /reports/costs: NguyenLieu 300.000, HaoHut 50.000, DonHuyChuaThu 20.000, Tong 370.000; /reports/margin: DoanhThu 1.000.000, BienLoiNhuanGop 630.000; giá trị order chưa thu không cộng vào doanh thu; không trừ lương/thuê.                                                                                                                                                                                     |
| TC-REP-05 | 05     | Một chênh lệch âm kiểm kê có giao dịch kho và phiếu xuất hủy tự sinh.                         | Chi phí chỉ tính một lần; không cộng cả sổ cái và chứng từ cho cùng biến động.                                                                                                             | 10/11/2026 (bản 6985565, Script+API): Tháng 02/2027: kiểm kê thiếu 50 g (đơn giá 100) → một giao dịch 'Điều chỉnh kiểm kê' −50 g GiaTri −5.000 và phiếu xuất tự sinh nguồn Kiểm kê 50 g/5.000. /reports/costs tháng 02/2027: HaoHut 5.000 (chỉ tính một lần, không cộng cả sổ cái và chứng từ).                                                                                                                                                                                                                                                                                                             |
| TC-REP-06 | 06     | Thay giá/công thức sau bán; có hao hụt kho chung.                                             | Chi phí món dùng phiên bản của dòng bán; không phân bổ hao hụt chung tùy ý.                                                                                                                | 10/11/2026 (bản 6985565, Script+API): Tháng 03/2027: bán 10 suất Món REP06 (10 g/suất, 10.000 đ) rồi đổi công thức thành 30 g và giá 25.000; xuất hủy hao hụt chung 200 g. Giá vốn món tháng 03: 10.000 (theo phiên bản 10 g lưu trên dòng bán, không phải 30 g); doanh thu 100.000 theo giá cũ; phần hao hụt 20.000 nằm ở HaoHut, không phân bổ vào giá vốn món.                                                                                                                                                                                                                                           |
| TC-REP-07 | 07     | Order sát cutoff và qua nửa đêm; ngày/giờ biên.                                               | Bucket khung giờ theo quy tắc; kỳ Business Date khớp order, không lẫn ngày lịch.                                                                                                           | 10/11/2026 (bản 6985565, Script+UI): Order tiền mặt lúc 05:59:59 26/03/2027 (10.000), 06:00 (20.000), 23:59 (30.000), 00:30 27/03 (40.000), 05:59 27/03 (50.000) (chạy 2 lượt nên mỗi mốc 2 đơn). Business Date: 05:59:59 → BD 25/03; bốn đơn còn lại → BD 26/03; BD 27/03 rỗng; doanh thu BD 26/03 = 280.000. Khung giờ BD 26/03: 0h 80.000, 5h 100.000, 6h 40.000, 23h 60.000. Màn Khung giờ tháng 03/2027: 'Chi tiết theo ngày trong tuần' tính theo Business Date — Thứ 6 (BD 26/03) 8 đơn 280.000, Thứ 5 (BD 25/03) 2 đơn 20.000 — đơn sau nửa đêm không bị tách sang Thứ 7, cột doanh thu có giá trị. |
| TC-REP-08 | 08     | Kỳ gốc 0, kỳ sau 100.000; thêm cặp 100.000 → 120.000.                                         | Cặp đầu không chia 0; cặp sau tăng 20%; chênh lệch tuyệt đối đúng.                                                                                                                         | 10/11/2026 (bản 6985565, Script+UI): Dữ liệu: 04/2027 không có đơn, 05/2027 100.000, 06/2027 120.000. API so sánh 04→05: change_percent null (không chia 0); 05→06: 20,00%. Màn So sánh 05/2027–06/2027: 100.000 ₫ → 120.000 ₫, 'Tăng 20%' và '+20.000 ₫'; 10/2026–11/2026: 'Không xác định tỷ lệ phần trăm', '+860.000 ₫'.                                                                                                                                                                                                                                                                                 |
| TC-REP-09 | 09     | Cùng bộ lọc có dữ liệu, rỗng, đổi kỳ.                                                         | Bảng/biểu đồ cùng tổng và đơn vị; rỗng không vẽ số liệu giả.                                                                                                                               | 10/11/2026 (bản 6985565, UI): Tab Doanh thu kỳ ngày 21/12/2026: thẻ 150.000 ₫, 2 đơn, biểu đồ cột 21/12 và bảng chi tiết 21/12 · 2 · 150.000 ₫ cùng tổng và đơn vị; khung 'Món bán chạy' theo đúng kỳ (Món 10k 03: 5, Món 20k REP03: 5). Kỳ rỗng 15/07/2027: 0 ₫, 0 đơn, 'Chưa có dữ liệu trong kỳ', không vẽ số giả.                                                                                                                                                                                                                                                                                       |
| TC-REP-10 | 10     | Order hủy, đóng chưa thu; sau đó áp khoản muộn hợp lệ cho order đóng.                         | Hai nhóm tách; khi nhận tiền rời tổng đóng, giữ lịch sử, doanh thu ghi một lần.                                                                                                            | 10/11/2026 (bản 6985565, Script+API): BD 12/12/2026: order 40.000 hủy; order 60.000 QR → chờ xác minh → Quản lý đóng chưa thu. Báo cáo: Order hủy 1 đơn/40.000; Đóng chưa thu 1 đơn/60.000 (lý do, người đóng 'Quản lý QA') — hai nhóm tách; doanh thu ngày 0. Áp khoản muộn hợp lệ cho order đóng: order 'Đã thanh toán', 1 hóa đơn; danh sách đóng chưa thu về 0; doanh thu ngày 60.000 (ghi một lần).                                                                                                                                                                                                    |
| TC-REP-11 | 11     | Tồn 100 đơn vị giá 10.000 đ; nhập 100 × 20.000 đ, xuất 50; nhập tiếp 100 × 30.000 đ, xuất 50. | Đơn giá bình quân sau hai lần nhập là 15.000 đ và 21.000 đ; giá vốn hai lần xuất lần lượt 750.000 đ và 1.050.000 đ theo công thức lưu trên dòng; giá trị đã ghi không đổi khi có nhập sau. | 10/11/2026 (bản 6985565, Script): NL REP11: tồn 100 × 10.000 đ; nhập 100 × 20.000 → đơn giá 15.000 (tồn 200); xuất 50 → GiaTri −750.000, dòng xuất GiaVonUocTinh 750.000; nhập 100 × 30.000 → (150 × 15.000 + 100 × 30.000)/250 = 21.000; xuất 50 → −1.050.000. Giá trị lần xuất đầu vẫn −750.000 sau lần nhập sau (không tính lại).                                                                                                                                                                                                                                                                        |
| TC-REP-12 | 12     | Xuất hủy nguyên liệu, thiếu kiểm kê, phiếu món đã chế biến.                                   | Hai nguồn đầu vào hao hụt; nguồn món giữ nhóm giá vốn order, không cộng lặp.                                                                                                               | 10/11/2026 (bản 6985565, Script+API): Tháng 04/2027: xuất hủy nguyên liệu 100 g (10.000), xuất hủy món đã chế biến 1 suất (10.000), kiểm kê thiếu 30 g (3.000). /reports/costs: HaoHut gồm nguồn Nguyên liệu và Kiểm kê; phần Món đã chế biến không cộng vào HaoHut mà giữ trong giá vốn order (NguyenLieu), không cộng lặp. (Chạy 2 lượt do lần đầu bị chặn kiểm kê: HaoHut tháng = 10.000 + 10.000 + 3.000 = 23.000, NguyenLieu = 2 order × 20.000.)                                                                                                                                                      |
| TC-REP-13 | 13     | Order hủy có món Chờ làm hoàn kho và món đã chế biến không hoàn.                              | Chỉ phần không hoàn vào chi phí hủy/đóng; nhận muộn chuyển giá vốn đúng một lần.                                                                                                           | 10/11/2026 (bản 6985565, Script+API): Tháng 05/2027: order Món REP13 3 suất Chờ làm (−300 g) + 1 suất đã xác nhận xong (−100 g); hủy toàn bộ: hoàn +300 g (30.000); báo cáo Order hủy ORD-200527-001 giá trị 200.000, giá vốn 10.000; /reports/costs DonHuyChuaThu 10.000 — chỉ phần không hoàn vào chi phí hủy. (Phần nhận muộn chuyển giá vốn đã kiểm ở REP-10/SALE-87: sau khi áp khoản muộn, order rời nhóm đóng chưa thu.)                                                                                                                                                                             |
| TC-REP-14 | 01–13  | Gọi trực tiếp API Báo cáo bằng Thu ngân và Bếp.                                               | 403 và không có dữ liệu, dù người dùng sửa URL hoặc tham số vai trò.                                                                                                                       | 10/11/2026 (bản 6985565, API): Thu ngân và Bếp gọi /reports/revenue, /reports/margin, kể cả thêm tham số role=MANAGER trên URL: đều 403, không trả dữ liệu.                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| TC-REP-15 | 01, 11 | Đổi ngày kinh doanh cấu hình sau khi đã phát sinh order.                                      | Không tính lại BusinessDate cũ; tổng doanh thu/giá vốn lịch sử không tự dịch kỳ.                                                                                                           | 10/11/2026 (bản 6985565, API): Doanh thu BD 10/12/2026 = 300.000, BD 26/03/2027 = 280.000 (8 order), BD 25/03/2027 = 2 order. Quản lý đổi giờ bắt đầu Business Date sang 07:00 (lịch hiệu lực 11/11/2026): đọc lại, tổng và số order từng BD không đổi — BusinessDate đã lưu không bị tính lại. Sau đó đặt lại 06:00 (lịch chờ được hủy).                                                                                                                                                                                                                                                                   |

### H.2. Điều kiện biên nghiệp vụ

Các tình huống giữ món hết hạn, kiểm kê, lô bị hủy, giá vốn và làm tròn thuộc kiểm tra chức năng. Kiểm tra liên quan đạt chưa có nghĩa toàn bộ ca đạt.

| **Mã**   | **Yêu cầu liên quan**                 | **Dữ liệu / sự kiện**                                                                                                | **Kết quả mong đợi**                                                                                                                                                                         | **Kết quả thực tế**                                                                                                                                                                                                                                                                                                                                                                                              |
|----------|---------------------------------------|----------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TC-BR-01 | FR-SALE-05; FR-INV-10                 | Giờ server bằng hạn giữ; tồn đủ, giá/công thức không đổi; gửi toàn lượt chọn                                         | Không coi giữ cũ còn hiệu lực; kiểm tra lại đủ rồi gửi một lần; không tự gia hạn                                                                                                             | 10/11/2026 (bản 6985565, Script): Lượt giữ 2 suất; đặt giờ server đúng bằng ThoiDiemHetHan đã lưu; tồn đủ, giá/công thức không đổi. Gửi không xác nhận → 'Lượt giữ chỗ đã hết hạn. Xác nhận…' (giữ cũ không được coi là còn hiệu lực, hạn không tự gia hạn); gửi có xác nhận → order \#493, tiêu hao đúng một lần (giao dịch 1→2), lượt giữ 'Đã gửi'.                                                            |
| TC-BR-02 | FR-INV-08; TC-INV-33                  | Chỉ còn dòng hết hạn chưa gửi/hủy; yêu cầu mở kiểm kê                                                                | Từ chối; phần hết hạn không chiếm khả dụng nhưng lượt chọn chưa kết thúc                                                                                                                     | 10/11/2026 (bản 6985565, API): Không còn món Chờ làm; lượt chọn có 2 dòng đã hết hạn chưa gửi/hủy. Mở kiểm kê → 422 'Còn lượt giữ chỗ chưa gửi, hãy xử lý trước khi kiểm kê.'; khả dụng 19.800 = tồn (phần hết hạn không chiếm khả dụng); không có phiên kiểm kê nào mở.                                                                                                                                         |
| TC-BR-03 | FR-INV-08                             | Hủy lượt chọn trong BR-02 rồi yêu cầu mở; không còn trở ngại khác                                                    | Giải phóng/đánh dấu xử lý một lần; mở phiên duy nhất, khóa kho                                                                                                                               | 10/11/2026 (bản 6985565, API): Hủy lượt chọn ở BR-02 → released 2; hủy lại → released 0 (xử lý một lần). Mở kiểm kê → 201 phiên \#108; mở lần nữa → 422 'Đang có phiên kiểm kê chưa chốt.'; giữ món lúc này → 422 'Đang kiểm kê…' (kho bị khóa). Sau đó hủy phiên.                                                                                                                                               |
| TC-BR-04 | FR-SALE-16                            | QR cũ hết hạn; tạo QR mới chưa nhận tiền; khoản cũ đúng tiền đến; chưa quyết định mở lại của Quản lý                 | Xác nhận khoản cũ, hủy QR mới trong một transaction; một hóa đơn, không đổi bàn                                                                                                              | 10/11/2026 (bản 6985565, API): Order mang về: QR cũ \#55 đã hết hạn; tạo QR mới \#56 chưa nhận tiền; webhook khoản cũ TT55 đủ 30.000 → 200; QR cũ 'Thành công', QR mới 'Đã hủy' trong cùng xử lý; order 'Đã thanh toán', đúng 1 hóa đơn, không tạo ngoại lệ; không liên quan bàn.                                                                                                                                |
| TC-BR-05 | FR-SALE-17, 23                        | Quản lý đã Mở lại thanh toán; khoản cũ đúng tiền đến khi chưa thu lại                                                | Ghi ngoại lệ, không tự thanh toán; chỉ Quản lý áp dụng hợp lệ                                                                                                                                | 10/11/2026 (bản 6985565, API): Order đã được Quản lý mở lại thanh toán (QR cũ Đã hủy); khoản cũ 30.000 đến → ngoại lệ \#7 'Chờ xử lý' lý do 'Order đã mở lại thanh toán; quản lý cần áp dụng khoản cũ', không tự thanh toán (order 'Đang mở', 0 hóa đơn); Thu ngân gọi áp dụng → 403 (chỉ Quản lý).                                                                                                              |
| TC-BR-06 | FR-SALE-15–17                         | Cùng khoản nhận được webhook lặp trước/sau xác nhận thủ công                                                         | Một lần thu, một hóa đơn; không tạo thêm ngoại lệ cho cùng khoản                                                                                                                             | 10/11/2026 (bản 6985565, API): Order có QR; Thu ngân báo khách chuyển (mã FTBR06…), Quản lý xác nhận đã nhận → 'Đã thanh toán', 1 hóa đơn. Sau đó webhook SePay cùng khoản (referenceCode trùng) gửi hai lần: đều 200; vẫn 1 hóa đơn, 1 giao dịch Thành công, không tạo ngoại lệ nào.                                                                                                                            |
| TC-BR-07 | FR-SALE-09, 22; FR-CAT-18             | Order đã trả tiền nhưng món chưa phục vụ; khách còn ngồi                                                             | Cho cập nhật phục vụ; không đổi món/tiền; bàn chưa tự trống                                                                                                                                  | 10/11/2026 (bản 6985565, API): Order tại chỗ ở B9, 2 suất, thu tiền mặt → 'Đã thanh toán' 60.000; dòng món vẫn cập nhật được Chờ làm → Đã xác nhận xong → Đã phục vụ (200); sửa số lượng bị 422 'Order đã đóng.'; tổng tiền giữ 60.000; B9 vẫn 'Đang phục vụ' (không tự trống).                                                                                                                                  |
| TC-BR-08 | FR-SALE-06, 12; FR-CAT-18             | Giải phóng bàn order cũ; bàn nhận order mới; khoản cũ được xác nhận                                                  | Không gắn lại/giải phóng bàn của order mới; không gọi thêm hoặc đổi bàn cho order cũ                                                                                                         | 10/11/2026 (bản 6985565, API): B9: order A (#499) tạo QR chờ tiền, Thu ngân giải phóng bàn; order B \#500 mở trên B9. Khoản QR của A đến → A 'Đã thanh toán'; B9 vẫn 'Đang phục vụ' gắn \#500 (không gắn lại/giải phóng); gọi thêm cho A → 422 'Order không còn mở.'; đổi bàn A → 422 'Order đã đóng.'.                                                                                                          |
| TC-BR-09 | FR-INV-05–06; FR-REP-11–13            | Bỏ 1 suất có 2 dòng nguyên liệu; ghi phiếu Món đã chế biến                                                           | Ghi 1 suất bỏ; lượng khớp tiêu hao gốc, không trừ hoặc tính chi phí lần hai                                                                                                                  | 10/11/2026 (bản 6985565, API): Món BR09 (BR09a 150 g + BR09b 50 g/suất), dòng 2 suất đã tiêu hao và 'Đã xác nhận xong'. Xuất hủy nguồn Món đã chế biến 1 suất (phiếu \#31): 2 dòng xuất BR09a 150 g/15.000 và BR09b 50 g/2.000, SoSuatHuy 1, khớp tiêu hao gốc; số giao dịch kho của hai nguyên liệu giữ 4 (không trừ lần hai), tồn BR09a giữ 700.                                                               |
| TC-BR-10 | FR-INV-09; FR-REP-12                  | Kiểm kê thiếu, tạo giao dịch điều chỉnh và phiếu xuất hủy tham chiếu                                                 | Tồn giảm theo chênh lệch đúng một lần; hao hụt không cộng cả hai nguồn                                                                                                                       | 10/11/2026 (bản 6985565, API): BR10 tồn 500 g (đơn giá 100); kiểm kê thực tế 450: một giao dịch 'Điều chỉnh kiểm kê' −50 g (GiaTri −5.000) và phiếu xuất tham chiếu nguồn Kiểm kê 50 g/5.000; tồn còn 450 (giảm đúng một lần); hao hụt chỉ tính một nguồn (xem REP-05: HaoHut 5.000).                                                                                                                            |
| TC-BR-11 | FR-REP-11; tài liệu 04 G.1            | Thiếu giá tham chiếu; sau đó bổ sung dữ liệu hợp lệ cho phép tính                                                    | Trước khi có đơn giá: giá trị chưa xác định; khi có phiếu nhập hợp lệ đầu tiên, phần chưa xác định được định giá theo đơn giá bình quân đầu tiên; 0 chỉ hiển thị khi phép tính hợp lệ bằng 0 | 10/11/2026 (bản 6985565, Script+API): BR25: nguyên liệu chưa từng nhập; kiểm kê thừa 5 → lô điều chỉnh, GiaTri NULL; tiêu hao 1 → GiaTri NULL; màn tồn kho trả DonGiaBinhQuan và GiaTriTon null ('Chưa xác định', INV-57), giá vốn món 'Chưa đủ dữ liệu' (CAT-51), không hiển thị 0. Nhập phiếu hợp lệ đầu tiên 5 × 6: đơn giá bình quân 6,00; hai biến động trước đó được định giá theo 6,00 (+30,00 và −6,00). |
| TC-BR-12 | FR-INV-03; tài liệu 04 G.1            | Xuất kho nhiều lần giữa hai phiếu nhập khác giá                                                                      | Mỗi lần xuất dùng đơn giá bình quân hiện hành tại thời điểm xuất; xuất không làm đổi đơn giá và không tạo bản ghi lịch sử giá                                                                | 10/11/2026 (bản 6985565, API): BR12: nhập 10 × 100 (bình quân 100); xuất 2 → −200, xuất 3 → −300; nhập 10 × 200 → bình quân (5 × 100 + 10 × 200)/15 = 166,67; xuất 4 → −666,68. Lịch sử giá chỉ có 2 dòng (hai lần nhập) — các lần xuất không đổi đơn giá, không tạo bản ghi lịch sử.                                                                                                                            |
| TC-BR-13 | FR-INV-02; FR-REP-11                  | Đã có phiếu xuất hủy định giá theo đơn giá hiện hành; sau đó thêm phiếu nhập hợp lệ khác giá                         | Đơn giá bình quân cập nhật theo phiếu mới; giá trị phiếu xuất hủy đã ghi giữ nguyên; chi phí của phần đã xuất không đổi                                                                      | 10/11/2026 (bản 6985565, API): BR13: nhập 10 × 100; xuất hủy 4 → GiaVonUocTinh 400; nhập tiếp 10 × 300 → bình quân (6 × 100 + 10 × 300)/16 = 225; giá trị phiếu xuất hủy vẫn 400, giao dịch xuất vẫn −400.                                                                                                                                                                                                       |
| TC-BR-14 | FR-INV-02; FR-REP-11                  | Phiếu nhập ghi nhầm ngày, lô chưa xuất/không giữ hiệu lực; sửa ngày nhập                                             | Cập nhật ngày lô, hạn dùng và thứ tự FIFO; đơn giá bình quân không đổi; giữ audit trước/sau                                                                                                  | 10/11/2026 (bản 6985565, API): BR14 (bảo quản 10 ngày): phiếu A 100 × 6 ngày 05/11, phiếu B 100 × 10 ngày 08/11 (bình quân 8,00). Sửa ngày phiếu A (lô chưa xuất, không giữ) sang 09/11: 200; lô A NgayNhap 09/11, hạn 19/11; thứ tự FIFO đổi — lô B (08/11) đứng trước; lịch sử đơn giá không đổi (6,00 → 8,00); nhật ký UPDATE_RECEIPT có DuLieuTruoc (NgayNhap 05/11) và DuLieuSau (09/11).                   |
| TC-BR-15 | FR-INV-02; FR-REP-11                  | Hủy phiếu đủ điều kiện khi nguyên liệu đã có xuất từ lô khác                                                         | Không bị khóa; đơn giá bình quân hiện hành được tính lại sau khi đảo phiếu; giá trị đã xuất, hóa đơn và doanh thu giữ nguyên                                                                 | 10/11/2026 (bản 6985565, API): BR15: phiếu A 10 × 100, xuất hủy 4 từ lô A (−400); phiếu B 10 × 200 (bình quân 162,50). Hủy phiếu B (lô B chưa xuất, không giữ) → 200, không bị khóa vì đã có xuất từ lô khác; đơn giá bình quân tính lại = 100,00 (tồn 6); giá trị đã xuất giữ −400.                                                                                                                             |
| TC-BR-16 | FR-INV-02                             | Sửa phiếu khi lô đã có xuất hoặc còn giữ hiệu lực                                                                    | Từ chối toàn bộ, phiếu/lô/giá vốn không bị cập nhật dở                                                                                                                                       | 10/11/2026 (bản 6985565, API): Phiếu hai dòng BR16a 50 × 4 và BR16b 30 × 5; BR16a đã xuất 5. Sửa cả hai dòng thành 80 × 9 → 422 'Phiếu nhập đã phát sinh xuất kho…'; cả hai dòng phiếu giữ 50 × 4 và 30 × 5, lô 45/50 và 30/30, lịch sử đơn giá không thêm dòng — không cập nhật dở.                                                                                                                             |
| TC-BR-17 | FR-INV-09; BR-LOT-02                  | Kiểm kê thừa, không còn lô còn hạn và không có giá tham chiếu                                                        | Vẫn tạo lô điều chỉnh và tăng lượng đúng; DonGia NULL, không yêu cầu nhập giá, không tạo phiếu nhập mua; phần giá trị chưa xác định                                                          | 10/11/2026 (bản 6985565, API): BR17 chưa có lô và chưa có giá; kiểm kê thực tế 50 g → tạo lô điều chỉnh \#128 LoDieuChinhKiemKe=1, MaChiTietNhap NULL, HanSuDung NULL, còn 50; giao dịch 'Điều chỉnh kiểm kê' +50 GiaTri NULL; không yêu cầu nhập giá, không tạo phiếu nhập mua (0 dòng nhập), không có lịch sử đơn giá.                                                                                         |
| TC-BR-18 | FR-INV-09; FR-REP-11                  | Điều chỉnh thừa khi nguyên liệu đã có đơn giá bình quân                                                              | Giá trị phần thừa = lượng thừa × đơn giá bình quân hiện hành, do hệ thống tính; không cộng lượng thừa vào nhập mua; đơn giá bình quân không đổi                                              | 10/11/2026 (bản 6985565, API): BR18 tồn 100 g, bình quân 40; kiểm kê thực tế 120 → giao dịch +20 GiaTri 800 (20 × 40, do hệ thống tính); không thêm dòng nhập mua (vẫn 1); lịch sử đơn giá không thêm bản ghi — bình quân giữ 40.                                                                                                                                                                                |
| TC-BR-19 | FR-INV-02; tài liệu 04 F.21           | Phiếu có hai dòng tạo hai lô chưa xuất, không còn giữ hiệu lực; hủy phiếu                                            | Đảo đúng lượng nhập của cả hai lô, lượng còn lại bằng 0, trạng thái Đã hủy; phiếu/lô/lịch sử còn truy vết; đơn giá bình quân hiện hành được tính lại                                         | 10/11/2026 (bản 6985565, API): Phiếu hai dòng BR19a 20 × 7 và BR19b 30 × 8 (mỗi nguyên liệu đã có 10 × 5), hai lô chưa xuất, không giữ; hủy phiếu → 200, phiếu 'Đã hủy', lô \#91 và \#92 còn 0 và 'Đã hủy' (vẫn truy vết được); đơn giá bình quân tính lại: BR19b 7,25 → 5,00; BR19a 6,33 → 4,99 (lệch 0,01 do đảo theo đơn giá đã làm tròn, PH-10).                                                             |
| TC-BR-20 | FR-INV-05; BR-LOT-01                  | Lô còn hạn có 10 đơn vị; xuất hủy 3 đơn vị nguyên liệu                                                               | Lô còn 7 đơn vị, không mang trạng thái Đã hủy; 7 đơn vị tiếp tục đủ điều kiện phân bổ nếu không bị giữ; hao hụt ghi đúng một lần                                                             | 10/11/2026 (bản 6985565, API): BR20 lô còn hạn 10; xuất hủy 3 từ lô → lô còn 7, trạng thái 'Còn hạn' (không 'Đã hủy'); khả dụng 7; giữ món cần 7 thành công; chỉ một giao dịch xuất.                                                                                                                                                                                                                             |
| TC-BR-21 | FR-INV-02, FR-INV-09; F.21            | Thử giữ món, xuất FIFO hoặc cộng chênh lệch kiểm kê vào lô Đã hủy                                                    | Không chọn lô Đã hủy; kiểm kê thừa dùng lô hợp lệ khác hoặc tạo lô điều chỉnh theo BR-LOT-02, không khôi phục lô đã hủy                                                                      | 10/11/2026 (bản 6985565, API): BR21: lô \#126 50 × 10 còn hạn và lô \#127 30 × 20 đã hủy (hủy phiếu, còn 0, 'Đã hủy'). Kiểm kê thừa 10 → cộng vào lô hợp lệ \#126 (50 → 60), không khôi phục lô \#127; gửi 2 suất (20 g) → FIFO chỉ trừ lô \#126, không chọn lô Đã hủy.                                                                                                                                          |
| TC-BR-22 | FR-REP-11; tài liệu 04 G.1            | Hai lần nhập 1 × 4 và 2 × 3 cho đơn giá bình quân trước làm tròn 10/3; xuất 3 đơn vị chuẩn                           | Lưu đơn giá 3,33; giá vốn dòng xuất 9,99 theo ROUND_HALF_UP; lượng vẫn theo độ chính xác sáu chữ số                                                                                          | 10/11/2026 (bản 6985565, API): BR22: nhập 1 × 4 và 2 × 3 → bình quân 10/3 lưu 3,33; xuất 3 đơn vị (chia qua 2 lô: −3,33 và −6,66) → dòng xuất GiaVonUocTinh 9,99 (3 × 3,33, ROUND_HALF_UP); lượng 3,000000.                                                                                                                                                                                                      |
| TC-BR-23 | FR-REP-11; tài liệu 04 G.1            | Đơn giá bình quân 1,01; xuất 0,5 đơn vị; giá trị trước làm tròn 0,505                                                | GiaVonUocTinh bằng 0,51 theo ROUND_HALF_UP; đơn giá lưu giữ 1,01; không tạo thêm biến động kho                                                                                               | 10/11/2026 (bản 6985565, API): BR23: bình quân 1,01; xuất 0,5 → GiaVonUocTinh 0,51 (0,505 làm tròn ROUND_HALF_UP); đơn giá lưu giữ 1,01; chỉ phát sinh đúng một giao dịch xuất.                                                                                                                                                                                                                                  |
| TC-BR-24 | FR-INV-04; tài liệu 04 G.1            | Tồn 150 đơn vị, đơn giá bình quân 15.000 đ; dòng Chờ làm đã tiêu hao 20 đơn vị khi đơn giá là 12.000 đ; hủy dòng món | Hoàn 20 đơn vị về lô gốc theo đơn giá 12.000 đ; đơn giá bình quân mới = (150 × 15.000 + 20 × 12.000)/170 = 14.647,06 đ; một bản ghi lịch sử giá mới                                          | 10/11/2026 (bản 6985565, API): BR24: nhập 100 × 12.000; dòng Chờ làm tiêu hao 20 (−240.000 theo 12.000); nhập 70 × 18.428,57 → tồn 150, bình quân 15.000,00. Hủy dòng món: 'Hoàn kho' +20, GiaTri 240.000 (đơn giá 12.000 của giao dịch xuất gốc); bình quân mới (150 × 15.000 + 20 × 12.000)/170 = 14.647,06, tồn 170; thêm đúng 1 bản ghi lịch sử giá (2 → 3).                                                 |
| TC-BR-25 | FR-INV-09; FR-REP-11; tài liệu 04 G.1 | Nguyên liệu chưa có đơn giá: lô điều chỉnh 5 đơn vị, một dòng tiêu hao 1 đơn vị; sau đó nhập 5 × 6                   | Trước khi nhập: giá trị chưa xác định; sau khi nhập: đơn giá bình quân 6,00, dòng tiêu hao trước đó được định giá 6,00 một lần; không tạo biến động kho mới                                  | 10/11/2026 (bản 6985565, API): BR25 chưa có đơn giá: kiểm kê thừa tạo lô điều chỉnh 5 (GiaTri NULL), một dòng tiêu hao 1 (GiaTri NULL); màn tồn trả đơn giá và giá trị tồn null. Nhập 5 × 6: bình quân 6,00; lô điều chỉnh được định giá +30,00, dòng tiêu hao −6,00 (một lần); không tạo biến động kho mới ngoài giao dịch nhập.                                                                                |

## I. Nhận xét

Trên bản 6985565 (ngày 10/11/2026): 256 đạt, 2 không đạt trên tổng 258 ca. Các ca không đạt: TC-SALE-61 (thông báo từ chối không chỉ rõ dòng hoặc món cần kiểm tra lại) và TC-SET-09 (nhật ký thao tác sửa món, nguyên liệu, nhà cung cấp, bàn và chuyển bàn không lưu dữ liệu trước và sau). Ngoài các ca, 10 lỗi phát hiện ngoài test case được ghi ở mục J.2; ba lỗi cần xử lý trước là PH-01 (tồn sau giao dịch luôn bằng 0), PH-07 (gửi lặp đồng thời trả lỗi 500) và PH-05 (phiếu xuất đã xác nhận vẫn ghi trạng thái Nháp). Hiệu năng cơ bản đo ngày 11/11/2026 trên bộ dữ liệu 2 tháng đạt ngưỡng ở cả bốn nhóm, không có lỗi và dữ liệu giữ đúng bất biến (mục G).

## J. Lỗi chức năng đang ghi nhận

### J.1. Ca không đạt

Hai ca dưới đây không đạt trên bản 6985565 ngày 10/11/2026; cần kiểm tra lại sau khi dev sửa.

| **Mã ca**  | **Lỗi ghi nhận**                                                                                                                                                                                                                                       | **Trạng thái** |
|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| TC-SALE-61 | Lượt gửi phần gọi thêm bị từ chối toàn bộ đúng (không trừ một phần, dòng order, phiếu bếp và giao dịch kho không đổi) nhưng thông báo 'Món đang hết nguyên liệu.' hoặc 'Lượt giữ chỗ không còn hiệu lực.' không chỉ rõ dòng hoặc món cần kiểm tra lại. | Không đạt      |
| TC-SET-09  | Nhật ký có đủ người thực hiện, thời điểm, loại thao tác và đối tượng, phân quyền đúng (Thu ngân và Bếp bị 403), nhưng UPDATE_DISH, UPDATE_INGREDIENT, UPDATE_SUPPLIER, UPDATE_TABLE và MOVE_ORDER_TABLE vẫn có DuLieuTruoc và DuLieuSau NULL.          | Không đạt      |

### J.2. Lỗi phát hiện ngoài test case

Mười lỗi dưới đây được phát hiện trong lúc kiểm thử ngày 10/11/2026 trên bản 6985565, nằm ngoài kỳ vọng của các ca; cần dev xem xét và kiểm tra lại sau khi sửa.

| **Mã** | **Phát hiện**                                                                                                                                                                                                                                                                                                                                                  | **Trạng thái** |
|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| PH-01  | Cột GIAO_DICH_KHO.TonSauGiaoDich luôn bằng 0 ở mọi giao dịch kho, kể cả 48.493 giao dịch của bộ dữ liệu seed. Code không gán balance_after (models.py để mặc định 0, không chỗ nào gán). Tài liệu 04 F.26 mô tả là 'Tồn sau khi ghi nhận'.                                                                                                                     | Ghi nhận       |
| PH-02  | PATCH /catalog/suppliers/{id} trả PhieuNhap rỗng dù nhà cung cấp có phiếu nhập; GET trả đúng.                                                                                                                                                                                                                                                                  | Ghi nhận       |
| PH-03  | NHOM_MON.NgayXoa để NULL khi xóa mềm nhóm món.                                                                                                                                                                                                                                                                                                                 | Ghi nhận       |
| PH-04  | Hủy phiếu nhập ghi giao dịch đảo với LoaiGiaoDich 'Hoàn kho', trùng tên với hoàn kho khi hủy món nên dễ nhầm khi lọc sổ kho hoặc báo cáo. Nhật ký CANCEL_RECEIPT có DuLieuTruoc NULL.                                                                                                                                                                          | Ghi nhận       |
| PH-05  | Phiếu xuất đã xác nhận (đã trừ tồn) vẫn có TrangThai 'Nháp' trong cơ sở dữ liệu và trên danh sách Phiếu xuất, dễ hiểu nhầm là chưa ghi. Giá trị trạng thái của PHIEU_XUAT_KHO chưa được quy định trong tài liệu 04.                                                                                                                                            | Ghi nhận       |
| PH-06  | Ngày giờ hiển thị dạng ISO thô ở màn Tồn kho ('Dữ liệu lúc 2026-11-10T18:53:07.579223+07:00') và cột Ngày nhập trong Chi tiết lô ('2026-11-10T18:57:13.171000'), thay vì định dạng dd/mm/yyyy hh:mm.                                                                                                                                                           | Ghi nhận       |
| PH-07  | Gửi lặp đồng thời cùng request_id (POST /sales/orders): yêu cầu đầu trả 201, các yêu cầu trùng trả HTTP 500 do IntegrityError 1062 trên uq_ORDER_MaYeuCauGui không được bắt (99/100 vòng). Dữ liệu vẫn đúng (1 order, 1 dòng, trừ kho 1 lần) nhưng máy khách nhận lỗi máy chủ thay vì order đã tạo hoặc 422. Gửi lặp tuần tự sau khi commit trả đúng order cũ. | Ghi nhận       |
| PH-08  | Hoàn tiền ngoại lệ nhiều lần: cột NGOAI_LE_THANH_TOAN.MaThamChieuHoan chỉ giữ mã tham chiếu của lần hoàn cuối (HT002 bị thay bằng HT003) trong khi SoTienHoan cộng dồn; mã tham chiếu các lần trước không còn trên bản ghi ngoại lệ.                                                                                                                           | Ghi nhận       |
| PH-09  | Hủy toàn bộ order: ORDER.ThoiDiemDong vẫn NULL sau khi order chuyển 'Đã hủy'.                                                                                                                                                                                                                                                                                  | Ghi nhận       |
| PH-10  | Đơn giá bình quân lệch do làm tròn khi đảo phiếu: BR19a (10 × 5 và 20 × 7, bình quân 6,33) sau khi hủy phiếu 20 × 7 về 4,99 thay vì 5,00, vì công thức đảo dùng đơn giá đã làm tròn 2 chữ số. Đúng với quy tắc làm tròn tại tài liệu 04 mục G.1.                                                                                                               | Ghi nhận       |
