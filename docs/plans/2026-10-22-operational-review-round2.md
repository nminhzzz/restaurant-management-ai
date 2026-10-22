# Kế hoạch sửa lỗi vận hành vòng 2

Phạm vi được yêu cầu: 10 phát hiện tại commit `cc8f4f8`. Giữ nguyên MySQL 8.4,
Business Date 06:00, phân quyền API và quy trình kiểm duyệt SQL AI.

- [x] Tiền: kiểm thử ngoại lệ đúng số và hoàn một phần; chốt ngoại lệ cùng hóa đơn,
  chặn dùng lại tiền đã hoàn; bọc xác nhận webhook bằng savepoint để lỗi không lưu dở.
- [x] Kho: kiểm thử hủy/giảm món trong phiên kiểm kê; kiểm tra tại đường hoàn kho thật;
  khóa và làm mới nguyên liệu trước khi ghi phiếu nhập, xác minh 5 + 7 = 12 trên MySQL.
- [x] Hold: kiểm thử hold cũ hết hạn bị khách khác giữ hết hàng; phân bổ lại bằng
  công thức/giá hiện hành trong transaction, không lấy lượng đang giữ của khách khác.
- [x] Hóa đơn: thay MAX + retry bằng bộ đếm theo ngày trong cùng transaction;
  migration khởi tạo bộ đếm từ hóa đơn hiện hữu; kiểm thử snapshot cũ trên MySQL.
- [x] SePay: đọc cửa sổ tối đa API, xử lý ID tăng dần, không vượt giao dịch lỗi;
  từ chối tiến con trỏ nếu cửa sổ bị cắt, dùng cập nhật có điều kiện chống ghi đè con trỏ.
- [x] AI: kiểm thử CTE lồng nhau; phân giải bảng theo scope của sqlglot; rút timeout
  provider để dành thời gian cho fallback và tách model Ollama khỏi model thương mại.
- [x] Phiên: kiểm thử 401 của phiên hiện tại và phản hồi cũ đến muộn; xóa đúng phiên,
  đưa về đăng nhập sau đổi mật khẩu; giữ phiên JWT 8 giờ; chưa bổ sung refresh token khi chưa có yêu cầu lựa chọn.
- [x] Chạy các test thất bại trước sửa, test mục tiêu sau sửa, `make gate`, kịch bản
  MySQL tạm; review độc lập và cập nhật tài liệu bằng kết quả thực tế.
