# Bàn giao dev đợt 08/11/2026

Mã nguồn gốc: `099191e` (`main`, 03/11/2026). Tài liệu căn cứ: `docs/BaoCao_HeThongQuanLyNhaHang.md`, `docs/Tai_lieu/01–06` và `docs/So_do/*.drawio` bản 08/11/2026.

File này liệt kê toàn bộ việc dev còn phải làm. Nếu code hiện tại, `docs/ba-handoff-2026-10-31.md` hoặc tài liệu cũ mâu thuẫn với file này hay với `docs/Tai_lieu` bản 08/11, làm theo file này và `docs/Tai_lieu`. Không làm thêm những gì không ghi ở đây.

Mỗi việc gồm: **Hiện trạng** (code đang làm gì), **Yêu cầu**, **Code liên quan** (điểm bắt đầu, không phải danh sách giới hạn), **Không làm** và **Hoàn thành khi**. Mã TC tra trong `docs/Tai_lieu/06_Tai_lieu_kiem_thu_va_ket_qua.md`; các ca đó đang ở trạng thái Chưa kiểm tra.

## A. Việc mới

### A1. Tính giá trị nguyên liệu theo bình quân gia quyền di động

**Hiện trạng.** `apps/api/src/app/modules/inventory/costing.py` tính bình quân theo tháng (`MonthlyAverageCost`, `recompute_month`, `refresh_costing`, `backfill_issue_costs`), lưu ở bảng `GIA_BINH_QUAN_THANG`. Khi phiếu nhập đổi, code tính lại tháng đó và các tháng sau, kể cả giá vốn của các lần xuất đã ghi.

**Yêu cầu.**

1. Mỗi nguyên liệu có một đơn giá bình quân hiện hành. Đơn giá này được tính lại khi:
   - nhập kho;
   - sửa số lượng hoặc đơn giá phiếu nhập hợp lệ;
   - hủy phiếu nhập hợp lệ;
   - hoàn kho khi hủy hoặc giảm món đang Chờ làm.
2. Công thức: `đơn giá mới = (tồn trước × đơn giá hiện hành + lượng biến động × đơn giá của biến động) / tồn sau`.
   - Khi sửa hoặc hủy phiếu nhập: đảo phần lượng và giá trị cũ của phiếu ra trước, rồi mới cộng phần mới (hủy thì không cộng gì).
   - Hoàn kho dùng đơn giá đã ghi trên giao dịch xuất gốc.
3. Nếu tồn sau bằng 0, giữ nguyên đơn giá hiện hành và không chia.
4. Xuất bán, xuất hủy và điều chỉnh kiểm kê không làm đổi đơn giá. Giá trị của các nghiệp vụ này bằng lượng × đơn giá hiện hành tại thời điểm phát sinh, ghi một lần vào `CHI_TIET_PHIEU_XUAT.GiaVonUocTinh` và giao dịch kho tương ứng. Không bao giờ tính lại giá trị này về sau.
5. Sửa ngày nhập chỉ cập nhật ngày lô, hạn dùng và thứ tự FIFO, không đổi đơn giá. Điều kiện được sửa hoặc hủy phiếu nhập giữ như hiện tại: các lô chưa phát sinh xuất và không có giữ món còn hiệu lực.
6. Nguyên liệu chưa từng có phiếu nhập hợp lệ thì không có đơn giá:
   - giá trị các biến động của nó là NULL, không gán 0;
   - khi có phiếu nhập hợp lệ đầu tiên, đơn giá nhập trở thành đơn giá ban đầu, và các giá trị NULL trước đó được định giá theo đơn giá này.
7. Làm tròn:
   - đơn giá: 2 chữ số, ROUND_HALF_UP;
   - giá trị dòng xuất: đơn giá đã làm tròn × lượng, rồi làm tròn 2 chữ số theo cùng quy tắc;
   - lượng: giữ 6 chữ số thập phân.
8. Mỗi lần tính lại đơn giá chạy trong cùng transaction với nghiệp vụ phát sinh, và ghi một dòng vào `LICH_SU_GIA_BINH_QUAN`.
9. Không đổi hóa đơn, doanh thu hay công thức đã lưu trên dòng món.

