# Thiết kế: Đồng bộ mã nguồn với đặc tả báo cáo

## Mục tiêu

Đưa MVP hiện tại khớp với các yêu cầu mới trong `docs/BaoCao_HeThongQuanLyNhaHang.md`, tập trung vào ba khoảng trống đã xác nhận: giữ chỗ món trước khi gửi order; cấu hình có hiệu lực theo Business Date; hạn mức và cache AI theo phạm vi người dùng. Đồng thời xử lý các lỗi kiểm thử API đang có trước khi dùng `make gate` làm tiêu chí hoàn tất.

## Nguồn yêu cầu và nguyên tắc

- Báo cáo mới là nguồn nghiệp vụ cho lần đồng bộ này. Phần Business Date được chuyển từ mốc cố định 06:00 sang giờ cấu hình có ngày hiệu lực; thay đổi có hiệu lực từ Business Date tiếp theo.
- Mọi phép tính ngày nghiệp vụ tiếp tục tập trung ở `app.shared.business_date`. Không tạo cách tính Business Date thứ hai trong service, route hoặc giao diện.
- Giữ MySQL 8.4, SQLAlchemy 2 async, Alembic và định danh bảng/cột tiếng Việt. Không dùng SQL ghép chuỗi.
- Mọi ghi dữ liệu tiếp tục kiểm tra quyền ở API, ghi audit cho thao tác rủi ro cao, và dùng transaction để tránh ghi nhận một phần.
- Giữ riêng phạm vi đọc AI theo từng vai trò. Bếp được xem lượng giữ tổng hợp; vai trò Thu ngân không được thấy dữ liệu giá vốn/kho.
- Giữ tương thích với các API order hiện có trong thời gian chuyển đổi; frontend mới dùng luồng giữ chỗ. Không xóa API cũ cho tới khi các consumer hiện có được kiểm tra.

## 1. Cấu hình và Business Date hiệu lực

`CAU_HINH_HE_THONG` và API cấu hình sẽ chứa các giá trị cần cho hành vi runtime: mốc Business Date đang áp dụng; mốc mới và ngày hiệu lực; ngưỡng tồn mặc định; số ngày cảnh báo sắp hết hạn; thời hạn giữ chỗ; hạn mức câu hỏi AI mỗi người dùng/ngày. Giá trị khởi tạo lần lượt giữ ngưỡng tồn hiện hành, 06:00, 3 ngày, 5 phút và 50 câu/người/ngày.

Quản lý cập nhật mốc giờ mới sẽ tạo giá trị chờ áp dụng, không đổi Business Date đang chạy. `app.shared.business_date` sẽ xác định cấu hình có hiệu lực tại thời điểm cần tính và cung cấp một điểm đọc thống nhất cho order, phiên bản giá/công thức, báo cáo và hạn mức AI. Các luồng không có session DB (ví dụ tác vụ nền) phải nhận cấu hình rõ ràng hoặc dùng snapshot đã nạp; không tự fallback sang hằng số 06:00 khi cấu hình sẵn có.

Thay đổi cấu hình được validate ở schema/service, áp dụng từ lần tạo/gia hạn giữ tiếp theo, và ghi audit trước/sau. Giá trị cấu hình trả về UI hiển thị cả giờ hiện hành và giờ đang chờ cùng ngày hiệu lực.

## 2. Giữ chỗ món và gửi order

### Dữ liệu

- Thêm `GIU_CHO_MON` cho từng dòng món đang chọn. Bản ghi lưu người thao tác, mã lượt chọn, món, số lượng, ghi chú, phiên bản giá/công thức đã xem, order tùy chọn, trạng thái và thời điểm hết hạn.
- Thêm `CHI_TIET_GIU_CHO` để ghi lượng nguyên liệu giữ trên từng lô. Cặp dòng giữ/lô là duy nhất; lượng giữ phải dương.
- Lượt đầu có thể chưa gắn order và không chiếm bàn. Lượt gọi thêm gắn một order đang mở. Dòng đã gửi tham chiếu duy nhất đến dòng order.
- Mỗi dòng/lần gửi lưu khóa idempotency để retry không tạo order line hoặc trừ kho lần hai.

### Luồng và khóa

API cung cấp thao tác tạo/cập nhật/gia hạn/xóa dòng giữ, đọc lượt chọn, gửi lượt chọn và giải phóng lượt. Chỉ người sở hữu lượt chọn hoặc người có quyền quản lý được thao tác; order gắn thêm chỉ được sửa khi vẫn đang mở.

Khi giữ hoặc gửi, service khóa nguyên liệu theo mã tăng dần, sau đó khóa các lô và lượt giữ liên quan. Chỉ lô còn hạn được dùng; lượng khả dụng là tồn hợp lệ trừ giữ còn hạn. Các bước tính khả dụng và ghi giữ chạy nguyên tử. Thời hạn mặc định 5 phút, không vượt hạn dùng sớm nhất của lô được giữ. Phép tính luôn lọc thời hạn trực tiếp, không phụ thuộc tác vụ dọn trạng thái.

