# Đối chiếu nghiệp vụ, thiết kế và mã nguồn

Phạm vi đối chiếu: báo cáo, tài liệu 01–06, bốn nguồn drawio và mã nguồn tại commit `8423b3f`. Nghiệp vụ lấy từ bản đầy đủ tại `f789de7`, các yêu cầu hiện hành và quyết định của chủ đề tài: đúng ba vai trò với vai trò thứ ba là Bếp; giữ quy tắc xóa nhóm món. Khác biệt kỹ thuật không mặc định là lỗi yêu cầu. Kết quả kiểm thử ngày 27–28/10 là kết quả lịch sử, không chứng minh bản code hiện tại đã nghiệm thu.

Tài liệu 03, M.5 quy định các nhánh quyết định trọng yếu; tài liệu 02–03 quy định hành vi; phần D tài liệu 04 quy định mô hình khái niệm; phần F/G quy định thiết kế vật lý. Mã `WAREHOUSE` tương ứng Bếp. Thiết kế vật lý dùng 37 bảng để ánh xạ 31 lớp nghiệp vụ; sáu bảng phụ trợ không tạo thêm vai trò hoặc chức năng kinh doanh. Những dòng “dev” bên dưới là công việc chưa được xác nhận hoàn tất trong lần biên tập tài liệu này.

