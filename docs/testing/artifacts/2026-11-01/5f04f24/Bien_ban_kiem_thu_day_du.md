# Biên bản kiểm thử mở rộng

Ngày thực hiện: 01/11/2026 23:03 (UTC+7).
Repository: nminhzzz/restaurant-management-ai.
Commit: 5f04f240f96c37289282209cf499f726ceaa1536 (main được fetch trước khi chạy).

## Kết quả

| Phạm vi | Kết quả | Bằng chứng |
|---|---|---|
| Cổng chuẩn make gate, dùng đúng pnpm 9.15.0 và MySQL đang chạy | Mã thoát 0; định dạng, lint, kiểm tra kiểu, backend, frontend và build đều hoàn tất | gate_final.log; gate_final_exit.txt |
| Backend thường trong lượt gate cuối | 751 đạt; 24 ca không thuộc nhóm mặc định được chạy riêng ở hai nhóm dưới; không có ca bị skip trong nhóm đã chọn | gate_final.log |
| MySQL 8.4.7 integration | 16 đạt, không skip; thực thi trên schema đã migrate, có tài khoản AI chỉ đọc riêng theo vai trò | mysql_integration.log; mysql_integration.xml |
| Nhóm slow/dữ liệu theo năm | 7 đạt, 1 không đạt do test vẫn dùng tên trạng thái cũ | slow.log; slow.xml |
| Frontend trong gate cuối | 51 file, 200 test đạt; build production thành công | gate_final.log |
| TC-BR-19–23 và trạng thái lô | Có trong nhóm backend thường và đều đạt; không cộng trùng vào tổng số test | backend_final.xml; gate_final.log |
| Tải đọc báo cáo, thăm dò | 5 endpoint × 60 request; concurrency 20; 0 lỗi HTTP; p95 từ 135,7 đến 215,9 ms trên tháng có dữ liệu | load_populated_month.log; load_scope.json |
| Kiểm tra dữ liệu thăm dò | Bộ kiểm tra của dự án không phát hiện sai lệch tồn/lô/sổ cái/giữ món và các ràng buộc được script kiểm tra | partial_integrity.json |
| Sao lưu API và khôi phục CSDL riêng | 37 bảng, 94,184 dòng; checksum từng bảng trước và sau khớp hoàn toàn; 15.701 giây, gồm bước migrate schema khôi phục | backup_roundtrip.log; backup_roundtrip.json; restore_migration.log |
| Toàn vẹn mã nguồn | 927 file được đối chiếu với Git, không có thay đổi | source_integrity.json |

## Lỗi cần dev xử lý

`apps/api/tests/seed/test_orders.py:100`, ca `test_every_order_has_a_plausible_final_state`, vẫn chấp nhận “Chờ đối soát” và “Tranh chấp”. Dữ liệu thực tế sinh ra “Chờ xác minh thanh toán” và “Đóng – chưa thu được tiền”, phù hợp đặc tả hiện hành. Cần cập nhật kỳ vọng test theo vòng đời đã chốt, không sửa nghiệp vụ để chiều test cũ. Ca này đã chạy thật và được giữ nguyên là không đạt trong slow.xml.

Lint frontend có một cảnh báo biến `Bars` chưa dùng tại `apps/web/src/features/reports/closed-unpaid-panel.tsx:12`. Đây là warning, không làm gate thất bại.

## Môi trường và các lượt chẩn đoán

Linux x86_64; Python 3.12.14; MySQL Community 8.4.7; pnpm 9.15.0 qua Corepack theo packageManager của repo. API cài từ uv.lock. MySQL chạy TCP trong môi trường kiểm thử riêng, tắt Unix socket vì môi trường không cho tạo socket đó. Đã migrate restaurant, restaurant_test và restaurant_integration; tài khoản/view AI được cấu hình theo scripts/prepare_ci_mysql.sh, dùng driver Python thay cho Docker/mysql CLI.

Lượt backend đầu có 749 đạt, 2 lỗi tại các test timeout/fallback AI. Truy vết xác định SDK không khởi tạo được vì môi trường dùng SOCKS proxy nhưng thiếu socksio. Sau khi cài socksio, hai ca riêng chạy lại đạt và lượt make gate cuối đạt đủ 751 test. Các log lỗi cũ vẫn giữ để truy vết; kết luận hiện hành dựa trên gate_final.log.

Lỗi pnpm ban đầu phát sinh khi công cụ môi trường dùng pnpm 11 và tạo file workspace tạm không phù hợp. Đã bỏ file tạm do công cụ tạo và dùng đúng pnpm 9.15.0. Không sửa cấu hình nguồn của repository để đạt test. pytest-timeout được bổ sung cho lượt chẩn đoán; lượt gate cuối dùng nguyên lệnh make gate của repo.

## Giới hạn của phép đo tải

Lệnh seed của dự án được yêu cầu tạo 20.000 order qua service thật, nhưng dừng ở giới hạn 600 giây; còn 5,500 order và 16,696 dòng món đã commit. Không ghi bộ dữ liệu này thành bộ 20.000 order hoàn chỉnh. Biên bản đo cuối dùng tháng 2026-01 có 1,762 order, không dùng kết quả tháng rỗng.

Đây là tải đọc báo cáo ngắn với 20 request đồng thời, không phải đợt tải hỗn hợp đủ thời lượng, quy mô và các mức người dùng theo kế hoạch NFR-01/NFR-03. Chưa đủ căn cứ đánh dấu toàn bộ NFR-01/NFR-03 đạt. load.log là lượt thăm dò ban đầu trên tháng chưa có dữ liệu; không dùng lượt đó để kết luận hiệu năng.

## Phạm vi sao lưu–khôi phục

Đã gọi endpoint POST /api/v1/settings/backup?include_credentials=true bằng tài khoản Quản lý trên dữ liệu mô phỏng. Bản sao JSON được khôi phục vào CSDL mới đã migrate, giữ kiểu ngày/số, để MySQL tính lại cột dẫn xuất và đối chiếu checksum toàn bộ 37 bảng. Bản sao chứa mật khẩu băm chỉ được giữ trong bộ nhớ của phép thử, không đưa vào ZIP này.

Phép thử xác nhận xuất và khôi phục dữ liệu trong lần chạy này. Chưa kiểm chứng lịch sao lưu định kỳ, RPO liên tục hoặc mọi tình huống sự cố hạ tầng; không suy rộng thành toàn bộ NFR-11 đã nghiệm thu.

## Phần chưa kiểm chứng

- Không có khóa API cho mô hình thật trong môi trường, nên chưa chạy lại thực nghiệm AI A/B/C và bộ câu hỏi an toàn bằng nhà cung cấp thật. Các test AI tự động dùng mock/fixture; không lấy chúng thay số liệu đánh giá AI trong báo cáo.
- Chưa kiểm thử thủ công toàn bộ giao diện trên môi trường đang triển khai, thiết bị thật hoặc cổng thanh toán tiền thật.
- Chưa nghiệm thu NFR-01/NFR-03 với bộ 20.000 order và kịch bản tải hỗn hợp đầy đủ.
- Còn một test slow dùng kỳ vọng trạng thái cũ cần dev sửa rồi chạy lại.

Không sửa code hoặc test để đổi kết quả; không push Git; không sửa báo cáo khóa luận hoặc kết quả lịch sử. Các số liệu trên chỉ áp dụng cho commit và môi trường được ghi rõ trong biên bản này.
