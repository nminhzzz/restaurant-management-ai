# Bàn giao dev: giảm tải màn gọi món (28/11/2026)

## Mục tiêu

Sau góp ý của giảng viên phản biện, chuyển việc tính số suất khả dụng sang lúc dữ liệu kho hoặc lượt giữ thay đổi. Màn gọi món đọc số đã lưu. Khi nhập kho hoặc chọn, giảm, bỏ món, chỉ cập nhật các món dùng nguyên liệu bị ảnh hưởng. Giữ nguyên kiểm tra và phân bổ tồn theo lô trong giao dịch giữ món.

## Hiện trạng và số đo trước sửa

- Frontend: [order-step.tsx](../apps/web/src/features/sales/order-step.tsx), hàm `loadMenu`. Mỗi lần giỏ đổi và mỗi 5 giây khi tab hiển thị, web tải lại bàn, nhóm món, thực đơn và chi tiết đơn nếu đang mở đơn có sẵn.
- Backend: [catalog/router.py](../apps/api/src/app/modules/catalog/router.py), API `GET /catalog/dishes`. Số suất đã được tính theo lô cho cả trang thực đơn qua `available_portions_for_dishes`, nhưng API còn tính trạng thái và xử lý phiên bản hiệu lực theo từng món.
- Mốc trước sửa ở commit `3036a30`: một lượt đo API trên Windows, MySQL thử riêng, 30 món, 20 phiên thu ngân đồng thời trong khoảng 60 giây. Kịch bản mô phỏng mở màn, chọn, bỏ hoặc gửi món và tải định kỳ.

| Chỉ số | Trước sửa |
| --- | ---: |
| Tổng request, lỗi HTTP hoặc timeout | 927 request, 0 lỗi |
| Tổng câu SQL | 61.398 |
| API thực đơn | 259 lượt, 219 câu SQL/lượt, chiếm 92,4% tổng câu SQL |
| p95 API giữ món | 6,76 giây |
| p95 từ chọn món đến khi tải lại xong | 12,42 giây |

Đây là số đo trước sửa của kịch bản riêng này, chưa đo thời gian render giao diện. Tỷ lệ giảm thực tế sẽ lấy từ lượt đo sau sửa, tính cả truy vấn phát sinh để cập nhật số suất.

## Dữ liệu và quy tắc tính

- Tồn khả dụng của nguyên liệu là tổng lượng còn dùng được trên các lô sau khi trừ lượng đang giữ còn hiệu lực theo từng lô. Dùng cùng điều kiện lô hợp lệ, hạn dùng, công thức hiệu lực và Business Date như luồng giữ món hiện tại. Tái sử dụng logic tại [sales/reservations.py](../apps/api/src/app/modules/sales/reservations.py).
- Số suất khả dụng của một món là giá trị nhỏ nhất của `floor(tồn khả dụng / định lượng cho một suất)` trong các nguyên liệu của công thức đang áp dụng. Món thiếu công thức giữ quy tắc trạng thái hiện tại. Số suất lưu theo món phục vụ hiển thị. Tồn theo lô và lượt giữ vẫn quyết định yêu cầu giữ có thành công.
- Khi nguyên liệu thay đổi, tìm tất cả món có công thức đang áp dụng dùng nguyên liệu đó, khử trùng mã món rồi tính theo lô cho tập món này. Khi đổi công thức hoặc công thức hẹn trước đến ngày hiệu lực, tính lại món tương ứng. Phần giá và trạng thái món phải phản ánh đúng phiên bản hiệu lực, kể cả khi tách bước kích hoạt phiên bản khỏi API làm mới số suất.
- Khi nhả lượt giữ, dùng lượng đã ghi theo lô từ lúc giữ. Khi gửi món thành công, trừ tồn và kết thúc giữ trong cùng giao dịch. Nếu hai lượng bằng nhau theo từng lô thì khả dụng giữ nguyên, không trừ số suất thêm lần nữa.
- Tính và lưu số suất cho dữ liệu hiện có trước khi chuyển màn gọi món sang đọc số đã lưu. Cập nhật số suất từ dữ liệu đã nhất quán sau giao dịch. Xử lý đồng thời để một lần tính cũ không ghi đè kết quả mới. Nếu bước cập nhật sau giao dịch lỗi, cần có cơ chế tính lại và khôi phục sau khởi động lại.

