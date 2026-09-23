# Sinh dữ liệu mô phỏng

Chưa triển khai. Script ở đây phải sinh ra bộ dữ liệu 12 tháng phục vụ cả báo cáo lẫn thực nghiệm
(tối thiểu 20.000 đơn theo NFR-03, trên 60–80 món), bám các đặc trưng thật của ngành:

- hai đỉnh trong ngày (trưa và tối), cuối tuần cao hơn ngày thường;
- yếu tố mùa vụ theo tháng;
- phân bố món theo quy luật lũy thừa (một số ít món chiếm phần lớn số đơn).

Dữ liệu sinh ra phải tôn trọng các ràng buộc nghiệp vụ: trừ kho theo công thức và theo lô FIFO,
Business Date 06:00–06:00, và trạng thái của từng dòng món trong order.

Khi triển khai, thêm entrypoint `generate.py` để `make seed` gọi được.