**CSDL.** Migration mới:
- Tạo `LICH_SU_GIA_BINH_QUAN`:
  - khóa chính (`MaNguyenLieu`, `ThoiDiemHieuLuc DATETIME(3)`);
  - `DonGiaBinhQuan DECIMAL(18,2) NOT NULL`;
  - `SoLuongTon DECIMAL(18,6) NOT NULL`;
  - `MaGiaoDichKho BIGINT NULL`, FK tới `GIAO_DICH_KHO`, RESTRICT.
- Xóa `GIA_BINH_QUAN_THANG`. Không cần chuyển dữ liệu cũ, vì dữ liệu dev/demo được sinh lại ở A6.
- Đơn giá hiện hành là dòng có `ThoiDiemHieuLuc` lớn nhất, không vượt thời điểm xét.

**Code liên quan.**
- `inventory/costing.py`: thay toàn bộ logic theo tháng.
- `inventory/service.py`: các luồng tạo, sửa, hủy phiếu nhập; xuất; hoàn kho.
- `inventory/models.py`.
- `reports/queries.py`: chỉ đọc giá trị đã ghi trên giao dịch.
- Test: `tests/modules/test_inventory_costing.py`, `test_business_month_costing.py` (xóa hoặc viết lại), `test_reports_margin.py`.

**Không làm.**
- Không giữ song song cách tính theo tháng.
- Không tính lại `GiaVonUocTinh` đã ghi.
- Không coi NULL là 0, và không bỏ phần NULL khỏi tổng rồi hiển thị như tổng đầy đủ.

**Hoàn thành khi.**
- Ví dụ:
  - Bò tồn 0, nhập 10 kg giá 200.000 → đơn giá 200.000.
  - Nhập tiếp 10 kg giá 260.000 → (10 × 200.000 + 10 × 260.000) / 20 = 230.000.
  - Hủy phiếu thứ hai khi lô chưa xuất → (20 × 230.000 − 10 × 260.000) / 10 = 200.000.
- Các ca đạt: TC-INV-19, 21–23; TC-REP-04–06, 11–13; TC-BR-09, 10, 12, 13, 18, 22–25.
- Căn cứ đặc tả:
  - tài liệu 04, mục G.1 (các đoạn về `LICH_SU_GIA_BINH_QUAN`, làm tròn và giá trị chưa xác định);
  - tài liệu 03: FR-INV-02/03/04/05/09, FR-REP-11.

### A2. Kiểm kê: xem trước rồi mới xác nhận

**Hiện trạng.** Trong `apps/web/src/features/inventory/stocktake-panel.tsx`, nút “Xác nhận kiểm kê” gọi `POST /inventory/stocktakes/{sid}/counts` rồi `POST /inventory/stocktakes/{sid}/confirm` ngay. Người dùng không thấy kết quả trước khi tồn bị điều chỉnh.

**Yêu cầu.**
1. Luồng: Bếp mở phiên (kho tạm khóa như hiện tại) → nhập số lượng thực tế và lý do → bấm **Xem trước**.
2. Hệ thống trả về cho từng nguyên liệu: tồn trước điều chỉnh (sổ sách), tồn sau điều chỉnh (số thực tế) và chênh lệch. Bước này không ghi gì vào CSDL.
3. Màn hình hiển thị bảng đó với hai nút:
   - **Xác nhận**: gọi luồng counts + confirm hiện có.
   - **Quay lại sửa**: trở về màn nhập và giữ nguyên số đã nhập.
4. **Hủy phiên** giữ như hiện tại.
5. Phần xem trước nằm trong màn kiểm kê hiện có (hộp thoại hoặc bước trong panel), không thêm trang mới.
6. Backend thêm API chỉ tính, không ghi, ví dụ `POST /inventory/stocktakes/{sid}/preview`, nhận cùng dữ liệu với `/counts`.

**Không làm.**
- Không thêm trạng thái mới. Phiếu kiểm kê vẫn chỉ có Đang kiểm kê / Đã xác nhận / Đã hủy.
- Không điều chỉnh tồn trước khi bấm Xác nhận.
- Không mở khóa kho khi đang xem trước.

