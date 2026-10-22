# Review source so với docs — 21/10/2026

Kết luận: source hiện tại chưa đủ điều kiện nghiệm thu theo đặc tả trong `docs/BaoCao_HeThongQuanLyNhaHang.md`. Có lỗi ảnh hưởng dữ liệu bán hàng, giữ chỗ, kiểm kê, doanh thu và giá vốn, dù gate hiện tại xanh. Không có P0 được chứng minh trong đợt này.

Tổng hợp: **15 phát hiện P1**, **18 phát hiện P2**. P1 cần xử lý trước nghiệm thu; P2 là sai lệch chức năng/hợp đồng dữ liệu cần sửa hoặc thống nhất lại phạm vi docs.

## Phạm vi và phương pháp

- Đối chiếu báo cáo chính (FR, NFR, quy tắc dữ liệu), các kế hoạch và biên bản kiểm thử với API, web, model, migration/view và công cụ seed/eval của cả sáu module.
- Review working tree đang có nhiều thay đổi chưa commit, bao gồm phần thanh toán ngoại lệ và giao diện báo cáo/AI. Không sửa implementation hay test của dự án.
- Chạy `make gate`: exit code 0; ruff/prettier/eslint/mypy/tsc, 541 test API, 168 test web, production build đều qua. Có 20 test integration/slow bị loại theo cấu hình mặc định.
- Chạy 23 tình huống tái hiện độc lập trên SQLite in-memory bằng service thật; một ca số lượng âm được kiểm chứng thêm qua HTTP ASGI. Các exception trong tệp bằng chứng là triệu chứng lỗi được cố ý kích hoạt, không phải lỗi của gate.
- Chưa chạy kiểm thử tải/đồng thời trên MySQL thật, thiết bị/máy in vật lý, trình duyệt Safari/Edge hoặc API LLM thương mại. Không coi test SQLite là bằng chứng cho khóa dòng MySQL; không khẳng định review tĩnh chứng minh được mọi NFR.
- Một số hạn chế đã được docs/testing thừa nhận. Việc được ghi nhận là nợ kỹ thuật không làm chức năng đáp ứng FR nếu đặc tả chính vẫn yêu cầu.

Bằng chứng: [kết quả tái hiện](source-docs-review-2026-10-21-repro.json). Script sử dụng trong phiên: `/tmp/kltn_source_docs_repro.py`; log gate: `/tmp/kltn-review-gate.log`. Không thao tác ghi lên CSDL vận hành.

## Phát hiện

### R01 — P1 — API chấp nhận số lượng âm, tạo tổng tiền âm

