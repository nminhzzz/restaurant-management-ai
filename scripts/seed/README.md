# Sinh dữ liệu mô phỏng

Đã triển khai: `generate.py` gọi `catalog.py` và `operations.py` qua tầng service, dùng tham số
trong `config.py`, theo Phụ lục B.1 của báo cáo. Danh mục là thực đơn viết tay của một quán nhỏ:
30 món trong 4 nhóm, 35 nguyên liệu (10 thịt và hải sản, 12 bún, phở, rau, củ, quả, 13 hàng khô),
3 nhà cung cấp theo nhóm hàng, 12 bàn và tài khoản ba vai trò. Công thức dùng đúng nguyên liệu của
món, giá bán để lại tỷ lệ giá vốn 10–45%, đơn giá nhập bám theo giá chợ của từng nguyên liệu.
Dữ liệu vận hành gồm nhập/xuất kho, order, thanh toán và chốt giá vốn.

Chạy từ thư mục gốc trên CSDL mới đã migration:

```bash
make db-up
make migrate
make seed
```

Mặc định: seed `42`, `2` tháng (60 Business Date trước mốc `--now`), 70 order ngày thường và 110
order cuối tuần, dao động ±15% (khoảng 4.800 order). Quán mở 10:00–22:00 với hai đỉnh trưa/tối;
mỗi order có 1–4 món khác nhau, mỗi món 1–2 suất, phân bố món không đồng đều. Truyền `--orders`
để ép đúng một tổng số order (dùng cho kiểm tra nhanh). Số order ghi thành công phải bằng số đã
lên kế hoạch; thiếu mục tiêu hoặc sai bất biến làm lệnh thất bại.

Kho: thịt, hải sản, rau, bún, phở nhập 08:00 hằng ngày; hàng khô nhập thứ Hai và thứ Năm. Lượng
nhập bằng nhu cầu dự kiến đến lần nhập kế tiếp cộng tồn tối thiểu, trừ tồn còn dùng được, làm tròn
lên 0,5 kg; mỗi dòng không quá 30 kg và tồn một nguyên liệu không vượt 40 kg (kiểm tra trên toàn
bộ sổ kho sau khi sinh). Đơn giá dao động ±10% quanh giá thường ngày. Mỗi sáng lô đã quá hạn được
xuất hủy với lý do “Hết hạn”; ngoài ra mỗi ngày có 10% khả năng hao hụt 0,2–1 kg một nguyên liệu
tươi. Order thiếu nguyên liệu thì nhập bổ sung đúng thời điểm đó rồi thử lại.
Thống kê JSON cuối lệnh ghi số lượt thử, số từ chối, nguyên nhân, order chờ đối soát/tranh chấp,
schema và revision. Savepoint rollback toàn bộ chứng từ bị từ chối; lỗi bất ngờ dừng ngay với ngữ cảnh.

Kiểm tra nhanh trên một schema thử riêng đã migration:

```bash
cd apps/api
DATABASE_URL='mysql+asyncmy://restaurant:restaurant@localhost:3306/restaurant_acceptance_20261017?charset=utf8mb4' \
  uv run python ../../scripts/seed/generate.py --seed 42 --months 1 --orders 40
```

Bản trước sửa chỉ tạo 22/40 order mà vẫn báo thành công. Bản sửa đã có test đạt đúng 40/40.
Đợt MySQL của bộ sinh 12 tháng cũ (trước khi chuyển sang Phụ lục B.1) dùng `--months 12 --orders 365 --now 2026-10-17T10:00:00+07:00`: đạt **365 order,
104 phiếu nhập, 38 phiếu xuất**, toàn bộ bất biến đạt; 4 order chờ đối soát và 4 tranh chấp
được ghi riêng, bàn vật lý đều đã giải phóng. Đây là kiểm tra tính toàn vẹn, chưa phải đo tải 20.000 order.

Tài khoản mô phỏng: `seed_manager`, `seed_cashier`, `seed_warehouse`; mật khẩu `matkhau123`.
Seed từ chối CSDL đã có món; không chạy lặp để bổ sung dữ liệu. `make db-down` rồi `make db-up`
giữ nguyên volume, nên không tạo CSDL sạch. Dùng schema thử mới nếu muốn sinh lại.

View và quyền AI được áp dụng riêng theo [`db/views/README.md`](../../db/views/README.md).
Kết quả kiểm chứng ở [`docs/testing/results-2026-10-17.md`](../../docs/testing/results-2026-10-17.md).

Có thể truyền `--now` dạng ISO để tái lập mốc thời gian. Seed giữ phân bố theo cuối tuần và
khung giờ, và thử lại có giới hạn khi thiếu tồn. Bản tóm tắt JSON
không chứa tài khoản/mật khẩu CSDL. Xem [nhật ký trả nợ](../../docs/testing/technical-debt-2026-10-17.md).
