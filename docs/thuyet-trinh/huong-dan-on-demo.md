# Hướng dẫn thuyết trình và demo phần C (15 phút)

Luồng trong phần 3 đã tập trên web bằng bản sao CSDL ngày 06/11/2026, nên nhãn nút là nhãn thật. Câu trả lời AI lấy từ CSDL demo. Riêng bước Quản lý xác nhận tiền, lượt tập mới mở được hộp nhập số tiền, chưa bấm OK.

Thứ tự học: phần 1 → tập phần 3 → phần 4 → phần 5. Phần 7 là demo đầy đủ 30 Use Case để tập và dùng khi được hỏi thêm; phần 8 là SePay; phần 9 là máy in bếp.

---

## 1. Mười hai ý phải nói được bằng lời của mình

| # | Khái niệm | Nói ngắn gọn | Tại sao |
|---|---|---|---|
| 1 | **Ba con số tồn** | Tồn sổ sách = tổng các lô. Đủ điều kiện = các lô còn hạn. Khả dụng = đủ điều kiện − đang giữ còn hiệu lực. | Sổ sách để kiểm kê; khả dụng mới quyết định bán được không. |
| 2 | **Giữ món** | Chọn món thì giữ nguyên liệu có hạn (mặc định 5 phút). Khả dụng giảm, sổ sách chưa đổi. Gửi bếp mới trừ kho, đúng một lần. | Góp ý 1: người chọn trước không bị người gửi trước giành nguyên liệu. |
| 3 | **FIFO cho số lượng** | Trừ lô nhập sớm nhất còn hạn. Không đủ tổng thì từ chối, không trừ một phần. Hủy hợp lệ thì hoàn đúng lô gốc. | Dùng hàng cũ trước, truy vết được. |
| 4 | **Bình quân tháng cho tiền** | Giá vốn = lượng tiêu hao × đơn giá bình quân tháng, tự tính lại khi phiếu nhập đổi. Không có chốt giá thủ công. | **Bẫy lớn nhất:** FIFO không quyết định giá vốn. |
| 5 | **Business Date** | Ngày kinh doanh mặc định bắt đầu 06:00. Đổi giờ có hiệu lực từ ngày kế tiếp, không tính lại ngày đã lưu. | Quán mở khuya; báo cáo cũ không đổi. |
| 6 | **Phiên bản giá/công thức** | Lên lịch theo Business Date hoặc sửa áp dụng ngay, hai cơ chế độc lập. Dòng đã gửi giữ phiên bản cũ. | Đổi giá không làm sai order cũ. |
| 7 | **Xóa mềm** | Đã có lịch sử thì chỉ ẩn khỏi vận hành. | Giữ báo cáo và truy vết. |
| 8 | **Trạng thái order** | Đang mở → Chờ xác nhận thanh toán (QR) hoặc Đã thanh toán. Ngoại lệ: Chờ xác minh thanh toán, Đóng – chưa thu được tiền, Đã hủy. | Khóa món và tiền khi đang thu; doanh thu chỉ tính order Đã thanh toán. |
| 9 | **Trạng thái món** | Chờ làm → Đã xác nhận xong → Đã phục vụ, do **nhân viên** cập nhật theo xác nhận của Bếp. | Chỉ Chờ làm mới được hủy và hoàn kho. |
| 10 | **Webhook, chống lặp** | QR chỉ được xác nhận qua webhook hợp lệ. Gửi lặp vẫn một kết quả. | Không thu trùng, không tạo order trùng. |
| 11 | **Transaction, khóa** | Giữ/gửi món khóa nguyên liệu theo mã tăng dần rồi khóa lô. Lỗi thì hoàn tác hết. | Không bán vượt tồn, tránh deadlock. |
| 12 | **Phân quyền, nhật ký** | Quyền kiểm tra ở API. Thao tác rủi ro cao ghi nhật ký, không sửa/xóa được. | Gọi thẳng API vẫn bị chặn; truy được ai làm gì. |

**Công thức:** Lợi nhuận gộp = Doanh thu − (giá vốn bán hàng + hao hụt kho + tiêu hao của order hủy/đóng chưa thu). Tính theo tháng, toàn nhà hàng, không gồm lương và mặt bằng.

**Trong code `WAREHOUSE` là Bếp.** Khi nói, luôn gọi là Bếp.

---

## 2. Chuẩn bị máy

CSDL demo là `restaurant`, đã migrate và đã có dữ liệu đến 06/11.

**Sáng ngày demo, chạy theo thứ tự:**

```bash
git checkout fix/demo-blockers      # hoặc nhánh chính nếu đã merge
make db-up
uv run --project apps/api python scripts/seed/demo_recent.py --days N --per-day 10
make api
cd apps/web && pnpm build && pnpm start
```

- **N** = số ngày từ 06/11 đến ngày demo, tính cả hai đầu. Ví dụ demo 12/11 thì N = 7. Lệnh này còn chuyển món cũ sang Đã phục vụ và cập nhật giá vốn.
- Dùng `pnpm start`, không dùng `make web`: bản dev hiện huy hiệu "1 Issue" ở góc màn hình.
- `.env` phải có `PAYMENT_GATEWAY=simulator`.

