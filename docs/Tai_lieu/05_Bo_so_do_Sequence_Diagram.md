# 05. SƠ ĐỒ TUẦN TỰ

Xây dựng hệ thống quản lý nhà hàng tích hợp AI hỗ trợ hoạt động kinh doanh

Hai mươi chín sơ đồ tuần tự chính tương ứng 29 Use Case và sáu sơ đồ con của hệ thống quản lý nhà hàng.

## Mô hình hóa tương tác (Sequence Diagram)

Bộ sơ đồ tuần tự gồm 29 sơ đồ chính tương ứng 29 Use Case tại mục 3.1.2 của báo cáo chính và sáu sơ đồ con mô tả các luồng dùng chung hoặc có nhiều nhánh. Mã SD sử dụng mã của Use Case tương ứng; hậu tố a, b đánh dấu sơ đồ con. Nội dung tương tác bám sát đặc tả đầu vào, đầu ra, các bước xử lý và ngoại lệ tại tài liệu 03. Mỗi sơ đồ thể hiện tác nhân, giao diện, bộ xử lý, dữ liệu hoặc hệ thống ngoài; lời gọi dùng nét liền, kết quả trả về dùng nét đứt, các thanh trắng thể hiện thời gian thực thi.

SD-3.4 kiểm tra giữ hết hạn theo giờ server, độc lập tác vụ nền; SD-6.1 chỉ thực thi SELECT theo vai trò, tối đa 3 giây và 500 dòng, ghi mã yêu cầu và usage. Các sơ đồ mô tả thiết kế tương tác; bằng chứng thực thi được trình bày riêng trong tài liệu 06.

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image38.png" width="584" />

Hình 1. SD-1.1 – Quản lý nhóm món

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image39.png" width="584" />

Hình 2. SD-1.2 – Quản lý món ăn

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image40.png" width="495" />

Hình 3. SD-1.2a – Thiết lập công thức của món

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image41.png" width="549" />

Hình 4. SD-1.3 – Quản lý giá bán

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image42.png" width="584" />

Hình 5. SD-1.4 – Quản lý bàn

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image43.png" width="546" />

Hình 6. SD-1.5 – Quản lý nguyên liệu

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image44.png" width="584" />

Hình 7. SD-1.6 – Quản lý nhà cung cấp

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image45.png" width="584" />

Hình 8. SD-2.1 – Gọi món tại chỗ

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image46.png" width="568" />

Hình 9. SD-2.1a – Chọn món và quản lý giữ món

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image47.png" width="566" />

Hình 10. SD-2.2 – Gọi món mang về

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image48.png" width="584" />

Hình 11. SD-2.3 – Quản lý order và phục vụ

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image49.png" width="524" />

Hình 12. SD-2.3a – Giảm hoặc hủy món đã gửi

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image50.png" width="584" />

Hình 13. SD-2.3b – Đổi bàn và giải phóng bàn

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image51.png" width="580" />

Hình 14. SD-2.4 – Thanh toán

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image52.png" width="572" />

Hình 15. SD-2.5 – Thanh toán QR

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image3.png" width="575" />

Hình 16. SD-2.5a – Xác nhận webhook và khoản đến muộn

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image54.png" width="471" />

Hình 17. SD-2.6 – Xử lý xác minh thanh toán và khoản QR ngoại lệ

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image4.png" width="516" />

Hình 18. SD-2.6a – Xử lý khoản QR ngoại lệ

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image56.png" width="584" />

Hình 19. SD-2.7 – Hủy toàn bộ order

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image57.png" width="584" />

Hình 20. SD-2.8 – Tra cứu order

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image5.png" width="530" />

Hình 21. SD-3.1 – Nhập kho theo lô

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image59.png" width="584" />

Hình 22. SD-3.2 – Theo dõi xuất nguyên liệu

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image60.png" width="503" />

Hình 23. SD-3.3 – Lập phiếu xuất hủy

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image6.png" width="396" />

Hình 24. SD-3.4 – Kiểm kê và điều chỉnh tồn

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image62.png" width="584" />

Hình 25. SD-3.5 – Theo dõi tồn kho theo lô

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image63.png" width="584" />

Hình 26. SD-4.1 – Xem báo cáo doanh thu

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image7.png" width="584" />

Hình 27. SD-4.2 – Xem chi phí và lợi nhuận gộp

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image65.png" width="584" />

Hình 28. SD-4.3 – Xem báo cáo tiêu thụ món

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image66.png" width="584" />

Hình 29. SD-4.4 – Xem phân bố order theo khung giờ

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image67.png" width="584" />

Hình 30. SD-4.5 – Xem báo cáo order và thanh toán

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image68.png" width="584" />

Hình 31. SD-5.1 – Quản lý người dùng

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image69.png" width="584" />

Hình 32. SD-5.2 – Cấu hình hệ thống

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image70.png" width="584" />

Hình 33. SD-5.3 – Xem nhật ký hệ thống

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image8.png" width="466" />

Hình 34. SD-5.4 – Đăng nhập và quản lý tài khoản cá nhân

<img src="../images/05_Bo_so_do_Sequence_Diagram/media/image2.png" width="532" />

Hình 35. SD-6.1 – Hỏi AI Assistant
