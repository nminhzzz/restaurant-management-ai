# Design Tokens: Hệ thống quản lý nhà hàng tích hợp AI

> Nguồn duy nhất cho màu, chữ, khoảng cách, bo góc và component dùng chung của `apps/web`.
> Đổi token thì sửa file này trước, rồi mới sửa `src/app/globals.css` và component. Không sửa rải rác.
> Trang mẫu trực quan: `docs/design/preview.html` (mở thẳng bằng trình duyệt).

## 1. Định hướng

- **Công cụ vận hành, không phải trang giới thiệu.** Người dùng là thu ngân, quản lý, thủ kho, thao tác
  hàng trăm lần mỗi ca. Ưu tiên đọc nhanh, bấm trúng, trạng thái nhìn là hiểu.
- **Nền:** shadcn/ui (Radix + Tailwind 4). Màn hình order học Square POS / KiotViet (lưới món to, giỏ hàng
  cố định bên phải). Màn hình quản trị học Linear (bảng gọn, tiêu đề trang rõ, ít khung).
- **Tablet trước (NFR-13, NFR-17):** mọi vùng chạm chính ≥ 44px.
- **Chỉ giao diện sáng** trong phạm vi đồ án. Dark mode không nằm trong MVP.

## 2. Màu

### 2.1 Vì sao màu chính là đen than (Than chì)

Trong nhà hàng, **đỏ / cam / xanh lá đã có nghĩa nghiệp vụ** (hết hàng, sắp hết, đã thanh toán), nên màu thương
hiệu phải nằm ngoài ba họ đó. Bản đầu dùng xanh chàm với nền xanh–trắng và bo tròn, nhìn giống giao diện sinh tự
động. Bản hiện tại chọn **Than chì**: màu chính là đen than, nền và viền là xám trung tính (không ngả vàng, không
ngả xanh). Cả màn hình chỉ có đen, xám và ba màu trạng thái, nên dòng "sắp hết" hay "đã hủy" nổi lên ngay.
Chữ trắng trên `primary` đạt 17.9:1.

Hai phương án đã so sánh và loại: Mận chín (`#5C1D4E`) và Cà phê (`#4A2C1D`, cùng họ với cam cảnh báo).

### 2.2 Bảng token

Tên token trùng tên lớp Tailwind: `--color-primary` → `bg-primary`, `text-primary`, `border-primary`.

| Token | Hex | Dùng cho |
| --- | --- | --- |
| `canvas` | `#EDEEF0` | Nền trang |
| `surface` | `#FFFFFF` | Card, panel, input |
| `surface-sunken` | `#F5F6F7` | Header bảng, hover dòng, skeleton, badge trung tính |
| `border` | `#DCDEE2` | Viền card, đường chia dòng |
| `border-strong` | `#878B93` | Viền control (input, select, nút phụ), đường kẻ dưới header bảng, viền nét đứt của Nháp (≥ 3:1 trên `surface`) |
| `ink` | `#15171B` | Chữ chính, tiêu đề, viền control khi hover |
| `muted` | `#4A4F57` | Mô tả, chữ phụ, header bảng |
| `subtle` | `#5F6570` | Caption, nhãn KPI, placeholder (≥ 4.5:1 trên `canvas`) |
| `primary` / `primary-hover` | `#15171B` / `#363A41` | Nút chính, focus ring, tab và trang đang chọn, badge "đang xử lý" |
| `primary-subtle` / `primary-subtle-fg` | `#E6E8EB` / `#15171B` | Dòng đang chọn trong danh sách, khung gợi ý nhẹ |
| `sidebar` · `sidebar-fg` · `sidebar-muted` | `#15171B` · `#C8CBD1` · `#8A8F98` | Nền sidebar tối, chữ mục nav, chữ phụ |
| `sidebar-border` · `sidebar-hover` | `#272A30` · `#1F2227` | Đường chia và hover trong sidebar |
| `success` · `success-subtle` · `success-fg` | `#15803D` · `#E1F0E5` · `#14532D` | Đã thanh toán, đang bán, còn hạn |
| `warning` · `warning-subtle` · `warning-fg` | `#D97706` · `#FAEBD2` · `#843A0C` | Sắp hết, chờ đối soát, tạm tính |
| `danger` · `danger-hover` · `danger-subtle` · `danger-fg` | `#C62828` · `#A51F1F` · `#F9E1DF` · `#8C1B16` | Hết nguyên liệu, đã hủy, lỗi, thao tác phá hủy |

