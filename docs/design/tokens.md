# Design Tokens: Hệ thống quản lý nhà hàng tích hợp AI

> Nguồn duy nhất cho màu, chữ, khoảng cách, bo góc và component dùng chung của `apps/web`.
> Đổi token thì sửa file này trước, rồi mới sửa `src/app/globals.css` và component. Không sửa rải rác.
> Trang mẫu trực quan: artifact "Hệ thiết kế nhà hàng" (bản nguồn `docs/design/preview.html`).

## 1. Định hướng

- **Công cụ vận hành, không phải trang giới thiệu.** Người dùng là thu ngân, quản lý, thủ kho, thao tác
  hàng trăm lần mỗi ca. Ưu tiên đọc nhanh, bấm trúng, trạng thái nhìn là hiểu.
- **Nền:** shadcn/ui (Radix + Tailwind 4). Màn hình order học Square POS / KiotViet (lưới món to, giỏ hàng
  cố định bên phải). Màn hình quản trị học Linear (bảng gọn, tiêu đề trang rõ, ít khung).
- **Tablet trước (NFR-13, NFR-17):** mọi vùng chạm chính ≥ 44px.
- **Chỉ giao diện sáng** trong phạm vi đồ án. Dark mode không nằm trong MVP.

## 2. Màu

### 2.1 Vì sao màu chính là xanh chàm, không phải cam

Bản cũ dùng `amber-600` làm màu chính và `amber-500` làm màu cảnh báo, gần như trùng nhau: nút "Thanh toán"
và dòng "Sắp hết nguyên liệu" cùng một màu. Trong nhà hàng, **đỏ / cam / xanh lá đã có nghĩa nghiệp vụ**
(hết hàng, sắp hết, đã thanh toán), nên màu thương hiệu phải nằm ngoài ba họ đó. Xanh chàm (`primary`)
không đụng trạng thái nào và đủ tương phản cho chữ trắng (6.8:1).

### 2.2 Bảng token

Tên token trùng tên lớp Tailwind: `--color-primary` → `bg-primary`, `text-primary`, `border-primary`.

| Token | Hex | Dùng cho |
| --- | --- | --- |
| `canvas` | `#F5F7FA` | Nền trang |
| `surface` | `#FFFFFF` | Card, panel, sidebar, input |
| `surface-sunken` | `#EEF1F5` | Header bảng, hover, skeleton, badge trung tính |
| `border` | `#DDE3EA` | Viền mặc định, đường chia dòng |
| `border-strong` | `#C5CDD8` | Viền khi hover, viền nét đứt của trạng thái Nháp |
| `ink` | `#0F172A` | Chữ chính, tiêu đề |
| `muted` | `#475569` | Mô tả, chữ phụ |
| `subtle` | `#5B6B80` | Caption, label nhỏ, placeholder (≥ 4.5:1 trên `canvas`) |
| `primary` / `primary-hover` | `#1F4FD1` / `#1A40AB` | Nút chính, link, focus ring, mục nav đang chọn |
| `primary-subtle` / `primary-subtle-fg` | `#EAF0FD` / `#1A3E9E` | Nav active, tab active, badge "đang xử lý" |
| `success` · `success-subtle` · `success-fg` | `#15803D` · `#E8F5EC` · `#166534` | Đã thanh toán, đang bán, còn hạn |
| `warning` · `warning-subtle` · `warning-fg` | `#D97706` · `#FDF3E1` · `#92400E` | Sắp hết, chờ đối soát, tạm tính |
| `danger` · `danger-hover` · `danger-subtle` · `danger-fg` | `#DC2626` · `#B91C1C` · `#FDECEC` · `#991B1B` | Hết nguyên liệu, đã hủy, lỗi, thao tác phá hủy |

Biểu đồ dùng `chart-1` … `chart-6` (`#1F4FD1`, `#7A98E6`, `#B8C8F2`, `#0F172A`, `#5B6B80`, `#C5CDD8`):
cột nổi bật nhất dùng `chart-1`, các cột còn lại `chart-2`; biểu đồ tròn đi lần lượt 1 → 6. Trong SVG
tham chiếu bằng `var(--color-chart-1)`.

Quy tắc:

1. **Một màu nhấn mỗi màn hình: `primary`.** Ba màu trạng thái không tính là màu nhấn, chỉ dùng khi dữ liệu
   thật sự mang trạng thái đó.
