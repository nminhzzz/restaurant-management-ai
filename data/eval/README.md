# Bộ dữ liệu đánh giá Text-to-SQL tiếng Việt

Đóng góp khoa học của đề tài: 50–100 cặp **câu hỏi tiếng Việt – câu SQL chuẩn** cho nghiệp vụ
nhà hàng, phân tầng ba mức độ khó, dùng để đo chất lượng khối trợ lý AI.

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

## Ba cấu hình đối chứng

| Cấu hình | Nội dung |
| --- | --- |
| `A` | Chỉ lược đồ view (đường cơ sở) |
| `B` | Lược đồ + chuẩn hóa câu hỏi tiếng Việt + few-shot |
| `C` | Cấu hình B chạy trên mô hình thứ hai (`AI_CONFIG_C_MODEL`) |

Chỉ số đo theo Phụ lục 4: **độ chính xác thực thi** (chạy cả câu SQL của mô hình lẫn SQL chuẩn
rồi so **kết quả**, không so chuỗi SQL), **tỷ lệ SQL lỗi**, **tỷ lệ từ chối**, **thời gian phản hồi
trung bình**. Câu hỏi vượt quyền được tính đúng khi trợ lý từ chối trả dữ liệu.

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

