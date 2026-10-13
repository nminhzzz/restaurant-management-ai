# Sinh dữ liệu mô phỏng

`make seed` chạy `generate.py` và sinh bộ dữ liệu 12 tháng phục vụ cả báo cáo (NFR-03) lẫn thực nghiệm
Text-to-SQL (Phụ lục 4). Script chỉ chạy trên CSDL **sạch** (đã `make migrate`, chưa có món nào); nếu
đã có danh mục thì dừng và báo lỗi thay vì ghi đè.

```bash
make db-up && make migrate && make seed
cd apps/api && uv run python ../../scripts/seed/generate.py --seed 42 --months 12 --orders 20000
```

Tham số: `--seed` (mặc định 42), `--months` (12), `--orders` (tổng số order mục tiêu, 20.000). Mọi lựa
chọn ngẫu nhiên đi qua `random.Random(seed)` nên cùng `--seed` luôn dựng lại cùng bộ dữ liệu.

## Các bước

1. **Dữ liệu tham chiếu** (`seed_reference_data`): ba vai trò và dòng cấu hình hệ thống.
2. **Danh mục** (`catalog.py`): ba tài khoản `seed_manager`, `seed_cashier`, `seed_warehouse`
   (mật khẩu `matkhau123`, chỉ dùng cục bộ), 60–80 món, danh sách nguyên liệu, 5 nhà cung cấp, 20 bàn,
   công thức (2–4 nguyên liệu mỗi món) và giá bán có hiệu lực từ trước ngày đầu tiên của bộ dữ liệu.
3. **Vận hành** (`operations.py`): với từng Business Date trong 12 × 30 ngày, sinh order, thanh toán,
   nhập kho và xuất hao hụt; cuối mỗi tháng gọi đóng tháng (`close_month`, `backfill_issue_costs`) để có
   `GIA_BINH_QUAN_THANG` và giá vốn phiếu xuất. Tất cả đi qua service của các module, nên trừ kho theo
   công thức và theo lô FIFO, Business Date 06:00–06:00 và trạng thái dòng món đều tuân thủ nghiệp vụ
   (generator không ghi trực tiếp vào bảng).

## Đặc trưng mô phỏng (`config.py`)

- Hai đỉnh trong ngày (trưa 11–13h, tối 18–20h) và giờ thấp điểm 15–16h (`HOUR_WEIGHTS`).
- Cuối tuần cao hơn ngày thường (`WEEKEND_MULTIPLIER = 1.6`); hệ số mùa vụ theo tháng
  (`MONTH_SEASONALITY`).
- Phân bố món theo luật lũy thừa (`DISH_POWER_LAW_EXPONENT = 1.2`): một số ít món chiếm phần lớn order.
- Mỗi order là đơn tại chỗ do tài khoản `seed_manager` tạo; 4% bị hủy (`CANCELLED_ORDER_RATIO`), 70%
  thanh toán tiền mặt, phần còn lại (26%) qua QR. Trong số QR, `RECONCILE_RATIO` và `DISPUTE_RATIO` điều
  khiển các giao dịch hết hạn phải đối soát hoặc bị xác nhận chưa nhận được tiền.
- Nhập kho vào thứ Hai và thứ Năm (20 nguyên liệu mỗi lần), mỗi ngày có 10% khả năng một phiếu xuất
  hao hụt nhỏ.

## Giới hạn đã biết

- Nguyên liệu trong bộ seed chưa có `SoNgayBaoQuan`, nên các lô nhập không có `HanSuDung`; các câu hỏi về
  lô sắp hết hạn (ví dụ `Q092` trong `data/eval/questions.jsonl`) trả về rỗng trên dữ liệu này.
- Phiếu nhập luôn dùng nhà cung cấp đầu tiên (`supplier_ids[0]`), nên các câu hỏi so sánh nhà cung cấp
  chỉ có một nhà cung cấp có dữ liệu nhập.
