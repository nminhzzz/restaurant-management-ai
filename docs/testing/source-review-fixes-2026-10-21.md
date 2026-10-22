# Xử lý review source–docs ngày 21/10/2026

Phạm vi: sửa các phát hiện P1 trong `docs/testing/source-docs-review-2026-10-21.md` và bật luồng
thanh toán QR thật qua SePay. Các P2 chưa xử lý được liệt kê ở cuối.

## P1 đã sửa

| Mã | Nội dung | Cách sửa |
| --- | --- | --- |
| R01 | Số lượng âm | Chặn `quantity < 1` ở router và service cho tạo order, thêm/sửa dòng; test HTTP `-3` trả 422. |
| R02 | QR không khóa order | `start_qr` khóa order và chuyển `Chờ xác nhận thanh toán`; sửa/hủy món, thu tiền mặt bị từ chối; hủy/hết hạn QR đưa order về `Đang mở`. |
| R03 | Bán phần đã giữ/lô quá hạn | FIFO chỉ lấy phần khả dụng sau giữ chỗ và lọc `HanSuDung` thực tế; kiểm tra khả dụng dùng chung một hàm. |
| R04 | Kiểm kê không cô lập | Mọi nhánh giữ/gửi món gọi `ensure_no_open_stocktake`; mở phiên bị chặn khi còn giữ chỗ. |
| R05 | Hủy phiếu nhập đã dùng | Chặn sửa/hủy khi lô đã có giao dịch xuất hoặc đang được giữ chỗ. |
| R06 | Thiếu idempotency | Thêm `ORDER.MaYeuCauGui` và `CHI_TIET_ORDER.MaYeuCauDong` (unique); gửi lặp trả lại order/dòng cũ, frontend giữ mã qua lần thử lại. |
| R07 | Gửi món ghi nhận một phần | Validate toàn bộ danh sách trước khi ghi, bọc trong transaction lồng; thêm endpoint gửi nhiều dòng nguyên tử, frontend dùng một request. |
| R08 | Hold dùng giá/công thức cũ | Khi chuyển hold thành dòng order, so phiên bản giá/công thức hiện hành và từ chối kèm giá mới. |
| R09 | Nhận món đã xóa/bị chặn | Kiểm tra dùng chung `ensure_dish_sellable` cho giữ chỗ, gửi mới và gọi thêm. |
| R10 | Hủy 1 trong 3 dòng lỗi 500 | Đổi truy vấn kiểm tra còn dòng sang `.first()`; có test 3 dòng. |
| R11 | Cộng tiền chưa xác minh vào doanh thu | Doanh thu chỉ lấy hóa đơn; tiền chờ tách riêng `provisional`, không trừ tranh chấp khỏi doanh thu. |
| R12 | Business Date hóa đơn lệch order | Thanh toán/hóa đơn kế thừa `ORDER.BusinessDate`; giao dịch kho dùng ngày phát sinh thực tế. |
| R13 | Mất giá vốn 05c | Giá vốn order hủy/đóng chưa thu tính từ sổ kho (trừ tự động − hoàn kho) × giá bình quân; cộng 05c vào tổng giá vốn và hiển thị riêng. |
| R14 | Giá bình quân thiếu tồn đầu kỳ/kỳ trước | Tính bình quân trên tồn đầu kỳ + nhập trong tháng; tháng không nhập kế thừa giá kỳ trước. |
| R15 | Audit lỗi với tác nhân hệ thống | `MaNguoiDung` cho phép null; giao diện hiển thị “Hệ thống”. |

Bổ sung ngoài P1: thanh toán/giải phóng bàn giải phóng lượt giữ chỗ; hủy order không tự trả bàn
(R17/R18 một phần).

## Kiểm chứng

- `make gate` xanh: 557 test API, 168 test web, lint/typecheck/build.
- Test hồi quy mới: `apps/api/tests/modules/test_source_review_fixes.py` (14 ca) và các ca bổ sung
  trong test doanh thu/giá vốn.
- Chạy lại trên MySQL thật (CSDL demo): số lượng âm trả 422; QR khóa order và chặn tiền mặt; hủy QR
  mở lại order; gửi danh sách có món sai không tạo order; gửi lặp cùng mã trả cùng một order.

## P2 đã xử lý (đợt 2, 21/10/2026)

Toàn bộ P2 của đợt review đã xử lý:

