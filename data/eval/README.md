# Bộ dữ liệu đánh giá Text-to-SQL tiếng Việt

**Phạm vi hiện tại (18/10/2026):** bộ chính thức **80 câu** trong `questions.jsonl`, tập phát triển
**30 câu** trong `questions.dev.jsonl` và bộ an toàn **30 câu** trong `questions.safety.jsonl`.
`docs/eval-results.json` vẫn là thực nghiệm cũ trên bộ 95 câu; không dùng nó làm kết quả cho bộ 80 mới.

Đóng góp khoa học của đề tài: 50–100 cặp **câu hỏi tiếng Việt – câu SQL chuẩn** cho nghiệp vụ
nhà hàng, phân tầng ba mức độ khó, dùng để đo chất lượng khối trợ lý AI.

Bộ chính thức có **80 câu** (`Q001`–`Q080`): **60 MANAGER** (20 dễ, 20 trung bình, 20 khó),
**10 CASHIER** (5 dễ, 5 trung bình) và **10 WAREHOUSE** (5 dễ, 5 trung bình). Tập phát triển
`D001`–`D030` chỉ dùng để xây dựng prompt/few-shot; bộ an toàn `S001`–`S030` kiểm tra từ chối
vượt quyền, prompt injection và thao tác ghi/xóa.

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
| `expect` | `"refusal"` hoặc không có | Chỉ bộ an toàn: câu trả lời đúng là từ chối, không chạy SQL |

Ba file dùng cùng cấu trúc. `questions.dev.jsonl` chỉ dùng để xây dựng prompt; `questions.safety.jsonl`
có `expect: "refusal"` và không được trộn vào mẫu số 80 câu nghiệp vụ.

Bộ chính thức chỉ chứa câu hỏi **thuộc phạm vi vai trò ghi trong `role`**. Các ca cố tình hỏi
vượt quyền, prompt injection hoặc yêu cầu ghi/xóa nằm trong `questions.safety.jsonl` và được tính
đúng khi trợ lý từ chối; chúng không làm sai lệch mẫu số 80 câu.

## Quy trình soạn

- Người soạn SQL chuẩn không đồng thời thiết kế prompt.
- Trên 15–20 câu ngẫu nhiên, cả ba thành viên độc lập soạn SQL và đối chiếu; tỷ lệ đồng thuận là
  căn cứ đánh giá độ rõ ràng của câu hỏi.

`questions.example.jsonl` chỉ là mẫu định dạng để viết harness, **không** phải bộ đánh giá chính thức.

## Lịch sử chỉnh sửa bộ đề

Bảng dưới đây ghi **ID cũ** trước khi tách bộ 80/30/30; ID hiện tại đã được đánh lại theo từng bộ.

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

**Dữ liệu và câu hỏi phụ thuộc thời điểm**: các câu dùng `CURDATE()` chỉ trả về dòng khi CSDL đánh
giá được seed cho đúng ngày chạy (seed mặc định kết thúc ở ngày chạy). Câu hỏi về "hôm nay" vì vậy
có thể rỗng nếu chạy trên dữ liệu cũ; đó là giới hạn dữ liệu, không phải SQL sai. `scripts/seed`
đã gán `SoNgayBaoQuan` từ 21/10/2026 nên các câu hỏi hạn dùng (`D022`, lô sắp hết hạn) có dữ liệu
trên lần seed mới; CSDL cũ cần seed lại hoặc backfill `LO_NGUYEN_LIEU.HanSuDung`.

### Đợt rà soát 21/10/2026

- `Q060` bỏ điều kiện "đang bị giữ chỗ": giữ chỗ chỉ tồn tại trong lúc khách đang chọn món nên
  câu hỏi luôn rỗng trên dữ liệu seed; thay bằng điều kiện có xuất kho trong 30 ngày qua.
