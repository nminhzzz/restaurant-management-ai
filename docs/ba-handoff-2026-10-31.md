# Ghi chú bàn giao cho BA: chỗ tài liệu lệch với mã nguồn (31/10/2026)

Đối chiếu bản tài liệu `95c34d1` (báo cáo `docs/BaoCao_HeThongQuanLyNhaHang.md` và `docs/Tai_lieu/01–06`) với mã nguồn
trên nhánh `fix/docs-code-alignment`. Chỉ liệt kê chỗ **cần BA cập nhật tài liệu**, kèm vị trí để tìm nhanh.
Số dòng là của bản `95c34d1`. Mục nào ghi "mã nguồn" nghĩa là phía code đã/đang được xử lý riêng, BA không cần làm gì.

Phần khớp, không cần sửa: bộ 80 câu và SHA256 khóa, toàn bộ số liệu A/B/C và an toàn, số test (720/15/8/199),
209 ca trong tài liệu 06, tên model, ma trận quyền (Bảng 12), 30 UC khớp 30 SD, mặc định Business Date 06:00,
giữ món 5 phút, hạn mức 50 câu/ngày, QR 10 phút, các view `vw_ai_*` và quyền theo vai trò, mọi link/ảnh tương đối.

## 1. Lược đồ CSDL (tài liệu 04, phần D, F, G; báo cáo §4.2)

1. **Số bảng:** tài liệu ghi 31, mã nguồn có 37. Thêm 6 bảng phụ trợ chưa có trong tài liệu: `LICH_GIO_BUSINESS_DATE`,
   `DEM_ORDER`, `DEM_HOA_DON`, `NGOAI_LE_THANH_TOAN`, `HAN_MUC_AI_NGAY`, `BO_NHO_DEM_SQL_AI`. Cần thêm mục "bảng kỹ thuật/phụ trợ"
   hoặc ghi chú "31 là số bảng miền nghiệp vụ".
2. **Ngoại lệ thanh toán** (04, F.17, dòng 917–921): tài liệu để 5 cột `TrangThaiNgoaiLe`, `SoTienNgoaiLe`, `MaThamChieuHoan`,
   `ThoiDiemXuLyNgoaiLe`, `NguoiXuLyNgoaiLe` trong `GIAO_DICH_THANH_TOAN`; code tách thành bảng `NGOAI_LE_THANH_TOAN`
   (`MaNgoaiLe`, `TrangThai`, `LyDo`, `ThoiDiemXuLy`, `NguoiXuLy`, `SoTienHoan`, …).
3. **Giờ Business Date chờ hiệu lực** (04, F.3, dòng 721–722): tài liệu có `GioBatDauBusinessDateMoi`, `NgayHieuLucGioMoi` trong
   `CAU_HINH_HE_THONG`; code dùng bảng lịch `LICH_GIO_BUSINESS_DATE` (đúng với FR-SET-04 "lịch hiệu lực").
4. **`MON_AN.HetNguyenLieu`** (04, F.6, dòng 762; báo cáo §4.2.2): tài liệu ghi là thuộc tính dẫn xuất, không lưu; code lưu cột
   boolean và dùng trong cột GENERATED `TrangThai`.
5. **`PHIEU_XUAT_KHO.NguonXuat`** (04, F.22, dòng 984 và phần G): tài liệu có cột, code chưa có (chỉ có hằng `ISSUE_SOURCES`
   trong service). Cần BA/dev chốt: thêm cột vào code hay bỏ khỏi tài liệu.
6. **Tên cột lệch:** `ORDER.ThoiDiemTao` (code: `NgayTao`); `PHIEU_NHAP_KHO.NguoiLap` (code: `NguoiTao`);
   `CHI_TIET_KIEM_KE.MaChiTietKK` (code: `MaChiTietKiemKe`).
7. **Cột có trong code nhưng chưa có trong tài liệu:** `NGUOI_DUNG.PhienBanToken`; `CAU_HINH_HE_THONG.MocDongBoSepay`;
   `BAN.KhuVuc`; `ORDER.MaYeuCauGui`, `NgayCapNhat`; `CHI_TIET_ORDER.MaYeuCauDong`; `HOA_DON.NoiDungChup` (JSON);
   `GIAO_DICH_THANH_TOAN.NgayTao`; `PHIEU_BEP`: `TrangThai`, `SoLanThuTrongDot`, `LanThuTiepTheo`, `MaKhoaIn`, `HanKhoaIn`, `LoiIn`,
   `NgayTao`; `PHIEU_XUAT_KHO`: `TrangThai`, `NgayTao`; `CHI_TIET_KIEM_KE.LyDoChenhLech`; `GIU_CHO_MON.NgayTao`;
   `TRUY_VAN_AI`: `ChiTietSuDung`, `PhanHoi`.
