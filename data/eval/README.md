# Đánh giá AI theo báo cáo 23/10/2026

Bộ chính thức gồm 80 câu: 60 Quản lý (20 dễ, 20 trung bình, 20 khó),
10 Thu ngân và 10 Bếp (mỗi vai trò 5 dễ, 5 trung bình). Tập phát triển
30 câu phục vụ few-shot, tách khỏi bộ chính thức; bộ an toàn 30 câu chạy riêng.
Không dùng kết quả lịch sử trong `docs/eval-results.json` để kết luận cho bộ mới.

## Dữ liệu và đáp án chuẩn

Mỗi dòng JSONL có `id`, `question`, `difficulty`, `role`, `view` (view chính),
`views` (toàn bộ view được dùng), `sql`, `notes`, `reference_time`,
`reference_business_date`, `metric_definition`, `answer_rubric`, `expected_result`
và `review_status`. SQL chỉ đọc tập view theo chủ đề của vai trò. Không truy cập
bảng nghiệp vụ hoặc view tổng hợp cũ đã bỏ cấp quyền.

Thời điểm tham chiếu cố định tránh việc đáp án thay đổi theo ngày chạy. Harness
phân tích AST để ràng buộc các hàm ngày/giờ MySQL theo thời điểm này, bao gồm mẫu
Business Date cũ. Prompt dùng cùng đồng hồ tham chiếu. Không thay chuỗi trong dữ liệu.
Các phép lấy tồn hiện tại vẫn cần bản sao CSDL đánh giá ở đúng trạng thái tham chiếu.

`expected_result: null` nghĩa là **chưa chụp đáp án**. Trước đợt chính thức:

1. Sinh và phục hồi bản sao dữ liệu đánh giá; dừng các tác vụ ghi trên bản sao đó.
2. Chụp kết quả chuẩn bằng tài khoản chỉ đọc:

   ```bash
   cd apps/api
   uv run python ../../data/eval/artifacts.py snapshot \
     --questions ../../data/eval/questions.jsonl \
     --out ../../data/eval/questions.locked.jsonl --dataset-id restaurant-eval-20261023
   ```

3. Người khác kiểm tra SQL, số liệu, định nghĩa chỉ số và rubric; 20 câu được ba
   thành viên giải độc lập theo báo cáo. Lưu biên bản đồng thuận và sửa đáp án
   trước khi khóa bộ đề. Công cụ không tự ghi nhận bước kiểm tra con người là đạt.
4. Giữ tệp `.manifest.json`, SHA256 bộ đề/lược đồ và bản sao CSDL; không thay prompt
   theo từng đáp án của bộ đã khóa. Chụp kết quả không thay thế việc lưu bản sao CSDL.

Nếu chạy bản chưa khóa, harness chạy SQL chuẩn để so sánh nhưng kết quả đó chỉ
phù hợp phát triển công cụ, chưa phải bằng chứng thực nghiệm chính thức.

## Cấu hình thực nghiệm

| Cấu hình | Prompt | Model | Thinking khi sinh SQL |
| --- | --- | --- | --- |
| A | Lược đồ và quy tắc quyền | `LLM_MODEL` | disabled |
| B | A + định nghĩa nghiệp vụ, chuẩn hóa, few-shot phát triển | cùng model | disabled |
| C | Giống B | cùng model | enabled, reasoning_effort=high |

Diễn giải dùng thinking disabled cho cả ba. Không dùng `AI_CONFIG_C_MODEL` làm
model thứ hai trong thực nghiệm này; fallback provider bị tắt để giữ biến đối chứng.
Mỗi câu có tối đa hai lần sinh SQL/kiểm duyệt/thực thi, truy vấn tối đa 3 giây/500 dòng.
Không dùng cache hoặc hạn mức người dùng của sản phẩm trong harness.

Chạy trên bản sao CSDL đã chuẩn bị view và tài khoản riêng từng vai trò:

```bash
cd apps/api
uv run python ../../data/eval/harness.py --configs A,B,C --runs 3 \
  --questions ../../data/eval/questions.locked.jsonl --out ../../docs/eval-parity-results.json
```

Các cấu hình chạy xen kẽ theo câu, đảo cấu hình bắt đầu theo lần lặp. Kết quả ghi
lại từng câu/lần, SQL, bảng chuẩn, bảng nhận được, diễn giải, model, token, chi phí
đã biết và độ trễ từ chuẩn hóa/sinh SQL đến diễn giải; thời gian chạy SQL chuẩn
không cộng vào độ trễ sản phẩm. Token hoặc chi phí thiếu do provider không trả
usage được đánh dấu chưa đầy đủ, không diễn giải thành chi phí bằng 0.

Độ đúng thực thi tính theo số liệu; thứ tự chỉ bắt buộc khi rubric yêu cầu.
Báo cáo p50/p95, độ đúng, chi phí theo vai trò và độ khó; lỗi/từ chối nhầm vẫn nằm
trong mẫu số. Bộ an toàn chạy riêng bằng `--questions questions.safety.jsonl`.
Bộ này là ca hỏi đáp; các ca đổi quyền giữa phiên, GRANT và giới hạn vật lý CSDL
còn được kiểm tra bằng integration test, không suy ra từ riêng kết quả harness.

## Chấm diễn giải

`answer_correct` và `answer_accuracy` mặc định là null. Người kiểm tra đối chiếu
bảng và mọi nhận xét với rubric, ghi một tệp JSON như sau:

```json
[{"config":"B","question_id":"Q001","run_index":1,
  "answer_correct":true,"reviewer":"Người kiểm tra","notes":"Số liệu, kỳ và nhận xét đều khớp."}]
```

Áp dụng và tính lại chỉ số:

```bash
cd apps/api
uv run python ../../data/eval/artifacts.py grade \
  --results ../../docs/eval-parity-results.json --grades ../../docs/eval-grades.json \
  --out ../../docs/eval-parity-graded.json
```

SQL sai không được chấm thành câu trả lời đúng. Chỉ khi mọi lượt đã được chấm mới
có độ đúng câu trả lời tổng thể; không loại những lượt chưa chấm khỏi mẫu số.

## Kiểm chứng công cụ

`cd apps/api && uv run pytest tests/eval` chạy với LLM/engine giả và không đo độ đúng
của model thật. Các kết quả, SUS, UAT và số đo hiệu năng chưa chạy không được ghi
nhận là đã đạt. Công cụ phát tải Phụ lục J có hướng dẫn riêng trong `docs/performance.md`.
