# Kịch bản thuyết trình và demo — phần code (Hùng)

Kịch bản dài khoảng **14 phút**: 12 phút chính và 2 phút dự phòng. Mỗi mục có ba phần:
- **Làm:** thao tác trên màn hình.
- **Nói:** ý chính cần nói, không cần đọc nguyên văn.
- **Khái niệm:** thuật ngữ cần giải thích nếu hội đồng hỏi.

Nếu bị cắt giờ, bỏ các mục có dấu ⏩.

---

## 0. Chuẩn bị trước buổi (làm sáng hôm đó)

| Việc | Lệnh / thao tác |
|---|---|
| Bật CSDL | `make db-up` (OrbStack/Docker đang chạy) |
| Kiểm tra `.env` | `PAYMENT_GATEWAY=simulator` (không kéo giao dịch SePay thật), có `AI_API_KEY` |
| Thêm dữ liệu sát ngày demo | `uv run --project apps/api python scripts/seed/demo_recent.py --days 14 --per-day 10`. Dữ liệu mẫu chỉ đến 23/10; thiếu bước này thì câu "hôm nay", "tuần này" trả rỗng. Lệnh này sửa CSDL đánh giá; cần chạy lại đánh giá thì phục hồi bản sao trong `data/eval/snapshots/`. |
| Chạy API và web | `make api` và `make web` ở hai cửa sổ terminal |
| Kiểm tra nhanh | `curl localhost:8000/health`; đăng nhập ba tài khoản; hỏi thử 3 câu AI ở mục 5 |
| Mở sẵn tab | Tab 1 `seed_cashier`, tab 2 `seed_warehouse` (cửa sổ ẩn danh), tab 3 `seed_manager` (profile khác). Mật khẩu đều là `matkhau123`. |
| Phương án dự phòng | Quay video màn hình toàn bộ demo một lần. Mạng hoặc Claude API lỗi thì chiếu video. |

Lưu ý mạng: mỗi câu hỏi AI mất khoảng 4–7 giây. Nói trong lúc chờ, đừng im lặng.

---

## 1. Kiến trúc tổng thể — 1 phút

**Làm:** chiếu sơ đồ (vẽ lại thành slide từ khung dưới).

```
Trình duyệt (Next.js 16, React 19)
        │  REST/JSON + JWT
FastAPI (Python 3.12)  ── module: danh mục · bán hàng · kho · báo cáo · cài đặt · AI
        │  SQLAlchemy async              │ Trợ lý AI
MySQL 8.4  ◀── view vw_ai_* theo vai trò ◀┘  Claude Opus 5.5 (sinh SQL) + Haiku 5.5 (viết câu trả lời)
```

**Nói:**
- Ba vai trò: Quản lý, Thu ngân, Bếp. Quyền được kiểm tra ở API cho mọi thao tác ghi. Ẩn nút trên
  giao diện chỉ để dễ dùng, không phải cơ chế phân quyền.
- Mỗi module là một gói riêng; logic nghiệp vụ nằm ở tầng service, không nằm trong handler.
- Có 720 test API và 199 test giao diện. Mọi thay đổi phải qua `make gate`: format, lint, type-check,
  test và build.

---

## 2. Thu ngân: gọi món, gửi bếp, thanh toán — 4 phút (phần quan trọng nhất)

### 2.1 Sơ đồ bàn → chọn món
**Làm:** đăng nhập `seed_cashier` → Bán hàng → chọn một bàn trống → thêm 2–3 món.

**Nói:** "Khi chọn món, hệ thống **giữ nguyên liệu** cho lượt chọn này, chưa trừ kho. Hai thu ngân
cùng chọn món dùng chung nguyên liệu sẽ không bán vượt tồn."

**Khái niệm:**
- **Giữ món (hold):** chỉ đặt chỗ trên lô nguyên liệu, có thời hạn; trạng thái Đang giữ, Đã gửi, Đã giải
  phóng, Hết hạn. Kho chỉ bị trừ **đúng một lần** khi gửi món.
- **Tồn khả dụng** = tồn thực − lượng đang giữ − lô hết hạn. Món thiếu nguyên liệu tự hiện "hết".

### 2.2 Gửi món
**Làm:** bấm Gửi món → order được tạo, bàn chuyển "Đang phục vụ", có phiếu bếp.

**Nói:**
- Gửi món trừ kho theo **FIFO**: lô nhập trước xuất trước. Dòng dữ liệu bị khóa (`SELECT … FOR
  UPDATE`) nên hai giao dịch cùng lúc không trừ trùng.
