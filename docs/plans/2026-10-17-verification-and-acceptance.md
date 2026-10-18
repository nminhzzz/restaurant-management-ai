# Kế hoạch ổn định và nghiệm thu ngày 17/10/2026

Mục tiêu: xử lý các test thất bại, kiểm tra MySQL và giao diện, đồng bộ tài liệu với bằng chứng.

## Ràng buộc

- Giữ MySQL 8.4, phân quyền API, kiểm duyệt SQL và tài khoản AI theo vai trò.
- Dùng đồng hồ `app.shared.business_date`; không thay cấu hình local của người dùng.
- Giữ nguyên các thay đổi có sẵn trong `.env.example`, `db/views/README.md` và các thư mục chưa theo dõi.
- Không ghi điểm SUS hoặc kết luận UAT khi chưa có người dùng thật.

## Các bước

- [x] Tái hiện bảy test lỗi, đối chiếu cấu hình và đồng hồ; bổ sung ca hồi quy trước khi sửa.
  Tệp: `apps/api/tests/conftest.py`, `tests/modules/test_inventory_costing.py`,
  `src/app/modules/inventory/service.py`. Chạy lại nhóm test kho và thanh toán.
- [x] Chạy migration, view và integration trên MySQL; kiểm tra luồng nhập–gọi món–thanh toán–báo cáo
  trên dữ liệu thử riêng. Lưu lệnh, số lượng và hạn chế vào `docs/testing/results-2026-10-17.md`.
- [x] Kiểm tra giao diện qua Chrome ở desktop và kích thước tablet dọc/ngang bằng
  `chrome-devtools`; lưu ảnh và kết quả. Không suy ra kết quả Safari hoặc tablet thật từ giả lập.
- [x] Đồng bộ `README.md`, README seed/API/web, roadmap và báo cáo. Ghi kết quả A/B/C hiện có
  là thực nghiệm đã lưu, tách khỏi kế hoạch đánh giá mới và SUS/UAT chưa thực hiện.
- [x] Chạy `make gate`, rà diff và ghi kết quả cuối. Không commit hoặc đụng dữ liệu thật.

Kết quả: 439 test API, 155 test web, 7 ca MySQL integration; gate xanh và review độc lập không còn
phát hiện cần sửa trong bản thay đổi. Log, ảnh và hạn chế tại
[`../testing/results-2026-10-17.md`](../testing/results-2026-10-17.md).

## Phần chưa thể nghiệm thu trong phiên

- [ ] Thu phiếu SUS và biên bản UAT của người dùng thật, tổng hợp vào báo cáo.
- [ ] Kiểm tra tablet vật lý, bàn phím ảo, Edge và Safari.
- [ ] Rà bất nhất nhãn trạng thái bàn so với bộ lọc trên mẫu seed, theo luồng giải phóng bàn của
  đặc tả mới. Chưa xác nhận toàn bộ FR/NFR mới chỉ từ kết quả các ca đã chạy.
