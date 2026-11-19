# Bàn giao dev: 4 việc sau buổi báo cáo với cô (19/11/2026)

| # | Việc | Góp ý của cô |
|---|---|---|
| 1 | Kiểm kê: danh sách lô dưới mỗi nguyên liệu | #5 |
| 2 | Phiếu xuất: hệ thống đề xuất hủy lô hết hạn, chờ duyệt | #7 |
| 3 | Tự cập nhật dữ liệu, bỏ nút "Làm mới" | #2, #8 |
| 4 | Nhập kho: bỏ đơn vị mua, nhập theo đơn vị tính của nguyên liệu | #4 |

Làm theo thứ tự trên; mỗi việc nên là một commit riêng.

Nguồn yêu cầu: buổi báo cáo với cô hướng dẫn ngày 19/11. Kiểm kê ở khoảng 23:20–25:01, phiếu xuất ở khoảng 28:37–31:37.
Tài liệu đã sửa theo yêu cầu này nằm trong repo: `docs/Tai_lieu/02–04`, `docs/BaoCao_HeThongQuanLyNhaHang.md`, `docs/So_do/` (bản Word giống hệt nằm trong zip `final-v15_19-11`):
- Tài liệu 02: mục 1.14 mới (QT-14 Duyệt phiếu đề xuất hủy lô hết hạn), mục 1.15 bước 2 (kiểm kê), quy tắc 18.
- Tài liệu 03: UC 3.3 bước 5–6, UC 3.4 bước 2, các mục FR-INV-01, FR-INV-05, FR-INV-08, FR-INV-14, FR-CAT-12.
- Tài liệu 04: các bảng thuộc tính PHIEU_XUAT_KHO, CHI_TIET_PHIEU_XUAT và phương thức; mô tả DonViMuaGoc, HeSoQuyDoi của CHI_TIET_PHIEU_NHAP.
- Sơ đồ QT-13 (lập phiếu tay) và QT-14 (duyệt phiếu đề xuất).

Code phải làm khớp với các tài liệu này.

Repo đang sạch, chưa có code nào cho bốn việc này. File `docs/ba-handoff-2026-11-19.patch` là bản làm dở của việc 1 và 2,
**chỉ để tham khảo**:
- Phần kiểm kê đã chạy, có test.
- Phần phiếu xuất chưa xong: `IssueReject` chưa được khai báo và chưa có giao diện.

Nếu áp dụng patch thì chạy `git apply --check docs/ba-handoff-2026-11-19.patch` trước.

---

## Việc 1. Kiểm kê: danh sách lô dưới mỗi nguyên liệu

Màn hình: tab **Kho → Kiểm kê**, sau khi bấm "Tạo phiếu kiểm kê", trong file `apps/web/src/features/inventory/stocktake-panel.tsx`, component `DraftStocktake`.

### Lỗi hiện tại
- Code gọi `/inventory/lots?page_size=100`, nên hiện cả các lô **Đã dùng hết** và **Đã hủy**. Cô không biết số tồn thuộc lô nào.
- Chỉ lấy 100 lô đầu của cả kho. Kho có nhiều lô thì nguyên liệu phía sau bị thiếu lô.
- Mỗi dòng hiện thừa thông tin (trạng thái lô), và HSD đang hiện kiểu `2026-11-21`.

### Yêu cầu
1. **Lô được liệt kê** là các lô còn số lượng (`SoLuongConLai > 0`) và chưa hủy (`TrangThai <> 'Đã hủy'`). Lô hết hạn vẫn được liệt kê, kể cả lô đang nằm trong phiếu đề xuất hủy chờ duyệt, vì lô đó chưa bị trừ tồn.
2. **Thứ tự**: nhập trước xếp trên, nhập sau xếp dưới, tức `NgayNhap` rồi `MaLoNguyenLieu`, đúng thứ tự FIFO.
3. **Mỗi dòng chỉ có 3 thông tin**: mã lô, lượng còn lại kèm đơn vị, HSD theo dạng **ngày/tháng/năm**. Ví dụ:
   `Lô #12 · 4,5 kg · HSD 21/11/2026`. Lô không có HSD thì bỏ phần HSD: `Lô #20 · 3 kg`. Không hiện trạng thái lô.
