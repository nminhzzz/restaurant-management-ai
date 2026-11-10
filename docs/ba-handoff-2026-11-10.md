# Bàn giao dev đợt 10/11/2026

Phản hồi báo cáo của dev về việc thực hiện bàn giao 08/11 (`6985565`). Tài liệu đã cập nhật theo các điểm 1–7; điểm 8 cần dev làm.

## Đã chốt và cập nhật tài liệu

| # | Nội dung | Quyết định | Tài liệu |
|---|---|---|---|
| 1 | `GIAO_DICH_KHO.GiaTri DECIMAL(18,2) NULL` | Đồng ý. Cùng dấu với `SoLuongThayDoi`, ghi một lần, NULL khi chưa có đơn giá | Tài liệu 04: a26 (Bảng 39), F.26 |
| 2 | Đảo phiếu nhập làm tử số âm | Giữ nguyên đơn giá hiện hành, như trường hợp tồn sau bằng 0 | Tài liệu 04: G.1 |
| 3 | Seed B.1 xuất hủy lô quá hạn mỗi sáng, lý do “Hết hạn” | Đồng ý | Báo cáo, Phụ lục B.1 |
| 4 | Món gán theo loại (8/8/7/7), thực đơn và công thức soạn sẵn | Đồng ý; giá ghi theo dữ liệu thật 25.000–135.000 đ | Báo cáo, Phụ lục B.1 |
| 5 | Trọng số giờ “ban đêm” | Bỏ; chỉ giờ trong khung 10:00–22:00 có trọng số | Báo cáo, Phụ lục B.1 |
| 6 | B.2 nhập đầy tới 40 kg sáng ngày mốc | Đồng ý, ghi là ngoại lệ cho kịch bản tải | Báo cáo, Phụ lục B.2 |
| 7 | Giảm số suất món đã gửi bắt buộc lý do | Đồng ý | Tài liệu 03: FR-SALE-07 (đặc tả và bảng ưu tiên) |

## Việc dev cần làm

### C1. Đưa `GiaTri` vào view giao dịch kho của Quản lý

**Yêu cầu.**
1. Migration mới thêm cột `GiaTri` vào `vw_ai_quanly_giaodich`. Không thêm vào view của Bếp (`vw_ai_kho_giaodich`) hay Thu ngân.
2. Cập nhật lược đồ view trong prompt của Quản lý và `db/views/README.md`; giải thích cột: giá trị biến động, cùng dấu với `SoLuong`, NULL là chưa xác định, không coi là 0.
3. Không cấp thêm quyền ngoài tập view hiện có của tài khoản chỉ-đọc Quản lý.

**Hoàn thành khi.** Trợ lý trả lời được giá vốn nguyên liệu tiêu hao theo kỳ từ giá trị đã ghi trên giao dịch, khớp báo cáo FR-REP-11; Bếp và Thu ngân vẫn không đọc được cột này.

### C2. Viết lại Q039 và Q051

Hai câu đang dùng cột giá bình quân tháng đã bỏ. Viết lại SQL chuẩn theo `vw_ai_quanly_giavon` (lịch sử đơn giá) hoặc `GiaTri` của C1, giữ ý định câu hỏi. Chạy `make audit-eval` trên bộ B.1 và chụp lại đáp án chuẩn.

### C3. Cố định mốc sinh dữ liệu

Seed lấy đồng hồ hệ thống làm mốc nên mỗi máy ra số order khác nhau (máy dev 4.879, máy BA 4.963 cùng hạt giống 42). Chốt một giá trị `--now` cho B.1 và B.2, ghi vào `Makefile`/README, để mọi lượt nghiệm thu, đo tải và đánh giá AI dùng cùng một bộ dữ liệu. Báo lại giá trị đã chốt để cập nhật Phụ lục B.

## Còn lại từ đợt 08/11

B3 (`make gate` đầy đủ, integration MySQL), B4 (đo tải, sao lưu), B5 (chạy lại đánh giá AI, sau C1–C3). BA nghiệm thu lại 258 ca trong tài liệu 06 trên dữ liệu mới.
