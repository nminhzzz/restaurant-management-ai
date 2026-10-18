# Đợt sửa nợ kỹ thuật ngày 18/10/2026

Phạm vi: xử lý tuần tự các lỗi và khoảng cách đã rà soát giữa mã nguồn và báo cáo.
Mọi thay đổi đều có test đi kèm; migration mới **chưa** áp dụng vào CSDL làm việc của người dùng.

## Đã xử lý

### Trợ lý AI và dữ liệu view
- Bộ few-shot `data/eval/questions.example.jsonl` được viết lại theo đúng cột hiện có
  (`TongTien`, `ThanhTienMon`, `CanhBaoTonThap`) và có test chặn cột lỗi thời.
- `vw_ai_quanly`/`vw_ai_thungan` loại dòng món đã hủy, chỉ đưa giao dịch thanh toán thành công;
  nhánh phiếu nhập loại phiếu hủy và quy `NgayNhap` về Business Date 06:00.
- Ghi chú cột trong prompt và `db/views/README.md` được đồng bộ với hành vi mới.
- Fallback tài khoản AI chỉ-đọc: local dùng tài khoản chính, môi trường khác bắt buộc cấu hình
  riêng và fail rõ ràng thay vì chạy bằng quyền ghi.
- Hạn mức AI chuyển sang từng người dùng/ngày: khóa `(BusinessDate, MaNguoiDung)`, giá trị mặc định
  lấy từ `SoCauHoiAIMoiNgay` trong cấu hình hệ thống (50).
- Phiếu bếp in tên món và tên bàn thay vì id nội bộ.

### Danh mục và lịch áp dụng
- Giá/công thức `Chờ áp dụng` được kích hoạt khi tới Business Date, đóng phiên bản cũ và cập nhật
  `missing_recipe`; áp dụng khi đọc giá/công thức, khi lên danh sách và khi mở màn hình món.
- Món chỉ có công thức chờ áp dụng không còn được bán; món không có công thức hiệu lực bị từ chối
  ở cả tạo order và gọi thêm.
- Bàn có thêm khu vực/số chỗ, API và giao diện sửa bàn; nhà cung cấp có email/người liên hệ/địa chỉ;
  nguyên liệu có `SoNgayBaoQuan` để tính hạn lô, tất cả đã nhập được trên giao diện.

### Xác thực và phân quyền
- Ngoài môi trường local, mỗi request đọc lại tài khoản trong CSDL: tài khoản bị khóa hoặc đổi vai trò
  có hiệu lực ngay, không chờ token hết hạn.
- Các route đọc danh mục và order được giới hạn lại theo Bảng 10:
  Thu ngân không đọc nguyên liệu/NCC; Nhân viên kho không đọc món/giá/bàn/order.

### Kho, kiểm kê và giá vốn
- Giá bình quân tháng loại phiếu nhập đã hủy và lô điều chỉnh kiểm kê (đơn giá 0).
- Giá vốn bán hàng chỉ tính order `Đã thanh toán`, không tính order còn mở.
- Hao hụt bao gồm chênh lệch âm kiểm kê, tính theo giá bình quân tháng; dòng thiếu giá bị đánh dấu tạm tính.
- Kiểm kê: chỉ một phiên mở; chặn nhập/xuất/trừ kho khi phiên đang mở; yêu cầu kiểm đủ nguyên liệu
  hoạt động; ghi lại nhiều lần không tạo dòng trùng; trạng thái kết thúc dùng `Đã chốt`.
- Chênh lệch âm trừ được cả lô hết hạn, đúng với tồn thực tế gồm lô hết hạn.

### Giữ chỗ nguyên liệu (backend)
- Thêm `GIU_CHO_MON`/`CHI_TIET_GIU_CHO`: phân bổ theo lô FIFO, hạn giữ lấy từ cấu hình, không ghi
  `GIAO_DICH_KHO` khi chỉ giữ.
- API `POST/PATCH/DELETE /sales/holds` và `GET /sales/holds?selection_code=...`; giữ chỗ chỉ thuộc
  người tạo, dùng cho bàn trống/mang về hoặc gọi thêm vào order đang mở (`order_id`).
- Gửi món bằng `hold_id` trên dòng order, ở cả tạo order và gọi thêm: trừ đúng lượng đã giữ trên từng
  lô đúng một lần; gửi lặp bị từ chối, không trừ kho lần hai.
- `vw_ai_kho` có `SoLuongGiu`/`SoLuongKhaDung` để trả lời lượng khả dụng sau giữ chỗ; `vw_ai_quanly`
  cũng có hai cột này ở nhánh `TON_KHO`.
- Giao diện gọi món tạo hold ngay khi bấm món; tăng/giảm số lượng gọi `PATCH`, bỏ món gọi `DELETE`,
  gửi order kèm `hold_id`. Nếu tạo hold lỗi, món không vào giỏ và không gửi order.
- `GET /catalog/dishes` trả `SoSuatKhaDung` (số suất còn giữ được theo công thức và tồn khả dụng);
  menu hiển thị “Còn X suất” và ẩn món đã hết suất.