| **Mục** | **Điểm đối chiếu** | **Kết luận và trách nhiệm** |
|---|---|---|
| 01 | 31/37 bảng | Tài liệu đã phân biệt 31 lớp nghiệp vụ và 37 bảng vật lý; bổ sung sáu bảng phụ trợ trong phần F và sơ đồ khóa theo nhóm. Không xóa bảng kỹ thuật để ép số lượng về 31. |
| 02 | Ngoại lệ thanh toán | Thuộc tính khái niệm được ánh xạ sang NGOAI_LE_THANH_TOAN; một giao dịch có thể có nhiều khoản ngoại lệ. Giữ FR-SALE-16–17, duy nhất mã khoản nhận và ghi doanh thu một lần. Dev kiểm chứng luồng áp dụng/hoàn ngoài hệ thống, không chỉ sự tồn tại của bảng. |
| 03 | Lịch Business Date | Chấp nhận bảng LICH_GIO_BUSINESS_DATE để hiện thực FR-SET-04; tài liệu phân biệt lịch lưu với thông tin mốc giờ chờ hiệu lực. Không thay đổi BusinessDate lịch sử. |
| 04 | MON_AN.HetNguyenLieu | Yêu cầu gốc là thuộc tính dẫn xuất, không lưu cột độc lập. Dev sửa nguồn tính trạng thái và migration phù hợp; không thay FR-CAT-27 thành dùng cờ lưu làm nguồn sự thật. |
| 05 | PHIEU_XUAT_KHO.NguonXuat | Giữ phân biệt ba nguồn Nguyên liệu / Món đã chế biến / Kiểm kê theo FR-INV-05. Dev bổ sung hoặc chứng minh ánh xạ lưu trữ bảo toàn được nguồn, truy vết và tính chi phí đúng một lần; hằng trong service chưa đủ bằng chứng. |
| 06 | Tên cột | Thiết kế dùng ORDER.NgayTao, PHIEU_NHAP_KHO.NguoiTao và CHI_TIET_KIEM_KE.MaChiTietKiemKe. Đây là thống nhất kỹ thuật, không đổi điều kiện nghiệp vụ. |
| 07 | Cột kỹ thuật chưa mô tả | Bổ sung phiên bản token, mốc đồng bộ, khu vực bàn, mã chống lặp, bản chụp hóa đơn, thông tin thử in, lý do kiểm kê, usage và phản hồi AI ở phần F. Dev kiểm chứng ý nghĩa và ràng buộc; không suy từ tên cột rằng tính năng đã đạt. |
| 08 | Kiểu dữ liệu | Mã vai trò VARCHAR(20); định danh thay thế BIGINT. Thiết kế tiền DECIMAL(18,2), lượng/hệ số DECIMAL(18,6), chi phí API DECIMAL(18,10), thời điểm DATETIME(3). Code hiện dùng DECIMAL(18,4) rộng rãi và độ chính xác thời gian khác; dev lập migration và kiểm tra làm tròn, dữ liệu hiện có, so sánh, tổng hợp. Không đổi hàng loạt mà bỏ kiểm tra mất độ chính xác. |
| 09 | Ngưỡng tồn riêng | NULL nghĩa là dùng mặc định; 0 là ngưỡng riêng hợp lệ theo yêu cầu không âm. Dev sửa quy ước 0=dùng mặc định nếu còn tồn tại; kiểm thử cả NULL, 0 và giá trị dương. |
| 10 | Trạng thái nghiệp vụ | Giữ vòng đời gốc của order và thanh toán. Phiếu nhập Hiệu lực/Đã hủy; kiểm kê Đang kiểm kê/Đã xác nhận/Đã hủy. Dev sửa hoặc ánh xạ giá trị nội bộ rõ ràng, không đưa thêm “Chờ đối soát”/“Tranh chấp” thành trạng thái nghiệp vụ mới. Trạng thái thử in chi tiết được mô tả riêng, không đồng nghĩa món đã chế biến. |
| 11 | Chi tiết giữ món | Thiết kế cho ON DELETE CASCADE từ chi tiết tới lượt giữ; các tham chiếu nghiệp vụ/lịch sử còn lại RESTRICT. Không xóa lượt giữ đã gửi để mất dấu chống gửi lặp. |
| 12 | Ràng buộc toàn vẹn | Giữ điều kiện số lượng dương, tồn không âm, phiên bản giá/công thức thuộc đúng món, điều kiện lô điều chỉnh và chống xử lý trùng khoản nhận. Giao dịch kho có một nguồn nghiệp vụ chính; liên kết bổ sung để truy vết không ghi lượng hai lần. PhamViDuLieu lưu danh sách view thực dùng. Dev đối chiếu và thêm ràng buộc còn thiếu bằng migration, kèm test MySQL. |
| 13 | FK nhật ký | Thiết kế quy định RESTRICT tường minh tới người dùng, định danh không đổi và nhật ký chỉ ghi thêm. Dev đối chiếu migration thực tế. |
| 14 | Đăng xuất | Bản nghiệp vụ gốc chỉ yêu cầu đăng xuất, chưa chốt thu hồi từng token ở máy chủ. Tài liệu mô tả đúng hiện trạng xóa thông tin đăng nhập trên trình duyệt. Không có endpoint logout trong Bảng 13; không tuyên bố đã thu hồi JWT. Nâng cấp thu hồi tức thời là quyết định bảo mật riêng, chưa mặc định nằm trong phạm vi đã chốt. |
| 15 | Xóa nhóm món | Dev giữ ba trường hợp: chưa từng có món → xóa vĩnh viễn; còn món chưa xóa mềm → từ chối; chỉ còn món xóa mềm → xóa mềm nhóm. Mọi thao tác xóa có audit. Code tại bản đối chiếu vẫn xóa mềm nhóm chưa từng có món. |
| 16 | Hợp đồng lỗi | Báo cáo mô tả cấu trúc error.code/message, error_id cho lỗi nội bộ, mã 422 cho vi phạm nghiệp vụ và thông báo hạn mức AI trong phản hồi. Không ép nghiệp vụ đổi chỉ vì lựa chọn mã HTTP. |
| 17 | Endpoint | Bảng 13 ghi một số endpoint có trong router; không trình bày URL chưa kiểm chứng là chức năng đã triển khai. |
| 18 | Dẫn chiếu phân quyền | Tài liệu 02 dẫn đúng Bảng 12 của báo cáo. |
| 19 | SePay | Báo cáo phân biệt khả năng cấu hình adapter mô phỏng/SePay với bằng chứng thử nghiệm. Kết quả Chương 6 dùng mô phỏng; kết quả tiền thật để trống khi chưa có hồ sơ. |
| 20 | Tự tính bình quân và sao lưu | Bình quân/giá vốn tự tính khi dữ liệu hiệu lực thay đổi; không có chốt giá tháng thủ công. Dev thay luồng phụ thuộc POST /inventory/costing/{month}/close bằng cập nhật tự động và bảo đảm tính lại kỳ cũ/mới cùng kỳ sau. Sao lưu/phục hồi thuộc NFR-11. |
| 21 | Tự động đóng | Luồng gốc không tự đóng order đang chờ xác minh theo thời gian; chỉ Quản lý đóng theo FR-SALE-35. Dev rà enum, prompt và truy vấn còn dùng trạng thái “Tự động đóng”; loại bỏ hoặc cô lập mã cũ, không đưa trạng thái đó trở lại báo cáo. |
| 22 | Chờ / Chờ làm | “Chờ làm” là trạng thái nghiệp vụ hiển thị. Nếu DB lưu “Chờ”, cần ánh xạ nhất quán ở API/UI và truy vấn; không coi hai nhãn là hai bước chế biến. |
| 23 | Bộ câu hỏi dev | Bảng 53 lấy từ questions.dev.jsonl: D001–D030; độ khó 8/10/12; vai trò 2 Quản lý, 13 Thu ngân và 15 Bếp. Bảng 51 dùng dải Q001–Q080 cho tập đánh giá. |
| 24 | Dẫn chiếu đánh giá | Thống nhất 6.4=thực nghiệm AI, 6.5=an toàn, 6.6=nghiệp vụ, 6.7=hiệu năng, 6.8=SUS/UAT. |
| 25 | Lỗi chấm AI | Có 31 lượt không đạt; nhãn lỗi gồm 27 nhận xét, 4 phạm vi/kỳ, 2 số liệu. Nhãn có thể chồng nhau, không cộng thành số lượt. |
| 26 | NFR-01 | Kết luận toàn tiêu chí là Chưa đạt cho đợt lịch sử: p95 đạt nhưng có lỗi kỹ thuật. Biên bản tải giữ số liệu gốc; dev chạy lại sau thay đổi pool trên cùng phiên bản nghiệm thu. |
| 27 | Người chấm | Hồ sơ ghi nhãn agent Claude Sonnet 5.5 chấm mù cấu hình; không đủ bằng chứng khẳng định ba người/agent độc lập. Không nhầm với ba agent kiểm tra chéo 20 SQL ở biên bản riêng. |
| 28 | Gói bằng chứng | Bỏ gán commit 68505dc cho đợt nghiệp vụ khi chưa chứng minh được nguồn chạy. Giữ số liệu lịch sử và để trống phiên bản/gói log ở bảng truy vết; cần chủ sở hữu bổ sung bằng chứng gốc. |
| 29 | Bộ test cũ | docs/testing/test-cases.md được đánh dấu bộ kỹ thuật lịch sử. Danh mục nghiệm thu hiện hành là tài liệu 06; không ánh xạ cùng mã TC sang hai nội dung khác nhau. |
| 30 | AGENTS.md | Dẫn yêu cầu hiện hành, nguồn nghiệp vụ gốc, đúng vai trò Bếp và quy tắc biên tập. Không dùng ngày báo cáo cũ làm nguồn chuẩn. |
| 31 | Ảnh không dùng | Chỉ ảnh còn được tài liệu dẫn được đưa vào gói tài liệu bàn giao. Dọn tài nguyên lịch sử trong repo là thao tác riêng, không làm điều kiện nghiệp vụ. |
| 32 | Biên bản kỹ thuật cũ | Giữ biên bản có ngày theo phạm vi lịch sử; số NFR cũ không thay thế mã trong báo cáo và tài liệu 06 hiện hành. |

