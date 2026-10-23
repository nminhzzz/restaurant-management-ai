# Kế hoạch hoàn thiện mã nguồn theo báo cáo 23/10/2026

**Chuẩn nghiệm thu:** `docs/BaoCao_HeThongQuanLyNhaHang.md`, commit `d2d5c86`.
**Mục tiêu:** hiện thực đủ yêu cầu chức năng và cung cấp công cụ kiểm chứng yêu cầu phi chức năng; không thay thế bằng việc giảm yêu cầu trong báo cáo.
**Kiến trúc:** giữ Next.js/FastAPI/SQLAlchemy/MySQL 8.4 và module hiện hành. Thay đổi có migration tiến/lùi, kiểm tra quyền API, transaction và test hồi quy. Bổ sung tích hợp in cấu hình được, không gửi tới thiết bị ngoài khi chưa cấu hình.
**Ủy quyền:** người dùng yêu cầu triển khai lần lượt toàn bộ phần thiếu. Báo cáo mới được ưu tiên khi khác quy ước cũ về giờ Business Date và số view/vai trò.
**Nhánh:** `feat/docs-parity-20261023`; làm trong thư mục hiện tại, không push/triển khai.

## Thứ tự và phân công

### Task 1: Toàn vẹn bán hàng và kiểm kê

- [x] Đọc toàn bộ FR-SALE/FR-INV, quy tắc G; lập test thất bại cho tăng món theo phiên bản mới, món chờ làm trước kiểm kê và kiểm kê thừa.
- [x] Tăng số lượng đi qua luồng gọi thêm/giữ món; API cũ không được tăng dòng lịch sử bằng giá/công thức cũ. Giữ được giảm món và API tương thích có thông báo rõ.
- [x] Khóa phiên kiểm kê nguyên tử; chặn khi còn hold hoặc món chưa xử lý; kiểm kê thừa cộng vào lô gần nhất còn hạn, fallback lô điều chỉnh không có dòng nhập giả.
- [x] Chạy các test bán hàng/kho và kiểm tra quyền, rollback, idempotency liên quan.

### Task 2: Lịch giờ ngày kinh doanh và cấu hình

- [x] Lưu lịch mốc giờ theo ngày hiệu lực; thay đổi bắt đầu từ Business Date kế tiếp, ngày hiện tại và lịch sử không đổi.
- [x] Bộ hàm dùng chung giải quyết giờ theo lịch, độ chính xác phút; đưa lịch vào context từng request/transaction, không dùng biến toàn cục chia sẻ giữa người dùng.
- [x] Cập nhật tất cả đường nghiệp vụ, prompt, view, job liên quan; kiểm thử chuyển mốc sớm/muộn, qua tháng và mốc phút.
- [x] Form cấu hình cho nhập giờ, hiển thị mốc đang dùng/lịch chờ; số ngày cảnh báo phải dương.
- [x] Migration riêng sau `c7f2d8a9e301`, revision `d23102300001`.

### Task 3: Giao diện và truy vấn kho

- [x] API trả tồn sổ sách/đủ điều kiện/đang giữ/khả dụng, đơn vị và thời điểm tính nhất quán.
- [x] Bảng kho hiển thị đủ chỉ số; chi tiết lô và lịch sử nhập/xuất/hoàn có bộ lọc, phân trang, quyền quản lý/bếp.
- [x] Chọn lô xuất hủy bằng dữ liệu thật thay cho nhập tay ID; đủ trạng thái tải/lỗi/trống và test tương tác.

### Task 4: Phạm vi và nhật ký AI

- [x] Tách view theo chủ đề trong từng vai trò, tổng hợp trước quan hệ một-nhiều; view số suất khả dụng không lộ công thức hoặc giá vốn cho Bếp.
- [x] Đồng bộ scope/prompt/guard/accounts/grants/schema introspection/tests; cache không dùng kết quả tồn khả dụng cũ.
- [x] Ghi model thực, tổng token, chi phí và số lần gọi cả retry/diễn giải/fallback; không làm mất log khi provider lỗi.
- [x] FK nhật ký AI RESTRICT; migration `d23102300002` sau Task 2; kiểm thử giới hạn 2 lần/3 giây/500 dòng và cô lập quyền.
- [x] Kết quả luôn có bảng và ghi chú; chi tiết kỹ thuật thu gọn mặc định.

### Task 5: Tích hợp in phiếu bếp

- [x] Hàng đợi in bền vững sau transaction gửi món, adapter máy in nhiệt cấu hình từ server, timeout và retry; không in trước commit.
- [x] Lỗi in không hủy nghiệp vụ, trạng thái phiếu và số lần in phản ánh kết quả thật; in lại theo quyền, không tự trừ kho lại.
- [x] Test máy in giả lập và hướng dẫn kết nối máy in thật; xác minh phần cứng ghi riêng.

### Task 6: Bộ đánh giá AI và kiểm chứng hiệu năng

