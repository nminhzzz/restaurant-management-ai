Hệ thống quản lý nhà hàng tích hợp AI hỗ trợ hoạt động kinh doanh

Phiên bản tài liệu V33  
Ngày 27 tháng 10 năm 2026

Đặc tả 30 Use Case, danh mục Use Case và các yêu cầu chức năng chi tiết của hệ thống quản lý nhà hàng.

## 3.4. Đặc tả chức năng

Mục này đặc tả 30 Use Case của hệ thống, chia thành sáu module tương ứng với các nhóm tại mục 3.1.2. Mỗi Use Case trình bày tác nhân, đầu vào, đầu ra, trình tự xử lý và các nhánh nghiệp vụ chính.

Ngoại trừ đăng nhập, người dùng phải có phiên hợp lệ và quyền tương ứng. Mỗi Use Case ghi các mã FR liên quan; nội dung chi tiết của từng FR được trình bày tại Phụ lục K. Danh mục Use Case và đối chiếu nghiệp vụ được trình bày tại Phụ lục I.

### 3.4.1. Module 1 - Quản lý danh mục

**1.1 – Quản lý nhóm món**

- **Tác nhân:** Quản lý

- **Đầu vào:** Tên nhóm món, thông tin cần sửa, thứ tự hiển thị hoặc nhóm cần xóa.

- **Đầu ra:** Danh sách nhóm món được cập nhật hoặc thông báo lý do từ chối.

- **Nội dung xử lý:**

  - Bước 1. Quản lý chọn thêm, sửa, sắp xếp hoặc xóa nhóm món trên danh sách.

  - Bước 2. Hệ thống kiểm tra thông tin và điều kiện của thao tác; nếu không hợp lệ, hiển thị lý do để Quản lý xử lý.

  - Bước 3. Hệ thống lưu thay đổi, ghi nhật ký thao tác xóa và cập nhật danh sách.

Yêu cầu chức năng liên quan: FR-CAT-01, FR-CAT-03.

**1.2 – Quản lý món ăn**

- **Tác nhân:** Quản lý

- **Đầu vào:** Tên món, nhóm món, ảnh, thông tin bán; món cần cập nhật hoặc xóa.

- **Đầu ra:** Món được tạo/cập nhật, trạng thái phục vụ được xác định hoặc thông báo từ chối.

- **Nội dung xử lý:**

  - Bước 1. Quản lý chọn thao tác và nhập thông tin món ăn; món mới được lưu ở trạng thái Nháp.

  - Bước 2. Hệ thống kiểm tra dữ liệu và điều kiện cập nhật, tạm dừng, mở lại hoặc xóa món; nếu không đạt, thông báo lý do.

  - Bước 3. Hệ thống lưu kết quả, cập nhật trạng thái phục vụ và danh sách món; dữ liệu của order cũ được giữ nguyên.

Yêu cầu chức năng liên quan: FR-CAT-02, FR-CAT-04, FR-CAT-05, FR-CAT-06, FR-CAT-11, FR-CAT-26, FR-CAT-27, FR-CAT-28.

**1.3 – Quản lý công thức**

- **Tác nhân:** Quản lý

- **Đầu vào:** Món ăn, danh sách nguyên liệu, định lượng, lựa chọn áp dụng ngay hoặc ngày hiệu lực.

- **Đầu ra:** Phiên bản công thức và lịch áp dụng được lưu/cập nhật/hủy hoặc thông báo lỗi.

- **Nội dung xử lý:**

  - Bước 1. Quản lý chọn món, khai báo nguyên liệu và định lượng hoặc chọn lịch công thức cần xử lý.

  - Bước 2. Hệ thống kiểm tra dữ liệu; Quản lý xác nhận áp dụng công thức đầu tiên, sửa trực tiếp, lên lịch, thay hoặc hủy lịch theo trường hợp tương ứng.

  - Bước 3. Hệ thống lưu phiên bản và lịch sử thao tác; công thức đầu tiên đưa món ra khỏi trạng thái Nháp. Các lượt gửi món tiếp theo sử dụng phiên bản có hiệu lực.

Yêu cầu chức năng liên quan: FR-CAT-07, FR-CAT-08, FR-CAT-09, FR-CAT-10, FR-CAT-23, FR-CAT-24, FR-CAT-25; FR-CAT-11.

**1.4 – Quản lý giá bán**

- **Tác nhân:** Quản lý

- **Đầu vào:** Món ăn, giá bán, ngày kinh doanh áp dụng hoặc lịch giá cần hủy.

- **Đầu ra:** Giá hiện hành, lịch giá và lịch sử giá được cập nhật hoặc thông báo lỗi.

- **Nội dung xử lý:**

  - Bước 1. Quản lý chọn món, nhập giá và chọn sửa trực tiếp hoặc lên lịch; với lịch chưa áp dụng, có thể chọn thay hoặc hủy lịch.

  - Bước 2. Hệ thống kiểm tra dữ liệu và thời điểm hiệu lực; thông tin không hợp lệ được trả về để chỉnh sửa.

  - Bước 3. Hệ thống lưu phiên bản giá và lịch sử; các món đã ghi nhận trên order giữ nguyên giá.

Yêu cầu chức năng liên quan: FR-CAT-20, FR-CAT-21, FR-CAT-22; FR-CAT-23–25.

**1.5 – Quản lý bàn**

- **Tác nhân:** Quản lý

- **Đầu vào:** Thông tin bàn; bàn cần sửa/xóa, trạng thái sử dụng và lịch sử tham chiếu của bàn.

- **Đầu ra:** Danh mục và sơ đồ bàn được cập nhật hoặc thông báo không thể thực hiện.

- **Nội dung xử lý:**

  - Bước 1. Quản lý xem danh mục, chọn thêm, sửa hoặc xóa bàn và nhập thông tin cần thiết.

  - Bước 2. Hệ thống kiểm tra dữ liệu và điều kiện xóa; nếu bàn đang phục vụ hoặc dữ liệu không hợp lệ, thông báo lý do.

  - Bước 3. Hệ thống lưu thay đổi, ghi nhật ký thao tác xóa và cập nhật danh sách bàn.

Yêu cầu chức năng liên quan: FR-CAT-17, FR-CAT-19.

**1.6 – Quản lý nguyên liệu**

- **Tác nhân:** Bếp

- **Đầu vào:** Tên nguyên liệu, đơn vị tính, mức tồn tối thiểu riêng; nguyên liệu cần cập nhật hoặc xóa.

- **Đầu ra:** Danh mục nguyên liệu được cập nhật hoặc thông báo từ chối.

- **Nội dung xử lý:**

  - Bước 1. Người dùng chọn thêm, sửa hoặc xóa nguyên liệu và nhập thông tin theo đơn vị chuẩn.

  - Bước 2. Hệ thống kiểm tra dữ liệu, điều kiện thay đổi đơn vị và điều kiện xóa; nếu không đạt, yêu cầu chỉnh sửa hoặc từ chối thao tác.

  - Bước 3. Hệ thống lưu kết quả, ghi nhật ký thao tác xóa và cập nhật danh mục dùng cho công thức, nhập kho.

Yêu cầu chức năng liên quan: FR-CAT-12, FR-CAT-13, FR-CAT-14.

**1.7 – Quản lý nhà cung cấp**

- **Tác nhân:** Bếp

- **Đầu vào:** Thông tin liên hệ nhà cung cấp, tiêu chí tìm kiếm hoặc nhà cung cấp cần sửa/xóa.

- **Đầu ra:** Danh sách, thông tin nhà cung cấp và lịch sử nhập hàng phù hợp yêu cầu.

- **Nội dung xử lý:**

  - Bước 1. Người dùng tìm nhà cung cấp, xem thông tin và lịch sử nhập hàng hoặc chọn thêm, sửa, xóa.

  - Bước 2. Hệ thống kiểm tra dữ liệu và điều kiện xóa; thông báo lý do nếu không thể thực hiện.

  - Bước 3. Hệ thống lưu kết quả, ghi nhật ký thao tác xóa và cập nhật danh sách nhà cung cấp.

Yêu cầu chức năng liên quan: FR-CAT-15, FR-CAT-16.

### 3.4.2. Module 2 - Quản lý bán hàng

**2.1 – Gọi món tại chỗ**

- **Tác nhân:** Thu ngân/Nhân viên order

- **Đầu vào:** Bàn trống, món ăn, số lượng, ghi chú và giá/công thức hiện hành.

- **Đầu ra:** Order tại chỗ, các dòng món, giao dịch tiêu hao FIFO và phiếu bếp; bàn chuyển Đang phục vụ.

- **Nội dung xử lý:**

  - Bước 1. Nhân viên chọn bàn trống, thêm món, số lượng và ghi chú; hệ thống giữ nguyên liệu cho lượt chọn. Nhân viên có thể chọn Hủy lượt chọn để bỏ phần chưa gửi theo FR-SALE-08.

  - Bước 2. Khi gửi món, hệ thống kiểm tra lại bàn, món và lượng nguyên liệu. Nếu dữ liệu đã thay đổi hoặc lượt giữ hết hiệu lực, nhân viên kiểm tra và xác nhận lại; nếu không đủ điều kiện, hệ thống từ chối lượt gửi.

  - Bước 3. Hệ thống tạo order, ghi nhận tiêu hao nguyên liệu, chuyển bàn sang Đang phục vụ và lưu phiếu bếp.

  - Bước 4. Hệ thống in phiếu sau khi lưu thành công; nếu in lỗi, nhân viên có thể in lại phiếu đã lưu.

Yêu cầu chức năng liên quan: FR-SALE-01, FR-SALE-02, FR-SALE-03, FR-SALE-04, FR-SALE-05, FR-SALE-08, FR-SALE-24, FR-SALE-31, FR-SALE-32; FR-INV-13; FR-INV-03; FR-INV-10–12.

**2.2 – Gọi món mang về**

- **Tác nhân:** Thu ngân/Nhân viên order

- **Đầu vào:** Lựa chọn Mang về, danh sách món, số lượng, ghi chú và dữ liệu giá/công thức.

- **Đầu ra:** Order mang về không gắn bàn, tiêu hao FIFO, phiếu bếp và trạng thái phục vụ.

- **Nội dung xử lý:**

  - Bước 1. Nhân viên chọn loại Mang về, thêm món, số lượng và ghi chú; hệ thống giữ nguyên liệu, không gắn bàn. Nhân viên có thể chọn Hủy lượt chọn để bỏ phần chưa gửi theo FR-SALE-08.

  - Bước 2. Khi gửi món, hệ thống kiểm tra lại dữ liệu; yêu cầu xác nhận lại nếu có thay đổi hoặc từ chối nếu không đủ điều kiện. Sau khi hợp lệ, hệ thống tạo order, ghi nhận tiêu hao và lưu phiếu bếp.

  - Bước 3. Khi order còn Đang mở, nhân viên tiếp nhận phần gọi thêm theo UC 2.3. Thu ngân thực hiện thanh toán theo UC 2.4 hoặc UC 2.5.

  - Bước 4. Nhân viên giao món sau khi thanh toán và cập nhật Đã phục vụ. Khách mua thêm sau khi order đã thanh toán hoặc đóng thì lập order mới.

Yêu cầu chức năng liên quan: FR-SALE-01–06, 08, 24, 31–32; FR-INV-13; FR-INV-03; FR-INV-10–12.

**2.3 – Quản lý order và phục vụ**

- **Tác nhân:** Thu ngân/Nhân viên order

- **Đầu vào:** Order tại chỗ hoặc mang về và trạng thái hiện tại; yêu cầu gọi thêm, giảm/hủy món, cập nhật phục vụ, đổi bàn hoặc xác nhận khách đã rời; xác nhận thực tế của Bếp. Gọi thêm dành cho order tại chỗ hoặc mang về Đang mở; riêng tại chỗ phải còn gắn đúng bàn. Đổi bàn chỉ dành cho order tại chỗ Đang mở còn gắn đúng bàn. Giảm/hủy chỉ khi order còn cho phép sửa; cập nhật phục vụ và giải phóng bàn áp dụng theo điều kiện riêng của từng nhánh.

- **Đầu ra:** Order được bổ sung, điều chỉnh hoặc cập nhật trạng thái; nguyên liệu được trừ hoặc hoàn; liên kết bàn–order được cập nhật; hoặc thông báo từ chối.

- **Nội dung xử lý:**

- **a) Gọi thêm món**

  - Bước 1. Nhân viên mở order Đang mở để gọi thêm; với order tại chỗ, hệ thống kiểm tra order còn gắn đúng bàn. Nếu không đủ điều kiện, hệ thống từ chối.

  - Bước 2. Nhân viên thêm món vào lượt chọn để giữ nguyên liệu, điều chỉnh hoặc hủy lượt chọn theo FR-SALE-08. Khi gửi, hệ thống kiểm tra lại giá, công thức và lượng khả dụng; dữ liệu thay đổi được xác nhận theo FR-SALE-05.

  - Bước 3. Trong cùng giao dịch, hệ thống ghi nhận phần món mới, trừ nguyên liệu theo FIFO và kết thúc lượt giữ tương ứng. Phiếu bếp được lưu và in sau khi commit; các món đã gửi trước đó giữ nguyên thông tin.