## Trạng thái các thay đổi code đã đọc

- Nhãn giao diện Bếp đã đổi tại `8423b3f`; dữ liệu VAI_TRO đã tồn tại có thể còn tên cũ vì seed không cập nhật dòng cũ.
- Đã có code ghi audit khi giảm món và giữ nguyên/rút ngắn hạn giữ khi giảm số lượng; có test tương ứng trong repository. Lần biên tập tài liệu này không chạy lại các test đó.
- Xóa nhóm chưa từng có món, các ràng buộc/schema và các sai lệch khác không được tự đánh dấu đã sửa hoặc đã đạt.

## Điều kiện nghiệm thu

Dev thực hiện theo tài liệu nghiệp vụ đã chốt, ghi rõ migration và phiên bản chạy. Kiểm thử hồi quy sử dụng tài liệu 06, bao gồm ca trọng yếu và module Báo cáo. Các test phụ thuộc MySQL thật phải chạy trong môi trường có MySQL; báo cáo giới hạn môi trường riêng với lỗi sản phẩm. Kết quả cập nhật vào báo cáo chỉ khi có log, phiên bản và phạm vi tương ứng.

## Phụ lục đối chiếu cột và kiểu dữ liệu

Bảng dưới so sánh thiết kế phần F với khai báo ORM tại bản code đối chiếu, bao gồm các cột kế thừa từ mixin. Mũi tên chỉ từ code sang thiết kế. Đây là danh sách tĩnh để lập migration và kiểm thử, chưa phải kết quả kiểm tra CSDL đã triển khai. Ràng buộc, chỉ mục, giá trị trạng thái và dữ liệu đang có còn được kiểm tra riêng theo các mục 04–13.

