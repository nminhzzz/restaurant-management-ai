# apps/web — Giao diện web

Frontend của hệ thống quản lý nhà hàng tích hợp AI: Next.js 16 (App Router), React 19, TypeScript,
Tailwind 4, Radix UI, Vitest. Toàn bộ chuỗi hiển thị cho người dùng bằng tiếng Việt. Quy ước chung nằm ở
`AGENTS.md` gốc repository; `apps/web/AGENTS.md` do `next dev` sinh và ghi lại, không sửa tay.

## Cấu trúc

| Đường dẫn                | Nội dung                                                                                                                                      |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/app/`               | Route: `/login` và nhóm `(app)/<module>` (`catalog`, `sales`, `inventory`, `reports`, `settings`, `assistant`)                                |
| `src/components/`        | Khung ứng dụng (`app-shell`), hộp thoại xác nhận, phân trang, trạng thái trang, ô nhập; `ui/` là các thành phần Radix/shadcn dùng chung       |
| `src/features/<module>/` | Màn hình và logic giao diện theo module (có test `*.test.tsx` đặt cạnh)                                                                       |
| `src/lib/`               | `api-client` (gọi API, gắn token), `session`, `roles`, `status` (màu theo trạng thái), `format`, `modules.ts` (nguồn duy nhất mô tả 6 module) |
| `src/types/`             | Kiểu dùng chung                                                                                                                               |

Thiết kế giao diện (màu, cỡ chữ, khoảng cách, trạng thái) ghi ở `docs/design/tokens.md`. Quyền thật được kiểm tra
ở API; ẩn nút theo vai trò trên giao diện chỉ là gợi ý trải nghiệm.

## Chạy

Cần API đang chạy (`make api`, cổng 8000). Biến môi trường (đều tùy chọn):

| Biến                       | Mặc định                |
| -------------------------- | ----------------------- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` |
| `NEXT_PUBLIC_API_PREFIX`   | `/api/v1`               |

```bash
pnpm dev            # http://localhost:3000
pnpm test           # vitest run
pnpm lint           # eslint
pnpm typecheck      # tsc --noEmit
pnpm format:check   # prettier --check (pnpm format để tự sửa)
pnpm build          # production build
```

Từ thư mục gốc: `make web`, `make test-web`, `make gate`.

## Lưu ý

- `next-env.d.ts` bị gitignore; `pnpm typecheck` trên bản clone mới vẫn phải xanh, nên không dùng
  `LayoutProps`/`PageProps` do Next sinh tự động.
- Thêm module mới thì sửa `src/lib/modules.ts`, đừng chép tay vào từng trang.