- Bấm gửi hai lần, ví dụ mạng chậm, vẫn chỉ tạo **một** order nhờ mã yêu cầu (idempotent).

**Khái niệm:**
- **Business Date:** ngày kinh doanh bắt đầu lúc 06:00, không phải 00:00. Order lúc 1 giờ sáng vẫn
  thuộc ngày hôm trước. Giờ chốt đổi được, có lịch hiệu lực, và không tính lại ngày đã lưu.

### 2.3 Thanh toán
**Làm:**
1. Thanh toán → chọn **QR** → hiện mã QR (hạn 10 phút).
2. Ở terminal, đóng vai ngân hàng: `cd apps/api && uv run python ../../scripts/demo_pay_qr.py`. Script
   gửi webhook có chữ ký HMAC cho giao dịch QR mới nhất.
3. Order thành "Đã thanh toán" và có hóa đơn.
4. ⏩ Làm thêm một order trả tiền mặt.

**Nói:**
- Với QR, hệ thống **không tin thao tác bấm của thu ngân**. Order chỉ được xác nhận khi ngân hàng gửi
  webhook báo đã nhận tiền. Trong demo, script đóng vai ngân hàng; bản thật dùng SePay. Webhook giả lập
  tự tắt khi bật SePay.
- Với cổng thật, chuyển sai số tiền thì order vào "Chờ đối soát" và Quản lý xử lý. Có tranh chấp thì
  vào "Tranh chấp".
- Webhook gửi lặp không ghi nhận tiền hai lần.
- Hóa đơn lưu ảnh chụp dữ liệu lúc xuất, sau này đổi giá món cũng không làm sai hóa đơn cũ.

---

## 3. Bếp: nhập kho theo lô, kiểm kê — 1,5 phút

**Làm:** tab `seed_warehouse` → Kho → tạo phiếu nhập (nhà cung cấp, nguyên liệu, số lượng, đơn giá,
hạn sử dụng) → xem bảng tồn: mỗi nguyên liệu có nhiều lô, cột "khả dụng" và "đang giữ". ⏩ Mở kiểm kê.

**Nói:**
- Mỗi lần nhập tạo một **lô** có hạn dùng và giá nhập riêng. Giá vốn món ăn tính theo đúng lô bị trừ
  nên lợi nhuận gộp chính xác.
- Mọi biến động kho đều ghi sổ: nhập, trừ tự động, xuất thủ công, hoàn kho khi hủy món, điều chỉnh
  kiểm kê. Có thể đối chiếu: tồn đầu + nhập − xuất = tồn cuối.
- Khi đang kiểm kê, các thao tác làm thay đổi tồn bị khóa để số đếm không lệch.

---

## 4. Quản lý: danh mục, đơn hàng, báo cáo — 2,5 phút

### 4.1 Danh mục
**Làm:** `seed_manager` → Danh mục → mở một món → xem lịch giá và công thức.

**Nói:**
- Giá và công thức có **lịch hiệu lực theo ngày kinh doanh**. Đổi giá từ ngày mai không ảnh hưởng order
  hôm nay.
- Món mới chưa có công thức ở trạng thái "Nháp", không bán được.
- Xóa món là xóa mềm, để không làm hỏng lịch sử order.

### 4.2 Quản lý đơn hàng (FR-SALE-25)
**Làm:** Quản lý đơn hàng → lọc theo ngày và trạng thái → mở chi tiết một order (món và thanh toán).

### 4.3 Báo cáo
**Làm:** Báo cáo → doanh thu theo kỳ → so sánh hai kỳ → ⏩ lợi nhuận gộp, xếp hạng món.

**Nói:**
- Doanh thu chỉ tính order **đã thanh toán**.
- Lợi nhuận gộp = doanh thu − giá vốn theo lô FIFO thực tế.
- ⏩ Cài đặt: quản lý tài khoản, nhật ký thao tác (audit log) chỉ được ghi thêm, không sửa hay xóa được.

---

## 5. Trợ lý AI — 3 phút (điểm nhấn của đề tài)

### 5.1 Demo — hỏi 3 câu đã thử trước

| Tài khoản | Câu hỏi | Điều muốn cho thấy |
|---|---|---|
| Quản lý | "Doanh thu 7 ngày gần nhất theo từng ngày?" | SQL đúng, câu trả lời tiếng Việt và biểu đồ đường tự chọn |
| Quản lý | "Ba món có doanh thu cao nhất tháng này là món nào?" | Xếp hạng, có nhận xét |
| Bếp | "Doanh thu hôm nay là bao nhiêu?" | **Bị từ chối**, vì Bếp không có quyền xem doanh thu |