## Bảng đọc và ghi theo thao tác

| Thao tác | Đọc | Ghi |
| --- | --- | --- |
| Mở màn gọi món | Thực đơn, giá, trạng thái và số suất đã lưu. Bàn, nhóm món và chi tiết đơn theo ngữ cảnh. | Không ghi lượt giữ hay biến động tồn. |
| Thêm món hoặc tăng số lượng | Công thức của món, lô tồn và lượt giữ còn hiệu lực của nguyên liệu cần dùng. | Kiểm tra và tạo hoặc tăng lượt giữ theo lô trong giao dịch. Tính và ghi số suất mới của món liên quan nếu kết quả đổi. Tồn thực giữ nguyên. |
| Giảm hoặc bỏ món chưa gửi | Lượt giữ và lượng đã giữ tại từng lô. | Giảm hoặc giải phóng lượt giữ. Cập nhật số suất của các món liên quan. Tồn thực giữ nguyên. |
| Gửi món | Dòng món, lượt giữ và lô liên quan để xác nhận khả năng gửi. | Ghi đơn hoặc dòng món, trừ tồn theo lô, kết thúc lượt giữ và ghi nhận phiếu bếp theo luồng hiện có. Nếu khả dụng giữ nguyên thì không cần ghi lại số suất. |
| Xác nhận phiếu nhập | Nguyên liệu, số lượng và thông tin lô nhập. | Ghi phiếu nhập và lô, cập nhật số suất cho các món dùng nguyên liệu vừa nhập. |
| Hủy phiếu nhập, xuất hủy được xác nhận, xác nhận kiểm kê, hoàn kho khi hủy món/đơn hợp lệ, lô hoặc lượt giữ hết hạn | Lô, lượng và lượt giữ thực tế bị ảnh hưởng. | Ghi biến động theo nghiệp vụ tương ứng. Cập nhật số suất nếu lượng khả dụng thay đổi. |
| Máy khác đang mở màn gọi món | Mỗi 5 giây khi tab hiển thị, đọc mã món và số suất đã lưu. | Không ghi dữ liệu nghiệp vụ. |

**Ví dụ kiểm tra:** Có 1.000 g gà. Gà rang dùng 200 g/suất, gà luộc dùng 250 g/suất. Ban đầu còn 5 và 4 suất. Giữ 2 suất gà rang thì đang giữ 400 g, còn 3 và 2 suất. Bỏ 1 suất thì đang giữ 200 g, còn 4 và 3 suất. Gửi suất còn lại thì tồn thực là 800 g, đang giữ 0 g, vẫn còn 4 và 3 suất.

## Yêu cầu frontend và API

1. Bỏ việc chạy lại `loadMenu` sau mỗi lần thêm, giảm hoặc bỏ món. Trả số suất mới của các món bị ảnh hưởng khi thao tác thành công, hoặc lấy ngay qua API đọc nhẹ nếu luồng trả kết quả cần tách riêng. Cập nhật đúng các món trên màn và xử lý phản hồi đến sai thứ tự.
2. Dùng API định kỳ nhẹ để đọc số suất đã lưu khi tab hiển thị. Gom các lần làm mới trùng nhau. Danh sách bàn, nhóm món, giá và chi tiết đơn làm mới theo nhu cầu của từng dữ liệu.
3. Giữ hành vi hiện tại khi món hết nguyên liệu: món vẫn hiện để nhân viên thấy lý do, có nhãn **Hết nguyên liệu** và bị khóa chọn. Nếu dữ liệu hiển thị chưa kịp cập nhật và yêu cầu giữ bị từ chối, báo lý do và làm mới số suất. Giữ các quy tắc khác về trạng thái món và phân quyền.

## Nghiệm thu và đo lại

