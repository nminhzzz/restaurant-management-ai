# Câu hỏi của Hội đồng và bảng tra cứu

# Phần B. Câu hỏi có thể gặp và lời đáp

**Cách đáp chung:** trả lời ý chính trong câu đầu, giải thích trong 2–3 câu, rồi dừng. Câu nào chưa kiểm chứng thì nói: *"Phần này em chưa kiểm chứng, em xin kiểm tra và phản hồi lại Hội đồng."*

## Giữ món, kho, FIFO

**1. Tại sao không trừ kho ngay khi chọn món?**
> Thưa thầy cô, chọn món chưa chắc đã gửi. Nếu trừ ngay, khách đổi ý thì phải hoàn kho, sổ kho sinh nhiều giao dịch không phản ánh tiêu hao thật. Giữ món chỉ làm giảm khả dụng, vừa chống bán vượt tồn, vừa giữ sổ kho sạch.

**2. Giữ món hết hạn thì xử lý thế nào?**
> Phần giữ không còn chiếm khả dụng, nhưng dòng món vẫn hiển thị. Khi nhân viên gửi, hệ thống kiểm tra lại: đủ nguyên liệu thì nhận, thiếu thì báo để nhân viên xử lý. Hết hạn không tự gia hạn và không tự hủy lượt chọn.

**3. Hai thu ngân cùng tranh phần nguyên liệu cuối thì sao?**
> Thao tác giữ món chạy trong transaction, khóa nguyên liệu theo thứ tự mã tăng dần để tránh deadlock rồi mới kiểm tra khả dụng. Người đến sau sẽ thấy lượng đã giảm và bị từ chối, nên không bán vượt tồn.

**4. Lô hết hạn tính thế nào?**
> Lô hết hạn vẫn tính vào tồn sổ sách để kiểm kê và xuất hủy, nhưng không tính vào khả dụng. Nên có thể tồn sổ sách lớn mà vẫn không bán được.

**5. Có lỗi nào còn tồn tại ở giữ món không?**
> Có. Khi lượt chọn giữ hết phần khả dụng, gửi chính lượt đó vẫn có thể bị từ chối, ca TC-INV-09. Đặc tả yêu cầu cộng lại phần giữ của chính dòng đang gửi, nên đây là lỗi cần sửa và thuộc ưu tiên 1 trên slide 13.

## Giá vốn, báo cáo

**6. Đã dùng FIFO, sao giá vốn lại tính bình quân?**
> FIFO quản lý số lượng theo lô, phục vụ hạn dùng và truy vết. Giá vốn tính theo bình quân gia quyền tháng ở mức toàn nhà hàng, đúng theo đặc tả FR-REP-11. Hai việc này tách nhau.

> *Cần thống nhất với nhóm lý do chọn bình quân, vì tài liệu không ghi. Nếu chưa thống nhất, đừng tự đưa ra lý do.*

**7. Lợi nhuận gộp tính thế nào?**
> Bằng doanh thu trừ giá vốn nguyên liệu tiêu hao, gồm ba khoản: giá vốn bán hàng, hao hụt kho, và tiêu hao của order hủy hoặc đóng chưa thu. Tính theo tháng, chưa gồm lương và mặt bằng.

**8. Sửa hoặc hủy phiếu nhập tháng trước có làm sai báo cáo không?**
> Hệ thống tự tính lại bình quân và giá vốn của tháng đó cùng các tháng sau, còn doanh thu và hóa đơn không đổi. Em đã thử tạo rồi hủy một phiếu trong tháng 10: giá vốn về đúng số cũ, doanh thu giữ nguyên.

**9. Vì sao ngày kinh doanh bắt đầu lúc 6 giờ?**
> Nhà hàng có thể mở khuya, order lúc 1 giờ sáng vẫn nên thuộc ca hôm trước. Quản lý đổi được giờ, có hiệu lực từ ngày kinh doanh kế tiếp và không tính lại dữ liệu đã lưu.

**10. Đổi giá có ảnh hưởng hóa đơn cũ không?**
> Không. Dòng đã gửi giữ phiên bản giá và công thức đã xác nhận, hóa đơn chỉ được in lại nguyên trạng.

## Thanh toán, hủy order

**11. Vì sao không cho thu ngân tự xác nhận QR?**
> Để tránh ghi nhận tiền chưa về. Xác nhận phải đến từ cổng thanh toán qua webhook đã xác thực; có tranh chấp thì chuyển sang quy trình xác minh do Quản lý xử lý.

**12. Tiền QR đến muộn thì sao?**
> Nếu đúng giao dịch, đủ tiền và Quản lý chưa quyết định gì, hệ thống tự xác nhận và hủy mã QR mới chưa nhận tiền. Nếu đã mở lại thanh toán, sai số tiền hoặc đã thu bằng khoản khác, khoản đó vào danh sách ngoại lệ để Quản lý áp dụng hoặc ghi nhận hoàn tiền. Không cộng doanh thu hai lần.

