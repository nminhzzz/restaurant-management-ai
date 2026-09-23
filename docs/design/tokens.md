# Design Tokens — Hệ thống quản lý nhà hàng tích hợp AI

> Nguồn duy nhất cho màu, chữ, khoảng cách và component dùng chung của `apps/web`.
> Các phase 1–7 bám theo file này, không tự chế palette riêng.
> Stack: Next.js 16 + Tailwind 4 + system font. Không cài webfont để build offline.

## 1. Định hướng

- **Hybrid shadcn/ui + Square/KiotViet (POS) + Linear (quản trị):** shadcn làm nền (Tailwind + Radix), màn hình order học KiotViet/Square (nút to, 1 tay thao tác), bảng/quản trị học Linear/Notion.
- **B2B nội bộ, tablet trước:** NFR-13 tablet, NFR-17 Chrome/Edge/Safari. Mọi tương tác chính phải bấm được bằng ngón tay (>= 44px).
- **Tiếng Việt, trung tính ấm:** giữ `slate` làm nền, thêm 1 accent ấm cho nhà hàng, không rebrand sặc sỡ.

## 2. Màu

### Nền & chữ
| Token | Giá trị Tailwind | Dùng cho |
|-------|------------------|----------|
| `bg` | `bg-slate-50` | Nền trang |
| `surface` | `bg-white` | Card, panel, sidebar |
| `border` | `border-slate-200` | Viền card, bảng |
| `border-hover` | `border-slate-300` | Hover card |
| `text` | `text-slate-900` | Tiêu đề, nội dung chính |
| `muted` | `text-slate-600` | Mô tả, placeholder |
| `subtle` | `text-slate-500` | Label uppercase, caption |

### Accent
| Token | Tailwind | Dùng cho |
|-------|----------|----------|
| `primary` | `bg-amber-600` / `hover:bg-amber-700` / `text-white` | Nút chính, CTA thanh toán, link active |
| `primary-subtle` | `bg-amber-50` `text-amber-800` | Badge, highlight nhẹ |
| `success` | `bg-emerald-600` / `text-emerald-700` `bg-emerald-50` | Còn hạn, đã thanh toán, hiệu lực |
| `warning` | `bg-amber-500` / `text-amber-700` `bg-amber-50` | Sắp hết, cảnh báo tồn tối thiểu |
| `danger` | `bg-red-600` / `text-red-700` `bg-red-50` | Hết nguyên liệu, đã hủy, lỗi |
| `info` | `bg-sky-600` / `bg-sky-50` | Thông tin, đang chế biến |

> Không dùng quá 1 accent trên 1 màn hình. Bảng/biểu đồ dùng `slate` + 1 trong 4 semantic trên.

### Trạng thái món/kho (ánh xạ §3.3)
- `Hoạt động` / `Còn hạn` / `Hiệu lực` → `success`
- `Hết nguyên liệu` / `Hết hạn` → `danger`
- `Ẩn` / `Đã khóa` → `muted` + `line-through` nhẹ
- `Nháp` → `muted` `border-dashed`

## 3. Chữ

- **Font:** system stack hiện có (`system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial`) — đủ hiển thị dấu tiếng Việt, không cài thêm.
- **Scale:**
  - `text-xs` (12px) — label uppercase `tracking-wide font-medium` cho `requirements`, caption bảng.
  - `text-sm` (14px) — mô tả, nội dung bảng, form.
  - `text-base` (16px) — nội dung chính, giá tiền.
  - `text-xl` / `text-2xl` — tiêu đề section.
  - `text-3xl` — tiêu đề trang chủ.
- **Weight:** `font-medium` cho label, `font-semibold` cho tiêu đề. Không dùng `font-bold` tràn lan.
- **Line-height:** mặc định Tailwind. Giá tiền dùng `tabular-nums`.

## 4. Khoảng cách & bố cục

