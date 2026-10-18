# apps/api — Backend API

FastAPI, SQLAlchemy async và MySQL 8.4; gồm sáu module và pipeline Text-to-SQL theo vai trò.
Quy ước dự án nằm trong `AGENTS.md` ở thư mục gốc; đặc tả trong `docs/BaoCao_HeThongQuanLyNhaHang.md`.

## Cấu trúc

| Đường dẫn | Nội dung |
| --- | --- |
| `src/app/core/` | Cấu hình, CSDL, xác thực, phân quyền và xử lý lỗi |
| `src/app/shared/` | ORM base, Business Date, audit log và phân trang |
| `src/app/modules/` | Danh mục, bán hàng, kho, báo cáo, cài đặt và trợ lý AI |
| `migrations/` | Migration Alembic |
| `tests/` | Unit test, kiểm thử API và integration MySQL |

## Lệnh

```bash
uv sync
uv run uvicorn app.main:app --reload --app-dir src --port 8000
uv run alembic upgrade head
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy .
```

Unit test không nạp `.env` hoặc các biến cấu hình từ shell; từng ca tự cấu hình provider cần kiểm tra.
Vì vậy cấu hình SePay và khóa LLM local không làm đổi nhánh xử lý của test. Integration giữ cấu hình
CSDL thật và chạy riêng bằng `uv run pytest -m integration`.

Kiểm thử xuyên module MySQL trong `tests/modules/test_mysql_workflow.py` cần
`MYSQL_TEST_DATABASE_URL` trỏ đến schema mới, đã migration, có tiền tố `restaurant_test` hoặc
`restaurant_acceptance`. Chứng từ được rollback sau mỗi ca; bộ đếm mã order dùng kết nối commit
riêng nên có thể tăng. Không dùng schema đã seed cho các ca này vì kiểm tra tổng báo cáo cần nền rỗng.

Kiểm tra view cần `DATABASE_URL` và đủ ba biến `AI_READONLY_URL_MANAGER`, `AI_READONLY_URL_CASHIER`,
`AI_READONLY_URL_WAREHOUSE` cùng trỏ về CSDL đã cài view/quyền. Hướng dẫn và kết quả cụ thể ở
[`docs/testing/results-2026-10-17.md`](../../docs/testing/results-2026-10-17.md).

## Trạng thái bàn và AI dùng chung

Chạy migration tới head `f8db86d6d0a4` trước khi khởi động bản mới. Chuỗi migration gần đây bổ sung
`BAN.MaOrderDangPhucVu`, hai bảng hạ tầng `HAN_MUC_AI_NGAY`, `BO_NHO_DEM_SQL_AI`, các trường cấu hình
vận hành (`SoNgayCanhBaoHetHan`, `ThoiGianGiuChoPhut`, `SoCauHoiAIMoiNgay`), khóa hạn mức AI theo
`(BusinessDate, MaNguoiDung)`, hai bảng giữ chỗ `GIU_CHO_MON`/`CHI_TIET_GIU_CHO` và mở rộng
`GIAO_DICH_THANH_TOAN.TrangThai` cho trạng thái “Chờ xác minh thanh toán”. Các bảng này không nằm
trong view chỉ-đọc của AI. Migration khôi phục bàn ghi Trống nhưng còn một order mở; nếu một bàn có
nhiều order mở, migration dừng trước DDL để đối soát dữ liệu.

Migration `f8db86d6d0a4` tạo trigger chặn UPDATE/DELETE trên `NHAT_KY_HE_THONG` và `TRUY_VAN_AI`.
MySQL cần bật `log_bin_trust_function_creators=1` (đã có trong `docker-compose.yml` và CI) để tài khoản
migration tạo được trigger khi binary logging đang bật.

Giữ chỗ nguyên liệu là API server-side: `POST/PATCH/DELETE /sales/holds`; gửi món dùng `hold_id` trên
dòng order. Giữ chỗ chỉ phân bổ theo lô và không ghi `GIAO_DICH_KHO`; khi gửi mới trừ kho đúng một lần.

Luồng ngoại lệ thanh toán: `POST /sales/payments/{id}/request-verification` (Thu ngân/Quản lý),
`POST /sales/payments/{id}/reopen` và `POST /sales/orders/{id}/close-unpaid` (Quản lý). Order đang
chờ xác minh bị khóa, không nhận thêm món; đóng chưa thu không tạo hóa đơn.

Hạn mức AI tính theo từng người dùng trong ngày; giá trị mặc định lấy từ `SoCauHoiAIMoiNgay` trong
cấu hình hệ thống (50), không còn là một bộ đếm chung cho cả nhà hàng.

Thanh toán không tự giải phóng bàn. Thu ngân/Quản lý gọi `POST /sales/tables/{id}/release`
với `order_id` đang hiển thị khi khách rời; backend khóa bàn và so lại liên kết order.
Tạo/đổi bàn kiểm tra bàn trống; thanh toán hay hủy order cũ không được giải phóng bàn của lượt mới.

Hạn mức AI lưu MySQL và giữ lượt trước mỗi lần sinh SQL logic, kể cả retry sau guard hoặc lỗi provider.
Không hoàn lượt khi transaction câu hỏi rollback. Đây không phải bộ đếm token hoặc mọi HTTP request:
fallback nội bộ provider và diễn giải kết quả không tính thành lượt sinh SQL riêng.

Cache SQL có TTL `AI_SQL_CACHE_TTL_SECONDS` (mặc định 300, từ 1 đến 86400 giây), khóa theo vai trò,
Business Date, schema/prompt, provider/model và cấu hình guard. Cache hit vẫn kiểm duyệt SQL.
Ghi cache không dọn dữ liệu hết hạn trong cùng transaction để tránh deadlock MySQL.
Chạy định kỳ `make ai-cache-prune` từ thư mục gốc (ví dụ mỗi giờ); thao tác xóa theo lô,
chỉ xóa khóa vẫn hết hạn khi kiểm tra lại. TTL vẫn được kiểm tra khi đọc nếu chưa chạy dọn.

Job CI MySQL riêng được thêm tại `.github/workflows/ci.yml`. Chạy tương đương local:
`MYSQL_CONTAINER=restaurant-db MYSQL_ROOT_PASSWORD=restaurant-root bash scripts/prepare_ci_mysql.sh`,
sau đó đặt URL trỏ đúng `restaurant_integration`, `restaurant_test`, ba tài khoản `ci_ai_*`,
và `CI_REQUIRE_MYSQL=1` trước khi chạy `uv run pytest -m integration`. Có ca skip thì lệnh thất bại.
Script này chỉ chuẩn bị hai schema thử cố định; không xóa dữ liệu hoặc nạp lại seed.

Chi tiết: [kết quả trả nợ kỹ thuật](../../docs/testing/technical-debt-2026-10-17.md).