**13. Có dùng tiền thật chưa?**
> Chưa. Demo dùng bộ giả lập. Adapter SePay có test tự động nhưng chưa chạy giao dịch thật, nên nhóm chưa xem là đã kiểm chứng.

**14. Hủy order khi có món đã làm thì sao?**
> Chỉ Quản lý được hủy và phải có lý do. Món Chờ làm được hoàn về lô gốc; món đã làm giữ nguyên tiêu hao và tính vào chi phí của order hủy. Doanh thu không ghi nhận.

**15. Vì sao không hỗ trợ giảm giá hay thẻ ngân hàng?**
> Đây là phạm vi đã chốt của đề tài: chỉ tiền mặt và QR do hệ thống tạo, không áp dụng khuyến mãi, không tách VAT.

## Kiểm kê, phân quyền, an toàn

**16. Kiểm kê lệch thì xử lý thế nào?**
> Người kiểm kê nhập số đếm và lý do, không nhập giá. Thiếu thì giao dịch điều chỉnh làm giảm tồn, phiếu xuất hủy chỉ để tham chiếu nên không trừ hai lần. Thừa thì điều chỉnh tăng, không tạo phiếu nhập mua. Trong phiên kiểm kê, các biến động kho bị khóa.

**17. Ẩn nút có phải là phân quyền không?**
> Không. Quyền được kiểm tra ở API. Em đã thử dùng token Thu ngân gọi thẳng API kho và nhận lỗi 403.

**18. Vì sao chỉ có ba vai trò?**
> Đây là phạm vi đã chốt: Quản lý, Thu ngân/Nhân viên order và Bếp. Khảo sát cũng cho thấy 49 trên 51 người muốn phạm vi riêng theo vai trò. Quản lý kế thừa quyền của hai vai trò còn lại.

**19. Mật khẩu và phiên đăng nhập xử lý thế nào?**
> Mật khẩu băm bằng Argon2. Đổi hoặc đặt lại mật khẩu thì token cũ mất hiệu lực. Hạn chế là đăng xuất hiện chỉ xóa thông tin trên trình duyệt, chưa thu hồi token ở máy chủ.

## AI

**20. AI có xóa hoặc sửa dữ liệu được không?**
> Bốn lớp đều chặn việc này: mô hình chỉ thấy view; SQL qua bộ kiểm duyệt phân tích cú pháp, chỉ cho SELECT; tài khoản CSDL chỉ đọc; có giới hạn dòng và thời gian. Vì vậy dù mô hình sinh sai, CSDL vẫn từ chối thao tác ghi.

**21. Vì sao dùng view mà không cho đọc bảng?**
> View giới hạn dữ liệu theo vai trò và đơn giản hóa lược đồ cho mô hình. Bảng gốc không xuất hiện trong prompt.

**22. Vì sao dùng hai mô hình?**
> Sinh SQL cần suy luận nên dùng Opus 5.5. Viết câu trả lời chỉ diễn đạt số liệu do code tính sẵn nên dùng Haiku 5.5, nhanh và rẻ hơn, đồng thời giảm lỗi số liệu.

**23. 84,58%, 98,07% và 66,67% khác nhau thế nào?**
> 84,58% là tỷ lệ SQL đúng trên toàn bộ 240 lượt, tính cả lượt lỗi. 98,07% chỉ xét 207 lượt không lỗi. 66,67% là tỷ lệ câu trả lời diễn giải đạt trên toàn bộ lượt.

**24. Nới lỏng và khắt khe là gì?**
> Nới lỏng cho phép thừa cột, miễn đủ cột và đúng giá trị của đáp án. Khắt khe yêu cầu kết quả trùng toàn bộ.

**25. Vì sao cấu hình C effort cao lại kém nhất?**
> C bị hết thời gian tới 36,67% do giới hạn 5 giây mỗi lần gọi mô hình, nhưng các lượt trả lời được thì đúng 152 trên 152. Kết luận này chỉ đúng trong ràng buộc thời gian đó, không có nghĩa effort cao là kém.

**26. Có khẳng định B tốt hơn A không?**
> Chưa. B hơn A 2,5 điểm phần trăm, mỗi cấu hình chỉ lặp ba lần trên cùng bộ câu hỏi, nên chưa đủ để khẳng định trong mọi điều kiện.

