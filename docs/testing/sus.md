# Khảo sát SUS (System Usability Scale)

Theo Phụ lục 4 của `docs/BaoCao_HeThongQuanLyNhaHang.md`: 3–5 người đóng vai Chủ nhà hàng/Quản lý,
kết hợp phỏng vấn ngắn. Với cỡ mẫu này kết quả chỉ có giá trị định tính, tham khảo — không suy rộng
thành kết luận thống kê.

Thang đo gốc: Brooke, J. (1996). *SUS: A "quick and dirty" usability scale.* Trong P. W. Jordan,
B. Thomas, B. A. Weerdmeester, & A. L. McClelland (Eds.), *Usability Evaluation in Industry*
(pp. 189–194). Taylor & Francis.

## 1. Thông tin người tham gia

| Trường | Giá trị |
| --- | --- |
| Mã người tham gia | SUS-01 (SUS-02 … SUS-05) |
| Vai trò đóng | Chủ nhà hàng / Quản lý |
| Kinh nghiệm vận hành nhà hàng | ___ năm |
| Đã từng dùng phần mềm quản lý nhà hàng nào chưa | Có / Không — nếu có, phần mềm nào |
| Thiết bị dùng khi thử nghiệm | Tablet / Laptop, trình duyệt ___ |
| Ngày thực hiện | dd/mm/yyyy |
| Người hướng dẫn (quan sát viên) | ___ |

## 2. Nhiệm vụ thực hiện trước khi trả lời phiếu

Người tham gia thao tác trên môi trường đã có dữ liệu mô phỏng (`make seed`), đăng nhập bằng tài khoản
vai trò Quản lý. Thực hiện đủ 7 nhiệm vụ theo đúng thứ tự, không được nhắc từng bước — quan sát viên chỉ
ghi nhận có hoàn thành được không và có cần trợ giúp không.

| # | Nhiệm vụ | Màn hình liên quan |
| --- | --- | --- |
| 1 | Tạo một order mới cho một bàn Trống, gọi 2 món, thêm ghi chú "không hành" cho một món, Submit | Bán hàng → Gọi món |
| 2 | Đổi order vừa tạo sang một bàn Trống khác | Bán hàng → Gọi món |
| 3 | Thanh toán order đó bằng hình thức QR, sau đó hủy mã QR và thanh toán lại bằng tiền mặt | Bán hàng → Thanh toán |
| 4 | Lên lịch một thay đổi giá bán cho một món, áp dụng từ Business Date kế tiếp | Danh mục → Món ăn → Lên lịch giá |
| 5 | Xem báo cáo doanh thu theo tuần và báo cáo biên lợi nhuận gộp theo tháng | Báo cáo |
| 6 | Ghi nhận một phiếu nhập kho cho một nguyên liệu | Kho → Nhập kho |
| 7 | Đặt câu hỏi cho AI Assistant: "Món nào bán chạy nhất tuần này?" rồi mở mục "Xem chi tiết" | AI Assistant |

Sau khi hoàn thành cả 7 nhiệm vụ (hoặc dừng giữa chừng nếu không thể tiếp tục), người tham gia điền
phiếu SUS bên dưới ngay lập tức, trước khi rời khỏi máy.

## 3. Phiếu khảo sát SUS (tiếng Việt, thang 5 điểm)

Với mỗi câu, khoanh tròn một mức độ đồng ý, từ 1 (Hoàn toàn không đồng ý) đến 5 (Hoàn toàn đồng ý).

| # | Phát biểu | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Tôi nghĩ mình sẽ muốn sử dụng hệ thống này thường xuyên. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 2 | Tôi thấy hệ thống này phức tạp một cách không cần thiết. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 | Tôi thấy hệ thống này dễ sử dụng. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4 | Tôi nghĩ mình cần có sự hỗ trợ của người am hiểu kỹ thuật để có thể sử dụng hệ thống này. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 | Tôi thấy các chức năng trong hệ thống này được tích hợp khá hợp lý với nhau. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 6 | Tôi thấy hệ thống này có quá nhiều điểm thiếu nhất quán. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 7 | Tôi hình dung hầu hết mọi người sẽ học cách sử dụng hệ thống này rất nhanh. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 8 | Tôi thấy hệ thống này rất cồng kềnh, bất tiện khi sử dụng. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 9 | Tôi cảm thấy tự tin khi sử dụng hệ thống này. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 10 | Tôi cần phải học nhiều thứ trước khi có thể bắt đầu sử dụng hệ thống này. | ☐ | ☐ | ☐ | ☐ | ☐ |

### Phỏng vấn ngắn sau khi điền phiếu (định tính)

1. Bước/thao tác nào khiến anh/chị lúng túng nhất trong 7 nhiệm vụ vừa làm?
2. Có chức năng nào anh/chị mong đợi nhưng không tìm thấy?
3. So với cách quản lý hiện tại (sổ giấy/Excel/phần mềm khác), hệ thống này giúp ích hay gây khó hơn ở
   điểm nào?
4. Anh/chị có tin tưởng câu trả lời của AI Assistant không? Vì sao?

## 4. Công thức tính điểm

Với các câu **lẻ** (1, 3, 5, 7, 9): điểm góp = (điểm đã khoanh − 1).
Với các câu **chẵn** (2, 4, 6, 8, 10): điểm góp = (5 − điểm đã khoanh).

```
SUS = [ Σ(điểm lẻ − 1) + Σ(5 − điểm chẵn) ] × 2.5
```

Kết quả nằm trong khoảng 0–100 cho mỗi người tham gia.

## 5. Bảng tổng hợp kết quả (3–5 người tham gia)

| Người tham gia | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | Q9 | Q10 | Điểm SUS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SUS-01 | | | | | | | | | | | |
| SUS-02 | | | | | | | | | | | |
| SUS-03 | | | | | | | | | | | |
| SUS-04 | | | | | | | | | | | |
| SUS-05 | | | | | | | | | | | |
| **Trung bình** | | | | | | | | | | | **___** |

## 6. Khung diễn giải điểm số

Theo thang phân loại phổ biến kèm theo SUS (Bangor, Kortum & Miller, 2009, dựa trên thang gốc của
Brooke, 1996):

| Khoảng điểm SUS | Xếp hạng chấp nhận | Diễn giải |
| --- | --- | --- |
| ≥ 80.3 | A (Excellent) | Dễ dùng vượt trội |
| 68 – 80.2 | B (Good) | 68 là điểm trung bình tham chiếu (average) trên tập dữ liệu chuẩn hóa gốc |
| 51 – 67.9 | C (OK) | Chấp nhận được nhưng còn điểm cần cải thiện |
| < 51 | D/F (Poor) | Cần cải thiện đáng kể trước khi đưa vào vận hành thật |

Vì cỡ mẫu 3–5 người, điểm trung bình và khung xếp hạng ở trên chỉ dùng để **định hướng** cải thiện UX
(ưu tiên sửa gì trước), không dùng làm kết luận định lượng chính thức trong báo cáo khoa học. Nội dung
phỏng vấn ngắn (mục 3) quan trọng hơn con số điểm khi cỡ mẫu nhỏ.