8. **Kiểu dữ liệu:** `VAI_TRO.MaVaiTro` và `NGUOI_DUNG.MaVaiTro` là `VARCHAR(20)` (`MANAGER`/`CASHIER`/`WAREHOUSE`), tài liệu ghi INT
   (04 dòng 81, 692; báo cáo §4.2.2 và Bảng 11). Khóa chính/ngoại khác trong code là BIGINT. Tiền và lượng trong code là
   `DECIMAL(18,4)` (tài liệu: (18,2) và (18,6)); `ChiPhiUSD` là (18,10) (tài liệu: (18,8)); `GIAO_DICH_KHO.TonSauGiaoDich` tài liệu ghi (18,2)
   dù là lượng. Ngày nhập/xuất/kiểm kê trong code là `DateTime`, tài liệu ghi DATE. Độ chính xác thời gian: 04 ghi `DATETIME(6)`,
   báo cáo §4.2.2 ghi `DATETIME(3)`, code dùng mặc định. Cần thống nhất.
9. **`NGUYEN_LIEU.MucTonToiThieu`** (04, F.10): tài liệu "để trống thì dùng mặc định"; code là NOT NULL, giá trị `0` nghĩa là dùng mặc định.
10. **Giá trị trạng thái** (04, F và phần mô tả lớp): code dùng bộ giá trị khác.
    - `PHIEU_KIEM_KE.TrangThai`: code "Nháp / Đã chốt / Đã hủy" (tài liệu: "Đang kiểm kê / Đã xác nhận / Đã hủy"; dòng 518, 1006).
    - `PHIEU_NHAP_KHO.TrangThai`: code tạo ở "Nháp" rồi chỉ chuyển "Đã hủy"; tài liệu ghi "Hiệu lực / Đã hủy" (dòng 424).
    - `PHIEU_BEP.TrangThaiIn`: code "Chờ in / Đang in / Chưa rõ kết quả / Thất bại / Đã gửi máy in" (tài liệu: "Thành công / Thất bại"; dòng 928).
    - `GIAO_DICH_THANH_TOAN.TrangThai`, `LICH_SU_GIA_MON.LoaiThayDoi`, `CHI_TIET_ORDER.TrangThai` ("Chờ" trong DB, "Chờ làm" trong tài liệu): cần thống nhất từ vựng.
    - Order và giao dịch còn hai trạng thái chưa có trong tài liệu: **"Chờ đối soát"** và **"Tranh chấp"**, cùng các endpoint
      `/orders/{id}/reconcile`, `/payments/{id}/reference`, `/payments/{id}/resolve` (04 dòng 297, 378 chỉ có luồng "Chờ xác minh").
11. **`CHI_TIET_GIU_CHO → GIU_CHO_MON`** (04, G, dòng 1178): tài liệu ghi RESTRICT, code dùng `ON DELETE CASCADE` (hợp lý vì chi tiết phụ thuộc cha).
12. **Ràng buộc có trong tài liệu nhưng code chưa có** (cần quyết định thêm vào code qua migration mới, hoặc nới tài liệu):
    CHECK `> 0` cho `LICH_SU_GIA_MON.GiaBan`, `CHI_TIET_CONG_THUC.DinhLuong`, `CHI_TIET_ORDER.SoLuong`, `CHI_TIET_PHIEU_NHAP.SoLuong` và
    `HeSoQuyDoi`, `LO_NGUYEN_LIEU.SoLuongNhap` (và `SoLuongConLai >= 0`), `CHI_TIET_PHIEU_XUAT.SoLuong`; quy tắc `MaChiTietNhap` NULL khi
    `LoDieuChinhKiemKe = true` (BR-LOT-02); UNIQUE `GIAO_DICH_THANH_TOAN.MaGiaoDichCong` (code chỉ có UNIQUE `MaGiaoDichNganHang` và UNIQUE
    trên bảng ngoại lệ); CHECK nguồn của `GIAO_DICH_KHO` ("đúng một trong bốn FK" nhưng "Hoàn kho" trong code dùng nhiều FK);
    `PHAM_VI_DU_LIEU` trong `TRUY_VAN_AI` (F.29 yêu cầu ghi danh sách view thực tế, code ghi nhãn họ view, cột `String(50)`).
    Đây là thay đổi lược đồ, **chưa làm**, chờ quyết định.