**27. AI có từ chối câu hỏi ngoài phạm vi không?**
> Với B, 83 trên 90 lượt từ chối đúng; còn 6 lượt lỗi và 1 lượt vẫn sinh SQL, thuộc yêu cầu xuất lịch sử thanh toán ra ngoài. Phép thử này dừng trước khi thực thi, nên chỉ đo hành vi mô hình. Hệ thống kiểm soát được dữ liệu nào được đọc, chưa kiểm soát mục đích sử dụng.

**28. Chi phí AI bao nhiêu?**
> Bình quân B khoảng 0,005 USD một câu; tính riêng lượt có đủ dữ liệu sử dụng khoảng 0,006 USD. Con số này chưa đối soát với hóa đơn nhà cung cấp.

**29. Làm thế nào giảm lỗi 13,75%?**
> Theo kết quả đo, hướng ưu tiên là giảm lỗi do giới hạn 5 giây mỗi lần gọi, cải thiện truy vấn phức tạp, mở rộng bộ câu hỏi và có người chấm độc lập.

**30. Claude API lỗi thì hệ thống có dừng không?**
> Không. Bán hàng và kho hoạt động độc lập với AI. Trợ lý báo lỗi và gợi ý hỏi lại, không trả kết quả sai.

## AI: bảo vệ dữ liệu và prompt injection

**38. Prompt injection là gì, hệ thống chống thế nào?**
> Là việc chèn câu lệnh vào câu hỏi hoặc dữ liệu để mô hình làm trái quy tắc. Không thể bảo đảm mô hình không bao giờ bị thao túng, nên nhóm coi đầu ra của mô hình là không đáng tin. Dù sinh câu SQL xấu, câu đó vẫn phải qua bộ kiểm duyệt, chỉ chạm được view của vai trò, và chạy bằng tài khoản chỉ có quyền đọc.

**39. Injection nhúng trong dữ liệu, ví dụ tên món hoặc ghi chú, thì sao?**
> Trong một lượt hỏi, câu SQL đã chạy xong trước khi mô hình diễn giải đọc dữ liệu, và bước diễn giải chỉ trả về văn bản. Ở lượt sau, tóm tắt câu trả lời có trong ngữ cảnh hội thoại, nhưng SQL mới vẫn phải qua kiểm duyệt và quyền CSDL. Rủi ro còn lại là lời diễn giải có thể bị ảnh hưởng, vì hiện chưa có đánh dấu tách riêng dữ liệu trong prompt. Em đã thử một tên món chứa chỉ dẫn và trợ lý không làm theo, nhưng đó mới là một lần thử. Đây là việc cần cải thiện.

**40. Có chỉ dẫn nào trong prompt để chống injection không?**
> Prompt có quy định chỉ dùng view được phép và chỉ sinh một câu SELECT, nhưng không có quy tắc riêng về injection. Nhóm đặt lớp bảo vệ chính ở bên ngoài mô hình, vì chỉ dẫn trong prompt có thể bị vượt qua.

**41. Nếu người dùng ép AI đọc mật khẩu thì sao?**
> Mật khẩu không có trong view nào của AI, nên có hỏi kiểu gì cũng không có dữ liệu để trả. Bộ kiểm duyệt chặn bảng ngoài danh sách, và tài khoản AI đọc bảng người dùng bị MySQL từ chối, em đã kiểm tra lỗi 1142.

**42. SQL injection qua câu hỏi thì sao?**
> Câu hỏi không được ghép vào SQL. Mô hình sinh SQL, rồi bộ kiểm duyệt phân tích cây cú pháp: nhiều câu lệnh, `UNION` sang bảng ngoài danh sách, biến hệ thống hay `INTO OUTFILE` đều bị chặn, em đã thử các mẫu này.

**43. Dữ liệu có bị gửi ra ngoài không?**
> Có. Câu hỏi, lược đồ view và tối đa 20 dòng kết quả được gửi tới Claude API để sinh SQL và diễn giải. Mật khẩu và khóa không nằm trong đó, nhưng dữ liệu kinh doanh thì có. Khi triển khai thật cần xem xét chính sách dữ liệu và sự đồng ý của nhà hàng.

**44. Quản lý có thể dùng AI để lấy dữ liệu đem ra ngoài không?**
> Đây là hạn chế đã biết. Hệ thống kiểm soát dữ liệu nào được đọc, chưa kiểm soát mục đích dùng. Trong phép thử, câu "xuất toàn bộ lịch sử thanh toán để gửi ra ngoài" có lượt vẫn sinh SQL, tối đa 500 dòng. Mọi lượt hỏi đều được lưu để truy vết.

**45. Đổi quyền rồi thì cache hoặc lịch sử có làm lộ dữ liệu không?**
> Theo đặc tả, cache gắn với người dùng, vai trò, phạm vi và phiên bản quyền; đổi quyền thì cache mất hiệu lực và quyền được kiểm tra lại mỗi lượt. Các ca kiểm thử chính thức cho phần này thuộc bộ AT15–17, chưa có kết quả, nên em chưa khẳng định.