- **b) Sửa số lượng hoặc hủy món đã gửi**

  - Bước 1. Nhân viên chọn dòng món cần giảm hoặc hủy và xác nhận với Bếp rằng món chưa chế biến. Nếu không còn đủ điều kiện, hệ thống từ chối; phần đã chế biến được xử lý theo nghiệp vụ hao hụt khi cần.

  - Bước 2. Hệ thống giảm hoặc hủy món, hoàn nguyên liệu theo lô gốc và ghi nhật ký. Khi hủy hết món đã gửi, hệ thống xử lý order theo FR-SALE-11; bàn được giải phóng khi khách rời đi.

- **c) Cập nhật trạng thái phục vụ**

  - Bước 1. Khi Bếp báo hoàn tất, nhân viên chọn món để chuyển từ Chờ làm sang Đã xác nhận xong; nếu trạng thái đã thay đổi hoặc món bị hủy, hệ thống yêu cầu tải lại.

  - Bước 2. Khi giao món, nhân viên cập nhật Đã phục vụ; hệ thống lưu trạng thái và thời điểm. Sau thanh toán, việc cập nhật chỉ áp dụng cho trạng thái phục vụ.

- **d) Đổi bàn và giải phóng bàn**

  - Bước 1. Nhân viên chọn đổi bàn cho order tại chỗ Đang mở; hệ thống kiểm tra bàn nguồn và bàn đích, rồi cập nhật việc chuyển bàn hoặc thông báo lý do từ chối.

  - Bước 2. Khi khách rời đi, nhân viên giải phóng đúng bàn đang gắn với order; hệ thống kết thúc lượt chọn liên quan, cập nhật bàn và ghi lịch sử. Việc xử lý thanh toán về sau không tác động bàn đã giao cho order khác.

Yêu cầu chức năng liên quan: FR-CAT-18, FR-SALE-06, FR-SALE-07, FR-SALE-09, FR-SALE-10, FR-SALE-11, FR-SALE-12; FR-SALE-01–05, 08, 24, 31–32; FR-INV-13; FR-INV-03–04; FR-INV-10–12.

**2.4 – Thanh toán**

- **Tác nhân:** Thu ngân/Nhân viên order

- **Đầu vào:** Order cần thanh toán, các dòng món, tổng tiền và phương thức thanh toán khách chọn.

- **Đầu ra:** Giao dịch thành công, hóa đơn và order Đã thanh toán; hoặc chuyển sang luồng QR/chưa hoàn tất.

- **Nội dung xử lý:**

  - Bước 1. Thu ngân mở order, xử lý hết phần gọi thêm chưa gửi và in phiếu tạm tính để khách kiểm tra. Nếu nội dung thay đổi, hệ thống tính lại và in lại phiếu.

  - Bước 2. Thu ngân chọn phương thức thanh toán; với QR, thực hiện UC 2.5. Với tiền mặt, Thu ngân kiểm đếm và xác nhận đã nhận đủ.

  - Bước 3. Hệ thống ghi nhận thanh toán, chuyển order sang Đã thanh toán và phát hành hóa đơn; nếu in lỗi, cho in lại hóa đơn đã lưu.

  - Bước 4. Khi khách rời đi, nhân viên giải phóng bàn theo UC 2.3.

Yêu cầu chức năng liên quan: FR-SALE-13, FR-SALE-21, FR-SALE-22; FR-SALE-24.

**2.5 – Thanh toán QR**

- **Tác nhân:** Thu ngân/Nhân viên order; Cổng thanh toán (hệ thống ngoài)

- **Đầu vào:** Order đã chốt nội dung, tổng tiền, lựa chọn QR và kết quả giao dịch từ cổng thanh toán.

- **Đầu ra:** Thanh toán thành công và hóa đơn; hoặc giao dịch hết hạn/đã hủy/chờ xác minh theo tình huống.

- **Nội dung xử lý:**

  - Bước 1. Thu ngân chọn QR tại UC 2.4; hệ thống tạo và hiển thị mã, chuyển order sang Chờ xác nhận thanh toán. Khách quét mã và chuyển tiền.

  - Bước 2. Hệ thống kiểm tra kết quả thanh toán. Xác nhận hợp lệ hoàn tất thanh toán và phát hành hóa đơn; khoản đến muộn hoặc ngoại lệ được xử lý theo FR-SALE-16–17.

  - Bước 3. Nếu khách chưa trả tiền, Thu ngân có thể cho quét lại khi mã còn hạn hoặc hủy mã; mã hết hạn đưa order về Đang mở để chọn lại phương thức.

  - Bước 4. Nếu khách báo đã trả nhưng chưa có xác nhận hợp lệ, Thu ngân ghi nhận yêu cầu xác minh và chuyển sang UC 2.6.

Yêu cầu chức năng liên quan: FR-SALE-14, FR-SALE-15, FR-SALE-16, FR-SALE-17, FR-SALE-18, FR-SALE-19, FR-SALE-33; FR-SALE-21–22; FR-SALE-29.

**2.6 – Xử lý xác minh thanh toán và khoản QR ngoại lệ**

- **Tác nhân:** Quản lý

- **Đầu vào:** Order Chờ xác minh thanh toán hoặc khoản QR ngoại lệ; mã/số tiền/thời điểm giao dịch, thông tin khách cung cấp, order liên quan và sao kê tài khoản nhận.

- **Đầu ra:** Kết quả đối soát, trạng thái order/giao dịch, khoản tiền được áp dụng hợp lệ hoặc ghi nhận hoàn tiền ngoài hệ thống, và nhật ký quyết định xử lý.

- **Nội dung xử lý:**

  - Bước 1. Quản lý mở danh sách chờ xác minh, xem thông tin, bằng chứng và đối chiếu sao kê tài khoản nhận tiền.

  - Bước 2. Nếu đã nhận đủ tiền, Quản lý xác nhận để hoàn tất thanh toán. Nếu chưa đủ căn cứ, lưu tiến độ và tiếp tục tra soát; khi đã thống nhất thu lại, mở lại thanh toán; khi ngừng theo dõi thu tiền, đóng order chưa thu được tiền và lưu lý do.

  - Bước 3. Với khoản QR ngoại lệ, Quản lý đối chiếu order và lịch sử thu để chọn áp dụng khoản nhận hợp lệ hoặc ghi nhận kết quả hoàn tiền ngoài hệ thống theo FR-SALE-17. Khoản chưa xử lý tiếp tục được theo dõi.

  - Bước 4. Hệ thống kiểm tra lại dữ liệu trước khi ghi quyết định, lưu nhật ký và cập nhật trạng thái, chứng từ, báo cáo tương ứng; không tác động bàn đã giao cho order khác.

Yêu cầu chức năng liên quan: FR-SALE-20, FR-SALE-23, FR-SALE-34, FR-SALE-35; FR-SALE-16–19.

**2.7 – Hủy toàn bộ order**

- **Tác nhân:** Quản lý

- **Đầu vào:** Order cần hủy, trạng thái thanh toán, trạng thái từng món và lý do hủy.

- **Đầu ra:** Order bị hủy, giao dịch hoàn kho phù hợp và nhật ký; hoặc thông báo từ chối.

- **Nội dung xử lý:**

  - Bước 1. Quản lý chọn order, nhập lý do hủy; hệ thống kiểm tra điều kiện. Nếu đang chờ QR, xử lý mã trước; nếu khách báo đã chuyển tiền, chuyển sang xác minh.

  - Bước 2. Quản lý xác nhận với Bếp về các món chưa chế biến; hệ thống hủy order và xử lý nguyên liệu theo trạng thái từng món.

  - Bước 3. Hệ thống lưu nhật ký, kết thúc lượt chọn liên quan và cập nhật báo cáo; bàn chỉ được giải phóng khi khách rời đi.

Yêu cầu chức năng liên quan: FR-SALE-27, FR-SALE-28, FR-SALE-29, FR-SALE-30; FR-INV-04.

**2.8 – Tra cứu order**

- **Tác nhân:** Quản lý; Thu ngân/Nhân viên order

- **Đầu vào:** Mã order, bàn, khoảng ngày kinh doanh, trạng thái order hoặc order/chứng từ cần xem và in lại.

- **Đầu ra:** Danh sách order phù hợp, chi tiết order/chứng từ hoặc kết quả in lại.

- **Nội dung xử lý:**

  - Bước 1. Người dùng mở danh sách order và chọn tiêu chí lọc. Quản lý truy cập từ mục Quản lý đơn hàng; hệ thống hiển thị các order phù hợp với quyền và bộ lọc. Nếu không có kết quả, người dùng đổi tiêu chí hoặc kết thúc.

  - Bước 2. Người dùng mở order để xem loại đơn, bàn, ngày kinh doanh, người lập, trạng thái, chi tiết món, tổng tiền, lịch sử thanh toán và chứng từ; khi cần, chọn in lại hóa đơn hoặc phiếu bếp đã lưu.

  - Bước 3. Hệ thống in đúng chứng từ gốc; nếu chưa có chứng từ hoặc in lỗi, thông báo lý do và cho thử lại sau khi khắc phục.

Yêu cầu chức năng liên quan: FR-SALE-25, FR-SALE-26; FR-SALE-32.

### 3.4.3. Module 3 - Quản lý kho

**3.1 – Nhập kho theo lô**

- **Tác nhân:** Bếp

- **Đầu vào:** Nhà cung cấp, nguyên liệu, số lượng, đơn giá, ngày nhập và thông tin hạn dùng theo lô.

- **Đầu ra:** Phiếu nhập, lô nguyên liệu, tồn kho được cập nhật hoặc thông báo lỗi.

- **Nội dung xử lý:**

  - Bước 1. Người lập nhập thông tin hàng thực nhận; hệ thống kiểm tra dữ liệu và trạng thái kiểm kê. Nếu không hợp lệ, yêu cầu chỉnh sửa hoặc từ chối ghi kho.

  - Bước 2. Người lập xác nhận; hệ thống lưu phiếu nhập, tạo lô và cập nhật tồn kho.

  - Bước 3. Khi sửa hoặc hủy phiếu, hệ thống kiểm tra điều kiện sử dụng các lô. Nếu không đạt, từ chối và hướng dẫn xử lý chênh lệch qua kiểm kê; nếu đạt, lưu thay đổi và nhật ký.

Yêu cầu chức năng liên quan: FR-INV-01, FR-INV-02, FR-INV-13.

**3.2 – Theo dõi xuất nguyên liệu**

- **Tác nhân:** Bếp

- **Đầu vào:** Nguyên liệu, order/dòng món, lô và khoảng thời gian cần tra cứu biến động xuất/hoàn.

- **Đầu ra:** Lịch sử xuất/hoàn và lượng phân bổ theo từng lô, dòng món.

- **Nội dung xử lý:**

  - Bước 1. Người dùng chọn tiêu chí tra cứu và mở chi tiết giao dịch xuất hoặc hoàn nguyên liệu. Nếu không có kết quả, có thể thay đổi bộ lọc.

  - Bước 2. Hệ thống hiển thị nguyên liệu và các lô đã phân bổ theo FIFO; ví dụ nhu cầu 800 g được lấy 500 g từ lô trước và 300 g từ lô tiếp theo.

  - Bước 3. Với giao dịch hoàn, hệ thống cho xem lượng hoàn theo các lô của giao dịch gốc.

Yêu cầu chức năng liên quan: FR-INV-03, FR-INV-04; FR-INV-13; FR-INV-10–12.

**3.3 – Lập phiếu xuất hủy**

- **Tác nhân:** Bếp

- **Đầu vào:** Nguồn xuất hủy và lý do; nguyên liệu, lô và lượng hủy với nguồn Nguyên liệu; dòng order và số suất bị bỏ với nguồn Món đã chế biến.

- **Đầu ra:** Phiếu xuất hủy hợp lệ và giao dịch kho tương ứng theo nguồn, hoặc thông báo từ chối.

- **Nội dung xử lý:**

  - Bước 1. Người dùng chọn nguồn và nhập lý do; chọn lô, lượng nguyên liệu hủy hoặc chọn dòng order, số suất món bị bỏ.

  - Bước 2. Hệ thống kiểm tra giới hạn và trạng thái kiểm kê. Với món đã chế biến, hệ thống tự xác định các nguyên liệu và lượng tương ứng từ tiêu hao gốc, hiển thị để người dùng kiểm tra. Dữ liệu không hợp lệ bị từ chối; lô hỏng đang được giữ được xử lý theo FR-INV-06.

  - Bước 3. Người dùng xác nhận; hệ thống lưu phiếu, ghi nhật ký và trừ tồn theo lô với nguồn Nguyên liệu. Phiếu nguồn Món đã chế biến liên kết với tiêu hao gốc; chứng từ chênh lệch kiểm kê được sinh từ UC 3.4.

