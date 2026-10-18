# Trả nợ kỹ thuật ngày 17/10/2026

Phạm vi: sáu khoản đã được người dùng duyệt trong phiên; giữ nguyên mọi thay đổi đang có.

## Thiết kế và tiêu chí

- [x] Bàn: CSDL là nguồn trạng thái; bàn đang phục vụ không bị bộ lọc coi là trống khi order đã
  thanh toán/chờ đối soát. Bổ sung thao tác giải phóng có quyền API, kiểm tra order hiện tại và
  khóa bàn. Tạo/đổi bàn phải kiểm tra bàn trống; thanh toán muộn không được giải phóng bàn khác.
  Thêm liên kết `BAN.MaOrderDangPhucVu` theo đặc tả, migration backfill và ca hồi quy.
- [x] Business Date: hàm dùng chung trả khoảng tháng [06:00 ngày đầu, 06:00 ngày đầu tháng sau).
  Chốt giá vốn, backfill và báo cáo hao hụt dùng đúng hàm; test trước/sau ranh giới cả hai đầu.
- [x] CI: job MySQL 8.4 riêng khởi tạo hai schema, migration/view/tài khoản AI, chạy integration
  và thất bại nếu có ca skip. Không dùng khóa LLM hoặc dịch vụ ngân hàng thật.
- [x] Seed: không nuốt lỗi; savepoint cho chứng từ bị từ chối, thống kê nguyên nhân/thành công,
  xác nhận bất biến cuối lượt và trả lỗi khi thiếu quy mô mục tiêu. Làm tròn chi phí DECIMAL.
- [x] AI: hai bảng hạ tầng MySQL giữ cache SQL có TTL, Business Date, vai trò, provider/model,
  lược đồ/giới hạn trong khóa; hạn mức cập nhật nguyên tử và commit trước mỗi lần sinh SQL.
  Worker/restart dùng chung DB, không dùng bộ đếm RAM. SQL cache vẫn qua guard khi đọc.
  Bảng hạ tầng được ghi riêng khỏi mô hình nghiệp vụ trong tài liệu.
- [x] Tài liệu: thay danh sách nợ cũ bằng trạng thái có bằng chứng, phân biệt bộ 95 câu cũ và
  kế hoạch mới 80 câu + 30 câu phát triển; không bịa kết quả của kế hoạch mới hoặc SUS/UAT.
- [x] Xác minh: test hồi quy, MySQL thật, browser, `make gate`, review độc lập; lưu kết quả mới
  và giữ nguyên bằng chứng của lượt kiểm chứng trước.

## Thực thi

Các miền Business Date, seed và trạng thái AI có thể triển khai độc lập; điều phối giữ phần bàn,
CI, migration nối tiếp và tài liệu. Chỉ chạy migration trên schema thử trong phiên này.


## Kết quả cuối

`make gate` xanh: 479 test API, 157 test web; 10 ca MySQL integration qua không skip.
Seed MySQL 12 tháng/365 order đúng mục tiêu và toàn vẹn. Hai phát hiện review về deadlock cache
và dữ liệu bàn cũ đã được sửa và kiểm tra lại độc lập.

Bằng chứng: [nhật ký kết quả](../testing/technical-debt-2026-10-17.md).
Không commit/push; migration chỉ áp dụng schema thử. SUS/UAT và các phần nghiệm thu ngoài sáu
khoản này không được đánh dấu hoàn thành từ kết quả kỹ thuật.
