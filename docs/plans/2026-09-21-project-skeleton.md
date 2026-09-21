# Kế hoạch — dựng khung dự án

Ngày: 2026-09-21 · Nhánh: `chore/project-skeleton`

## Mục tiêu

Đưa repository từ trạng thái chỉ có tài liệu sang một khung dự án chạy được: cấu trúc thư mục,
toolchain, quy ước, CI và các primitive dùng chung đã được kiểm thử — làm nền cho ba thành viên
triển khai song song sáu module.

**Ngoài phạm vi lần này:** DDL 29 bảng, tập view `VW_AI_*`, seed dữ liệu mô phỏng, bộ dữ liệu
đánh giá chính thức, và logic nghiệp vụ của từng module.

## Quyết định đã chốt

| Hạng mục | Chọn | Lý do |
| --- | --- | --- |
| DBMS | PostgreSQL 18 | Khớp §1.4.2 và §4.1.2 của báo cáo; `sqlglot` dialect postgres; `GRANT` chỉ-đọc chặt cho tài khoản của trợ lý AI |
| Cấu trúc | Monorepo `apps/api` + `apps/web` | Backend và frontend tiến hoá cùng nhịp, chia sẻ tài liệu và CI |
| Backend | FastAPI + SQLAlchemy 2 async + Alembic | Đúng §4.1.1 |
| Frontend | Next.js 16 App Router + TS + Tailwind 4 | Đúng §1.4.2 |
| Định danh CSDL | Giữ tiếng Việt theo ERD | Khớp báo cáo và bộ dữ liệu đánh giá; tên lớp/biến Python vẫn tiếng Anh |
| Kiểm thử web | Vitest + Testing Library | Chạy nhanh, cùng hệ sinh thái Vite |

## Đã hoàn thành

- **Gốc repo**: `README.md`, `AGENTS.md`, `Makefile`, `docker-compose.yml`, `.env.example`,
  `.editorconfig`, bổ sung `.gitignore` cho Node/Next/uv.
- **CI** (`.github/workflows/ci.yml`): job `api` (ruff format check · ruff check · mypy · pytest)
  và job `web` (prettier check · eslint · tsc · vitest · next build).
- **Backend**: app factory + 6 router module; `core/` (config, session async, argon2 + JWT,
  dependency xác thực và `require_roles`, error handler trả thông báo tiếng Việt);
  `shared/` (declarative base, soft delete, Business Date 06:00, audit log `NHAT_KY_HE_THONG`,
  pagination, enum vai trò).
- **Module AI**: `scope.py` (vai trò → view), `guard.py` (kiểm duyệt SQL bằng `sqlglot`:
  một câu lệnh, chỉ `SELECT`, chỉ quan hệ trong danh sách view cho phép, luôn áp trần số dòng),
  `pipeline/` với `normalize` đã hoàn chỉnh và bốn bước còn lại là interface chờ triển khai,
  endpoint `POST /assistant/chat` trả 501 để frontend tích hợp được ngay.
- **Frontend**: route group `(app)` với 6 trang module + `/login`, app shell, registry module
  dùng chung, API client có kiểu, khung chat gọi thật vào endpoint của trợ lý AI.
- **Tài nguyên**: `db/views/README.md` ghi hợp đồng ba view phân quyền; `data/eval/` có đặc tả
  định dạng bộ câu hỏi – SQL và file mẫu; `scripts/seed/README.md` ghi yêu cầu dữ liệu mô phỏng.

## Kiểm chứng

| Cổng | Kết quả |
| --- | --- |
| `ruff format --check` · `ruff check` · `mypy` | xanh (46 file nguồn) |
| `pytest` | 43 test xanh |
| `prettier --check` · `eslint` · `tsc --noEmit` | xanh |
| `vitest` | 4 test xanh |
| `next build` | xanh, 8 route tĩnh |

## Việc tiếp theo

1. **DDL + migration**: 29 bảng theo §3.2.1, khoá ngoại và index theo §3.2.3, kèm ba view
   `VW_AI_*` và tài khoản CSDL chỉ-đọc.
2. **Module 1 — Danh mục**: món ăn, phiên bản giá/công thức theo Business Date, xoá mềm.
3. **Module 2 — Bán hàng**: order, phiếu bếp, thanh toán, hoá đơn (phụ thuộc DDL).
4. **Module 3 — Kho**: nhập theo lô, trừ FIFO, kiểm kê.
5. **Module 5 — Cài đặt**: tài khoản, phân quyền, nhật ký — cần trước để có dữ liệu đăng nhập thật.
6. **Module AI**: prompt, generator, executor, interpreter + harness chạy ba cấu hình A/B/C.
7. **Dữ liệu**: bộ 50–100 câu hỏi – SQL và script sinh dữ liệu 12 tháng.

## Rủi ro

- **Báo cáo mâu thuẫn DBMS**: §3.2 ghi MySQL trong khi §1.4.2 và §4.1.2 ghi PostgreSQL. Cần sửa
  §3.2 cho thống nhất trước khi viết DDL, nếu không phần thiết kế CSDL sẽ lệch với sản phẩm.
- **Prompt của trợ lý AI phụ thuộc lược đồ**: bước `prompt.py` chỉ nên triển khai sau khi DDL ổn định.
- **Phụ thuộc mạng khi build**: đã bỏ `next/font/google` để `next build` chạy được cả khi offline.