2. **`warning` không bao giờ là nền của nút có chữ trắng** (chỉ 3.2:1). Cảnh báo luôn ở dạng
   `warning-subtle` + `warning-fg`.
3. Không còn token `info` riêng. Trạng thái "đang xử lý / đang chế biến" dùng `primary-subtle`.
4. Không dùng màu Tailwind gắn cứng (`amber-50`, `slate-700`…) trong component. Thiếu màu thì thêm token vào đây.

### 2.3 Ánh xạ trạng thái nghiệp vụ → badge

| Trạng thái (giá trị trong CSDL) | Tone |
| --- | --- |
| Món `Hoạt động` · bàn `Trống` · Order `Đã thanh toán` · Lô `Còn hạn` · Giá `Hiệu lực` | `success` |
| Tồn kho sắp chạm mức tối thiểu · Order `Chờ đối soát` · Giá vốn `Tạm tính` | `warning` |
| Món `Hết nguyên liệu` · Order/dòng `Đã hủy` · Lô `Hết hạn` | `danger` |
| Order `Đang mở` · dòng `Chờ` · phiếu `Chờ in` · bàn `Đang phục vụ` · bàn `Đã đặt` | `primary` |
| Món `Ẩn` · tài khoản `Đã khóa` · dòng `Đã phục vụ` | `neutral` |
| Món `Nháp` | `muted` (viền nét đứt) |

## 3. Chữ

- **Font chữ:** **Be Vietnam Pro** (thiết kế riêng cho tiếng Việt, dấu không bị đè), nạp qua
  `@fontsource/be-vietnam-pro` trong `app/layout.tsx` nên `next build` vẫn chạy offline. Khai báo ở
  `--font-sans`, mọi phần tử nhận mặc định.
- **Chữ đơn cách** (mã order `ORD-250926-042`, SQL, mã lô): `JetBrains Mono` (`@fontsource/jetbrains-mono`,
  lớp `font-mono`), rơi về `ui-monospace`.
- **Thang cỡ chữ** (chỉ dùng các bậc này):

| Bậc | Cỡ / dòng | Weight | Dùng cho |
| --- | --- | --- | --- |
| `text-xs` | 12 / 16 | 500 | Caption, header bảng, badge |
| `text-sm` | 14 / 20 | 400 | Nội dung bảng, form, mô tả. **Cỡ mặc định của app** |
| `text-base` | 16 / 24 | 500 | Tên món trên ô POS, tiêu đề card |
| `text-xl` | 20 / 28 | 600 | Tiêu đề trang |
| `text-2xl` | 24 / 32 | 600 | Số tổng tiền, số liệu trên thẻ KPI |

- Mọi con số tiền, số lượng, thời gian: `tabular-nums`. Tiền định dạng `185.000 ₫` (`toLocaleString("vi-VN")`).
- Header bảng không viết hoa toàn bộ. Chữ hoa chỉ dùng cho nhãn rất ngắn (≤ 2 từ).

## 4. Bo góc, viền, bóng

Ba token, mỗi loại phần tử một bậc, không trộn:

| Token | Giá trị | Lớp | Phần tử |
| --- | --- | --- | --- |
| `radius-control` | 8px | `rounded-control` | Nút, input, select, tab, mục nav |
| `radius-container` | 12px | `rounded-container` | Card, bảng, ô món POS, panel |
| `radius-overlay` | 16px | `rounded-overlay` | Dialog, sheet, popover lớn |
| (badge) | 9999px | `rounded-full` | Badge trạng thái, chip chọn bàn |

- **Viền là mặc định, bóng là ngoại lệ.** Card và bảng chỉ có `border`. Bóng chỉ cho lớp nổi
  (dropdown, dialog, toast): `shadow-md shadow-ink/10`.
- Không lồng card trong card. Nhóm nội dung bên trong card bằng `divide-y` hoặc khoảng trắng.

## 5. Khoảng cách & bố cục

- Thang 4px của Tailwind. Khoảng dùng nhiều: `gap-2` (8) trong nhóm nút, `gap-4` (16) giữa field,
  `gap-6` (24) giữa khối trong trang.
- **Khung ứng dụng:** sidebar `w-60` cố định từ `lg`, drawer dưới `lg`. Nội dung `p-4 lg:p-6`, rộng tối đa
  `max-w-7xl` (màn POS dùng toàn bộ chiều ngang).