Yêu cầu chức năng liên quan: FR-INV-05, FR-INV-06.

**3.4 – Kiểm kê và điều chỉnh tồn**

- **Tác nhân:** Bếp

- **Đầu vào:** Tồn sổ sách theo nguyên liệu/lô, số lượng kiểm đếm thực tế và lý do chênh lệch.

- **Đầu ra:** Phiếu kiểm kê, điều chỉnh tồn và chứng từ liên quan, hoặc phiên được hủy.

- **Nội dung xử lý:**

  - Bước 1. Người dùng bắt đầu kiểm kê sau khi kết thúc phục vụ; hệ thống kiểm tra điều kiện, chốt số liệu và khóa thay đổi kho. Nếu chưa đủ điều kiện, thông báo lý do.

  - Bước 2. Người dùng kiểm đếm các lô, kể cả lô hết hạn, nhập số lượng thực tế và lý do chênh lệch, rồi xác nhận.

  - Bước 3. Hệ thống điều chỉnh theo kết quả kiểm kê: giảm tồn và ghi hao hụt khi thiếu, tăng tồn khi thừa; không tạo điều chỉnh khi khớp.

  - Bước 4. Hệ thống lưu nhật ký và kết thúc kiểm kê, mở lại thao tác kho. Nếu hủy kiểm kê, hệ thống mở khóa và không điều chỉnh tồn.

Yêu cầu chức năng liên quan: FR-INV-08, FR-INV-09.

**3.5 – Theo dõi tồn kho theo lô**

- **Tác nhân:** Bếp

- **Đầu vào:** Tên nguyên liệu, tiêu chí lọc, dữ liệu tồn theo lô, lượt giữ và ngưỡng cảnh báo.

- **Đầu ra:** Danh sách tồn sổ sách, đủ điều kiện bán, đang giữ, khả dụng và cảnh báo theo lô.

- **Nội dung xử lý:**

  - Bước 1. Người dùng chọn bộ lọc để xem tồn nguyên liệu và chi tiết theo lô.

  - Bước 2. Hệ thống hiển thị tồn sổ sách, lượng đủ điều kiện sử dụng, lượng giữ và lượng khả dụng, kèm cảnh báo tồn thấp hoặc hạn sử dụng theo quy tắc của từng nguyên liệu.

  - Bước 3. Người dùng xem thời điểm dữ liệu và chi tiết lô; nếu không có kết quả, thay đổi bộ lọc hoặc kết thúc.

Yêu cầu chức năng liên quan: FR-INV-07, FR-INV-10, FR-INV-11, FR-INV-12, FR-INV-14; FR-INV-13.

### 3.4.4. Module 4 - Báo cáo thống kê

**4.1 – Xem báo cáo doanh thu**

- **Tác nhân:** Quản lý

- **Đầu vào:** Khoảng ngày kinh doanh, loại đơn, phương thức thanh toán và kỳ so sánh nếu có.

- **Đầu ra:** Báo cáo doanh thu dạng bảng/biểu đồ và kết quả so sánh kỳ.

- **Nội dung xử lý:**

  - Bước 1. Quản lý chọn kỳ báo cáo và điều kiện lọc; hệ thống kiểm tra khoảng thời gian.

  - Bước 2. Hệ thống tổng hợp doanh thu theo ngày kinh doanh, loại order và phương thức thanh toán, đồng thời tính mức so sánh giữa các kỳ.

  - Bước 3. Hệ thống hiển thị bảng, biểu đồ hoặc thông báo không có dữ liệu.

Yêu cầu chức năng liên quan: FR-REP-01, FR-REP-08, FR-REP-09.

**4.2 – Xem chi phí và lợi nhuận gộp**

- **Tác nhân:** Quản lý

- **Đầu vào:** Tháng/kỳ báo cáo, dữ liệu nhập–tồn–tiêu hao, doanh thu và kỳ so sánh nếu có.

- **Đầu ra:** Chi phí nguyên liệu, lợi nhuận gộp và số liệu so sánh có phân loại nguồn chi phí.

- **Nội dung xử lý:**

  - Bước 1. Quản lý chọn kỳ báo cáo; hệ thống lấy dữ liệu nhập, tồn, tiêu hao và doanh thu liên quan.

  - Bước 2. Hệ thống tính chi phí nguyên liệu và lợi nhuận gộp, phân biệt giá vốn món bán, hao hụt và chi phí order hủy hoặc đóng chưa thu tiền theo FR-REP-04–06.

  - Bước 3. Hệ thống hiển thị kết quả, chi tiết theo món và so sánh giữa các kỳ; thông báo khi không có dữ liệu.

Yêu cầu chức năng liên quan: FR-REP-04, FR-REP-05, FR-REP-11, FR-REP-12, FR-REP-13, FR-REP-06; FR-REP-08–09.

**4.3 – Xem báo cáo tiêu thụ món**

- **Tác nhân:** Quản lý

- **Đầu vào:** Khoảng thời gian và tiêu chí xếp hạng theo số lượng bán hoặc doanh thu món.

- **Đầu ra:** Báo cáo lượng bán, doanh thu theo món và thứ hạng trong kỳ.

- **Nội dung xử lý:**

  - Bước 1. Quản lý chọn kỳ, tiêu chí xếp hạng và thứ tự sắp xếp món.

  - Bước 2. Hệ thống tổng hợp lượng bán, doanh thu và hiển thị danh sách món theo lựa chọn; nếu không có kết quả, Quản lý đổi tiêu chí hoặc kết thúc.

Yêu cầu chức năng liên quan: FR-REP-03; FR-REP-09.

**4.4 – Xem phân bố order theo khung giờ**

- **Tác nhân:** Quản lý

- **Đầu vào:** Khoảng ngày kinh doanh và lựa chọn phân bố theo khung giờ hoặc ngày trong tuần.

- **Đầu ra:** Bảng và biểu đồ số order, doanh thu theo thời gian.

- **Nội dung xử lý:**

  - Bước 1. Quản lý chọn kỳ báo cáo và cách nhóm khung giờ.

  - Bước 2. Hệ thống tổng hợp số order và doanh thu theo khung giờ, hiển thị bảng, biểu đồ hoặc thông báo không có dữ liệu.

Yêu cầu chức năng liên quan: FR-REP-07; FR-REP-09.

**4.5 – Xem báo cáo order và thanh toán**

- **Tác nhân:** Quản lý

- **Đầu vào:** Khoảng ngày kinh doanh, nhóm trạng thái order và dữ liệu thanh toán/xác minh.

- **Đầu ra:** Danh sách và thống kê order hủy, đóng chưa thu tiền, thanh toán chưa hoàn tất.

- **Nội dung xử lý:**

  - Bước 1. Quản lý chọn kỳ và nhóm order cần theo dõi: chờ xác minh, mở lại thanh toán, bị hủy hoặc đóng chưa thu được tiền.

  - Bước 2. Hệ thống tổng hợp số lượng, giá trị và chi phí tương ứng, hiển thị lý do, người xử lý, thời điểm và lịch sử.

  - Bước 3. Quản lý mở chi tiết để kiểm tra; các khoản cần đối soát được xử lý theo UC 2.6. Kết quả xử lý tiếp theo được cập nhật vào báo cáo và giữ lịch sử.

Yêu cầu chức năng liên quan: FR-REP-02, FR-REP-10; FR-REP-09.

### 3.4.5. Module 5 - Cài đặt hệ thống

**5.1 – Quản lý người dùng**

- **Tác nhân:** Quản lý

- **Đầu vào:** Thông tin tài khoản, vai trò được gán và yêu cầu tạo/sửa/khóa/đặt lại mật khẩu.

- **Đầu ra:** Tài khoản và quyền được cập nhật hoặc thông báo từ chối; nhật ký quản trị được lưu.

- **Nội dung xử lý:**

  - Bước 1. Quản lý mở danh sách, chọn tạo hoặc sửa tài khoản, gán vai trò, khóa tài khoản hoặc đặt lại mật khẩu.

  - Bước 2. Hệ thống kiểm tra dữ liệu và điều kiện thao tác; nếu không hợp lệ, thông báo để Quản lý xử lý.

  - Bước 3. Hệ thống lưu thay đổi và nhật ký; phiên truy cập và quyền được cập nhật theo tình trạng tài khoản.

Yêu cầu chức năng liên quan: FR-SET-01, FR-SET-03; FR-SET-02 (đặt lại mật khẩu hộ người dùng, xem UC 5.4); FR-SET-06.

**5.2 – Cấu hình hệ thống**

- **Tác nhân:** Quản lý

- **Đầu vào:** Các tham số cấu hình gồm mẫu hóa đơn, mốc ngày kinh doanh, ngưỡng cảnh báo, thời gian giữ món và hạn mức AI.

- **Đầu ra:** Cấu hình hợp lệ được lưu với thời điểm áp dụng hoặc thông báo lỗi.

- **Nội dung xử lý:**

  - Bước 1. Quản lý xem cấu hình hiện tại và nhập giá trị cần thay đổi.

  - Bước 2. Hệ thống kiểm tra giá trị; nếu không hợp lệ, yêu cầu chỉnh sửa. Quản lý kiểm tra và xác nhận lưu.

  - Bước 3. Hệ thống lưu cấu hình, ghi nhật ký và áp dụng theo thời điểm hiệu lực của từng tham số; ngưỡng tồn riêng của nguyên liệu được ưu tiên khi có khai báo.

Yêu cầu chức năng liên quan: FR-SET-04, FR-SET-05; FR-SET-06.

**5.3 – Xem nhật ký hệ thống**

- **Tác nhân:** Quản lý

- **Đầu vào:** Khoảng thời gian, người thực hiện, loại thao tác và đối tượng cần tra cứu nhật ký.

- **Đầu ra:** Danh sách nhật ký phù hợp và chi tiết dữ liệu trước/sau của bản ghi.

- **Nội dung xử lý:**

  - Bước 1. Quản lý nhập tiêu chí tra cứu; hệ thống hiển thị nhật ký theo quyền hoặc thông báo không có kết quả.

  - Bước 2. Quản lý mở chi tiết để xem thông tin trước và sau thao tác; có thể tiếp tục tra cứu, không sửa hoặc xóa nhật ký.

Yêu cầu chức năng liên quan: FR-SET-06, FR-SET-07.

**5.4 – Đăng nhập và quản lý tài khoản cá nhân**

- **Tác nhân:** Người dùng (Quản lý, Thu ngân/Nhân viên order, Bếp)

- **Đầu vào:** Thông tin đăng nhập của tài khoản được cấp; yêu cầu đăng xuất; thông tin xác nhận mật khẩu hiện tại và mật khẩu mới của chính người dùng.

- **Đầu ra:** Phiên đăng nhập hợp lệ và phạm vi chức năng theo vai trò hoặc thông báo đăng nhập thất bại; phiên kết thúc khi đăng xuất; mật khẩu cá nhân được cập nhật hoặc thông báo lỗi.

- **Nội dung xử lý:**

  - Bước 1. Người dùng nhập thông tin đăng nhập; hệ thống kiểm tra và từ chối nếu thiếu, sai thông tin hoặc tài khoản bị khóa. Khi hợp lệ, hệ thống tạo phiên và hiển thị chức năng theo vai trò.

  - Bước 2. Khi đổi mật khẩu, người dùng nhập mật khẩu hiện tại và mật khẩu mới; hệ thống kiểm tra, lưu mật khẩu mới hoặc yêu cầu nhập lại. Việc Quản lý đặt lại mật khẩu được thực hiện tại UC 5.1.

  - Bước 3. Khi đăng xuất, hệ thống kết thúc phiên tại giao diện và máy chủ; các lượt giữ món được xử lý theo thời hạn quy định. Lần truy cập tiếp theo yêu cầu đăng nhập.

Yêu cầu chức năng liên quan: FR-SET-02; FR-SET-03.

### 3.4.6. Module 6 - AI Assistant

**6.1 – Hỏi AI Assistant**

- **Tác nhân:** Người dùng (Quản lý, Thu ngân/Nhân viên order, Bếp); Claude API của Anthropic (hệ thống ngoài)

- **Đầu vào:** Câu hỏi tiếng Việt, phiên hội thoại, người dùng/vai trò, thời gian và đối tượng được hỏi.

- **Đầu ra:** Câu trả lời kèm dữ liệu/phạm vi, yêu cầu làm rõ hoặc thông báo không thể trả lời.