**Hoàn thành khi.**
- Các ca đạt: TC-INV-41–45, 52–54.
- Căn cứ: tài liệu 02 mục 2.3.17 (QT-17); tài liệu 03 UC 3.4, FR-INV-08/09; tài liệu 05 SD-3.4.

### A3. Xuất hủy nguyên liệu: xem trước rồi mới ghi phiếu

**Hiện trạng.**
- `POST /inventory/issues` ghi phiếu và trừ tồn ngay.
- Đã có `GET /inventory/issues/prepared-preview` cho nguồn Món đã chế biến.

**Yêu cầu.**
1. Với nguồn Nguyên liệu: sau khi người lập chọn lô và lượng, hệ thống hiển thị bản xem trước gồm:
   - lô và lượng hủy;
   - tồn còn lại của lô;
   - giá trị = lượng × đơn giá bình quân hiện hành, hoặc “Chưa xác định” nếu chưa có đơn giá;
   - các lượt giữ món sẽ bị giải phóng.
2. Bản xem trước không ghi gì. **Xác nhận** gọi `POST /inventory/issues` như hiện tại; **Quay lại sửa** không ghi gì.
3. Nguồn Món đã chế biến cũng phải qua bước xem trước trước khi lưu, dùng `prepared-preview` đang có.
4. Có thể dùng chung component xem trước với A2.

**Không làm.** Không ghi phiếu hay giao dịch kho trước khi xác nhận.

**Hoàn thành khi.**
- Các ca đạt: TC-INV-55, TC-INV-49.
- Căn cứ: tài liệu 02 mục 2.3.16 (QT-16); tài liệu 03 UC 3.3, FR-INV-05/06; tài liệu 05 SD-3.3.

### A4. Màn tồn kho hiển thị đơn giá bình quân và giá trị tồn

**Hiện trạng.** `GET /inventory/stock` và `stock-table.tsx` chưa có cột giá.

**Yêu cầu.**
1. Mỗi nguyên liệu thêm hai cột:
   - **Đơn giá bình quân hiện hành**;
   - **Giá trị tồn** = tồn sổ sách × đơn giá.
   Chưa có đơn giá thì cả hai cột hiển thị “Chưa xác định”; API trả `null`, không trả 0.
2. Chọn một nguyên liệu để xem lịch sử đơn giá. Mỗi dòng gồm thời điểm, chứng từ phát sinh, đơn giá và tồn sau giao dịch. API mới đọc từ `LICH_SU_GIA_BINH_QUAN`.

**Hoàn thành khi.**
- Các ca đạt: TC-INV-56, 57.
- Căn cứ: tài liệu 02 mục 2.3.18; tài liệu 03 UC 3.5, FR-INV-12.

### A5. Giá vốn ước tính của món và cảnh báo tỷ lệ giá vốn

**Hiện trạng.**
- Danh sách món (`apps/web/src/features/catalog/dish-list.tsx`) và chi tiết món (`dish-detail.tsx`, đã chứa `RecipeEditor` và `PriceScheduler`) chưa có thông tin giá vốn.
- `CAU_HINH_HE_THONG` chưa có ngưỡng.

**Yêu cầu.**
1. Thêm cột cấu hình bằng migration:
   - `CAU_HINH_HE_THONG.TyLeGiaVonCanhBao DECIMAL(5,2) NOT NULL DEFAULT 40`, CHECK từ 1 đến 100;
   - Quản lý sửa được giá trị này ở màn Cài đặt, cùng chỗ với các tham số hiện có.
2. Với mỗi món, tính:
   - giá vốn ước tính = Σ (định lượng từng nguyên liệu trong công thức đang áp dụng, đã quy đổi về đơn vị chuẩn × đơn giá bình quân hiện hành);
   - tỷ lệ giá vốn = giá vốn / giá bán hiện hành, hiển thị 1 chữ số thập phân;
   - lãi gộp mỗi suất = giá bán − giá vốn.