**Dữ liệu đã tạo sẵn cho demo:**

| Dữ liệu | Giá trị |
|---|---|
| Món bán trong demo | `Bò lúc lắc đặc biệt`, 120.000 ₫, cần 0,15 kg/suất |
| Nguyên liệu | `Thịt bò thăn`: lô 5 kg (hạn 10/11), lô 10 kg (hạn 11/11) |
| Món Nháp | `Bò né trứng (món mới)`, chưa có công thức |
| Món sắp hết (cho tình huống sai) | `Nấm đùi gà xào (sắp hết)`, còn đủ đúng 2 suất; không gửi bếp món này |
| Phiếu nhập cho tình huống sai | **#611**, lô 5 kg `Thịt bò thăn`. Nếu tạo lại phiếu nhập thì số này đổi |
| Order chờ xác minh | Lọc trong Quản lý đơn hàng, có sẵn hơn 400 order |

**Nếu demo sau 09/11:** tạo lại hai phiếu nhập `Thịt bò thăn` cách nhau một ngày, vì hai lô trên sắp hết hạn. Hạn dùng tự tính từ ngày nhập cộng số ngày bảo quản, không nhập tay.

**Trước giờ lên:**
- Vào Cài đặt → Cấu hình, đặt tên nhà hàng; hóa đơn đang in chữ "Nhà hàng".
- Mở ba cửa sổ riêng (ẩn danh/profile khác): `seed_warehouse`, `seed_cashier`, `seed_manager`, mật khẩu trong `scripts/seed/README.md`. Zoom trình duyệt 125%.
- Mở terminal ở `apps/api`, gõ sẵn `uv run python ../../scripts/demo_pay_qr.py`.
- Tắt thông báo máy tính, cắm sạc, chuẩn bị 4G dự phòng cho AI.
- Quay sẵn video cả luồng để dự phòng.
- Mỗi lần tập xong, khôi phục dữ liệu nếu bàn hoặc tồn đã bị dùng nhiều.

---

## 3. Kịch bản 15 phút

Thứ tự: **slide 9 → demo (khoảng 10 phút) → slide 10, 11, 12, 13.** Demo trước để Hội đồng thấy hệ thống chạy thật, rồi số liệu mới có ý nghĩa.

| Phút | Màn hình | Thao tác | Câu nói |
|---|---|---|---|
| 0:00 | Slide 9 | Giới thiệu | "Em sẽ đi một ngày của nhà hàng: từ kho, gọi món, thanh toán đến báo cáo và AI. Mỗi bước em nói vì sao làm như vậy." |
| 0:30 | **Bếp** · Kho → Tồn kho | Tìm `Thịt bò thăn`, bấm **Lô và lịch sử** | "Mỗi dòng nhập là một lô có hạn dùng. Tồn sổ sách là 15 kg, khả dụng cũng là 15 kg." |
| 1:30 | **Thu ngân** · Bán hàng | Chọn **Bàn 01**, tìm món, bấm món 2 lần, chưa gửi | "Em chọn 2 suất nhưng chưa gửi bếp." |
| 2:00 | **Bếp** · Làm mới | Chỉ vào Đang giữ và Khả dụng | "Đang giữ 0,3 kg, khả dụng còn 14,7 kg, sổ sách vẫn 15 kg. Đây là phần khắc phục góp ý 1 của Hội đồng." |
| 3:00 | **Thu ngân** | Bấm **Gửi bếp** | "Lúc này mới tạo order và phiếu bếp. Bấm gửi hai lần vẫn chỉ tạo một order." |
| 3:30 | **Bếp** · Lô và lịch sử | Chỉ lô 5 kg còn 4,7 kg | "Kho trừ đúng một lần, lấy lô nhập trước." |
| 4:15 | **Thu ngân** | Chọn Bàn 01 → **Thanh toán** → **Thêm món** 1 suất → **Hủy món** dòng vừa thêm | "Món còn Chờ làm thì hủy được và nguyên liệu về đúng lô gốc. Món đã làm thì không." |
| 5:00 | **Thu ngân** | **In phiếu tạm tính** → **QR chuyển khoản** → **Tạo mã QR** | "Phiếu tạm tính không phải hóa đơn. Đây là mã mô phỏng, không có tiền thật. Mã có hiệu lực 10 phút và order bị khóa." |
| 5:45 | Terminal | Chạy `demo_pay_qr.py`, quay lại web | "Script này đóng vai ngân hàng, gửi webhook có chữ ký. Hệ thống không tin thao tác bấm của thu ngân." Màn hình tự chuyển sang Đã thanh toán. |
| 6:15 | **Thu ngân** | Xem hóa đơn → **Về sơ đồ bàn** → Bàn 01 → **Giải phóng bàn** | "Thanh toán xong bàn không tự trống, vì khách có thể còn ngồi." |
| 6:45 | **Quản lý** · Quản lý đơn hàng | Lọc **Chờ xác minh thanh toán** → **Xem** → **Xác nhận đã nhận tiền** → giữ số tiền, bấm OK | "Khách báo đã trả nhưng chưa có webhook thì không bắt trả lại. Quản lý đối chiếu sao kê; có các hướng xác nhận, mở lại, hoặc đóng chưa thu." |
| 7:45 | **Quản lý** · Báo cáo | **Doanh thu** → **Lợi nhuận** tháng 2026-11 | "Doanh thu chỉ tính order đã thanh toán. FIFO quyết định trừ lô nào, còn giá vốn tính theo bình quân tháng và tự cập nhật." |
| 8:30 | **Quản lý** · Danh mục | Tìm `Bò né trứng (món mới)`, chỉ trạng thái Nháp | "Món chưa có công thức thì chưa bán được, vì chưa biết trừ nguyên liệu nào." |
| 8:50 | **Quản lý** · Trợ lý AI | Hỏi: *Doanh thu 7 ngày gần nhất theo từng ngày?* Mở chi tiết kỹ thuật | Trong lúc chờ: "Mô hình chỉ thấy view của vai trò. SQL phải qua kiểm duyệt rồi mới chạy bằng tài khoản chỉ đọc." |
| 10:00 | **Bếp** · Trợ lý AI | Hỏi: *Doanh thu hôm nay là bao nhiêu?* | "Vai trò Bếp không có dữ liệu doanh thu, nên trợ lý không trả số mà đề nghị hỏi về kho." |
| 10:30 | Slide 10–11 | | "223/247 ca đạt ở lượt 03–04/11; hiệu năng đạt ngưỡng. Bán hàng và Kho trên 90%; Báo cáo và điều kiện biên còn nhiều lỗi nhất." |
| 11:45 | Slide 12 | | "Cấu hình B đúng 84,58%, nhưng lỗi/timeout 13,75%, vượt ngưỡng 5%, nên NFR-02 chưa đạt. Khi trả được SQL thì đúng 203/207. Vấn đề chính là thời gian, không phải SQL sai." |
| 13:15 | Slide 13 | | "Em đã sửa hủy phiếu nhập và tạo tài khoản, chạy lại 5 ca liên quan và đạt. Tiếp theo là giữ/gửi món, giá vốn, webhook. Con số 223 chưa cộng thêm vì chưa chạy lại toàn bộ." |
| 14:30 | Chốt | | "Điểm mạnh nhất là tồn kho, bán hàng và báo cáo khớp nhau. Hạn chế lớn nhất là độ ổn định của AI. Em xin hết, mời thầy cô đặt câu hỏi." |

