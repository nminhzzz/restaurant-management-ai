# AGENTS.md — restaurant-management-ai

Đồ án tốt nghiệp: hệ thống quản lý nhà hàng tích hợp trợ lý AI (Text-to-SQL tiếng Việt).
Quy tắc chung trong `~/.codex/AGENTS.md` vẫn áp dụng đầy đủ; file này chỉ bổ sung phần riêng của dự án.

## Stack

| Tầng | Công nghệ |
| --- | --- |
| Web | Next.js 16 (App Router), React 19, TypeScript, Tailwind 4, Vitest |
| API | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic, pytest, ruff, mypy |
| Dữ liệu | PostgreSQL 18, view phân quyền `VW_AI_*` |
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
- **Định danh CSDL là ngoại lệ có chủ đích**: tên bảng/cột giữ nguyên tiếng Việt theo ERD trong báo cáo
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
- Truy vấn chạy bằng tài khoản CSDL chỉ-đọc, có timeout và trần số dòng (`AI_MAX_ROWS`).

## Cạm bẫy đã biết

- Báo cáo đang **mâu thuẫn về DBMS**: §1.4.2 và §4.1.2 ghi PostgreSQL, §3.2 ghi MySQL. Dự án đã chọn
  PostgreSQL; khi sửa tài liệu phải đồng bộ lại §3.2.
- `next-env.d.ts` bị gitignore; `pnpm typecheck` trên bản clone mới không có file này vẫn phải xanh —
  đừng dùng `LayoutProps`/`PageProps` sinh tự động trong code.
- `apps/web/AGENTS.md` do chính `next dev` sinh và ghi lại; không sửa file đó.
