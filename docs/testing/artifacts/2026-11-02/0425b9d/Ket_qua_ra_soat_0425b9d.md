# Kiểm tra bản 0425b9d ngày 02 tháng 11 năm 2026

Commit kiểm tra: 0425b9d58aa4ec510d8a0d56fb18156abe3597b2. Không sửa hay push mã nguồn dự án. Ca tái hiện bổ sung chỉ chạy ở tệp tạm rồi gỡ khỏi checkout.

- Format, lint và typecheck đạt; frontend có một warning biến Bars chưa dùng.
- make gate nguyên trạng: mã thoát 2, dừng ở backend; 761 đạt, 6 lỗi, 24 deselected.
- Bốn lỗi tests/core/test_dependencies.py do không kết nối được MySQL localhost:3306. Không kết luận lỗi nghiệp vụ từ bốn ca này.
- Hai lỗi timeout/fallback AI do môi trường dùng SOCKS proxy nhưng thiếu socksio. Bổ sung socksio 1.0.0 trong virtualenv và chạy lại nguyên hai test: 2/2 đạt. Không đổi biến proxy hoặc nguồn ứng dụng.
- Nhóm test_spec_gap_cases.py và test_lot_status.py: 24/24 đạt, đã nằm trong lượt backend trên; không cộng thêm thành số test độc lập.
- Frontend: 51 tệp, 200/200 test đạt; production build đạt. Chạy riêng sau khi gate dừng.
- Nhóm slow: 8/8 đạt, 309,47 giây; fixture dùng 365 order trong 12 tháng. Không phải lượt tải 20.000 order.
- Integration MySQL chưa chạy lại vì MySQL không khởi động được trong môi trường này. DB của dev migrate/refresh là lời báo của dev, chưa xác minh độc lập.
- Chưa có kết quả chạy lại AI thật, tải đầy đủ, backup/restore hay giao diện trên 0425b9d. Kết quả 5f04f24 vẫn là lịch sử.

## REV LOT 01 tác vụ quét có thể ghi đè trạng thái cuối

Đã chạy một ca tái hiện điều khiển thứ tự xen kẽ trên SQLite, kết quả không đạt: tác vụ đọc lô Còn hạn nhưng quá hạn; trước UPDATE, mô phỏng giao dịch hủy đã hoàn tất, lưu Đã hủy và lượng 0; tác vụ UPDATE theo mã lô, ghi lại Hết hạn. Assertion giữ Đã hủy bị lỗi.

Nguồn: apps/api/src/app/modules/inventory/lot_status.py, refresh_all_lot_statuses. SELECT đầu loại lô Đã hủy nhưng UPDATE cuối chỉ lọc theo id. Không có khóa hoặc điều kiện đối chiếu trạng thái, lượng và hạn dùng hiện tại. Việc chỉ thêm status != Đã hủy ở SELECT đầu chưa bảo vệ được khoảng giữa đọc và ghi.

Dev cần bảo vệ UPDATE khỏi dữ liệu đã thay đổi, giữ Đã hủy là cuối, và tránh ghi sai trạng thái khi xuất kho/hoàn kho xảy ra giữa hai bước. Có thể dùng khóa hàng với thứ tự khóa thống nhất hoặc cập nhật có điều kiện đối chiếu snapshot và thử lại theo dữ liệu mới. Chạy test đồng thời thật trên MySQL. Ca SQLite chứng minh lỗi thứ tự ghi, không thay thế thử nghiệm hai transaction MySQL.

Chạy lại ca tái hiện: chép sweep_interleaving.py vào apps/api/tests/modules/test_review_lot_interleaving.py, chạy uv run pytest tests/modules/test_review_lot_interleaving.py từ apps/api rồi gỡ tệp kiểm tra khỏi checkout. Không sửa assertion để coi trạng thái Hết hạn là đúng.

## Phạm vi test case

Có 17 mã mới trong nhóm thiếu ánh xạ trước đó, cộng 3 mã BR-19/22/23 được bổ sung assertion; không phải 20 mã mới hoàn toàn. Danh sách còn lại của dev có 13 mã: SALE-08/19/26/46/49, INV-46/47, BR-07/08, CAT-31/32 và REP-09/15.

Đã đối chiếu riêng các assertion của 20 mã liên quan trong case_review.json và tài liệu 06. SALE-94 chỉ mock một response 151 dòng, chưa kiểm nhiều trang; SALE-99 chưa kiểm toàn bộ kho/hóa đơn/doanh thu; SET-03 chưa xác nhận thông báo tiếng Việt; BR-03 chưa xác nhận khóa mọi thao tác kho. Các ca khác có test nguồn nhưng chưa có đối chiếu từng assertion vẫn giữ trạng thái một phần. Không xác nhận hơn 200 ca đó đã được rà một–một trong lượt này.

## Gói Word

Sửa trực tiếp trên Word cũ, giữ phần lịch sử, bổ sung kết quả 02/11 tại các ca liên quan, báo cáo và handoff. Bỏ bảng truy vết riêng và thư mục bằng chứng khỏi ZIP Word theo phạm vi nộp đã trao đổi. Bằng chứng đầy đủ giữ riêng.