**Trễ giờ thì cắt theo thứ tự:** Thêm/Hủy món (4:15) → Danh mục (8:30) → câu hỏi của Bếp. Không cắt giữ nguyên liệu, QR và câu AI đầu tiên.

**Khi có sự cố:**

| Sự cố | Cách xử lý |
|---|---|
| AI báo "Trợ lý phản hồi quá lâu" | "Đây đúng là hạn chế ở slide 12", rồi hỏi lại một lần. Vẫn lỗi thì chiếu video. Khi tập, câu "So sánh doanh thu tháng này với tháng trước" đã bị lỗi này, nên không dùng nó làm câu chính. |
| Script QR lỗi | Dùng **Hủy QR** rồi thu tiền mặt: **Vừa đủ** → **Xác nhận đã thu** |
| Web treo | Tải lại trang; vẫn lỗi thì chuyển sang video, không sửa trước mặt Hội đồng |
| Số liệu lạ | "Đây là dữ liệu mô phỏng 12 tháng" và đi tiếp |

---

## 4. Cách trình bày cho chuyên nghiệp

1. **Mỗi thao tác nói theo ba nhịp:** làm gì → hệ thống phản ứng gì → vì sao thiết kế vậy. Ví dụ: "Em chọn món → khả dụng giảm → để không bán vượt tồn."
2. **Nói trước khi bấm**, và dừng 1–2 giây ở màn kết quả. Dùng con trỏ chỉ đúng con số đang nói.
3. **Không đọc slide.** Mỗi slide chỉ một thông điệp, đã có ở cột Câu nói.
4. **Tự nêu hạn chế trước khi bị hỏi.** Việc nói thẳng NFR-02 chưa đạt tạo độ tin cậy.
5. **Phân biệt ba mức khi nói:** đã kiểm thử, đã có code, chưa làm. Không nói "hoàn thiện" chung chung.
6. **Khi chờ AI, tiếp tục giải thích** cơ chế an toàn, đừng im lặng nhìn màn hình.
7. **Không biết thì nói thật:** "Phần này em chưa kiểm chứng, em xin kiểm tra và phản hồi lại", rồi dừng.
8. **Tập ít nhất ba lượt có bấm giờ:** một lượt một mình, một lượt có bạn đóng vai Hội đồng, một lượt trên đúng máy và màn chiếu.