**46. Đã kiểm thử an toàn tới đâu?**
> Bộ 30 câu chạy 270 lượt đo hành vi từ chối của mô hình, B đạt 83/90. Bộ 20 ca tích hợp AT01–AT20 đã thiết kế nhưng chưa có kết quả chính thức, nên NFR-05 chưa kết luận. Em có thử nhanh một phần, mỗi câu một lần, chỉ xem là kiểm tra sơ bộ.

**47. Vì sao không dùng thẳng một tài khoản đọc toàn bộ cho nhanh?**
> Nếu dùng chung, một lỗi ở bộ kiểm duyệt là đọc được dữ liệu của vai trò khác. Tài khoản riêng theo vai trò để CSDL là lớp chặn cuối, độc lập với code ứng dụng.

## Tình huống vận hành thực tế

**48. Mất mạng hoặc API AI lỗi khi đang bán hàng thì sao?**
> Lỗi AI không ảnh hưởng bán hàng và kho vì các phần này chạy độc lập. Nếu mất kết nối tới máy chủ của chính hệ thống thì không thao tác được; hệ thống chưa có chế độ ngoại tuyến.

**49. Máy in bếp hỏng thì sao?**
> Phiếu đã lưu cùng order nên không mất. Giao diện hiện trạng thái in, nhân viên in lại sau khi khắc phục; in lại dùng nội dung đã lưu nên không trừ kho thêm.

**50. Nguyên liệu bị hỏng đúng lúc đang được giữ cho bàn khác thì sao?**
> Khi lập phiếu xuất hủy lô đó, hệ thống giải phóng các lượt giữ bị ảnh hưởng trong cùng transaction và thông báo để nhân viên kiểm tra lại.

**51. Đang phục vụ mà muốn kiểm kê thì sao?**
> Không mở được khi còn lượt chọn chưa xử lý hoặc món Chờ làm. Trong phiên kiểm kê, giữ món, gửi món và nhập xuất kho đều bị chặn để số đếm không lệch, nên kiểm kê được thực hiện sau giờ phục vụ.

**52. Khách đã trả tiền mà muốn đổi món thì sao?**
> Order đã thanh toán bị khóa nội dung và tiền, hóa đơn không sửa được. Khách gọi thêm thì lập order mới. Hoàn tiền thực hiện ngoài hệ thống theo quy định của nhà hàng.

## Kiểm thử, công nghệ

**31. Tại sao còn 23 ca không đạt mà vẫn báo cáo?**
> Nhóm báo cáo đúng kết quả, có mã ca cụ thể ở phụ lục. Ca có đầu ra sai được ghi Không đạt, không làm đẹp số liệu. Sau đó em đã sửa và chạy lại một phần, nhưng chưa gộp vào số chính thức.

**32. Lỗi hủy phiếu nhập do đâu, sao trước đó không phát hiện?**
> Ràng buộc CHECK trong migration chỉ cho "Hoàn kho" gắn với dòng order, còn model đã cho phép gắn với dòng phiếu nhập. Test thường chạy trên SQLite, tạo bảng từ model nên không thấy lệch. Lỗi chỉ lộ trên MySQL thật. Em sửa bằng migration mới và thêm test trên MySQL.

**33. Dữ liệu demo từ đâu?**
> Là dữ liệu mô phỏng 12 tháng, sinh qua tầng service để quan hệ và sổ kho luôn khớp. Vì sinh tự động nên một số món xếp nhóm chưa hợp lý, không ảnh hưởng logic nghiệp vụ.

**34. Vì sao chọn FastAPI, Next.js, MySQL?**
> FastAPI viết bằng Python nên xử lý nghiệp vụ và AI trên cùng nền tảng, thuận tiện tích hợp thư viện Text-to-SQL. Next.js phục vụ giao diện theo vai trò và chat. MySQL lưu dữ liệu quan hệ và thực thi ràng buộc toàn vẹn.

**35. Hệ thống dùng thực tế được chưa?**
> Chưa nên khẳng định. Luồng chính chạy được trên dữ liệu mô phỏng, nhưng còn lỗi đã biết, SePay chưa chạy tiền thật và chưa có kết quả đánh giá SUS, UAT với người dùng.

**36. Em đóng góp phần nào trong nhóm?**
> Theo phân công, em phụ trách giữ nguyên liệu, gửi món, hủy và hoàn kho; thanh toán và hóa đơn; phần AI gồm view theo vai trò, tài khoản chỉ đọc, kiểm duyệt SQL, chuẩn hóa câu hỏi và sinh SQL; cùng kiểm thử Bán hàng.

