# Kế hoạch đồng bộ code và tài liệu

> **For agentic workers:** Thực hiện từng plan theo thứ tự dưới đây. Các bước dùng checklist; thay đổi hành vi phải theo TDD: viết test, xác nhận đỏ, sửa tối thiểu, xác nhận xanh.

**Goal:** Đồng bộ MVP với báo cáo đã merge và hoàn tất make gate.

**Architecture:** Tách thành các lát cắt độc lập. Ổn định test trước; sau đó cấu hình Business Date; giữ chỗ server-side; quota/cache AI và cuối cùng đồng bộ tài liệu.

**Tech Stack:** FastAPI, Python 3.12, SQLAlchemy 2 async, Alembic, MySQL 8.4, Next.js 16, React 19, TypeScript, pytest, Vitest.

**Spec:** ../specs/2026-10-11-align-code-with-report-design.md

## Global Constraints

- DBMS là MySQL 8.4; định danh CSDL giữ tiếng Việt theo §4.2.2.
- Truy vấn nghiệp vụ chỉ dùng SQLAlchemy; không nối chuỗi SQL.
- Business Date được tính tập trung qua app.shared.business_date.
- Thao tác ghi kiểm tra quyền API, dùng transaction và ghi audit khi có rủi ro cao.
- AI dùng đúng một view/tài khoản chỉ đọc riêng theo vai trò; SQL luôn qua guard.validate_sql.

---

## Thứ tự thực hiện

1. [Làm ổn định baseline pytest](2026-10-11-stabilize-api-gate.md) — cô lập test khỏi .env và sửa bộ lọc kỳ chi phí xuất kho.
2. [Cấu hình và Business Date hiệu lực](2026-10-11-configurable-business-date.md) — migration, API, helper, UI, audit và cảnh báo hạn lô.
3. [Giữ chỗ món server-side](2026-10-11-server-side-item-holds.md) — FIFO, gửi idempotent, kiểm kê và giao diện gọi món.
4. [Quota/cache AI và view phân quyền](2026-10-11-ai-quota-cache-views.md) — quota theo người/ngày nghiệp vụ, cache an toàn và lượng giữ cho Bếp.
5. [Đồng bộ tài liệu dự án](2026-10-11-document-consistency.md) — quy tắc Business Date và 22 liên kết ảnh sai casing.

### Checkpoint chung

- Sau plan 1: API tests xanh; lỗi do test fixture được phân biệt với lỗi code.
- Sau plan 2: mọi caller dùng chung chính sách Business Date; cấu hình ngày hiệu lực và cảnh báo hạn lô đúng ngưỡng; test API/schema/UI xanh.
- Sau plan 3: giữ không làm trừ tồn; gửi trùng không tạo hiệu ứng kép; kiểm kê cô lập được.
- Sau plan 4: quota riêng theo user; dữ liệu động luôn mới; view/grant vẫn đúng phạm vi.
- Sau plan 5: AGENTS.md khớp report; tất cả link ảnh tồn tại.
- Cuối cùng chạy make gate; không đánh dấu xong nếu còn lỗi.

### Kiểm chứng cuối

- Chạy `make gate` từ thư mục gốc sau khi từng lát cắt đã qua test mục tiêu.
- Kiểm tra migration chain bằng `cd apps/api && uv run alembic heads`; Expected: đúng một head.
- Rà schema/view/grant bằng các test schema và bộ test MySQL 8.4 được liệt kê trong plan tương ứng.
- Nếu lỗi hạ tầng cục bộ làm gate không chạy, ghi rõ lệnh, lỗi và phần chưa được kiểm chứng; không suy diễn rằng code đã đạt.