**Những chỗ tránh đưa lên màn hình:**
- Bảng Tồn kho chưa lọc: có dòng "Thịt bò 22.828 kg, 584 lô hết hạn". Luôn tìm `Thịt bò thăn` trước.
- Danh sách món chưa lọc: dữ liệu sinh ngẫu nhiên có món xếp sai nhóm, như "Xôi gà" ở Tráng miệng. Nếu bị hỏi, nói đây là dữ liệu mô phỏng.
- Bộ lọc Nhật ký thao tác còn hiện mã tiếng Anh, như `CANCEL_RECEIPT`.
- Báo cáo còn dòng "đang chờ đối soát" và gợi ý AI của Thu ngân còn chữ "đối soát". Khi nói, dùng thuật ngữ **Chờ xác minh thanh toán**.
- Phiếu bếp hiện "Chờ in" vì demo không nối máy in. Nếu bị hỏi, nói máy in mới kiểm bằng bộ nhận giả lập.

**Không bấm vào các lỗi còn lại:**

| Ca | Biểu hiện | Cách tránh |
|---|---|---|
| INV-09 | Giữ hết khả dụng thì gửi bị từ chối | Chỉ chọn 2 suất, còn dư nhiều |
| SALE-19 | Order đã rời bàn vẫn gọi thêm được | Không gọi thêm sau khi giải phóng bàn |
| SALE-32 | Giảm suất không có bước nhập lý do | Dùng **Hủy món** |
| SALE-13, 61 | Thông báo thiếu nguyên liệu không rõ món | Không cố ý demo thiếu nguyên liệu |
| SALE-70 | Chi tiết order thiếu lịch sử thanh toán | Không hứa có lịch sử ở đó |
| BR-06 | Webhook sau xác nhận thủ công tạo thêm ngoại lệ | Không chạy script sau khi Quản lý xác nhận |
| CAT-03 | Sắp xếp nhóm món bị từ chối | Không bấm |
| CAT-10 | Order cũ hiện mã thay tên món đã xóa | Không xóa món có lịch sử |
| CAT-16 | Tổng tiền phiếu nhập bằng 0 | Không chỉ vào cột này |
| SET-09, BR-14 | Nhật ký thiếu dữ liệu trước/sau | Không mở chi tiết nếu chưa kiểm tra trước |
| REP-11, BR-11, BR-13 | Giá vốn sai ở một số điều kiện | Chỉ mở tháng 2026-11 đã kiểm tra |

**Không học theo `kich-ban-demo.md` cũ.** File đó còn số 85,42%, trạng thái "Chờ đối soát/Tranh chấp", và câu sai "lợi nhuận tính theo lô FIFO". Chỉ dùng số trên slide 10–12 và báo cáo Chương 6. Các bảng SUS/UAT và McNemar trong báo cáo còn trống, không nêu kết quả.

---

## 5. Câu hỏi có thể gặp và cách trả lời

### Nghiệp vụ

**Vì sao giữ nguyên liệu khi chọn món, không trừ kho luôn?**
Chọn món chưa chắc đã gửi. Trừ kho ngay thì hủy lượt chọn phải hoàn kho, sổ kho sinh nhiều giao dịch vô nghĩa. Giữ món chỉ giảm khả dụng, gửi bếp mới trừ một lần.

**Giữ hết hạn mà chưa gửi thì sao?**
Phần giữ không còn chiếm khả dụng. Dòng món vẫn hiện; khi gửi, hệ thống kiểm tra lại, đủ thì nhận, thiếu thì báo. Hết hạn không tự gia hạn và không tự hủy lượt chọn.

**Hai thu ngân cùng tranh phần cuối thì sao?**
Giữ món chạy trong transaction, khóa nguyên liệu theo thứ tự mã tăng dần và kiểm tra khả dụng nguyên tử. Người đến sau không giữ được phần đã hết.

**Đã dùng FIFO, sao giá vốn lại tính bình quân?**
FIFO quản lý lượng trên từng lô, phục vụ hạn dùng và truy vết. Giá vốn trong báo cáo được đặc tả theo bình quân gia quyền tháng ở mức toàn nhà hàng. *Lý do chọn phương pháp không ghi trong tài liệu, cả nhóm nên thống nhất câu trả lời.*

**Sửa phiếu nhập có làm sai báo cáo tháng trước không?**
Hệ thống tự tính lại bình quân và giá vốn của kỳ bị ảnh hưởng cùng các kỳ sau; doanh thu và hóa đơn không đổi. Em đã thử: tạo rồi hủy một phiếu trong tháng 10, giá vốn về đúng số cũ, doanh thu giữ nguyên.

**Khi nào không được hủy phiếu nhập?**
Khi lô đã phát sinh xuất hoặc còn giữ món hiệu lực. Khi đó xử lý qua kiểm kê. Hủy phiếu thì giữ lại phiếu, lô và lịch sử để truy vết.

**Vì sao ngày kinh doanh bắt đầu 06:00?**
Order lúc 1 giờ sáng vẫn thuộc doanh thu ngày hôm trước. Quản lý đổi được giờ; có hiệu lực từ ngày kế tiếp và không tính lại dữ liệu cũ.

**Đổi giá có ảnh hưởng order cũ không?**
Không. Dòng đã gửi giữ phiên bản giá và công thức đã xác nhận; hóa đơn lưu bản chụp, chỉ in lại nguyên trạng.

