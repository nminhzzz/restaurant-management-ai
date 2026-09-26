# Thiết kế lại màn Trợ lý AI: lịch sử hội thoại và câu trả lời chuẩn hoá

- Ngày: 26/09/2026 · Nhánh: `feat/square-design-system`
- Mockup đã duyệt: artifact "Trợ lý AI nhà hàng" (https://claude.ai/artifact/6mMFMGrnaQf3TdPsy3xT2Y), với một chỉnh sửa:
  mục đang mở trong cột lịch sử **chỉ đổi màu nền**, không có viền trái.
- Nền giao diện: design system Than chì trong `docs/design/tokens.md`.

## 1. Mục tiêu

1. Màn trợ lý có bố cục như các sản phẩm chat hiện nay: cột lịch sử, màn chào, ô nhập dính đáy, câu trả lời dễ đọc.
2. Hỏi trợ lý ngay trên màn đang làm việc qua ô chat nổi ở góc dưới phải, không phải rời màn hiện tại.
3. Người dùng mở lại được các phiên đã hỏi trước đó (chỉ phiên của chính mình).
4. Câu trả lời theo một khuôn cố định: một câu kết luận, 2–4 ý chính, gợi ý câu hỏi tiếp theo.
5. Bảng và biểu đồ hiển thị nhãn tiếng Việt, tiền `185.000 ₫`, ngày `dd/mm/yyyy`.

**Thành công khi:** người dùng không cần đọc tên cột kỹ thuật hay câu SQL để hiểu câu trả lời; mở lại được phiên cũ;
`make gate` xanh; các bất biến bảo mật ở §6 vẫn giữ.

## 2. Ngoài phạm vi

- Không đổi schema CSDL, không thêm migration.
- Không lưu dòng dữ liệu kết quả. Phiên cũ chỉ hiện phần chữ; muốn có bảng hoặc biểu đồ thì bấm "Chạy lại".
- Không xoá hay đổi tên phiên (`TRUY_VAN_AI` là nhật ký kiểm tra).
- Không streaming, không hiện các bước tiến trình giả.
- Sidebar app giữ nguyên, không thu thành cột icon. `AppShell` chỉ thêm chỗ gắn ô chat nổi.
- **Không làm tự động hoá (AI tự thực hiện thao tác ghi).** Trợ lý giữ nguyên thiết kế chỉ-đọc: tài khoản CSDL
  riêng mỗi vai trò chỉ có `SELECT`, `validate_sql` chỉ cho câu `SELECT`. Cho AI ghi dữ liệu (tạo phiếu nhập,
  hủy order…) phá mô hình bảo mật này và cần thêm tool-calling, bước xác nhận, phân quyền từng thao tác. Ghi vào
  báo cáo như hướng phát triển: "AI đề xuất, người xác nhận" (trợ lý trả về liên kết mở sẵn biểu mẫu đã điền,
  người dùng tự bấm lưu).

## 3. API

### 3.1 Câu trả lời có cấu trúc

Bước diễn giải (`pipeline/interpreter.py`) vẫn là **một** lần gọi LLM. Prompt yêu cầu trả về đúng một đối tượng JSON:

```json
{"headline": "…", "highlights": ["…", "…"], "follow_ups": ["…", "…"]}
```

Quy tắc trong prompt: tiếng Việt; chỉ dựa trên kết quả truy vấn; tiền viết dạng `185.000 ₫`; ngày `dd/mm/yyyy`;
`headline` ≤ 1 câu; `highlights` 2–4 ý, mỗi ý ≤ 1 câu, có số liệu cụ thể; `follow_ups` ≤ 3 câu hỏi mà vai trò hiện
tại trả lời được.

Backend chuẩn hoá phần trả về (`pipeline/answer_format.py`, hàm thuần):

- Bỏ code fence nếu có, parse JSON. Chuỗi rỗng bị loại. `headline` cắt ở 300 ký tự; `highlights` tối đa 4 ý,
  mỗi ý 300 ký tự; `follow_ups` tối đa 3, mỗi câu 200 ký tự (giới hạn của `ChatRequest.question` là 500), bỏ câu trùng.
- JSON hỏng hoặc thiếu `headline` → quay về cách cũ: `headline` = toàn bộ văn bản, `highlights = []`,
  `follow_ups = []`. Văn bản rỗng → `FALLBACK_ANSWER` như hiện nay.
- Ghi chú phạm vi (`scope_note(role)`) **vẫn do code tạo**, không đi qua LLM (quy tắc nghiệp vụ 16).

Văn bản `answer` (trả về như cũ và lưu vào `KetQuaTomTat`) được dựng lại từ cấu trúc:

```
<headline>
- <highlight 1>
- <highlight 2>

Phạm vi dữ liệu: …
```

Hàm ngược `split_answer(text)` tách `answer` đã lưu thành `headline` + `highlights` (bỏ đoạn cuối bắt đầu bằng
`Phạm vi dữ liệu:`). Bản ghi cũ viết tự do → toàn bộ thành `headline`.

### 3.2 Nhãn và kiểu cột

`modules/ai/labels.py` (hàm thuần):

- Từ điển tên cột của ba view `vw_ai_*` và các alias hay gặp trong `data/eval` → `{label, kind}`,
  với `kind ∈ text | money | number | date | datetime | percent`.
- Cột không có trong từ điển: đoán `kind` theo tên (`Tien`, `Gia`, `DoanhThu`, `LoiNhuan` → money; `TyTrong`,
  `TyLe`, `PhanTram` → percent; `Ngay`, `Date` → date; `ThoiDiem` → datetime) rồi theo giá trị (toàn số → number);
  `label` = tách CamelCase thành các từ (`TongSoDon` → `Tong So Don`), không đoán dấu.

### 3.3 Hợp đồng `POST /assistant/chat`

`ChatResponse` thêm trường, **không** bỏ trường cũ:

| Trường | Kiểu | Ghi chú |
| --- | --- | --- |
| `answer` | `str` | Như cũ: văn bản đầy đủ gồm ghi chú phạm vi |
| `headline` | `str` | Câu kết luận |
| `highlights` | `list[str]` | 0–4 ý |
| `follow_ups` | `list[str]` | 0–3 câu hỏi |
| `scope_note` | `str \| None` | `None` khi chưa tới bước truy vấn (cần làm rõ, quá hạn mức) |
| `columns` | `list[ColumnMeta]` | Thứ tự cột của `data`; rỗng khi không có dữ liệu |
| `kind` | `"answer" \| "clarify" \| "refused" \| "error"` | Để web chọn cách hiển thị |

Các nhánh lỗi hiện có (`ClarificationNeeded`, `QuotaExceeded`, `BusinessRuleError`, `TimeoutError`) trả
`headline` = thông điệp như hiện nay, `kind` tương ứng (`clarify`, `refused`, `refused`, `error`).

### 3.4 Lịch sử

Router `modules/ai/router.py`, logic trong `service.py`:

- `GET /assistant/sessions?page=&size=` → `Page[SessionSummary]`, `SessionSummary = {id, title, turn_count,
  created_at, last_at}`. `title` = câu hỏi đầu tiên của phiên (cắt 120 ký tự); sắp theo `last_at` giảm dần;
  chỉ các phiên **của người gọi** có ít nhất một lượt hỏi. Mặc định `size=30`, tối đa 100.
- `GET /assistant/sessions/{id}` → `SessionDetail = {id, title, turns: list[TurnOut]}`,
  `TurnOut = {id, question, headline, highlights, status, occurred_at}`, theo thứ tự thời gian.
- Phiên không tồn tại **hoặc thuộc người khác** → `404` với cùng thông điệp, để không lộ phiên có tồn tại hay không.
- Cần đăng nhập (`CurrentUser`); mọi vai trò đều dùng được, mỗi người chỉ thấy phiên của mình.

## 4. Web

### 4.1 Cấu trúc file (`src/features/assistant/`)

| File | Vai trò |
| --- | --- |
| `assistant-screen.tsx` | Bố cục hai cột, giữ state phiên hiện tại, gọi API chat |
| `history-panel.tsx` | Danh sách phiên nhóm theo ngày, nút "Cuộc trò chuyện mới", ngăn kéo dưới `xl` |
| `welcome.tsx` | Màn chào: lời chào theo tên, ô nhập, 4 thẻ câu hỏi gợi ý theo vai trò |
| `composer.tsx` | Textarea tự giãn, đếm `n/500`, Enter gửi / Shift+Enter xuống dòng |
| `assistant-message.tsx` | Một câu trả lời: kết luận, ý chính, khung kết quả, chú thích phạm vi, hành động, hỏi tiếp |
| `result-tabs.tsx` | Tab Biểu đồ / Bảng / SQL (chỉ hiện tab có dữ liệu) |
| `format-cell.ts` | Định dạng giá trị theo `kind`, dùng `lib/format.ts` |
| `chart-view.tsx` | Sửa để dùng nhãn cột và định dạng tiền |
| `use-conversation.ts` | Hook dùng chung cho màn trợ lý và ô chat nổi: danh sách lượt, gửi câu hỏi, `session_id`, trạng thái chờ |
| `assistant-widget.tsx` | Ô chat nổi: nút mở, khung chat thu gọn, gắn trong `AppShell` |

`chat-panel.tsx` được thay bằng `assistant-screen.tsx`. `app/(app)/assistant/page.tsx` bỏ `PageHeader` và cho
màn trợ lý chiếm đủ chiều cao vùng nội dung: `h-[calc(100dvh-5.5rem)]` dưới `lg` (header mobile + padding
`p-4`), `lg:h-[calc(100dvh-3rem)]` từ `lg` (padding `p-6`); chỉ khung hội thoại và cột lịch sử cuộn bên trong.

### 4.2 Hành vi

- **Phiên mới:** "Cuộc trò chuyện mới" xoá hội thoại hiện tại và về màn chào; `session_id` do API trả ở lượt đầu.
  Sau lượt đầu, danh sách lịch sử tải lại để phiên mới xuất hiện ở đầu.
- **Mở phiên cũ:** gọi `GET /assistant/sessions/{id}`, hiện các lượt dạng chữ. Mỗi lượt cũ có nút "Chạy lại"
  (gửi lại câu hỏi vào chính phiên đó). Câu hỏi tiếp theo gửi kèm `session_id` của phiên đang mở.
- **Mục đang mở trong lịch sử:** nền `primary-subtle`, không viền trái.
- **Nhóm lịch sử:** Hôm nay / Hôm qua / 7 ngày trước / Cũ hơn, tính theo giờ máy người dùng từ `last_at`.
- **Đang chờ:** "Đang phân tích câu hỏi · N giây" (đếm thật), khối vuông nhấp nháy; tắt hiệu ứng khi
  `prefers-reduced-motion`. Chặn gửi thêm khi đang chờ.
- **Câu trả lời `answer`:** kết luận in đậm, danh sách ý chính, khung kết quả, chú thích phạm vi có icon khiên,
  nút Sao chép (chép kết luận, ý chính và ghi chú phạm vi) và Hỏi lại, các nút "Hỏi tiếp" (bấm là gửi ngay).
- **`clarify` / `refused`:** khung viền trái màu `warning`, không có khung kết quả. **`error`** và lỗi mạng:
  khung `danger` kèm nút "Thử lại".
- **Tự cuộn** xuống lượt mới nhất khi gửi và khi nhận câu trả lời.
- **Bảng:** tối đa 10 dòng một trang như hiện nay; tiền, số, phần trăm căn phải và `tabular-nums`.
- **Truy cập:** tab kết quả dùng `role="tablist"`; trạng thái chờ `role="status"`; lỗi `role="alert"`; mọi nút chỉ
  có icon đều có `aria-label`; điều hướng được hoàn toàn bằng bàn phím.

### 4.3 Ô chat nổi

- **Vị trí:** nút "Hỏi trợ lý" (nền `ink`, cao 48px) ở góc dưới phải mọi màn trong `(app)`. Bấm mở khung
  420 × 600px (tối đa bằng vùng nhìn trừ lề 20px); dưới `sm` khung chiếm toàn màn hình. Phím tắt `Ctrl/⌘ + K` mở
  hoặc đóng; `Esc` thu nhỏ.
- **Không hiện** ở `/assistant` (đã có màn đầy đủ) và `/sales` (giỏ hàng dính cạnh phải chứa nút "Gửi order" và
  "Thanh toán" nằm đúng góc dưới phải; màn POS cần thao tác nhanh, không để gì che).
- **Giữ trạng thái khi chuyển màn:** gắn trong `AppShell` nên hội thoại và trạng thái mở/thu nhỏ còn nguyên khi
  người dùng chuyển giữa các module. Tải lại trang thì mất hội thoại đang mở, nhưng phiên vẫn có trong lịch sử.
- **Nội dung:** header có tên, nhãn vai trò, nút "Cuộc trò chuyện mới", "Mở toàn màn hình", "Thu nhỏ". Thân dùng lại
  `assistant-message.tsx` ở chế độ gọn (không avatar, cỡ chữ 14px, chỉ tab Bảng và SQL; tab Biểu đồ vẫn có khi có
  dữ liệu biểu đồ). Ô nhập dùng lại `composer.tsx`.
- **Gợi ý theo màn đang mở:** khi chưa có lượt nào, hiện một dòng "Đang ở màn Kho" và 3 câu gợi ý của module hiện tại
  (lấy từ bảng gợi ý theo vai trò, lọc theo module). Không gửi ngữ cảnh màn hình cho API.
- **Mở toàn màn hình:** chuyển sang `/assistant?session=<id>`; màn trợ lý đọc tham số này để mở đúng phiên.
- **Toast:** `Toaster` chuyển `offset` đáy lên 88px để không chồng lên nút mở.

## 5. Kiểm thử

**API (pytest):**
- `answer_format`: JSON hợp lệ; có code fence; JSON hỏng → quay về văn bản; cắt độ dài; bỏ trùng `follow_ups`;
  `split_answer` với bản ghi mới và bản ghi cũ.
- `labels`: cột trong từ điển; đoán theo tên; đoán theo giá trị; tách CamelCase.
- Service/HTTP: `/chat` trả đủ trường mới và `kind` đúng cho từng nhánh; ghi chú phạm vi luôn có ở câu trả lời thành
  công dù LLM trả gì.
- Lịch sử: chỉ liệt kê phiên của người gọi; bỏ phiên rỗng; thứ tự theo `last_at`; phân trang; đọc phiên người khác
  → 404; phiên không tồn tại → 404; chưa đăng nhập → 401.

**Web (vitest):** gửi câu hỏi và hiện kết luận + ý chính; bấm "Hỏi tiếp" gửi ngay câu đó; tab chỉ hiện khi có dữ
liệu; bảng dùng nhãn tiếng Việt và định dạng tiền; mở phiên cũ hiện các lượt; "Cuộc trò chuyện mới" về màn chào;
`clarify` không có khung kết quả; lỗi mạng có nút Thử lại. Ô chat nổi: không hiện ở `/assistant` và `/sales`;
mở/thu nhỏ bằng nút và `Ctrl + K`; hội thoại còn nguyên khi đổi màn; "Mở toàn màn hình" dẫn tới
`/assistant?session=<id>` và màn này mở đúng phiên.

## 6. Bất biến bảo mật (không được đổi)

- Mọi SQL do LLM sinh vẫn đi qua `app.modules.ai.guard.validate_sql`; không đường tắt. "Chạy lại" đi qua
  `POST /chat` như câu hỏi mới, không chạy lại SQL đã lưu.
- Mỗi vai trò chỉ một view, một tài khoản CSDL chỉ-đọc riêng; `AI_MAX_ROWS`, `AI_SQL_TIMEOUT_SECONDS`,
  `AI_MAX_SQL_ATTEMPTS` giữ nguyên.
- API lịch sử kiểm tra quyền sở hữu phiên ở tầng service (AuthZ, không chỉ AuthN); trả 404 cho phiên của người khác.
- Nội dung LLM trả về chỉ hiển thị dạng văn bản (React escape), không render HTML hay markdown thô.

## 7. Rủi ro

- **LLM không theo khuôn JSON:** đã có đường lui về văn bản; test phủ nhánh này.
- **Alias cột lạ không có dấu:** nhãn tách CamelCase không dấu; bổ sung từ điển khi gặp trong `data/eval`.
- **Chiều cao toàn màn trong `AppShell`:** vùng nội dung có padding và header mobile; dùng `100dvh` trừ đúng các
  khoảng đó, kiểm tra ở 1440px, 1024px và 390px.
