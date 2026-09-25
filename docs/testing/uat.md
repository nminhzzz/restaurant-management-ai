# Kế hoạch nghiệm thu người dùng (UAT)

Theo MT6 (mục 1.3.2 của báo cáo): tổ chức UAT với người có kinh nghiệm vận hành nhà hàng. Ưu tiên mời lại
những người đã tham gia phỏng vấn ở Phụ lục 3 (QL1–QL5, TN1–TN2, OD1–OD2, KH1–KH2) hoặc người có vai trò
tương đương nếu không mời lại được người cũ, để bối cảnh nghiệp vụ họ mô tả khi phỏng vấn khớp với kịch
bản họ sẽ kiểm thử.

## 1. Người tham gia

| Vai trò đóng | Số lượng đề xuất | Tiêu chí chọn |
| --- | --- | --- |
| Chủ nhà hàng/Quản lý | 2 | Từng trực tiếp vận hành nhà hàng, có ra quyết định giá/lợi nhuận |
| Thu ngân/Nhân viên order | 2 | Đã từng thao tác order/thu ngân thực tế (giấy hoặc phần mềm khác) |
| Nhân viên kho | 1–2 | Đã từng nhập/xuất kho, kiểm kê thủ công |

Tối thiểu 5 người, tối đa 6, để mỗi buổi UAT không kéo quá dài mà vẫn phủ đủ ba vai trò.

## 2. Môi trường thử nghiệm

- Dữ liệu: seed mô phỏng 12 tháng theo NFR-03 (`make seed`) — không dùng dữ liệu sản xuất thật.
- Thiết bị: tối thiểu một tablet thật (giả lập quầy order/thu ngân giờ cao điểm) và một laptop/desktop
  (giả lập máy tính văn phòng của Quản lý xem báo cáo).
- Tài khoản: mỗi người tham gia được cấp một tài khoản đúng vai trò họ đóng, tạo trước buổi UAT (không
  dùng chung tài khoản Quản lý cho nhiều người).
- Máy in: nếu có máy in nhiệt thật, kết nối để kiểm tra FR-SALE-27/28 (in phiếu bếp) đúng luồng thật;
  nếu không có, mô phỏng bằng log lệnh in và nêu rõ giới hạn này trong biên bản.