**Hủy order khi một số món đã làm thì sao?**
Chỉ Quản lý được hủy, bắt buộc có lý do. Món Chờ làm được hoàn kho, món đã làm tính vào tiêu hao của order hủy. Doanh thu không ghi nhận.

**Khách chuyển tiền nhưng hệ thống chưa nhận thì sao?**
Thu ngân chuyển sang Chờ xác minh thanh toán, order bị khóa. Quản lý đối chiếu sao kê rồi xác nhận, mở lại thanh toán, hoặc đóng chưa thu có lý do. Hệ thống không tự đóng theo thời gian.

**Tiền QR đến muộn thì sao?**
Đúng giao dịch, đủ tiền và chưa có quyết định của Quản lý thì tự xác nhận, đồng thời hủy mã QR mới chưa nhận tiền. Đã có quyết định mở lại, sai tiền hoặc đã thu bằng khoản khác thì ghi vào ngoại lệ để Quản lý xử lý. Đây là phần em không demo vì script chỉ xử lý giao dịch đang chờ.

**Kiểm kê lệch thì xử lý thế nào?**
Chỉ nhập số đếm và lý do, không nhập giá. Thiếu sinh giao dịch điều chỉnh, phiếu xuất hủy chỉ để tham chiếu nên không trừ hai lần. Thừa tạo điều chỉnh tăng, không tạo nhập mua. Trong phiên, kho bị khóa.

### Kỹ thuật và an toàn

**Quyền kiểm tra ở đâu?**
Ở API với mọi thao tác. Ẩn nút chỉ để dễ dùng. Em đã thử dùng token Thu ngân gọi thẳng API kho, kết quả 403.

**Mật khẩu lưu thế nào? Đăng xuất có thu hồi token không?**
Mật khẩu băm bằng Argon2, không lưu bản rõ. Đổi hoặc đặt lại mật khẩu thì token cũ mất hiệu lực nhờ phiên bản token. Đăng xuất hiện chỉ xóa thông tin trên trình duyệt, chưa thu hồi JWT ở máy chủ; đây là hạn chế đã ghi nhận.

**Thanh toán QR có an toàn không?**
Webhook phải xác thực, đối chiếu giao dịch và số tiền; xử lý trùng không tạo hóa đơn thứ hai. Bản demo dùng bộ giả lập; adapter SePay có test tự động, chưa chạy giao dịch thật.

**Lỗi hủy phiếu nhập do đâu, sao test trước đó không phát hiện?**
Ràng buộc CHECK trong migration chỉ cho "Hoàn kho" gắn với dòng order, trong khi model đã cho phép gắn dòng phiếu nhập. Test thường chạy SQLite, tạo bảng từ model nên không thấy lệch. Em sửa bằng migration mới và thêm test hồi quy trên MySQL.

**Hệ thống chịu tải được bao nhiêu?**
Với 20.000 order, ở 5/10/20 người dùng p95 nghiệp vụ lớn nhất là 356/427/767 ms, không lỗi. Mỗi nhóm đo một lần, có yêu cầu đơn lẻ tới 1.400 ms, nên chưa đủ kết luận cho tải dài.

**Vì sao chỉ 223/247?**
Nhóm công bố đúng kết quả lượt 03–04/11, có ghi rõ ca không đạt theo mã. Sau đó em đã sửa và chạy lại 5 ca, nhưng chưa gộp vào số chính thức vì chưa chạy lại toàn bộ.

### AI Assistant

**AI có sửa hoặc xóa dữ liệu được không?**
Có bốn lớp chặn: mô hình chỉ thấy view của vai trò; SQL qua bộ kiểm duyệt, chỉ cho SELECT; tài khoản CSDL chỉ đọc riêng; giới hạn 500 dòng và 3 giây.

**Vì sao không cho AI đọc thẳng bảng?**
View vừa giới hạn quyền vừa đơn giản hóa lược đồ cho mô hình.

**AI có từ chối câu ngoài phạm vi không?**
Ở cấu hình B, 83/90 lượt từ chối đúng; còn 6 lượt lỗi và 1 lượt sinh SQL. Phép thử này dừng trước khi thực thi, nên chỉ đo hành vi mô hình, không phải toàn bộ lớp bảo vệ. Ba lượt sinh SQL trên toàn bộ cấu hình đều là yêu cầu xuất lịch sử thanh toán ra ngoài; hệ thống chưa kiểm soát mục đích dùng dữ liệu.

**84,58%, 98,07% và 66,67% khác nhau thế nào?**
84,58% là SQL đúng trên toàn bộ 240 lượt, tính cả lượt lỗi. 98,07% chỉ xét 207 lượt không lỗi. 66,67% là câu trả lời diễn giải đúng trên toàn bộ lượt.

**Nới lỏng và khắt khe khác nhau thế nào?**
Nới lỏng cho thừa cột miễn đủ cột và đúng giá trị của đáp án. Khắt khe đòi trùng toàn bộ bảng.

**Vì sao cấu hình C effort cao lại kém?**
C bị timeout nhiều do giới hạn 5 giây mỗi lần gọi (36,67%). Khi trả lời được thì đúng 152/152. Kết luận chỉ áp dụng trong ràng buộc này.

