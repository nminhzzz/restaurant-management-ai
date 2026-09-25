# Checklist tương thích thiết bị/trình duyệt (NFR-13, NFR-17)

NFR-13 — tối ưu thao tác trên tablet: chạm nhanh, bàn phím số cho số lượng, hoạt động tốt cả hai chiều
màn hình (portrait/landscape). NFR-17 — hoạt động ổn định trên Chrome, Edge, Safari, cả máy tính và
tablet.

Thực hiện checklist này cho mỗi màn hình chính, trên đủ tổ hợp thiết bị/trình duyệt ở mục 1, trước khi
mời người tham gia vào buổi UAT trên tablet thật.

## 1. Ma trận thiết bị × trình duyệt

| Thiết bị | Trình duyệt | Chrome | Edge | Safari |
| --- | --- | --- | --- | --- |
| Desktop/laptop (Windows hoặc macOS) | | ☐ | ☐ | ☐ (macOS) |
| iPad (hoặc tablet iOS tương đương) | | ☐ (Chrome iOS) | — | ☐ (Safari, bắt buộc) |
| Tablet Android | | ☐ (bắt buộc) | ☐ | — |

Ghi chú: trên iOS, mọi trình duyệt đều dùng chung engine WebKit của Safari — vẫn nên bật một dòng riêng
để bắt lỗi UI Chrome-for-iOS đặc thù (thanh địa chỉ, safe-area).

## 2. Tiêu chí kỹ thuật cần kiểm tra trên mỗi màn hình

- **Touch target ≥ 44px**: mọi nút bấm, ô nhập, item danh sách có thể chạm được đều có vùng chạm tối
  thiểu 44×44px (đo bằng DevTools hoặc thước ảo), kể cả khi hai nút liền kề (không dính/chồng vùng chạm).
- **Bàn phím số cho số lượng**: các ô nhập số lượng món, số lượng nhập/xuất kho, đơn giá mở bàn phím số
  (`inputmode="numeric"` hoặc tương đương) trên tablet, không mở bàn phím chữ đầy đủ.
- **Portrait/landscape**: xoay thiết bị, không bị vỡ layout, không mất nội dung, không phải cuộn ngang.
- **Không bị che bởi bàn phím ảo**: khi mở bàn phím số/chữ, trường đang nhập không bị bàn phím che khuất.

## 3. Checklist theo màn hình chính

| Màn hình | Touch ≥ 44px | Bàn phím số đúng chỗ | Portrait OK | Landscape OK | Chrome | Edge | Safari | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Đăng nhập (`/login`) | ☐ | — | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Bán hàng → Gọi món (chọn món, số lượng, ghi chú) | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | Màn hình dùng nhiều nhất giờ cao điểm — ưu tiên kiểm tra kỹ nhất |
| Bán hàng → Sơ đồ bàn / đổi bàn | ☐ | — | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Bán hàng → Thanh toán (chọn phương thức, mã QR, đối soát) | ☐ | ☐ (mã giao dịch) | ☐ | ☐ | ☐ | ☐ | ☐ | Mã QR phải đọc được rõ trên màn hình tablet |
| Bán hàng → Tra cứu order | ☐ | — | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Danh mục → Món ăn/Công thức/Giá | ☐ | ☐ (giá, định lượng) | ☐ | ☐ | ☐ | ☐ | ☐ | Chủ yếu dùng trên desktop, vẫn kiểm tra tablet vì Quản lý có thể sửa gấp tại quầy |
| Danh mục → Nguyên liệu/Nhà cung cấp | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Kho → Nhập kho | ☐ | ☐ (số lượng, đơn giá) | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Kho → Xuất kho thủ công | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Kho → Kiểm kê định kỳ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | Danh sách dài — kiểm tra hiệu năng cuộn trên tablet |
| Kho → Danh sách tồn kho | ☐ | — | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Báo cáo (doanh thu/xếp hạng/biên lợi nhuận/khung giờ) | ☐ | — | ☐ | ☐ | ☐ | ☐ | ☐ | Chủ yếu desktop; kiểm tra biểu đồ không vỡ khi thu nhỏ |
| Cài đặt → Tài khoản/Phân quyền | ☐ | — | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Cài đặt → Cấu hình chung/Audit log | ☐ | — | ☐ | ☐ | ☐ | ☐ | ☐ | |
| AI Assistant (chat, mở "Xem chi tiết") | ☐ | — | ☐ | ☐ | ☐ | ☐ | ☐ | Kiểm tra bàn phím ảo không che ô nhập câu hỏi |

## 4. Quy trình chạy checklist

1. Chạy `make web` (hoặc bản deploy staging), mở trên từng thiết bị/trình duyệt ở mục 1.
2. Với mỗi màn hình ở mục 3, thực hiện thao tác thật (không chỉ nhìn UI): bấm nút, nhập số lượng, xoay
   thiết bị, để xác nhận từng ô ☐ chứ không suy đoán bằng mắt.
3. Ghi lại ảnh chụp màn hình cho bất kỳ ô nào không đạt, đính kèm vào issue log của `uat.md` nếu phát
   hiện trong buổi UAT, hoặc báo riêng cho nhóm phát triển nếu phát hiện trước đó.
4. Toàn bộ ô ở mục 3 phải ☐ → ☑ trước khi mời người tham gia SUS/UAT thao tác trên tablet thật, để buổi
   đánh giá không bị nhiễu bởi lỗi tương thích thiết bị đã biết trước.
