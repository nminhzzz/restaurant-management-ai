# Sửa lỗi vận hành sau review 22/10/2026

Đợt sửa đầu xử lý 16 phát hiện về đối soát, tồn kho, giá vốn và phiên đăng nhập;
`make gate` khi đó đạt 593 test API và 172 test web. Rà soát vòng 2 phát hiện các nhánh
còn thiếu; thay đổi và phạm vi kiểm chứng mới được ghi ở cuối tài liệu.

## P1

| # | Nội dung | Cách sửa |
| --- | --- | --- |
| 1 | Đối soát "đã nhận tiền" không kiểm số tiền | `resolve_reconciliation` bắt buộc `SoTienNhan` bằng đúng tổng order; nếu còn ngoại lệ chênh lệch chưa xử lý thì từ chối. UI hỏi số tiền thực nhận (mặc định bằng tổng). |
| 2 | Sửa được mã ngân hàng của giao dịch đã thu | `record_bank_reference` khóa dòng, từ chối khi giao dịch đã thành công/có hóa đơn hoặc mã đã ghi nhận; mã cổng còn được lưu thêm ở `MaGiaoDichCong` và kiểm tra khi chống trùng webhook. |
| 3 | Xuất kho trừ mất phần đang giữ của lô | Lô chỉ bị trừ đúng lượng lấy ra (`quantity_remaining -= take`). Nếu phiếu xuất cần phần đang giữ, các lượt giữ của lô đó được giải phóng trong cùng transaction (FR-INV-06). |
| 4 | Khóa kiểm kê bị lách | Sửa/hủy phiếu nhập và hoàn kho khi hủy/giảm món đều đi qua `ensure_no_open_stocktake`. |
| 5 | Giá vốn bị cộng hai lần (05b + 05c) | Báo cáo hao hụt loại các dòng phiếu xuất có `MaChiTietOrder` (nguồn Món đã chế biến); chi phí đó chỉ nằm ở 05c từ giao dịch kho gốc. |
| 6 | Sửa/hủy món không khóa order | `update_line`, `cancel_line`, `add_line`, `cancel_order`, `move_table` khóa dòng ORDER (`FOR UPDATE`) trước khi kiểm tra trạng thái, cùng khóa với luồng thanh toán. |

## P2

| # | Nội dung | Cách sửa |
| --- | --- | --- |
| 7 | `ThanhTien` lỗi thời sau khi sửa số lượng | Cập nhật `OrderLine.ThanhTien` khi đổi số lượng; view AI tính `SoLuong * DonGia` để cả dữ liệu cũ cũng đúng. |
| 8 | Xác nhận hold hết hạn không có tác dụng ở đường gửi hàng loạt | `add_lines` truyền `confirm_expired` xuống `add_line`. |
| 9 | Hoàn một phần vẫn đóng ngoại lệ | `SoTienHoan` cộng dồn; chỉ đóng khi đã hoàn đủ, còn lại giữ "Chờ xử lý" kèm tiến độ. |
| 10 | Đổi/đặt lại mật khẩu không thu hồi JWT | Thêm `NGUOI_DUNG.PhienBanToken`; token mang claim `ver`; đổi mật khẩu, khóa tài khoản hoặc đổi vai trò tăng phiên bản. |
| 11 | `ENVIRONMENT=local` bỏ kiểm tra trạng thái/quyền | Việc đọc lại DB được điều khiển bởi `AUTH_REVALIDATE_TOKENS` (mặc định bật, kể cả local); test tắt để dùng token dựng tay. |
| 12 | Poll SePay chỉ đọc 20 giao dịch, không bắt kịp | Lưu con trỏ `CAU_HINH_HE_THONG.MocDongBoSepay`, gửi `since_id`, đọc 100 dòng/lần; con trỏ chỉ tiến qua giao dịch đã xử lý. |
| 13 | Xếp hạng món/khung giờ tính cả order chưa thu | Cửa sổ báo cáo chỉ nhận order `Đã thanh toán`. |
| 14 | Fallback không chuyển sang Ollama | `CommercialClient` nhận `fallback_client` Ollama và chuyển provider khi lỗi transport/429/5xx. |
| 15 | Ghi đè lịch giá/công thức thiếu dữ liệu cũ | Audit `SCHEDULE_*` lưu `before.LichBiGhiDe` (giá/ngày/nguyên liệu của lịch bị xóa). |
| 16 | Sửa phiếu nhập không đồng bộ lô | Cập nhật cả `received_quantity` và `unit_price` của lô để định giá tồn đầu kỳ đúng. |

## Giới hạn kiểm chứng