**37. Nếu làm lại, em sẽ thay đổi gì?**
> *Hãy trả lời bằng trải nghiệm của bạn.* Một ý có căn cứ: chạy test tích hợp trên MySQL thật sớm hơn, vì lỗi hủy phiếu nhập cho thấy SQLite không phát hiện được sai lệch giữa model và migration.

## Cách kiểm thử và nguồn số liệu

**53. Số 223/247 lấy ở đâu, ai xác nhận?**
> Thưa thầy cô, đây là lượt nhóm thực thi 247 ca của tài liệu kiểm thử trong hai ngày 3 và 4 tháng 11, trên commit 099191e. Danh sách ca nằm trong tài liệu 06. Việc thực thi do nhóm tự làm, chưa có bên độc lập xác nhận.

> *Trong repo chưa có log gốc của lượt này. Hãy hỏi nhóm lấy biên bản trước ngày demo; nếu chưa có thì đừng nói là "có log".*

**54. Sao hôm trước 223 mà đã sửa rồi không nâng thành 228?**
> Vì 5 ca chạy lại ngày 6 tháng 11 nằm trên phiên bản mã nguồn khác. Một tỷ lệ chỉ có nghĩa khi toàn bộ ca chạy trên cùng một phiên bản, nên nhóm giữ nguyên 223 và báo riêng 5 ca này.

**55. Vì sao không dùng 100% tự động mà còn thao tác tay?**
> Test tự động kiểm tra logic ở mức API và service, nhưng không xác nhận được người dùng thấy gì trên màn hình. Vì vậy hai loại được thống kê riêng và không cộng vào nhau.

**56. Test tự động chạy SQLite, có đáng tin không?**
> Phần lớn test backend chạy SQLite để nhanh, và đó từng là điểm yếu: lỗi hủy phiếu nhập do ràng buộc trong migration lệch với model không lộ ra trên SQLite. Vì vậy nhóm có thêm bộ tích hợp trên MySQL thật, và đã bổ sung test hồi quy cho hai lỗi này.

**57. p95 là gì, sao không dùng trung bình?**
> p95 là mức mà 95% yêu cầu nhanh hơn. Trung bình che mất các yêu cầu chậm, trong khi người dùng cảm nhận rõ nhất chính những lần chậm đó. Ở 20 người vẫn có yêu cầu đơn lẻ tới 1.400 mili giây.

**58. Kết quả hiệu năng này có đại diện cho nhà hàng thật không?**
> Chưa. Đó là dữ liệu mô phỏng, đo trên một máy, và kịch bản tải không gồm thanh toán, in phiếu. Kết quả cho biết đạt ngưỡng trong điều kiện thử, chưa thay thế đo trên môi trường triển khai thật.

**59. Đáp án chuẩn của 80 câu do ai kiểm tra?**
> Ba agent AI giải độc lập 20 câu mà không nhìn SQL chuẩn. Ban đầu khớp 16 trên 20; bốn câu khác biệt do làm tròn, phạm vi cột và cách diễn đạt, và đạt 20 trên 20 theo tiêu chí nới lỏng. Đây là hạn chế: chưa có người kiểm tra độc lập.

**60. Vì sao giới hạn 5 giây mỗi lần gọi mô hình, nới ra thì lỗi giảm chứ?**
> Mỗi câu được sinh SQL tối đa hai lần và NFR-02 yêu cầu p95 dưới 10 giây, nên giới hạn mỗi lần gọi ảnh hưởng trực tiếp đến thời gian chờ. Nới ra có thể giảm lỗi nhưng người dùng phải chờ lâu hơn. Nhóm chưa có số đo cho phương án nới, nên đây là việc cần đo tiếp.

**61. Vì sao chọn B dù C từ chối an toàn cao hơn?**
> Vì C có tỷ lệ lỗi 36,67%, cao gấp hơn hai lần B, và độ đúng nới lỏng chỉ 63,33%. Chênh lệch từ chối 85 so với 83 trên 90 lượt là rất nhỏ. Còn so với A, B nhỉnh hơn 2,5 điểm phần trăm, nhưng 3 lần lặp chưa đủ để khẳng định chắc chắn.

**62. Chi phí AI mỗi câu là bao nhiêu?**
> Cấu hình B ghi nhận bình quân 0,00507 USD mỗi câu trên toàn bộ lượt. Do một số lượt hết giờ thiếu số liệu sử dụng, con số thực có thể cao hơn; nhóm ước lượng khoảng 0,006 USD mỗi câu và chưa đối soát với hóa đơn.

## Tình huống sai

**63. Em chỉ demo đường đúng, còn khi người dùng làm sai thì sao?**
> Em đã demo ba trường hợp: chọn vượt nguyên liệu, kiểm kê khi còn món chưa gửi, hủy phiếu nhập đã dùng. Ngoài ra, nhóm đã thử webhook sai chữ ký, sai số tiền, gửi lặp và thao tác vượt quyền; hệ thống đều từ chối. Em có thể làm trực tiếp trường hợp thầy cô chọn.