- [x] Metadata câu hỏi: thời điểm tham chiếu, định nghĩa chỉ số, kết quả chuẩn/snapshot, rubric diễn giải, tách dev/chính thức.
- [x] A/B/C cùng model; thinking tắt/tắt/bật-high; chạy xen kẽ, 3 lần, không cache; sử dụng guard/retry/diễn giải như ứng dụng.
- [x] Đo đầu-cuối, độ đúng SQL/diễn giải, lỗi/từ chối nhầm, token/chi phí, p50/p95 theo nhóm; không tự coi diễn giải đúng khi chưa chấm.
- [x] Phụ lục J: seed/manifest, tải nghiệp vụ phụ thuộc và báo cáo, CSV, bất biến sau chạy, tham số thời lượng/VU/seed tái lập.
- [x] Không gán kết quả giả cho SUS/UAT, thiết bị, ngân hàng hay hiệu năng chưa đo.

### Task 7: Rà soát đủ FR/NFR và nghiệm thu

- [x] Ma trận từng FR/NFR -> source/test/bằng chứng; rà lại nhánh ngoại lệ, phân quyền, schema và index, không chỉ danh sách sai lệch cũ.
- [x] Mô tả bảng/cột kỹ thuật bổ sung và cập nhật quy ước dự án theo thiết kế mới; không sửa yêu cầu để che thiếu hụt.
- [ ] Review độc lập, sửa phát hiện, chạy `make gate`; chạy migration và integration trên CSDL tạm khi MySQL sẵn sàng.
  (đã chạy gate và migration trên MySQL cục bộ; integration MySQL tạm còn lại)
- [x] Báo cáo rõ tính năng đã hiện thực, kiểm thử đã chạy và bằng chứng bên ngoài còn cần thu.

## Nhật ký thực hiện

- Baseline: `make gate` đã đạt 610 API + 179 web, build thành công trước thay đổi.
- Không xóa tính năng ngoài báo cáo; không thao tác CSDL người dùng/máy in/ngân hàng khi kiểm thử.

- 2026-10-23 (tiếp phiên): áp migration `d23102300001`–`d23102300003` trên MySQL cục bộ; xử lý 12 lỗi kiểm thử (4 lỗi vòng lặp sự kiện khi request chạm CSDL thật và 8 test
  còn theo hành vi cũ: luồng gọi thêm, cảnh báo tồn theo lượng khả dụng, khóa kiểm kê, bảng Business Date).
  Hoàn thiện FR-REP-01 (phân nhóm theo loại đơn) và FR-REP-08 (kỳ gốc bằng 0 hiển thị chênh lệch tuyệt đối
  và "Không xác định tỷ lệ phần trăm"); bổ sung ngày/trạng thái/giá trị vào lịch sử nhập hàng của nhà cung
  cấp (FR-CAT-15). Cập nhật `docs/testing/test-cases.md` theo thiết kế mới và thêm ma trận NFR → bằng chứng.
  `make gate` xanh: 670 API test, 189 web test, lint/typecheck/build đạt. Chưa chạy nghiệm thu máy in thật,
  MySQL concurrency/performance và bộ đánh giá AI chính thức — các mục này cần môi trường/dữ liệu bên ngoài.

- 2026-10-23 (đợt rà soát web): đối chiếu 104 FR với giao diện, bổ sung các phần còn thiếu:
  xác minh thanh toán (mã GD/ảnh/kết quả xử lý), tra cứu order nâng cao, in lại thật, lượt giữ chưa gửi,
  sửa phiếu nhập, ngày nhập, nguồn xuất theo dữ liệu thật, lý do chênh lệch kiểm kê, trạng thái "Sắp hết hạn",
  chọn kỳ báo cáo + doanh thu theo thứ + biểu đồ UC 4.5, món xóa mềm, khóa ĐVT, lý do chặn món, reset mức tồn,
  lịch sử AI có bảng/biểu đồ và gợi ý diễn đạt lại, chặn route theo vai trò.
  Migration mới: `d23102300004` (bằng chứng thanh toán), `d23102300005` (lý do kiểm kê),
  `d23102300006` (phản hồi AI). Test mới: `order-lookup`, `receipt-edit-dialog`, các ca API tương ứng.
- 2026-10-23 (hoàn tất rà soát web): `make gate` xanh lần cuối với 671 API test + 190 web test;
  migration `d23102300004`–`d23102300006` đã áp trên MySQL cục bộ. Các luồng mới có test riêng:
  yêu cầu xác minh kèm mã GD/ảnh, mở lại/đóng chưa thu kèm kết quả xử lý, tra cứu order nâng cao,
  sửa phiếu nhập, lý do kiểm kê, trạng thái lô sắp hết hạn, chọn kỳ báo cáo, doanh thu theo thứ,
  món xóa mềm, khóa đơn vị tính và lịch sử AI giữ bảng/biểu đồ.
- 2026-10-23 (đóng nốt khác biệt): so sánh kỳ nhận khoảng nhiều tháng (`left_from/left_to`,
  `right_from/right_to`), lịch sử nhập hàng của nhà cung cấp mở được chi tiết dòng hàng,
  audit log hiển thị nhãn tiếng Việt cho loại thao tác. Bổ sung test API/web tương ứng.