- **Mẫu trang chuẩn** (mọi màn hình quản trị):
  1. `PageHeader`: tiêu đề `text-xl` + mô tả một dòng bên trái, hành động chính bên phải.
  2. Thanh công cụ: tìm kiếm, bộ lọc, tab trạng thái.
  3. Nội dung: bảng / lưới / biểu đồ.
- **Màn POS:** lưới món `grid-cols-2 sm:grid-cols-3 xl:grid-cols-4`, giỏ hàng cột phải `w-96` sticky từ `lg`,
  bottom sheet dưới `lg`.

## 6. Component dùng chung

Có sẵn ở `src/components/ui/`, không tự viết lại bằng thẻ HTML thô:
`Button`, `Input`, `Textarea`, `Label`, `Select`, `Dialog`, `DropdownMenu`, `Tabs`, `Badge`, `Table`, `Card`,
`Skeleton`, toast (`sonner`).

Mẫu cấp trang ở `src/components/page-states.tsx`: `PageHeader`, `EmptyState`, `LoadingState` (skeleton có
chữ "Đang tải…" cho trình đọc màn hình), `ErrorState` (có nút Thử lại), `StatCard`, `StatusBadge` (tự chọn tone
theo §2.3 qua `lib/status.ts`). Tải dữ liệu qua hook `lib/use-resource.ts`; định dạng tiền, số, ngày qua
`lib/format.ts`; nhãn vai trò qua `lib/roles.ts`.

- **Button:** `primary` (hành động chính, tối đa 1 nút mỗi vùng), `secondary` (Hủy, Quay lại, hành động phụ),
  `ghost` (icon, đóng), `danger` (xóa, hủy order, luôn qua bước xác nhận). Cỡ `default` h-9, `pos` h-11.
- **Form:** label đặt **trên** control, lỗi đặt **dưới** control bằng `text-danger-fg`. Không dùng placeholder
  thay label.
- **Icon:** `lucide-react`, `size-4` trong nút và nav, stroke mặc định. Nút chỉ có icon phải có `aria-label`.

## 7. Trạng thái tương tác

- Hover: dòng bảng `bg-canvas`, card `border-border-strong`, nút `secondary` `bg-surface-sunken`.
- Focus: `focus-visible:ring-2 ring-primary ring-offset-2` cho mọi phần tử bấm được.
- Nhấn: ô món POS `active:scale-[0.98]`.
- Disabled: `opacity-50 pointer-events-none`.
- **Loading:** `Skeleton` có hình giống nội dung thật. Không dùng chữ "Đang tải…" trơn, không spinner toàn trang.
- **Rỗng:** `EmptyState` gồm icon, một câu nói vì sao rỗng, một nút để lấp đầy (ví dụ "Tạo phiếu nhập").
- **Lỗi:** lỗi của form nằm ngay dưới field. Lỗi của thao tác đi qua toast `danger`. Lỗi tải trang nằm trong
  vùng nội dung, có nút "Thử lại".
- Toast `bottom-right`, 3 giây, chữ tiếng Việt nói rõ đã xảy ra gì ("Đã gửi order ORD-250926-042 xuống bếp").

## 8. Nội dung hiển thị

- Tiếng Việt toàn bộ (NFR-14). Vai trò hiển thị: `MANAGER` → **Quản lý**, `CASHIER` → **Thu ngân**,
  `WAREHOUSE` → **Thủ kho**.
- Không hiển thị mã yêu cầu (`FR-CAT-01…`), tên người phụ trách hay chữ "chưa triển khai" cho người dùng cuối.
  Thông tin đó thuộc tài liệu, không thuộc giao diện.

## 9. Khả năng tiếp cận

- Tương phản chữ ≥ 4.5:1 (đã kiểm với mọi cặp `*-fg` trên `*-subtle`, `subtle` trên `canvas`).
- Bảng có `caption` (có thể ẩn) và `scope`. Icon có `aria-label` hoặc `aria-hidden`.
- Trạng thái không chỉ truyền bằng màu: badge luôn có chữ.

## 10. Quy tắc cho mọi màn hình mới

1. Dùng component ở §6 và token ở §2. Không có class màu Tailwind gắn cứng.
2. Theo mẫu trang ở §5, có đủ loading / rỗng / lỗi ở §7.
3. Thêm module chỉ sửa `lib/modules.ts`, sidebar tự render.
4. `pnpm test` + `pnpm typecheck` + `pnpm lint` xanh.