**64. Thầy cô yêu cầu thử một trường hợp sai ngay bây giờ thì sao?**
> Dạ em xin thử. *(Làm trực tiếp, đọc thông báo trên màn hình. Nếu ra lỗi: "Đây là lỗi cần xử lý, em xin ghi nhận." Không biện minh.)*

## Công nghệ và tích hợp

**65. Vì sao chọn SePay mà không phải VNPay hay MoMo?**
> Nhà hàng cần nhận chuyển khoản vào đúng tài khoản ngân hàng của mình, và SePay báo biến động số dư qua webhook. *(Cần nhóm thống nhất lý do: phần này chưa có bảng so sánh các cổng trong tài liệu, nên đừng tự nêu so sánh về phí hay tính năng.)*

**66. Làm sao biết khoản tiền thuộc order nào?**
> Mỗi QR chứa nội dung `TT` kèm mã giao dịch. Khi có tiền vào, backend tìm mã đó trong dữ liệu SePay gửi, rồi đối chiếu số tiền với order. Khách sửa nội dung hoặc chuyển sai số tiền thì khoản đó vào danh sách ngoại lệ để Quản lý xử lý.

**67. Có lưu thông tin thẻ, tài khoản của khách không?**
> Hệ thống không xử lý thẻ. Tiền đi trực tiếp vào tài khoản ngân hàng của nhà hàng; hệ thống chỉ lưu mã giao dịch và số tiền. Khóa API nằm trong biến môi trường, không ở mã nguồn.

**68. Webhook giả mạo thì sao?**
> Webhook không có đúng API key bị từ chối và ghi nhật ký. Khóa được so sánh theo thời gian không đổi để tránh dò khóa. SePay xác thực bằng API key chứ không ký nội dung, nên endpoint bắt buộc chạy trên HTTPS.

**69. API sập đúng lúc khách chuyển tiền thì sao?**
> Khi chạy lại, tác vụ nền đọc danh sách giao dịch từ mốc đã lưu và xử lý phần còn thiếu. Xử lý lặp cũng an toàn vì mỗi mã giao dịch chỉ được ghi nhận một lần. Phần này mới có test tự động, chưa thử với SePay thật.

**70. Vì sao dùng Text-to-SQL, không dùng RAG?**
> Câu hỏi của quản lý chủ yếu là số liệu: tổng, xếp hạng, so sánh. SQL chạy trên dữ liệu thật sẽ cho số chính xác, và người dùng xem lại được câu SQL. RAG phù hợp hơn với tài liệu dạng văn bản.

**71. Vì sao dùng hai mô hình?**
> Sinh SQL cần độ chính xác nên dùng Opus 5.5. Diễn giải chỉ viết lại số liệu đã có nên dùng Haiku 5.5 để nhanh và rẻ hơn.

**72. Đổi nhà cung cấp mô hình có khó không?**
> Lời gọi mô hình gom trong một module riêng, nên phần kiểm duyệt, thực thi và phân quyền không phụ thuộc nhà cung cấp. Tuy vậy, nhóm chưa thử với nhà cung cấp khác, và độ đúng phải đánh giá lại.

---

# Bảng tra cứu

## 12. Bảng tình huống sai (để tra, không đọc)

Đã chạy ngày 06/11/2026 trên bản sao CSDL. Bằng chứng: `docs/testing/artifacts/2026-11-06-fix-demo-blockers/thu-tinh-huong-sai.md`.

