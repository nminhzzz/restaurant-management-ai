# Kết nối máy in phiếu bếp

FR-SALE-31/32 dùng hàng đợi bền vững trong `PHIEU_BEP`. Khi gửi món hoặc gọi thêm,
transaction lưu nguyên nội dung phiếu cùng nghiệp vụ. Worker trong lifespan API chỉ đọc
phiếu đã commit, khóa hàng bằng MySQL `FOR UPDATE SKIP LOCKED`, commit lease trước khi
mở kết nối máy in. In lại dùng chính nội dung đã lưu, không tính lại giá/công thức,
không tạo dòng món hay xuất kho lần nữa. API yêu cầu quyền Quản lý hoặc Thu ngân.

## Cấu hình máy chủ

Áp dụng migration `d23102300003` qua `make migrate` trên CSDL môi trường thử nghiệm
trước. Máy in phải hỗ trợ ESC/POS qua TCP thô (thường cổng 9100), có địa chỉ cố định
trong mạng nội bộ mà máy chủ API truy cập được. Không cấu hình địa chỉ máy in trên trình duyệt.

```dotenv
KITCHEN_PRINTER_HOST=
KITCHEN_PRINTER_PORT=9100
KITCHEN_PRINTER_TIMEOUT_SECONDS=3
KITCHEN_PRINTER_POLL_SECONDS=2
KITCHEN_PRINTER_MAX_ATTEMPTS=3
KITCHEN_PRINTER_RETRY_SECONDS=5
```

Để trống `HOST`: giữ phiếu mới ở **Chờ in**, không gửi mạng và không báo thành công.
Đặt `POLL_SECONDS=0` để tắt worker. Khởi động lại API sau khi sửa biến môi trường.
Adapter gửi lệnh khởi tạo, nội dung và cắt giấy ESC/POS. Nội dung CSDL giữ nguyên
Unicode tiếng Việt; bản in dùng chuyển tự không dấu vì bảng mã/font tiếng Việt của
máy in phổ thông không thống nhất. Kiểm tra rõ khả năng đọc ghi chú và lệnh cắt giấy
của model thực tế trước nghiệm thu. Chỉ mở cổng máy in cho máy chủ API trong LAN.

## Ý nghĩa trạng thái và khôi phục

- **Chờ in**: chưa gửi, hoặc chờ thử lại sau lỗi kết nối trước khi ghi byte.
- **Đang in**: một worker đã nhận phiếu; các worker khác và nút in lại không gửi trùng.
- **Đã gửi máy in**: TCP đã nhận dữ liệu gửi. Đây là kết quả gửi lệnh, không xác nhận
  giấy ra khỏi máy; máy hết giấy vẫn có thể nhận dữ liệu vào bộ đệm.
- **Thất bại**: hết số lần thử kết nối trong một đợt, hoặc nhân viên báo lỗi.
- **Chưa rõ kết quả**: lỗi sau khi bắt đầu ghi, timeout tổng, hoặc worker chết và hết
  lease. Không tự gửi lại vì máy in có thể đã nhận phiếu. Nhân viên kiểm tra giấy rồi
  chủ động **In lại**. Cần khôi phục cấu hình và khởi động worker nếu đã tắt máy in.

Mỗi đợt tự thử tối đa `MAX_ATTEMPTS`, cách nhau `RETRY_SECONDS`. Chỉ lỗi trước khi gửi
byte mới được thử tự động. In lại thủ công không giới hạn số đợt. Bấm lặp khi phiếu
đang chờ không thêm công việc; đang in thì API từ chối. `SoLanIn` của phiếu mới đếm
số lần bắt đầu thử gửi (bao gồm kết nối lỗi), không đếm số tờ giấy. `ThoiDiemIn` là
thời điểm UTC bắt đầu lần thử gần nhất. Giao diện tự tải lại khi phiếu còn chờ/đang in,
hiển thị lỗi và cho báo lỗi sau khi kiểm tra thực tế. Trình duyệt không được báo
thành công thay worker.

Migration chuyển phiếu lịch sử sang **Chưa rõ kết quả** để tránh tự in lại các đơn
cũ khi bật worker lần đầu. Bộ đếm lịch sử giữ nguyên và chưa được xác minh vì phiên
bản cũ chỉ ghi nhận thao tác trình duyệt. Downgrade bỏ cột/index hàng đợi; không thể
khôi phục ý nghĩa trạng thái trình duyệt cũ đã thiếu bằng chứng.

TCP ESC/POS không có mã chống lặp hay biên nhận giấy đáng tin cậy. Không cam kết
in vật lý đúng một lần: mất tiến trình ngay sau gửi có thể tạo trạng thái chưa rõ;
in lại thủ công sau đó có khả năng tạo bản thứ hai. Lease và token ngăn worker
cạnh tranh hoặc kết quả cũ ghi đè lần in mới; không thay thế xác nhận phần cứng.

## Kiểm chứng

Kiểm thử tự động không dùng máy in ngoài: `cd apps/api && uv run pytest
 tests/modules/test_kitchen_print_queue.py tests/modules/test_sales_tickets.py`.
Bộ test gồm TCP server loopback nhận byte ESC/POS, giữ nguyên snapshot, rollback,
claim đã commit trước I/O, worker cạnh tranh trong lúc gửi, lỗi kết nối có giới hạn,
lỗi chưa rõ không tự lặp, lease hết hạn, nhiều đợt in lại và từ chối kết quả thành
công giả từ trình duyệt. Kiểm tra giao diện: `cd apps/web && pnpm test
 src/features/sales/order-detail.test.tsx`.

Nghiệm thu phần cứng phải ghi bằng chứng riêng, chưa được thực hiện trong phiên này:

1. Dùng CSDL thử riêng và máy in thử; ghi model, IP/cổng, khổ giấy, firmware, cấu hình
   môi trường, giờ thử và ảnh phiếu. Gửi đơn có ghi chú, mang về/bàn và lượt gọi thêm;
   đối chiếu snapshot, tên món, lượng và chuyển tự không dấu trên giấy.
2. Tắt máy in trước lúc gửi: đơn và xuất kho vẫn commit, worker thử hữu hạn, hiện lỗi.
   Bật máy rồi in lại; kiểm tra kho không đổi, phiếu giữ nguyên nội dung.
3. Chạy hai API worker, gửi đồng thời; kiểm tra mỗi phiếu chỉ một worker xử lý.
   Đây là kiểm tra khóa MySQL thực; SQLite unit test không chứng minh khóa MySQL.
4. Gián đoạn mạng/tiến trình ngay sau gửi; kiểm tra không tự in lại khi lease hết hạn,
   ghi nhận trạng thái chưa rõ và quyết định in lại của nhân viên sau đối chiếu giấy.
5. Thử hết giấy, mất giấy, bấm in lại nhiều lần; lưu kết quả quan sát, không suy ra
   thành công vật lý chỉ từ trạng thái TCP. Không chạy các bước này trên thiết bị
   hay CSDL vận hành khi chưa có lịch thử được thống nhất.
