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
| `data/eval` | Bộ 95 câu hỏi tiếng Việt – SQL chuẩn và harness A/B/C |
| `scripts/seed` | Sinh dữ liệu mô phỏng 12 tháng phục vụ báo cáo và thực nghiệm |
| `docs` | Báo cáo, sơ đồ UML (drawio), hình ảnh, kế hoạch triển khai |
| `docs/plans` | Lộ trình tổng và kế hoạch chi tiết từng phase (`phases/`) |

## Yêu cầu môi trường

- Python 3.12+ và [uv](https://docs.astral.sh/uv/)
- Node.js 20+ và pnpm 9+
- Docker (chạy MySQL)

## Bắt đầu

```bash
git clone https://github.com/nminhzzz/restaurant-management-ai.git
cd restaurant-management-ai
make setup      # uv sync (api) + pnpm install (web)
make db-up      # MySQL 8.4 bằng docker compose
make env        # copy .env.example -> .env (chỉ khi chưa có)
```

Sửa `.env` trước khi chạy:

- **Bắt buộc cho trợ lý AI:** đặt `AI_API_KEY` (DeepSeek). Không có key thì đặt
  `AI_PROVIDER=fake` để trợ lý trả lời giả lập, hoặc `AI_PROVIDER=ollama` nếu đã chạy Ollama.
- Đặt `AI_LLM_TIMEOUT_SECONDS=5.0`. Mẫu `.env.example` hiện còn ghi `1.5`, giá trị này làm
  prompt đầy đủ (~4.200 ký tự, ~3 giây) luôn timeout và trợ lý trả lỗi.
- **Thanh toán:** giữ `PAYMENT_GATEWAY=simulator` để demo không cần ngân hàng; muốn chuyển
  khoản thật thì xem `docs/payment-sepay-setup.md`.

```bash
make migrate    # schema (view AI không nằm trong migration, xem bước dưới)
```

Tạo view phân quyền và tài khoản chỉ-đọc cho trợ lý AI (một lần cho mỗi CSDL):

```bash
export AI_READONLY_PASSWORD_MANAGER='...' AI_READONLY_PASSWORD_CASHIER='...' \
       AI_READONLY_PASSWORD_WAREHOUSE='...'
./scripts/apply_grants.sh
```

Sau đó điền ba URL tương ứng vào `.env`:

```dotenv
AI_READONLY_URL_MANAGER=mysql+asyncmy://ai_manager:<mật-khẩu>@localhost:3306/restaurant?charset=utf8mb4
AI_READONLY_URL_CASHIER=mysql+asyncmy://ai_cashier:<mật-khẩu>@localhost:3306/restaurant?charset=utf8mb4
AI_READONLY_URL_WAREHOUSE=mysql+asyncmy://ai_warehouse:<mật-khẩu>@localhost:3306/restaurant?charset=utf8mb4
```

Nếu bỏ trống ba URL này, chế độ `local` dùng tạm tài khoản chính; chỉ phù hợp để thử, không đạt
NFR-06.

```bash
make seed       # dữ liệu 12 tháng + tài khoản seed_* (chỉ chạy trên CSDL chưa có món)
make api        # http://localhost:8000/docs
make web        # http://localhost:3000
```

Tài khoản seed: `seed_manager`, `seed_cashier`, `seed_warehouse` — mật khẩu `matkhau123`.
Muốn thêm doanh thu sát ngày để xem biểu đồ/báo cáo:

```bash
uv run --project apps/api python scripts/seed/demo_recent.py --days 14 --per-day 10
```

Kiểm tra nhanh sau khi chạy: `curl localhost:8000/health`, đăng nhập web, mở Bán hàng/Báo cáo/Trợ lý.

**Lưu ý:** `make seed` từ chối CSDL đã có món. Muốn làm lại từ đầu, tạo CSDL mới hoặc
`docker compose down -v` (xoá toàn bộ dữ liệu MySQL — chỉ làm khi chắc chắn).

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

Đã có phần triển khai của **Phase 0 → 7** trong lộ trình ban đầu: migration CSDL, ba view phân quyền
`vw_ai_*`, tài khoản chỉ-đọc riêng và API/giao diện cho sáu module Cài đặt · Danh mục · Kho · Bán hàng ·
Báo cáo · Trợ lý AI. Có script sinh dữ liệu 12 tháng (`make seed`), bộ **95 câu hỏi**
(`data/eval/questions.jsonl`) và harness A/B/C (`data/eval/harness.py`). Điều này không đồng nghĩa
mọi yêu cầu trong bản báo cáo cập nhật đã được nghiệm thu.

**Q5/Q6 đã chốt ngày 26/09/2026**: DeepSeek, mô hình chính `deepseek-flash`, cấu hình C
`deepseek-v4-pro`. Kết quả lần chạy đã lưu ở [`docs/eval-results.json`](docs/eval-results.json):
độ đúng thực thi A/B/C lần lượt **56,84% / 66,32% / 57,89%**. Đây là kết quả đã lưu trên bộ 95 câu,
không phải kết quả cho kế hoạch đánh giá mới gồm 80 câu trong báo cáo.

Thanh toán QR thật dùng SePay: xem [hướng dẫn cấu hình](docs/payment-sepay-setup.md) và script
kiểm thử chuyển tiền thật `scripts/sepay_smoke.py`. Chạy AI hoặc thực nghiệm mới cần cấu hình `AI_PROVIDER`, `LLM_MODEL`, `AI_API_KEY` và các URL
CSDL chỉ-đọc; unit test dùng client giả, không cần khóa API. QR có adapter giả lập mặc định và
adapter SePay tùy cấu hình (`PAYMENT_GATEWAY`). Unit test không đọc cấu hình/khóa local.

Kết quả mới nhất: [xử lý review source–docs ngày 21/10/2026](docs/testing/source-review-fixes-2026-10-21.md)
(15 phát hiện P1) và [đợt chỉnh trợ lý AI](docs/testing/technical-debt-2026-10-21.md),
gồm gợi ý câu hỏi khớp phạm vi view, prompt rõ nhánh dữ liệu và giữ dữ liệu khi diễn giải chậm.
Trước đó: [đợt bổ sung thanh toán ngày 20/10/2026](docs/testing/technical-debt-2026-10-20.md),
gồm danh sách ngoại lệ thanh toán (FR-SALE-16/17), báo cáo thanh toán chờ và đóng chưa thu trên giao diện,
cùng các lỗi trạng thái QR sau khi quản lý xử lý. Kết quả trước đó:
[đợt sửa nợ kỹ thuật ngày 18/10/2026](docs/testing/technical-debt-2026-10-18.md),
[đợt trả sáu khoản nợ kỹ thuật ngày 17/10/2026](docs/testing/technical-debt-2026-10-17.md),
gồm giải phóng bàn, mốc tháng 06:00, CI MySQL, seed có kiểm chứng và cache/hạn mức AI lưu MySQL.
Nhật ký [kiểm chứng trước sửa](docs/testing/results-2026-10-17.md) được giữ riêng để truy vết.
**SUS/UAT với người dùng thật và kiểm tra tablet thật/Safari/Edge vẫn chờ thực hiện**; mẫu phiếu
và kịch bản nằm trong [`docs/testing/`](docs/testing/README.md).

Kế hoạch triển khai đầy đủ nằm ở [`docs/plans/2026-09-24-master-roadmap.md`](docs/plans/2026-09-24-master-roadmap.md):
**tám phase** từ lược đồ CSDL tới dữ liệu đánh giá, kèm thứ tự phụ thuộc và các cổng cần duyệt. Kế hoạch
chi tiết từng phase ở `docs/plans/phases/`. Nhật ký dựng khung ban đầu:
`docs/plans/2026-09-21-project-skeleton.md`.

Đặc tả đầy đủ: [`docs/BaoCao_HeThongQuanLyNhaHang.md`](docs/BaoCao_HeThongQuanLyNhaHang.md).