**B có thực sự tốt hơn A không?**
Hơn 2,5 điểm phần trăm, mỗi cấu hình ba lần lặp, chưa đủ để khẳng định trong mọi điều kiện.

**Vì sao dùng hai mô hình?**
Opus sinh SQL. Haiku viết câu trả lời từ số liệu do code tính sẵn, nên nhanh và rẻ hơn, giảm lỗi số liệu.

**Chi phí bao nhiêu?**
Bình quân B khoảng 0,005 USD/câu; tính riêng lượt đủ usage khoảng 0,006 USD/câu. Số liệu chưa đối soát với hóa đơn nhà cung cấp.

**Đánh giá có khách quan không?**
Bộ đề khóa trước khi chạy. Hạn chế: đáp án và phần chấm diễn giải do agent AI kiểm tra, chưa có người chấm độc lập.

**Nếu Claude API lỗi thì sao?**
Bán hàng và kho vẫn chạy độc lập. Trợ lý báo lỗi và gợi ý hỏi lại, không trả kết quả sai.

### Câu khó, trả lời thẳng

**Hạn chế lớn nhất của hệ thống là gì?**
AI còn lỗi/timeout 13,75%; câu khó chỉ đúng 55%; còn 19 ca chức năng chưa đạt; SePay chưa chạy giao dịch thật; chưa có kết quả SUS/UAT.

**Hệ thống đã dùng thực tế được chưa?**
Chưa. Luồng chính chạy được trên dữ liệu mô phỏng, nhưng còn lỗi đã biết và chưa có người dùng thật đánh giá.

**Phần này do em làm hay AI làm?**
Trả lời đúng theo thực tế phân công của nhóm và những gì bạn tự giải thích được. Đọc trước phần code mình sẽ trình bày để nói được luồng.

---

## 6. Tự kiểm tra trước ngày demo

1. Tồn 15 kg, chọn 2 suất 0,15 kg: ba con số tồn đổi thế nào khi chọn, gửi, hủy trước gửi, hủy sau gửi?
2. Có 5 kg lô A, 10 kg lô B, lấy 7 kg: trừ thế nào? Giá vốn có theo giá từng lô không?
3. Order 01:30 thuộc ngày nào?
4. Giữ món hết hạn có mở kiểm kê được không?
5. Thanh toán xong bàn có tự trống không? Vì sao?
6. Webhook gửi hai lần thì sao?
7. Xuất hủy món đã chế biến có trừ kho thêm không?
8. Vì sao còn 19 ca nhưng vẫn báo 223/247?
9. Tự nói toàn bộ cột Câu nói ở phần 3 trong dưới 15 phút, không nhìn tài liệu.

Đáp án và các nhánh chi tiết: tài liệu 03 phần K và M.5, báo cáo 6.4–6.5. Kết quả chạy lại: `docs/testing/artifacts/2026-11-06-fix-demo-blockers/ket-qua-chay-lai.md`.

---

## 7. Demo đầy đủ 30 Use Case

Dùng để tự tập, hoặc mở đúng màn khi Hội đồng hỏi; toàn bộ khoảng 35–45 phút (ước tính), không dùng trong 15 phút chính.

Nhãn nút lấy từ code. Lượt tập 06/11 mới đi hết luồng Thu ngân đến hóa đơn QR, nên các dòng còn lại phải tự bấm thử ít nhất một lần.