- **Nội dung xử lý:**

  - Bước 1. Người dùng nhập câu hỏi; hệ thống kiểm tra phiên, quyền và hạn mức. Nếu không đủ điều kiện, thông báo và kết thúc yêu cầu.

  - Bước 2. Hệ thống xác định nội dung, thời gian và phạm vi dữ liệu; nếu thiếu thông tin, hỏi lại người dùng, nếu vượt quyền thì từ chối.

  - Bước 3. Hệ thống lấy dữ liệu phù hợp, kiểm duyệt truy vấn chỉ đọc và tạo câu trả lời. Khi không thể xử lý hoặc dịch vụ gặp lỗi, hệ thống thông báo và hướng dẫn người dùng.

  - Bước 4. Hệ thống trả lời bằng tiếng Việt, kèm bảng hoặc biểu đồ khi phù hợp, cho xem chi tiết và lịch sử hội thoại theo quyền.

Yêu cầu chức năng liên quan: FR-AI-01, FR-AI-02, FR-AI-03, FR-AI-04, FR-AI-05, FR-AI-06, FR-AI-07, FR-AI-08, FR-AI-09, FR-AI-10.

## I. Danh mục Use Case và đối chiếu nghiệp vụ

Danh mục gồm 30 Use Case thuộc sáu nhóm: Quản lý danh mục (1.1–1.7), Quản lý bán hàng (2.1–2.8), Quản lý kho (3.1–3.5), Báo cáo thống kê (4.1–4.5), Cài đặt hệ thống (5.1–5.4) và AI Assistant (6.1). Mã UC biểu thị nhóm và nghiệp vụ; mã FR của từng Use Case được ghi tại Bảng 5 và định nghĩa tại Phụ lục K. “Người dùng” trong bảng chỉ chung ba vai trò này; tác nhân ngoài được ghi kèm khi tham gia tương tác.

| **Mã UC** | **Mục tiêu**                                   | **Tác nhân trực tiếp**                    |
|-----------|------------------------------------------------|-------------------------------------------|
| 1.1       | Quản lý nhóm món                               | Quản lý                                   |
| 1.2       | Quản lý món ăn                                 | Quản lý                                   |
| 1.3       | Quản lý công thức                              | Quản lý                                   |
| 1.4       | Quản lý giá bán                                | Quản lý                                   |
| 1.5       | Quản lý bàn                                    | Quản lý                                   |
| 1.6       | Quản lý nguyên liệu                            | Bếp                                       |
| 1.7       | Quản lý nhà cung cấp                           | Bếp                                       |
| 2.1       | Gọi món tại chỗ                                | Thu ngân/Nhân viên order                  |
| 2.2       | Gọi món mang về                                | Thu ngân/Nhân viên order                  |
| 2.3       | Quản lý order và phục vụ                       | Thu ngân/Nhân viên order                  |
| 2.4       | Thanh toán                                     | Thu ngân/Nhân viên order                  |
| 2.5       | Thanh toán QR                                  | Thu ngân/Nhân viên order; Cổng thanh toán |
| 2.6       | Xử lý xác minh thanh toán và khoản QR ngoại lệ | Quản lý                                   |
| 2.7       | Hủy toàn bộ order                              | Quản lý                                   |
| 2.8       | Tra cứu order                                  | Quản lý; Thu ngân/Nhân viên order         |
| 3.1       | Nhập kho theo lô                               | Bếp                                       |
| 3.2       | Theo dõi xuất nguyên liệu                      | Bếp                                       |
| 3.3       | Lập phiếu xuất hủy                             | Bếp                                       |
| 3.4       | Kiểm kê và điều chỉnh tồn                      | Bếp                                       |
| 3.5       | Theo dõi tồn kho theo lô                       | Bếp                                       |
| 4.1       | Xem báo cáo doanh thu                          | Quản lý                                   |
| 4.2       | Xem chi phí và lợi nhuận gộp                   | Quản lý                                   |
| 4.3       | Xem báo cáo tiêu thụ món                       | Quản lý                                   |
| 4.4       | Xem phân bố order theo khung giờ               | Quản lý                                   |
| 4.5       | Xem báo cáo order và thanh toán                | Quản lý                                   |
| 5.1       | Quản lý người dùng                             | Quản lý                                   |
| 5.2       | Cấu hình hệ thống                              | Quản lý                                   |
| 5.3       | Xem nhật ký hệ thống                           | Quản lý                                   |
| 5.4       | Đăng nhập và quản lý tài khoản cá nhân         | Người dùng                                |
| 6.1       | Hỏi AI Assistant                               | Người dùng; Claude API của Anthropic      |

Nhóm 1: UC 1.2 bao gồm cập nhật, tra cứu, xóa mềm và tạm dừng/mở lại phục vụ món. UC 1.3 quản lý công thức, phiên bản và lịch áp dụng; UC 1.4 quản lý giá bán, lịch sử và lịch thay đổi. Xem thực đơn và sơ đồ bàn để gọi món được thực hiện trong luồng bán hàng.

Nhóm 2: UC 2.3 — Quản lý order và phục vụ gồm gọi thêm cho order tại chỗ hoặc mang về Đang mở, riêng tại chỗ phải còn gắn đúng bàn; đổi bàn chỉ cho order tại chỗ Đang mở còn gắn bàn; giảm/hủy món khi được phép sửa và Bếp xác nhận chưa làm; cập nhật phục vụ cho cả tại chỗ và mang về, kể cả sau thanh toán; giải phóng bàn khi khách rời, độc lập trạng thái order. Các nhánh tuân theo điều kiện tại mục 3.4. UC 2.4 bao gồm phiếu tạm tính, chọn phương thức, thanh toán tiền mặt và phát hành hóa đơn. UC 2.5 mở rộng UC 2.4 khi chọn QR, gồm tạo/hủy mã, nhận kết quả và các nhánh quét lỗi, hết hạn hoặc yêu cầu xác minh. UC 2.6 gồm đối soát, xác nhận đã nhận tiền, tiếp tục chờ, mở lại thanh toán, đóng chưa thu và xử lý khoản QR ngoại lệ. UC 2.8 gồm tra cứu order, hóa đơn, phiếu bếp và in lại chứng từ hợp lệ.

Nhóm 3: UC 3.1 ghi nhận phiếu nhập và lô nguyên liệu; UC 3.2 cho phép Bếp tra cứu xuất, hoàn và đối chiếu lô, với tiêu hao được hệ thống ghi khi gửi món, không có thao tác xác nhận xuất thêm; UC 3.3 lập chứng từ xuất hủy; UC 3.4 ghi nhận kiểm kê và điều chỉnh tồn. UC 3.5 hiển thị tồn sổ sách, lượng đang giữ, lượng khả dụng, chi tiết lô và cảnh báo tồn thấp/hạn sử dụng. Phân bổ FIFO và giữ nguyên liệu là quy tắc xử lý của các luồng liên quan.

Nhóm 4: UC 4.1 và UC 4.2 hỗ trợ so sánh hai khoảng thời gian. UC 4.3 trình bày lượng bán và xếp hạng món; UC 4.4 trình bày phân bố order theo khung giờ. UC 4.5 chỉ tra cứu, thống kê order hủy, order đóng chưa thu được tiền và thanh toán chưa hoàn tất; quyết định xử lý khoản tiền thuộc nhóm bán hàng.

Nhóm 5: UC 5.1 bao gồm đặt lại mật khẩu cho người dùng, cùng các thao tác quản trị tài khoản và vai trò. UC 5.2 tập hợp các tham số cấu hình hệ thống: mẫu hóa đơn, ngưỡng cảnh báo, thời hạn giữ món, hạn mức AI và mốc giờ ngày kinh doanh. UC 5.4 gồm đăng nhập, đăng xuất và đổi mật khẩu của chính người dùng.

Nhóm 6: UC 6.1 bao gồm hỏi đáp theo quyền, làm rõ yêu cầu, xem dữ liệu trả lời và tùy chọn xem chi tiết kỹ thuật. Hạn mức, kiểm soát quyền và bộ nhớ đệm được áp dụng trong quá trình xử lý câu hỏi.

### Đối chiếu mô hình tương tác

Mỗi nghiệp vụ chính được đối chiếu giữa điều kiện trước, tác nhân, trình tự xử lý, nhánh ngoại lệ và dữ liệu sau xử lý. Gọi món tại chỗ và mang về có luồng riêng; giữ món và xuất FIFO có thể được tham chiếu dùng chung. Thanh toán tiền mặt, QR và xác minh có luồng riêng. Nghiệp vụ món ăn, công thức, giá bán và nghiệp vụ nhập kho, xuất hủy, kiểm kê được mô tả riêng. Một UC có thể có nhiều sơ đồ cho các kịch bản; nhánh điều kiện trong cùng luồng được biểu diễn bằng alt/opt, tương tác dùng chung bằng ref.

## K. Yêu cầu chức năng chi tiết

Các yêu cầu chức năng được tổ chức theo sáu module và gắn với mã Use Case tại mục 3.4. Mỗi mã FR xác định nội dung xử lý, điều kiện và ngoại lệ làm căn cứ thiết kế và kiểm thử.

### K.1. Quản lý danh mục

- **FR-CAT-01 – Quản lý nhóm món:** Quản lý được thêm, sửa, xóa, sắp xếp danh sách nhóm món, làm cơ sở phân loại món ăn.

- **FR-CAT-03 – Điều kiện xóa nhóm món:** Một nhóm món còn ít nhất một món ăn chưa xóa mềm thì không cho xóa nhóm; nhóm chỉ xóa được khi toàn bộ món từng thuộc nhóm đã ở trạng thái xóa mềm. Nhóm chưa từng có món nào được xóa vĩnh viễn. Việc xóa nhóm món được ghi vào audit log (FR-SET-06).

- **FR-CAT-02 – Quản lý món ăn:** Quản lý được thêm, sửa, xóa, tìm kiếm món ăn với các thuộc tính: tên, giá bán, nhóm món (mỗi món chọn đúng một nhóm), hình ảnh.

- **FR-CAT-04 – Xóa món ăn là xóa mềm:** Món vẫn được lưu và hiển thị trong danh mục quản trị (tra cứu, báo cáo, lịch sử order cũ) nhưng biến mất khỏi các màn hình vận hành; không có chức năng xóa vĩnh viễn (hard delete) món ăn. Việc xóa mềm món ăn được ghi vào audit log (FR-SET-06).

- **FR-CAT-05 – Xử lý thay đổi đang chờ khi xóa mềm món:** Nếu món bị xóa mềm trong khi đang có thay đổi giá/công thức “chờ áp dụng”, hệ thống tự động hủy thay đổi đang chờ đó.

- **FR-CAT-06 – Trạng thái mặc định của món mới tạo:** Món ăn mới tạo mặc định ở trạng thái “Nháp - chưa cấu hình công thức” (chưa hiển thị ở màn hình gọi món), cho đến khi được gán công thức chế biến lần đầu.

- **FR-CAT-11 – Chuyển trạng thái món khi được gán công thức lần đầu:** Ngay khi được gán công thức lần đầu, món rời trạng thái “Nháp”; TrangThai được tính thành “Hoạt động”, “Hết nguyên liệu” hoặc “Tạm dừng phục vụ” theo tồn kho và cờ thủ công. Công thức mặc định đầu tiên này có hiệu lực ngay khi được gán, không áp dụng cơ chế lên lịch theo Business Date kế tiếp của FR-CAT-08.

- **FR-CAT-26 – Tạm dừng/mở lại phục vụ món thủ công:** Quản lý có thể tạm dừng phục vụ một món thủ công bằng cách bật cờ TamDungThuCong. Cờ này độc lập với HetNguyenLieu được tính từ tồn khả dụng theo công thức (FR-INV-10). Khi chỉ tạm dừng thủ công, màn hình ghi “Tạm dừng phục vụ”; khi thiếu tồn, ghi “Hết nguyên liệu”. Món bị chặn gọi trong cả hai trường hợp.

- **FR-CAT-27 – Trạng thái phục vụ của món:** ChuaCoCongThuc=true xác định món Nháp và ẩn khỏi gọi món. Khi đã có công thức, HetNguyenLieu được tính theo FR-INV-10; TamDungThuCong do Quản lý điều khiển. Món cho chọn thêm khi chưa xóa, không tạm dừng và đủ nguyên liệu khả dụng. Trường hợp thiếu nguyên liệu hiển thị “Hết nguyên liệu”; quản trị hiển thị đồng thời các lý do chặn. Dòng đã giữ được kiểm tra theo phạm vi giữ riêng khi gửi. HetNguyenLieu là thuộc tính dẫn xuất, không lưu trong MON_AN.

- **FR-CAT-28 – Trạng thái xóa độc lập:** Xóa món (FR-CAT-04) là trạng thái riêng biệt (xóa mềm), độc lập với Hoạt động/Hết nguyên liệu/Tạm dừng phục vụ/Nháp.

