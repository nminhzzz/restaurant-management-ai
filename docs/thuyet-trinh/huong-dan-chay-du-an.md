# Hướng dẫn chạy dự án

Với máy đang dùng để demo, CSDL `restaurant` đã có sẵn dữ liệu, nên chỉ cần làm **phần 1**. Mở 3 terminal, tất cả bắt đầu ở thư mục gốc dự án:

```bash
cd /Users/nmh/work/Mac/NMHx/Personal/KLTN
```

## 1. Chạy demo (mỗi lần demo)

**Terminal 1: CSDL và backend**

```bash
git checkout fix/demo-blockers
make db-up
make migrate
uv run --project apps/api python scripts/seed/demo_recent.py --days N --per-day 10
make api
```

- **N:** số ngày từ 06/11 đến ngày demo, tính cả hai đầu. Ví dụ demo 12/11 thì N = 7. Nếu demo ngay 06/11 thì bỏ qua lệnh này.
- **Kiểm tra:** chạy `curl -s localhost:8000/health`, phải thấy `"status":"ok"` và `"gateway":"simulator"`.

**Terminal 2: frontend**

```bash
cd apps/web
pnpm build && pnpm start
```

Mở http://localhost:3000. Nên dùng lệnh này thay cho `make web`, vì bản dev hiện huy hiệu "1 Issue" ở góc màn hình.

**Terminal 3: giả lập ngân hàng xác nhận QR**

```bash
cd apps/api
uv run python ../../scripts/demo_pay_qr.py
```

Gõ sẵn lệnh, **chỉ Enter sau khi Thu ngân đã bấm tạo QR**. Lệnh xác nhận giao dịch QR đang chờ mới nhất.

## 2. Tài khoản có sẵn

Hệ thống có ba vai trò và cả ba tài khoản dùng chung mật khẩu **`matkhau123`**:

| Tài khoản | Vai trò | Dùng để demo |
|---|---|---|
| `seed_warehouse` | Bếp/Kho | Nhập kho, phiếu xuất, kiểm kê, công thức |
| `seed_cashier` | Thu ngân | Bàn, gọi món, thanh toán |
| `seed_manager` | Quản lý | Báo cáo, cài đặt, đối soát, AI đầy đủ |

Mỗi tài khoản nên mở trong một cửa sổ riêng (ẩn danh hoặc profile khác) để phiên đăng nhập không đè lên nhau.

## 3. AI

AI không có tiến trình riêng, nó chạy trong backend và gọi Claude API, nên **máy phải có mạng**. `.env` ở thư mục gốc cần có:

```dotenv
AI_API_KEY=<khóa Claude API>        # hoặc ANTHROPIC_API_KEY
LLM_MODEL=claude-opus-5-5
LLM_INTERPRETATION_MODEL=claude-haiku-5-5
AI_READONLY_URL_MANAGER=mysql+asyncmy://ai_manager:<mật khẩu>@localhost:3306/restaurant?charset=utf8mb4
AI_READONLY_URL_CASHIER=mysql+asyncmy://ai_cashier:<mật khẩu>@localhost:3306/restaurant?charset=utf8mb4
AI_READONLY_URL_WAREHOUSE=mysql+asyncmy://ai_warehouse:<mật khẩu>@localhost:3306/restaurant?charset=utf8mb4
```

Hai dòng model là giá trị mặc định, không có cũng được. **Đừng chiếu file `.env` lên màn hình.**

**Kiểm tra:** đăng nhập `seed_manager`, vào Trợ lý AI và hỏi *"Hôm nay có bao nhiêu order?"*.

## 4. ngrok: chỉ cần cho SePay thật

**Demo bằng `simulator` thì không cần ngrok.** Nên dùng `simulator` cho buổi demo, vì SePay thật chưa từng chạy giao dịch nào. Khi muốn thử SePay thật, hãy thử trước buổi demo:

1. Lần đầu dùng ngrok, chạy `ngrok config add-authtoken <token>`.
2. Mở terminal 4 và chạy `ngrok http 8000`, rồi lấy URL `https://....ngrok-free.app`. Chỉ cần mở cổng backend, không mở cổng 3000.
3. Thêm vào `.env`, rồi khởi động lại API:

   ```dotenv
   PAYMENT_GATEWAY=sepay
   SEPAY_BANK_ACCOUNT=<số tài khoản>
   SEPAY_BANK_CODE=<mã ngân hàng>
   SEPAY_ACCOUNT_NAME=<tên chủ tài khoản>
   SEPAY_WEBHOOK_API_KEY=<khóa tự đặt>
   SEPAY_API_TOKEN=<token SePay>
   SEPAY_PAYMENT_PREFIX=TT
   ```

4. Khai webhook trên trang SePay:
   - **URL:** `https://<domain ngrok>/api/v1/sales/webhooks/sepay`
   - **Sự kiện:** tiền vào
   - **Xác thực:** header `Authorization: Apikey <SEPAY_WEBHOOK_API_KEY>`
5. Kiểm tra `curl -s localhost:8000/health`, phải thấy `"gateway":"sepay"` và `"live":true`.
6. Thử xong thì đổi lại `PAYMENT_GATEWAY=simulator`, khởi động lại API và **tắt ngrok ngay**, vì tunnel đang để API lộ ra Internet.

Với ngrok bản miễn phí, URL có thể đổi sau mỗi lần chạy lại, khi đó phải khai lại trên SePay. Trong chế độ `sepay`, `demo_pay_qr.py` bị từ chối, nên phải chuyển tiền thật. Các ca thử chi tiết ở mục 8 của `huong-dan-on-demo.md` và trong `docs/payment-sepay-setup.md`.

## 5. Tắt sau khi demo

- **Backend, frontend, ngrok:** nhấn `Ctrl+C` trong từng terminal.
- **CSDL:** chạy `make db-down`, dữ liệu vẫn được giữ. **Đừng thêm `-v`**, vì lệnh đó xóa toàn bộ dữ liệu.

## 6. Chỉ khi cài trên máy mới

Máy mới cần Docker, `uv`, `pnpm`:

```bash
make setup
make env                   # tạo .env từ mẫu, rồi điền phần 3
make db-up
make migrate
make seed                  # dữ liệu 12 tháng, chỉ chạy trên CSDL chưa có món

export AI_READONLY_PASSWORD_MANAGER=<mật khẩu>
export AI_READONLY_PASSWORD_CASHIER=<mật khẩu>
export AI_READONLY_PASSWORD_WAREHOUSE=<mật khẩu>
./scripts/apply_grants.sh  # tạo view AI và 3 tài khoản chỉ đọc
```

Ba mật khẩu này phải khớp với `AI_READONLY_URL_*` trong `.env`. Dữ liệu từ `make seed` không có các món và lô đã chuẩn bị riêng cho demo (`Thịt bò thăn`, `Bò lúc lắc đặc biệt`...), nên tốt nhất là demo trên máy đã chuẩn bị.

## Lỗi hay gặp

| Hiện tượng | Cách xử lý |
|---|---|
| API báo cổng 8000 đã dùng | Kiểm tra bằng `lsof -nP -iTCP:8000 -sTCP:LISTEN`, rồi tắt đúng tiến trình đó |
| Web không gọi được API, lỗi CORS | Mở bằng `localhost:3000`, không dùng `127.0.0.1` |
| Không kết nối được CSDL | Chạy `docker ps` xem `restaurant-db` đã chạy chưa; nếu chưa thì mở Docker/OrbStack rồi `make db-up` |
| AI báo lỗi hoặc hết giờ | Kiểm tra mạng, chuyển sang 4G rồi hỏi lại; câu "so sánh doanh thu tháng này với tháng trước" từng bị hết giờ |
| Demo sau 09/11 | Hai lô `Thịt bò thăn` sắp hết hạn, cần tạo lại hai phiếu nhập cách nhau một ngày |
