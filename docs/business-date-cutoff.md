# Lịch mốc giờ ngày kinh doanh

FR-SET-04 cho phép Quản lý chọn mốc giờ theo phút. Mỗi lần thay đổi được lưu trong
`LICH_GIO_BUSINESS_DATE`: `NgayHieuLuc` (DATE, khóa chính), `GioBatDau` (TIME) và
`ThoiDiemBatDau` (DATETIME). Dòng khởi tạo ngày 01/01/1000 giữ mốc giờ ban đầu;
migration không tính lại `BusinessDate` đã lưu trên order, hóa đơn hoặc giao dịch.

Ngày áp dụng là ngày kinh doanh kế tiếp tại thời điểm thay đổi. Thời điểm bắt đầu
ngày chuyển tiếp là giá trị lớn hơn giữa ranh giới đã lên lịch và ngày áp dụng ghép
với giờ mới. Nhờ vậy, đổi từ 06:00 sang 04:30 lúc 05:00 không làm ngày kinh doanh
đang diễn ra kết thúc ngược về quá khứ: ngày kế tiếp bắt đầu lúc 06:00, các ngày sau
bắt đầu lúc 04:30. Đổi sang 08:15 kéo dài ngày hiện tại đến 08:15. Sửa lịch chờ giữ
ranh giới đã lên lịch để không phân loại lại khoảng thời gian đã phát sinh. Chọn
lại giờ đang dùng hủy lịch chờ nếu ranh giới cũ vẫn ở tương lai; nếu ranh giới cũ đã
qua, ngày chuyển tiếp vẫn giữ thời điểm bắt đầu đang chờ, rồi trở lại giờ đang dùng.

`app.shared.business_date` là nơi duy nhất tính ranh giới và khoảng ngày/tháng.
`BusinessDateSession` nạp lịch bất biến vào `ContextVar` khi mở session từ factory
ứng dụng, dùng cho request, tác vụ thanh toán nền, seed và công cụ báo cáo. Context
được khôi phục khi đóng session, kể cả khi lỗi; các request đồng thời không chia sẻ
lịch có thể thay đổi. Mỗi session dùng một ảnh chụp lịch. Thời gian có múi giờ được
chuẩn hóa về Asia/Ho_Chi_Minh trước khi xác định ngày kinh doanh.

API cấu hình trả giờ đang dùng, giờ chờ, ngày hiệu lực và thời điểm chuyển tiếp.
Giao diện hiển thị cả ngày và thời điểm này. Số ngày cảnh báo hạn dùng, thời hạn giữ
món và hạn mức câu hỏi AI phải là số nguyên dương.

Bộ đánh giá có thể dùng `business_date.at_time(moment)` để đặt thời điểm tham chiếu
riêng cho từng tác vụ. Context thời gian hỗ trợ lồng nhau và tự khôi phục; không sửa
đồng hồ chung của tiến trình và không ảnh hưởng câu hỏi chạy đồng thời.