3. Hiển thị trên danh sách món: giá bán, giá vốn ước tính, tỷ lệ, lãi gộp.
   - Món có tỷ lệ **lớn hơn** ngưỡng được đánh dấu cảnh báo.
   - Chi tiết món có bảng từng nguyên liệu: định lượng, đơn giá, thành tiền.
4. Các trường hợp đặc biệt:
   - Món chưa có công thức: ghi “Chưa có công thức”.
   - Có nguyên liệu chưa có đơn giá: ghi “Chưa đủ dữ liệu” kèm tên nguyên liệu đó, không tính phần thiếu bằng 0, không hiển thị tỷ lệ và không cảnh báo.
5. Khi Quản lý nhập giá bán mới (`price-scheduler.tsx`), hiển thị ngay tỷ lệ giá vốn theo giá đang nhập.
6. Chỉ vai trò Quản lý nhận các trường giá vốn. API trả danh sách món cho Thu ngân và Bếp không chứa các trường này.

**Không làm.**
- Không tự đổi giá bán.
- Không dùng con số này cho báo cáo lợi nhuận. Báo cáo vẫn dùng giá trị đã ghi trên giao dịch (A1).
- Không tách công thức thành trang hay tab riêng ở cấp Danh mục. Công thức ở trong chi tiết món như hiện tại.

**Hoàn thành khi.**
- Ví dụ: Bò xào giá 80.000 đ, công thức 150 g bò (230.000 đ/kg) và 50 g hành (40.000 đ/kg), ngưỡng 40% → giá vốn 36.500 đ, tỷ lệ 45,6%, lãi gộp 43.500 đ, có cảnh báo.
- Các ca đạt: TC-CAT-49–51.
- Căn cứ: tài liệu 02 mục 2.3.1, 2.3.3 (QT-01, QT-03) và quy tắc 19; tài liệu 03 FR-CAT-29, FR-SET-04, UC 1.2 và 1.3; tài liệu 04 F.3, lớp `MON_AN` (`tinhGiaVonUocTinh()`).

### A6. Dữ liệu mô phỏng 2 tháng, quy mô quán nhỏ

**Hiện trạng.** `make seed` sinh dữ liệu 12 tháng, `scripts/seed_perf.py` sinh khoảng 20.000 order; tồn kho có nguyên liệu lên tới vài chục tấn.

**Yêu cầu.** Sinh lại theo Phụ lục B của báo cáo:
1. Thông số chung:
   - 60 ngày;
   - 70 order ngày thường và 110 order cuối tuần, dao động ±15%, tổng khoảng 4.800 order;
   - mở cửa 10:00–22:00;
   - 12 bàn, 30 món, 35 nguyên liệu, 3 nhà cung cấp; mỗi dòng món 1–2 suất.
2. Nhập kho:
   - đồ tươi nhập hằng ngày; đồ khô và gia vị nhập thứ Hai và thứ Năm;
   - lượng nhập bằng nhu cầu đến lần nhập kế tiếp cộng tồn tối thiểu, mỗi dòng không quá 30 kg;
   - đơn giá dao động ±10% giữa các lần nhập.
3. Tồn của mỗi nguyên liệu không vượt 40 kg tại mọi thời điểm. Thêm bước kiểm tra điều kiện này sau khi sinh.
4. Phụ lục B.1 là bộ cho đánh giá AI (`scripts/seed/config.py`, `generate.py`, `operations.py`, `catalog.py`). Phụ lục B.2 là bộ đo hiệu năng (`scripts/seed_perf.py`, `scripts/perf/seed.py`), cùng quy mô, nhập hai lần mỗi tuần.

Cập nhật mô tả “12 tháng” trong `Makefile` và README theo quyết định của dev.

**Hoàn thành khi.** Hai bộ dữ liệu sinh được với cùng hạt giống, qua bước kiểm tra tồn ≤ 40 kg, và giá trị kho được tính theo A1.

## B. Việc còn tồn từ đợt 31/10

### B1. 13 ca chưa có test tự động