Khi gửi, backend kiểm tra lại trạng thái món, phiên bản giá/công thức, bàn/order và khả dụng. Nếu snapshot đã cũ, trả yêu cầu xác nhận lại và giải phóng lượt cũ theo đặc tả; không tự ý gửi bằng giá/công thức mới. Nếu hợp lệ, trong một transaction tạo order/dòng món cần thiết, ghi giao dịch kho, cập nhật lô và tổng tồn, kết thúc giữ, cập nhật bàn và tạo phiếu bếp. Lỗi ở bất cứ bước nào rollback toàn bộ. In vật lý diễn ra sau commit; lỗi được giải quyết qua chức năng in lại hiện có.

Giữ chỗ không tạo giao dịch kho. Hủy/xóa dòng, hết hạn, món bị dừng/xóa, hoặc thao tác nghiệp vụ phù hợp sẽ giải phóng đúng lượng giữ. Phiên kiểm kê đang mở chặn giữ/gia hạn/gửi và các giao dịch nhập/xuất/hoàn kho trong transaction; chỉ một phiên kiểm kê được hoạt động.

### API, giao diện và view AI

Giao diện gọi món chuyển giỏ hàng từ state cục bộ sang lượt chọn trên server, hiển thị đồng hồ/thông báo hết hạn và yêu cầu xác nhận khi giá/công thức đổi. Không tạo order hoặc chiếm bàn trước khi gửi thành công.

View AI của Bếp bổ sung lượng giữ tổng hợp để trả lời lượng khả dụng hiện tại. Các view khác không được cấp thêm bảng/cột ngoài phạm vi vai trò. Tài liệu `db/views/README.md` và grant scripts được cập nhật cùng migration.

## 3. Hạn mức và cache AI

Hạn mức mặc định là 50 câu hỏi/người dùng/Business Date, lấy từ cấu hình hệ thống. Mỗi lượt người dùng gửi tính là một câu, bất kể sinh SQL cần một hay hai lần; request bị từ chối vì đã hết hạn mức không bị tính thêm. Bộ đếm phải phân biệt người dùng, không mất toàn bộ khi worker khởi động lại và không cho request đồng thời vượt hạn mức. Việc tính Business Date dùng helper chung.

Cache có thời hạn ngắn và phân biệt người dùng, vai trò, tập view, câu hỏi chuẩn hóa, tham số thời gian và phiên bản quyền. Chỉ dùng cache khi có thể chứng minh kết quả còn hợp lệ. Câu hỏi cần tồn/giữ/số suất hiện thời luôn đọc dữ liệu mới. Khi không thể xác định dữ liệu phụ thuộc hoặc invalidation an toàn, không dùng cache kết quả. Cache không được làm rộng phạm vi view hoặc bỏ qua `guard.validate_sql`.

## 4. Điều tra gate và tiêu chí hoàn tất

Trước khi sửa hành vi, tái hiện 7 lỗi pytest sau merge trong worktree sạch và kiểm tra ảnh hưởng của `.env`/cấu hình máy cục bộ mà không in giá trị bí mật. Phân biệt lỗi do môi trường với lỗi logic; test baseline được lưu làm mốc. Sửa các lỗi API thuộc code dự án theo TDD, không làm thay đổi `.env` hoặc dữ liệu riêng của người dùng.

Phần đồng bộ được chấp nhận khi:

1. Test chứng minh giữ không làm trừ tồn; giữ cùng lô không vượt số lượng; hết hạn không chiếm khả dụng; gửi chuyển giữ sang tiêu hao đúng một lần; gửi trùng trả cùng kết quả; kiểm kê chặn giao dịch cạnh tranh; rollback không để sót cập nhật.
2. Test chứng minh Business Date dùng cấu hình có hiệu lực và giờ mới chỉ tác động từ ngày hiệu lực; cấu hình sai bị từ chối và ghi audit.
3. Test chứng minh hạn mức riêng theo user/ngày, request đồng thời không vượt hạn mức, và câu hỏi dữ liệu động không nhận cache cũ.
4. View/grant từng vai trò chỉ cấp đúng tập dữ liệu; kiểm thử guard vẫn chạy trên mọi SQL sinh ra.
5. Format, lint, typecheck, pytest và build đều xanh qua `make gate`.

Sao lưu tự động FR-SET-07 vẫn nằm ngoài MVP theo báo cáo. Không mở rộng phạm vi sang chức năng chưa được nêu trong tài liệu.

## Tách đợt thực hiện

Đây là một chương trình thay đổi lớn, nên triển khai theo lát cắt có thể review độc lập:

1. **Baseline và cấu hình nền:** tái hiện lỗi gate; thêm cấu hình hiệu lực; chuyển Business Date sang cấu hình tập trung; cập nhật UI, migration và test.
2. **Giữ chỗ và tồn kho:** model/migration, service giữ theo lô/khóa, API, tương tác với kiểm kê, test đồng thời và idempotency.
3. **Luồng bán hàng:** chuyển giao diện sang server-side cart; gửi lượt chọn thành order; giữ tương thích route và nối phiếu bếp/bàn.
4. **AI và dữ liệu phân quyền:** hạn mức theo user, cache an toàn, view Bếp có lượng giữ, grant và kiểm thử quyền.
5. **Hoàn tất:** chạy gate toàn repo và rà lại các yêu cầu liên quan trong báo cáo.

Mỗi lát cắt có test trước khi sửa production code. Không gộp các thay đổi nếu test ở lát cắt trước chưa xanh.