- Các lỗi đua (#6) được sửa bằng khóa dòng; test hiện chạy SQLite nên không tái hiện được
  tranh chấp thật. Cần một lượt kiểm thử đồng thời trên MySQL trước khi vận hành thường xuyên.
- Chưa chạy lại chuyển khoản thật, UAT/SUS sau đợt sửa này.

## Kiểm chứng đồng thời trên MySQL (22/10/2026)

`scripts/verify_mysql_concurrency.py` dựng một CSDL MySQL tạm, migrate, seed tối thiểu rồi chạy
bốn kịch bản bằng hai kết nối song song, sau đó xoá CSDL:

| Kịch bản | Kết quả |
| --- | --- |
| Hai thu ngân thu tiền mặt cùng order | 1 thành công, 1 bị từ chối, đúng 1 hóa đơn |
| Sửa số lượng món đồng thời với thanh toán | Hóa đơn, dòng món và bản chụp đều 150.000đ |
| Cùng một webhook SePay gửi hai lần | 1 hóa đơn, 0 ngoại lệ giả |
| Hai phiếu xuất tranh cùng một lô (10, xuất 6) | 1 phiếu thành công; lô và sổ cùng còn 4 |

Lần chạy đầu phát hiện thêm một lỗi thật: dưới REPEATABLE READ, sau khi chờ khóa order, câu
`SELECT` thường vẫn đọc snapshot cũ nên hóa đơn ghi 50.000đ trong khi dòng món đã sửa thành
150.000đ. Đã sửa bằng **locking read** (`FOR UPDATE`) khi tính tổng và chụp hóa đơn; lần chạy lại
cả bốn kịch bản đều đạt.

Chưa kiểm chứng: chuyển khoản thật sau đợt sửa, UAT/SUS, và tải đồng thời ở mức nhiều quầy.


## Bổ sung sau review vòng 2

Đã sửa các nhánh còn thiếu, kèm test thất bại trước sửa và test hồi quy:

| Phạm vi | Thay đổi |
| --- | --- |
| Đối soát có ngoại lệ | Không xác nhận qua đường thủ công khi còn ngoại lệ; dùng một đường áp dụng/hoàn tiền trong danh sách ngoại lệ. Khoản đã hoàn một phần chỉ được hoàn tiếp phần còn lại. |
| Webhook | Xác nhận và cấp hóa đơn nằm trong savepoint; lỗi cấp hóa đơn hoàn tác trạng thái thanh toán trước khi ghi nhận ngoại lệ. |
| Kiểm kê | Đường hoàn kho thực tế `_return_line_stock` kiểm tra phiên kiểm kê đang mở. |
| Tồn kho đồng thời | Khóa và giữ tham chiếu tới nguyên liệu đã làm mới; cập nhật trên dữ liệu hiện hành, không đọc lại snapshot cũ. |
| Hold hết hạn | Phân bổ lại theo giá/công thức hiện hành và trừ lượng đang giữ của lượt khác; khóa nguyên liệu trước lượt giữ, đọc tổng giữ chỗ hiện hành khi ghi. Các truy vấn hiển thị không khóa lượt giữ. |
| Số hóa đơn | Bảng kỹ thuật `DEM_HOA_DON` cấp số nguyên tử trong transaction; migration `c7f2d8a9e301` khởi tạo từ số hóa đơn đã phát hành. |
| SePay | Xử lý ID tăng dần, đọc tối đa 5.000 dòng của API v1, dừng trước giao dịch lỗi, cập nhật con trỏ có điều kiện. Cửa sổ đầy thì từ chối tiến mốc và yêu cầu đối soát lịch sử, tránh bỏ qua khoản chưa thấy. |
| SQL AI | Phân giải CTE theo scope; CTE lồng nhau không cho phép đọc bảng thật cùng tên ở bên ngoài. |
| Fallback AI | Deadline tuyệt đối cho từng lần gọi provider; thread hết hạn chỉ có thể kết thúc lời gọi của nó, không tự gọi tiếp provider. Timeout mặc định 1,5 giây; model Ollama riêng qua `AI_OLLAMA_MODEL` (mặc định `qwen2.5:7b`, cần được cài trên Ollama). |
| Phiên đăng nhập | 401 xóa đúng phiên bị từ chối và chuyển về đăng nhập có thông báo; phản hồi cũ không xóa phiên mới. Đổi mật khẩu kết thúc phiên đã bị thu hồi. Hiện vẫn dùng access JWT 8 giờ, chưa thêm refresh token. |

Script MySQL nay kiểm chứng thêm: nhập 5 + 7 giữ đúng tổng lô và tổng nguyên liệu 12;
cấp số hóa đơn với snapshot cũ; migration tiếp tục từ số hóa đơn hiện hữu;
hold hết hạn không lấy lượng của lượt mới; hoàn kho và gửi hold sau một phiếu nhập khác
vừa commit không làm mất cập nhật. Tổng cộng 10 ca trên CSDL tạm đều đạt.

Lượt đọc độc lập đã kiểm tra lại thứ tự khóa và việc giữ đối tượng ORM sau khóa.
Chưa chạy lại chuyển khoản thật hoặc UAT/SUS. Các kiểm thử trên CSDL tạm không chứng minh
mọi lịch xen kẽ đồng thời hoặc mọi lỗi của ngân hàng trong vận hành.

Kết quả cuối lượt sửa: `make gate` đạt **606 test API + 176 test web**, bao gồm
format/lint/typecheck/build. `make migrate` đã áp dụng `c7f2d8a9e301` vào CSDL cục bộ
đang cấu hình; `alembic current` xác nhận ở head. Chưa commit hoặc triển khai mã.
