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