| **Bảng** | **Sai khác cần dev xử lý/kiểm chứng** |
|---|---|
| NGUOI_DUNG | DATETIME → DATETIME(3): NgayTao |
| CAU_HINH_HE_THONG | DECIMAL(18,4) → DECIMAL(18,6): NguongTonMacDinh |
| NHAT_KY_HE_THONG | DATETIME → DATETIME(3): ThoiDiem |
| NHOM_MON | DATETIME → DATETIME(3): NgayXoa |
| MON_AN | Cột lưu trong code nhưng thiết kế suy ra: HetNguyenLieu; Cột lưu trong code nhưng thiết kế suy ra: TrangThai |
| LICH_SU_GIA_MON | DECIMAL(18,4) → DECIMAL(18,2): GiaBan; DATETIME → DATETIME(3): ThoiDiemHetHieuLuc, ThoiDiemHieuLuc, ThoiDiemTao |
| CONG_THUC | DATETIME → DATETIME(3): ThoiDiemHetHieuLuc, ThoiDiemHieuLuc, ThoiDiemTao |
| CHI_TIET_CONG_THUC | DECIMAL(18,4) → DECIMAL(18,6): DinhLuong |
| NGUYEN_LIEU | DECIMAL(18,4) → DECIMAL(18,6): MucTonToiThieu, SoLuongTon; Điều kiện rỗng: MucTonToiThieu → NULL |
| ORDER | DECIMAL(18,4) → DECIMAL(18,2): TongTien; DATETIME → DATETIME(3): NgayCapNhat, NgayTao, ThoiDiemDong |
| CHI_TIET_ORDER | DATETIME → DATETIME(3): ThoiDiemThem; BIGINT → INT: SoLuong; DECIMAL(18,4) → DECIMAL(18,2): DonGia, ThanhTien |
| LICH_SU_DOI_BAN | DATETIME → DATETIME(3): ThoiDiem |
| HOA_DON | DATETIME → DATETIME(3): ThoiDiemXuat; DECIMAL(18,4) → DECIMAL(18,2): TongTien |
| GIAO_DICH_THANH_TOAN | TEXT().with_variant(mysql.LONGTEXT(), 'mysql') → LONGTEXT: AnhChungTu; DATETIME → DATETIME(3): NgayTao, ThoiDiemHetHan, ThoiDiemTaoQR; DECIMAL(18,4) → DECIMAL(18,2): SoTien |
| PHIEU_BEP | DATETIME → DATETIME(3): HanKhoaIn, LanThuTiepTheo, NgayTao, ThoiDiemIn |
| PHIEU_NHAP_KHO | DATETIME → DATETIME(3): NgayNhap; DECIMAL(18,4) → DECIMAL(18,2): TongTien |
| CHI_TIET_PHIEU_NHAP | DECIMAL(18,4) → DECIMAL(18,6): HeSoQuyDoi, SoLuong; DECIMAL(18,4) → DECIMAL(18,2): DonGia, ThanhTien |
| LO_NGUYEN_LIEU | Cột lưu trong code nhưng thiết kế suy ra: TrangThai; DATETIME → DATETIME(3): NgayNhap; DECIMAL(18,4) → DECIMAL(18,2): DonGia; DECIMAL(18,4) → DECIMAL(18,6): SoLuongConLai, SoLuongNhap; Điều kiện rỗng: DonGia → NULL |
| PHIEU_XUAT_KHO | Cột chỉ có trong thiết kế: NguonXuat; DATETIME → DATETIME(3): NgayTao, NgayXuat |
| CHI_TIET_PHIEU_XUAT | DECIMAL(18,4) → DECIMAL(18,6): SoLuong; DECIMAL(18,4) → DECIMAL(18,2): GiaVonUocTinh; Điều kiện rỗng: GiaVonUocTinh → NULL |
| PHIEU_KIEM_KE | DATETIME → DATETIME(3): NgayKiemKe |
| CHI_TIET_KIEM_KE | DECIMAL(18,4) → DECIMAL(18,6): ChenhLech, TonHeThong, TonThucTe |
| GIAO_DICH_KHO | DECIMAL(18,4) → DECIMAL(18,6): SoLuongThayDoi, TonSauGiaoDich; DATETIME → DATETIME(3): ThoiDiem |
| GIA_BINH_QUAN_THANG | DECIMAL(18,4) → DECIMAL(18,2): DonGiaBinhQuan; DECIMAL(18,4) → DECIMAL(18,6): TongSoLuongNhap; DATETIME → DATETIME(3): ThoiDiemTinh |
| PHIEN_CHAT_AI | DATETIME → DATETIME(3): ThoiDiemBatDau, ThoiDiemKetThuc |
| TRUY_VAN_AI | VARCHAR(50) → JSON: PhamViDuLieu; DATETIME → DATETIME(3): ThoiDiem; Điều kiện rỗng: TokenDauRa → NULL, TokenDauVao → NULL |
| GIU_CHO_MON | DATETIME → DATETIME(3): NgayTao, ThoiDiemHetHan |
| CHI_TIET_GIU_CHO | DECIMAL(18,4) → DECIMAL(18,6): SoLuongGiu |
| LICH_GIO_BUSINESS_DATE | DATETIME → DATETIME(3): ThoiDiemBatDau |
| NGOAI_LE_THANH_TOAN | DECIMAL(18,4) → DECIMAL(18,2): SoTien, SoTienHoan; DATETIME → DATETIME(3): NgayTao, ThoiDiemXuLy |
| BO_NHO_DEM_SQL_AI | DATETIME → DATETIME(3): HetHanLuc |