### Ngoại lệ thanh toán
- Thêm trạng thái `Chờ xác minh thanh toán` và `Đóng – chưa thu được tiền`; mở rộng cột trạng thái
  giao dịch để chứa được chuỗi dài.
- Thu ngân/Quản lý yêu cầu xác minh khi khách báo đã chuyển tiền; order bị khóa, không nhận thêm món.
- Quản lý mở lại thanh toán (hủy giao dịch chờ, đưa order về `Đang mở`) hoặc đóng chưa thu (không tạo
  hóa đơn); cả hai bắt buộc lý do và ghi nhật ký.
- Quản lý xác nhận tiền đã về từ trạng thái chờ xác minh; chuyển khoản đến muộn vẫn được đối chiếu.
- Doanh thu tạm tính và danh sách thanh toán chờ bao gồm tiền đang chờ xác minh.
- `GET /reports/closed-unpaid` tách riêng order đóng chưa thu khỏi báo cáo order hủy, kèm giá trị,
  giá vốn nguyên liệu đã tiêu hao và lý do; báo cáo order hủy cũng có `GiaVon`/`TongGiaVon`.
- Giao diện thanh toán có nút “Khách báo đã chuyển tiền” và, với Quản lý, ba thao tác xác nhận đã
  nhận/mở lại/đóng chưa thu; trạng thái chờ xác minh khóa gọi thêm và thu tiền mặt.

### Cài đặt và báo cáo
- `CAU_HINH_HE_THONG` có `SoNgayCanhBaoHetHan`, `ThoiGianGiuChoPhut`, `SoCauHoiAIMoiNgay`;
  API và giao diện cấu hình đọc/ghi các trường này.
- Quản lý sửa được họ tên/số điện thoại/vai trò tài khoản; chặn tự bỏ quyền quản lý và chặn bỏ
  quyền quản lý cuối cùng.
- Báo cáo doanh thu chia được theo **loại đơn**; thêm danh sách **thanh toán chưa hoàn tất**
  (`GET /reports/pending-payments`) kèm số tiền, trạng thái và số phút đã chờ.
- So sánh hai kỳ gồm cả **doanh thu và giá vốn**, kèm phần trăm chênh lệch; giao diện hiển thị thẻ và
  bảng giá vốn, không chỉ doanh thu.
- Giao diện nguyên liệu nhập được `SoNgayBaoQuan`; giao diện nhà cung cấp nhập được email, người liên
  hệ và địa chỉ.

### Bộ đánh giá
- Tách `questions.jsonl` thành **80 câu chính thức** đúng phân tầng 30/30/20 và 60/10/10 theo vai trò.
- `questions.dev.jsonl` có 30 câu phát triển; `questions.safety.jsonl` có 30 ca an toàn với
  `expect: "refusal"`, tách khỏi mẫu số 80.
- Harness nhận `--questions` để chạy riêng bộ an toàn/phát triển; test khóa phân tầng, ID và view.

## Kiểm chứng

- API: **535 test qua**, 18 test integration/slow được loại khỏi lượt gate theo cấu hình.
- Web: **162 test qua**; prettier, eslint, tsc và `next build` đều qua.
- API: ruff format/check và mypy qua.
- **MySQL 8.4 integration: 10 test qua** trên `restaurant_test` đã migrate; seed 20.000 order
  hoàn tất với `integrity: passed`.
- Benchmark báo cáo tháng 2026-09: revenue 0,036s; dishes 0,020s; hours 0,017s; costs 0,097s
  (ngân sách 2s/endpoint).
- Đã sửa lỗi collation thật trên MySQL: view dùng `SET NAMES`/`COLLATE utf8mb4_unicode_ci`
  để UNION không lẫn `utf8mb4_0900_ai_ci`.
- Ba tài khoản AI chỉ-đọc đọc đúng view: manager 332.253 dòng, cashier 105.606 dòng,
  warehouse 225.831 dòng trên dữ liệu seed.
- Thực nghiệm A/B/C trên 80 câu: **A 61,25% · B 62,50% · C 53,75%**; bộ an toàn 30 ca:
  **A/C 96,67% · B 100%**. C có timeout 20s và tỷ lệ lỗi 12,5%.
- Tải đồng thời 8 worker × 40 request/endpoint: p95 revenue 65,6ms; dishes 33,1ms; hours 52,0ms;
  costs 148,9ms; comparison 494,7ms — 0 lỗi.
- Tải đỉnh 16 worker × 80 request/endpoint: p95 revenue 95,7ms; dishes 78,9ms; hours 63,3ms;
  costs 634,3ms; comparison 306,1ms — 0 lỗi, tất cả dưới 2s. `comparison` dùng cache 30s sau
  lần tính đầu để tránh lặp chi phí hai tháng.
- Menu 80 món: **0,274s** sau khi gộp truy vấn khả dụng thành batch (trước đó 1,88s).

## Còn lại

- SUS/UAT; tablet thật, Edge/Safari.
- Áp dụng migration vào CSDL triển khai thật (commit checkpoint `0db1e9b` đã tạo).