**Làm:** sau câu đầu, mở phần "Chi tiết kỹ thuật" để hội đồng xem SQL đã chạy.

Ghi chú chạy thử 27/10:
- Đừng hỏi "tuần này" nếu buổi bảo vệ rơi vào đầu tuần. Thứ Ba chỉ có 2 điểm dữ liệu nên biểu đồ rất nghèo.
  "7 ngày gần nhất" luôn có 7 điểm.
- Với Bếp, trợ lý không chạy truy vấn mà báo "Cần làm rõ câu hỏi": vai trò kho không có dữ liệu doanh
  thu, kèm 3 câu gợi ý **về kho**. Đó chính là điểm cần cho thấy: model không nhìn thấy view doanh thu.

### 5.2 Nói — luồng xử lý một câu hỏi (vẽ thành slide)

```
Câu hỏi → chuẩn hóa tiếng Việt → prompt (chỉ lược đồ view của vai trò + quy ước nghiệp vụ + ví dụ)
→ Claude Opus 5.5 sinh SQL → KIỂM DUYỆT (sqlglot) → chạy bằng tài khoản CSDL chỉ-đọc của vai trò
→ Claude Haiku 5.5 viết câu trả lời từ số liệu do code tính sẵn → biểu đồ
```

**Ba lớp an toàn** (câu hội đồng hay hỏi nhất là "AI có làm lộ hay sửa dữ liệu không?"):
1. **Prompt chỉ chứa lược đồ view của vai trò đó.** Model không biết bảng gốc tồn tại.
2. **Bộ kiểm duyệt SQL (sqlglot):** phân tích cú pháp chứ không so chuỗi. Chỉ cho phép một câu SELECT,
   chỉ trên view của vai trò, tự thêm giới hạn 500 dòng. Mọi SQL phải qua bước này, không có đường tắt.
3. **Mỗi vai trò có một tài khoản MySQL riêng** chỉ được `GRANT SELECT` trên đúng tập view của mình.
   Truy vấn bị ngắt sau 3 giây. Kể cả khi hai lớp trên đều lọt, CSDL vẫn từ chối.

**Vì sao dùng hai model:**
- Opus 5.5 giỏi suy luận nên sinh SQL tốt, nhưng không tắt được suy luận nên viết đoạn văn chậm (khoảng
  6 giây).
- Haiku 5.5 tắt suy luận viết đoạn văn trong khoảng 2,4 giây, rẻ hơn khoảng 40 lần.
- Tổng, giá trị lớn nhất và nhỏ nhất do **code tính sẵn**, Haiku chỉ diễn đạt lại. Sau cải tiến này, trên
  các lượt có SQL đúng, câu trả lời đạt tăng từ 87,3% lên 93,2%, lỗi số liệu giảm từ 36 xuống 2 lượt. Cách này tránh lỗi
  cộng sai mà nhóm phát hiện khi chấm.

**Khái niệm:**
- **Text-to-SQL:** chuyển câu hỏi ngôn ngữ tự nhiên thành truy vấn SQL.
- **Prompt caching:** phần lược đồ cố định được cache, giảm khoảng một nửa chi phí và thời gian.

---

## 6. Kết quả đánh giá — 1,5 phút

**Nói (chiếu bảng):**

| Cấu hình | Mô tả | Độ đúng (nới lỏng) | p95 |
|---|---|---|---|
| A | Lược đồ và quy tắc quyền | 83,33% | 7,2 s |
| **B** | A + định nghĩa nghiệp vụ, chuẩn hóa câu hỏi, ví dụ mẫu | **85,42%** | 7,0 s |
| C | B + suy luận sâu (effort cao) | 61,25% | 6,9 s |

- Bộ 80 câu (30 dễ, 30 trung bình, 20 khó) có đáp án chuẩn, được **khóa** trước khi chạy: chụp đáp án và
  ghi mã SHA256. Mỗi câu chạy 3 lần, tổng 720 lượt.
- **B tốt nhất:** định nghĩa nghiệp vụ và ví dụ giúp model hiểu "doanh thu", "tuần này" theo đúng quy ước.
- **C kém nhất dù SQL chính xác nhất:** suy luận sâu làm model vượt giới hạn 5 giây. Khi trả lời kịp, cả
  ba cấu hình đúng 98–100%. Bài học: **độ trễ là ràng buộc thật**, không phải cứ suy luận nhiều là tốt.