## Rà ngữ nghĩa xuyên suốt

Đối chiếu các quy trình QT, FR/UC, trạng thái, thiết kế dữ liệu, SD và kỳ vọng kiểm thử cho các nhánh dưới. Đây là rà đặc tả, không phải kết quả chạy phần mềm.

| **Luồng** | **Kết luận thống nhất** | **Nguồn quyết định và kiểm thử** |
|---|---|---|
| Giữ món tại mốc hết hạn | Hết hạn giải phóng khả dụng; lúc gửi phải kiểm tra lại, không tự gia hạn | FR-SALE-05/08; FR-INV-10; SD-2.1a; TC-BR-01 |
| Mở kiểm kê khi chỉ còn giữ hết hạn | Lượt chọn chưa gửi/hủy vẫn chặn; nhân viên phải gửi hoặc hủy trước; không tự hủy khi mở kiểm kê | QT-17; FR-INV-08; SD-3.4; TC-INV-33; TC-BR-02/03 |
| Webhook muộn khi có QR mới | Tự xác nhận khoản cũ nếu đủ điều kiện; hủy QR mới chưa nhận tiền trong cùng transaction | FR-SALE-16; SD-2.5a; TC-BR-04 |
| Webhook sau quyết định mở lại | Mở lại của Quản lý khác tự về Đang mở khi QR hết hạn; chỉ Quản lý được áp dụng khoản ngoại lệ | FR-SALE-17/23; SD-2.6a; TC-BR-05 |
| Webhook lặp và xác nhận thủ công | Liên kết cùng khoản nhận, không thu hoặc ghi ngoại lệ hai lần | FR-SALE-15/16; TC-BR-06 |
| Phục vụ sau thanh toán | Khóa nội dung/tiền, vẫn cập nhật phục vụ cho dòng chưa hủy; bàn không tự trống | FR-SALE-09/22; FR-CAT-18; SD-2.3; TC-BR-07 |
| Bàn đã phục vụ order mới | Xử lý tiền order cũ không ảnh hưởng bàn/order mới; không gọi thêm hoặc đổi bàn order cũ | FR-CAT-18; TC-BR-08 |
| Xuất hủy món đã chế biến | Số suất và tiêu hao gốc; không trừ tồn hoặc cộng hao hụt hai lần | QT-16; FR-INV-05/06; SD-3.3; TC-BR-09 |
| Kiểm kê thiếu | Chỉ giao dịch điều chỉnh làm giảm tồn; phiếu xuất hủy là chứng từ tham chiếu | FR-INV-09; SD-3.4; TC-BR-10 |
| Tự tính giá vốn và giá trị 0 | Bình quân/giá vốn cập nhật tự động; giá trị chưa xác định là NULL, không coi là 0; cập nhật các kỳ phụ thuộc nhất quán | Tài liệu 04 G.1; TC-BR-11–18 |
| Hạn dùng theo ngày | Ngày lịch tại nhà hàng, dùng được hết ngày hạn; không dùng BusinessDate để kéo dài hạn qua nửa đêm | Tài liệu 04 BR-LOT-01; kiểm thử ranh giới ngày lịch |

