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

## P2 còn lại

Chưa xử lý trong đợt này: R16 (hold hết hạn), R19 (cờ tạm dừng độc lập), R20 (nguồn/lô phiếu xuất
hủy), R21 (cảnh báo hạn dùng trên màn kho), R23 (bản chụp hóa đơn), R24 (in tạm tính/phiếu bếp thật),
R25 (business date trong prompt AI), R26 (gold Q051), R27 (harness đo câu trả lời/p95), R28
(before/after audit), R29 (cấu hình mốc 06:00), R30 (backup xác thực), R31 (lịch sử AI theo vai trò),
R32 (order mở lại trong danh sách chưa thu), R33 (hạn mức AI theo câu hỏi).

R22 (tiếp tục/hủy phiên kiểm kê) đã xử lý ở đợt bổ sung tối 21/10: `POST /inventory/stocktakes/{id}/cancel`,
nút Hủy phiên và banner "đang có phiên nháp" trên màn Kiểm kê.

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
