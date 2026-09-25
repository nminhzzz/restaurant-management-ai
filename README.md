# Hệ thống quản lý nhà hàng tích hợp AI

Đồ án tốt nghiệp — Trường Đại học Mở Hà Nội, Khoa Công nghệ thông tin.

Hệ thống gồm hai khối: **khối nghiệp vụ** quản lý nhà hàng (danh mục, bán hàng, kho, báo cáo, cài đặt)
và **khối trợ lý AI** cho phép hỏi đáp, phân tích dữ liệu kinh doanh bằng tiếng Việt qua Text-to-SQL.

## Kiến trúc

```
Next.js (web)  ──HTTP──▶  FastAPI (api)  ──SQL──▶  MySQL
                                │
                                └──▶  LLM (API thương mại, dự phòng Ollama)
```

- Câu SQL do LLM sinh ra đi qua lớp kiểm duyệt `sqlglot` trước khi thực thi: chỉ nhận `SELECT`
  trên đúng view phân quyền của vai trò đang hỏi.
- Trợ lý AI đọc dữ liệu qua các view chỉ-đọc `vw_ai_quanly` / `vw_ai_thungan` / `vw_ai_kho`,
  tách biệt hoàn toàn khỏi bảng nghiệp vụ lõi. Mỗi vai trò truy vấn bằng tài khoản CSDL chỉ-đọc
  riêng, chỉ được `GRANT SELECT` trên đúng view của mình (NFR-06).

## Cấu trúc repository

| Đường dẫn | Nội dung |
| --- | --- |
| `apps/api` | Backend FastAPI, 6 module nghiệp vụ + pipeline Text-to-SQL |
| `apps/web` | Frontend Next.js (App Router, TypeScript, Tailwind) |
| `db/views` | Định nghĩa view phân quyền cho trợ lý AI |
| `data/eval` | Bộ dữ liệu đánh giá 50–100 cặp câu hỏi tiếng Việt – SQL chuẩn |
| `scripts/seed` | Sinh dữ liệu mô phỏng 12 tháng phục vụ báo cáo và thực nghiệm |
| `docs` | Báo cáo, sơ đồ UML (drawio), hình ảnh, kế hoạch triển khai |
| `docs/plans` | Lộ trình tổng và kế hoạch chi tiết từng phase (`phases/`) |

## Yêu cầu môi trường

- Python 3.12+ và [uv](https://docs.astral.sh/uv/)
- Node.js 20+ và pnpm 9+
- Docker (chạy MySQL)

## Bắt đầu

```bash
make setup      # cài dependencies cho cả api và web
make db-up      # khởi động MySQL bằng docker compose
make env        # tạo tập biến môi trường cục bộ từ file mẫu
make migrate    # tạo schema (khi có migration đầu tiên)
make api        # http://localhost:8000/docs
make web        # http://localhost:3000
```

## Lệnh thường dùng

| Lệnh | Việc |
| --- | --- |
| `make gate` | Chạy toàn bộ cổng kiểm tra: lint · type-check · test · build |
| `make lint` / `make fmt` | Kiểm tra / tự sửa định dạng và lint |
| `make typecheck` | mypy (api) và tsc (web) |
| `make test` | pytest (api) và vitest (web) |
| `make db-up` / `make db-down` | Bật / tắt MySQL |

Cài hook cục bộ (ruff + prettier) một lần bằng `pipx install pre-commit && pre-commit install`;
hook chỉ là lớp nhanh, `make gate` và CI vẫn là cổng kiểm tra đầy đủ.

## Phân quyền

Ba vai trò cố định: **Chủ nhà hàng/Quản lý**, **Thu ngân/Nhân viên order**, **Nhân viên kho**.
Quyền được kiểm tra ở tầng API (`app.core.dependencies.require_roles`), không chỉ ẩn nút trên giao diện.

## Hiện trạng

Đã xong **Phase 0 → 7**: lược đồ CSDL 29 bảng theo báo cáo cộng `DEM_ORDER` (`migrations/versions/`),
ba view phân quyền `vw_ai_*` và tài khoản chỉ-đọc riêng (`db/views/`), sáu module nghiệp vụ
Cài đặt · Danh mục · Kho · Bán hàng · Báo cáo · Trợ lý AI có API và giao diện dùng được, cùng bộ
dữ liệu mô phỏng 12 tháng (`make seed`), bộ 75 câu hỏi – SQL chuẩn (`data/eval/questions.jsonl`) và
harness ba cấu hình đối chứng (`data/eval/harness.py`).

Trợ lý AI và lần chạy thực nghiệm A/B/C cần cấu hình nhà cung cấp LLM (`AI_PROVIDER`, `LLM_MODEL`,
`AI_API_KEY`, hoặc `AI_PROVIDER=ollama`); bộ test dùng client giả nên không cần khoá. Hai việc chưa
chốt được vì phụ thuộc lựa chọn đó là **Q5** (mô hình cho cấu hình C) và **Q6** (domain API được phép)
— xem `docs/plans/2026-09-24-master-roadmap.md`.

Kế hoạch triển khai đầy đủ nằm ở [`docs/plans/2026-09-24-master-roadmap.md`](docs/plans/2026-09-24-master-roadmap.md):
**tám phase** từ lược đồ CSDL tới dữ liệu đánh giá, kèm thứ tự phụ thuộc và các cổng cần duyệt. Kế hoạch
chi tiết từng phase ở `docs/plans/phases/`. Nhật ký dựng khung ban đầu:
`docs/plans/2026-09-21-project-skeleton.md`.

Đặc tả đầy đủ: [`docs/BaoCao_HeThongQuanLyNhaHang.md`](docs/BaoCao_HeThongQuanLyNhaHang.md).
