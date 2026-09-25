# Bộ dữ liệu đánh giá Text-to-SQL tiếng Việt

Đóng góp khoa học của đề tài: 50–100 cặp **câu hỏi tiếng Việt – câu SQL chuẩn** cho nghiệp vụ
nhà hàng, phân tầng ba mức độ khó, dùng để đo chất lượng khối trợ lý AI.

Hiện có **95 câu hỏi** (`Q001`–`Q095`): 45 MANAGER (FR-AI-02, gồm cả các câu về món bán chạy/ít
bán, biên lợi nhuận, giá nhập nguyên liệu và order bị hủy được bổ sung để khớp view mới), 24
CASHIER (FR-AI-03, gồm doanh thu theo món), 26 WAREHOUSE (FR-AI-04, gồm cảnh báo tồn tối thiểu và
lô sắp hết hạn). Phân tầng độ khó: 31 easy, 40 medium, 24 hard.

## Định dạng

Mỗi dòng trong `questions.jsonl` là một bản ghi JSON độc lập:

| Trường | Kiểu | Ý nghĩa |
| --- | --- | --- |
| `id` | string | Mã câu hỏi, dạng `Q001` |
| `question` | string | Câu hỏi tiếng Việt nguyên văn, giữ dấu |
| `difficulty` | `"easy"` \| `"medium"` \| `"hard"` | Mức độ khó |
| `role` | `"MANAGER"` \| `"CASHIER"` \| `"WAREHOUSE"` | Vai trò được phép hỏi câu này |
| `view` | string | View mà SQL chuẩn phải tham chiếu (`vw_ai_quanly`, …) |
| `sql` | string | Câu SQL chuẩn, chỉ `SELECT` trên đúng `view` |
| `notes` | string hoặc null | Ghi chú về cách hiểu câu hỏi, nếu có nhiều cách diễn giải |

Câu hỏi phải **thuộc phạm vi vai trò ghi trong `role`**: bộ dữ liệu cũng dùng để kiểm chứng
FR-AI-05 (trợ lý không truy cập chéo dữ liệu giữa các vai trò), nên cần cả các ca cố tình hỏi
vượt quyền và kỳ vọng là bị từ chối.

## Quy trình soạn

- Người soạn SQL chuẩn không đồng thời thiết kế prompt.
- Trên 15–20 câu ngẫu nhiên, cả ba thành viên độc lập soạn SQL và đối chiếu; tỷ lệ đồng thuận là
  căn cứ đánh giá độ rõ ràng của câu hỏi.

`questions.example.jsonl` chỉ là mẫu định dạng để viết harness, **không** phải bộ đánh giá chính thức.

## Lịch sử chỉnh sửa bộ đề

Sau khi ba view `vw_ai_*` được viết lại thành UNION ALL NULL-padded với cột phân biệt
`LoaiBanGhi`, nhiều SQL chuẩn của `Q001`–`Q075` (soạn cho lược đồ view cũ) trở nên sai lệch dù
vẫn chạy được. Đợt rà soát sau đây sửa lại để khớp lược đồ view hiện tại (giữ nguyên id, vai trò,
view, độ khó):

- **Lọc sai nhánh `LoaiBanGhi` (đếm/COUNT(*) bị nhân đôi)**: `Q001`, `Q003`, `Q015`, `Q021`,
  `Q029`, `Q032`, `Q039`, `Q060`, `Q064`, `Q069` — trước đó lọc bằng `MaOrder IS NOT NULL` hoặc
  `TrangThaiOrder = ...`, các cột này cũng có dữ liệu ở nhánh `DONG_MON`; đổi sang
  `WHERE LoaiBanGhi = 'ORDER'`. `Q037` cũng được lọc tường minh bằng `LoaiBanGhi = 'THANH_TOAN'`
  dù `MaGiaoDich` vốn đã là cột riêng của nhánh đó, cho nhất quán.
- **Đếm nguyên liệu bị nhân theo số dòng ở các nhánh khác**: `Q005`, `Q024` — `MaNguyenLieu`
  có mặt ở 3-4 nhánh; đổi sang `COUNT(DISTINCT MaNguyenLieu) ... WHERE LoaiBanGhi = 'TON_KHO'`.
