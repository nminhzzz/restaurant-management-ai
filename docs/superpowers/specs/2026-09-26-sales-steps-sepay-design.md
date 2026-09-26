# Bán hàng theo bước, hiển thị giá khi gọi món và thanh toán QR qua SePay (Test mode)

- Ngày: 26/09/2026 · Nhánh: `feat/square-design-system`
- Mockup: artifact "Bán hàng theo bước" (https://claude.ai/artifact/ETjSBQFy8EYgnh1TbWWksw). Mockup vẽ khung QR của
  VNPay; bản thật dùng VietQR chuyển khoản của SePay (§5), bố cục khung giữ nguyên.
- Nền giao diện: design system Than chì trong `docs/design/tokens.md`.
- Liên quan: `2026-09-26-assistant-redesign-design.md` (ô chat nổi **không** hiện ở `/sales`).

## 1. Mục tiêu

1. Màn Bán hàng chia thành 3 bước lấy bàn làm trung tâm: **Chọn bàn → Gọi món → Thanh toán**, thêm màn Hoàn tất.
2. Giá món hiện ngay trên ô món và giỏ hàng; tổng tiền cập nhật khi thêm món.
3. Thanh toán QR dùng **VietQR chuyển khoản qua SePay** (Test mode), bật bằng cấu hình; bộ giả lập hiện tại vẫn là
   mặc định. Bản đầu chọn VNPay; đổi sang SePay theo trao đổi ngày 26/09 vì VietQR chuyển khoản đúng cách thu tiền
   tại quầy và khớp mô tả "QR do hệ thống tạo + webhook" sẵn có trong báo cáo.

**Thành công khi:** thu ngân mở bàn, gọi món, thu tiền mà không cần tra mã order; giá trên màn gọi món khớp đơn giá
được chốt khi gửi order; một giao dịch mô phỏng trong SePay Test mode chuyển order sang "Đã thanh toán" và tạo hoá đơn;
`make gate` xanh.

## 2. Ngoài phạm vi

- Không tách/gộp hoá đơn, không thanh toán một phần, không VAT.
- Không lưu số tiền khách đưa và tiền thối (chỉ tính trên giao diện).
- Không làm sơ đồ bàn kéo thả theo mặt bằng thật; sơ đồ là lưới bàn.
- Không dùng thẻ, ví điện tử hay cổng khác; không chạy SePay Live.
- Không đổi schema CSDL, không thêm migration.

## 3. Lỗi giá không hiển thị (sửa trước)

**Nguyên nhân:** `GET /catalog/dishes` ghi cứng `GiaHienTai=None` (`catalog/router.py:120`), trong khi đơn giá thật chỉ
được chốt lúc gửi order qua `active_price_version` (`sales/orders.py:112`).

**Sửa:** `list_dishes` lấy giá đang hiệu lực theo Business Date hiện tại bằng đúng logic của `active_price_version`,
gom trong một truy vấn cho cả trang (không truy vấn từng món). Các chỗ khác đang trả `GiaHienTai=None`
(`router.py:183`, `:507`) sửa theo cùng cách. Món chưa có giá hiệu lực → `GiaHienTai = null`; ô món hiện
"Chưa có giá" và **không** thêm được vào giỏ (tránh order 0 ₫).

**Test hồi quy:** món có phiên bản giá hiệu lực → trả đúng giá; giá lên lịch trong tương lai chưa tính; món không có
giá → `null`; giá trả về bằng `DonGia` của dòng order tạo ngay sau đó.

## 4. API bán hàng

### 4.1 Sơ đồ bàn

`GET /sales/floor` (Quản lý, Thu ngân) trả trong một lần:

```json
{
  "tables": [{"MaBan": 4, "TenBan": "Bàn 04", "TrangThai": "Đang phục vụ",
              "order": {"MaOrder": 142, "MaOrderHienThi": "ORD-260926-142", "MoLuc": "2026-09-26T14:32:00",
                        "SoMon": 4, "TamTinh": 248000}}],
  "takeaway": [{"MaOrder": 139, "MaOrderHienThi": "ORD-260926-139", "MoLuc": "2026-09-26T14:18:00",
                "SoMon": 2, "TamTinh": 120000}]
}
```

`order` là order "Đang mở" của bàn (hoặc `null`); `SoMon` = tổng số lượng các dòng chưa hủy; `TamTinh` = tổng thành
tiền các dòng chưa hủy. `takeaway` = order "Mang về" đang mở. Logic trong `sales/service.py`, gom truy vấn (không N+1).

### 4.2 Giữ nguyên

`POST /sales/orders`, `POST /sales/orders/{id}/lines` (gọi thêm món), `POST /sales/orders/{id}/pay/cash`,
`POST /sales/orders/{id}/pay/qr`, hủy QR, đối soát, hoá đơn. Kiểm tra quyền giữ ở tầng API như hiện tại.

## 5. Cổng thanh toán

### 5.1 Adapter

`sales/gateways/` với một giao diện chung, chọn bằng `PAYMENT_GATEWAY=simulator|sepay` (mặc định `simulator`):

| Hàm | Giả lập (`simulator.py`, logic hiện có) | SePay (`sepay.py`) |
| --- | --- | --- |
| `qr_details(payment, order)` | `None` | URL ảnh VietQR, mã thanh toán, ngân hàng, số và tên tài khoản nhận |
| `parse_callback(headers, body)` | HMAC hiện tại | Kiểm API key, đọc số tiền, nội dung, mã giao dịch SePay |
| `find_payment(payment)` | `None` | Tra giao dịch qua API của SePay (xem §10) |

Phần xác nhận chung tách thành `confirm_payment(session, payment_id, amount, bank_ref)` trong `payments.py`: khoá
giao dịch và order (`FOR UPDATE`), idempotent khi đã "Thành công", đối chiếu số tiền với tổng order, tạo hoá đơn, trả
bàn. Webhook giả lập và webhook SePay cùng gọi hàm này; hành vi hiện tại của webhook giả lập giữ nguyên.

### 5.2 SePay

- **Cấu hình** (`core/config.py`, chỉ đọc từ `.env`, không commit): `SEPAY_BANK_ACCOUNT`, `SEPAY_BANK_CODE`,
  `SEPAY_ACCOUNT_NAME`, `SEPAY_WEBHOOK_API_KEY`, `SEPAY_API_TOKEN` (tuỳ chọn, cho "Kiểm tra lại"),
  `SEPAY_PAYMENT_PREFIX` (mặc định `TT`). `PAYMENT_GATEWAY=sepay` mà thiếu tài khoản hoặc API key → lỗi khi khởi động.
  `.env.example` thêm các biến này với giá trị rỗng.
- **Mã thanh toán:** mỗi giao dịch có mã `<prefix><MaGiaoDich>` (ví dụ `TT388`) đặt trong nội dung chuyển khoản.
  Prefix phải khai báo giống hệt trong mục "Cấu trúc mã thanh toán" của SePay để SePay tự tách mã.
- **Tạo QR:** `POST /sales/orders/{id}/pay/qr` như cũ, response thêm `qr_image_url` (URL ảnh VietQR của SePay với
  `acc`, `bank`, `amount` = tổng order, `des` = mã thanh toán), `payment_code`, ngân hàng, số và tên tài khoản nhận
  để hiện kèm mã (khách chuyển tay được nếu không quét). Hết hạn sau 10 phút như hiện tại.
- **Webhook:** `POST /sales/webhooks/sepay` (không cần đăng nhập). Xác thực bằng header
  `Authorization: Apikey <SEPAY_WEBHOOK_API_KEY>` (so sánh bằng `hmac.compare_digest`). Chỉ xử lý
  `transferType = "in"`. Lấy mã thanh toán từ trường `code`, nếu trống thì tìm `<prefix>\d+` trong `content`; gọi
  `confirm_payment` với `transferAmount` và `referenceCode`.
  - Idempotent theo `id` giao dịch SePay (lưu vào `MaThamChieuNganHang`): gửi lại cùng `id` không tạo hoá đơn thứ hai.
  - Đã nhận thì trả HTTP 200 `{"success": true}`, kể cả khi mã không khớp giao dịch nào (để SePay không gửi lại);
    trường hợp không khớp ghi log và `SystemAuditLog`.
  - Sai API key → 401, ghi `SystemAuditLog` như webhook hiện tại.
  - Sai số tiền hoặc giao dịch đã hết hạn → giao dịch sang "Chờ đối soát" theo luồng đối soát hiện có, không tự xác
    nhận.
- **Kiểm tra lại:** `POST /sales/payments/{id}/check` (Quản lý, Thu ngân). Có `SEPAY_API_TOKEN` thì tra giao dịch vào
  gần nhất mang mã thanh toán qua API của SePay rồi gọi `confirm_payment`; không có token thì chỉ trả trạng thái hiện
  tại.
- **Chạy ở máy local:** webhook cần URL công khai HTTPS (cloudflared tunnel) khai báo trong SePay Test mode. Demo: màn
  thu ngân hiện QR, người demo bấm "Giả lập giao dịch" trong trang SePay với đúng số tiền và nội dung chuyển khoản.
- **Test:** không gọi mạng thật; `httpx.MockTransport` cho API tra giao dịch; payload webhook mẫu theo tài liệu SePay.

## 6. Web

### 6.1 Luồng

`/sales` giữ vị trí trong URL: `?step=floor|order|pay&table=<MaBan>&order=<MaOrder>`, nên tải lại trang không mất chỗ.

1. **Chọn bàn** (`floor-step.tsx`): lưới bàn có trạng thái (Trống / Có khách / Đã đặt); bàn có khách hiện tạm tính,
   số món, giờ mở và vạch đen phía trên. Bộ lọc theo trạng thái, ô tra mã order. Chọn bàn có khách → khung bên phải
   hiện tóm tắt order với "Gọi thêm" và "Thanh toán". Chọn bàn trống → bước 2 với order mới. Khung "Mang về" có nút
   "Đơn mới" và danh sách đơn mang về đang mở.
2. **Gọi món** (`order-step.tsx`, tách từ `order-screen.tsx`): thanh ngữ cảnh (bàn, mã order, giờ mở, nút về sơ đồ).
   Lưới món có giá, số lượng đã chọn ở góc phải ô món. Giỏ hàng chia "Món mới" (sửa được số lượng, ghi chú) và "Đã gửi
   bếp" (chỉ xem), có tạm tính từng phần và tổng. "Gửi bếp" → về sơ đồ bàn; "Gửi bếp & thanh toán" → bước 3.
   Order mới dùng `POST /sales/orders`; order đang mở dùng `POST /sales/orders/{id}/lines`.
3. **Thanh toán** (`pay-step.tsx`, tách từ `payment-panel.tsx` và `order-detail.tsx`): hoá đơn tạm bên trái; bên phải
   chọn **Tiền mặt** (ô tiền khách đưa, nút nhanh "Vừa đủ" và các mệnh giá làm tròn, tiền thối, nút "Xác nhận đã thu
   …", khoá khi tiền đưa nhỏ hơn cần thu) hoặc **QR chuyển khoản** (ảnh VietQR, số tiền, ngân hàng, số tài khoản, nội
   dung chuyển khoản có nút sao chép, đếm ngược theo `ThoiDiemHetHan`, "Kiểm tra lại", "Hủy QR", nhãn "Môi trường thử
   nghiệm SePay"). Khi dùng giả lập, khung QR giữ hành vi hiện tại. Trong lúc chờ, trạng thái QR được hỏi lại mỗi 3
   giây.
4. **Hoàn tất** (`done-step.tsx`): số hoá đơn, order, phương thức, tổng, tiền thối (nếu tiền mặt), "In hoá đơn",
   "Về sơ đồ bàn".

Thanh bước (`sales-stepper.tsx`) cho bấm quay lại bước trước; bước sau chỉ bấm được khi đủ điều kiện (có bàn hoặc đơn
mang về để gọi món, có order đang mở để thanh toán). Tra cứu order cũ (đã thanh toán, đã hủy) vẫn làm được qua ô tra mã.

### 6.2 Phụ thuộc mới

Không có. Ảnh QR là URL ảnh VietQR của SePay, trình duyệt tải trực tiếp (máy thu ngân cần mạng).

## 7. Báo cáo

Sửa các chỗ trong `docs/BaoCao_HeThongQuanLyNhaHang.md` đang ghi cổng QR thật nằm ngoài phạm vi: mục 1.4.3, dòng
FR-SALE trong bảng tổng kết (dòng ~1837) và hạn chế số 6 (dòng ~1954). Nội dung mới: VietQR chuyển khoản qua SePay
(Test mode) bằng adapter, xác nhận bằng webhook có API key và API tra giao dịch; giả lập giữ cho kiểm thử tự động.
Tìm thêm các chỗ nhắc "chữ ký webhook" để mô tả đúng cách SePay xác thực (API key trong header).

## 8. Kiểm thử

**API:**
- Giá món (§3).
- `/sales/floor`: bàn trống, bàn có order, đơn mang về, tạm tính bỏ dòng đã hủy, quyền (Thủ kho → 403).
- Adapter SePay: URL ảnh QR đủ tham số; tách mã thanh toán từ `code` và từ `content`.
- Webhook SePay: thành công; sai API key → 401; `transferType = "out"` bỏ qua; mã không khớp → ghi log, trả success;
  sai số tiền → "Chờ đối soát"; gửi trùng cùng `id` không tạo hoá đơn thứ hai; giao dịch đã hết hạn.
- `check` với API tra giao dịch giả; cấu hình thiếu khoá → lỗi khi khởi động; webhook giả lập giữ nguyên hành vi.

**Web:** chuyển bước và giữ `?step=`; bàn có khách hiện "Gọi thêm"/"Thanh toán"; ô món hiện giá, món chưa có giá không
thêm được; tổng giỏ đúng; "Gửi bếp" gọi đúng endpoint cho order mới và order đang mở; tiền thối đúng, nút xác nhận
khoá khi tiền khách đưa nhỏ hơn cần thu; QR và nội dung chuyển khoản hiện khi có `qr_image_url`; hoàn tất hiện số hoá
đơn.

## 9. Bảo mật

- `SEPAY_WEBHOOK_API_KEY`, `SEPAY_API_TOKEN` chỉ trong `.env`; không log, không trả về client.
- Webhook là endpoint công khai: xác thực API key trước mọi xử lý, đối chiếu số tiền với tổng order tính lại ở server,
  idempotent theo mã giao dịch SePay, khoá bản ghi khi xác nhận. SePay xác thực bằng API key trong header (không ký
  nội dung), nên chỉ nhận qua HTTPS.
- Trạng thái thanh toán chỉ đổi qua webhook hoặc API tra giao dịch phía server; web không tự đánh dấu đã thanh toán.
- Tổng tiền luôn tính ở server; web chỉ hiển thị.

## 10. Rủi ro

- **API tra giao dịch trong Test mode:** chưa xác nhận API tra giao dịch của SePay chạy với tài khoản Test mode. Plan
  có một bước kiểm tra sớm; nếu không chạy, "Kiểm tra lại" chỉ đọc trạng thái, còn xác nhận dựa vào webhook và luồng
  đối soát thủ công hiện có.
- **Định dạng payload:** tên trường lấy theo tài liệu SePay; test dùng payload mẫu, kiểm lại bằng một giao dịch mô
  phỏng thật trước khi đóng giai đoạn.
- **Tunnel khi demo:** không có URL công khai thì webhook không tới; cần chuẩn bị cloudflared trước buổi bảo vệ.
- **Đổi luồng quen thuộc:** các thao tác giữ tên gọi cũ ("Gửi bếp", "Thanh toán").