4. **Phải khớp**: tổng lượng các lô dưới một nguyên liệu bằng cột **Tồn hệ thống** (`SoLuongTon`) của nguyên liệu đó.
5. Tải **đủ mọi trang** lô, không bị cắt ở 100.

### Gợi ý triển khai
- **API** `GET /inventory/lots` (`router.py`, `queries.list_lots`): thêm tham số `in_stock: bool = False`. Khi `true`, lọc
  `remaining > 0` và `IngredientLot.status != 'Đã hủy'`. Thứ tự sắp xếp đã là `received_at, id`.
- **Web**: gọi `/inventory/lots?in_stock=true&page=N&page_size=100` theo vòng lặp tới khi đủ `total`. Định dạng HSD bằng
  hàm format ngày có sẵn trong `@/lib/format`; nếu chưa có hàm `dd/MM/yyyy` thì thêm vào đó.

### Tiêu chí nghiệm thu và test
- [ ] **pytest**: nhập 3 phiếu (5, 5, 3), hủy phiếu thứ 3, xuất 5. Khi đó `?in_stock=true` trả đúng 1 lô, và tổng các lô bằng `stock_qty` (= 5).
- [ ] **vitest**: giao diện gọi API với `in_stock=true`, tải cả trang 2, mỗi dòng hiện đúng định dạng `Lô #… · … · HSD dd/mm/yyyy`.

---

## Việc 2. Phiếu xuất: hệ thống đề xuất hủy lô hết hạn, chờ duyệt

Màn hình: tab **Kho → Phiếu xuất**, gồm `issue-list.tsx` và `issue-detail-dialog.tsx`.
Backend: `apps/api/src/app/modules/inventory/` (`service.py`, `router.py`, `models.py`, `lot_status.py`).

### Hiện trạng
Mọi phiếu xuất đều do người dùng lập và trừ kho ngay, ở trạng thái `Đã xác nhận`. Hệ thống chưa tự sinh phiếu nào.

### Yêu cầu nghiệp vụ (đã chốt)
1. **Hệ thống tự lập phiếu đề xuất**. Sau mốc bắt đầu Business Date (mặc định 06:00), hệ thống lập **một** phiếu cho mọi lô:
   - hết hạn: `HanSuDung < Business Date hôm nay`;
   - còn số lượng, chưa hủy;
   - chưa nằm trong phiếu nào đang **Chờ duyệt**, cũng chưa nằm trong phiếu nào **Đã từ chối**.

   Phiếu có các giá trị: `LyDo = 'Hết hạn'`, `NguonXuat = 'Nguyên liệu'`, `TrangThai = 'Chờ duyệt'`, `NguoiLap = NULL`, `NgayXuat = NULL`,
   `GhiChu = 'Hệ thống đề xuất hủy các lô đã quá hạn sử dụng.'`. Mỗi dòng ghi `MaNguyenLieu`, `MaLoNguyenLieu`, `SoLuong` = lượng còn lại của lô.
   **Phiếu này chưa trừ kho.** Nếu đang có phiên kiểm kê mở thì không đề xuất.
2. **Người duyệt là Bếp (WAREHOUSE) hoặc Quản lý (MANAGER)**, không giới hạn riêng Quản lý. Phiếu ghi lại người duyệt và thời điểm duyệt.
3. **Duyệt**:
   - Mỗi dòng trừ **đúng lô** ghi trên dòng (`allow_expired=True`, `lot_ids=[lô]`), lượng trừ = min(lượng trên dòng, lượng lô còn lại).
   - Lô đã hết hàng hoặc đã hủy thì bỏ dòng đó. Nếu không còn dòng nào thì báo lỗi, gợi ý người dùng từ chối phiếu.
   - Ghi `GiaVonUocTinh` theo đơn giá bình quân tại lúc duyệt.
   - Phiếu chuyển `Đã xác nhận`, `NguoiDuyet` = người bấm, `NgayDuyet` = `NgayXuat` = thời điểm duyệt. Ghi audit log.
   - Không cho duyệt khi đang có phiên kiểm kê mở.