## Quyết định nghiệp vụ được xác nhận

| **Mã** | **Quy tắc áp dụng** | **Công việc dev** |
|---|---|---|
| QD-01 | Bình quân, giá vốn và lợi nhuận tự cập nhật khi phiếu nhập thay đổi hợp lệ. Không chốt giá tháng thủ công hoặc khóa sửa chỉ vì đã tính bình quân. Sửa ngày sang tháng khác tính lại tháng cũ, tháng mới và các kỳ sau bị ảnh hưởng. | Giữ điều kiện lô chưa xuất/không giữ hiệu lực; cập nhật ngày lô, hạn dùng và FIFO; tính lại phụ thuộc, giữ lịch sử đính chính; không đổi hóa đơn/doanh thu. |
| QD-02 | Kiểm kê chỉ nhập số lượng và lý do. Thừa không tạo nhập mua hoặc yêu cầu nhập giá. Hệ thống tự định giá theo bình quân khi đủ căn cứ; chưa có giá vẫn ghi số lượng và để giá trị chưa xác định. | DonGia lô điều chỉnh và GiaVonUocTinh cho phép NULL khi thiếu căn cứ; phân biệt NULL với 0, không bỏ phần chưa định giá khỏi tổng rồi báo như tổng đầy đủ. |

Hai quyết định này được đồng bộ vào báo cáo, tài liệu 02/03/04/06 và các hình liên quan. Kiểm thử bổ sung TC-BR-13–18 mới là thiết kế, chưa có kết quả thực thi. Không đánh dấu code đã đáp ứng chỉ từ việc cập nhật tài liệu.