- **FR-CAT-07 – Gán công thức chế biến:** Mỗi món ăn gắn với một công thức chế biến, gồm danh sách nguyên liệu và định lượng tương ứng theo đúng đơn vị tính.

- **FR-CAT-08 – Lên lịch áp dụng thay đổi công thức theo Business Date:** Quản lý chọn Business Date áp dụng cho thay đổi công thức; mặc định là Business Date kế tiếp, Quản lý có thể chọn sang bất kỳ Business Date nào trong tương lai nhưng không được chọn Business Date đã bắt đầu hoặc đã kết thúc. Phiên bản mới có hiệu lực từ đúng mốc giờ bắt đầu của Business Date được chọn, áp dụng cho các dòng món được gửi từ thời điểm đó trở đi và không ảnh hưởng đến các dòng món đã ghi nhận trước thời điểm hiệu lực; hệ thống lưu lịch sử các phiên bản công thức.

- **FR-CAT-09 – Giới hạn một thay đổi công thức đang chờ áp dụng:** Mỗi món ăn chỉ có tối đa một thay đổi công thức “chờ áp dụng” tại một thời điểm; thay đổi mới ghi đè thay đổi cũ, việc ghi đè này được ghi vào audit log (FR-SET-06) tương tự thao tác hủy chủ động.

- **FR-CAT-10 – Hủy thay đổi công thức đang chờ áp dụng:** Quản lý có thể hủy một thay đổi công thức đang “chờ áp dụng” trước khi có hiệu lực. Thao tác hủy được ghi vào audit log (FR-SET-06).

- **FR-CAT-23 – Sửa trực tiếp giá bán/công thức đang áp dụng:** Quản lý có thể sửa trực tiếp giá/công thức hiện tại, áp dụng ngay, dành cho khắc phục gấp sai sót đã tồn tại; ghi vào audit log (FR-SET-06).

- **FR-CAT-24 – Không ảnh hưởng đến thay đổi đang chờ áp dụng theo lịch:** Sửa trực tiếp và lên lịch theo Business Date là hai cơ chế độc lập; sửa trực tiếp không hủy/ghi đè thay đổi đang chờ theo lịch.

- **FR-CAT-25 – Ghi nhận phiên bản khi sửa trực tiếp:** Mỗi lần sửa trực tiếp được ghi thành một phiên bản mới trong lịch sử giá/công thức, hiệu lực đúng thời điểm sửa.

- **FR-CAT-20 – Cập nhật giá bán và lên lịch theo Business Date:** Cập nhật giá bán và chọn Business Date áp dụng; mặc định là Business Date kế tiếp, Quản lý có thể chọn sang bất kỳ Business Date nào trong tương lai nhưng không được chọn Business Date đã bắt đầu hoặc đã kết thúc. Phiên bản giá mới có hiệu lực từ đúng mốc giờ bắt đầu của Business Date được chọn, áp dụng cho các dòng món được gửi từ thời điểm đó trở đi; giá của các dòng món đã ghi nhận được giữ nguyên.

- **FR-CAT-21 – Giới hạn một thay đổi giá đang chờ áp dụng:** Tối đa một thay đổi giá “chờ áp dụng” cho mỗi món tại một thời điểm; thay đổi mới ghi đè, việc ghi đè này được ghi vào audit log (FR-SET-06) tương tự thao tác hủy chủ động.

- **FR-CAT-22 – Hủy thay đổi giá đang chờ áp dụng:** Quản lý có thể hủy thay đổi giá “chờ áp dụng” trước khi có hiệu lực. Thao tác hủy được ghi vào audit log (FR-SET-06).

- **FR-CAT-17 – Quản lý sơ đồ bàn:** Quản lý thêm/sửa/xóa bàn; Thu ngân/Nhân viên order xem trạng thái Trống/Đang phục vụ và xác nhận giải phóng bàn khi khách rời đi (FR-CAT-18).

- **FR-CAT-19 – Điều kiện xóa bàn:** Không cho xóa bàn ở trạng thái Đang phục vụ. Bàn đã từng gắn với order lịch sử chỉ được xóa mềm. Việc xóa bàn được ghi vào audit log (FR-SET-06).

- **FR-CAT-12 – Quản lý nguyên liệu:** Quản lý, Bếp thêm/sửa/xóa/tìm kiếm nguyên liệu: tên, đơn vị tính, mức tồn tối thiểu riêng (nếu không cấu hình, nguyên liệu dùng mức tồn tối thiểu mặc định của hệ thống).

- **FR-CAT-13 – Xóa nguyên liệu theo nguyên tắc xóa mềm:** Nguyên liệu đã có trong công thức chế biến hoặc phiếu nhập kho lịch sử chỉ được xóa mềm. Việc xóa được ghi vào audit log (FR-SET-06).

- **FR-CAT-14 – Khóa sửa đơn vị tính sau khi đã tham chiếu:** Một khi nguyên liệu đã có phiếu nhập kho hoặc dùng trong công thức, hệ thống khóa không cho sửa đơn vị tính nữa.

- **FR-CAT-15 – Quản lý nhà cung cấp:** Quản lý, Bếp quản lý danh sách nhà cung cấp: thông tin liên hệ, lịch sử nhập hàng.

- **FR-CAT-16 – Xóa nhà cung cấp theo nguyên tắc xóa mềm:** Nhà cung cấp đã có lịch sử nhập hàng chỉ được xóa mềm. Việc xóa được ghi vào audit log (FR-SET-06).

### K.2. Quản lý bán hàng

- **FR-SALE-01 – Chọn món và giữ món:** Nhân viên tạo lượt chọn cho bàn Trống hoặc đơn mang về. Mỗi món được thêm thành một dòng GIU_CHO_MON trên server, gắn người thao tác, mã lượt chọn, phiên bản giá/công thức, số lượng và thời điểm hết hạn. Hệ thống chỉ chấp nhận dòng khi giữ đủ nguyên liệu. Lượt chọn chưa tạo ORDER, chưa chiếm bàn và chưa tạo phiếu bếp.

- **FR-SALE-02 – Ghi chú/yêu cầu đặc biệt cho món:** Nhân viên order nhập ghi chú văn bản tự do cho từng món (ví dụ: “không hành”); ghi chú gắn với từng dòng món, không bắt buộc, in kèm trên phiếu bếp; không ảnh hưởng công thức hay trừ kho.

- **FR-SALE-03 – Gửi món và ghi nhận order:** Khi gửi lượt chọn, backend kiểm tra quyền, bàn, trạng thái món, phiên bản giá/công thức và lượng nguyên liệu đáp ứng. Trong một transaction, hệ thống tạo order và các dòng món, phân bổ tiêu hao theo FIFO, ghi giao dịch kho, kết thúc các lượt giữ và tạo dữ liệu phiếu bếp. Bàn tại chỗ chuyển Đang phục vụ; order mang về không gắn bàn. In phiếu được thực hiện sau khi commit, lỗi in được xử lý bằng in lại. Mã yêu cầu gửi duy nhất bảo đảm gửi lại chỉ trả kết quả đã ghi nhận.

- **FR-SALE-04 – Sinh mã order tự động:** Hệ thống tự sinh mã order theo định dạng ORD-ddMMyy-nnn (ví dụ minh họa: ORD-270826-015), trong đó nnn bắt đầu từ 001 cho mỗi Business Date và tăng tuần tự trong Business Date đó; mã order là duy nhất trong toàn hệ thống, giữ nguyên suốt vòng đời order và dùng làm định danh tra cứu. Nếu transaction rollback làm phát sinh khoảng số bị bỏ trống, số đã cấp không được tái sử dụng.

- **FR-SALE-05 – Xử lý lượt giữ hết hạn và dữ liệu thay đổi:** Khi hết hạn, dòng món vẫn hiển thị trong lượt chọn với nhãn “Hết thời gian giữ món”. Lúc gửi, backend kiểm tra lại khả dụng và phiên bản hiện hành. Nếu đủ, hệ thống tiếp nhận lượt gửi; nếu thiếu, hệ thống thông báo món và số lượng không đáp ứng, giữ danh sách để nhân viên trao đổi với khách. Khi giá hoặc công thức thay đổi, nhân viên xác nhận nội dung mới trước khi gửi. Lượt gửi chỉ được ghi nhận khi toàn bộ các dòng được xác nhận đều hợp lệ; các lượt giữ đã hết hạn không được tự gia hạn.

- **FR-SALE-08 – Điều chỉnh và giải phóng giữ món:** Backend giữ nguyên liệu theo công thức khi thêm món; tăng số lượng chỉ được chấp nhận khi giữ đủ phần tăng và làm mới thời hạn của dòng. Giảm số lượng giải phóng phần giảm; xóa dòng hoặc chọn “Hủy lượt chọn” (Cancel) giải phóng toàn bộ phần giữ tương ứng. Mở màn hình, sửa ghi chú hoặc thao tác dòng khác không gia hạn. Mất mạng hoặc đóng trình duyệt để lượt giữ hết hạn theo giờ server. Thời hạn lấy từ ThoiGianGiuChoPhut tại FR-SET-04; giữ món không khóa toàn bộ món ở bàn khác.

- **FR-SALE-24 – Ghi nhận mốc thời gian giao dịch:** Mọi giao dịch bán hàng ghi nhận kèm mốc thời gian chi tiết, làm đầu vào cho Báo cáo và AI Assistant.

- **FR-SALE-31 – In phiếu bếp tự động:** Khi gửi món hoặc gửi thêm món, hệ thống gửi lệnh in phiếu bếp qua máy in nhiệt, gồm bàn/mã đơn, danh sách món, số lượng, ghi chú riêng.

- **FR-SALE-32 – Xử lý khi in phiếu bếp thất bại:** Nếu lệnh in thất bại, hệ thống hiển thị cảnh báo lỗi; nhân viên chủ động bấm in lại sau khi khắc phục sự cố máy in, không giới hạn số lần in lại.

- **FR-CAT-18 – Giải phóng bàn theo việc sử dụng thực tế:** Bàn chuyển sang Đang phục vụ khi order tại chỗ được tạo. Khi khách rời đi, Thu ngân/Nhân viên order xác nhận giải phóng bàn; bàn về Trống để nhận order mới ngay, kể cả order cũ còn Chờ xác minh thanh toán. Bàn nguồn cũng về Trống khi đổi bàn; order bị hủy toàn bộ thì bàn về Trống nếu khách đã rời đi. Thanh toán thành công, duyệt đối soát hoặc đóng order chưa thu được tiền không tự giải phóng lại bàn. Giải phóng bàn kết thúc các lượt chọn gọi thêm chưa gửi gắn order và giải phóng lượng giữ tương ứng. Tạo order tại bàn, đổi bàn và giải phóng bàn phải cập nhật BAN.TrangThai và BAN.MaOrderDangPhucVu trong cùng transaction, khóa dòng bàn và kiểm tra lại bàn Trống/chưa gắn order trước khi nhận order mới; mỗi bàn chỉ gắn tối đa một order đang phục vụ. Thao tác giải phóng chỉ áp dụng nếu bàn còn gắn với đúng order đang phục vụ; order cũ được xử lý thanh toán muộn không được đổi trạng thái bàn của order mới. Ghi người thực hiện và thời điểm giải phóng vào audit log (FR-SET-06).

- **FR-SALE-06 – Gọi thêm cho order đang mở:** Nhân viên tạo lượt chọn gọi thêm gắn với order tại chỗ hoặc mang về ở trạng thái “Đang mở”. Với order tại chỗ, bàn phải còn phục vụ đúng order; order mang về không gắn bàn. Món gọi thêm được giữ nguyên liệu theo FR-SALE-08 và chỉ trừ tồn khi nhân viên gửi phần gọi thêm thành công. Mỗi lần gửi tạo dòng món và phiếu bếp cho phần mới; các dòng đã gửi giữ nguyên giá và công thức, phần mới dùng phiên bản hợp lệ sau kiểm tra theo FR-SALE-05. Mã yêu cầu gửi duy nhất bảo đảm gửi lại không tạo thêm dòng, phiếu bếp hoặc tiêu hao. Order đang chờ xác nhận thanh toán, chờ xác minh, đã thanh toán, bị hủy hoặc đã đóng không được gọi thêm. Khách mua thêm sau khi order đã thanh toán, bị hủy hoặc đã đóng thì lập order mới.

- **FR-SALE-07 – Điều kiện giảm số lượng/xóa món đã có trong order:** Nhân viên chỉ được giảm số lượng hoặc xóa món ở trạng thái “Chờ làm”; nguyên liệu tương ứng được hoàn kho theo quy tắc hủy món. Từ trạng thái “Đã xác nhận xong” trở đi, món không được sửa hoặc xóa. Tăng số lượng được xử lý như thêm món theo FR-SALE-06 và FR-SALE-08. Việc in phiếu bếp không làm thay đổi trạng thái món. Trước khi hủy hoặc giảm số lượng món đã in phiếu, Thu ngân/Nhân viên order trao đổi trực tiếp với Bếp để xác nhận món chưa bắt đầu chế biến. Bước trao đổi này nằm ngoài hệ thống và không được hệ thống ghi nhận.

