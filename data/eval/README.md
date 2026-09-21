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
