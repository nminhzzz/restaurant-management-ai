# Đợt bổ sung thanh toán ngày 20/10/2026

Phạm vi: hoàn thiện phần thanh toán còn thiếu so với báo cáo — xử lý khoản QR đến muộn/thu trùng
(FR-SALE-16/17), đưa báo cáo thanh toán chưa hoàn tất lên giao diện (FR-REP-02/10), và sửa lỗi
giao diện thanh toán giữ trạng thái QR cũ sau khi quản lý xác nhận.

## Đã xử lý

### Ngoại lệ thanh toán (FR-SALE-16/17)
- Thêm bảng `NGOAI_LE_THANH_TOAN` (migration `4f7a1c2d9e10`): mỗi khoản nhận có một
  `MaGiaoDichCong` duy nhất, lưu số tiền, order/giao dịch liên quan, lý do, trạng thái, người xử lý,
  thời điểm xử lý và ghi chú hoàn tiền. Bảng này bổ sung ngoài 29 bảng trong báo cáo vì đặc tả
  FR-SALE-17 yêu cầu theo dõi khoản ngoại lệ theo mã giao dịch cổng thanh toán.
- Webhook SePay xử lý đúng FR-SALE-16:
  - Tiền đến khi QR đã `Hết hạn`/`Đã hủy` nhưng order còn `Đang mở`, chưa mở lại, chưa có thanh toán
    khác và đúng số tiền: tự xác nhận, phát hành hóa đơn đúng một lần và hủy QR mới hơn đang chờ
    (`LATE_PAYMENT_VOIDS_QR`).
  - Order đã mở lại, đã đóng, đã hủy, đã thu bằng giao dịch khác hoặc sai số tiền: ghi vào danh sách
    ngoại lệ, không tự đổi order. Webhook lặp cùng `MaGiaoDichCong` chỉ tạo một dòng.
  - Sai số tiền vẫn chuyển order sang `Chờ đối soát` như trước, đồng thời lưu ngoại lệ để quản lý
    đối chiếu.
- API mới (chỉ Quản lý): `GET /sales/payment-exceptions`, `POST /sales/payment-exceptions/{id}/resolve`
  với kết quả `applied` (áp dụng vào order, phát hành hóa đơn một lần) hoặc `refunded` (bắt buộc ghi
  chú hoàn tiền ngoài hệ thống). Cả hai ghi audit log `RESOLVE_PAYMENT_EXCEPTION`.
- Quản lý áp dụng được khoản đến muộn cho order `Đóng – chưa thu được tiền`; order trở lại
  `Đã thanh toán`, rời báo cáo closed-unpaid và hóa đơn chỉ phát hành một lần.

### Báo cáo thanh toán trên giao diện
- Tab **Báo cáo → Thanh toán** mới: danh sách giao dịch `Chờ xác nhận`/`Chờ xác minh thanh toán`/
  `Chờ đối soát`/`Tranh chấp` kèm số phút đã chờ (FR-REP-02) và danh sách khoản ngoại lệ với thao
  tác Áp dụng / Đã hoàn tiền.
- Tab **Order hủy** có thêm nhóm `Đóng – chưa thu được tiền` (FR-REP-10): tiền chưa thu, giá vốn,
  lý do, người đóng và thời điểm đóng. Hai trường người đóng/thời điểm lấy từ audit log
  `CLOSE_UNPAID_ORDER` nên API `/reports/closed-unpaid` trả thêm `NguoiDong`, `ThoiDiemDong`.

### Giao diện thanh toán
- Sau khi quản lý xác nhận đã nhận tiền / mở lại thanh toán / đóng chưa thu / áp dụng khoản đến muộn,
  giao diện xoá giao dịch QR đang giữ trong state thay vì hiển thị trạng thái cũ; đồng hồ đếm ngược
  không còn chạy trên giao dịch đã chuyển `Chờ xác minh thanh toán`.
- Order đã thanh toán chỉ hiển thị hóa đơn (tự tải hóa đơn), không còn form nhập tiền khách đưa.
- Xác nhận thanh toán thành công từ màn hình chờ xác minh/áp dụng khoản muộn chuyển sang bước
  hoàn tất như thanh toán tiền mặt, để cột order bên trái không còn trạng thái cũ.

## Kiểm chứng

- API: **540 test qua** (20 integration/slow deselected); mypy và ruff format/check qua.
- Web: **168 test qua**; prettier, eslint, tsc và `next build` qua.
- MySQL 8.4 thật (CSDL demo 6 tháng): đã chạy webhook SePay cho order đóng chưa thu → tạo ngoại lệ →
  áp dụng → order `Đã thanh toán`, hóa đơn phát hành một lần; chạy webhook đến muộn cho QR hết hạn →
  tự xác nhận và hủy QR mới đang chờ.
- Migration `4f7a1c2d9e10` đã áp dụng cho CSDL local `restaurant` và `restaurant_demo`.
