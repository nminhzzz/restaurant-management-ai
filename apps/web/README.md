# apps/web — Giao diện quản lý nhà hàng

Next.js 16 (App Router), React 19, TypeScript và Tailwind 4. Sáu module dùng chung registry
`src/lib/modules.ts`; giao diện và thông báo hiển thị bằng tiếng Việt.

## Chạy và kiểm tra

```bash
pnpm install
pnpm dev          # http://localhost:3000
pnpm test         # Vitest + Testing Library
pnpm lint
pnpm typecheck
pnpm build
```

Backend mặc định là `http://localhost:8000/api/v1`. Đặt `NEXT_PUBLIC_API_BASE_URL` và
`NEXT_PUBLIC_API_PREFIX` trước khi chạy/build nếu dùng địa chỉ khác; CORS của API phải cho phép
origin giao diện đó. Đăng nhập bằng tài khoản do quản lý cấp hoặc tài khoản mô phỏng của seed.

## Cấu trúc

| Đường dẫn         | Nội dung                                                 |
| ----------------- | -------------------------------------------------------- |
| `src/app/`        | Đăng nhập và route sáu module                            |
| `src/features/`   | Màn hình, biểu mẫu và xử lý tương tác theo module        |
| `src/components/` | Khung ứng dụng, điều khiển và trạng thái dùng chung      |
| `src/lib/`        | API client, phiên đăng nhập, cấu hình và registry module |

Font Be Vietnam Pro và JetBrains Mono được phục vụ từ `@fontsource`, build không cần tải font.
Thiết bị cảm ứng có vùng chạm tối thiểu 44px cho nút, tab và ô nhập văn bản/số.
Phân quyền thực sự được kiểm tra ở API.

Ở sơ đồ bàn, thanh toán và giải phóng bàn là hai thao tác riêng. Khi khách rời, chọn bàn đang
phục vụ và bấm “Giải phóng bàn”; bộ lọc, nhãn bàn và order đang phục vụ lấy cùng trạng thái từ API.
Thao tác cũ bị từ chối nếu bàn đã chuyển sang lượt khách khác.

Kết quả kiểm thử desktop và giả lập tablet, ảnh chụp cùng giới hạn kiểm tra trình duyệt nằm tại
[`nhật ký trả nợ kỹ thuật`](../../docs/testing/technical-debt-2026-10-17.md).
