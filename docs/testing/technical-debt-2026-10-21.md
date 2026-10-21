# Đợt chỉnh trợ lý AI ngày 21/10/2026

Phạm vi: làm cho các câu hỏi mẫu của Trợ lý AI trả lời được trên dữ liệu mô phỏng, giảm câu hỏi
làm rõ không cần thiết và không đánh mất kết quả khi bước diễn giải chậm.

## Đã xử lý

### Gợi ý câu hỏi khớp phạm vi view và dữ liệu
- Bỏ câu hỏi "Những lô nào sắp hết hạn trong tuần này?" khỏi gợi ý của Quản lý: `vw_ai_quanly`
  không có cột lô/hạn dùng nên trợ lý luôn phải hỏi lại. Câu này vẫn giữ cho vai trò Kho
  (`vw_ai_kho` có `HanSuDungLo`).
- Đổi "Hôm nay có bao nhiêu hoá đơn đã thanh toán?" thành "Tháng này…" và "Món nào bán chạy nhất
  hôm nay?" thành "tuần này" để câu trả lời có dữ liệu ngay cả khi ngày hiện tại chưa phát sinh order.
- Thêm gợi ý "Nguyên liệu nào có tồn kho thấp nhất?" cho Quản lý.

### Prompt rõ nhánh dữ liệu và trạng thái
- Ghi chú cột nêu rõ `MaHoaDon`/`TongTien` chỉ có ở `LoaiBanGhi = 'HOA_DON'`,
  `MaGiaoDich`/`PhuongThuc`/`SoTien` chỉ có ở `LoaiBanGhi = 'THANH_TOAN'`.
- Liệt kê đầy đủ giá trị `TrangThaiOrder` (kể cả "Chờ đối soát", "Đóng – chưa thu được tiền")
  để trợ lý không hỏi lại khi người dùng dùng đúng tên trạng thái.

### Không mất dữ liệu khi diễn giải chậm
- Sinh SQL, kiểm duyệt và thực thi vẫn nằm trong ngân sách phản hồi (`AI_RESPONSE_BUDGET_SECONDS`).
- Bước diễn giải văn bản chạy với phần thời gian còn lại; nếu vượt, trợ lý trả về dòng dữ liệu,
  SQL và biểu đồ kèm câu "Kết quả đã được truy vấn nhưng chưa diễn giải được thành câu trả lời"
  thay vì đánh dấu cả lượt là lỗi (NFR-02).
- Kết quả rỗng được giải thích là "Truy vấn hợp lệ nhưng không có dòng dữ liệu nào thỏa điều kiện",
  không còn ngụ ý câu hỏi nằm ngoài phạm vi.

### Dữ liệu mô phỏng
- `scripts/seed/catalog.py` gán `SoNgayBaoQuan` theo nhóm nguyên liệu (thịt/hải sản 3 ngày,
  rau/bún 7 ngày, đồ khô 365 ngày) để lô nhập có `HanSuDung` và câu hỏi hạn dùng trả lời được.
- CSDL demo hiện có 3 nguyên liệu dưới mức tối thiểu và 67 lô hết hạn trong tuần, đủ để kiểm tra
  các câu hỏi cảnh báo tồn kho/hạn dùng.

### Bộ câu hỏi đánh giá và dữ liệu seed
- Rà soát toàn bộ 80 câu chính thức, 30 câu phát triển và 30 ca an toàn bằng script mới
  `scripts/audit_eval_questions.py` / `make audit-eval`: kiểm tra cấu trúc, trùng câu hỏi, guard và
  chạy SQL chuẩn bằng tài khoản chỉ-đọc của từng vai trò.
- Sửa các câu không còn chuẩn: `Q060` (bỏ điều kiện giữ chỗ luôn rỗng), `Q064` (trùng `Q004`),
  `D008`/`D026` (trùng câu hỏi với bộ chính thức), `D015` (luôn rỗng vì nguyên liệu nào cũng có
  giao dịch kho), `D030` (alias `Thang` trùng cột view và câu hỏi trùng `D004`).
- `scripts/seed/operations.py` sinh thêm **20% order mang về** để dữ liệu phủ luồng bán hàng này
  (trước đây toàn bộ order seed là tại chỗ).
- Cập nhật `data/eval/README.md`: bỏ ghi chú lỗi thời về `D022`, thêm quy trình audit và lưu ý
  kết quả `docs/eval-results.json` cần chạy lại sau khi đổi nội dung câu hỏi.
- Apply lại `db/views/vw_ai_*.sql` cho CSDL `restaurant` (view cũ bị invalid sau migration) và
  `restaurant_demo`; kiểm tra bằng `make audit-eval` trên cả hai CSDL, 0 lỗi SQL/guard.

### QR thanh toán ở chế độ mô phỏng
- Trước đây `PAYMENT_GATEWAY=simulator` không trả `qr_image_url`, nên màn hình thanh toán chỉ có
  đồng hồ đếm ngược mà không có mã QR. Nay adapter giả lập sinh ảnh SVG bằng `segno` (data URI,
  không cần mạng), kèm nội dung `SIM<ma giao dich>` và nhãn "Mã QR mô phỏng — không chuyển tiền thật".
- Ảnh QR thật vẫn chỉ do adapter SePay tạo khi cấu hình đủ `SEPAY_*`; giao diện phân biệt hai chế độ.

### Giao diện trợ lý
- Trạng thái chờ có thêm hai dòng skeleton nhấp nháy bên dưới "Đang phân tích câu hỏi · N giây",
  để người dùng thấy hệ thống đang xử lý thay vì màn hình trống.
- Câu trả lời mới hiện dần theo thứ tự: tiêu đề → từng gạch đầu dòng → bảng/biểu đồ → phạm vi dữ liệu,
  thay vì bật ra toàn bộ. Hiệu ứng tôn trọng `prefers-reduced-motion`; nội dung vẫn nằm đầy đủ trong
  DOM nên trình đọc màn hình và test không bị ảnh hưởng. Lịch sử mở lại không chạy lại hiệu ứng.

## Kiểm chứng

- Chạy toàn bộ 14 câu hỏi mẫu của ba vai trò trên CSDL demo: tất cả trả về `answer` (kể cả câu
  hạn dùng khi bước diễn giải vượt ngân sách, dữ liệu vẫn hiển thị).
- API: **541 test qua**; Web: **168 test qua**; ruff, mypy, eslint, tsc, prettier và `next build` qua.
- `make audit-eval d=restaurant_demo`: 0 lỗi, 5 cảnh báo câu rỗng phụ thuộc dữ liệu/ngày chạy;
  `make audit-eval` trên `restaurant`: 0 lỗi.