4. **Từ chối**: phiếu chuyển `Đã từ chối`, ghi `NguoiDuyet` và `NgayDuyet`, có thể kèm lý do (ghi nối vào `GhiChu`). Kho không đổi. Lô trong phiếu bị từ chối **không được đề xuất lại**.
5. **Phiếu do người dùng lập giữ nguyên như hiện tại**: xem trước, xác nhận, trừ kho ngay, trạng thái `Đã xác nhận`. Nếu kiểm tra thực tế thấy còn hàng hỏng chưa có trong phiếu đề xuất thì người dùng lập thêm phiếu thủ công.
6. Phiếu ở trạng thái `Chờ duyệt` hoặc `Đã từ chối` **không được tính** vào hao hụt kho (FR-REP-12).

### Thay đổi CSDL (migration mới, nối sau head `d13112600001`)
| Bảng | Cột | Kiểu | Ghi chú |
|---|---|---|---|
| PHIEU_XUAT_KHO | NguoiDuyet | BIGINT NULL | FK → NGUOI_DUNG.MaNguoiDung, RESTRICT |
| PHIEU_XUAT_KHO | NgayDuyet | DATETIME(3) NULL | |
| CHI_TIET_PHIEU_XUAT | MaLoNguyenLieu | BIGINT NULL | FK → LO_NGUYEN_LIEU.MaLoNguyenLieu, RESTRICT |

- `TrangThai` nhận 3 giá trị `Chờ duyệt / Đã xác nhận / Đã từ chối`. Tài liệu 04 bản cũ ghi cột này có CHECK chỉ nhận `Đã xác nhận`. **Cần kiểm tra trên MySQL** xem có CHECK đó thật không (trong model hiện không có). Nếu có thì migration phải nới CHECK ra.
- Nhớ cập nhật `tests/schema/*` nếu có test so cột.

### API
| Method | Đường dẫn | Quyền | Việc |
|---|---|---|---|
| POST | `/inventory/issues/propose-expired` | MANAGER, WAREHOUSE | Chạy đề xuất ngay; trả `MaPhieuXuat` hoặc `null` (dùng khi demo) |
| POST | `/inventory/issues/{id}/approve` | MANAGER, WAREHOUSE | Duyệt phiếu `Chờ duyệt` |
| POST | `/inventory/issues/{id}/reject` | MANAGER, WAREHOUSE | Từ chối, body `{ "note": "..." }` tùy chọn |
| GET | `/inventory/issues?status=Chờ duyệt` | như cũ | Thêm bộ lọc `status`; mỗi dòng trả thêm `NguoiDuyet`, `NgayDuyet` |
| GET | `/inventory/issues/{id}` | như cũ | Trả thêm `NguoiDuyet`, `TenNguoiDuyet`, `NgayDuyet`. Với dòng chưa có giao dịch kho, `MaLoNguyenLieu` lấy từ cột mới của dòng |

- Phân quyền kiểm tra ở API (`require_roles`), không chỉ ẩn nút trên giao diện.
- Duyệt hoặc từ chối một phiếu không ở trạng thái `Chờ duyệt` → lỗi nghiệp vụ "Chỉ duyệt hoặc từ chối phiếu đang chờ duyệt.". Khóa dòng phiếu bằng `with_for_update` để hai người không duyệt trùng.

### Lịch chạy
Gọi hàm đề xuất sau `refresh_all_lot_statuses` trong `lot_status_tick` (`lot_status.py`; vòng lặp đã có ở `main.py`, mặc định chạy mỗi 3600 giây). Bọc riêng trong try/except để lỗi đề xuất không làm hỏng việc cập nhật trạng thái lô. Hàm phải chạy lại được nhiều lần mà không đề xuất trùng lô.

### Những chỗ khác phải sửa theo
- `reports/queries.py` → `waste_cost`: thêm điều kiện `StockIssue.status == 'Đã xác nhận'`.
- `costing.py` (định giá lại dòng có `estimated_cost` NULL): dòng chờ duyệt cũng có giá vốn NULL; khi duyệt sẽ tính lại. Cân nhắc lọc bỏ phiếu chưa xác nhận ở đây.
- **View AI** `vw_ai_kho_xuat`, `vw_ai_quanly_xuat` đã có cột `TrangThai` nên **không bắt buộc sửa**. Nếu muốn view chỉ lấy phiếu đã xác nhận thì phải làm migration view và chạy lại bộ đánh giá AI. **Hỏi Khánh trước**, vì số liệu đánh giá trong báo cáo đã chốt.

