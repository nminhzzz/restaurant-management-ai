# Phiếu kiểm tra chéo bộ đề đánh giá

Tự viết SQL cho từng câu trên CSDL đánh giá, **không xem đáp án chuẩn và không trao đổi với người khác** trước khi nộp. Chỉ dùng view ghi ở từng câu (định nghĩa trong `db/views/`). Có thể ghi ngày cụ thể thay cho hàm ngày.

Điền SQL vào tệp trả lời JSON (mẫu `mau-tra-loi.json`), đổi tên thành `answers.<tên>.json` và ghi tên mình vào trường `member`.

## Quy ước dùng chung

- 'Hôm nay' là ngày kinh doanh tham chiếu ghi ở từng câu (ngày kinh doanh bắt đầu 06:00).
- 'N ngày qua' = N ngày kinh doanh kết thúc hôm nay.
- 'Tuần này' = thứ Hai đến hôm nay; 'tuần trước' = thứ Hai đến Chủ nhật tuần trước.
- 'N tháng gần đây' = N tháng dương lịch gồm tháng hiện tại.
- Doanh thu/lượng bán của món chỉ tính order đã thanh toán.
- 'Bán được' = order đã có hóa đơn.
- 'Chưa thanh toán' = mọi trạng thái trừ Đã thanh toán, Đã hủy, Đóng – chưa thu được tiền.
- Tháng ghi dạng YYYY-MM.

## 1. Q010 — Món nào bán chạy nhất tuần này theo số lượng?

- Độ khó: easy · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_dongmon
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Món nào bán chạy nhất tuần này theo số lượng?

## 2. Q016 — Hôm nay còn bao nhiêu order chưa thanh toán?

- Độ khó: easy · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_order
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Hôm nay còn bao nhiêu order chưa thanh toán?

## 3. Q018 — Bảy ngày qua có bao nhiêu order mang về?

- Độ khó: easy · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_order
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Bảy ngày qua có bao nhiêu order mang về?

## 4. Q061 — Hôm nay bán được bao nhiêu đơn?

- Độ khó: easy · Vai trò: CASHIER
- View được dùng: vw_ai_thungan_hoadon
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Hôm nay bán được bao nhiêu đơn?

## 5. Q064 — Tháng này tổng tiền thu từ QR là bao nhiêu?

- Độ khó: easy · Vai trò: CASHIER
- View được dùng: vw_ai_thungan_thanhtoan
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Tháng này tổng tiền thu từ QR là bao nhiêu?

## 6. Q073 — Tồn của nguyên liệu Thịt bò hiện là bao nhiêu?

- Độ khó: easy · Vai trò: WAREHOUSE
- View được dùng: vw_ai_kho_ton
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Tồn của nguyên liệu Thịt bò hiện là bao nhiêu?

## 7. Q026 — Số đơn tại chỗ và mang về trong 30 ngày qua?

- Độ khó: medium · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_order
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Số đơn tại chỗ và mang về trong 30 ngày qua?

## 8. Q030 — Doanh thu trung bình mỗi ngày trong 30 ngày qua?

- Độ khó: medium · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_hoadon
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Doanh thu trung bình mỗi ngày trong 30 ngày qua?

## 9. Q036 — Tháng này có bao nhiêu order bị hủy?

- Độ khó: medium · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_order
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Số order có trạng thái Đã hủy trong tháng hiện tại.

## 10. Q038 — Top 3 nhóm món có doanh thu cao nhất tháng này?

- Độ khó: medium · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_dongmon
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Top 3 nhóm món có doanh thu cao nhất tháng này?

## 11. Q066 — Doanh thu theo từng ngày trong tuần này?

- Độ khó: medium · Vai trò: CASHIER
- View được dùng: vw_ai_thungan_thanhtoan
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Doanh thu theo từng ngày trong tuần này?

## 12. Q076 — Số lượng nhập kho theo từng ngày trong tháng này?

- Độ khó: medium · Vai trò: WAREHOUSE
- View được dùng: vw_ai_kho_giaodich
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Số lượng nhập kho theo từng ngày trong tháng này?

## 13. Q080 — Số lượng nhập theo từng nguyên liệu trong 30 ngày qua?

- Độ khó: medium · Vai trò: WAREHOUSE
- View được dùng: vw_ai_kho_giaodich
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Số lượng nhập theo từng nguyên liệu trong 30 ngày qua?

## 14. Q041 — Doanh thu tháng này so với tháng trước tăng hay giảm bao nhiêu phần trăm?

- Độ khó: hard · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_hoadon
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Doanh thu tháng này so với tháng trước tăng hay giảm bao nhiêu phần trăm?

## 15. Q045 — Số đơn theo loại đơn và theo tháng trong 3 tháng gần đây?

- Độ khó: hard · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_order
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Số đơn theo loại đơn và theo tháng trong 3 tháng gần đây?

## 16. Q049 — Số đơn trung bình mỗi ngày theo từng tháng trong năm nay?

- Độ khó: hard · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_order
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Số đơn trung bình mỗi ngày theo từng tháng trong năm nay?

## 17. Q050 — Phương thức thanh toán nào chiếm tỉ trọng cao nhất trong 30 ngày qua, kèm số tiền và tỉ lệ phần trăm?

- Độ khó: hard · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_thanhtoan
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Phương thức thanh toán nào chiếm tỉ trọng cao nhất trong 30 ngày qua, kèm số tiền và tỉ lệ phần trăm?

## 18. Q053 — Ba món có doanh thu cao nhất tháng này là món nào?

- Độ khó: hard · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_dongmon
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Ba món có doanh thu cao nhất tháng này là món nào?

## 19. Q057 — Nguyên liệu nào dưới mức tồn tối thiểu và không nhập trong 30 ngày qua?

- Độ khó: hard · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_nhap, vw_ai_quanly_ton
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Nguyên liệu nào dưới mức tồn tối thiểu và không nhập trong 30 ngày qua?

## 20. Q060 — Nguyên liệu nào có tồn thấp hơn mức trung bình và đã phát sinh xuất kho trong 30 ngày qua?

- Độ khó: hard · Vai trò: MANAGER
- View được dùng: vw_ai_quanly_giaodich, vw_ai_quanly_ton
- Ngày kinh doanh 'hôm nay': 2026-10-23
- Định nghĩa chỉ số: Giữ chỗ chỉ tồn tại trong lúc khách đang chọn món nên không dùng làm điều kiện của câu hỏi chuẩn.