- Cổng thanh toán QR: dùng môi trường sandbox của cổng thanh toán (nếu đã chọn nhà cung cấp — xem Vấn đề
  #3, Phụ lục 2) hoặc mô phỏng webhook thủ công qua script gọi API nội bộ nếu chưa có sandbox.

## 3. Kịch bản theo vai trò (end-to-end)

### 3.1. Thu ngân/Nhân viên order — giờ cao điểm trưa

**Bối cảnh**: quán đang giờ cao điểm trưa, khách vào liên tục, có yêu cầu đặc biệt, có khách đổi bàn và
một trường hợp thanh toán QR bị timeout.

1. Khách vào Bàn 5 (đang Trống). Mở order mới, chọn 3 món, thêm ghi chú "không hành" cho 1 món, Submit.
   → Mã order sinh tự động dạng `ORD-250926-042`; phiếu bếp in tự động; Bàn 5 chuyển "Đang phục vụ".
2. Khách gọi thêm 1 món giữa chừng. → Thêm món thành công, in bổ sung phiếu bếp.
3. Bếp báo hết nguyên liệu một món khác đang được khách của bàn kế bên gọi cùng lúc → món đó tự ẩn khỏi
   danh sách gọi món cho toàn bộ nhân viên order.
4. Khách bàn 5 muốn chuyển sang bàn 8 (Trống) vì bàn rộng hơn. → Đổi bàn, Bàn 5 về Trống, Bàn 8 "Đang
   phục vụ", thao tác ghi audit log.
5. Khách yêu cầu thanh toán QR. Tạo mã QR, đợi quá 10 phút không có xác nhận (mô phỏng bằng thời gian
   rút ngắn ở môi trường thử nghiệm hoặc chờ thật). → Giao dịch chuyển "Hết hạn".
6. Khách báo đã chuyển khoản nhưng hệ thống chưa ghi nhận. Chuyển giao dịch sang "Chờ đối soát", nhập mã
   giao dịch ngân hàng khách cung cấp, đính kèm ảnh chụp xác nhận chuyển khoản.
7. (Bàn giao cho Quản lý xử lý bước đối soát — xem kịch bản 3.2, bước 4.)

**Tiêu chí chấp nhận**: toàn bộ 6 bước thực hiện được không cần trợ giúp kỹ thuật; mã order, trạng thái
bàn, trạng thái giao dịch QR hiển thị đúng và cập nhật theo thời gian thực trên màn hình.

### 3.2. Chủ nhà hàng/Quản lý — vận hành và ra quyết định

1. Đăng nhập, xem sơ đồ bàn hiện tại và tồn kho có nguyên liệu nào dưới mức cảnh báo.
2. Lên lịch thay đổi giá bán cho một món, áp dụng từ Business Date kế tiếp (06:00 ngày mai); xác nhận
   giá cũ vẫn áp dụng cho các order đã tạo trước 06:00.
3. Sửa trực tiếp giá một món khác đang bán sai (ví dụ: nhập nhầm giá) để có hiệu lực ngay lập tức.
4. Xử lý giao dịch "Chờ đối soát" từ kịch bản 3.1 bước 6: kiểm tra mã giao dịch/ảnh chứng từ Thu ngân đã
   nhập, chọn "Xác nhận đã nhận tiền". → Giao dịch "Thành công", hóa đơn tự phát hành.
5. Xem báo cáo biên lợi nhuận gộp tháng hiện tại và báo cáo order bị hủy trong tuần.
6. Đặt câu hỏi cho AI Assistant: "So sánh doanh thu tuần này với tuần trước" và "Món nào có biên lợi
   nhuận thấp nhất tháng này?". Mở mục "Xem chi tiết" để kiểm tra SQL sinh ra hợp lý.
7. Vào Cài đặt, xem audit log của các thao tác vừa thực hiện (đổi bàn, sửa giá trực tiếp, xác nhận đối
   soát) — xác nhận đủ người thực hiện/thời điểm/loại thao tác/dữ liệu trước-sau.

**Tiêu chí chấp nhận**: Quản lý tự đọc được số liệu báo cáo và tự tin dùng để ra quyết định (ghi nhận
qua phỏng vấn ngắn cuối buổi); audit log đầy đủ, không thiếu thao tác rủi ro cao nào.

### 3.3. Nhân viên kho — nhập hàng và kiểm kê

1. Ghi nhận phiếu nhập kho cho một nhà cung cấp quen thuộc: 3 nguyên liệu, số lượng, đơn giá, ngày nhập.
   → Tồn kho tăng đúng theo hệ số quy đổi đơn vị mua hàng.
2. Xuất kho thủ công cho một nguyên liệu bị hỏng, nhập lý do "hết hạn sử dụng". → Tồn giảm đúng, có audit
   log.
3. Thử xuất kho thủ công vượt tồn khả dụng cho một nguyên liệu khác. → Bị từ chối, hệ thống gợi ý kiểm
   kê lại.
4. Thực hiện kiểm kê định kỳ: đối chiếu tồn thực tế (đếm tay/giả lập) với số liệu hệ thống cho toàn bộ
   nguyên liệu trong kho, ghi nhận chênh lệch, xác nhận. → Tồn được ghi đè theo số kiểm kê.
5. Xem danh sách tồn kho, lọc theo nguyên liệu đang dưới mức cảnh báo tối thiểu.
6. Đặt câu hỏi cho AI Assistant: "Nguyên liệu nào sắp hết trong tuần này?" — xác nhận AI không trả lời
   được câu hỏi về doanh thu nếu người dùng cố tình hỏi lệch phạm vi.

**Tiêu chí chấp nhận**: nhân viên kho hoàn thành đủ 6 bước, không nhầm lẫn giữa nhập kho tự động (qua
order) và xuất kho thủ công; hiểu đúng khi nào phải dùng kiểm kê thay vì xuất kho thủ công.

## 4. Tiêu chí chấp nhận chung (Go/No-Go)

| # | Tiêu chí | Ngưỡng |
| --- | --- | --- |
| 1 | Hoàn thành kịch bản vai trò mình đóng không cần người hỗ trợ kỹ thuật can thiệp trực tiếp vào hệ thống | ≥ 80% bước hoàn thành độc lập |
| 2 | Không phát sinh lỗi nghiêm trọng (mất dữ liệu, sai số tiền, sai tồn kho, vượt phân quyền) | 0 lỗi nghiêm trọng |
| 3 | Audit log ghi đủ các thao tác rủi ro cao phát sinh trong buổi UAT | Đối chiếu FR-SET-08, không thiếu bản ghi |
| 4 | Người tham gia đồng ý hệ thống có thể thay thế một phần quy trình hiện tại của họ (giấy/Excel/phần mềm cũ) | Đa số người tham gia (>50%) đồng ý qua phỏng vấn cuối buổi |
| 5 | AI Assistant không trả lời vượt phạm vi vai trò trong bất kỳ câu hỏi nào được thử | 0 vi phạm |

Hệ thống được xem là "đạt UAT" khi cả 5 tiêu chí trên đều thỏa; nếu tiêu chí 2 hoặc 5 không đạt, coi là
**No-Go** cho tới khi lỗi được khắc phục và kiểm thử lại đúng kịch bản đã fail.

## 5. Bảng sign-off

| Người tham gia | Vai trò đóng | Kịch bản đã thực hiện | Đạt / Không đạt | Chữ ký | Ngày |
| --- | --- | --- | --- | --- | --- |
| | Chủ nhà hàng/Quản lý | 3.2 | | | |
| | Chủ nhà hàng/Quản lý | 3.2 | | | |
| | Thu ngân/NV order | 3.1 | | | |
| | Thu ngân/NV order | 3.1 | | | |
| | Nhân viên kho | 3.3 | | | |

**Kết luận Go/No-Go**: ☐ Go ☐ No-Go
**Người chủ trì buổi UAT**: ___________ **Ngày**: ___________

## 6. Nhật ký vấn đề (Issue log)

| Mã | Vai trò phát hiện | Kịch bản/bước | Mô tả vấn đề | Mức độ (Nghiêm trọng/Trung bình/Nhẹ) | Đã xử lý ngay tại buổi? | Ghi chú xử lý |
| --- | --- | --- | --- | --- | --- | --- |
| UAT-ISS-01 | | | | | ☐ Có ☐ Không | |
| UAT-ISS-02 | | | | | ☐ Có ☐ Không | |
| UAT-ISS-03 | | | | | ☐ Có ☐ Không | |

Mọi vấn đề mức "Nghiêm trọng" bắt buộc được vá và kiểm thử lại đúng bước phát hiện trước khi kết luận
"Go". Vấn đề mức "Nhẹ" được ghi nhận làm hướng cải thiện tương lai, không chặn kết luận UAT.