### Giao diện
- `lib/status.ts`: thêm màu cho `Chờ duyệt` (warning) và `Đã từ chối` (danger hoặc muted).
- **Danh sách phiếu xuất**:
  - thêm bộ lọc Trạng thái;
  - phiếu `Chờ duyệt` hiển thị nổi bật;
  - thêm nút **"Kiểm tra lô hết hạn"** gọi `propose-expired`, để demo không phải chờ lịch chạy;
  - cột Thao tác của phiếu chờ duyệt có **Duyệt** / **Từ chối**, hoặc đặt hai nút này trong hộp chi tiết.
- **Chi tiết phiếu**:
  - hiện người lập ("Hệ thống" nếu `NguoiLap` NULL), người duyệt, ngày duyệt;
  - mỗi dòng có lô kèm HSD;
  - nút Duyệt có hộp xác nhận; Từ chối cho nhập lý do;
  - duyệt hoặc từ chối xong thì tải lại danh sách.

### Tiêu chí nghiệm thu và test (pytest)
- [ ] Lô hết hạn còn hàng → đề xuất tạo 1 phiếu `Chờ duyệt`, `NguoiLap` NULL, kho **không đổi**.
- [ ] Gọi đề xuất lần hai → không tạo phiếu mới cho cùng lô.
- [ ] Bếp duyệt → kho giảm đúng lô, phiếu `Đã xác nhận`, `NguoiDuyet` = id của Bếp, có giao dịch kho `Xuất thủ công` gắn dòng xuất.
- [ ] Quản lý duyệt cũng được; Thu ngân gọi approve/reject → 403.
- [ ] Từ chối → kho không đổi, phiếu `Đã từ chối`; gọi đề xuất lại → lô đó không bị đề xuất lại.
- [ ] Duyệt phiếu đã duyệt hoặc đã từ chối → lỗi nghiệp vụ.
- [ ] Đang có phiên kiểm kê mở → không đề xuất, không duyệt được.
- [ ] Lô bị dùng bớt sau khi đề xuất → khi duyệt chỉ trừ phần còn lại.
- [ ] Hao hụt kho (FR-REP-12) không tính phiếu `Chờ duyệt` và `Đã từ chối`.
- [ ] Phiếu lập tay vẫn hoạt động như cũ: toàn bộ test hiện có của `test_inventory_issues.py` vẫn xanh.
- [ ] Migration chạy upgrade và downgrade được trên MySQL 8.4.

---

## Việc 3. Tự cập nhật dữ liệu, bỏ nút "Làm mới" (góp ý #2 và #8)

Cô góp ý (05:47–07:30 và 32:17–32:49): lượng khả dụng không tự cập nhật, phải bấm "Làm mới" mới thấy. Nhóm đã hứa sẽ tự cập nhật sau vài giây.

### Yêu cầu
1. **Tự tải lại mỗi 5 giây** (trong khoảng 3–5 giây nhóm đã hứa; màn order đã dùng 5 giây), **chỉ khi tab trình duyệt đang hiển thị**
   (`document.visibilityState === "visible"`). Cách làm giống `features/sales/order-detail.tsx`: `window.setInterval(resource.refresh, 5000)`.
   Hàm `refresh()` của `useResource` tải ngầm, không hiện lại khung đang tải.
   - `features/inventory/stock-table.tsx`: tab **Tồn kho** (tồn, đang giữ, khả dụng).
   - `features/sales/order-step.tsx`: thực đơn khi chọn món, gồm "Còn N suất" (`menu`).
2. **Tự tải khi vào tab**. Các tab trong `inventory-workspace.tsx` không dùng `forceMount`, nên mỗi lần chọn tab là tải mới.
   Dev kiểm tra lại cho chắc; tab nào giữ dữ liệu cũ thì gọi `reload()` khi tab được chọn.
3. **Bỏ nút "Làm mới"** ở `stock-table.tsx` (dòng "Dữ liệu lúc … Làm mới") và `inventory-history.tsx` (tab Lô và biến động).
   Giữ dòng chữ **"Dữ liệu lúc hh:mm:ss"** để người xem biết số liệu mới tới đâu.
4. Đang gõ hoặc đang mở hộp thoại (tạo phiếu, kiểm kê) thì không được làm mất dữ liệu đang nhập. Chỉ tải lại danh sách, không đụng tới form.