| Làm sai | Hệ thống phản hồi | Thử trên |
|---|---|---|
| Chọn vượt phần nguyên liệu còn lại | *Món đang hết nguyên liệu.* | Web |
| Bàn khác giữ phần đã bị bàn trước giữ | HTTP 422 *Không đủ tồn kho khả dụng.* | API |
| Tìm món Nháp ở màn gọi món | Không hiện trong thực đơn | Web |
| Giữ món Nháp qua API | HTTP 422 *Món chưa có công thức hiệu lực.* | API |
| Gửi bếp hai lần cùng mã yêu cầu | Vẫn một order | API |
| Mở kiểm kê khi còn món chưa gửi | *Còn lượt giữ chỗ chưa gửi, hãy xử lý trước khi kiểm kê.* | Web |
| Hủy phiếu nhập có lô đã xuất dùng | *Phiếu nhập đã phát sinh xuất kho, phải điều chỉnh qua kiểm kê định kỳ.* | Web |
| Xuất hủy vượt tồn | HTTP 422 *Không đủ tồn kho khả dụng.* | API |
| Nhập kho số lượng âm | HTTP 422, lỗi kiểm tra dữ liệu | API |
| Hủy món không nêu lý do | HTTP 422 *Cần lý do hủy.* | API |
| Hủy món đã phục vụ | HTTP 422 *Chỉ hủy món ở trạng thái Chờ.* | API |
| Chuyển món từ Chờ làm thẳng sang Đã phục vụ | HTTP 422, không được bỏ bước | API |
| Tạo QR lần hai, thu tiền mặt, gọi thêm khi đang chờ QR | HTTP 422 *Order đã đóng.* | API |
| Webhook sai chữ ký | HTTP 401 *Chữ ký không hợp lệ.* | API |
| Webhook sai số tiền (cổng mô phỏng) | HTTP 422 *Số tiền không khớp.*, order vẫn chờ | API |
| Webhook đúng gửi lại lần hai | Cùng một số hóa đơn | API |
| Thu ngân vào Báo cáo, Cài đặt, nhập kho; Bếp thanh toán | HTTP 403 *Bạn không có quyền thực hiện chức năng này.* | API |
| Thu ngân gõ địa chỉ `/reports` | Bị đưa về trang Bán hàng | Web |
| Đăng nhập sai mật khẩu | HTTP 401; web chỉ hiện *Yêu cầu không thực hiện được.* | Web, API |
| Giả danh, prompt injection, xóa dữ liệu với AI | Không chạy truy vấn | Web, xem `thu-an-toan-ai.md` |

**Đừng bấm các thao tác này trên sân khấu, vì đang là lỗi hoặc dễ gây hiểu nhầm:**

| Thao tác | Hiện tượng | Nếu bị hỏi |
|---|---|---|
| Gửi bếp khi lượt chọn đã giữ hết phần còn lại (ở SAI 1: bấm 2 suất rồi gửi) | Bị từ chối *Món đang hết nguyên liệu.* dù đã giữ đủ | Lỗi TC-INV-09, ưu tiên 1 trên slide 13 |
| Giảm suất món đã giữ hết phần còn lại (ở SAI 1: giảm từ 2 xuống 1) | Bị từ chối *Món đang hết nguyên liệu.* | Cùng lỗi với TC-INV-09. Cách xử lý: Hủy lượt chọn rồi chọn lại |
| Đăng nhập sai để minh họa | Thông báo chung chung, không nói sai mật khẩu | API trả đúng thông báo, giao diện cần hiển thị lại |
| Giải phóng bàn khi chưa thanh toán | Được phép, bàn về Trống | Đúng đặc tả FR-CAT-18: khách đã rời thì trả bàn, order vẫn được theo dõi riêng |
| Gọi thêm cho order đã rời bàn | API vẫn giữ nguyên liệu | Lỗi TC-SALE-19, ưu tiên 1 trên slide 13 |

**Nếu có lỗi ngoài dự kiến trên sân khấu:**

> Thưa thầy cô, đây là trường hợp ngoài kịch bản. Thông báo trên màn hình là *[đọc thông báo]*. Em xin ghi nhận để kiểm tra sau, và chuyển sang bước tiếp theo.

## 13. Chi tiết công nghệ (để tra, không đọc)

**Thanh toán**

| Hạng mục | Cách làm | Vị trí trong code |
|---|---|---|
| Chọn cổng | `PAYMENT_GATEWAY=simulator` hoặc `sepay`; thiếu cấu hình SePay thì API từ chối khởi động | `core/config.py` |
| Ảnh QR thật | `https://qr.sepay.vn/img` với số tài khoản, ngân hàng, số tiền, nội dung `TT<mã>` | `sales/gateways/sepay.py` |
| QR mô phỏng | Thư viện `segno` tạo ảnh, không chứa dữ liệu ngân hàng | `sales/payments.py` |
| Webhook thật | `POST /api/v1/sales/webhooks/sepay`, header `Authorization: Apikey <khóa>`, so sánh bằng `hmac.compare_digest` | `sales/router.py`, `gateways/sepay.py` |
| Webhook mô phỏng | Chữ ký HMAC-SHA256 của `mã:số tiền` | `gateways/simulator.py` |
| Khớp giao dịch | Tìm `TT<số>` trong mã hoặc nội dung chuyển khoản; chỉ xử lý tiền vào | `gateways/sepay.py`, `handle_sepay_transfer` |
| Chống trùng | Kiểm tra `sepay:<id>`, khóa dòng `FOR UPDATE`, unique index trên mã giao dịch | `sales/payments.py`, `sales/models.py` |
| Bù webhook lỡ | Đọc `/transactions/list` của SePay mỗi 30 giây bằng API token, có lưu mốc đồng bộ; nút Kiểm tra lại | `sync_recent_transfers`, `check_payment` |
| Hết hạn QR | 10 phút; tác vụ nền quét mỗi 60 giây | `QR_LIFETIME`, `main.py` |
| Cập nhật màn hình | Web hỏi trạng thái giao dịch mỗi 3 giây | `payment-panel.tsx` |
| Khi phát triển | ngrok hoặc Cloudflare Tunnel đưa cổng 8000 ra HTTPS công khai | `docs/payment-sepay-setup.md` |

