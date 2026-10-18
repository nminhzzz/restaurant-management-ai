# Kết quả trả nợ kỹ thuật ngày 17/10/2026

Phạm vi: sáu khoản được người dùng duyệt sau [lượt kiểm chứng trước](results-2026-10-17.md).
Giữ nguyên bằng chứng cũ; đây là trạng thái mới nhất của các khoản đó. Chưa commit/push hoặc
áp dụng migration vào CSDL làm việc của người dùng; các thao tác CSDL trong đợt này dùng schema thử.

## Các khoản đã xử lý

| Khoản | Thay đổi | Kiểm chứng |
| --- | --- | --- |
| Trạng thái bàn | `BAN.MaOrderDangPhucVu` gắn lượt phục vụ; thanh toán không tự giải phóng. Thu ngân/Quản lý giải phóng riêng với mã order kỳ vọng, khóa bàn và audit. Tạo/đổi bàn kiểm tra lại bàn trống; thanh toán/hủy cũ không đổi bàn của lượt mới. Giao diện lọc và hiển thị cùng trạng thái vật lý. | Test API, giao diện, MySQL và thao tác Chrome |
| Business Date | `business_month_range` trả khoảng `[06:00 ngày đầu tháng, 06:00 ngày đầu tháng sau)`, dùng cho nhập kho, backfill và hao hụt. Backfill làm tròn DECIMAL 4 chữ số. | Test 05:59/06:00 cả hai đầu, tháng 12, tháng sai/giới hạn năm |
| CI MySQL | Job MySQL 8.4 riêng tạo hai schema, chạy migration, view, ba tài khoản AI và integration. `CI_REQUIRE_MYSQL=1` biến skip thành lỗi. | Chạy lệnh tương đương local trên MySQL 8.4.11; phép thử skip thoát mã 1 |
| Seed | Savepoint cho từng chứng từ, rollback khi bị từ chối; thống kê nguyên nhân và lượt thử. Lỗi bất ngờ dừng có ngữ cảnh, thử lại có giới hạn để đạt đúng mục tiêu. Kiểm tra tồn nguyên liệu/lô/sổ và trạng thái order cuối lượt. | Ca hồi quy đúng 40/40; seed MySQL 12 tháng đúng 365/365, toàn vẹn đạt |
| Cache/hạn mức AI | Hai bảng hạ tầng MySQL, giữ hạn mức nguyên tử trong transaction riêng trước từng lần sinh SQL; TTL, Business Date, role, model/provider, schema/prompt và cấu hình guard trong khóa cache. Cache hit vẫn qua guard. Dọn cache tách riêng. | Test đồng thời nhiều store/worker, restart giả lập, retry/lỗi provider/rollback, TTL và đổi ngữ cảnh |
| Tài liệu | Danh sách nợ cũ đã thay bằng trạng thái có bằng chứng. Phân biệt bộ 95 câu đã chạy với kế hoạch mới 80 câu chính thức + 30 câu phát triển. | README gốc/API/web/seed, roadmap, báo cáo và nhật ký đã đồng bộ |

## Kết quả chạy

- `make gate`: **479 test backend, 157 test frontend**, định dạng/lint/mypy/TypeScript/build đều qua.
  Backend có hai cảnh báo deprecation từ phụ thuộc; 18 ca integration/slow được loại khỏi lượt gate.
- MySQL 8.4.11: **10 ca integration qua, không skip**. Gồm ba luồng tiền mặt/QR giả lập/SePay,
  hợp đồng view, quyền ba vai trò, quota đồng thời, cache đồng thời và backfill trạng thái bàn cũ.
- Review độc lập đã phát hiện hai lỗi trong bản tích hợp ban đầu: deadlock cache khi DELETE theo
  khoảng hết hạn trước upsert và bỏ sót bàn Trống có order mở khi migration. Cả hai đã sửa,
  có ca tái hiện trên MySQL; lượt review lại không còn phát hiện quan trọng trong phạm vi sửa.

Log: [gate](artifacts/2026-10-17-debt/gate.txt),
[MySQL integration](artifacts/2026-10-17-debt/mysql-integration.txt),
[chính sách skip CI](artifacts/2026-10-17-debt/ci-skip-policy.txt),
[seed MySQL](artifacts/2026-10-17-debt/seed-mysql.txt).

Job GitHub Actions mới **chưa chạy trên GitHub**, vì chưa push thay đổi. Lệnh chuẩn bị và integration
đã chạy local bằng cùng script/cấu hình schema thử; không coi đó là kết quả remote CI.

## Seed và giao diện trên MySQL

Schema mới `restaurant_seed_debt_20261017`, migration `e31f52a6c901`, seed `42`:

```bash
DATABASE_URL='mysql+asyncmy://restaurant:restaurant@localhost:3306/restaurant_seed_debt_20261017?charset=utf8mb4' \
PAYMENT_GATEWAY=simulator uv run --project apps/api python scripts/seed/generate.py \
  --months 12 --orders 365 --now 2026-10-17T10:00:00+07:00
```

Đúng **365 order, 104 phiếu nhập, 38 phiếu xuất**, không có lượt bị từ chối; 4 order chờ đối soát,
4 tranh chấp được ghi riêng. Bàn vật lý đã giải phóng sau lịch sử phục vụ; ba tầng tồn kho và
trạng thái tài chính đều qua validator. Đây là mẫu giảm quy mô kiểm tra 12 tháng, **chưa phải lượt
sinh mặc định 20.000 order hoặc phép đo hiệu năng tải**.

Trên Chrome 768×1024 giả lập cảm ứng, đăng nhập lại vào schema thử mới, chọn Bàn 01, gọi một
Xôi gà 100.000 đồng, gửi bếp và thanh toán tiền mặt. Hóa đơn 342 của order 367 đã phát hành,
bàn vẫn hiển thị Đang phục vụ và bộ lọc Có khách 1/Trống 19. Chạm Giải phóng bàn, giao diện tải
lại thành Có khách 0/Trống 20, Bàn 01 Trống. Không có tràn ngang ở lần đo sau thao tác.

Ảnh: [sau thanh toán](artifacts/2026-10-17-debt/table-occupied-after-payment.png),
[sau giải phóng](artifacts/2026-10-17-debt/table-released.png),
[kết quả đo](artifacts/2026-10-17-debt/table-release-metrics.json).
Số hóa đơn/order chỉ là định danh trong schema thử này.

## Migration và vận hành

Chạy `make migrate` trên CSDL đích trước khi khởi động bản mới. Revision `e31f52a6c901` thêm:

- `BAN.MaOrderDangPhucVu`: khóa ngoại tới order, unique khi có giá trị.
- `HAN_MUC_AI_NGAY`: Business Date và số lần sinh SQL đã giữ lượt.
- `BO_NHO_DEM_SQL_AI`: khóa ngữ cảnh, SQL đã kiểm duyệt và thời điểm hết hạn UTC.

Hai bảng sau là hạ tầng vận hành, không mở rộng phạm vi dữ liệu của các view AI. Migration phục hồi
bàn có đúng một order mở kể cả nhãn cũ đang Trống; nếu có nhiều order mở ở một bàn, dừng **trước
DDL** để đối soát thay vì tự chọn và làm mất dấu order. Bàn đang phục vụ chỉ còn chứng từ tài chính
đã đóng/chờ đối soát được liên kết với order gần nhất, vẫn cần xác nhận khách rời để giải phóng.

Hạn mức AI tính **lần sinh SQL logic**, bao gồm retry qua guard; không phải tổng HTTP request/token,
không tính diễn giải hoặc fallback nội bộ provider thành một lượt sinh SQL riêng. Lượt đã giữ
không hoàn lại khi câu hỏi lỗi/rollback. Các worker dùng chung CSDL giữ cùng bộ đếm.

TTL mặc định 300 giây, cấu hình `AI_SQL_CACHE_TTL_SECONDS` trong khoảng 1–86400. Hết TTL thì cache
không được dùng dù chưa dọn vật lý. Chạy `make ai-cache-prune` định kỳ, ví dụ mỗi giờ, để dọn theo
lô khóa chính; không dọn theo khoảng trong transaction ghi cache, tránh deadlock MySQL. Đây là
lệnh vận hành đã có, không tự cài cron trên máy người dùng.

Chuẩn bị integration: `MYSQL_CONTAINER=restaurant-db MYSQL_ROOT_PASSWORD=restaurant-root bash scripts/prepare_ci_mysql.sh`.
Đặt `DATABASE_URL` về `restaurant_integration`, `MYSQL_TEST_DATABASE_URL` về `restaurant_test`,
ba `AI_READONLY_URL_*` về tài khoản `ci_ai_*` tương ứng và `CI_REQUIRE_MYSQL=1`, chạy
`cd apps/api && uv run pytest -m integration`. Script không xóa schema cũ; schema luồng phải
không có dữ liệu bán hàng seed sẵn vì kiểm tra tổng báo cáo cần nền rỗng.

## Phần không thuộc sáu khoản nợ đã xử lý

SUS/UAT với người thật, tablet vật lý/Edge/Safari, tải đồng thời và p95/INP, sao lưu–phục hồi,
thực nghiệm bộ 80+30 câu mới và toàn bộ nghiệp vụ giữ chỗ theo báo cáo mới vẫn cần thực hiện
theo kế hoạch tương ứng. Không suy kết quả các phần đó từ gate hoặc mẫu seed đã chạy.