- Source: [apps/api/src/app/modules/sales/router.py:276](../../apps/api/src/app/modules/sales/router.py#L276).
- Đối chiếu: FR-SALE-07; FR-INV-04.
- Bằng chứng/tác động: PATCH dòng món nhận payload dict thay vì UpdateLineIn và service không chặn quantity <= 0. Tái hiện qua HTTP: quantity=-3 trả 200, SoLuong=-3; order thành -150.000 đồng.
- Hướng xử lý: Kiểm tra đầu vào phải nằm ở API và service; dùng ràng buộc số lượng dương, giảm/xóa theo nghiệp vụ riêng.

### R02 — P1 — Tạo QR không khóa order và vẫn cho thanh toán tiền mặt

- Source: [apps/api/src/app/modules/sales/payments.py:142](../../apps/api/src/app/modules/sales/payments.py#L142).
- Đối chiếu: FR-SALE-14; FR-SALE-22.
- Bằng chứng/tác động: start_qr chỉ tạo giao dịch, không chuyển trạng thái order; order vẫn Đang mở. Đã tái hiện QR 50.000 đồng, sau đó sửa dòng thành 100.000 đồng; pay_cash cũng thành công trong khi QR cũ còn Chờ xác nhận.
- Hướng xử lý: Khóa order và kiểm tra lại dưới khóa khi tạo QR; thống nhất các nhánh sửa món, tiền mặt, hủy và hết hạn theo state machine trong docs.

### R03 — P1 — Đường gửi món không có hold lấy cả phần nguyên liệu đã giữ và lô quá hạn

- Source: [apps/api/src/app/modules/inventory/stock.py:48](../../apps/api/src/app/modules/inventory/stock.py#L48).
- Đối chiếu: NFR-08; FR-INV-03/10/13; BR-LOT-01.
- Bằng chứng/tác động: Submit và add_line vẫn cho bỏ hold_id. FIFO lấy quantity_remaining mà không trừ giữ chỗ, chỉ lọc cờ TrangThai thay vì kiểm tra expiry_date: giữ 18 trên tồn 20 rồi gửi trực tiếp 5 vẫn thành công; lô hết hạn hôm trước nhưng cờ Còn hạn vẫn bị bán.
- Hướng xử lý: Mọi đường tiêu hao phải dùng cùng một quy tắc khả dụng theo hold và hạn sử dụng thực tế; không cho endpoint cũ vượt qua quy tắc mới.

### R04 — P1 — Phiên kiểm kê không cô lập giữ chỗ và tiêu hao qua hold

- Source: [apps/api/src/app/modules/sales/reservations.py:157](../../apps/api/src/app/modules/sales/reservations.py#L157).
- Đối chiếu: FR-INV-08; NFR-20.
- Bằng chứng/tác động: create_hold/update_hold/consume_hold không gọi ensure_no_open_stocktake. create_stocktake cũng không kiểm tra giữ chỗ và món chưa xử lý: đã mở phiên Nháp, tạo hold rồi gửi món, tồn từ 20 xuống 18 ngay trong phiên.
- Hướng xử lý: Áp dụng một cơ chế khóa nghiệp vụ chung trong transaction cho mọi nhánh nhập/xuất/giữ/hoàn; kiểm tra điều kiện trước khi mở phiên.

### R05 — P1 — Hủy phiếu nhập đã sử dụng một phần và sửa/hủy lô đang giữ vẫn được phép

- Source: [apps/api/src/app/modules/inventory/service.py:140](../../apps/api/src/app/modules/inventory/service.py#L140).
- Đối chiếu: FR-INV-02.
- Bằng chứng/tác động: cancel_receipt chỉ chặn khi lô đã dùng hết, vẫn hủy phần còn lại của phiếu đã xuất một phần. Đã bán một suất từ lô 20, sau đó hủy phiếu thành công và tồn còn 0; cả update_receipt lẫn cancel_receipt không kiểm tra giữ chỗ còn hiệu lực.
- Hướng xử lý: Phiếu có bất kỳ giao dịch xuất hoặc giữ chỗ hợp lệ phải bị chặn sửa/hủy; kiểm tra lịch sử giao dịch, không chỉ so sánh số tồn hiện tại.

### R06 — P1 — Chưa có idempotency cho yêu cầu gửi món

- Source: [apps/api/src/app/modules/sales/schemas.py:24](../../apps/api/src/app/modules/sales/schemas.py#L24).
- Đối chiếu: FR-SALE-03; NFR-08.
- Bằng chứng/tác động: SubmitOrderIn không nhận mã yêu cầu gửi, router không truyền mã xuống service; Reservation.request_id/request_line_id không được gán. Gửi hai lần cùng mã ở payload cho đơn mang về tạo hai order 1 và 2, trừ tồn hai lần.
- Hướng xử lý: Mã yêu cầu cần ràng buộc duy nhất và trả lại kết quả cũ sau retry; áp dụng cho cả lượt gửi đầu và gọi thêm.

### R07 — P1 — Gửi danh sách món vẫn ghi nhận một phần

- Source: [apps/api/src/app/modules/sales/orders.py:371](../../apps/api/src/app/modules/sales/orders.py#L371).
- Đối chiếu: FR-SALE-03; FR-SALE-05; NFR-10.
- Bằng chứng/tác động: Service bắt lỗi từng dòng rồi trả created_lines cùng rejected và router commit. Tái hiện danh sách một món hợp lệ, một món không tồn tại: nhận một dòng, loại một dòng và đã trừ tồn; frontend còn xóa toàn bộ cart sau cảnh báo. Gọi thêm ở order-step.tsx:302 gửi từng dòng bằng nhiều request nên cũng không nguyên tử.
- Hướng xử lý: Toàn bộ lượt gửi đã xác nhận phải thành công hoặc rollback; giữ nguyên danh sách và trình bày lỗi từng món để nhân viên trao đổi với khách.

### R08 — P1 — Gửi hold dùng giá/công thức cũ mà không xác nhận thay đổi

- Source: [apps/api/src/app/modules/sales/orders.py:337](../../apps/api/src/app/modules/sales/orders.py#L337).
- Đối chiếu: FR-SALE-03/05; FR-CAT-20/23/25.
- Bằng chứng/tác động: Nhánh hold chỉ đọc price_version_id/recipe_id đã lưu, không so với phiên bản hiện hành và không yêu cầu xác nhận nội dung mới. Đã giữ giá 50.000 đồng, sửa giá trực tiếp lên 99.000 đồng, gửi hold vẫn tính 50.000 đồng; add_line dùng cùng cách.
- Hướng xử lý: Kiểm tra phiên bản lúc gửi; khi thay đổi phải trả nội dung mới để xác nhận và phân bổ lại công thức trong cùng transaction.

### R09 — P1 — Backend vẫn nhận món đã xóa hoặc bị chặn phục vụ

- Source: [apps/api/src/app/modules/sales/reservations.py:172](../../apps/api/src/app/modules/sales/reservations.py#L172).
- Đối chiếu: FR-CAT-04/26/27; FR-SALE-03.
- Bằng chứng/tác động: create_hold chỉ lấy giá/công thức và tồn, không kiểm tra Dish.is_deleted hoặc trạng thái phục vụ; _resolve_line_inputs của đường trực tiếp cũng thiếu kiểm tra. Đã đặt is_deleted=True, tạo hold và gửi order thành công.
- Hướng xử lý: Dùng một kiểm tra trạng thái món chung cho tạo hold, tăng giữ chỗ, gửi mới và gọi thêm; không phụ thuộc bộ lọc của frontend.

### R10 — P1 — Hủy một dòng trong order có ba dòng gây lỗi 500

- Source: [apps/api/src/app/modules/sales/orders.py:557](../../apps/api/src/app/modules/sales/orders.py#L557).
- Đối chiếu: FR-SALE-10.
- Bằng chứng/tác động: Sau hủy, truy vấn tất cả dòng còn lại nhưng gọi scalar_one_or_none(). Với hai dòng còn lại, SQLAlchemy ném MultipleResultsFound; đã tái hiện trực tiếp.
- Hướng xử lý: Dùng phép kiểm tra tồn tại hoặc giới hạn một dòng; bảo đảm rollback và hoàn kho không bị ghi nhận dở dang.

### R11 — P1 — Tiền chưa xác minh bị cộng vào doanh thu

- Source: [apps/api/src/app/modules/reports/queries.py:251](../../apps/api/src/app/modules/reports/queries.py#L251).
- Đối chiếu: FR-REP-02; FR-REP-04.
- Bằng chứng/tác động: total=invoices_total + pending - disputed; pending gồm Chờ xác minh thanh toán, và revenue_by_period cũng cộng nhóm này. Order chưa có hóa đơn 50.000 đồng đã làm doanh thu tăng 50.000 đồng trong tái hiện.
- Hướng xử lý: Doanh thu chỉ ghi nhận khoản thành công; tách số tiền chờ xử lý ra chỉ tiêu riêng và loại phép khấu trừ tranh chấp chưa có doanh thu gốc.

### R12 — P1 — Business Date của hóa đơn/thanh toán lệch order

- Source: [apps/api/src/app/modules/sales/payments.py:125](../../apps/api/src/app/modules/sales/payments.py#L125).
- Đối chiếu: FR-REP-02/05a; quy tắc Business Date tại báo cáo dòng 1275.
- Bằng chứng/tác động: pay_cash và start_qr tính Business Date theo lúc thanh toán thay vì kế thừa order. Tái hiện order ngày 24/09, trả tiền ngày 25/09 thì hóa đơn ở 25/09; báo cáo giá vốn lại lọc ORDER.BusinessDate, làm doanh thu và chi phí lệch kỳ.
- Hướng xử lý: Thanh toán/hóa đơn kế thừa ORDER.BusinessDate; giao dịch kho dùng ngày biến động thực tế. Nhánh gọi thêm cũng đang truyền order.business_date vào tiêu hao thay vì ngày phát sinh.

### R13 — P1 — Tiêu hao order hủy bị mất khỏi giá vốn; tổng giá vốn bỏ khoản 05c

- Source: [apps/api/src/app/modules/sales/orders.py:660](../../apps/api/src/app/modules/sales/orders.py#L660).
- Đối chiếu: FR-SALE-28; FR-REP-04/05c/10.
- Bằng chứng/tác động: cancel_order đổi mọi dòng sang Đã hủy, kể cả món đã chế biến không hoàn kho; exceptional_order_costs lại loại chính các dòng này. Tái hiện mất một đơn vị nguyên liệu nhưng báo cáo hủy ghi GiaVon=0. Ngoài ra queries.py:562 chỉ cộng 05a + 05b, bỏ toàn bộ 05c kể cả order đóng chưa thu tiền.
- Hướng xử lý: Giữ được căn cứ tiêu hao thực của dòng hủy và tổng hợp 05c vào tổng giá vốn/lợi nhuận; tránh lấy trạng thái hủy làm đồng nghĩa với đã hoàn kho.

### R14 — P1 — Đơn giá bình quân không tính tồn đầu kỳ và không kế thừa kỳ trước

- Source: [apps/api/src/app/modules/inventory/costing.py:18](../../apps/api/src/app/modules/inventory/costing.py#L18).
- Đối chiếu: FR-REP-05a.
- Bằng chứng/tác động: close_month chỉ chia tổng tiền nhập tháng cho lượng nhập tháng, bỏ giá trị/lượng tồn đầu kỳ; tháng không nhập không sinh MonthlyAverageCost. Đã tái hiện tháng kế tiếp không nhập trả 0 dòng chi phí; báo cáo inner join giá bình quân có thể bỏ hẳn nguyên liệu đã tiêu hao mà không báo thiếu giá vốn.
- Hướng xử lý: Tính bình quân trên tồn đầu kỳ cộng nhập; kế thừa giá kỳ gần nhất khi không nhập và đánh dấu tạm tính khi còn thiếu dữ liệu giá.

### R15 — P1 — Trang audit có thể lỗi khi gặp thao tác tự động của webhook

- Source: [apps/api/src/app/modules/settings/schemas.py:96](../../apps/api/src/app/modules/settings/schemas.py#L96).
- Đối chiếu: FR-SET-09.
- Bằng chứng/tác động: SystemAuditLog.user_id cho phép NULL và payments tạo nhiều log user_id=None. AuditEntryOut.MaNguoiDung lại bắt buộc int; model_validate đã ném ValidationError với log hệ thống hợp lệ, làm endpoint danh sách hỏng nếu trang chứa dòng đó.
- Hướng xử lý: Hợp đồng API/UI phải hỗ trợ tác nhân hệ thống; không loại bỏ nhật ký tự động để né lỗi.

### R16 — P2 — Hold hết hạn không có đường kiểm tra lại và gửi theo đặc tả

- Source: [apps/api/src/app/modules/sales/reservations.py:232](../../apps/api/src/app/modules/sales/reservations.py#L232).
- Đối chiếu: FR-SALE-05.
- Bằng chứng/tác động: _owned_active từ chối hold hết hạn ngay trước khi kiểm tra tồn/phiên bản; đã tái hiện tồn vẫn đủ nhưng gửi bị báo Không có món nào đủ tồn kho. list_holds còn loại hold hết hạn, frontend không giữ expires_at/trạng thái để hiển thị nhãn và xác nhận lại.
- Hướng xử lý: Giữ dòng món hết hạn trong lượt chọn, kiểm tra lại lúc gửi và yêu cầu xác nhận thay đổi; không tự gia hạn ngầm.

### R17 — P2 — Thanh toán và giải phóng bàn bỏ qua vòng đời lượt chọn chưa gửi

- Source: [apps/api/src/app/modules/sales/floor.py:95](../../apps/api/src/app/modules/sales/floor.py#L95).
- Đối chiếu: FR-CAT-18; FR-SALE-11/13.
- Bằng chứng/tác động: release_table chỉ xóa pointer của bàn; pay_cash/start_qr không kiểm tra các lượt gọi thêm chưa xử lý. Đã tái hiện giải phóng bàn nhưng hold vẫn Đang giữ; cũng thanh toán được khi còn hold gắn order, sau đó hold tiếp tục chiếm tồn. Hủy/đóng order không giải phóng hold tương ứng.
- Hướng xử lý: Backend bắt xử lý hết lượt chọn trước thanh toán; giải phóng các lượt chọn khi giải phóng bàn hoặc kết thúc order theo đúng quy tắc.

### R18 — P2 — Hủy order tự giải phóng bàn dù chưa xác nhận khách rời đi

- Source: [apps/api/src/app/modules/sales/orders.py:664](../../apps/api/src/app/modules/sales/orders.py#L664).
- Đối chiếu: FR-CAT-18; FR-SALE-11/30.
- Bằng chứng/tác động: cancel_order và nhánh tự đóng trong cancel_line gọi _free_table vô điều kiện. Tái hiện hủy order chuyển bàn về Trống ngay, không có đầu vào xác nhận khách đã rời đi.
- Hướng xử lý: Tách kết quả tài chính/order khỏi việc khách còn sử dụng bàn; chỉ giải phóng khi có xác nhận phù hợp.

### R19 — P2 — Cờ tạm dừng thủ công bị phép tính tồn kho ghi đè

- Source: [apps/api/src/app/modules/catalog/service.py:949](../../apps/api/src/app/modules/catalog/service.py#L949).
- Đối chiếu: FR-CAT-26/27.
- Bằng chứng/tác động: set_manual_out_of_stock ghi trực tiếp HetNguyenLieu; model không có TamDungThuCong độc lập. recompute_automatic_out_of_stock ghi lại cùng trường theo tồn sổ sách: tái hiện tạm dừng=True rồi tính lại tồn thành False.
- Hướng xử lý: Thêm trạng thái thủ công độc lập với khả dụng dẫn xuất và hiển thị đồng thời nguyên nhân chặn theo docs.

### R20 — P2 — Phiếu xuất hủy chưa hỗ trợ nguồn và chọn lô

- Source: [apps/api/src/app/modules/inventory/schemas.py:43](../../apps/api/src/app/modules/inventory/schemas.py#L43).
- Đối chiếu: FR-INV-05/06; BR-LOT-01.
- Bằng chứng/tác động: IssueCreate chỉ có reason và ingredient_id/quantity; create_issue luôn trừ FIFO. Không có đầu vào chọn lô, nguồn Món đã chế biến hoặc số suất/dòng order, và không giải phóng hold bị ảnh hưởng; dùng nội dung lý do có chữ hết hạn để cho phép FIFO chọn lô quá hạn.
- Hướng xử lý: Cần mô hình nguồn chứng từ và phân bổ lô rõ ràng; nguồn món đã chế biến/kiểm kê chỉ phân loại giao dịch gốc, không trừ lại.

### R21 — P2 — Cảnh báo hạn dùng chưa được triển khai trên màn hình kho

- Source: [apps/api/src/app/modules/inventory/service.py:633](../../apps/api/src/app/modules/inventory/service.py#L633).
- Đối chiếu: FR-INV-14; FR-SET-04.
- Bằng chứng/tác động: list_stock/StockTable chỉ có cảnh báo tồn tối thiểu, không có danh sách/cảnh báo lô gần hết hạn; expiry_warning_days chỉ được cấu hình/lưu, không tham gia tính trạng thái lô. Lô khởi tạo Còn hạn không có tác vụ chung đổi trạng thái theo thời gian.
- Hướng xử lý: Tính trạng thái theo hạn dùng hiện tại và ngưỡng cấu hình, trả về API để Bếp nhìn thấy cảnh báo riêng trên màn hình Kho.

### R22 — P2 — Phiên kiểm kê bị kẹt sau reload và không có thao tác hủy

- Source: [apps/web/src/features/inventory/stocktake-panel.tsx:242](../../apps/web/src/features/inventory/stocktake-panel.tsx#L242).
- Đối chiếu: FR-INV-08; NFR-20.
- Bằng chứng/tác động: draftId chỉ lưu trong useState, lịch sử chỉ hiển thị và không khôi phục phiếu Nháp để nhập/chốt; router không có endpoint hủy phiên. Reload sau Tạo phiếu khiến lần tạo tiếp bị từ chối và các nghiệp vụ có kiểm tra khóa kho bị chặn.
- Hướng xử lý: Cho tiếp tục phiếu đang mở từ server và hủy phiên có kiểm soát; tính tới tab đóng, tải lại và trường hợp chưa có nguyên liệu.

### R23 — P2 — In lại hóa đơn không bảo toàn nội dung đã phát hành

- Source: [apps/api/src/app/modules/sales/router.py:714](../../apps/api/src/app/modules/sales/router.py#L714).
- Đối chiếu: FR-SALE-21/26.
- Bằng chứng/tác động: _invoice_payload đọc tên món, thông tin nhà hàng và giao dịch mới nhất ở hiện tại thay vì bản chụp gốc/giao dịch invoice tham chiếu. Tái hiện đổi tên món sau thanh toán làm tên trên hóa đơn in lại thay đổi; giao dịch QR mới hơn giao dịch thực nhận cũng có thể khiến phương thức hiển thị sai.
- Hướng xử lý: Lưu đủ bản chụp nội dung hóa đơn và dùng payment_transaction_id của hóa đơn khi đọc/in lại.

### R24 — P2 — Chưa có in tạm tính và thao tác in phiếu bếp thực sự

- Source: [apps/api/src/app/modules/sales/router.py:383](../../apps/api/src/app/modules/sales/router.py#L383).
- Đối chiếu: FR-SALE-21/31/32.
- Bằng chứng/tác động: Nhánh reprint phiếu bếp chỉ record_print_result(ticket, True), không gửi lệnh in; frontend gọi endpoint rồi hiện toast đã gửi in. Chỉ tìm thấy window.print cho hóa đơn, không có luồng phiếu tạm tính mang nhãn CHƯA THANH TOÁN trước khi chọn phương thức.
- Hướng xử lý: Triển khai đầu ra in và phản hồi lỗi thực; tách phiếu tạm tính khỏi hóa đơn đã phát hành. Nếu chỉ mô phỏng, phải thu hẹp tuyên bố đáp ứng FR tương ứng.

### R25 — P2 — Prompt AI hiểu sai hôm nay trước 06:00

- Source: [apps/api/src/app/modules/ai/pipeline/prompt.py:177](../../apps/api/src/app/modules/ai/pipeline/prompt.py#L177).
- Đối chiếu: Business Date; FR-AI-02/03.
- Bằng chứng/tác động: Prompt chỉ dẫn hôm nay là BusinessDate = CURDATE(). Trong khoảng 00:00–05:59, ngày kinh doanh hiện tại phải là ngày trước; nhiều SQL chuẩn cũng dùng CURDATE nên cả mô hình và bộ chuẩn có thể đồng thuận trên kết quả sai.
- Hướng xử lý: Cấp ngày kinh doanh hiện tại từ helper backend vào prompt và chuẩn hóa ngày tương đối nhất quán trong SQL chuẩn.

### R26 — P2 — SQL chuẩn lợi nhuận Q051 không đúng công thức trong báo cáo

- Source: [data/eval/questions.jsonl:51](../../data/eval/questions.jsonl#L51).
- Đối chiếu: FR-REP-04/05a/05b/05c; phương pháp đánh giá §5.2.
- Bằng chứng/tác động: Q051 chỉ lấy doanh thu trừ tổng giao dịch Trừ tự động nhân giá bình quân; bỏ Hoàn kho, Xuất thủ công và Điều chỉnh kiểm kê âm, đồng thời tính cả order còn mở chưa thuộc 05a/05c. Chỉ cần trừ một suất rồi hủy và hoàn đủ, gold vẫn tính giá vốn suất đó.
- Hướng xử lý: Xây SQL chuẩn từ cùng định nghĩa nghiệp vụ đã chốt và bổ sung ca dữ liệu phân biệt hoàn kho/hao hụt/order chưa kết thúc; audit chạy được SQL không chứng minh gold đúng.

### R27 — P2 — Harness đánh giá chưa đo câu trả lời và độ trễ đầu-cuối theo docs

- Source: [data/eval/harness.py:209](../../data/eval/harness.py#L209).
- Đối chiếu: MT5; NFR-02; §5.2.
- Bằng chứng/tác động: _run chỉ sinh SQL một lần rồi thực thi SQL sinh và SQL chuẩn, không chạy interpreter hoặc chấm nhận xét; latency còn bao gồm thực thi câu chuẩn. CLI mỗi cấu hình chỉ chạy một lượt, không có 3 lần/câu, p95, usage/chi phí hay độ đúng câu trả lời như phương pháp đã nêu.
- Hướng xử lý: Hoàn thiện harness hoặc giới hạn rõ kết quả là benchmark thực thi SQL; kết quả hiện tại không đủ để chứng minh p95 AI hay độ đúng diễn giải. Báo cáo đã thừa nhận kết quả cũ chưa chứng minh các tiêu chí này.

### R28 — P2 — Audit thiếu dữ liệu trước/sau và nội dung đối soát cần tra cứu

- Source: [apps/api/src/app/modules/sales/payments.py:968](../../apps/api/src/app/modules/sales/payments.py#L968).
- Đối chiếu: FR-SALE-19/20/34; FR-SET-08/09.
- Bằng chứng/tác động: record_bank_reference cập nhật reference/evidence nhưng log chỉ ghi loại thao tác và ID; resolve_reconciliation chỉ ghi ketQua. Nhiều thao tác cấu hình/danh mục cũng ghi log không có before/after; ghi đè lịch giá/công thức còn xóa bản lịch cũ mà log mới không lưu giá trị bị ghi đè.
- Hướng xử lý: Ghi đầy đủ giá trị trước/sau, bằng chứng, nội dung và kết quả ở từng thao tác rủi ro; bảo đảm tái dựng được quyết định sau khi bản hiện hành đổi.

### R29 — P2 — Cấu hình mốc Business Date mới chỉ có trường lưu, chưa có chức năng áp dụng

- Source: [apps/api/src/app/modules/settings/schemas.py:75](../../apps/api/src/app/modules/settings/schemas.py#L75).
- Đối chiếu: FR-SET-04.
- Bằng chứng/tác động: ConfigUpdate không có GioBatDauBusinessDate, service chú thích bỏ qua trường này, helper luôn dùng mặc định 06:00 và không có lịch hiệu lực cấu hình. Vì vậy yêu cầu thay đổi từ Business Date kế tiếp trong docs chưa thực hiện.
- Hướng xử lý: Bổ sung lịch hiệu lực và truyền cấu hình thống nhất qua helper, hoặc chỉnh phạm vi docs nếu MVP cố định 06:00.

### R30 — P2 — Bản sao lưu bỏ mất dữ liệu xác thực cần để phục hồi

- Source: [apps/api/src/app/modules/settings/service.py:360](../../apps/api/src/app/modules/settings/service.py#L360).
- Đối chiếu: FR-SET-06; NFR-09.
- Bằng chứng/tác động: export_backup bỏ NGUOI_DUNG.MatKhauHash trong khi cột này NOT NULL và không có mặc định. Bản xuất không tự chứa đủ dữ liệu để phục hồi bảng tài khoản và đăng nhập như trước sự cố; manifest chỉ liệt kê trường bỏ đi, không cung cấp thủ tục khôi phục phần thiếu.
- Hướng xử lý: Dùng bản sao lưu đầy đủ được bảo vệ phù hợp, hoặc định nghĩa rõ bản xuất dữ liệu và quy trình khôi phục tài khoản riêng; kiểm chứng phục hồi trên CSDL rỗng.

### R31 — P2 — Lịch sử AI không tách theo vai trò hiện tại

- Source: [apps/api/src/app/modules/ai/service.py:288](../../apps/api/src/app/modules/ai/service.py#L288).
- Đối chiếu: FR-AI-01/05; FR-SET-03.
- Bằng chứng/tác động: ChatSession tạo role_id=None; API lịch sử chỉ truyền user_id và không lọc phạm vi/role. Tài khoản từng là Quản lý sau khi đổi sang Bếp vẫn đọc lại bản tóm tắt doanh thu/lợi nhuận cũ qua endpoint lịch sử, dù truy vấn mới đã bị giới hạn đúng view.
- Hướng xử lý: Lưu vai trò tại thời điểm chat và xác định chính sách đọc lịch sử theo quyền hiện tại; không để endpoint lịch sử bỏ qua phạm vi dữ liệu.

### R32 — P2 — Order mở lại thanh toán biến mất khỏi danh sách khoản chưa thu

- Source: [apps/api/src/app/modules/reports/queries.py:779](../../apps/api/src/app/modules/reports/queries.py#L779).
- Đối chiếu: FR-REP-02; FR-SALE-23.
- Bằng chứng/tác động: reopen_payment chuyển giao dịch cũ sang Đã hủy, order về Đang mở; pending_payments chỉ chọn trạng thái chờ/tranh chấp, không chọn giao dịch Đã hủy gắn lịch sử xác minh. Vì vậy order vừa mở lại không còn trong danh sách theo dõi nếu chưa tạo giao dịch mới.
- Hướng xử lý: Theo dõi khoản chưa thu ở mức order và lịch sử xử lý, thay vì chỉ lọc trạng thái giao dịch hiện tại.

### R33 — P2 — Hạn mức câu hỏi đang đếm lần sinh SQL, bỏ qua cache hit

- Source: [apps/api/src/app/modules/ai/pipeline/generator.py:91](../../apps/api/src/app/modules/ai/pipeline/generator.py#L91).
- Đối chiếu: FR-AI-10; FR-SET-04; NFR-16.
- Bằng chứng/tác động: reserve_call nằm trong vòng lặp retry nên một câu có thể mất hai lượt; cache hit trả trước reserve_call nên không tính câu hỏi nào. Interpreter vẫn gọi LLM cho cache hit, vì vậy hạn mức câu hỏi không chặn được các lần diễn giải phát sinh chi phí.
- Hướng xử lý: Tách hạn mức câu hỏi/người/ngày khỏi bộ đếm gọi provider; thống nhất định nghĩa giữa cấu hình, thông báo và kiểm thử.

## Thứ tự xử lý đề nghị

1. Chặn số lượng âm; thống nhất state machine QR/order; chặn mọi đường tiêu hao vượt giữ chỗ hoặc phiên kiểm kê.
2. Sửa idempotency, giao dịch gửi món nguyên tử, kiểm tra trạng thái món và phiên bản khi gửi; bổ sung test theo FR thay vì chấp nhận hành vi hiện có.
3. Sửa định nghĩa doanh thu, Business Date, giá bình quân và giá vốn 05a/05b/05c; xây bộ số liệu nhỏ có tổng tiền/tồn/giá vốn tính tay để đối chiếu cả API lẫn gold AI.
4. Hoàn thiện vòng đời giữ chỗ/kiểm kê/phiếu xuất hủy, audit và nội dung in; kiểm chứng phục hồi backup.
5. Chốt lại phạm vi MVP còn thiếu trong docs, rồi chạy MySQL concurrency, benchmark đầu-cuối AI và nghiệm thu UI/thiết bị.

## Khoảng trống cần kiểm chứng thêm

- `resolve_reconciliation` và các thao tác sửa/hủy dòng đọc order/payment/ingredient mà chưa có khóa/refresh nhất quán. Unique invoice có thể ngăn tạo trùng hóa đơn nhưng không chứng minh toàn bộ luồng cạnh tranh hợp lệ; cần ca xác nhận đối soát cạnh tranh với mở lại/tiền mặt và hoàn kho đồng thời.
- `create_stocktake` dùng kiểm tra tồn tại rồi insert; cần kiểm chứng hai lần mở phiên đồng thời và ghi kho đang chạy khi phiên được mở.
- Khóa tài khoản/đổi vai trò được kiểm tra lại từ CSDL khi môi trường khác local; local vẫn tin role trong JWT. Không dùng kết quả kiểm thử local để kết luận NFR-19 đã được chứng minh trên triển khai.
- `compare_periods` lấy giá vốn theo toàn bộ `month_key` ngay cả khi khoảng chọn là ngày/tuần; cần chốt cách so sánh chi phí khi kỳ không phải tháng (FR-REP-08).
- Danh sách món quản trị đang loại mọi món xóa mềm (`catalog/service.py:172`), trong khi FR-CAT-04 yêu cầu vẫn tra cứu được trong danh mục quản trị.

Không đề xuất đổi docs để hợp thức hóa các lỗi sai tiền/tồn. Những chức năng thật sự chưa nằm trong MVP cần được đánh dấu rõ, còn các bất biến giao dịch và tài chính phải được thực hiện đúng.