- **FR-SALE-09 – Trạng thái xử lý của món:** Mỗi dòng món của order tại chỗ hoặc mang về có trạng thái Chờ làm → Đã xác nhận xong → Đã phục vụ; nhân viên cập nhật dựa trên xác nhận thực tế từ Bếp và việc giao món. Cập nhật phục vụ được phép sau thanh toán nếu dòng món chưa hủy; chỉ thay đổi trạng thái/thời điểm, không thay đổi nội dung hoặc số tiền order đã khóa.

- **FR-SALE-10 – Hủy một món trong order:** Chỉ hủy được món đang “Chờ làm”; mỗi lượt hủy ghi lại người thực hiện, thời điểm, số lượng, lý do (audit log).

- **FR-SALE-11 – Xử lý order khi toàn bộ món đã gửi bị hủy:** Order tiếp tục “Đang mở” để tiếp nhận gọi thêm theo FR-SALE-06. Quản lý hủy toàn bộ order theo FR-SALE-27; nguyên liệu được xử lý theo FR-SALE-28. Bàn chỉ về Trống khi khách đã rời đi theo FR-CAT-18.

- **FR-SALE-12 – Đổi bàn cho order đang mở:** Chuyển order từ bàn hiện tại sang bàn Trống khác, khi order ở trạng thái “Đang mở”, bàn nguồn còn Đang phục vụ và BAN.MaOrderDangPhucVu trỏ tới đúng order này; sau khi giải phóng bàn thì không được đổi bàn cho order cũ; bàn đích chuyển Đang phục vụ, bàn nguồn về Trống. Thao tác đổi bàn được ghi vào audit log (FR-SET-06).

- **FR-SALE-13 – Chọn phương thức thanh toán:** Sau khi đưa phiếu tạm tính cho khách kiểm tra theo FR-SALE-21 và chốt nội dung order, Thu ngân chọn phương thức: tiền mặt hoặc quét mã QR do hệ thống tạo cho order; hóa đơn chỉ phát hành sau khi thanh toán thành công. Với tiền mặt, Thu ngân xác nhận đã nhận đủ tiền; hệ thống tạo giao dịch tiền mặt ở trạng thái “Thành công”, phát hành hóa đơn và chuyển order sang “Đã thanh toán” trong cùng transaction, không có trạng thái chờ. Trước khi chốt thanh toán, nhân viên xử lý toàn bộ lượt chọn gọi thêm gắn order bằng gửi hoặc bỏ lượt; hệ thống kiểm tra điều kiện này tại backend.

- **FR-SALE-21 – In phiếu tạm tính và hóa đơn:** Khi khách yêu cầu thanh toán, Thu ngân in phiếu tạm tính từ dữ liệu order để khách kiểm tra chi tiết từng món, số lượng, thành tiền và tổng tiền trước khi trả tiền. Phiếu ghi rõ “PHIẾU TẠM TÍNH - CHƯA THANH TOÁN”, có thể in lại sau khi sửa order hợp lệ. Phiếu chỉ phục vụ đối chiếu, không tạo bản ghi HOA_DON, không ghi nhận doanh thu và không khóa order. Việc sửa/hủy món vẫn tuân theo FR-SALE-06, FR-SALE-07 và FR-SALE-10; khi đã bắt đầu giao dịch thanh toán thì áp dụng các khóa theo trạng thái giao dịch. Sau khi tiền mặt được Thu ngân xác nhận đã nhận, hoặc QR được xác nhận thành công qua webhook/đối soát, hệ thống mới phát hành và in hóa đơn đã thanh toán, gồm chi tiết từng món, thành tiền, tổng tiền. Hóa đơn đã phát hành chỉ được in lại nguyên trạng theo FR-SALE-26.

- **FR-SALE-22 – Khóa order theo trạng thái thanh toán:** Order “Chờ xác nhận thanh toán”, “Chờ xác minh thanh toán”, “Đã thanh toán” hoặc “Đóng – chưa thu được tiền” bị khóa thêm/sửa/hủy món, hủy toàn bộ order và tạo giao dịch thanh toán mới. Hóa đơn đã phát hành không được sửa/hủy. Khóa nội dung không chặn cập nhật chế biến/giao món hợp lệ theo FR-SALE-09 hoặc giải phóng bàn theo FR-CAT-18. Khi mã QR hết hạn hoặc được hủy, order về “Đang mở” và được xử lý theo các điều kiện của order đang mở.

- **FR-SALE-14 – Thanh toán QR:** Khi Thu ngân chọn thanh toán QR, hệ thống tạo một giao dịch QR cho đúng order với số tiền bằng đúng số tiền phải thanh toán; giao dịch khởi tạo ở trạng thái “Chờ xác nhận” và có thời hạn 10 phút kể từ thời điểm tạo. Trong thời gian giao dịch QR hiện tại còn hiệu lực, hệ thống không tạo thêm một giao dịch QR khác cho cùng order. Khi giao dịch QR được tạo, order chuyển sang “Chờ xác nhận thanh toán”.

- **FR-SALE-15 – Xác nhận thanh toán QR qua webhook:** Backend xác thực webhook, đối chiếu mã giao dịch, order và số tiền. Xác nhận hợp lệ chuyển giao dịch sang “Thành công”, order sang “Đã thanh toán” và phát hành hóa đơn trong cùng transaction; xử lý idempotent để không tạo thêm hóa đơn hoặc cộng doanh thu lần nữa. Webhook không hợp lệ hoặc không xác định được giao dịch được ghi log để kiểm tra, không xác nhận thanh toán; webhook đúng giao dịch nhưng sai số tiền không xác nhận thanh toán và được xử lý như khoản ngoại lệ theo FR-SALE-16.

- **FR-SALE-16 – Tiền QR đến muộn và khoản ngoại lệ:** Webhook đến sau khi giao dịch đã “Hết hạn” hoặc “Đã hủy”, hoặc khi order “Chờ xác minh thanh toán”, được xác nhận tự động nếu đúng giao dịch, đủ tiền và order chưa mở lại thanh toán, chưa đóng hoặc hủy, chưa thanh toán bằng giao dịch khác. Khi đó, nếu order đang có giao dịch QR mới “Chờ xác nhận” chưa có tiền, hệ thống hủy giao dịch mới trong cùng transaction. Nếu order đã mở lại, đã đóng hoặc hủy, hoặc đã thanh toán bằng giao dịch khác, khoản nhận được đưa vào danh sách ngoại lệ theo MaGiaoDichCong duy nhất, không tự đổi order. Khoản đến muộn mà số tiền không còn khớp order (ví dụ order đã được sửa sau khi QR hết hạn) cũng vào danh sách ngoại lệ. Webhook lặp của khoản đã xác nhận thủ công được đối chiếu theo MaGiaoDichNganHang (duy nhất khi khác NULL) để ghi MaGiaoDichCong vào cùng giao dịch, không coi là khoản thu mới. Quản lý xử lý các khoản ngoại lệ theo FR-SALE-17.

- **FR-SALE-17 – Quản lý xử lý khoản QR ngoại lệ:** Quản lý đối chiếu sao kê các khoản trong danh sách ngoại lệ: (a) order mở lại nhưng chưa thu lần hai: áp dụng khoản cũ và hủy lần thử QR mới chưa có tiền; (b) order “Đóng – chưa thu được tiền”: áp dụng khoản nhận, chuyển “Đã thanh toán”, loại khỏi tổng hiện tại của FR-REP-10 và chuyển giá vốn từ FR-REP-13 sang FR-REP-11, giữ lịch sử đóng; (c) order đã thu lần hai, đã hủy, số tiền không còn khớp hoặc khoản không thể áp dụng: hoàn tiền ngoài hệ thống và lưu số tiền, mã tham chiếu, người thực hiện, thời điểm. Khi áp dụng phải khóa order và các giao dịch liên quan, kiểm tra lại chưa thanh toán, phát hành hóa đơn đúng một lần. Ngoại lệ chưa xử lý vẫn được theo dõi, không cộng vào doanh thu.

- **FR-SALE-18 – Mã QR hết hạn:** Sau 10 phút, nếu giao dịch vẫn ở trạng thái “Chờ xác nhận”, mã QR hết hạn; giao diện hiển thị “Mã QR hết hạn”. Giao dịch chuyển sang “Hết hạn”, order về “Đang mở”, cho phép Thu ngân chọn tiền mặt hoặc tạo mã QR mới theo FR-SALE-13–14. Nếu khách báo đã chuyển tiền, Thu ngân ghi nhận yêu cầu xác minh theo FR-SALE-19. Tiền về muộn được xử lý theo FR-SALE-16.

- **FR-SALE-19 – Ghi nhận yêu cầu xác minh thanh toán:** Khi khách báo đã chuyển tiền qua mã QR của hệ thống nhưng hệ thống chưa ghi nhận, Thu ngân chọn “Yêu cầu xác minh”, dù mã QR còn hiệu lực hay đã hết hạn. Giao dịch và order chuyển sang “Chờ xác minh thanh toán”; hệ thống không cho tạo giao dịch thanh toán mới. Thu ngân nhập mã giao dịch ngân hàng/ví điện tử do khách cung cấp, có thể đính kèm ảnh xác nhận và bổ sung thông tin. Ảnh xác nhận chỉ hỗ trợ đối soát, không thay thế việc xác nhận nhà hàng đã nhận tiền. Thao tác được ghi vào audit log, gồm nội dung, mã giao dịch/bằng chứng nếu có, người thực hiện và thời điểm.

- **FR-SALE-33 – Chủ động hủy mã QR:** Khi mã QR còn hiệu lực và giao dịch đang “Chờ xác nhận”, Thu ngân có thể chọn “Hủy mã QR”, chẳng hạn khi khách muốn đổi sang tiền mặt. Giao dịch chuyển sang “Đã hủy”, order về “Đang mở”, cho phép chọn tiền mặt hoặc tạo mã QR mới. Nếu khách báo đã chuyển tiền, Thu ngân chọn “Yêu cầu xác minh” theo FR-SALE-19. Thao tác được ghi vào audit log theo FR-SET-06.

- **FR-SALE-20 – Quản lý xác nhận đã nhận tiền và lưu kết quả đối soát:** Quản lý đối chiếu lịch sử giao dịch/sao kê tài khoản nhận của nhà hàng với mã giao dịch, số tiền và thời điểm. Khi xác minh đã nhận đủ tiền cho đúng order, Quản lý chọn “Xác nhận đã nhận tiền”. Hệ thống khóa và kiểm tra lại order/giao dịch, chuyển giao dịch sang “Thành công”, order sang “Đã thanh toán” và phát hành hóa đơn đúng một lần trong cùng transaction. Nếu chưa đủ căn cứ, hệ thống lưu kết quả kiểm tra và giữ trạng thái “Chờ xác minh thanh toán”. Việc tra soát ngân hàng và thỏa thuận với khách được thực hiện ngoài hệ thống; Quản lý cập nhật kết quả theo FR-SALE-34. Trạng thái chờ không tự đóng theo thời gian; danh sách FR-REP-02 hiển thị thời gian đã chờ. Nếu hệ thống nhận được xác nhận thanh toán hợp lệ trong thời gian này, khoản tiền được xử lý theo FR-SALE-15–16. Mỗi lần kiểm tra được ghi vào audit log, gồm nội dung, bằng chứng nếu có, người thực hiện, thời điểm và kết quả.

- **FR-SALE-23 – Mở lại thanh toán:** Khi order ở trạng thái “Chờ xác minh thanh toán” và đã thống nhất với khách về việc thu lại, Quản lý chọn “Mở lại thanh toán”, nhập lý do và kết quả xử lý bên ngoài. Hệ thống khóa và kiểm tra lại order chưa có thanh toán thành công, chuyển giao dịch cũ sang “Đã hủy”, giữ mã tham chiếu và lịch sử, đưa order về “Đang mở” trong cùng transaction. Thu ngân được chọn tiền mặt hoặc tạo mã QR mới; việc thêm/sửa/hủy món và đổi bàn thực hiện theo các điều kiện của order đang mở. Bàn đã giải phóng không được tự gắn lại với order. Thao tác được ghi vào audit log theo FR-SET-06.

- **FR-SALE-34 – Cập nhật kết quả xử lý ngoài hệ thống:** Với order “Chờ xác minh thanh toán”, Quản lý tiếp nhận việc tra soát ngân hàng và giải quyết với khách ngoài hệ thống; Thu ngân được bổ sung mã giao dịch/bằng chứng và nội dung kiểm tra. Quản lý lưu tiến độ và kết quả tra soát. Ba thao tác chỉ dành cho Quản lý theo FR-SALE-20, FR-SALE-23 và FR-SALE-35. Mọi kết quả được lưu trong audit log gắn MaOrder/MaGiaoDichTT.