- [ ] Chạy đúng ví dụ gà rang và gà luộc ở trên. Một món dùng nguyên liệu khác giữ nguyên số suất. Gửi món không làm số suất giảm hai lần.
- [ ] Hai phiên cùng chọn khi chỉ còn một suất. Chỉ một lượt giữ thành công. Máy còn lại nhận thông báo đúng và cập nhật số suất.
- [ ] Kiểm tra nhập kho, nhả hoặc hết hạn giữ, hủy phiếu nhập, xuất hủy, kiểm kê, hoàn kho và thay đổi công thức hoặc hạn dùng. Sau migration, các món trên dữ liệu cũ có số suất đúng.
- [ ] Mở Network để xác nhận thêm hoặc bỏ món không tải lại cả bàn, nhóm món và thực đơn. Request định kỳ chỉ đọc số suất, sử dụng số đã lưu.
- [ ] Đo trước–sau với 20 phiên, 30 món, cùng dữ liệu khởi tạo, thời lượng và kịch bản. Ghi commit, tổng request, số SQL theo nhóm thao tác, p95 giữ món, p95 từ chọn đến cập nhật xong, lỗi và số thao tác hoàn tất. Tính cả số SQL nền hoặc SQL ghi số suất phát sinh do bản sửa. Nếu số thao tác hoàn tất khác nhau, so thêm **SQL trên mỗi thao tác** để tránh kết luận sai từ tổng số SQL.

---

## Bổ sung nghiệp vụ phát hành hóa đơn điện tử

### Luồng tại quầy

1. **Trước thanh toán:** Thu ngân mở đơn, kiểm tra món và tổng tiền. Khi cần đưa khách đối chiếu, bấm **In phiếu tạm tính**. Bản in ghi rõ **PHIẾU TẠM TÍNH** và hiển thị nội dung đơn tại lúc in. Có thể in lại sau khi sửa đơn.
2. **Khi thanh toán thành công:** Hệ thống ghi nhận giao dịch, chốt dữ liệu đơn và mở màn **Đã thanh toán**. Màn này hiển thị tổng tiền, phương thức thanh toán và khối **Hóa đơn điện tử**. Bỏ nút **In hóa đơn nội bộ** và **In lại** khỏi luồng giao chứng từ cho khách.
3. **Phát hành:** Ngay khi thanh toán thành công, tự mở popup **Phát hành hóa đơn điện tử** cho Thu ngân hoặc Quản lý. Nếu đóng popup, có thể mở lại bằng nút **Phát hành hóa đơn điện tử** trên màn Đã thanh toán. Mở popup chưa gửi yêu cầu. Popup hiển thị nội dung đã chốt, tổng tiền và thông tin người mua theo mẫu áp dụng. Bấm **Xác nhận phát hành** để gửi yêu cầu. Khi dùng sandbox, nhận diện rõ hóa đơn thử nghiệm trên màn hình.
4. **Sau khi phát hành thành công:** Hiện số/ký hiệu hóa đơn và nút **Xem/In hóa đơn điện tử**. Khi bấm, mở bản PDF của chính hóa đơn đã phát hành ở tab mới để thu ngân in hoặc lưu từ trình duyệt. Dùng file PDF hoặc link xem PDF từ nhà cung cấp. Khi mở lại đơn và bấm **In lại**, mở đúng PDF đó, cùng số và nội dung. Chỉ hiện thao tác in sau khi đã phát hành thành công.
5. **Khi dịch vụ lỗi hoặc phản hồi chậm:** Màn hình vẫn hiển thị đơn đã thanh toán và trạng thái phát hành. Thu ngân xử lý tiếp ngay từ chi tiết đơn.

### Bảng đọc và ghi dữ liệu

| Thao tác | Đọc dữ liệu | Ghi dữ liệu |
| --- | --- | --- |
| In phiếu tạm tính | Dòng món, giá và tổng tiền hiện tại của đơn. | Không ghi nhận thanh toán hoặc phát hành hóa đơn. |
| Thanh toán thành công | Đơn, dòng món và kết quả giao dịch. | Lưu giao dịch và bản chụp dữ liệu bán hàng để phát hành, đối soát và tra cứu. |
| Xác nhận phát hành | Bản chụp đã chốt, dữ liệu người bán, mẫu, cấu hình thuế và thông tin người mua theo trường hợp áp dụng. | Tạo một yêu cầu phát hành gốc có mã tham chiếu cố định cho mỗi đơn, lưu dữ liệu gửi và trạng thái **Chờ phát hành**. Gọi dịch vụ sau khi giao dịch ghi yêu cầu đã commit. |
| Dịch vụ trả kết quả | Đối chiếu theo mã tham chiếu. | Lưu mã giao dịch bên dịch vụ, trạng thái, số/ký hiệu, thời điểm phát hành và thông tin tra cứu nếu có. |
| Kiểm tra trạng thái hoặc Thử lại | Yêu cầu đã lưu và tình trạng tại nhà cung cấp. | Cập nhật bản ghi hiện có. Nếu timeout thì đánh dấu **Chưa rõ kết quả**, tra cứu trước khi gửi lại. |
| Xem, tải hoặc in hóa đơn điện tử | Bản thể hiện của hóa đơn đã phát hành. | Không lập hóa đơn mới. |