- **`ORDER BY SoLuongTon ASC` chọn nhầm dòng `NULL`**: `Q050` — nhánh `GIAO_DICH_KHO`/
  `LO_NGUYEN_LIEU` có `SoLuongTon = NULL`, MySQL xếp `NULL` lên đầu khi `ASC` nên `LIMIT 5` lấy
  nhầm; thêm `WHERE LoaiBanGhi = 'TON_KHO'`.
- **`MaBan` và `TongTien` không bao giờ cùng một dòng** (`MaBan` chỉ ở nhánh `ORDER`, `TongTien`
  chỉ ở nhánh `HOA_DON`) nên `GROUP BY MaBan, SUM(TongTien)` luôn ra `NULL`: `Q027`, `Q040`,
  `Q061` — viết lại bằng JOIN hai subquery (`ORDER` nối `HOA_DON` qua `MaOrder`).
- **Trả về danh sách thay vì một số trung bình**: `Q036` "Doanh thu trung bình mỗi ngày trong 30
  ngày qua?" — SQL cũ trả doanh thu từng ngày; sửa thành `AVG` của doanh thu từng ngày.
- **Nguyên liệu chưa từng có giao dịch kho bị lặp dòng**: `Q075` — bảng ngoài trước đó quét cả 3
  nhánh (trùng tên nhiều lần); giới hạn `LoaiBanGhi = 'TON_KHO'` ở ngoài, `'GIAO_DICH_KHO'` ở
  `NOT EXISTS`.
- **Cột `Thang` của `GIA_VON_THANG` là `YYYYMM` (vd. `202609`), không phải `1-12`**: `Q082`,
  `Q084` — SQL cũ so sánh/join bằng `MONTH(BusinessDate)` (1-12) nên không bao giờ khớp; sửa
  sang `YEAR(...) * 100 + MONTH(...)`. Đồng thời `COLUMN_NOTES["Thang"]` trong
  `apps/api/src/app/modules/ai/pipeline/prompt.py` được sửa lại vì ghi sai định dạng cột này.
- **Tháng hiện tại chưa được "đóng tháng" nên không có `GIA_VON_THANG`**: `Q082`, `Q084` hỏi
  "tháng này" nhưng giá vốn bình quân chỉ tồn tại sau khi quản lý đóng tháng (FR liên quan đến
  `costing.close_month`); đổi câu hỏi sang "tháng trước" để luôn có dữ liệu. `Q082` cũng dùng
  tên nguyên liệu không tồn tại trong dữ liệu mô phỏng (`'Gạo'` — chỉ có `'Gạo tẻ'`/`'Gạo
  nếp'`/`'Bột gạo'`); đổi sang `'Gạo tẻ'`.
- **Câu hỏi và SQL lệch nhau về "đơn" và "giờ xuất hóa đơn"**: `Q035`, `Q043` — SQL nhóm theo giờ
  xuất hóa đơn (view không có thời điểm tạo order) nhưng câu hỏi hỏi "đơn"; đổi câu hỏi thành
  "Số hóa đơn theo từng giờ ..." để khớp SQL, không sửa SQL.

Đã kiểm tra: mọi SQL còn lại vẫn đúng dù dùng `IS NOT NULL` thay vì `LoaiBanGhi = '...'` — cột lọc
(`MaHoaDon`, `MaGiaoDich`, `PhuongThuc`, `LoaiGiaoDich`, ...) chỉ có dữ liệu ở đúng một nhánh nên
không bị ảnh hưởng.

