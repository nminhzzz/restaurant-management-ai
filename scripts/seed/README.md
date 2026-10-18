# Sinh dữ liệu mô phỏng

Đã triển khai: `generate.py` gọi `catalog.py` và `operations.py` qua tầng service, dùng tham số
trong `config.py`. Danh mục có 60–80 món, nguyên liệu, nhà cung cấp, bàn và tài khoản ba vai trò.
Dữ liệu vận hành gồm nhập/xuất kho, order, thanh toán, kiểm kê và chốt giá vốn.

Chạy từ thư mục gốc trên CSDL mới đã migration:

```bash
make db-up
make migrate
make seed
```

Mặc định: seed `42`, khoảng thời gian `12` tháng, mục tiêu `20.000` order. Mẫu vận hành có hai
đỉnh trưa/tối, cuối tuần cao hơn ngày thường, mùa vụ và phân bố món không đồng đều. Số order
thực sự ghi thành công phải bằng `--orders`; thiếu mục tiêu hoặc sai bất biến làm lệnh thất bại.
Thống kê JSON cuối lệnh ghi số lượt thử, số từ chối, nguyên nhân, order chờ đối soát/tranh chấp,
schema và revision. Savepoint rollback toàn bộ chứng từ bị từ chối; lỗi bất ngờ dừng ngay với ngữ cảnh.

Kiểm tra nhanh trên một schema thử riêng đã migration:

```bash
cd apps/api
DATABASE_URL='mysql+asyncmy://restaurant:restaurant@localhost:3306/restaurant_acceptance_20261017?charset=utf8mb4' \
  uv run python ../../scripts/seed/generate.py --seed 42 --months 1 --orders 40
```

Bản trước sửa chỉ tạo 22/40 order mà vẫn báo thành công. Bản sửa đã có test đạt đúng 40/40.
Đợt MySQL mới dùng `--months 12 --orders 365 --now 2026-10-17T10:00:00+07:00`: đạt **365 order,
104 phiếu nhập, 38 phiếu xuất**, toàn bộ bất biến đạt; 4 order chờ đối soát và 4 tranh chấp
được ghi riêng, bàn vật lý đều đã giải phóng. Đây là kiểm tra tính toàn vẹn, chưa phải đo tải 20.000 order.

Tài khoản mô phỏng: `seed_manager`, `seed_cashier`, `seed_warehouse`; mật khẩu `matkhau123`.
Seed từ chối CSDL đã có món; không chạy lặp để bổ sung dữ liệu. `make db-down` rồi `make db-up`
giữ nguyên volume, nên không tạo CSDL sạch. Dùng schema thử mới nếu muốn sinh lại.

View và quyền AI được áp dụng riêng theo [`db/views/README.md`](../../db/views/README.md).
Kết quả kiểm chứng ở [`docs/testing/results-2026-10-17.md`](../../docs/testing/results-2026-10-17.md).

Có thể truyền `--now` dạng ISO để tái lập mốc thời gian. Seed giữ phân bố theo mùa, cuối tuần và
khung giờ, phân bổ tổng order đúng mục tiêu và thử lại có giới hạn khi thiếu tồn. Bản tóm tắt JSON
không chứa tài khoản/mật khẩu CSDL. Xem [nhật ký trả nợ](../../docs/testing/technical-debt-2026-10-17.md).