| Mã | Cách xử lý |
| --- | --- |
| R16 | Lượt giữ hết hạn vẫn được kiểm tra lại khi gửi; backend trả lỗi rõ và chỉ nhận khi thu ngân xác nhận `XacNhanHetHan`, không tự gia hạn ngầm. |
| R19 | Thêm cờ `TamDungThuCong` độc lập với `HetNguyenLieu` dẫn xuất; trạng thái hiển thị ưu tiên "Hết nguyên liệu" khi cả hai, có nút tạm dừng/mở lại trên danh sách món. |
| R20 | Phiếu xuất hủy có nguồn (Nguyên liệu / Món đã chế biến / Kiểm kê), chọn lô cụ thể; nguồn món đã chế biến chỉ phân loại chi phí, không trừ kho lần hai; nguồn kiểm kê phải trỏ phiếu đã chốt. |
| R21 | Trạng thái lô tính theo hạn dùng hiện tại và ngưỡng cấu hình; màn kho hiển thị hạn gần nhất, số lô sắp hết hạn/hết hạn. |
| R23 | `HOA_DON.NoiDungChup` lưu bản chụp tên món, đơn giá, phương thức, tổng tiền; in lại đọc bản chụp thay vì dữ liệu hiện tại. |
| R24 | Thêm phiếu tạm tính (không tạo hóa đơn/doanh thu); in lại phiếu bếp in nội dung thật và báo lỗi nếu trình duyệt chặn. In tự động ra máy in nhiệt cần print agent ngoài phạm vi MVP — ghi rõ khi nghiệm thu. |
| R25 | Prompt nhận ngày kinh doanh hiện tại từ backend; 66/80 SQL chuẩn đổi sang `DATE(CURDATE() - INTERVAL 6 HOUR)`. |
| R26 | Q051 tính đủ 05a+05b+05c từ `GIAO_DICH_KHO` (có `TrangThaiOrder`) và khớp `/reports/margin`. |
| R27 | Harness chạy 3 lần/câu, báo p95, loại thời gian chạy SQL chuẩn khỏi độ trễ; ghi rõ chỉ đo độ đúng thực thi SQL. |
| R28 | Audit ghi before/after cho tham chiếu ngân hàng, đối soát, mở lại/đóng chưa thu, cấu hình và thay giá/công thức (kèm phiên bản bị thay thế). |
| R29 | MVP cố định mốc 06:00: API từ chối thay đổi kèm lý do, giao diện đã ghi rõ phạm vi. |
| R30 | Bản sao lưu có `include_credentials` (mặc định vẫn ẩn hash), kèm `restore_notes` và audit cờ này. |
| R31 | Phiên chat lưu vai trò; lịch sử chỉ đọc phiên cùng vai trò hiện tại. |
| R32 | Khoản chưa thu theo mức order, gồm order vừa mở lại thanh toán. |
| R33 | Hạn mức đếm câu hỏi (kể cả cache hit), không đếm lần gọi provider/retry. |

R22 đã xử lý ở đợt trước (hủy phiên kiểm kê).

## Thanh toán thật

Xem `docs/payment-sepay-setup.md`. Cần điền `SEPAY_BANK_ACCOUNT`, `SEPAY_BANK_CODE`,
`SEPAY_ACCOUNT_NAME`, `SEPAY_WEBHOOK_API_KEY` (và tuỳ chọn `SEPAY_API_TOKEN`) rồi đặt
`PAYMENT_GATEWAY=sepay`. Webhook `POST /api/v1/sales/webhooks/sepay` tự xác nhận khi đúng mã
`TT<MaGiaoDich>`, đúng số tiền và order còn hiệu lực.

Bổ sung cho vận hành thật (21/10/2026):

- `HOA_DON.SoHoaDon` được cấp tuần tự theo BusinessDate (`HD-YYYYMMDD-NNNN`) và có unique index;
  `NguoiLap` lấy người tạo order khi webhook tự xác nhận.
- Unique index trên mã giao dịch ngân hàng và mã ngoại lệ: webhook gửi lặp không tạo lần thu thứ hai.
- Tác vụ nền quét QR hết hạn mỗi `PAYMENT_QR_EXPIRY_INTERVAL_SECONDS` giây (mặc định 60).
- Khi chưa có webhook: `SEPAY_POLL_INTERVAL_SECONDS` (mặc định 30) tự đọc danh sách giao dịch của
  tài khoản và hạch toán; bỏ qua giao dịch không có mã `TT<id>` để không tạo ngoại lệ rác.
- "Kiểm tra lại" đọc danh sách giao dịch SePay cả khi QR đã hết hạn/chờ xác minh.
- Hoàn tiền bắt buộc lưu `MaThamChieuHoan` và `SoTienHoan`; hoàn xong order về "Đang mở" nếu chưa
  có hóa đơn, để khách trả lại.
- Kiểm chứng cấu hình bằng `GET /health` (khối `payment`) và `scripts/sepay_smoke.py`.
- Ứng dụng chặn route khi chưa đăng nhập (`AppShell` chuyển về `/login`).
- Grants MySQL đã cấp lại đúng một view cho mỗi tài khoản `ai_*`; integration test đọc cấu hình
  thật từ `.env` thay vì rơi về tài khoản chính.

Không nằm trong phạm vi báo cáo nên chưa làm: trả một phần/nhiều phương thức cho một order,
và chi tiền cho nhà cung cấp.