13. **Khóa ngoại nhật ký:** FK `NHAT_KY_HE_THONG.MaNguoiDung` chưa khai báo `ON DELETE/UPDATE` tường minh (04, G, dòng 1116 cấm dùng mặc định).

## 2. Chức năng, trạng thái và quy tắc (tài liệu 02, 03, 04, 05; báo cáo chương 4)

14. **Đăng xuất** (báo cáo dòng 1203 "Thu hồi phiên; 401"; 03 dòng 568 "kết thúc phiên tại máy chủ"): code **không có** endpoint đăng xuất;
    giao diện chỉ xóa phiên cục bộ, JWT không bị thu hồi. Cần sửa tài liệu cho đúng thực tế (hoặc chốt làm thêm cơ chế thu hồi, `PhienBanToken` đã có sẵn).
15. **Xóa nhóm món chưa từng có món** (FR-CAT-03, 03 dòng 655): tài liệu nói xóa vĩnh viễn; code luôn xóa mềm (`catalog/service.py:100-103`).
    Đề xuất sửa tài liệu thành "xóa mềm". Có thể liên quan TC-CAT-09 và TC-CAT-41 "chưa đạt" trong tài liệu 06.
16. **Mã lỗi và thân lỗi** (báo cáo dòng 1220): thân lỗi chỉ gồm `{error:{code,message}}` (riêng lỗi 500 có `error_id`), không có `request_id`/`details`;
    mọi vi phạm trạng thái trả **422** (409 chỉ dùng một chỗ ở `settings/service.py:115`); hết hạn mức AI trả **200** kèm câu trả lời, không phải 429.
17. **Bảng 13** (báo cáo dòng 1198–1212): cột URL để trống ở mọi hàng.
18. **Tham chiếu bảng:** tài liệu 02 dòng 10 "quyền chi tiết tại Bảng 10" phải là **Bảng 12** (Bảng 10 là danh sách lớp).
19. **Thanh toán:** báo cáo dòng 288, 1560 nói chưa kết nối cổng thanh toán thật; code có adapter SePay chọn bằng `PAYMENT_GATEWAY`
    (`simulator`/`sepay`) và hai webhook (`router.py:554-583`). Nên ghi hai chế độ vào tài liệu 02/03/04.
20. **Chức năng chưa có FR/UC:** `POST /inventory/costing/{month}/close` (chốt giá bình quân tháng) và `POST /settings/backup` chưa gắn FR nào.
21. **"Tự động đóng"** (trạng thái order): còn trong báo cáo và prompt AI nhưng không có chỗ nào trong code gán trạng thái này (`reports/queries.py:42`).
22. **Dòng món:** tài liệu và UI dùng "Chờ làm", giá trị lưu trong DB là "Chờ". Cần thống nhất (hiện chỉ khác tên khái niệm và giá trị lưu).

## 3. Tài liệu kiểm thử (tài liệu 06 và báo cáo chương 6)

23. **Bảng 53** (06 dòng 2336–2370): ghi tập dev là `DEV01–DEV30`, phân bố 11 dễ/12 trung bình/7 khó, 20 Quản lý/5 Thu ngân/5 Bếp. Thực tế
    `data/eval/questions.dev.jsonl` là `D001–D030`, phân bố **8/10/12**, vai trò **2 Quản lý / 13 Thu ngân / 15 Bếp**; chỉ 1 câu trùng nội dung.
    **Bảng 51** (06 dòng 2321) dùng ID `AIxx` trong khi file thật dùng `Q001…`.
24. **Tham chiếu mục chéo sai** trong 06: dòng 2311 và 2289 trỏ "mục 6.8", đúng là **6.4** (6.8 là SUS); dòng 2386 "mục 6.4" cho bộ AT, đúng là **6.5**;
    dòng 2459 "100 lượt tại mục 6.4", đúng là **6.6** (báo cáo dòng 1505).
