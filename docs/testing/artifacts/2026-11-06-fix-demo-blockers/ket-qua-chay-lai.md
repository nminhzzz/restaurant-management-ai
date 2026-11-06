# Chạy lại các ca liên quan đến hai lỗi đã sửa — 06/11/2026

- **Phiên bản:** nhánh `fix/demo-blockers`, code chưa commit, sau commit `099191e`.
- **Môi trường:** MySQL 8.4 (`restaurant-db`), bản sao dữ liệu của CSDL `restaurant`, migration `d06112600001`.
- **Cách chạy:** gọi API bằng tài khoản `seed_*`. Log thô ở `api-rerun-output.txt`; log có cả các lượt thử trước khi hoàn chỉnh kịch bản.
- **Phạm vi:** chỉ 5 ca dưới đây. Kết quả 223/247 của lượt 03–04/11 giữ nguyên, không cộng gộp.

| Ca | Trước (03–04/11) | Kết quả 06/11 | Bằng chứng |
|---|---|---|---|
| TC-SET-01 | Không đạt | Đạt | HTTP 201, có `NgayTao`; tài khoản mới đăng nhập được |
| TC-INV-05 | Không đạt | Đạt | Bếp hủy phiếu: HTTP 200, lô về 0 và `Đã hủy`, có nhật ký `CANCEL_RECEIPT` |
| TC-BR-15 | Không đạt | Đạt | Doanh thu và số đơn tháng 10 không đổi; giá vốn tăng khi có phiếu, về đúng số cũ sau khi hủy |
| TC-BR-19 | Không đạt | Đạt, xem ghi chú | Hai lô về 0 và `Đã hủy`; phiếu `Đã hủy`; lịch sử `Nhập` và `Hoàn kho` còn nguyên |
| TC-BR-21 | Bị chặn | Đạt | Giữ món bị từ chối (HTTP 422); kiểm kê thừa tạo lô điều chỉnh mới, lô đã hủy vẫn 0 và `Đã hủy` |

Ghi chú TC-BR-19: lượt API này không đối chiếu riêng giá vốn của hai dòng. Việc tính lại giá vốn được kiểm tra trong test `test_cancelling_a_receipt_recomputes_costs_of_both_lines_and_later_months` (SQLite) và qua TC-BR-15 trên MySQL.

Lượt chạy lại phát hiện thêm và đã sửa: danh sách lô hiển thị lô đã hủy thành `Đã hết`.

Kiểm tra tự động cuối cùng: `make gate` đạt (771 test backend, 200 test frontend, build); test tích hợp MySQL đạt 18/18.