Các ca: TC-SALE-08, 19, 26, 46, 49; TC-INV-46, 47; TC-BR-07, 08; TC-CAT-31, 32; TC-REP-09, 15.

Viết test đúng assertion của ca trong tài liệu 06. Không lấy số hàm test thay cho số ca nghiệm thu.

### B2. Sửa 21 ca không đạt và 1 ca bị chặn

Đây là kết quả đợt kiểm thử 03–04/11 trên `099191e`, ghi trong tài liệu 06:
- Không đạt: TC-INV-09, TC-SALE-19, TC-CAT-03, TC-CAT-10, TC-SALE-32, TC-SET-01, TC-SET-09, TC-CAT-13, TC-CAT-16, TC-SALE-13, TC-SALE-70, TC-BR-06, TC-INV-05, TC-REP-08, TC-REP-09, TC-REP-07, TC-BR-14, TC-BR-19, TC-BR-15, TC-BR-11, TC-SALE-61.
- Bị chặn: TC-BR-21.

Nhánh `fix/demo-blockers` (đầu nhánh `395d0ca`, ngày 06/11, tách từ `099191e`) đã sửa và chạy lại đạt TC-SET-01, TC-INV-05, TC-BR-15, TC-BR-19, TC-BR-21. Bằng chứng ở `docs/testing/artifacts/2026-11-06-fix-demo-blockers/` trên nhánh đó. Nhánh này chưa merge vào `main`. Merge nó vào `main` trước khi làm phần A; `main` chỉ có thêm hai commit tài liệu nên không đụng code. Sau đó sửa các ca còn lại theo thứ tự:
1. Giữ và gửi món: TC-INV-09, TC-SALE-19.
2. Giá vốn và báo cáo: TC-REP-07, 08, 09, TC-BR-11, 14. Làm cùng A1, vì kỳ vọng của các ca này đã đổi sang bình quân di động.
3. Webhook và nhật ký: TC-BR-06, TC-SET-09.
4. Các lỗi còn lại.

### B3. Chạy đủ cổng kiểm tra

Trên nhánh `fix/demo-blockers`, lượt ngày 06/11 ghi `make gate` đạt (771 test backend, 200 test frontend, build) và integration MySQL đạt 18/18. Trên `main` chưa có lượt đạt toàn bộ, vì nhánh này chưa được merge.

Sau khi merge và làm xong A1–A6, chạy lại `make gate` và integration MySQL trong môi trường có MySQL và `AI_READONLY_URL_*`. Ghi mã commit và log.

### B4. Đo hiệu năng và sao lưu

Sau A6, chạy kịch bản tải hỗn hợp 5/10/20 người dùng trên bộ dữ liệu B.2, theo mục G tài liệu 06 (NFR-01, NFR-03).

NFR-11 mới có một lượt sao lưu/khôi phục khớp checksum. Còn phải kiểm chứng lịch sao lưu và RPO.

### B5. Chạy lại đánh giá AI

Sau A6, chạy lại thực nghiệm A/B/C (80 câu × 3 cấu hình × 3 lần = 720 lượt) và bộ an toàn trên bộ dữ liệu B.1 khi có khóa API. Ghi phiên bản, ngày chạy và file kết quả.

### B6. Dọn cảnh báo

Biến `Bars` không dùng trong `apps/web/src/features/reports/closed-unpaid-panel.tsx`, nếu vẫn còn.

## C. Thứ tự làm đề xuất

1. Merge `fix/demo-blockers` vào `main` (B2).
2. A1, vì A3, A4, A5 và nhóm giá vốn của B2 đều dựa trên đơn giá bình quân.
3. B2 nhóm giá vốn (TC-REP-07/08/09, TC-BR-11/14), làm cùng A1.
4. A2 và A3.
5. A4 và A5.
6. A6.
7. Phần còn lại của B2, rồi B1.
8. B3, sau đó B4 và B5.

## D. Quy tắc đối chiếu khi viết test

Bảng dưới là kỳ vọng thống nhất giữa QT, FR/UC, thiết kế dữ liệu, SD và kiểm thử.

