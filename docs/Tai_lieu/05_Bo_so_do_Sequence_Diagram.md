Hệ thống quản lý nhà hàng tích hợp AI hỗ trợ hoạt động kinh doanh

Phiên bản tài liệu V33  
Ngày 27 tháng 10 năm 2026

Ba mươi sơ đồ tuần tự chính tương ứng 30 Use Case và năm sơ đồ con của hệ thống quản lý nhà hàng.

## 3.3. Mô hình hóa tương tác (Sequence Diagram)

Bộ sơ đồ tuần tự gồm 30 sơ đồ chính tương ứng 30 Use Case tại mục 3.1.2 và năm sơ đồ con mô tả các luồng dùng chung hoặc có nhiều nhánh. Mã SD sử dụng mã của Use Case tương ứng; hậu tố a, b đánh dấu sơ đồ con. Nội dung tương tác bám sát đặc tả đầu vào, đầu ra, các bước xử lý và ngoại lệ tại mục 3.4. Mỗi sơ đồ thể hiện tác nhân, giao diện, bộ xử lý, dữ liệu hoặc hệ thống ngoài; lời gọi dùng nét liền, kết quả trả về dùng nét đứt, các thanh trắng thể hiện thời gian thực thi.

SD-3.4 kiểm tra giữ hết hạn theo giờ server, độc lập tác vụ nền; SD-6.1 chỉ thực thi SELECT theo vai trò, tối đa 3 giây và 500 dòng, ghi mã yêu cầu và usage. Các sơ đồ thể hiện thiết kế, chưa thay thế kết quả kiểm thử sau sửa lỗi.

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image38.png" width="584" />

Hình 37. SD-1.1 – Quản lý nhóm món

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image39.png" width="584" />

Hình 38. SD-1.2 – Quản lý món ăn

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image40.png" width="525" />

Hình 39. SD-1.3 – Quản lý công thức

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image41.png" width="581" />

Hình 40. SD-1.4 – Quản lý giá bán

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image42.png" width="584" />

Hình 41. SD-1.5 – Quản lý bàn

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image43.png" width="578" />

Hình 42. SD-1.6 – Quản lý nguyên liệu

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image44.png" width="584" />

Hình 43. SD-1.7 – Quản lý nhà cung cấp

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image45.png" width="584" />

Hình 44. SD-2.1 – Gọi món tại chỗ

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image46.png" width="584" />

Hình 45. SD-2.1a – Chọn món và quản lý giữ món

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image47.png" width="584" />

Hình 46. SD-2.2 – Gọi món mang về

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image48.png" width="584" />

Hình 47. SD-2.3 – Quản lý order và phục vụ

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image49.png" width="584" />

Hình 48. SD-2.3a – Giảm hoặc hủy món đã gửi

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image50.png" width="584" />

Hình 49. SD-2.3b – Đổi bàn và giải phóng bàn

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image51.png" width="584" />

Hình 50. SD-2.4 – Thanh toán

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image52.png" width="584" />

Hình 51. SD-2.5 – Thanh toán QR

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image53.png" width="584" />

Hình 52. SD-2.5a – Xác nhận webhook và khoản đến muộn

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image54.png" width="498" />

Hình 53. SD-2.6 – Xử lý xác minh thanh toán và khoản QR ngoại lệ

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image55.png" width="534" />

Hình 54. SD-2.6a – Xử lý khoản QR ngoại lệ

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image56.png" width="584" />

Hình 55. SD-2.7 – Hủy toàn bộ order

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image57.png" width="584" />

Hình 56. SD-2.8 – Tra cứu order

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image58.png" width="551" />

Hình 57. SD-3.1 – Nhập kho theo lô

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image59.png" width="584" />

Hình 58. SD-3.2 – Theo dõi xuất nguyên liệu

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image60.png" width="584" />

Hình 59. SD-3.3 – Lập phiếu xuất hủy

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image1.png" width="522" />

Hình 60. SD-3.4 – Kiểm kê và điều chỉnh tồn

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image62.png" width="584" />

Hình 61. SD-3.5 – Theo dõi tồn kho theo lô

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image63.png" width="584" />

Hình 62. SD-4.1 – Xem báo cáo doanh thu

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image64.png" width="584" />

Hình 63. SD-4.2 – Xem chi phí và lợi nhuận gộp

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image65.png" width="584" />

Hình 64. SD-4.3 – Xem báo cáo tiêu thụ món

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image66.png" width="584" />

Hình 65. SD-4.4 – Xem phân bố order theo khung giờ

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image67.png" width="584" />

Hình 66. SD-4.5 – Xem báo cáo order và thanh toán

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image68.png" width="584" />

Hình 67. SD-5.1 – Quản lý người dùng

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image69.png" width="584" />

Hình 68. SD-5.2 – Cấu hình hệ thống

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image70.png" width="584" />

Hình 69. SD-5.3 – Xem nhật ký hệ thống

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image71.png" width="482" />

Hình 70. SD-5.4 – Đăng nhập và quản lý tài khoản cá nhân

<img src="images/05_Bo_so_do_Sequence_Diagram/media/image2.png" width="563" />

Hình 71. SD-6.1 – Hỏi AI Assistant