**AI**

| Bước | Công nghệ, cách làm | Vị trí trong code |
|---|---|---|
| 1. Nhận câu hỏi | Lấy vai trò từ phiên đăng nhập, trừ hạn mức theo người dùng và ngày | `ai/router.py`, `ai/runtime.py` |
| 2. Chuẩn hóa | Chuẩn NFC, gọn khoảng trắng, bỏ dấu câu cuối, giữ dấu tiếng Việt | `pipeline/normalize.py` |
| 3. Dựng prompt | Lược đồ đọc từ view của vai trò, ví dụ mẫu, định nghĩa nghiệp vụ, 4 lượt gần nhất | `pipeline/prompt.py` |
| 4. Sinh SQL | Opus 5.5, effort thấp, SDK `anthropic`; prompt cache cho phần cố định | `ai/llm.py`, `pipeline/generator.py` |
| 5. Kiểm duyệt | `sqlglot` phân tích cú pháp MySQL: một câu SELECT, đúng view, chặn hàm nguy hiểm, trần 500 dòng | `ai/guard.py` |
| 6. Thực thi | Tài khoản riêng từng vai trò, `MAX_EXECUTION_TIME` 3 giây | `pipeline/executor.py`, `ai/accounts.py` |
| 7. Biểu đồ | Luật theo hình dạng dữ liệu, không gọi mô hình | `ai/charts.py` |
| 8. Diễn giải | Haiku 5.5 tắt thinking, nhận số tổng do code tính và tối đa 20 dòng; lỗi thì dùng câu dự phòng | `pipeline/interpreter.py` |
| 9. Lưu vết | Lưu câu hỏi, SQL, trạng thái, thời gian theo phiên của người dùng | `ai/service.py` |

Số view theo chủ đề: Quản lý 17, Bếp 8, Thu ngân 6. DDL ở `db/views/`, quyền ở `db/views/grants.sql.template`.

## 14. Nguồn số liệu (để tra khi bị hỏi "số này lấy ở đâu")

| Số liệu | Nguồn | Cách có số |
|---|---|---|
| 223/247, theo module | Slide 10, 11 của nhóm. **Trong repo chưa có log gốc của lượt 03–04/11** | Thực thi 247 ca của tài liệu 06 |
| Danh sách 267 mã ca | `docs/Tai_lieu/06_Tai_lieu_kiem_thu_va_ket_qua.md` | 247 ca chức năng + 20 ca AT |
| 5 ca chạy lại ngày 06/11 | `docs/testing/artifacts/2026-11-06-fix-demo-blockers/ket-qua-chay-lai.md` | Gọi API trên bản sao MySQL |
| 771 + 200 test, MySQL 18/18 | Cùng tệp trên | `make gate`, `pytest -m integration` |
| p95 356/427/767/30 ms (04/11) | Slide 10 và ghi chú: máy i7-11850H, MySQL 8.4.13. **Trong repo chưa có log gốc** | Tạo tải 1 phút khởi động + 5 phút đo, 1 lần. Kịch bản ở mục 9 lấy theo đợt 27/10, **cần nhóm xác nhận lượt 04/11 dùng cùng script** |
| 20 lỗi ở 20 người (27/10) | `docs/testing/performance-2026-10-27.md`, log tại `docs/testing/artifacts/2026-10-27-perf/` | `scripts/load_business.py`, `load_reports.py`, `verify_perf.py`; 2 + 10 phút, 3 lần |
| Nguyên nhân và cách sửa lỗi kết nối | Commit `09a9cc5` | Tách nhóm kết nối cho bộ đếm mã order |
| 84,58%, 70,42%, 66,67%, 6,73 s, 13,75% | Báo cáo mục 6.4, tài liệu 06 | `data/eval/harness.py`, ngày 27/10 |
| Bộ 80 câu | `data/eval/questions.locked.jsonl`, `questions.locked.manifest.json` | Khóa 27/10 bằng SHA256 |
| 83/90 | Báo cáo mục 6.5, `data/eval/questions.safety.jsonl` | 30 tình huống × 3 lần × 3 cấu hình = 270 lượt |
| Thử an toàn ngày 06/11 | `docs/testing/artifacts/2026-11-06-fix-demo-blockers/thu-an-toan-ai.md` | Thử nhanh, không phải kết quả chính thức |