Biểu đồ dùng thang xám `chart-1` … `chart-6` (`#15171B`, `#A9ADB4`, `#5F6570`, `#D2D5DA`, `#7C818A`, `#C0C4CA`),
xếp sao cho hai lát cạnh nhau của biểu đồ tròn không cùng độ sáng. Cột nổi bật nhất dùng `chart-1`, các cột còn lại
`chart-2`; biểu đồ tròn đi lần lượt 1 → 6. Trong SVG tham chiếu bằng `var(--color-chart-1)`.

Quy tắc:

1. **Không có màu thương hiệu mang sắc độ.** Ba màu trạng thái là màu duy nhất trên màn hình và chỉ dùng khi dữ liệu
   thật sự mang trạng thái đó.
2. **`warning` không bao giờ là nền của nút có chữ trắng** (chỉ 3.2:1). Cảnh báo luôn ở dạng
   `warning-subtle` + `warning-fg`.
3. Không còn token `info` riêng. Trạng thái "đang xử lý / đang chế biến" dùng badge `primary` (nền đen, chữ trắng)
   để không lẫn với badge `neutral` màu xám.
4. Không dùng màu Tailwind gắn cứng (`amber-50`, `slate-700`…) trong component. Thiếu màu thì thêm token vào đây.

### 2.3 Ánh xạ trạng thái nghiệp vụ → badge

| Trạng thái (giá trị trong CSDL) | Tone |
| --- | --- |
| Món `Hoạt động` · bàn `Trống` · Order `Đã thanh toán` · Lô `Còn hạn` · Giá `Hiệu lực` | `success` |
| Tồn kho sắp chạm mức tối thiểu · Order `Chờ đối soát` · Giá vốn `Tạm tính` | `warning` |
| Món `Hết nguyên liệu` · Order/dòng `Đã hủy` · Lô `Hết hạn` | `danger` |
| Order `Đang mở` · dòng `Chờ` · phiếu `Chờ in` · bàn `Đang phục vụ` · bàn `Đã đặt` | `primary` (nền đặc) |
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
| `text-[11px]` | 11 / 16 | 700, viết hoa, `tracking-wider` | Header bảng, nhãn KPI, nhãn nhóm |
| `text-xs` | 12 / 16 | 600 | Caption, badge |
| `text-sm` | 14 / 20 | 400 | Nội dung bảng, form, mô tả. **Cỡ mặc định của app** |
| `text-base` | 16 / 24 | 700 | Tiêu đề card, tiêu đề khối |
| `text-2xl` | 24 / 32 | 700, `tracking-tight` | Tiêu đề trang |
| `text-[28px]` | 28 / 36 | 700, `tracking-tight` | Số liệu trên thẻ KPI, tổng tiền |

- Mọi con số tiền, số lượng, thời gian: `tabular-nums`. Tiền định dạng `185.000 ₫` (`toLocaleString("vi-VN")`).
- Chữ hoa chỉ dùng cho nhãn ngắn: header bảng, nhãn KPI, nhãn nhóm. Badge, nút và tiêu đề viết thường.
- Font nạp các bậc 400 / 500 / 600 / 700; không dùng 800.

## 4. Bo góc, viền, bóng

Hướng thiết kế là **vuông vức nhưng không thô**: góc vát nhẹ, viền rõ, bóng chỉ cho lớp nổi.

| Token | Giá trị | Lớp | Phần tử |
| --- | --- | --- | --- |
| `radius-badge` | 3px | `rounded-badge` | Badge, ô đếm, mục bên trong nhóm tab/segmented, skeleton |
| `radius-control` | 4px | `rounded-control` | Nút, input, select, nhóm tab, mục nav, chip chọn bàn |
| `radius-container` | 6px | `rounded-container` | Card, bảng, ô món POS, panel, menu thả xuống |
| `radius-overlay` | 8px | `rounded-overlay` | Dialog, sheet |