### Yêu cầu triển khai

- Dùng bản chụp đã chốt của đơn để lấy dòng món, số lượng, giá và tổng tiền. Tận dụng dữ liệu thanh toán và bản chụp hiện có cho luồng mới. Bản ghi cũ vẫn phải đọc được để đối soát, tránh xóa bảng hoặc dữ liệu lịch sử khi đổi giao diện.
- Tại API, kiểm tra quyền Thu ngân hoặc Quản lý và điều kiện của đơn. Dùng ràng buộc duy nhất ở CSDL và khóa chống trùng theo nhà cung cấp. Nếu dịch vụ đã nhận nhưng client mất phản hồi, tra cứu bằng mã tham chiếu. Chỉ gửi lại khi API nhà cung cấp cho phép làm vậy mà tránh phát hành trùng.
- Hiện trạng thái **Chưa phát hành**, **Chờ phát hành**, **Đã phát hành**, **Phát hành lỗi** hoặc **Chưa rõ kết quả**. Lỗi phát hành không đổi trạng thái thanh toán. Hiện nút phù hợp như **Phát hành**, **Kiểm tra trạng thái**, **Thử lại** hoặc **Xem/Tải**.
- Đầu nối nhà cung cấp chạy ở backend. Khóa API lấy từ môi trường. Tách sandbox với môi trường thật và tránh ghi khóa hoặc dữ liệu người mua vào log. Nếu dùng webhook, xác thực thông báo và xử lý thông báo trùng hoặc sai thứ tự.
- **Phạm vi sandbox:** Dùng kịch bản khách kết thúc bữa ăn và thanh toán tại quầy. Trước khi bật môi trường thật, chốt nhà cung cấp, mẫu, cấu hình thuế, thời điểm lập theo nghiệp vụ áp dụng và quy trình hoàn tiền/điều chỉnh hóa đơn. Luồng demo sau thanh toán chỉ mô tả kịch bản này. [Nghị định 254/2026/NĐ-CP](https://vanban.chinhphu.vn/?docid=218689&orggroupid=2&pageid=27160)
- Điểm nối hiện có gồm [màn thanh toán](../apps/web/src/features/sales/payment-panel.tsx), [màn hoàn tất](../apps/web/src/features/sales/done-step.tsx), [API bán hàng](../apps/api/src/app/modules/sales/router.py) và [logic thanh toán](../apps/api/src/app/modules/sales/payments.py).

### Tiêu chí nghiệm thu

- [ ] Mở đơn sandbox có 2 suất gà rang 80.000 đ/suất và 1 suất cơm 20.000 đ. In phiếu tạm tính 180.000 đ trước khi thu tiền. Kiểm tra bản in có nhãn **PHIẾU TẠM TÍNH**.
- [ ] Thanh toán 180.000 đ. Màn hoàn tất tự mở popup **Phát hành hóa đơn điện tử**. Xác nhận phát hành qua sandbox và đối chiếu dòng món, tổng tiền, số hóa đơn và trạng thái với nhà cung cấp.
- [ ] Đơn chưa thanh toán trong kịch bản demo, tài khoản thiếu quyền hoặc dữ liệu thiếu bị chặn trước khi gửi. Bấm hai lần hoặc hai phiên cùng bấm chỉ tạo một hóa đơn gốc.
- [ ] Khi timeout sau khi dịch vụ đã nhận, tra cứu lại được đúng hóa đơn. Khi dịch vụ lỗi, đơn vẫn đã thanh toán và có thể mở lại để xử lý tiếp.
- [ ] Thay đổi giá món sau thanh toán rồi mở lại đơn. Hóa đơn điện tử vẫn dùng dữ liệu đã chốt. Nút **Xem/In** mở PDF ở tab mới, nút **In lại** mở đúng PDF đã phát hành. Các thao tác này không tạo bản phát hành mới.
