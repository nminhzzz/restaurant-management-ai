Hệ thống quản lý nhà hàng tích hợp AI hỗ trợ hoạt động kinh doanh

Phiên bản tài liệu V33  
Ngày 27 tháng 10 năm 2026

Ba mươi sơ đồ tuần tự chính tương ứng 30 Use Case và năm sơ đồ con của hệ thống quản lý nhà hàng.

## 3.3. Mô hình hóa tương tác (Sequence Diagram)

Bộ sơ đồ tuần tự gồm 30 sơ đồ chính tương ứng 30 Use Case tại mục 3.1.2 và năm sơ đồ con mô tả các luồng dùng chung hoặc có nhiều nhánh. Mã SD sử dụng mã của Use Case tương ứng; hậu tố a, b đánh dấu sơ đồ con. Nội dung tương tác bám sát đặc tả đầu vào, đầu ra, các bước xử lý và ngoại lệ tại mục 3.4. Mỗi sơ đồ thể hiện tác nhân, giao diện, bộ xử lý, dữ liệu hoặc hệ thống ngoài; lời gọi dùng nét liền, kết quả trả về dùng nét đứt, các thanh trắng thể hiện thời gian thực thi.

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image38.png)

Hình 37. SD-1.1 – Quản lý nhóm món

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image39.png)

Hình 38. SD-1.2 – Quản lý món ăn

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image40.png)

Hình 39. SD-1.3 – Quản lý công thức

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image41.png)

Hình 40. SD-1.4 – Quản lý giá bán

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image42.png)

Hình 41. SD-1.5 – Quản lý bàn

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image43.png)

Hình 42. SD-1.6 – Quản lý nguyên liệu

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image44.png)

Hình 43. SD-1.7 – Quản lý nhà cung cấp

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image45.png)

Hình 44. SD-2.1 – Gọi món tại chỗ

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image46.png)

Hình 45. SD-2.1a – Chọn món và quản lý giữ món

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image47.png)

Hình 46. SD-2.2 – Gọi món mang về

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image48.png)

Hình 47. SD-2.3 – Quản lý order và phục vụ

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image49.png)

Hình 48. SD-2.3a – Giảm hoặc hủy món đã gửi

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image50.png)

Hình 49. SD-2.3b – Đổi bàn và giải phóng bàn

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image51.png)

Hình 50. SD-2.4 – Thanh toán

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image52.png)

Hình 51. SD-2.5 – Thanh toán QR

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image53.png)

Hình 52. SD-2.5a – Xác nhận webhook và khoản đến muộn

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image54.png)

Hình 53. SD-2.6 – Xử lý xác minh thanh toán và khoản QR ngoại lệ

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image55.png)

Hình 54. SD-2.6a – Xử lý khoản QR ngoại lệ

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image56.png)

Hình 55. SD-2.7 – Hủy toàn bộ order

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image57.png)

Hình 56. SD-2.8 – Tra cứu order

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image58.png)

Hình 57. SD-3.1 – Nhập kho theo lô

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image59.png)

Hình 58. SD-3.2 – Theo dõi xuất nguyên liệu

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image60.png)

Hình 59. SD-3.3 – Lập phiếu xuất hủy

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image61.png)

Hình 60. SD-3.4 – Kiểm kê và điều chỉnh tồn

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image62.png)

Hình 61. SD-3.5 – Theo dõi tồn kho theo lô

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image63.png)

Hình 62. SD-4.1 – Xem báo cáo doanh thu

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image64.png)

Hình 63. SD-4.2 – Xem chi phí và lợi nhuận gộp

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image65.png)

Hình 64. SD-4.3 – Xem báo cáo tiêu thụ món

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image66.png)

Hình 65. SD-4.4 – Xem phân bố order theo khung giờ

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image67.png)

Hình 66. SD-4.5 – Xem báo cáo order và thanh toán

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image68.png)

Hình 67. SD-5.1 – Quản lý người dùng

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image69.png)

Hình 68. SD-5.2 – Cấu hình hệ thống

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image70.png)

Hình 69. SD-5.3 – Xem nhật ký hệ thống

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image71.png)

Hình 70. SD-5.4 – Đăng nhập và quản lý tài khoản cá nhân

![Sơ đồ hoặc hình minh họa](images/03_Bo_so_do_Sequence_Diagram/media/image72.png)

Hình 71. SD-6.1 – Hỏi AI Assistant
