# Bộ dữ liệu đánh giá Text-to-SQL tiếng Việt

Đóng góp khoa học của đề tài: 50–100 cặp **câu hỏi tiếng Việt – câu SQL chuẩn** cho nghiệp vụ
nhà hàng, phân tầng ba mức độ khó, dùng để đo chất lượng khối trợ lý AI.

Hiện có **95 câu hỏi** (`Q001`–`Q095`): 45 MANAGER (FR-AI-02, gồm cả các câu về món bán chạy/ít
bán, biên lợi nhuận, giá nhập nguyên liệu và order bị hủy được bổ sung để khớp view mới), 24
CASHIER (FR-AI-03, gồm doanh thu theo món), 26 WAREHOUSE (FR-AI-04, gồm cảnh báo tồn tối thiểu và
lô sắp hết hạn). Phân tầng độ khó: 31 easy, 40 medium, 24 hard.

Trong 95 câu có **6 câu cố tình vượt quyền** (`notes` chứa "vượt quyền": `Q017`, `Q019`, `Q020`, `Q047`,
`Q052`, `Q054`), kỳ vọng là bị từ chối. Harness chấm riêng: `business_accuracy` chỉ tính trên 89 câu
nghiệp vụ (28 easy, 37 medium, 24 hard; 45 MANAGER, 21 CASHIER, 23 WAREHOUSE) và `refusal_accuracy`
chỉ tính trên 6 câu vượt quyền; `execution_accuracy` (95 câu) vẫn được ghi để đối chiếu với các lần
chạy trước.

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

`questions.example.jsonl` **không** phải bộ đánh giá: đó là 6 ví dụ few-shot (2 mỗi vai trò) được
`prompt.py` chèn vào prompt của cấu hình B/C và của trợ lý trong sản phẩm. Quy tắc: không câu hỏi nào
trùng với `questions.jsonl`; SQL chỉ dùng cột có thật của view (`validate_for_role` chạy trên từng ví dụ
trong `tests/eval/test_questions.py`); ngày tương đối viết bằng `DATE_SUB(CURRENT_DATE, INTERVAL n DAY)`
để `prompt.py` neo vào Business Date hiệu lực.

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
cho toàn bộ 68 nguyên liệu, nên lô nhập không có `LO_NGUYEN_LIEU.HanSuDung` và `HanSuDungLo` không bao
giờ có giá trị; SQL đúng theo đặc tả, chỉ là dữ liệu seed chưa phủ trường hạn sử dụng.

## Ba cấu hình đối chứng

| Cấu hình | Nội dung |
| --- | --- |
| `A` | Chỉ lược đồ view (đường cơ sở) |
| `B` | Lược đồ + chuẩn hóa câu hỏi tiếng Việt + few-shot |
| `C` | Cùng prompt và chuẩn hóa như B, nhưng chạy trên mô hình thứ hai (`AI_CONFIG_C_MODEL`) |

Chỉ số harness đo tự động (Phụ lục 4): **độ chính xác thực thi** (chạy cả câu SQL của mô hình lẫn SQL
chuẩn rồi so **kết quả**, không so chuỗi SQL; có bản chặt và bản "nới lỏng" cho phép thừa cột), **tỷ lệ
SQL lỗi**, **tỷ lệ từ chối**, **thời gian phản hồi trung bình và p95** (nearest-rank). Câu hỏi vượt quyền
được tính đúng khi trợ lý từ chối trả dữ liệu. **Chưa đo tự động**: độ đúng câu trả lời (số liệu và
nhận xét của bước diễn giải) và token/chi phí mỗi câu — hai chỉ số này cần chấm tay hoặc đọc `usage` của
API.

Phạm vi đo của harness (khác sản phẩm): chuẩn hóa → prompt → **một lần** sinh SQL → `validate_for_role`
→ thực thi trên tài khoản chỉ-đọc của vai trò. Không có bước diễn giải, không sinh lại khi lỗi, không
cache và không áp ngân sách phản hồi 8 giây của sản phẩm (`ai_response_budget_seconds`). Vì vậy
`mean_latency_ms`/`p95_latency_ms` là **cận dưới** của thời gian toàn chuỗi NFR-02. SQL chuẩn cũng phải đi
qua `validate_for_role` (cùng trần 500 dòng) trước khi chạy: executor chỉ nhận `ValidatedSql`, harness
không có đường tắt.

Với DeepSeek, cấu hình `C` chạy trên một mô hình suy luận (reasoning) thứ hai qua `AI_CONFIG_C_MODEL`
(ví dụ `deepseek-v4-pro`). Harness chỉ đổi **tên mô hình**; mức suy luận lấy từ `LLM_REASONING_EFFORT`
của lần chạy đó (đặt `high` khi chạy `C` nếu muốn khớp mô tả trong báo cáo) và không gửi tham số
`thinking`. Mô hình suy luận phải sinh chuỗi suy luận trước câu trả lời nên chậm hơn; `mean_latency_ms`
của `C` được **ghi nhận nguyên trạng**, không bị cắt hay loại trừ.