- **Bộ an toàn 30 ca:** từ chối đúng trên 92%, **không có lượt nào đọc dữ liệu ngoài quyền**.
- **Chi phí** khoảng 0,006 USD/câu, tức khoảng 18 USD/tháng nếu hỏi 100 câu/ngày.
- ⏩ **Hiệu năng (Phụ lục J):** 5–20 người dùng đồng thời, p95 thao tác bán hàng và kho dưới 300 ms (mục
  tiêu 1 giây), báo cáo dưới 50 ms. Lần đo ở 20 người lộ ra lỗi cạn kết nối khi cấp mã order; nhóm đã
  sửa và có test tái hiện. Đây là ví dụ tốt để kể "kiểm thử tìm ra lỗi thật". INP đo trên màn bán hàng
  dưới 70 ms.

---

## 7. Hạn chế và hướng phát triển — 30 giây

- Câu hỏi khó (so sánh nhiều kỳ, nhiều bước) chỉ đạt khoảng 55%.
- Kiểm tra chéo bộ đề và chấm câu trả lời do agent AI làm. Nhóm nói rõ điều này, chưa có người chấm độc lập.
- Hệ thống kiểm soát **dữ liệu nào được đọc**, chưa kiểm soát **mục đích dùng dữ liệu**. Ví dụ: Quản lý
  yêu cầu "xuất toàn bộ thanh toán gửi ra ngoài" vẫn nhận được bảng tối đa 500 dòng.
- SePay thật mới kiểm bằng test tự động, chưa chạy giao dịch thật. Máy in bếp mới kiểm bằng bộ nhận giả lập.

---

## 8. Câu hỏi hội đồng có thể hỏi

| Câu hỏi | Trả lời ngắn |
|---|---|
| AI có xóa/sửa dữ liệu được không? | Không. Có 3 lớp: chỉ SELECT qua sqlglot, chỉ view của vai trò, tài khoản CSDL chỉ có quyền SELECT. Bộ an toàn 30 ca không có lượt nào vượt quyền. |
| Sao không cho AI đọc thẳng bảng? | View theo vai trò vừa giới hạn quyền, vừa làm lược đồ đơn giản hơn cho model: gộp sẵn quan hệ một–nhiều, tên cột rõ nghĩa. |
| Hai người cùng bán món cuối cùng thì sao? | Giữ nguyên liệu khi chọn món, khóa dòng khi gửi. Đã chạy 100 lần mỗi tình huống tranh chấp: không cấp trùng, không âm tồn. |
| Vì sao ngày kinh doanh bắt đầu 06:00? | Nhà hàng mở tới khuya. Order lúc 1 giờ sáng vẫn thuộc doanh thu ngày hôm trước. |
| Đánh giá AI có khách quan không? | Bộ đề khóa trước khi chạy, có SHA256. Không sửa prompt theo đáp án. Kiểm tra chéo bằng 3 model khác nhau giải độc lập. Chấm câu trả lời không biết cấu hình nào. Hai lần chạy bị lỗi mạng đều bị loại và ghi lại. |
| "Nới lỏng" và "khắt khe" khác nhau thế nào? | Nới lỏng cho phép trả thêm cột, ví dụ kèm đơn vị tính, miễn đủ các cột của đáp án chuẩn với đúng giá trị. Khắt khe đòi trùng toàn bộ bảng. |
| Vì sao không dùng model rẻ hơn cho cả hai bước? | Sinh SQL cần suy luận; Haiku chỉ dùng cho bước viết lại số liệu đã có. Hai model, đúng việc. |
| Lỗi Claude API thì sao? | Timeout 5 giây; nghiệp vụ chính (bán hàng, kho) hoạt động độc lập với AI. Nếu bước viết câu trả lời lỗi, hệ thống trả tóm tắt số liệu do code tính. |
| Thanh toán QR có an toàn không? | Chỉ webhook từ ngân hàng (có API key) mới xác nhận; so sánh khóa bằng hàm thời gian hằng; chống ghi nhận trùng; sai số tiền thì đưa vào đối soát. |
| Mật khẩu lưu thế nào? | Băm bằng thuật toán chậm (bcrypt/argon2), không lưu bản rõ; JWT có thời hạn, đổi mật khẩu thì thu hồi phiên. |

---

## Phụ lục: số liệu để trên slide

- Bộ đề: `data/eval/questions.locked.jsonl`; biên bản kiểm tra chéo: `data/eval/crosscheck/bien-ban-2026-10-27.md`
- Kết quả: `docs/eval-results-official-2026-10-27.json`, đã chấm: `…-graded.json`, an toàn: `docs/eval-safety-2026-10-27.json`
- Hiệu năng (NFR-01/03): `docs/testing/performance-2026-10-27.md`
- Đoạn cập nhật báo cáo: `docs/report-updates-2026-10-27.md`