### Tiêu chí nghiệm thu
- [ ] Mở tab Tồn kho trên máy A, máy B chọn món giữ nguyên liệu → trong vòng 5 giây, lượng khả dụng trên máy A tự giảm; hủy lượt chọn thì tự tăng lại.
- [ ] Không còn nút "Làm mới" ở Tồn kho và ở Lô và biến động; chuyển tab qua lại thì số liệu là số mới.
- [ ] Tab trình duyệt bị ẩn thì không gọi API định kỳ (vitest dùng fake timers và `visibilitychange`).
- [ ] vitest: sau 5 giây có gọi lại API; khi đóng component thì hủy timer.

---

## Việc 4. Nhập kho: bỏ đơn vị mua, nhập theo đơn vị tính của nguyên liệu (góp ý #4)

Cô góp ý (17:55–18:20): đơn vị khi nhập kho phải rõ, ví dụ thịt bò thăn mua theo thùng.
Đã chốt: **bỏ ô "Đơn vị mua" và ô "Hệ số quy đổi"** trên form nhập kho. Hàng mua theo thùng, hộp, bao được nhập theo khối lượng tịnh
hoặc số đơn vị ghi trên bao bì (tài liệu 03, FR-INV-01).

### Yêu cầu, form nhập kho (`features/inventory/receipt-form.tsx`)
1. Ô chọn nguyên liệu chỉ hiện tên, **bỏ "(kg)"** sau tên.
2. Bỏ hai ô "Đơn vị mua" và "Hệ số quy đổi". Payload không gửi `purchase_unit`, và gửi `conversion_factor` = 1 hoặc bỏ hẳn (API đã mặc định 1).
3. Nhãn ô số lượng ghi theo đơn vị tính của nguyên liệu đã chọn: **"Số lượng (kg)"**, "Số lượng (lon)"…
4. Cho nhập **Đơn giá** hoặc **Thành tiền** của dòng (ví dụ hai ô liên động: sửa ô này thì tính lại ô kia).
   Nhập thành tiền thì đơn giá = thành tiền / số lượng, làm tròn theo quy tắc tiền hiện có. API vẫn nhận `unit_price`.
   Ghi nhãn rõ "Đơn giá (đ/kg)".
5. Nên làm cùng ở form sửa phiếu nhập (`receipt-edit-dialog.tsx`), nếu form đó cũng có hai ô trên.

### Yêu cầu, form tạo/sửa nguyên liệu (module Danh mục)
6. Dưới ô **Đơn vị tính** thêm gợi ý: *"Chọn đơn vị dùng trong công thức: lon, hộp, quả nếu dùng nguyên đơn vị; g, kg, ml, l nếu dùng một phần."*
   (tài liệu 03, FR-CAT-12).

### Không đổi
- CSDL giữ nguyên cột `DonViMuaGoc`, `HeSoQuyDoi`, **không cần migration**. Phiếu mới có `DonViMuaGoc` = NULL, `HeSoQuyDoi` = 1 (tài liệu 04).
- Logic API (`service.py`, `qty_std = qty * factor`) giữ nguyên. Dữ liệu cũ có hệ số khác 1 vẫn đúng.

### Tiêu chí nghiệm thu
- [ ] Form nhập kho không còn ô Đơn vị mua và ô Hệ số; tên nguyên liệu không kèm "(kg)"; nhãn số lượng đổi theo nguyên liệu được chọn.
- [ ] Nhập Số lượng 20, Thành tiền 4.000.000 → gửi `unit_price` = 200000, kho cộng 20.
- [ ] Form nguyên liệu có dòng gợi ý dưới ô Đơn vị tính.
- [ ] Cập nhật `receipt-form.test.tsx` theo form mới; test API hiện có vẫn xanh.

---

## Kết thúc
- `make gate` phải xanh. Nếu máy đủ tài nguyên thì chạy thêm `make gate-integration` cho phần migration.
- Seed demo: nên có sẵn 1–2 lô hết hạn còn hàng, để lúc demo bấm "Kiểm tra lô hết hạn" là ra phiếu chờ duyệt.
- Class Diagram và sơ đồ CSDL đã có 3 cột mới; nếu đổi tên hoặc thêm cột khác thì báo Khánh để sửa sơ đồ.