- Không dùng `rounded-full` và các bậc Tailwind mặc định (`rounded-md`, `rounded-2xl`…). Chấm màu trong chú thích
  biểu đồ dùng `rounded-xs`.
- **Viền là mặc định, bóng là ngoại lệ.** Card và bảng chỉ có `border`. Control dùng `border-border-strong`,
  hover chuyển sang `border-ink`.
- Bóng có hai token: `shadow-float` cho lớp nổi (dropdown, select, dialog) và `shadow-lift` cho ô món POS khi hover.
- Vạch nhấn dạng `shadow-[inset_4px_0_0_0_…]` (trái) hoặc `inset_0_4px…` (trên) đánh dấu khối lỗi và thẻ đăng nhập;
  không dùng như trang trí cho card thường.
- Icon lucide dùng đầu nét vuông (`stroke-linecap: square`), khai báo một lần trong `globals.css`.
- Không lồng card trong card. Nhóm nội dung bên trong card bằng `divide-y` hoặc khoảng trắng.

## 5. Khoảng cách & bố cục

- Thang 4px của Tailwind. Khoảng dùng nhiều: `gap-2` (8) trong nhóm nút, `gap-4` (16) giữa field,
  `gap-6` (24) giữa khối trong trang.
- **Khung ứng dụng:** sidebar tối (`bg-sidebar`) `w-60` cố định từ `lg`, drawer dưới `lg`. Mục nav đang chọn
  nền trắng chữ đen. Nội dung `p-4 lg:p-6`, rộng tối đa
  `max-w-7xl` (màn POS dùng toàn bộ chiều ngang).
- **Mẫu trang chuẩn** (mọi màn hình quản trị):
  1. `PageHeader`: tiêu đề `text-2xl` đậm + mô tả một dòng bên trái, hành động chính bên phải.
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
  Chữ nút `font-semibold`; nút đang ở trang hiện tại của phân trang dùng `primary`.
- **Tabs:** nhóm tab cấp trang là khung viền `border-strong`, mục đang chọn nền `primary` chữ trắng. Tab lọc bên
  trong một khối dùng gạch chân 2px `border-primary`.
- **Form:** label đặt **trên** control, lỗi đặt **dưới** control bằng `text-danger-fg`. Không dùng placeholder
  thay label.
- **Icon:** `lucide-react`, `size-4` trong nút và nav, stroke mặc định. Nút chỉ có icon phải có `aria-label`.

## 7. Trạng thái tương tác

- Hover: dòng bảng `bg-surface-sunken`, control `border-ink`, ô món POS `border-ink shadow-lift`, nút `secondary`
  `bg-surface-sunken`.
- Focus: `focus-visible:ring-2 ring-primary ring-offset-2` cho nút; input/select đổi viền sang `primary` kèm
  `ring-1`. Trong sidebar tối dùng `ring-white`.
- Nhấn: nút và ô món POS `active:translate-y-px`.
- Disabled: `opacity-50 pointer-events-none`.
- **Loading:** `Skeleton` có hình giống nội dung thật. Không dùng chữ "Đang tải…" trơn, không spinner toàn trang.
- **Rỗng:** `EmptyState` gồm icon, một câu nói vì sao rỗng, một nút để lấp đầy (ví dụ "Tạo phiếu nhập").
- **Lỗi:** lỗi của form nằm ngay dưới field. Lỗi của thao tác đi qua toast `danger`. Lỗi tải trang nằm trong
  vùng nội dung, có nút "Thử lại".
- Toast `bottom-right`, 3 giây, bo `radius-container`, màu lấy từ token trạng thái (ghi đè biến của sonner trong
  `globals.css`), chữ tiếng Việt nói rõ đã xảy ra gì ("Đã gửi order ORD-250926-042 xuống bếp").

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
