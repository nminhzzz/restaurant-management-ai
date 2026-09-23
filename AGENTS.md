# AGENTS.md — restaurant-management-ai

Đồ án tốt nghiệp: hệ thống quản lý nhà hàng tích hợp trợ lý AI (Text-to-SQL tiếng Việt).
Quy tắc chung trong `~/.codex/AGENTS.md` vẫn áp dụng đầy đủ; file này chỉ bổ sung phần riêng của dự án.

## Stack

| Tầng | Công nghệ |
| --- | --- |
| Web | Next.js 16 (App Router), React 19, TypeScript, Tailwind 4, Vitest |
| API | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic, pytest, ruff, mypy |
| Dữ liệu | MySQL 8.4, view phân quyền `vw_ai_*` (một tài khoản chỉ-đọc riêng cho mỗi vai trò) |
| AI | LLM qua API thương mại (mặc định), dự phòng Ollama; kiểm duyệt SQL bằng `sqlglot` |

## Bản đồ repository

```
apps/api/src/app/
├── core/          # config, database, security, dependencies, errors
├── shared/        # base, soft delete, business date, audit, pagination, roles
└── modules/       # catalog · sales · inventory · reports · settings · ai
apps/web/src/
├── app/           # routes: (app)/<module> + /login
├── components/    # app shell, module placeholder
├── features/      # theo module, ví dụ features/assistant
├── lib/           # api-client, env, modules (registry 6 module)
└── types/
db/views/          # DDL view phân quyền cho trợ lý AI
data/eval/         # bộ câu hỏi – SQL chuẩn phục vụ đánh giá
scripts/seed/      # sinh dữ liệu mô phỏng 12 tháng
```

## Lệnh

```bash
make setup      # cài dependencies
make gate       # bắt buộc xanh trước khi kết thúc công việc
make api / make web
make db-up / make migrate
make test / make lint / make fmt / make typecheck
```

Chạy riêng: `cd apps/api && uv run pytest`, `cd apps/web && pnpm test`.

## Quy ước

- **Ngôn ngữ**: code, comment, tên file, commit message bằng tiếng Anh. Chuỗi hiển thị cho người dùng,
  tài liệu và nội dung học thuật bằng tiếng Việt.
- **Định danh CSDL là ngoại lệ có chủ đích**: tên bảng/cột giữ nguyên tiếng Việt theo lược đồ quan hệ trong báo cáo
  (`NGUYEN_LIEU`, `MaNguyenLieu`, `DaXoa`) để khớp tài liệu và bộ dữ liệu đánh giá. Tên lớp, hàm,
  biến trong Python vẫn là tiếng Anh — `class Ingredient` ánh xạ bảng `NGUYEN_LIEU`.
- Mỗi module nghiệp vụ có một gói riêng trong `apps/api/src/app/modules/` và một thư mục route riêng
  trong `apps/web/src/app/(app)/`. Logic nghiệp vụ nằm ở `service.py`, không nằm trong handler.
- `apps/web/src/lib/modules.ts` là nguồn duy nhất mô tả 6 module cho giao diện — thêm module mới thì
  sửa ở đó, đừng chép tay vào từng trang.
- Truy vấn SQL chỉ được dựng qua SQLAlchemy; không nối chuỗi SQL.
- Mọi thao tác ghi đều phải kiểm tra quyền ở tầng API. Ẩn nút trên giao diện không phải là phân quyền.
- Tuân thủ `Business Date` (06:00 → 06:00 hôm sau) qua `app.shared.business_date`; không tự tính lại.

## Trợ lý AI

- Sinh SQL rồi **bắt buộc** đi qua `app.modules.ai.guard.validate_sql` trước khi thực thi.
  Không có đường tắt nào bỏ qua bước này.
- Mỗi vai trò chỉ đọc đúng một view (`app.modules.ai.scope`). Prompt chỉ được chứa view đó.
- Truy vấn chạy bằng tài khoản CSDL chỉ-đọc **riêng cho từng vai trò** (`app.modules.ai.accounts`),
  mỗi tài khoản chỉ được `GRANT SELECT` trên đúng view của vai trò đó — không dùng chung.
- Trần số dòng `AI_MAX_ROWS` (500), timeout thực thi `AI_SQL_TIMEOUT_SECONDS` (3s) và tối đa
  `AI_MAX_SQL_ATTEMPTS` (2) lần sinh SQL cho mỗi câu hỏi đều theo NFR-06.

## Cạm bẫy đã biết

- DBMS đã chốt là **MySQL 8.4** và báo cáo cũng ghi MySQL — giữ nhất quán khi thêm nội dung CSDL,
  đừng đưa vào cú pháp PostgreSQL. Định danh giữ tiếng Việt theo lược đồ quan hệ (`NGUYEN_LIEU`,
  `MaNguyenLieu`, `DaXoa`).
- §3.2.1 của báo cáo cố ý dùng **kiểu của ngôn ngữ lập trình** (`String`, `int`, `Long`, `double`,
  `boolean`, `LocalDate`, `LocalDateTime`, `LocalTime`), không dùng kiểu vật lý của MySQL. Quy ước
  vật lý (NOT NULL, `ON DELETE`/`ON UPDATE`, CHECK, cột GENERATED, `BusinessDate` denormalize) nằm ở
  §3.2.2 — đọc kỹ trước khi viết DDL, đừng suy ra kiểu cột từ bảng ở §3.2.1.
- `next-env.d.ts` bị gitignore; `pnpm typecheck` trên bản clone mới không có file này vẫn phải xanh —
  đừng dùng `LayoutProps`/`PageProps` sinh tự động trong code.
- `apps/web/AGENTS.md` do chính `next dev` sinh và ghi lại; không sửa file đó.
- Báo cáo dùng **Class Diagram** (`docs/ClassDiagram_*.drawio`) và ánh xạ sang lược đồ quan hệ ở
  §3.2.2; BFD/DFD đã bị bỏ khỏi báo cáo nên đừng viện dẫn lại.
- Đường dẫn ảnh trong báo cáo là `Images/` (chữ hoa) — Linux phân biệt hoa/thường, đổi lại là vỡ ảnh.