## Cách chạy

Harness dùng cùng prompt builder, guard và executor của sản phẩm (xem phạm vi đo ở trên), nên cần CSDL
đã seed, các view `vw_ai_*` đã áp dụng và ba biến `AI_READONLY_URL_*` (để trống sẽ báo lỗi, không có
đường lui sang tài khoản chính):

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
   LLM_REASONING_EFFORT=low        # đặt high khi chạy riêng cấu hình C
   AI_READONLY_URL_MANAGER=...     # ba tài khoản chỉ-đọc, xem db/views/README.md
   AI_READONLY_URL_CASHIER=...
   AI_READONLY_URL_WAREHOUSE=...
   ```
2. Chuẩn bị CSDL: `make db-up && make migrate && make seed && ./scripts/apply_grants.sh`.
3. Chạy cả ba cấu hình:
   ```bash
   cd apps/api && uv run python ../../data/eval/harness.py --configs A,B,C --out ../../docs/eval-results.json
   ```
4. Kết quả tổng hợp (bảng so sánh 3 cấu hình, kèm khối `meta` ghi thời điểm chạy, nhà cung cấp, tên mô
   hình từng cấu hình và phạm vi đo) được ghi vào `docs/eval-results.json`; harness cũng in ra bảng tóm
   tắt trên terminal. Báo cáo yêu cầu 3 lượt lặp mỗi cấu hình: harness chạy một lượt mỗi lần gọi, nên
   chạy ba lần với ba tên `--out` khác nhau rồi gộp.

Chi phí và thời gian ước tính cho 95 câu hỏi (`data/eval/questions.jsonl`), mỗi câu một lần sinh SQL
trong harness: cấu hình `A`/`B` trên `deepseek-flash` mất khoảng vài giây
mỗi câu và tổng chi phí API ở mức dưới một đô la cho cả 95 câu; cấu hình `C` trên mô hình suy luận
(`deepseek-v4-pro`) chậm hơn đáng kể trên mỗi câu (xem lưu ý ở trên về mô hình suy luận) nên tổng
thời gian chạy `C` có thể dài hơn `A`+`B` cộng lại. Đây là ước tính để lập kế hoạch, không phải cam
kết; giá và tốc độ thực tế phụ thuộc vào bảng giá DeepSeek tại thời điểm chạy.

**Lưu ý**: không chạy lệnh trên trong môi trường không có `AI_API_KEY` thật — harness sẽ gọi API
DeepSeek thật và tính phí theo số token.


## Kết quả chạy thử ngày 26/09/2026

`docs/eval-results.json` là **một lượt chạy khám phá** trên 95 câu với bản guard/prompt lúc đó (trước đợt
siết bộ kiểm duyệt SQL, trước khi tách chấm câu vượt quyền), file không ghi tên mô hình, nên **không phải
kết quả thực nghiệm chính thức** và không thay cho 3 lượt lặp của báo cáo. Các con số dưới đây được tính
lại từ chính file đó (p95 và chia nhóm lấy từ `detail.*.outcomes`):

| Cấu hình | Chính xác (95 câu) | Chính xác (89 câu nghiệp vụ) | Trung bình | p95 | Lỗi | Từ chối |
| --- | --- | --- | --- | --- | --- | --- |
| A | 56,8% | 53,9% | 5,7 s | 15,1 s | 1,1% | 6,3% |
| B | 66,3% | 64,0% | 5,1 s | 14,5 s | 0,0% | 8,4% |
| C | 57,9% | 55,1% | 8,8 s | 20,2 s | 7,4% | 11,6% |

Cả 6 câu vượt quyền được từ chối đúng ở cả ba cấu hình. Theo độ khó (89 câu nghiệp vụ, đúng/tổng):
B đạt 25/28 easy, 25/37 medium, 7/24 hard. p95 của cả ba cấu hình **vượt ngưỡng 10 giây của NFR-02**
ngay cả khi chưa tính bước diễn giải (A: 16/95 câu quá 10 giây, B: 10/95, C: 31/95; chậm nhất 40,4 s) —
đuôi chậm đến từ độ trễ của API LLM; trung bình vẫn dưới 10 giây. Chênh lệch A→B (+9,5 điểm trên 95 câu)
phù hợp với giả thuyết rằng chuẩn hóa và few-shot giúp, nhưng một lượt chạy trên một bộ đề không đủ để
kết luận; C (mô hình suy luận) không tốt hơn B trong lượt này.