| UC | Tài khoản · Màn hình | Bấm thử | Ý cần nói |
|---|---|---|---|
| 5.4 | Đăng nhập | Đăng nhập sai rồi đúng; đổi mật khẩu | Sai hoặc bị khóa đều bị từ chối; đổi mật khẩu làm token cũ mất hiệu lực |
| 1.1 | Quản lý · Danh mục → Nhóm món | Thêm, sửa, xóa nhóm. **Không** thử sắp xếp (CAT-03) | Ba trường hợp xóa nhóm |
| 1.2 | Danh mục → Món ăn | **Thêm món**, tạm dừng rồi mở lại, xóa món mới tạo | Nháp chưa bán được; món đã có lịch sử chỉ xóa mềm |
| 1.3 | Chi tiết món → Công thức | Gán công thức; lên lịch; hủy lịch; áp dụng ngay | Gán lần đầu có hiệu lực ngay; mỗi món tối đa một lịch chờ |
| 1.4 | Chi tiết món → Giá bán | Lên lịch giá; **Hủy lịch**; **Áp dụng giá ngay** | Sửa trực tiếp không hủy lịch đang chờ |
| 1.5 | Danh mục → Bàn | Thêm, sửa bàn | Bàn đang phục vụ không xóa được |
| 1.6 | Bếp · Danh mục → Nguyên liệu | Thêm, sửa | Đơn vị tính bị khóa sau khi đã được tham chiếu; form có lỗi giữ giá trị cũ (CAT-13) |
| 1.7 | Danh mục → Nhà cung cấp | Thêm, sửa | Đã có lịch sử nhập thì chỉ xóa mềm |
| 3.1 | Bếp · Kho → Phiếu nhập | **Tạo phiếu nhập**; sửa; **Hủy phiếu** phiếu chưa dùng | Mỗi dòng là một lô; hạn tự tính; đã xuất hoặc đang giữ thì không sửa/hủy được |
| 3.5 | Kho → Tồn kho | Tìm nguyên liệu, **Lô và lịch sử** | Ba con số tồn; lô hết hạn vẫn tính vào sổ sách |
| 2.1 | Thu ngân · Bán hàng | Chọn bàn, thêm món, ghi chú, **Hủy lượt chọn**, **Gửi bếp** | Giữ món rồi mới trừ kho |
| 2.2 | Bán hàng → **Đơn mới** (Mang về) | Thêm món, gửi, thanh toán | Không gắn bàn, không đổi trạng thái bàn |
| 2.3 | Bàn → **Thanh toán** | **Thêm món**, **Đã xác nhận xong**, **Hủy món**, **Chuyển bàn**, **In lại**, **Báo in lỗi** | Chỉ Chờ làm mới hủy được; chỉ chuyển sang bàn trống; không gộp bàn |
| 2.4 | Màn thanh toán | **In phiếu tạm tính**, **Tiền mặt**, **Xác nhận đã thu**, **In lại** | Hóa đơn chỉ phát hành sau khi thu; in lại nguyên trạng |
| 2.5 | Màn thanh toán | **QR chuyển khoản**, **Tạo mã QR**, **Hủy QR**, **Kiểm tra lại**, **Khách báo đã chuyển tiền** | QR 10 phút; hủy hoặc hết hạn thì về Đang mở |
| 2.6 | Quản lý · Chi tiết order chờ xác minh | **Xác nhận đã nhận tiền**, **Lưu kết quả chưa đủ căn cứ**, **Mở lại thanh toán**, **Đóng chưa thu** | Không tự đóng; mọi quyết định có lý do và lịch sử |
| 2.6 | Báo cáo → Thanh toán → Ngoại lệ | Xem **Áp dụng**, **Đã hoàn tiền** | Chỉ giải thích: script demo không tạo được khoản đến muộn |
| 2.7 | Quản lý · Chi tiết order Đang mở | Hủy toàn bộ order, nhập lý do | Thu ngân không có quyền này; món đã làm tính tiêu hao |
| 2.8 | Quản lý đơn hàng / **Tìm nâng cao** | Lọc theo mã, bàn, ngày, trạng thái | In lại không phát sinh doanh thu hay tiêu hao |
| 3.2 | Kho → Lô và biến động | Xem nhập, xuất, hoàn của order vừa bán | Tiêu hao do hệ thống ghi, không có bước xác nhận thêm |
| 3.3 | Kho → Phiếu xuất → **Tạo phiếu xuất** | Nguồn Nguyên liệu; xem nguồn Món đã chế biến | Ba nguồn; không trừ hai lần |
| 3.4 | Kho → Kiểm kê | Mở phiên; Thu ngân thử giữ món; nhập đủ mọi nguyên liệu; **Xác nhận kiểm kê** hoặc hủy | Phải đếm đủ toàn bộ nguyên liệu mới xác nhận được, nên trên sân khấu chỉ mở rồi hủy phiên |
| 4.1 | Quản lý · Báo cáo → Doanh thu, So sánh | Đổi kỳ, đổi nhóm | Chỉ tính order Đã thanh toán |
| 4.2 | Báo cáo → Lợi nhuận | Chọn tháng có phiếu nhập | Ba khoản giá vốn |
| 4.3 | Báo cáo → Món ăn | Xếp hạng | Theo số lượng và doanh thu |
| 4.4 | Báo cáo → Khung giờ | Xem phân bố | Theo giờ và ngày trong tuần |
| 4.5 | Báo cáo → Order hủy, Thanh toán | Xem từng nhóm | Khoản chưa thu tách riêng khỏi doanh thu |
| 5.1 | Cài đặt → Tài khoản | **Thêm tài khoản**, khóa, mở khóa, đặt lại mật khẩu | Lỗi tạo tài khoản đã sửa; thao tác quản trị ghi nhật ký |
| 5.2 | Cài đặt → Cấu hình | Đổi giờ Business Date rồi chọn lại giờ cũ để hủy lịch | Có hiệu lực từ ngày kế tiếp |
| 5.3 | Cài đặt → Nhật ký thao tác | Lọc, mở một bản ghi đã kiểm tra | Chỉ xem, không sửa/xóa |
| 6.1 | Trợ lý AI cả ba vai trò | Câu ở phần 3; Thu ngân hỏi *Hôm nay đã có bao nhiêu hóa đơn?* và *Giá vốn tháng này là bao nhiêu?* | Khi tập: 1,8 giây trả 9 hóa đơn; câu giá vốn được đề nghị đổi sang doanh thu |

**Lưu ý kiểm kê:** phải hết lượt chọn chưa gửi và hết món Chờ làm mới mở được, kể cả món của order vừa demo. Phiên đang mở sẽ chặn bán hàng, nên phải xác nhận hoặc hủy trước khi bán tiếp.

---

