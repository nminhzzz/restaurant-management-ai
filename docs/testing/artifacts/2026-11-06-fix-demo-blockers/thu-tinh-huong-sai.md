# Thử các tình huống sai — 06/11/2026

Thử nhanh để chuẩn bị demo, **không cộng vào 223/247**. Mỗi tình huống chạy một lần.

- **Môi trường:** nhánh `fix/demo-blockers`, MySQL 8.4, bản sao dữ liệu của CSDL `restaurant`, `PAYMENT_GATEWAY=simulator`.
- **Web:** bản build production, Chrome headless. **API:** gọi trực tiếp bằng tài khoản `seed_*`.

## Trên giao diện

| Thao tác | Kết quả |
|---|---|
| Món còn 2 suất, bấm chọn lần thứ 3 | Hiện "Món đang hết nguyên liệu.", giỏ giữ 2 suất |
| Bấm Gửi bếp với lượt chọn đã giữ hết phần còn lại | Bị từ chối "Món đang hết nguyên liệu." (tái hiện lỗi TC-INV-09) |
| Tìm món Nháp ở màn gọi món | "Không có món nào khớp" |
| Bếp bấm Tạo phiếu kiểm kê khi còn lượt giữ | "Còn lượt giữ chỗ chưa gửi, hãy xử lý trước khi kiểm kê." |
| Bếp hủy phiếu nhập có lô đã xuất | "Phiếu nhập đã phát sinh xuất kho, phải điều chỉnh qua kiểm kê định kỳ."; phiếu vẫn Hiệu lực |
| Thu ngân mở `/reports` | Bị đưa về `/sales` |
| Đăng nhập sai mật khẩu | Ở lại trang đăng nhập, hiện "Yêu cầu không thực hiện được." (API trả "Tên đăng nhập hoặc mật khẩu không đúng.") |
| Bấm Hủy lượt chọn | Hiện hộp xác nhận của trình duyệt; lượt thử này bấm Cancel. Nhánh OK chỉ kiểm tra qua API |

## Qua API

| Thao tác | HTTP | Phản hồi |
|---|---|---|
| Đăng nhập sai mật khẩu | 401 | Tên đăng nhập hoặc mật khẩu không đúng. |
| Thu ngân nhập kho, xem báo cáo, xem tài khoản; Bếp thu tiền | 403 | Bạn không có quyền thực hiện chức năng này. |
| Giữ món chưa có công thức | 422 | Món chưa có công thức hiệu lực. |
| Nhập kho số lượng âm | 422 | Lỗi kiểm tra dữ liệu `quantity` phải lớn hơn 0 |
| Xuất hủy vượt tồn | 422 | Không đủ tồn kho khả dụng. |
| Giữ vượt khả dụng; bàn khác giữ phần đã bị giữ | 422 | Không đủ tồn kho khả dụng. |
| Mở kiểm kê khi còn lượt giữ | 422 | Còn lượt giữ chỗ chưa gửi, hãy xử lý trước khi kiểm kê. |
| Gửi bếp lần hai cùng `request_id` | 201 | Trả về đúng order cũ |
| Hủy phiếu nhập có lô đã xuất | 422 | Phiếu nhập đã phát sinh xuất kho, phải điều chỉnh qua kiểm kê định kỳ. |
| Hủy món không có lý do | 422 | Cần lý do hủy. |
| Hủy món Chờ làm có lý do | 200 | Lô hoàn lại đủ 5 kg |
| Chuyển Chờ làm sang Đã phục vụ | 422 | Không thể chuyển từ Chờ làm sang Đã phục vụ. |
| Hủy món đã phục vụ | 422 | Chỉ hủy món ở trạng thái Chờ. |
| Giải phóng bàn khi order chưa thanh toán | 200 | Bàn về Trống (đúng FR-CAT-18) |
| Khi đang chờ QR: tạo QR lần hai, thu tiền mặt, gọi thêm | 422 | Order đã đóng. |
| Webhook sai chữ ký | 401 | Chữ ký không hợp lệ. |
| Webhook sai số tiền | 422 | Số tiền không khớp.; order vẫn Chờ xác nhận thanh toán |
| Webhook đúng | 200 | Order Đã thanh toán, có hóa đơn |
| Webhook đúng gửi lại | 200 | Cùng số hóa đơn |
| Hủy lượt chọn | 200 | Khả dụng được trả lại, giữ lại được 2 suất; lô vẫn 2 kg |

## Chưa thử

Webhook SePay, QR hết hạn và gửi bếp sau khi giữ món hết hạn không chạy trong lượt này.