25. **Số lỗi chấm điểm:** báo cáo dòng 1442 và 06 dòng 2312 ghi "2 lỗi số liệu và 27 lỗi nhận xét" (29); `docs/eval-grades-after-2026-10-27.json` có
    **31 lượt trượt**: 27 nhận xét, 4 kỳ/phạm vi, 2 số liệu (một lượt có thể dính nhiều nhãn).
26. **NFR-01** (06 dòng L): ghi "Chưa đạt", trong khi `docs/testing/performance-2026-10-27.md` ghi "Đạt theo p95, kèm lỗi độ tin cậy". Hai bên dùng tiêu chí khác nhau, cần nói rõ.
27. **"Ba agent Sonnet 5.5 chấm mù"** (báo cáo): file grades chỉ có một nhãn reviewer ("Agent Claude Sonnet 5.5"), không kiểm chứng được "ba agent".
28. **Bằng chứng** `Bang_chung_kiem_thu_68505dc_2026-10-28` (06 dòng 30, báo cáo dòng 1665) không có trong repo (commit 68505dc chỉ đổi tên thư mục ảnh).
29. **`docs/testing/test-cases.md`** (bảng ca kiểm thử cũ): dùng ID `TC-CAT-nn`, `TC-SALE-nn` trùng với tài liệu 06 nhưng nghĩa khác (ví dụ TC-CAT-09, TC-CAT-41, TC-SALE-19)
    và số ca khác (41 CAT/41 SALE so với 48/101); trỏ tới 3 hàm test không còn tồn tại
    (`test_a_supplier_with_no_history_is_deleted_outright`, `test_manual_hiding_is_independent_of_stock`,
    `test_the_two_out_of_stock_causes_are_independent`, dòng 44, 56, 57, 126); vẫn dùng đánh số NFR cũ (NFR-06, 12, 14, 16 ở dòng 220–236). Nên bỏ file này
    hoặc đánh dấu "đã thay bằng tài liệu 06".

## 4. Khác

30. `AGENTS.md` dòng 70 ghi "báo cáo 23/10/2026"; báo cáo hiện là V33 ngày 27/10/2026. Giá trị `AI_MAX_ROWS=500`, `AI_SQL_TIMEOUT_SECONDS=3`,
    `AI_MAX_SQL_ATTEMPTS=2` khớp cả 4 nơi.
31. 92 ảnh (khoảng 20 MB) trong `docs/images/{00_Bao_cao_khoa_luan,01_…,03_…,04_…}` không còn tài liệu nào dẫn tới.
32. `docs/testing/performance-2026-10-27.md` (dòng 235) và `docs/testing/source-docs-review-2026-10-21.md` còn trích NFR theo đánh số cũ (NFR-20, …).
    Đây là biên bản có ngày nên giữ nguyên; chỉ lưu ý khi trích dẫn.

## 5. Đã xử lý ở phía mã nguồn (BA không cần làm)

- Vai trò thứ ba thống nhất tên **"Bếp"** ở giao diện (`roles.ts`), seed người dùng và seed `VAI_TRO`. Mã định danh vẫn là `WAREHOUSE`.
  Lưu ý: CSDL đã tạo sẵn vẫn giữ tên cũ "Nhân viên kho" ở bảng `VAI_TRO` (hàm seed chỉ chèn khi chưa có dòng).
- FR-SALE-10: giảm số lượng món nay ghi audit `REDUCE_ORDER_LINE` (người thực hiện, thời điểm, số lượng trước và sau).
- FR-SALE-08: giảm số lượng giữ món không còn gia hạn thời hạn; chỉ tăng mới làm mới.
- Sửa các chú thích trong code trích sai số NFR/FR (đánh số cũ) và các tài liệu kỹ thuật (`docs/testing/*`, `docs/design/tokens.md`,
  `docs/thuyet-trinh/kich-ban-demo.md`, `data/eval/README.md`).
- Mã còn lại **chưa sửa** (cần quyết định, ngoài phạm vi lần này): `apps/api/src/app/shared/enums.py` chứa enum cũ gần như không dùng
  và mâu thuẫn với máy trạng thái thật (`OrderStatus`, `OrderLineStatus`, `TableStatus`, `PaymentStatus`, …); là mã chết có từ trước.