## 8. SePay (QR thật)

**Khuyến nghị: buổi demo vẫn dùng `simulator`.** SePay thật chưa từng chạy một giao dịch nào, cần URL công khai và phụ thuộc mạng, ngân hàng. Chỉ nên đưa vào demo sau khi đã chạy thành công và có bằng chứng.

Hướng dẫn gốc: `docs/payment-sepay-setup.md`. Chạy trên bản sao CSDL hoặc sao lưu trước, vì script sẽ tạo order thật trong CSDL.

### Các bước chạy thử một lần

1. **Chuẩn bị:** tài khoản SePay đã liên kết ngân hàng nhận tiền.
2. **Chọn cách nhận kết quả:**
   - Có webhook (đúng luồng chính): `ngrok http 8000` hoặc `cloudflared tunnel --url http://localhost:8000`.
   - Không có URL công khai: để `SEPAY_POLL_INTERVAL_SECONDS=30` và có `SEPAY_API_TOKEN`. API tự đọc danh sách giao dịch, nên không chứng minh được webhook.
3. **Sửa `.env` rồi khởi động lại API:**
   ```dotenv
   PAYMENT_GATEWAY=sepay
   SEPAY_BANK_ACCOUNT=<số tài khoản>
   SEPAY_BANK_CODE=<mã ngân hàng SePay>
   SEPAY_ACCOUNT_NAME=<tên chủ tài khoản>
   SEPAY_WEBHOOK_API_KEY=<khóa bí mật tự đặt>
   SEPAY_API_TOKEN=<token SePay, cho nút Kiểm tra lại>
   SEPAY_PAYMENT_PREFIX=TT
   ```
   Thiếu ba biến tài khoản, mã ngân hàng hoặc khóa webhook thì API từ chối khởi động. Prefix phải trùng cấu trúc mã thanh toán trong SePay.
4. **Khai webhook trên SePay:** URL `https://<domain>/api/v1/sales/webhooks/sepay`, `POST`, sự kiện tiền vào, xác thực `Authorization: Apikey <SEPAY_WEBHOOK_API_KEY>`. Nhãn trên trang SePay chưa được đối chiếu, có thể khác.
5. **Kiểm tra:** `curl -s localhost:8000/health`, phải thấy `"gateway":"sepay"` và `"live":true`.
6. **Chuyển tiền thật:**
   ```bash
   API_BASE_URL=http://localhost:8000 SMOKE_USERNAME=seed_manager SMOKE_PASSWORD='<mật khẩu>' \
     uv run --project apps/api python scripts/sepay_smoke.py --dish <mã món rẻ>
   ```
   Không truyền `--dish` thì script lấy món đầu danh sách, số tiền là giá món đó. Chuyển đúng số tiền và nội dung `TT<mã>`; kết quả đúng là in `OK: paid. Invoice ...`.
7. **Các ca nên thử:** đúng tiền; gửi lại webhook (không tạo hóa đơn thứ hai); sai số tiền (vào ngoại lệ, xem ở Báo cáo → Thanh toán); sai khóa (bị từ chối).
8. **Lưu bằng chứng:** ảnh app ngân hàng (che số tài khoản), màn hóa đơn, log. Ghi vào báo cáo.
9. **Trả lại cấu hình demo:** `PAYMENT_GATEWAY=simulator`, khởi động lại API. Tiền đã chuyển phải tự hoàn ngoài hệ thống.

### Khi demo

| | `simulator` | `sepay` |
|---|---|---|
| Xác nhận tiền | `demo_pay_qr.py` | Tiền thật qua ngân hàng |
| `demo_pay_qr.py` | Chạy được | Bị từ chối, nên không giả được tiền thật |
| Màn hình | "Mã QR mô phỏng — không chuyển tiền thật." | VietQR đúng tài khoản thật |
| Cần mạng công khai | Không | Có, nếu dùng webhook |

**Câu nói khi dùng simulator:** "Kiến trúc tách cổng thanh toán thành adapter. Demo dùng bộ giả lập nên không có tiền thật. Adapter SePay đã có test tự động nhưng chưa chạy giao dịch thật, nên em không xem là đã kiểm chứng."

**Bảo mật:** không commit `.env`, không chiếu màn hình `.env`, tắt tunnel ngay sau khi thử vì tunnel để API ra Internet.

---

## 9. Máy in phiếu bếp

Demo không cần máy in: để trống `KITCHEN_PRINTER_HOST` thì phiếu ở trạng thái **Chờ in**, không gửi mạng và không báo thành công.

Nếu có máy in ESC/POS qua TCP (thường cổng 9100): đặt `KITCHEN_PRINTER_HOST` và `KITCHEN_PRINTER_PORT`, chạy `make migrate` nếu chưa, khởi động lại API. Bản in không dấu tiếng Việt. Chi tiết ở `docs/kitchen-printer-setup.md`.

**Câu nói:** "Nội dung phiếu lưu cùng transaction với order, in lại dùng đúng nội dung đã lưu nên không trừ kho lần nữa. Phần máy in mới kiểm bằng bộ nhận giả lập, chưa thử trên máy in thật."