- **Spacing:** 4px scale của Tailwind (`p-2, p-4, gap-3, gap-6, p-8` đã dùng trong repo).
- **Layout:**
  - Sidebar: `w-64` desktop, `w-[72px]` icon-only hoặc drawer trên < 768px.
  - Main: `max-w-3xl` cho trang rỗng, `max-w-6xl` cho bảng/báo cáo.
  - Card/panel: `rounded-lg border bg-white p-4`, `rounded-xl` cho modal.
  - Bảng: `overflow-x-auto`, header `bg-slate-50 text-xs uppercase`, row `hover:bg-slate-50`.
- **Grid món (POS):** `grid-cols-2 sm:grid-cols-3 lg:grid-cols-4` — mỗi ô là nút `min-h-24 p-3 rounded-xl`, chữ tên món `line-clamp-2`.

## 5. Bo góc, bóng, viền

- `rounded-md` — nút nhỏ, input.
- `rounded-lg` — card, ô món.
- `rounded-xl` — modal, sheet.
- `shadow-sm` — card nổi nhẹ; `shadow-md` — dropdown/modal. Không dùng shadow màu.

## 6. Component dùng chung (shadcn/ui)

Dùng các primitive sau, không tự viết lại:
`Button`, `Input`, `Select`, `Dialog`/`Sheet`, `Badge`, `Table`, `Card`, `Tabs`, `DropdownMenu`, `Toast`.

- **Button:**
  - `primary` (`bg-amber-600 text-white hover:bg-amber-700`) — hành động chính (Thanh toán, Lưu).
  - `secondary` (`bg-white border border-slate-200 hover:bg-slate-50`) — Hủy, Quay lại.
  - `ghost` (`hover:bg-slate-100`) — icon, đóng.
  - Size: `h-9` mặc định, `h-11` cho nút POS trên tablet.
- **Badge trạng thái:** `px-2 py-0.5 rounded-full text-xs font-medium` với màu semantic ở §2.
- **Input/Select:** `h-9 rounded-md border-slate-200 focus:ring-amber-500` .
- **Empty/Placeholder:** `border-dashed bg-white text-slate-500` như `ModulePlaceholder` hiện tại.

## 7. Tương tác & trạng thái

- Hover: `hover:bg-slate-50` (row), `hover:border-slate-300` (card).
- Active: `bg-slate-100` cho nav, `ring-2 ring-amber-500` cho ô món đang chọn.
- Disabled: `opacity-50 pointer-events-none`.
- Loading: `animate-pulse` cho skeleton, không spinner toàn màn hình.
- Toast: `success`/`danger` 3s, vị trí `bottom-right`.

## 8. Đáp ứng & cảm ứng

- Breakpoints Tailwind mặc định (`sm, lg`). POS: giỏ hàng sticky phải trên desktop, bottom sheet trên tablet dọc.
- Vùng chạm POS: nút món `min-h-11`, nút số lượng `h-12 w-12`, khoảng cách giữa nút `gap-2`.
- Bàn phím số cho trường số lượng (Phase 4), không dùng stepper nhỏ.

## 9. Khả năng tiếp cận

- Tương phản chữ/nền >= 4.5:1 (đã đạt với `slate-900` trên `white`/`slate-50`).
- Mọi icon có `aria-label`, bảng có `caption`/`scope`.
- Focus ring: `focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2`.

## 10. Quy tắc cho các phase

1. Không thêm màu mới ngoài bảng §2 nếu chưa ghi vào đây.
2. Chuỗi hiển thị luôn tiếng Việt (NFR-14), key/code giữ tiếng Anh.
3. Thêm module mới chỉ sửa `lib/modules.ts` (đã quy định), sidebar tự render.
4. Màn hình mới phải có `ModulePlaceholder` khi chưa có dữ liệu, không để trang trắng.
5. Kiểm thử `pnpm test` + `pnpm typecheck` cho mọi component mới.

## 11. Tham khảo

- Quản trị/bảng: Linear, Notion
- POS/tablet: Square POS, KiotViet, Sapo
- Nền component: shadcn/ui + Tailwind 4
- Chat AI: ChatGPT/Claude sidebar

> Đổi token thì sửa file này trước, rồi mới sửa `globals.css` / component — không sửa rải rác.