| **Luồng** | **Kỳ vọng** | **Căn cứ** |
|---|---|---|
| Giữ món tại mốc hết hạn | Hết hạn giải phóng khả dụng; lúc gửi phải kiểm tra lại, không tự gia hạn | FR-SALE-05/08; FR-INV-10; SD-2.1a; TC-BR-01 |
| Mở kiểm kê khi chỉ còn giữ hết hạn | Lượt chọn chưa gửi/hủy vẫn chặn; nhân viên phải gửi hoặc hủy trước; không tự hủy khi mở kiểm kê | QT-17; FR-INV-08; SD-3.4; TC-INV-33; TC-BR-02/03 |
| Xem trước điều chỉnh kiểm kê | Xem trước không ghi dữ liệu; tồn chỉ đổi khi xác nhận; Quay lại sửa giữ phiếu Đang kiểm kê và kho vẫn khóa | QT-17; FR-INV-08; SD-3.4; TC-INV-52–54 |
| Kiểm kê thiếu | Chỉ giao dịch điều chỉnh làm giảm tồn; phiếu xuất hủy là chứng từ tham chiếu | FR-INV-09; SD-3.4; TC-BR-10 |
| Xem trước xuất hủy | Không ghi phiếu hay giao dịch trước khi xác nhận; sau xác nhận chỉ có một phiếu theo số liệu cuối | QT-16; FR-INV-05; SD-3.3; TC-INV-55 |
| Xuất hủy món đã chế biến | Số suất và tiêu hao gốc; không trừ tồn hoặc cộng hao hụt hai lần | QT-16; FR-INV-05/06; SD-3.3; TC-BR-09 |
| Giá trị nguyên liệu | Đơn giá bình quân di động tính lại khi nhập, sửa/hủy phiếu nhập và hoàn kho; giá trị xuất ghi một lần; chưa có giá là NULL, không phải 0 | Tài liệu 04 G.1; TC-BR-11–13, 18, 22–25 |
| Giá vốn ước tính của món | Theo công thức và đơn giá hiện hành; thiếu giá thì “Chưa đủ dữ liệu”; vượt ngưỡng chỉ cảnh báo, không đổi giá bán | FR-CAT-29; TC-CAT-49–51 |
| Webhook muộn khi có QR mới | Tự xác nhận khoản cũ nếu đủ điều kiện; hủy QR mới chưa nhận tiền trong cùng transaction | FR-SALE-16; SD-2.5a; TC-BR-04 |
| Webhook sau quyết định mở lại | Mở lại của Quản lý khác tự về Đang mở khi QR hết hạn; chỉ Quản lý được áp dụng khoản ngoại lệ | FR-SALE-17/23; SD-2.6a; TC-BR-05 |
| Webhook lặp và xác nhận thủ công | Liên kết cùng khoản nhận, không thu hoặc ghi ngoại lệ hai lần | FR-SALE-15/16; TC-BR-06 |
| Phục vụ sau thanh toán | Khóa nội dung/tiền, vẫn cập nhật phục vụ cho dòng chưa hủy; bàn không tự trống | FR-SALE-09/22; FR-CAT-18; SD-2.3; TC-BR-07 |
| Bàn đã phục vụ order mới | Xử lý tiền order cũ không ảnh hưởng bàn/order mới; không gọi thêm hoặc đổi bàn order cũ | FR-CAT-18; TC-BR-08 |
| Hạn dùng theo ngày | Ngày lịch tại nhà hàng, dùng được hết ngày hạn; không dùng BusinessDate để kéo dài hạn qua nửa đêm | Tài liệu 04 BR-LOT-01; kiểm thử ranh giới ngày lịch |

## E. Nghiệm thu

- Mỗi thay đổi CSDL đi qua migration có up/down, kiểm tra trên MySQL 8.4.
- Kiểm thử hồi quy dùng tài liệu 06 (258 ca). Test phụ thuộc MySQL phải chạy trên MySQL thật; lỗi do môi trường ghi tách khỏi lỗi sản phẩm.
- Khi báo kết quả, ghi mã commit, lệnh đã chạy và log. Chỉ cập nhật kết quả vào tài liệu khi có đủ ba thông tin này.