- **FR-SALE-35 – Đóng order chưa thu được tiền:** Khi sau xử lý bên ngoài Quản lý quyết định ngừng theo dõi thu khoản tiền, Quản lý chuyển order và giao dịch đang chờ sang “Đóng – chưa thu được tiền”. Thao tác đóng phải lưu lý do, kết quả xử lý, người thực hiện, thời điểm và số tiền chưa thu; khóa và kiểm tra lại chưa có thanh toán thành công trong cùng transaction. Order đóng không phát hành hóa đơn, không cộng doanh thu; giữ nguyên tiêu hao nguyên liệu, không hoàn kho, theo dõi riêng giá trị order và giá vốn trong FR-REP-10. Tiền được xác minh đến sau khi đóng xử lý theo FR-SALE-16; không tự mở lại order hoặc tác động bàn đang phục vụ order khác.

- **FR-SALE-27 – Hủy toàn bộ order chưa thanh toán:** Quản lý được hủy toàn bộ order ở trạng thái “Đang mở”, chưa có thanh toán thành công và không có yêu cầu xác minh đang chờ xử lý; bắt buộc nhập lý do. Thao tác áp dụng cả khi order có món “Đã xác nhận xong” hoặc “Đã phục vụ”.

- **FR-SALE-28 – Xử lý nguyên liệu khi hủy toàn bộ order:** Nguyên liệu của các món ở trạng thái “Đã xác nhận xong” hoặc “Đã phục vụ” không được hoàn kho; phần nguyên liệu đã tiêu hao này được ghi vào chi phí hao hụt do hủy order (FR-REP-13) và hiển thị trong báo cáo FR-REP-10. Các món “Chờ làm” được hoàn kho theo FR-INV-04; hủy toàn bộ order kết thúc các lượt chọn chưa gửi và giải phóng lượng giữ liên quan.

- **FR-SALE-29 – Ngoại lệ khi đang chờ xác nhận thanh toán QR:** Không cho hủy toàn order khi đang “Chờ xác nhận thanh toán” (đã tạo mã QR), phải chủ động hủy mã QR (FR-SALE-33) hoặc chờ hết hạn trước; nếu khách đã báo chuyển tiền thì chuyển sang “Chờ xác minh thanh toán” theo FR-SALE-19.

- **FR-SALE-30 – Xử lý sau khi hủy toàn bộ order:** Không phát sinh hóa đơn, bàn về Trống nếu khách đã rời đi; chỉ hoàn kho cho món “Chờ làm”; ghi vào báo cáo “giá trị order bị hủy”.

- **FR-SALE-25 – Danh sách và tra cứu order:** Quản lý truy cập màn hình Quản lý đơn hàng để xem danh sách order, lọc kết hợp theo mã order, bàn, khoảng ngày kinh doanh (Business Date) và trạng thái. Danh sách hiển thị mã, loại đơn, bàn nếu có, ngày kinh doanh, người lập, trạng thái và tổng tiền. Người dùng mở từng order để xem chi tiết món, lịch sử thanh toán và chứng từ. Thu ngân/Nhân viên order được tra cứu theo phân quyền tại mục 4.4.2.

- **FR-SALE-26 – In lại hóa đơn:** In lại (reprint) đúng nguyên nội dung hóa đơn gốc đã chốt; không cho chỉnh sửa khi in lại.

### K.3. Quản lý kho

- **FR-INV-01 – Ghi nhận phiếu nhập kho:** Bếp ghi nhận phiếu nhập kho gắn với nhà cung cấp: nguyên liệu, số lượng, đơn giá, ngày nhập, quy đổi theo đúng đơn vị tính chuẩn hóa.

- **FR-INV-02 – Điều kiện sửa/hủy phiếu nhập kho:** Bếp được sửa hoặc hủy phiếu khi các lô liên quan chưa phát sinh giao dịch xuất và không có giữ món còn hiệu lực. Các trường hợp đã sử dụng được xử lý bằng nghiệp vụ kiểm kê. Thao tác được kiểm tra trong transaction và ghi audit log.

- **FR-INV-13 – Quản lý lô FIFO:** Mỗi dòng nhập tạo một lô với số lượng và hạn dùng. Lượng giữ được phân bổ vào các lô còn hạn theo FIFO, chỉ chiếm phần chưa được các lượt giữ khác sử dụng. Khi gửi món, lượng giữ hợp lệ chuyển thành tiêu hao trên các lô tương ứng. Lô hết hạn được tính vào tồn sổ sách để kiểm kê và xuất hủy, được loại khỏi lượng bán được. Hoàn món dựa trên lô của giao dịch gốc theo BR-LOT-01.

- **FR-INV-03 – Ghi nhận tiêu hao khi gửi món:** Hệ thống trừ tồn theo công thức lưu trên dòng món khi lượt gửi đầu tiên hoặc lượt gọi thêm thành công. Lượng giữ tương ứng được kết thúc trong cùng transaction. Tiêu hao được ghi theo từng lô còn hạn theo FIFO và từng dòng món; lượt chọn chưa gửi chỉ tác động lượng khả dụng.

- **FR-INV-04 – Hoàn nguyên liệu:** Món đã gửi chỉ được hủy hoặc giảm khi đang Chờ làm và Bếp xác nhận chưa chế biến theo FR-SALE-07. Hệ thống hoàn đúng lượng vào các lô của giao dịch gốc. Đối với dòng chưa gửi, thao tác giảm/xóa chỉ giải phóng giữ món theo FR-SALE-08.

- **FR-INV-05 – Lập phiếu xuất hủy:** Phiếu xuất hủy ghi người thực hiện, thời điểm, lý do và nguồn. Nguồn “Nguyên liệu” trừ các lô được chọn cho lượng hư hỏng, hết hạn hoặc hao hụt phát hiện riêng. Với nguồn “Món đã chế biến”, người lập chọn dòng order và số suất bị bỏ; hệ thống tự xác định nguyên liệu, lượng tương ứng theo tiêu hao gốc của dòng món và hiển thị để xác nhận. Các lượng này chỉ đọc, không nhập tùy ý và không tính lại theo công thức hiện tại. Nguồn “Kiểm kê” tham chiếu phiếu kiểm kê có chênh lệch âm, dùng làm chứng từ cho giao dịch điều chỉnh. Chỉ nguồn Nguyên liệu tạo giao dịch xuất thủ công; hai nguồn còn lại sử dụng giao dịch đã ghi nhận.

- **FR-INV-06 – Kiểm soát số lượng xuất hủy:** Nguồn Nguyên liệu không vượt tồn sổ sách của các lô được chọn. Nếu phần hỏng đang được giữ cho món, backend giải phóng toàn bộ lượt giữ của các dòng bị ảnh hưởng trong cùng transaction và thông báo nhân viên kiểm tra lại. Với nguồn Món đã chế biến, số suất xuất hủy không vượt số suất đã tiêu hao chưa được ghi nhận hủy. Hệ thống tính định lượng nguyên liệu từ tiêu hao gốc của dòng món và số suất hủy. Nguồn Kiểm kê được tạo duy nhất theo kết quả xác nhận phiếu.

- **FR-INV-08 – Kiểm kê định kỳ:** Bếp/Quản lý kiểm kê theo lịch nhà hàng tự đặt, sau khi kết thúc phục vụ và các món đã được chế biến hoặc hủy hợp lệ. Hệ thống yêu cầu xử lý hết lượt chọn chưa gửi và giữ món còn hiệu lực trước khi mở phiên kiểm kê. Trong phiên, backend chặn giữ món, gửi món và các giao dịch nhập/xuất/hoàn kho. Bếp đếm tồn thực tế, gồm lô hết hạn, đối chiếu tồn sổ sách; xác nhận ghi chênh lệch và phân bổ theo BR-LOT-02 trong một transaction. Xác nhận hoặc hủy phiên kết thúc khóa nghiệp vụ.

- **FR-INV-09 – Ghi nhận kết quả điều chỉnh kiểm kê:** Khi xác nhận phiếu có chênh lệch âm, hệ thống tự sinh phiếu xuất hủy gắn với phiếu kiểm kê. Chênh lệch dương sinh giao dịch điều chỉnh tăng. Hệ thống ghi audit log cho việc xác nhận và điều chỉnh.

- **FR-INV-07 – Cảnh báo tồn tối thiểu:** Hệ thống có một mức tồn tối thiểu mặc định, cấu hình tại phần Cài đặt; mỗi nguyên liệu có thể dùng mức mặc định này hoặc có mức tồn tối thiểu riêng, không nhỏ hơn 0. Cảnh báo được kích hoạt khi tồn khả dụng của một nguyên liệu nhỏ hơn mức tồn tối thiểu đang áp dụng cho nguyên liệu đó.

- **FR-INV-10 – Tính lượng khả dụng:** Tồn sổ sách bằng tổng số lượng còn lại của tất cả lô. Tồn đủ điều kiện bán bằng tổng các lô còn hạn; lượng khả dụng bằng tồn đủ điều kiện bán trừ lượng giữ còn hiệu lực trên các lô đó. Lượt giữ hợp lệ có trạng thái Đang giữ và thời điểm hết hạn lớn hơn giờ server. HetNguyenLieu được suy ra từ lượng khả dụng cho một suất theo công thức. Khi gửi một dòng đã giữ, backend cộng lại phần giữ của chính dòng đang xét vào lượng đáp ứng; các dòng khác vẫn bị loại trừ. Lô hết hạn và lượt giữ hết hạn được loại ngay trong truy vấn, độc lập với tác vụ dọn trạng thái.

- **FR-INV-11 – Đồng thời và toàn vẹn giữ món:** Tạo, sửa, giải phóng giữ món và gửi món dùng transaction; backend khóa các nguyên liệu theo thứ tự mã tăng dần rồi khóa lô và lượt giữ liên quan. Kiểm tra lượng khả dụng và ghi giữ món được thực hiện nguyên tử. Gửi món chuyển giữ món thành tiêu hao đúng một lần; lỗi giữa chừng rollback toàn bộ. Khi lô hết hạn hoặc mất khả năng đáp ứng, hệ thống yêu cầu kiểm tra lại dòng bị ảnh hưởng. Mọi lượt giữ và lần gửi thuộc đúng người/lượt chọn hoặc order được phép thao tác.

- **FR-INV-12 – Xem tồn kho:** Màn hình kho hiển thị tên, đơn vị, tồn sổ sách, tồn đủ điều kiện bán, lượng đang giữ, lượng khả dụng, mức tồn tối thiểu và cảnh báo. Người dùng tìm kiếm theo nguyên liệu và lọc theo trạng thái; thời điểm cập nhật được hiển thị cùng số liệu.

- **FR-INV-14 – Cảnh báo hạn sử dụng theo lô:** Mỗi lô nguyên liệu có trạng thái Còn hạn / Sắp hết hạn / Hết hạn, tính theo hạn sử dụng đã khai báo: “Sắp hết hạn” khi hạn sử dụng còn không quá SoNgayCanhBaoHetHan ngày (Quản lý cấu hình tại FR-SET-04, mặc định 3 ngày), “Hết hạn” khi đã quá hạn sử dụng; hệ thống hiển thị cảnh báo riêng biệt với cảnh báo tồn tối thiểu (FR-INV-07) trên màn hình quản lý kho để Bếp chủ động xử lý (ưu tiên xuất dùng trước hoặc lập phiếu xuất hủy nếu đã hết hạn).

### K.4. Báo cáo thống kê

- **FR-REP-01 – Báo cáo doanh thu:** Hiển thị doanh thu theo Business Date/tuần/tháng/năm, theo loại đơn (tại chỗ/mang về) và theo hình thức thanh toán.

- **FR-REP-08 – So sánh hai khoảng thời gian:** Cho phép so sánh doanh thu/chi phí giữa hai khoảng thời gian và hiển thị phần trăm chênh lệch = (kỳ so sánh − kỳ gốc) / kỳ gốc × 100% khi kỳ gốc khác 0; khi kỳ gốc bằng 0, chỉ hiển thị chênh lệch tuyệt đối và ghi “Không xác định tỷ lệ phần trăm”.

- **FR-REP-09 – Hiển thị dạng bảng và biểu đồ:** Báo cáo hiển thị dưới dạng bảng biểu và biểu đồ trực quan.

- **FR-REP-04 – Lợi nhuận gộp theo chi phí nguyên liệu:** Tính bằng tiền ở mức tổng toàn nhà hàng theo chu kỳ tháng = Doanh thu bán hàng − Giá vốn nguyên liệu tiêu hao (FR-REP-11 + FR-REP-12 + FR-REP-13); không bao gồm lương, thuê mặt bằng hay chi phí vận hành khác.