**Hạn chế đã biết, ngoài phạm vi sửa (không chạm vào seed/migrations)**: `Q092` ("lô nào sắp hết
hạn") luôn trả về rỗng trên dữ liệu mô phỏng hiện tại vì `NGUYEN_LIEU.SoNgayBaoQuan` là `NULL`
cho toàn bộ 68 nguyên liệu, nên `HanSuDungLo` không bao giờ có giá trị; SQL đúng theo đặc tả,
chỉ là dữ liệu seed chưa phủ trường hạn sử dụng.

## Ba cấu hình đối chứng

| Cấu hình | Nội dung |
| --- | --- |
| `A` | Chỉ lược đồ view (đường cơ sở) |
| `B` | Lược đồ + chuẩn hóa câu hỏi tiếng Việt + few-shot |
| `C` | Cấu hình B chạy trên mô hình thứ hai (`AI_CONFIG_C_MODEL`) |

Chỉ số đo theo Phụ lục 4: **độ chính xác thực thi** (chạy cả câu SQL của mô hình lẫn SQL chuẩn
rồi so **kết quả**, không so chuỗi SQL), **tỷ lệ SQL lỗi**, **tỷ lệ từ chối**, **thời gian phản hồi
trung bình**. Câu hỏi vượt quyền được tính đúng khi trợ lý từ chối trả dữ liệu.

Với DeepSeek, cấu hình `C` chạy trên một mô hình suy luận (reasoning) thứ hai qua
`AI_CONFIG_C_MODEL` (ví dụ `deepseek-v4-pro` với `thinking` bật) — mô hình này có thể vượt ngân
sách phản hồi 8 giây của NFR-02 vì phải sinh chuỗi suy luận trước câu trả lời. Harness không áp
ngân sách đó (nó không đi qua `ai_response_budget_seconds` của pipeline sản phẩm), nên
`mean_latency_ms` của cấu hình `C` được **ghi nhận nguyên trạng**, không bị cắt hay loại trừ,
để phản ánh đúng chi phí thời gian thật của mô hình suy luận.

## Cách chạy

Harness chạy qua đúng pipeline của Phase 6, nên cần CSDL đã seed và tài khoản chỉ-đọc của từng vai trò:

```bash
make db-up && make migrate && make seed     # dữ liệu 12 tháng
./scripts/apply_grants.sh                   # view + ba tài khoản chỉ-đọc
cd apps/api && uv run python ../../data/eval/harness.py --configs A,B,C --out ../../docs/eval-results.json
```

Chạy bằng **đường dẫn file** (không dùng `-m`): khi chạy tay, `sys.path[0]` là `data/eval/` nên
`import data...` không resolve; `app.*` vẫn import được vì `uv sync` cài package ở chế độ editable.

Bộ test của harness dùng client giả và engine giả nên chạy được trong `make gate`:

```bash
cd apps/api && uv run pytest tests/eval
```

## Chạy thực nghiệm A/B/C với DeepSeek

Các bước cụ thể để chạy trên CSDL MySQL đã seed, dùng DeepSeek làm nhà cung cấp LLM:

1. Đặt biến môi trường trong `.env` (xem `.env.example`):
   ```
   AI_PROVIDER=deepseek
   AI_API_KEY=<khoá API DeepSeek thật>
   LLM_MODEL=deepseek-flash
   LLM_BASE_URL=https://api.deepseek.com
   AI_CONFIG_C_MODEL=deepseek-v4-pro
   ```
2. Chuẩn bị CSDL: `make db-up && make migrate && make seed && ./scripts/apply_grants.sh`.
3. Chạy cả ba cấu hình:
   ```bash
   cd apps/api && uv run python ../../data/eval/harness.py --configs A,B,C --out ../../docs/eval-results.json
   ```
4. Kết quả tổng hợp (bảng so sánh 3 cấu hình) được ghi vào `docs/eval-results.json`; harness cũng in
   ra bảng tóm tắt trên terminal.

Chi phí và thời gian ước tính cho 95 câu hỏi (`data/eval/questions.jsonl`), mỗi câu tối đa
`AI_MAX_SQL_ATTEMPTS` (2) lần sinh SQL: cấu hình `A`/`B` trên `deepseek-flash` mất khoảng vài giây
mỗi câu và tổng chi phí API ở mức dưới một đô la cho cả 95 câu; cấu hình `C` trên mô hình suy luận
(`deepseek-v4-pro`) chậm hơn đáng kể trên mỗi câu (xem lưu ý ở trên về ngân sách 8 giây) nên tổng
thời gian chạy `C` có thể dài hơn `A`+`B` cộng lại. Đây là ước tính để lập kế hoạch, không phải cam
kết; giá và tốc độ thực tế phụ thuộc vào bảng giá DeepSeek tại thời điểm chạy.

**Lưu ý**: không chạy lệnh trên trong môi trường không có `AI_API_KEY` thật — harness sẽ gọi API
DeepSeek thật và tính phí theo số token.