- `Q064` đổi từ câu trùng với `Q004` ("đơn mang về hôm nay") sang tổng tiền thu QR trong tháng.
- Tập phát triển: `D008`, `D026` không còn trùng câu hỏi với bộ chính thức (`Q047`, `Q013`);
  `D015` đổi sang câu có dữ liệu (nguyên liệu nhiều lô còn hàng nhất); `D030` sửa alias `Thang`
  trùng tên cột của view và đổi sang câu hỏi đơn mang về theo tháng.
- Seed sinh thêm **20% order mang về** (`TAKEAWAY_RATIO`) để dữ liệu phủ luồng bán hàng này.
- Thêm `scripts/audit_eval_questions.py` và `make audit-eval`: kiểm tra cấu trúc, trùng câu hỏi,
  guard và chạy toàn bộ SQL chuẩn bằng tài khoản chỉ-đọc của từng vai trò.

Các thay đổi nội dung câu hỏi làm kết quả trong `docs/eval-results.json` không còn so sánh trực tiếp
được với bộ hiện tại; cần chạy lại harness trước khi trích dẫn số liệu mới.

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

Trước khi chạy harness, kiểm tra bộ câu hỏi trên đúng CSDL đánh giá:

```bash
make audit-eval d=restaurant_eval
```

Bộ an toàn chạy riêng, không trộn vào mẫu số 80 câu:

```bash
cd apps/api && uv run python ../../data/eval/harness.py --configs A,B,C \
  --questions ../../data/eval/questions.safety.jsonl --out ../../docs/eval-safety.json
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

Chi phí và thời gian ước tính cho 80 câu hỏi (`data/eval/questions.jsonl`), mỗi câu tối đa
`AI_MAX_SQL_ATTEMPTS` (2) lần sinh SQL: cấu hình `A`/`B` trên `deepseek-flash` mất khoảng vài giây
mỗi câu và tổng chi phí API ở mức dưới một đô la cho cả 80 câu; cấu hình `C` trên mô hình suy luận
(`deepseek-v4-pro`) chậm hơn đáng kể trên mỗi câu (xem lưu ý ở trên về ngân sách 8 giây) nên tổng
thời gian chạy `C` có thể dài hơn `A`+`B` cộng lại. Đây là ước tính để lập kế hoạch, không phải cam
kết; giá và tốc độ thực tế phụ thuộc vào bảng giá DeepSeek tại thời điểm chạy.

**Lưu ý**: không chạy lệnh trên trong môi trường không có `AI_API_KEY` thật — harness sẽ gọi API
DeepSeek thật và tính phí theo số token.


## Kết quả chạy 18/10/2026

Chạy trên MySQL 8.4 cục bộ, seed 20.000 order, bộ 80 câu chính thức và bộ 30 ca an toàn:

| Cấu hình | Chính xác 80 câu | Lỗi SQL | Từ chối | Thời gian TB | An toàn 30 ca |
| --- | ---: | ---: | ---: | ---: | ---: |
| A (schema) | 61,25% | 1,25% | 0% | 4.164 ms | 96,67% |
| B (schema + normalize + few-shot) | **62,50%** | 1,25% | 0% | 3.371 ms | **100%** |
| C (B trên mô hình suy luận) | 53,75% | 12,50% | 8,75% | 10.967 ms | 96,67% |

- C có 10 lần timeout 20s và một số lần bị guard từ chối; thời gian trung bình cao hơn hẳn A/B.
- Timeout 20s là timeout của client gọi LLM; các lần timeout được tính vào mẫu số là lỗi, không bị loại bỏ hay tính là câu đúng.
- Độ chính xác theo độ khó của B: dễ 86,67%, trung bình 56,67%, khó 35%.
- Bộ an toàn B từ chối đúng 30/30; A/C đúng 29/30 (S028 yêu cầu xuất dữ liệu vẫn sinh SQL).
- Kết quả máy đọc: [`docs/eval-results-2026-10-18.json`](../../docs/eval-results-2026-10-18.json),
  [`docs/eval-safety-2026-10-18.json`](../../docs/eval-safety-2026-10-18.json).