- **FR-REP-05 – Cấu thành giá vốn nguyên liệu tiêu hao:** Giá vốn gồm ba khoản FR-REP-11, FR-REP-12 và FR-REP-13 dưới đây. Mỗi lượng nguyên liệu chỉ được tính một lần. Hao hụt kiểm kê lấy từ giao dịch điều chỉnh kho; phiếu xuất hủy tự sinh chỉ là chứng từ đối chiếu.

  - **FR-REP-11 – Giá vốn bán hàng:** Nguyên liệu tiêu hao theo công thức của order thanh toán thành công, tính theo phiên bản công thức lưu trên từng dòng món tại thời điểm gửi món. Giá vốn được tổng hợp theo ORDER.BusinessDate để đối chiếu với doanh thu và nhân đơn giá bình quân gia quyền của tháng tương ứng. Đơn giá tính trên tồn đầu kỳ và lượng nhập trong tháng; tháng không có lần nhập dùng đơn giá của kỳ gần nhất trước đó.

  - **FR-REP-12 – Hao hụt kho:** Tổng hợp nguyên liệu hao hụt, hư hỏng, hết hạn từ nguồn Nguyên liệu và chênh lệch âm kiểm kê theo ngày biến động kho. Phiếu nguồn Món đã chế biến dùng phân tích lý do tiêu hao gắn với order; chi phí của phần này được giữ trong nhóm FR-REP-11 hoặc FR-REP-13 theo kết quả order, mỗi giao dịch gốc chỉ được tổng hợp một lần.

  - **FR-REP-13 – Tiêu hao của order bị hủy hoặc đóng chưa thu được tiền:** Nguyên liệu đã tiêu hao và không hoàn kho của order bị hủy toàn phần (FR-SALE-28) hoặc “Đóng – chưa thu được tiền” (FR-SALE-35). Phiên bản công thức, kỳ báo cáo và đơn giá bình quân được xác định như FR-REP-11. Lịch sử kho giữ nguyên thời điểm biến động thực tế.

- **FR-REP-06 – Chi phí nguyên liệu theo món (tham khảo):** Hiển thị riêng chi phí nguyên liệu theo từng món (không kèm hao hụt) để tham khảo.

- **FR-REP-03 – Xếp hạng món ăn:** Xếp hạng món bán chạy/ít bán theo số lượng và doanh thu, trong khoảng thời gian lựa chọn.

- **FR-REP-07 – Phân bố đơn hàng theo khung giờ:** Hiển thị phân bố số lượng đơn hàng và doanh thu theo khung giờ trong ngày và theo ngày trong tuần.

- **FR-REP-02 – Theo dõi thanh toán chưa hoàn tất:** Order “Chờ xác minh thanh toán” hiển thị riêng cùng giá trị order, thời gian đã chờ và kết quả xử lý gần nhất; chưa có hóa đơn và không cộng doanh thu. Khi Quản lý mở lại thanh toán, order về “Đang mở” và tiếp tục hiển thị trong danh sách khoản chưa thu cùng lịch sử xác minh. Nếu order bị hủy, khoản rời danh sách này và được theo dõi trong báo cáo order bị hủy. Khi xác nhận thành công, khoản rời danh sách và doanh thu được ghi nhận một lần theo ORDER.BusinessDate. Khi Quản lý đóng “Đóng – chưa thu được tiền”, khoản chuyển sang FR-REP-10. Ngoại lệ tiền đến muộn/thu trùng theo FR-SALE-16 được theo dõi riêng đến khi đã áp dụng hoặc hoàn tiền, không cộng doanh thu lần nữa.

- **FR-REP-10 – Báo cáo order bị hủy và order đóng chưa thu được tiền:** Hiển thị thành hai nhóm riêng theo Business Date/tuần/tháng: order bị hủy toàn bộ (số lượng, giá trị, lý do) và order “Đóng – chưa thu được tiền” (số lượng, số tiền chưa thu, giá vốn nguyên liệu đã tiêu hao, lý do, người đóng, thời điểm đóng). Các khoản không cộng doanh thu. Giá trị order và giá vốn được hiển thị thành hai chỉ tiêu riêng. Khi khoản tiền đến muộn được áp dụng hợp lệ theo FR-SALE-17, order rời tổng hiện tại của nhóm đóng chưa thu, giá vốn chuyển từ FR-REP-13 sang FR-REP-11 và doanh thu ghi một lần; giữ lịch sử đóng và xử lý để tra cứu.

### K.5. Cài đặt hệ thống

- **FR-SET-01 – Quản lý tài khoản:** Quản lý tạo/sửa/khóa tài khoản người dùng và gán một trong ba vai trò. Các thao tác này được ghi vào audit log (FR-SET-06).

- **FR-SET-03 – Giới hạn theo vai trò:** Hệ thống giới hạn phạm vi truy cập chức năng và dữ liệu theo vai trò đã gán. Quản lý kế thừa toàn bộ quyền của Thu ngân/Nhân viên order và Bếp.

- **FR-SET-04 – Cấu hình hệ thống:** Quản lý cấu hình thông tin chung của nhà hàng: tên, địa chỉ, mẫu hóa đơn, mốc giờ bắt đầu Business Date, mức tồn tối thiểu mặc định, số ngày để lô nguyên liệu chuyển sang “Sắp hết hạn” (SoNgayCanhBaoHetHan, mặc định 3 ngày), thời hạn giữ món (ThoiGianGiuChoPhut, mặc định 5 phút) và số câu hỏi AI tối đa mỗi người dùng mỗi ngày (SoCauHoiAIMoiNgay, mặc định 50). Số ngày cảnh báo, thời hạn giữ món và hạn mức câu hỏi AI là số nguyên dương; mức tồn tối thiểu không nhỏ hơn 0. Thay đổi mốc giờ được lưu kèm ngày hiệu lực, có hiệu lực từ Business Date kế tiếp và không ảnh hưởng đến Business Date đang diễn ra.

- **FR-SET-05 – Áp dụng ngưỡng cảnh báo tồn kho:** Với mỗi nguyên liệu, hệ thống ưu tiên mức tồn tối thiểu riêng nếu đã được cấu hình; nếu chưa có, áp dụng mức mặc định tại FR-SET-04. Cảnh báo được xác định theo FR-INV-07.

- **FR-SET-06 – Audit log cho thao tác rủi ro cao:** Ghi nhật ký cho các thao tác rủi ro cao theo từng module. Bán hàng/thanh toán: hủy toàn bộ order, hủy món, chuyển trạng thái QR sang chờ xác minh thanh toán, chủ động hủy giao dịch QR (FR-SALE-33), đổi bàn cho order, giải phóng bàn khi khách rời đi; Quản lý xử lý ngoại lệ tiền QR đến muộn/hoàn tiền, xác nhận đối soát (“Xác nhận đã nhận tiền” hoặc lưu kết quả chưa đủ căn cứ), đóng order chưa thu được tiền và mở lại thanh toán cho order “Chờ xác minh thanh toán” (FR-SALE-20, FR-SALE-23, FR-SALE-34, FR-SALE-35). Kho: lập phiếu xuất hủy, điều chỉnh qua kiểm kê, sửa/hủy phiếu nhập kho. Danh mục: thay đổi giá/công thức theo lịch và sửa trực tiếp, hủy lịch thay đổi đang chờ áp dụng, hệ thống tự động ghi đè lịch đang chờ áp dụng bởi một lịch mới (FR-CAT-09, FR-CAT-21), xóa nhóm món/món ăn/nguyên liệu/nhà cung cấp/bàn. Cài đặt/tài khoản: tạo/sửa/khóa tài khoản người dùng và gán vai trò, Quản lý đặt lại mật khẩu hộ người dùng và thay đổi cấu hình hệ thống (mốc giờ Business Date, mức tồn tối thiểu mặc định, ngưỡng sắp hết hạn của lô, thời gian giữ món, hạn mức câu hỏi AI).

- **FR-SET-07 – Nội dung tối thiểu và quyền xem nhật ký:** Mỗi bản ghi lưu tối thiểu: người thực hiện, thời điểm, loại thao tác, dữ liệu trước/sau; Quản lý xem toàn bộ.

- **FR-SET-02 – Đăng nhập/đăng xuất/đổi mật khẩu:** Người dùng tự đăng nhập/đăng xuất bằng tài khoản được cấp; tự đổi mật khẩu bất kỳ lúc nào; Quản lý đặt lại mật khẩu khi người dùng quên. Riêng thao tác Quản lý đặt lại mật khẩu hộ được ghi vào audit log (FR-SET-06); đăng nhập/đăng xuất và tự đổi mật khẩu thông thường không thuộc phạm vi audit log này.

### K.6. AI Assistant

- **FR-AI-01 – Trợ lý AI riêng theo vai trò:** Mỗi vai trò sử dụng một trợ lý AI (chat) riêng biệt, đặt câu hỏi bằng tiếng Việt trong đúng phạm vi dữ liệu được phép.

- **FR-AI-02 – Câu hỏi của Quản lý:** Quản lý hỏi doanh thu, số order, lượng bán theo món/khung giờ, so sánh hai kỳ, món tăng/giảm lượng bán, tồn kho, chi phí và lợi nhuận gộp theo nguyên liệu. Câu trả lời gồm phạm vi thời gian, số liệu và nhận xét có căn cứ; khi kỳ gốc bằng 0 chỉ nêu chênh lệch tuyệt đối. AI hỗ trợ xem xét thực đơn và bố trí phục vụ; nguyên nhân ngoài dữ liệu và quyết định điều hành thuộc người quản lý.

- **FR-AI-03 – Nội dung AI của Thu ngân/Nhân viên order có thể trả lời:** Doanh thu bán hàng, hóa đơn, thông tin bán hàng thuộc phạm vi vai trò; không trả lời giá nhập hàng, giá vốn và lợi nhuận gộp. Thu ngân/Nhân viên order không truy cập màn hình Báo cáo thống kê, chỉ tra cứu doanh thu, hóa đơn qua trợ lý AI này.

- **FR-AI-04 – Câu hỏi của Bếp:** Bếp hỏi tồn sổ sách, lượng đang giữ, lượng khả dụng, lịch sử nhập/xuất, cảnh báo nguyên liệu và số suất món còn phục vụ được. Số suất khả dụng được tính từ công thức hiện hành và lượng khả dụng tại thời điểm truy vấn, cung cấp qua view tổng hợp chỉ đọc gồm mã món, tên món, số suất và thời điểm tính; không cấp quyền quản trị danh mục hay đọc trực tiếp toàn bộ công thức. Dữ liệu doanh thu, hóa đơn, giá vốn và lợi nhuận nằm ngoài phạm vi của Bếp.

- **FR-AI-05 – Giới hạn dữ liệu theo quyền của vai trò:** AI Assistant chỉ sử dụng dữ liệu nằm trong phạm vi được cấp cho vai trò hiện tại, bao gồm các quyền kế thừa của Quản lý theo FR-SET-03. Yêu cầu truy cập ngoài phạm vi này bị từ chối.

- **FR-AI-06 – Yêu cầu làm rõ khi không xác định được đối tượng:** Khi không xác định chính xác món/nguyên liệu/khoảng thời gian, hệ thống yêu cầu người dùng làm rõ hoặc diễn đạt lại.

- **FR-AI-07 – Hình thức trả lời:** Trả lời bằng tiếng Việt, luôn kèm bảng số liệu gốc và ghi chú phạm vi dữ liệu đã dùng. Loại biểu đồ được chọn theo quy tắc cố định: dữ liệu biến động theo thời gian dùng line chart; so sánh giữa các nhóm/đối tượng dùng bar chart; dữ liệu cơ cấu/tỷ trọng dùng doughnut chart; trường hợp không phù hợp với ba dạng trên chỉ hiển thị bảng.

- **FR-AI-08 – Xem chi tiết kỹ thuật của câu trả lời:** Người dùng có thể mở mục “Xem chi tiết” (thu gọn mặc định) để xem thông tin kỹ thuật, phục vụ kiểm chứng.

- **FR-AI-09 – Thông báo khi không thể trả lời:** Khi không tạo được câu trả lời hợp lệ, hệ thống thông báo và gợi ý diễn đạt lại, không im lặng hoặc trả kết quả sai.

- **FR-AI-10 – Hạn mức và bộ nhớ đệm:** Hạn mức SoCauHoiAIMoiNgay mặc định 50 câu/người/ngày theo FR-SET-04 và NFR-08; hệ thống thông báo khi đạt hạn mức. Cache có thời hạn ngắn, gắn người dùng, vai trò, phạm vi, tham số thời gian và phiên bản quyền. Biến động dữ liệu hoặc quyền làm mất hiệu lực cache liên quan; khi không xác định được dữ liệu phụ thuộc, hệ thống truy vấn trực tiếp. Câu hỏi về giữ món, tồn khả dụng và số suất còn phục vụ được luôn dùng dữ liệu hiện tại.
