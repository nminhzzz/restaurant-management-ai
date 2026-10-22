# Thanh toán QR thật qua SePay

Hệ thống đã có sẵn luồng thanh toán QR thật: tạo VietQR đúng số tiền, nhận webhook khi tiền vào
tài khoản, tự xác nhận và phát hành hóa đơn đúng một lần. Chế độ `simulator` chỉ dùng cho test/demo.

Trạng thái thực tế của một hệ thống:

- Số hóa đơn cấp tuần tự theo ngày (`HD-YYYYMMDD-NNNN`), lưu ở `HOA_DON.SoHoaDon` và có unique index.
- Mã giao dịch ngân hàng (`MaGiaoDichNganHang`) và mã ngoại lệ (`NGOAI_LE_THANH_TOAN.MaGiaoDichCong`)
  đều có unique index: webhook gửi lặp không thể tạo hai lần thu tiền.
- QR hết hạn sau 10 phút; một tác vụ nền quét mỗi
  `PAYMENT_QR_EXPIRY_INTERVAL_SECONDS` giây (mặc định 60, đặt 0 để tắt) nên QR không bị treo khi
  không ai mở màn hình.
- Nút "Kiểm tra lại" gọi API danh sách giao dịch của SePay cả khi QR đã hết hạn hoặc đang chờ xác
  minh — dùng khi webhook bị lỡ.
- Hoàn tiền bắt buộc lưu mã tham chiếu (`MaThamChieuHoan`) và số tiền thực hoàn (`SoTienHoan`).

## 1. Chuẩn bị

- Tài khoản SePay đã liên kết tài khoản ngân hàng nhận tiền.
- Một URL HTTPS công khai trỏ tới API. Chưa có domain thì dùng tunnel tạm:

  ```bash
  cloudflared tunnel --url http://localhost:8000
  # hoặc: ngrok http 8000
  ```

  Lấy URL `https://<random>.trycloudflare.com` (hoặc `https://<id>.ngrok-free.app`) rồi
  dùng làm webhook. Tunnel tắt là webhook ngừng hoạt động, chỉ phù hợp để kiểm thử.

## 2. Cấu hình `.env`

```dotenv
PAYMENT_GATEWAY=sepay
SEPAY_BANK_ACCOUNT=0123456789          # số tài khoản nhận tiền
SEPAY_BANK_CODE=MBBank                 # mã ngân hàng SePay dùng trong QR
SEPAY_ACCOUNT_NAME=NGUYEN VAN A        # tên chủ tài khoản
SEPAY_WEBHOOK_API_KEY=<khoá bí mật>    # đặt trong SePay, gửi qua header Authorization
SEPAY_API_TOKEN=<token SePay>          # cho nút "Kiểm tra lại"
SEPAY_PAYMENT_PREFIX=TT                # nội dung chuyển khoản: TT<MaGiaoDich>
PAYMENT_QR_EXPIRY_INTERVAL_SECONDS=60  # quét QR hết hạn; 0 = tắt
SEPAY_POLL_INTERVAL_SECONDS=30         # tự đọc danh sách giao dịch khi chưa có webhook; 0 = tắt
```

Không commit `.env`. Nếu cấu hình thiếu hoặc còn placeholder `...`, API từ chối khởi động thay vì
tạo QR hỏng. `SEPAY_API_TOKEN` là tuỳ chọn, nhưng nên có: nó bật nút "Kiểm tra lại" và nhánh
đồng bộ định kỳ. Nếu chưa có domain HTTPS để đặt webhook, đặt `SEPAY_POLL_INTERVAL_SECONDS=30`
để API tự đối chiếu danh sách giao dịch (chậm hơn webhook tối đa một chu kỳ); khi có domain thì
webhook vẫn là đường chính và có thể đặt chu kỳ poll lớn hơn hoặc 0.

## 3. Cấu hình webhook trên SePay

- URL: `https://<domain>/api/v1/sales/webhooks/sepay`
- Phương thức: `POST`
- Xác thực: header `Authorization: Apikey <SEPAY_WEBHOOK_API_KEY>`
- Sự kiện: tiền vào tài khoản (transfer in).

SePay gửi `id`, `transferType`, `transferAmount`, `code`/`content`. Mã giao dịch của hệ thống nằm
trong nội dung chuyển khoản dạng `TT<MaGiaoDich>`; webhook đối chiếu mã, số tiền và order.
Gửi lặp cùng một `id` được trả `duplicate`, không tạo hóa đơn thứ hai.

## 4. Kiểm tra cấu hình

```bash
curl -s http://localhost:8000/health | jq .payment
# {"gateway":"sepay","bank_code":"MBBank","bank_account":"***6789",
#  "webhook_configured":true,"live":true}
```

`live: false` nghĩa là API vẫn đang chạy simulator hoặc thiếu biến môi trường.

## 5. Chuyển tiền thật lần đầu

```bash
API_BASE_URL=http://localhost:8000 \
SMOKE_USERNAME=quanly SMOKE_PASSWORD='...' \
uv run --project apps/api python scripts/sepay_smoke.py
```

Script tạo một order 1 món trên bàn trống, in số tiền + nội dung `TT<id>` + ảnh VietQR, rồi chờ.
Mở app ngân hàng, chuyển đúng số tiền và nội dung. Kết quả đúng:

1. Webhook được gọi, giao dịch sang `Thành công`, order `Đã thanh toán`.
2. Hóa đơn phát hành đúng một lần, số dạng `HD-20261021-0001`.
3. Script in `OK: paid. Invoice ...`.

Nếu quá 10 phút: QR hết hạn, script tự gọi "Kiểm tra lại" để thử nhánh đọc danh sách giao dịch.

Kiểm tra thủ công trên giao diện: Bán hàng → Thanh toán → QR phải hiển thị đúng số tài khoản thật.

## 6. Khi tiền về không khớp

Tiền đến muộn, sai số tiền, thu trùng hoặc order đã đóng được đưa vào
`Báo cáo → Thanh toán → Khoản chuyển khoản ngoại lệ` để quản lý xử lý:

- **Áp dụng**: cộng khoản tiền vào order còn mở và phát hành hóa đơn đúng một lần.
- **Đã hoàn tiền**: bắt buộc nhập mã tham chiếu hoàn tiền và số tiền hoàn. Hệ thống chỉ ghi nhận;
  việc chuyển tiền lại cho khách thực hiện ở app ngân hàng/SePay. Khoản hoàn không cộng hoặc trừ
  doanh thu lần hai.

Ngoại lệ chưa xử lý vẫn hiển thị cho tới khi có kết quả và không bao giờ cộng vào doanh thu.
