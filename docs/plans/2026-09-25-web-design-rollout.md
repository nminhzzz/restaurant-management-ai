# Áp design system vào `apps/web`

Ngày: 2026-09-25 · Nhánh: `feat/web-design-system`

**Mục tiêu:** mọi màn hình trong `apps/web` dùng token và component theo `docs/design/tokens.md`,
trông như trang mẫu `docs/design/preview.html`. Không đổi API, không đổi route.

**Tiêu chí xong:** không còn class màu Tailwind gắn cứng trong `src/features` và `src/app`; không màn hình
nào hiển thị mã FR, tên người phụ trách hay chữ "chưa triển khai"; `pnpm lint`, `typecheck`, `test`,
`build` xanh.

## Việc

1. **Nền:** font Be Vietnam Pro + JetBrains Mono qua `@fontsource` (build vẫn chạy offline); token biểu
   đồ `chart-1..6`; helper `lib/format.ts` (tiền, số, ngày), `lib/roles.ts` (nhãn vai trò tiếng Việt),
   `lib/status.ts` (trạng thái CSDL → tone badge).
2. **Component cấp trang:** `PageHeader`, `EmptyState`, `LoadingState` (skeleton, có chữ "Đang tải…" cho
   trình đọc màn hình), `ErrorState` (nút Thử lại), `StatCard`.
3. **Khung:** sidebar có icon (icon khai báo trong `lib/modules.ts`), vai trò tiếng Việt, bỏ trường
   `requirements`/`owner`/`summary` khỏi registry; `/` chuyển thẳng tới module đầu tiên của vai trò hoặc
   `/login`; màn đăng nhập dạng card; xóa `ModulePlaceholder`.
4. **Bán hàng:** POS (chọn loại đơn, chip bàn, tab nhóm món, lưới món, giỏ hàng có bước tăng giảm và ghi
   chú); tab Thanh toán gồm tra cứu + panel thanh toán hiện tên món thay vì mã. Sửa lỗi chỉ tải 20 món
   đầu (`size=200`).
5. **Danh mục:** bảng món có nhóm, giá, badge trạng thái, ô tìm kiếm.
6. **Kho:** bảng tồn kho có tab lọc Sắp hết / Hết hàng, badge trạng thái.
7. **Báo cáo:** thẻ số liệu, biểu đồ cột có trục, bảng chi tiết, món bán chạy.
8. **Trợ lý AI:** banner phạm vi theo vai trò, câu hỏi gợi ý, kết quả dạng card.
9. **Cài đặt:** hai tab chỉ đọc, Tài khoản và Nhật ký thao tác (API đã có).

## Test phải đổi và lý do

- `module-placeholder.test.tsx`: xóa cùng component (tokens.md §8 cấm hiển thị mã FR / người phụ trách).
- `stock-table.test.tsx`: bỏ khẳng định class `bg-red-100` (chi tiết cài đặt); thay bằng khẳng định badge
  "Sắp hết" trên đúng dòng.
- `payment-panel.test.tsx` (OrderScreen): chọn bàn bằng chip (radio "Bàn 7") thay cho `<select>`.

## Ngoài phạm vi

Form tạo/sửa món, phiếu nhập, kiểm kê, tạo tài khoản: API có nhưng giao diện là tính năng mới, làm sau.
