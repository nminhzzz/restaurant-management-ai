# TRƯỜNG ĐẠI HỌC MỞ HÀ NỘI

KHOA CÔNG NGHỆ THÔNG TIN

HỆ THỐNG QUẢN LÝ NHÀ HÀNG TÍCH HỢP AI HỖ TRỢ HOẠT ĐỘNG KINH DOANH

Ngành: Công nghệ thông tin

ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC

Hà Nội – Năm 2026

## DANH MỤC TỪ VIẾT TẮT

## CHƯƠNG 1: KHẢO SÁT HỆ THỐNG

### 1.1. Giới thiệu chung

Đề tài xây dựng hệ thống quản lý nhà hàng dạng ứng dụng web, tích hợp khối AI Assistant hỗ trợ hỏi đáp và phân tích dữ liệu kinh doanh bằng ngôn ngữ tự nhiên tiếng Việt. Tài liệu đặc tả yêu cầu chức năng (Feature List) làm cơ sở để đội phát triển (Dev, QA, Design) thống nhất phạm vi xây dựng sản phẩm và để giảng viên hướng dẫn xác nhận yêu cầu trước khi triển khai.

### 1.2. Mục đích đề tài

Ngành F&B tại Việt Nam có số lượng nhà hàng, quán ăn quy mô vừa và nhỏ chiếm tỷ trọng chủ yếu, nguồn lực công nghệ hạn chế: chủ quán ra quyết định chủ yếu dựa kinh nghiệm cá nhân, bố trí nhân sự/nguyên liệu chưa bám sát khung giờ cao điểm do thiếu số liệu phân bố đơn hàng theo giờ/theo ngày; phần mềm POS hiện có chỉ hiển thị số liệu thô dưới dạng bảng biểu cố định, khiến người dùng bỏ lỡ cơ hội tối ưu doanh thu và phải tự tổng hợp thủ công khi cần phân tích sâu.

Đề tài hướng tới nghiên cứu, thiết kế và xây dựng hệ thống quản lý nhà hàng tích hợp AI, giải quyết đồng thời bài toán vận hành nghiệp vụ và khai thác dữ liệu kinh doanh bằng tiếng Việt, giúp chủ nhà hàng/người quản lý không cần kiến thức kỹ thuật vẫn đặt được câu hỏi tự nhiên và nhận câu trả lời kèm biểu đồ, đánh giá trên bộ dữ liệu mô phỏng sát thực tế.

### 1.3. Mục tiêu đề tài

#### 1.3.1. Mục tiêu tổng quát

Xây dựng một hệ thống quản lý nhà hàng dạng web phục vụ một nhà hàng/quán ăn đơn lẻ, hỗ trợ đầy đủ vòng nghiệp vụ từ quản lý danh mục, bán hàng, kho, báo cáo thống kê đến cấu hình hệ thống, có tích hợp trợ lý AI hỗ trợ tra cứu và phân tích dữ liệu kinh doanh bằng tiếng Việt.

#### 1.3.2. Mục tiêu cụ thể

- MT1: Tham khảo ý kiến người có kinh nghiệm nhà hàng để đặc tả yêu cầu; thiết kế kiến trúc hệ thống và lược đồ cơ sở dữ liệu chuẩn hóa, phục vụ cả khối nghiệp vụ và AI Assistant.
- MT2: Xây dựng hoàn chỉnh 05 module nghiệp vụ cốt lõi (MVP): Quản lý danh mục, Quản lý bán hàng, Quản lý kho, Báo cáo thống kê, Cài đặt hệ thống.
- MT3: Xây dựng khối AI Assistant ứng dụng LLM kết hợp Text-to-SQL cho hỏi đáp, phân tích dữ liệu kinh doanh bằng tiếng Việt.
- MT4: Xây dựng bộ dữ liệu đánh giá 50–100 cặp câu hỏi tiếng Việt – SQL chuẩn, phân tầng ba mức độ khó.
- MT5: Đạt độ chính xác thực thi tối thiểu 80% (câu hỏi đơn giản/trung bình) và 55% (câu hỏi phức tạp), thời gian phản hồi trung bình dưới 8 giây/câu hỏi.
### 1.4. Phạm vi đề tài

#### 1.4.1. Phạm vi nghiệp vụ

Hệ thống phục vụ một nhà hàng/quán ăn đơn lẻ (chưa mở rộng đa chi nhánh), dành cho 3 vai trò người dùng: Chủ nhà hàng/Quản lý, Thu ngân/Nhân viên order, Nhân viên kho. Phạm vi tài liệu bao gồm các nhóm chức năng chính sau:

- Quản lý danh mục: món ăn, công thức chế biến, nguyên liệu, nhà cung cấp, bàn.
- Quản lý bán hàng: order (kèm ghi chú/yêu cầu riêng cho từng món), in phiếu bếp (kể cả in lại khi lỗi), tra cứu order, thanh toán, hóa đơn.
- Quản lý kho: nhập/xuất kho, tồn kho.
- Báo cáo thống kê: doanh thu, món bán chạy/ít bán, chi phí nguyên liệu và biên lợi nhuận gộp, phân tích theo các kỳ (Business Date, tuần, tháng, năm) và theo khung giờ cao điểm.
- Cài đặt hệ thống: tài khoản, phân quyền, cấu hình hệ thống.
- AI Assistant: hỏi đáp và phân tích dữ liệu kinh doanh bằng tiếng Việt thông qua Text-to-SQL kết hợp LLM.
#### 1.4.2. Phạm vi công nghệ

Hệ thống áp dụng kiến trúc ba tầng, mô hình client-server, backend module hóa theo nghiệp vụ:

- Tầng giao diện: ứng dụng web Next.js (ba vai trò người dùng và giao diện chat AI Assistant).
- Tầng ứng dụng: backend Python/FastAPI xử lý cả nghiệp vụ quản lý và dịch vụ AI Assistant.
- Tầng dữ liệu: PostgreSQL kèm tập view riêng theo vai trò để kiểm soát phân quyền, tách biệt AI Assistant khỏi nghiệp vụ lõi.
- SQL do LLM sinh ra được kiểm duyệt bằng sqlglot trước khi thực thi.
- Phương án chính dùng LLM thương mại qua API (GPT-4o-mini/Gemini Flash); phương án dự phòng dùng mô hình nguồn mở tại chỗ (Qwen2.5-Coder/Llama 3.1 qua Ollama).
Nhóm dự kiến xây dựng ba nhóm biểu đồ thiết kế chính: Use Case theo từng vai trò, ERD mô tả cấu trúc dữ liệu, và DFD (mức 0 và mức 1) cho các module, đặc biệt quy trình xử lý của AI Assistant.

#### 1.4.3. Giới hạn của đề tài

Các nội dung sau nằm ngoài phạm vi của đề tài:

- Quản lý nhân sự và tiền lương.
- Quản lý quan hệ khách hàng (CRM).
- Chương trình khuyến mãi/giảm giá.
- Tách/gộp hóa đơn.
- Quản lý sức chứa theo bàn.
- Tích hợp với các nền tảng giao đồ ăn trực tuyến.
- Tích hợp thanh toán bằng thẻ (quẹt thẻ).
- Triển khai đa chi nhánh.
- Thuế VAT tách dòng trên hóa đơn (giá bán niêm yết đã bao gồm mọi loại thuế/phí; quán tự cân đối nghĩa vụ thuế ngoài hệ thống).
- Phân ca làm việc / mở ca / chốt ca.
- Vai trò/tài khoản riêng cho vị trí Bếp trong phần mềm: bếp làm việc hoàn toàn qua phiếu giấy in tự động (FR-SALE-26); Kitchen Display System (KDS) được thay thế bằng máy in nhiệt in phiếu bếp tại chỗ.
- Chi tiết kỹ thuật tích hợp máy in nhiệt tại bếp (driver máy in, khổ giấy, giao thức kết nối phần cứng).
- Chi tiết kỹ thuật tích hợp cổng thanh toán, cơ chế khóa/transaction xử lý tranh chấp tồn kho đồng thời, và vận hành mô hình LLM/hạ tầng suy luận.
### 1.5. Phân công thực hiện

Đề tài đăng ký thực hiện theo nhóm gồm ba thành viên: Lê Nam Khánh, Nguyễn Mạnh Hùng và Lê Nho Minh (GVHD: ThS. Trịnh Thị Xuân). Công việc cụ thể được phân công như sau:

### 1.6. Phân tích đối thủ cạnh tranh

#### 1.6.1. Khảo sát và đánh giá chung

Các nhận định về sản phẩm thương mại được ghi nhận tại thời điểm khảo sát tháng 8/2026 và sẽ được rà soát lại trước khi bảo vệ. Các sản phẩm thương mại hiện có đã giải quyết tốt bài toán vận hành cơ bản (lập order, in hóa đơn, quản lý bàn/kho, xuất báo cáo doanh thu); phần phân tích dữ liệu chủ yếu ở dạng bảng biểu/biểu đồ theo mẫu định sẵn, chưa hỗ trợ đặt câu hỏi trực tiếp bằng ngôn ngữ tự nhiên trên dữ liệu vận hành — đây là khoảng trống mà đề tài hướng tới giải quyết.

#### 1.6.2. Phân tích chi tiết các đối thủ

Nghiên cứu Text-to-SQL ứng dụng LLM (bổ sung ngoài mẫu bảng — tham khảo)

Spider (Yu và cộng sự) là bộ dữ liệu chuẩn quy mô lớn cho Text-to-SQL đa lĩnh vực; BIRD (Li và cộng sự) xây dựng trên dữ liệu lớn, có yếu tố tri thức nghiệp vụ, phản ánh sát hơn độ khó triển khai thực tế. DIN-SQL (Pourreza và Rafiei) phân rã câu hỏi phức tạp thành các bước nhỏ kèm tự sửa lỗi; các khảo sát khác cho thấy thiết kế prompt quyết định chất lượng SQL sinh ra không kém việc chọn mô hình. Các công trình này đều xây dựng và đánh giá trên tiếng Anh với lược đồ tổng quát; chưa thấy nghiên cứu nào đánh giá riêng cho câu hỏi tiếng Việt trên lược đồ nghiệp vụ nhà hàng.

#### 1.6.3. Đề xuất giải pháp và định hướng phát triển

Dựa trên kết quả khảo sát và phân tích đối thủ, nhóm đề xuất giải pháp phát triển hệ thống theo hướng:

- Xây dựng đầy đủ khối nghiệp vụ vận hành nhà hàng (danh mục, bán hàng, kho, báo cáo, cài đặt) tương đương các sản phẩm thương mại hiện có.
- Bổ sung khối AI Assistant dùng Text-to-SQL kết hợp LLM để hỏi đáp, phân tích dữ liệu kinh doanh bằng tiếng Việt tự nhiên — tính năng mà các đối thủ khảo sát chưa hỗ trợ.
- Xây dựng bộ dữ liệu đánh giá Text-to-SQL tiếng Việt cho nghiệp vụ nhà hàng làm đóng góp khoa học, đồng thời là căn cứ đo lường chất lượng AI Assistant trước khi triển khai thực tế.
### 1.7. Khảo sát người dùng

#### 1.7.1. Mục đích khảo sát

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

#### 1.7.2. Phương pháp khảo sát

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

#### 1.7.3. Câu hỏi khảo sát

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

#### 1.7.4. Kết quả và phân tích kết quả khảo sát

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

### 1.8. Quy trình nghiệp vụ

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

### 1.9. Xác định yêu cầu

#### 1.9.1. Yêu cầu chức năng

Hệ thống gồm 6 module chức năng chính:

Danh mục yêu cầu chức năng chi tiết (FR) theo từng module được trình bày đầy đủ tại mục 2.3 — Đặc tả chức năng.

#### 1.9.2. Yêu cầu phi chức năng

NFR-01 — Thời gian phản hồi thao tác nghiệp vụ: Các thao tác nghiệp vụ chính (submit order, thêm/sửa món, thanh toán, cập nhật tồn kho) phản hồi trong vòng dưới 2 giây trong điều kiện tải bình thường (tối đa khoảng 20 phiên đăng nhập đồng thời).

NFR-02 — Thời gian phản hồi AI Assistant: AI Assistant phản hồi một câu hỏi trong vòng dưới 8 giây, bao gồm toàn bộ chuỗi xử lý: chuẩn hóa câu hỏi, sinh SQL, kiểm duyệt, thực thi và diễn giải kết quả.

NFR-03 — Chịu tải dữ liệu báo cáo: Module Báo cáo thống kê tổng hợp dữ liệu tối thiểu 12 tháng vận hành (ước tính 15.000–20.000 đơn hàng) mà không suy giảm đáng kể thời gian tải trang.

NFR-04 — Mã hóa mật khẩu: Mật khẩu tài khoản người dùng được lưu trữ dưới dạng băm (hash), không lưu ở dạng plaintext.

NFR-05 — Kiểm soát phân quyền ở tầng backend: Phân quyền truy cập dữ liệu và chức năng theo vai trò được kiểm soát ở tầng backend/API, không chỉ ẩn/hiện thành phần giao diện ở tầng frontend.

NFR-06 — Giới hạn quyền của AI Assistant: AI Assistant chỉ được cấp tài khoản CSDL chỉ đọc (read-only) trên tập view riêng biệt theo từng vai trò; không có quyền ghi (INSERT/UPDATE/DELETE) ở bất kỳ cấp độ nào.

NFR-07 — Nhật ký không thể chỉnh sửa: Toàn bộ bản ghi audit log và nhật ký câu hỏi/SQL của AI Assistant không thể chỉnh sửa hoặc xóa bởi tài khoản người dùng thường.

NFR-08 — Nhất quán dữ liệu khi tranh chấp tồn kho: Hệ thống đảm bảo tính nhất quán dữ liệu tồn kho khi có nhiều thao tác đồng thời tranh chấp cùng một nguyên liệu, theo nguyên tắc submit trước được trước.

NFR-09 — Điểm khôi phục dữ liệu sao lưu: Dữ liệu sao lưu có thể phục hồi về trạng thái gần nhất trước sự cố, RPO không quá 24 giờ đối với hình thức sao lưu thủ công.

NFR-10 — Toàn vẹn giao dịch: Mỗi giao dịch bán hàng, nhập/xuất kho đã ghi nhận không bị mất hoặc ghi nhận một phần khi hệ thống gặp sự cố giữa chừng (atomic).

NFR-11 — Kiến trúc dễ mở rộng vai trò/module: Kiến trúc hệ thống cho phép mở rộng thêm vai trò người dùng hoặc module nghiệp vụ mà không phải thiết kế lại toàn bộ lược đồ dữ liệu.

NFR-12 — Tách biệt tập view AI Assistant: Tập view riêng cho AI Assistant, phân tách theo từng vai trò, tách biệt khỏi bảng nghiệp vụ lõi.

NFR-13 — Tối ưu thao tác trên tablet: Giao diện nhập order/thanh toán tối ưu cho thao tác nhanh trên thiết bị màn hình cảm ứng (tablet), phù hợp giờ cao điểm.

NFR-14 — Ngôn ngữ hiển thị: Toàn bộ thông báo, cảnh báo hệ thống và câu trả lời của AI Assistant hiển thị bằng tiếng Việt.

NFR-15 — Ghi log lỗi hệ thống: Hệ thống ghi log lỗi ở tầng backend đủ chi tiết (thời điểm, thao tác, dữ liệu đầu vào liên quan) để phục vụ điều tra sự cố sau khi xảy ra.

NFR-16 — Kiểm soát chi phí gọi API LLM: Chi phí gọi API mô hình ngôn ngữ (LLM) của AI Assistant được giới hạn bằng hạn mức số câu hỏi mỗi ngày và cơ chế cache kết quả cho câu hỏi lặp lại.

NFR-17 — Tương thích trình duyệt/thiết bị: Giao diện web hoạt động ổn định trên các trình duyệt phổ biến hiện hành (Chrome, Edge, Safari) trên cả máy tính và máy tính bảng.

### 1.10. Xác định đối tượng sử dụng hệ thống

## CHƯƠNG 2: PHÂN TÍCH HỆ THỐNG

### 2.1. Mô hình hóa chức năng nghiệp vụ

#### 2.1.1. Xác định và gom nhóm chức năng

Các chức năng nghiệp vụ được gom thành 6 nhóm (module), tương ứng với bảng tổng quan chức năng tại mục 1.9.1:

#### 2.1.2. Sơ đồ phân rã chức năng (BFD)

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

### 2.2. Mô hình hóa tiến trình nghiệp vụ

#### 2.2.1. Ký hiệu sử dụng

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

#### 2.2.2. Sơ đồ luồng dữ liệu (DFD) mức ngữ cảnh

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

#### 2.2.3. DFD mức đỉnh (DFD1)

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

#### 2.2.4. DFD mức dưới đỉnh (DFD2)

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

### 2.3. Đặc tả chức năng

#### 2.3.1. Module 1 — Quản lý danh mục

Nguyên tắc xóa chung (áp dụng cho toàn bộ Module 1): mọi thao tác "xóa" trong Module Quản lý danh mục (nhóm món, món ăn, nguyên liệu, nhà cung cấp, bàn) đều là xóa mềm (soft delete) nếu đối tượng đã từng được dữ liệu vận hành/lịch sử tham chiếu (order, phiếu nhập kho, công thức chế biến, báo cáo). Đối tượng bị xóa mềm không còn xuất hiện ở các màn hình vận hành/lựa chọn mới nhưng vẫn giữ trong cơ sở dữ liệu để đảm bảo toàn vẹn dữ liệu lịch sử. Đối tượng chưa từng được tham chiếu bởi dữ liệu nào thì được xóa vĩnh viễn.

FR-CAT-01 — Quản lý nhóm món: Quản lý được thêm, sửa, xóa, sắp xếp danh sách nhóm món, làm cơ sở phân loại món ăn.

FR-CAT-02 — Quản lý món ăn: Quản lý được thêm, sửa, xóa, tìm kiếm món ăn với các thuộc tính: tên, giá bán, nhóm món (mỗi món chọn đúng một nhóm), hình ảnh.

FR-CAT-03 — Điều kiện xóa nhóm món: Một nhóm món còn ít nhất một món ăn chưa xóa mềm thì không cho xóa nhóm; nhóm chỉ xóa được khi toàn bộ món từng thuộc nhóm đã ở trạng thái xóa mềm. Nhóm chưa từng có món nào được xóa vĩnh viễn.

FR-CAT-04 — Xóa món ăn là xóa mềm: Món vẫn được lưu và hiển thị trong danh mục quản trị (tra cứu, báo cáo, lịch sử order cũ) nhưng biến mất khỏi các màn hình vận hành; không có chức năng xóa vĩnh viễn (hard delete) món ăn.

FR-CAT-05 — Xử lý thay đổi đang chờ khi xóa mềm món: Nếu món bị xóa mềm trong khi đang có thay đổi giá/công thức 'chờ áp dụng', hệ thống tự động hủy thay đổi đang chờ đó.

FR-CAT-06 — Trạng thái mặc định của món mới tạo: Món ăn mới tạo mặc định ở trạng thái 'Nháp — chưa cấu hình công thức' (chưa hiển thị ở màn hình gọi món), cho đến khi được gán công thức chế biến lần đầu.

FR-CAT-07 — Gán công thức chế biến: Mỗi món ăn gắn với một công thức chế biến, gồm danh sách nguyên liệu và định lượng tương ứng theo đúng đơn vị tính.

FR-CAT-08 — Lên lịch áp dụng thay đổi công thức theo Business Date: Quản lý chọn một Business Date cụ thể để áp dụng hiệu lực thay đổi công thức (mặc định đề xuất Business Date kế tiếp); có hiệu lực từ đúng 06:00 ngày áp dụng, cho order tạo từ thời điểm đó trở đi; hệ thống lưu lịch sử các phiên bản công thức.

FR-CAT-09 — Giới hạn một thay đổi công thức đang chờ áp dụng: Mỗi món ăn chỉ có tối đa một thay đổi công thức 'chờ áp dụng' tại một thời điểm; thay đổi mới ghi đè thay đổi cũ.

FR-CAT-10 — Hủy thay đổi công thức đang chờ áp dụng: Quản lý có thể hủy một thay đổi công thức đang 'chờ áp dụng' trước khi có hiệu lực.

FR-CAT-11 — Chuyển trạng thái món khi được gán công thức lần đầu: Ngay khi được gán công thức lần đầu, món tự động chuyển từ 'Nháp' sang 'Hoạt động' hoặc 'Hết nguyên liệu' theo tồn kho hiện có.

FR-CAT-12 — Quản lý nguyên liệu: Người dùng thêm/sửa/xóa/tìm kiếm nguyên liệu: tên, đơn vị tính, mức tồn tối thiểu.

FR-CAT-13 — Xóa nguyên liệu theo nguyên tắc xóa mềm: Nguyên liệu đã có trong công thức chế biến hoặc phiếu nhập kho lịch sử chỉ được xóa mềm.

FR-CAT-14 — Khóa sửa đơn vị tính sau khi đã tham chiếu: Một khi nguyên liệu đã có phiếu nhập kho hoặc dùng trong công thức, hệ thống khóa không cho sửa đơn vị tính nữa.

FR-CAT-15 — Quản lý nhà cung cấp: Người dùng quản lý danh sách nhà cung cấp: thông tin liên hệ, lịch sử nhập hàng.

FR-CAT-16 — Xóa nhà cung cấp theo nguyên tắc xóa mềm: Nhà cung cấp đã có lịch sử nhập hàng chỉ được xóa mềm.

FR-CAT-17 — Quản lý sơ đồ bàn: Người dùng quản lý sơ đồ bàn: thêm/sửa/xóa bàn, xem trạng thái Trống/Đang phục vụ.

FR-CAT-18 — Chuyển trạng thái bàn tự động: Bàn chuyển sang Đang phục vụ khi order được tạo; tự động về Trống khi order thanh toán thành công hoặc khi đổi bàn (bàn nguồn).

FR-CAT-19 — Điều kiện xóa bàn: Không cho xóa bàn đang Đang phục vụ. Bàn đã từng gắn với order lịch sử chỉ được xóa mềm.

FR-CAT-20 — Cập nhật giá bán và lên lịch theo Business Date: Cập nhật giá bán, chọn Business Date áp dụng (mặc định kế tiếp); có hiệu lực từ 06:00 Business Date đó, không ảnh hưởng order đang mở trước đó.

FR-CAT-21 — Giới hạn một thay đổi giá đang chờ áp dụng: Tối đa một thay đổi giá 'chờ áp dụng' cho mỗi món tại một thời điểm; thay đổi mới ghi đè.

FR-CAT-22 — Hủy thay đổi giá đang chờ áp dụng: Quản lý có thể hủy thay đổi giá 'chờ áp dụng' trước khi có hiệu lực.

FR-CAT-23 — Sửa trực tiếp giá bán/công thức đang áp dụng: Quản lý có thể sửa trực tiếp giá/công thức hiện tại, áp dụng ngay, dành cho khắc phục gấp sai sót đã tồn tại; ghi vào audit log (FR-SET-08).

FR-CAT-24 — Không ảnh hưởng đến thay đổi đang chờ áp dụng theo lịch: Sửa trực tiếp và lên lịch theo Business Date là hai cơ chế độc lập; sửa trực tiếp không hủy/ghi đè thay đổi đang chờ theo lịch.

FR-CAT-25 — Ghi nhận phiên bản khi sửa trực tiếp: Mỗi lần sửa trực tiếp được ghi thành một phiên bản mới trong lịch sử giá/công thức, hiệu lực đúng thời điểm sửa.

FR-CAT-26 — Ẩn/hiện món thủ công và các trạng thái vận hành: Quản lý ẩn/hiện tạm thời một món khỏi danh sách gọi món (thủ công, độc lập với ẩn tự động theo tồn kho). Trạng thái vận hành: Hoạt động / Hết nguyên liệu.

FR-CAT-27 — Hai nguyên nhân độc lập gây trạng thái Hết nguyên liệu: (2a) tự động do tồn kho không đủ, tự tắt khi kho cập nhật đủ; (2b) Quản lý bật thủ công, chỉ Quản lý tắt được. Món chỉ hiển thị khi cả hai đều tắt.

FR-CAT-28 — Trạng thái xóa độc lập: Xóa món (FR-CAT-04) là trạng thái riêng biệt (xóa mềm), độc lập với Hoạt động/Hết nguyên liệu/Nháp.

#### 2.3.2. Module 2 — Quản lý bán hàng

FR-SALE-01 — Khởi tạo order: Nhân viên order chọn một bàn Trống hoặc đánh dấu đơn mang về, chọn một hoặc nhiều món từ danh sách món Hoạt động, sau đó bấm Submit để chính thức tạo order.

FR-SALE-02 — Ghi chú/yêu cầu đặc biệt cho món: Nhân viên order nhập ghi chú văn bản tự do cho từng món (ví dụ: 'không hành'); ghi chú gắn với từng dòng món, không bắt buộc, in kèm trên phiếu bếp; không ảnh hưởng công thức hay trừ kho.

FR-SALE-03 — Thời điểm ghi nhận order: Order chỉ ghi nhận tại thời điểm bấm Submit; không lưu order rỗng. Khi submit: bàn chuyển Đang phục vụ, kho bắt đầu bị trừ, hệ thống tự động in phiếu bếp.

FR-SALE-04 — Sinh mã order tự động: Hệ thống tự sinh mã order duy nhất theo định dạng Business Date + số thứ tự (VD: ORD-270826-015), giữ nguyên suốt vòng đời order, dùng làm định danh tra cứu.

FR-SALE-05 — Xử lý hết tồn kho ngay trước khi submit: Nếu tồn kho vừa hết trong lúc chọn món, hệ thống từ chối riêng món liên quan, giữ nguyên các món hợp lệ khác.

FR-SALE-06 — Thêm món vào order đang mở: Nhân viên order thêm món mới vào order đang mở (chưa thanh toán); mỗi lần thêm, in bổ sung phiếu bếp.

FR-SALE-07 — Điều kiện sửa/xóa món đã có trong order: Chỉ được sửa số lượng/xóa món khi món đang 'Chờ làm'; từ 'Đã xác nhận xong' trở đi không được sửa/xóa.

FR-SALE-08 — Kiểm tra tồn kho khi thêm/tăng số lượng: Món hết tồn tự động ẩn khỏi danh sách chọn; khi tăng số lượng món đã có, hệ thống kiểm tra tồn khả dụng, từ chối nếu không đủ.

FR-SALE-09 — Gọi thêm món trong bữa ăn: Khách có thể gọi thêm món trong cùng order khi chưa thanh toán.

FR-SALE-10 — Trạng thái xử lý của món: Mỗi món có trạng thái: Chờ làm → Đã xác nhận xong → Đã phục vụ; nhân viên cập nhật dựa trên xác nhận thực tế từ bếp.

FR-SALE-11 — Hủy một món trong order: Chỉ hủy được món đang 'Chờ làm'; mỗi lượt hủy ghi lại người thực hiện, thời điểm, số lượng, lý do (audit log).

FR-SALE-12 — Tự động đóng order khi toàn bộ món bị hủy: Nếu toàn bộ món trong order đã bị hủy, hệ thống tự đóng order: không phát sinh hóa đơn, bàn về Trống, hoàn kho đầy đủ.

FR-SALE-13 — Đổi bàn cho order đang mở: Chuyển order từ bàn hiện tại sang bàn Trống khác, khi order chưa vào luồng thanh toán; bàn đích chuyển Đang phục vụ, bàn nguồn về Trống.

FR-SALE-14 — Chọn phương thức thanh toán: Thu ngân chọn phương thức: tiền mặt, chuyển khoản, hoặc quét mã QR.

FR-SALE-15 — Thanh toán QR: Tạo mã QR động đúng số tiền; order chuyển 'Chờ xác nhận thanh toán' tối đa 10 phút kể từ khi tạo mã (timeout).

FR-SALE-16 — Xác nhận thanh toán qua webhook: Khi cổng xác nhận thành công qua webhook, hệ thống tự động cập nhật 'Thanh toán thành công'.

FR-SALE-17 — Xử lý timeout thanh toán QR: Quá 10 phút chưa xác nhận, mã QR hết hạn; nếu khách có bằng chứng đã thanh toán, thu ngân chuyển order sang 'Đã thanh toán — chờ đối soát'.

FR-SALE-18 — In hóa đơn: In hóa đơn hoàn chỉnh sau khi thanh toán thành công, gồm chi tiết từng món, thành tiền, tổng tiền; không tách dòng thuế VAT.

FR-SALE-19 — Khóa order sau tất toán: Sau khi tất toán (kể cả 'chờ đối soát'), hệ thống khóa hoàn toàn order: không cho sửa món, hủy món, hủy hóa đơn hay thanh toán lại.

FR-SALE-20 — Ghi nhận mốc thời gian giao dịch: Mọi giao dịch bán hàng ghi nhận kèm mốc thời gian chi tiết, làm đầu vào cho Báo cáo và AI Assistant.

FR-SALE-21 — Tra cứu/tìm kiếm order: Tra cứu một order cụ thể theo mã order, bàn, khoảng thời gian (Business Date).

FR-SALE-22 — In lại hóa đơn: In lại (reprint) đúng nguyên nội dung hóa đơn gốc đã chốt; không cho chỉnh sửa khi in lại.

FR-SALE-23 — Hủy toàn bộ order chưa thanh toán: Chỉ Quản lý được hủy toàn bộ order chưa thanh toán (kể cả có món 'Đã xác nhận xong'/'Đã phục vụ'); bắt buộc nhập lý do hủy.

FR-SALE-24 — Ngoại lệ khi đang chờ xác nhận thanh toán QR: Không cho hủy toàn order khi đang 'Chờ xác nhận thanh toán' (đã tạo mã QR), phải hủy mã QR hoặc chờ hết hạn trước.

FR-SALE-25 — Xử lý sau khi hủy toàn bộ order: Không phát sinh hóa đơn, bàn về Trống; chỉ hoàn kho cho món 'Chờ làm'; ghi vào báo cáo 'giá trị order bị hủy'.

FR-SALE-26 — In phiếu bếp tự động: Khi order được submit hoặc thêm món mới, hệ thống gửi lệnh in phiếu bếp qua máy in nhiệt, gồm bàn/mã đơn, danh sách món, số lượng, ghi chú riêng.

FR-SALE-27 — Xử lý khi in phiếu bếp thất bại: Nếu lệnh in thất bại, hệ thống hiển thị cảnh báo lỗi; nhân viên chủ động bấm in lại sau khi khắc phục sự cố máy in, không giới hạn số lần in lại.

#### 2.3.3. Module 3 — Quản lý kho

FR-INV-01 — Ghi nhận phiếu nhập kho theo lô: Nhân viên kho ghi nhận phiếu nhập kho gắn với nhà cung cấp: nguyên liệu, số lượng, đơn giá, ngày nhập, hạn sử dụng, quy đổi theo đúng đơn vị tính chuẩn hóa. Mỗi phiếu nhập tạo một lô hàng (batch) riêng biệt cho nguyên liệu đó, lưu độc lập theo ngày nhập và hạn sử dụng; nguyên liệu nhập ở các thời điểm khác nhau (ví dụ thịt nhập hôm qua và thịt nhập hôm nay) được quản lý như hai lô tách biệt trong CSDL, không gộp chung số lượng vào lô đã tồn tại trước đó dù cùng một loại nguyên liệu.

FR-INV-02 — Điều kiện sửa/hủy phiếu nhập kho: Được sửa/hủy phiếu nhập nếu chưa có giao dịch xuất kho liên quan phát sinh sau đó; nếu đã có, phải điều chỉnh qua kiểm kê định kỳ.

FR-INV-03 — Trừ kho tự động theo công thức và theo lô (FIFO): Khi order submit lần đầu, thêm món mới, hoặc sửa tăng số lượng món, hệ thống tra công thức chế biến của món (FR-CAT-07) để xác định ánh xạ món ăn → nguyên liệu và định lượng cần trừ cho từng nguyên liệu. Với mỗi nguyên liệu, hệ thống trừ theo nguyên tắc Nhập trước – Xuất trước (FIFO): ưu tiên trừ vào lô có ngày nhập sớm nhất (còn hạn sử dụng) cho đến khi lô đó hết mới chuyển sang lô nhập kế tiếp; nếu một món cần trừ vượt số lượng còn lại của lô đang dùng, hệ thống tự động tách trừ tiếp sang lô kế tiếp theo thứ tự ngày nhập.

FR-INV-04 — Hoàn kho khi hủy/giảm số lượng: Khi món bị hủy hoặc sửa giảm số lượng ở trạng thái 'Chờ làm', hệ thống tự động hoàn nguyên liệu vào kho.

FR-INV-05 — Xuất kho thủ công: Nhân viên kho ghi nhận xuất kho thủ công cho hao hụt, hủy hàng, nguyên liệu hỏng.

FR-INV-06 — Chặn xuất kho thủ công âm tồn: Nếu số lượng xuất vượt tồn khả dụng, hệ thống từ chối và yêu cầu đối chiếu/kiểm kê lại.

FR-INV-07 — Cảnh báo tồn tối thiểu: Hệ thống cảnh báo khi tồn của một nguyên liệu xuống dưới mức tồn tối thiểu đã cấu hình.

FR-INV-08 — Kiểm kê định kỳ: Nhân viên kho đối chiếu tồn thực tế với hệ thống, ghi nhận chênh lệch, sau xác nhận hệ thống cập nhật ghi đè lại số lượng tồn hiện tại.

FR-INV-09 — Vai trò bắt buộc trong MVP: Kiểm kê định kỳ là van an toàn duy nhất để điều chỉnh sai lệch tồn kho trước khi cho phép xuất kho thủ công tiếp tục.

FR-INV-10 — Kiểm tra tồn kho khả dụng và tự động ẩn món: Hệ thống kiểm tra tồn khả dụng theo công thức ngay khi tồn kho thay đổi; tự động chuyển món sang 'Tự động ẩn do hết tồn kho' khi không đủ.

FR-INV-11 — Xử lý tranh chấp tồn kho: Khi nhiều thao tác tranh chấp một nguyên liệu, hệ thống kiểm tra lại tồn tại thời điểm submit, xử lý theo nguyên tắc submit trước được trước; không cho tồn kho âm.

FR-INV-12 — Xem danh sách tồn kho: Xem danh sách tồn kho hiện tại: tên, đơn vị tính, số lượng tồn khả dụng, mức tồn tối thiểu, trạng thái; tìm kiếm/lọc theo tên và trạng thái cảnh báo.

FR-INV-13 — Quản lý tồn kho chi tiết theo lô: Tồn kho của mỗi nguyên liệu được lưu và hiển thị chi tiết theo từng lô (ngày nhập, hạn sử dụng, số lượng còn lại, đơn giá nhập), bên cạnh số liệu tổng hợp toàn nguyên liệu tại FR-INV-12; nhân viên kho có thể xem, tìm kiếm, lọc danh sách lô theo nguyên liệu, ngày nhập hoặc hạn sử dụng.

FR-INV-14 — Tự động lập danh sách nguyên liệu hết hạn cuối ngày: Vào cuối mỗi Business Date (06:00), hệ thống tự động quét toàn bộ các lô nguyên liệu còn tồn, xác định những lô có hạn sử dụng đã qua (nhỏ hơn hoặc bằng thời điểm quét) và đưa vào "Danh sách nguyên liệu hết hạn — chờ hủy". Nhân viên kho xác nhận xuất hủy cho từng lô trong danh sách; sau khi xác nhận, hệ thống tự động ghi nhận thành một phiếu xuất kho thủ công loại "hết hạn" (liên kết FR-INV-05) và trừ số lượng lô đó khỏi tồn kho khả dụng.

FR-INV-15 — Xuất báo cáo nguyên liệu hết hạn: Hệ thống cho phép xuất báo cáo danh sách nguyên liệu đã hết hạn/bị hủy trong một khoảng thời gian (Business Date/tuần/tháng), gồm: tên nguyên liệu, lô, ngày nhập, hạn sử dụng, số lượng, giá trị hủy quy đổi theo đơn giá nhập; số liệu này đồng thời được tính vào chi phí hao hụt/hư hỏng/hết hạn của giá vốn nguyên liệu tiêu hao (FR-REP-05).

#### 2.3.4. Module 4 — Báo cáo thống kê

FR-REP-01 — Báo cáo doanh thu: Hiển thị doanh thu theo Business Date/tuần/tháng/năm, theo bàn và theo hình thức thanh toán.

FR-REP-02 — Xử lý giao dịch chờ đối soát trong báo cáo doanh thu: Giao dịch 'chờ đối soát' tính tạm vào doanh thu; nếu sau bị gắn cờ 'tranh chấp thanh toán', hệ thống điều chỉnh trừ lùi khỏi doanh thu thực nhận.

FR-REP-03 — Xếp hạng món ăn: Xếp hạng món bán chạy/ít bán theo số lượng và doanh thu, trong khoảng thời gian lựa chọn.

FR-REP-04 — Biên lợi nhuận gộp: Tính ở mức tổng toàn nhà hàng theo chu kỳ tháng = Doanh thu bán hàng − Giá vốn nguyên liệu tiêu hao.

FR-REP-05 — Cấu thành giá vốn nguyên liệu tiêu hao: Gồm: (a) nguyên liệu theo phiên bản công thức có hiệu lực tại thời điểm order tạo, nhân đơn giá bình quân gia quyền trong tháng; (b) chi phí hao hụt/hư hỏng/hết hạn phải xuất bỏ.

FR-REP-06 — Chi phí nguyên liệu theo món (tham khảo): Hiển thị riêng chi phí nguyên liệu theo từng món (không kèm hao hụt) để tham khảo, không quy thành biên lợi nhuận theo món.

FR-REP-07 — Phân bố đơn hàng theo khung giờ: Hiển thị phân bố số lượng đơn hàng và doanh thu theo khung giờ trong ngày và theo ngày trong tuần.

FR-REP-08 — So sánh hai khoảng thời gian: Cho phép so sánh doanh thu/chi phí giữa hai khoảng thời gian và hiển thị phần trăm chênh lệch.

FR-REP-09 — Hiển thị dạng bảng và biểu đồ: Báo cáo hiển thị dưới dạng bảng biểu và biểu đồ trực quan.

FR-REP-10 — Báo cáo order bị hủy: Hiển thị tổng giá trị và số lượng order bị hủy toàn bộ (kèm lý do), theo Business Date/tuần/tháng, tách biệt khỏi doanh thu.

#### 2.3.5. Module 5 — Cài đặt hệ thống

FR-SET-01 — Quản lý tài khoản: Quản lý tạo/sửa/khóa tài khoản người dùng và gán một trong ba vai trò.

FR-SET-02 — Đăng nhập/đăng xuất/đổi mật khẩu: Người dùng tự đăng nhập/đăng xuất bằng tài khoản được cấp; tự đổi mật khẩu bất kỳ lúc nào; Quản lý đặt lại mật khẩu khi người dùng quên.

FR-SET-03 — Giới hạn theo vai trò: Hệ thống giới hạn phạm vi truy cập chức năng và dữ liệu theo vai trò đã gán.

FR-SET-04 — Cấu hình thông tin chung: Quản lý cấu hình thông tin chung của nhà hàng: tên, địa chỉ, mẫu hóa đơn.

FR-SET-05 — Cấu hình cảnh báo tồn kho: Quản lý cấu hình tham số cảnh báo tồn kho mặc định.

FR-SET-06 — Xuất bản sao dữ liệu thủ công: Hệ thống cung cấp chức năng xuất bản sao dữ liệu thủ công.

FR-SET-07 — Sao lưu tự động (mở rộng): (Mở rộng) Hệ thống tự động sao lưu và phục hồi dữ liệu theo lịch.

FR-SET-08 — Audit log cho thao tác rủi ro cao: Ghi nhật ký cho các thao tác rủi ro cao: hủy toàn bộ order, hủy món, chuyển trạng thái QR sang chờ đối soát, xuất kho thủ công, điều chỉnh qua kiểm kê, thay đổi giá/công thức theo lịch và sửa trực tiếp.

FR-SET-09 — Nội dung tối thiểu và quyền xem nhật ký: Mỗi bản ghi lưu tối thiểu: người thực hiện, thời điểm, loại thao tác, dữ liệu trước/sau; Quản lý xem toàn bộ.

#### 2.3.6. Module 6 — AI Assistant

FR-AI-01 — Trợ lý AI riêng theo vai trò: Mỗi vai trò sử dụng một trợ lý AI (chat) riêng biệt, đặt câu hỏi bằng tiếng Việt trong đúng phạm vi dữ liệu được phép.

FR-AI-02 — Nội dung AI của Quản lý có thể trả lời: Doanh thu, biên lợi nhuận, tồn kho, món bán chạy/ít bán, chi phí và giá nhập nguyên liệu, báo cáo order bị hủy...

FR-AI-03 — Nội dung AI của Thu ngân/Nhân viên order có thể trả lời: Doanh thu, hóa đơn, thông tin bán hàng thuộc phạm vi vai trò; không trả lời giá nhập hàng/lợi nhuận theo món.

FR-AI-04 — Nội dung AI của Nhân viên kho có thể trả lời: Tồn kho hiện tại, nguyên liệu, lịch sử nhập/xuất, cảnh báo tồn tối thiểu; không trả lời doanh thu/hóa đơn/lợi nhuận.

FR-AI-05 — Không truy cập chéo dữ liệu giữa các vai trò: Trợ lý AI của một vai trò không được dùng dữ liệu thuộc vai trò khác, kể cả khi người dùng cố tình hỏi vượt quyền.

FR-AI-06 — Yêu cầu làm rõ khi không xác định được đối tượng: Khi không xác định chính xác món/nguyên liệu/khoảng thời gian, hệ thống yêu cầu người dùng làm rõ hoặc diễn đạt lại.

FR-AI-07 — Hình thức trả lời: Trả lời bằng tiếng Việt, kèm biểu đồ khi cần, luôn kèm bảng số liệu gốc và ghi chú phạm vi dữ liệu đã dùng.

FR-AI-08 — Xem chi tiết kỹ thuật của câu trả lời: Người dùng có thể mở mục 'Xem chi tiết' (thu gọn mặc định) để xem thông tin kỹ thuật, phục vụ kiểm chứng.

FR-AI-09 — Thông báo khi không thể trả lời: Khi không tạo được câu trả lời hợp lệ, hệ thống thông báo và gợi ý diễn đạt lại, không im lặng hoặc trả kết quả sai.

## CHƯƠNG 3: THIẾT KẾ HỆ THỐNG

### 3.1. Thiết kế kiến trúc hệ thống

#### 3.1.1. Kiến trúc tổng thể

Hệ thống áp dụng kiến trúc ba tầng, mô hình client-server, backend module hóa theo nghiệp vụ:

- Tầng giao diện (Presentation): ứng dụng web Next.js, phục vụ ba vai trò người dùng và giao diện chat AI Assistant.
- Tầng ứng dụng (Application): backend Python/FastAPI, xử lý cả nghiệp vụ quản lý (danh mục, bán hàng, kho, báo cáo, cài đặt) và dịch vụ AI Assistant (chuẩn hóa câu hỏi, sinh SQL, kiểm duyệt, thực thi, diễn giải kết quả).
- Tầng dữ liệu (Data): PostgreSQL, kèm tập view riêng theo từng vai trò (Quản lý/Thu ngân/Nhân viên kho) để kiểm soát phân quyền và tách biệt AI Assistant khỏi các bảng nghiệp vụ lõi.
#### 3.1.2. Kiến trúc phần mềm

Câu lệnh SQL do LLM sinh ra được kiểm duyệt bằng thư viện sqlglot trước khi thực thi (chỉ chấp nhận SELECT trên view được phân quyền, thực thi bằng tài khoản chỉ đọc). Phương án chính dùng LLM thương mại qua API (GPT-4o-mini/Gemini Flash); phương án dự phòng dùng mô hình nguồn mở tại chỗ (Qwen2.5-Coder/Llama 3.1 qua Ollama), đồng thời là một cấu hình đối chứng trong thực nghiệm đánh giá. Ba nhóm biểu đồ thiết kế chính dự kiến xây dựng: Use Case theo từng vai trò, ERD mô tả cấu trúc dữ liệu, và DFD (mức 0 và mức 1) cho các module, đặc biệt quy trình xử lý của AI Assistant.

### 3.2. Thiết kế cơ sở dữ liệu

#### 3.2.1. Xác định tập thực thể và thuộc tính

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

#### 3.2.2. Mô hình thực thể liên kết

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

### 3.3. Thiết kế giao diện

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

### 3.4. Thiết kế kiểm soát

#### 3.4.1. Phân định quyền hạn về dữ liệu

Dựa trên FR-SET-03 và NFR-05/NFR-06: phân quyền được kiểm soát ở tầng backend/API theo 3 vai trò (Chủ nhà hàng/Quản lý, Thu ngân/Nhân viên order, Nhân viên kho). Chi tiết ma trận quyền theo dữ liệu cần được thiết kế cụ thể ở giai đoạn thiết kế kỹ thuật.

#### 3.4.2. Phân định quyền hạn về chức năng

[Cần bổ sung — nội dung này không có sẵn trong tài liệu Feature List, cần khảo sát/thiết kế thêm]

#### 3.4.3. Phân định trách nhiệm và thẩm quyền theo từng vai trò

Xem bảng đối tượng sử dụng hệ thống tại mục 1.10.

## CHƯƠNG 4: TRIỂN KHAI XÂY DỰNG CHƯƠNG TRÌNH

### 4.1. Công nghệ sử dụng

#### 4.1.1. Giới thiệu lý do sử dụng (Công nghệ/framework)

- Next.js (frontend): xây dựng giao diện web cho ba vai trò người dùng và giao diện chat AI Assistant.
- Python/FastAPI (backend): xử lý cả nghiệp vụ quản lý và dịch vụ AI Assistant trên cùng một nền tảng, thuận tiện tích hợp các thư viện xử lý LLM/Text-to-SQL của Python.
- sqlglot: kiểm duyệt cú pháp câu lệnh SQL do LLM sinh ra trước khi thực thi, đảm bảo chỉ chấp nhận câu lệnh SELECT.
- LLM: phương án chính dùng mô hình thương mại qua API (GPT-4o-mini/Gemini Flash) cho chất lượng sinh SQL tốt và chi phí hợp lý; phương án dự phòng dùng mô hình nguồn mở tại chỗ (Qwen2.5-Coder/Llama 3.1 qua Ollama) để giảm phụ thuộc bên thứ ba và làm cấu hình đối chứng khi đánh giá.
#### 4.1.2. Giới thiệu lý do sử dụng (Database)

PostgreSQL được lựa chọn làm hệ quản trị cơ sở dữ liệu chính, kèm tập view riêng theo từng vai trò người dùng để kiểm soát phân quyền dữ liệu cho AI Assistant, tách biệt hoàn toàn khỏi các bảng nghiệp vụ lõi — đảm bảo thay đổi cấu trúc bảng nghiệp vụ không làm gián đoạn hoạt động của AI Assistant (NFR-12).

### 4.2. Kết quả thực hiện

Kết quả thực nghiệm dự kiến đo lường trên bộ dữ liệu đánh giá 50–100 cặp câu hỏi tiếng Việt – SQL chuẩn (phân tầng ba mức độ khó), với các chỉ số: độ chính xác thực thi, tỷ lệ SQL lỗi, tỷ lệ từ chối, thời gian phản hồi trung bình. Mục tiêu: độ chính xác thực thi tối thiểu 80% (câu hỏi đơn giản/trung bình) và 55% (câu hỏi phức tạp); thời gian phản hồi dưới 8 giây/câu hỏi. Ba cấu hình đối chứng được thực nghiệm: (A) chỉ dùng lược đồ, (B) bổ sung few-shot và chuẩn hóa tiếng Việt, (C) cấu hình B trên một mô hình khác. Kết quả cụ thể sẽ được cập nhật sau khi hoàn thành thực nghiệm.

## KẾT LUẬN

Đề tài xây dựng hệ thống quản lý nhà hàng tích hợp AI hỗ trợ hoạt động kinh doanh, gồm hai khối: khối nghiệp vụ quản lý truyền thống (danh mục, bán hàng, kho, báo cáo thống kê, cài đặt hệ thống) và khối AI Assistant cho phép người quản lý hỏi đáp, phân tích dữ liệu kinh doanh bằng ngôn ngữ tự nhiên tiếng Việt qua Text-to-SQL kết hợp LLM. Bên cạnh sản phẩm phần mềm, đề tài đóng góp một bộ dữ liệu đánh giá gồm các cặp câu hỏi tiếng Việt – câu lệnh SQL chuẩn cho nghiệp vụ nhà hàng, dùng để đo lường định lượng chất lượng của khối AI Assistant — góp phần lấp khoảng trống hiện chưa có nghiên cứu nào đánh giá Text-to-SQL tiếng Việt trên lược đồ nghiệp vụ nhà hàng.

Kết quả cụ thể về mức độ hoàn thành các module, số liệu thực nghiệm Text-to-SQL và đánh giá định tính (SUS) sẽ được cập nhật khi hoàn thiện triển khai và thực nghiệm.

## TÀI LIỆU THAM KHẢO

[1] T. Yu, R. Zhang, K. Yang, M. Yasunaga, D. Wang, Z. Li, J. Ma, I. Li, Q. Yao, S. Roman, Z. Zhang, and D. Radev, "Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task," in Proc. 2018 Conference on Empirical Methods in Natural Language Processing (EMNLP), Brussels, Belgium, 2018, pp. 3911–3921.

[2] J. Li, B. Hui, G. Qu, J. Yang, B. Li, B. Li, B. Wang, B. Qin, R. Cao, R. Geng, N. Huo, X. Zhou, C. Ma, G. Li, K. C. C. Chang, F. Huang, R. Cheng, and Y. Li, "Can LLM Already Serve as A Database Interface? A Big Bench for Large-Scale Database Grounded Text-to-SQLs," in Advances in Neural Information Processing Systems 36 (NeurIPS 2023), Datasets and Benchmarks Track, 2023.

[3] M. Pourreza and D. Rafiei, "DIN-SQL: Decomposed In-Context Learning of Text-to-SQL with Self-Correction," in Advances in Neural Information Processing Systems 36 (NeurIPS 2023), 2023.

[4] N. Rajkumar, R. Li, and D. Bahdanau, "Evaluating the Text-to-SQL Capabilities of Large Language Models," arXiv preprint arXiv:2204.00498, 2022.

[5] Z. Hong, Z. Yuan, Q. Zhang, H. Chen, J. Dong, F. Huang, and X. Huang, "Next-Generation Database Interfaces: A Survey of LLM-based Text-to-SQL," arXiv preprint arXiv:2406.08426, 2024.

[6] D. Gao, H. Wang, Y. Li, X. Sun, Y. Qian, B. Ding, and J. Zhou, "Text-to-SQL Empowered by Large Language Models: A Benchmark Evaluation," Proceedings of the VLDB Endowment, vol. 17, no. 5, pp. 1132–1145, 2024.

[7] KiotViet, "Phần mềm quản lý nhà hàng, quán ăn." [Trực tuyến]. Địa chỉ: https://www.kiotviet.vn. Truy cập: tháng 8/2026.

[8] MISA CukCuk, "Phần mềm quản lý nhà hàng CukCuk." [Trực tuyến]. Địa chỉ: https://www.cukcuk.vn. Truy cập: tháng 8/2026.

## PHỤ LỤC

Phụ lục 1 — Quy tắc nghiệp vụ chung (Business Rules tổng hợp), trích từ tài liệu Feature List:

- 1. Hệ thống phục vụ một nhà hàng/quán ăn đơn lẻ, chưa hỗ trợ đa chi nhánh.
- 2. Ba vai trò người dùng cố định, mỗi vai trò có phạm vi truy cập dữ liệu riêng.
- 3. Mỗi món ăn thuộc đúng một nhóm món duy nhất.
- 4. Order chỉ được ghi nhận kể từ thời điểm submit; không tồn tại order 0 món ở trạng thái mở. Order chỉ chuyển thành hóa đơn sau khi thanh toán thành công.
- 5. Sau khi thanh toán thành công, order/hóa đơn bị khóa hoàn toàn, chỉ cho phép in lại nguyên trạng; bàn tự động về Trống.
- 6. Không tích hợp thanh toán thẻ ngân hàng; thanh toán QR ở 'Chờ xác nhận thanh toán' cho đến khi webhook xác nhận hoặc timeout chuyển 'chờ đối soát'.
- 7. Không áp dụng khuyến mãi/giảm giá, không in tạm tính; hóa đơn không tách dòng thuế VAT.
- 8. Không hỗ trợ tách/gộp hóa đơn hay gộp bàn; hỗ trợ đổi bàn khi bàn đích đang trống.
- 9. Hệ thống tự động ẩn món khi tồn kho không đủ, hiện lại khi kho cập nhật đủ; nguyên tắc 'submit trước được trước' xử lý tranh chấp tồn kho.
- 10. Trừ kho khi order submit/thêm món/sửa tăng số lượng; hoàn kho khi hủy/sửa giảm ở trạng thái 'Chờ làm'.
- 11. Cảnh báo tồn kho dựa trên mức tồn tối thiểu cấu hình theo từng nguyên liệu.
- 12. Thay đổi giá/công thức có hai cơ chế độc lập: lên lịch theo Business Date, và sửa trực tiếp có hiệu lực ngay.
- 13. Business Date là mốc cố định 06:00–06:00 hôm sau, dùng làm căn cứ hiệu lực giá/công thức và đơn vị nhóm báo cáo theo ngày.
- 14. Biên lợi nhuận gộp = Doanh thu − Giá vốn nguyên liệu tiêu hao, tính theo tháng ở mức tổng toàn nhà hàng.
- 15. AI Assistant: mỗi vai trò có trợ lý AI riêng, chỉ truy cập dữ liệu thuộc phạm vi vai trò, kiểm soát ở tầng backend/data layer.
- 16. Mọi câu trả lời của AI Assistant phải kèm bảng số liệu gốc và chú thích phạm vi dữ liệu.
- 17. Kiểm kê kho định kỳ là chức năng bắt buộc trong MVP.
- 18. Hệ thống hỗ trợ ẩn/hiện món thủ công, tách biệt với chặn tự động theo tồn kho.
- 19. Hóa đơn có thể in lại nguyên trạng sau khi tất toán, không phải hình thức sửa/hủy.
- 20. Nguyên tắc xóa mềm áp dụng thống nhất cho toàn bộ danh mục khi đối tượng đã có dữ liệu lịch sử tham chiếu.
- 21. Quản lý có quyền hủy toàn bộ order chưa thanh toán; nguyên liệu chỉ hoàn kho cho phần món chưa chế biến.
- 22. Bếp không có tài khoản hay giao diện phần mềm riêng; tương tác qua phiếu bếp giấy in tự động.
- 23. Mỗi món trong order có thể kèm ghi chú riêng dạng văn bản tự do, không ảnh hưởng công thức hay trừ kho.
- 24. Người dùng tự đăng nhập/đăng xuất/đổi mật khẩu; khi in phiếu bếp thất bại, nhân viên chủ động in lại sau khi khắc phục sự cố máy in.
- 25. Nguyên liệu được quản lý chi tiết theo lô nhập (mỗi phiếu nhập kho tạo một lô riêng gắn với ngày nhập và hạn sử dụng, không gộp vào lô cũ dù cùng nguyên liệu); trừ kho theo công thức món ăn áp dụng nguyên tắc Nhập trước – Xuất trước (FIFO) giữa các lô. Cuối mỗi Business Date, hệ thống tự động xác định các lô đã hết hạn sử dụng, đưa vào danh sách chờ hủy để nhân viên kho xác nhận xuất hủy, và cho phép xuất báo cáo nguyên liệu hết hạn theo kỳ.

Phụ lục 2 — Các nội dung cần bổ sung thêm (trích từ tài liệu Feature List):

- Vấn đề #1 — Cách xác định 'nguyên liệu sắp hết' cụ thể hơn: cần phỏng vấn thêm để xác định mức tồn tối thiểu hợp lý cho từng nhóm nguyên liệu trước khi cấu hình FR-INV-07.
- Vấn đề #2 — Dữ liệu khảo sát từ các vai trò khác: cần bổ sung khảo sát với thu ngân, phục vụ và nhân viên kho.
- Vấn đề #3 — Giới hạn kỹ thuật cụ thể cho AI Assistant: NFR-06 chưa có con số cụ thể (timeout, LIMIT bản ghi), cần chốt ở giai đoạn thiết kế kỹ thuật.
- Vấn đề #4 — Lựa chọn cổng thanh toán QR cụ thể: FR-SALE-15 chưa chọn nhà cung cấp cổng thanh toán và ai đứng tên tài khoản merchant.
- Vấn đề #5 — Cơ chế kỹ thuật đảm bảo 'submit trước được trước' khi tranh chấp tồn kho: chưa đặc tả ở tài liệu nghiệp vụ, cần chuyển sang tài liệu thiết kế kỹ thuật.
- Vấn đề #6 — Khung giờ 06:00 của Business Date có phù hợp thực tế vận hành không: cần xác nhận lại với chủ quán.

Phụ lục 3 — Dữ liệu thử nghiệm và phương pháp đánh giá (trích từ Đề cương khóa luận):

Dữ liệu thử nghiệm: kết hợp phỏng vấn bán cấu trúc với 3–5 người từng quản lý ca, làm thu ngân hoặc là chủ quán quy mô nhỏ, cùng dữ liệu mô phỏng khoảng 12 tháng, 15.000–20.000 đơn hàng trên 60–80 món, theo các đặc trưng thật của ngành (hai đỉnh trong ngày, cuối tuần cao hơn, mùa vụ, phân bố món theo quy luật lũy thừa).

Bộ dữ liệu đánh giá: 50–100 cặp câu hỏi tiếng Việt – SQL chuẩn, phân tầng ba mức độ khó. Người soạn SQL chuẩn không đồng thời thiết kế prompt; trên một tập con 15–20 câu ngẫu nhiên, cả ba thành viên độc lập soạn SQL để đối chiếu, tính tỷ lệ đồng thuận làm căn cứ đánh giá độ rõ ràng câu hỏi.

Tiêu chí định lượng: độ chính xác thực thi, tỷ lệ SQL lỗi, tỷ lệ từ chối, thời gian phản hồi. Ba cấu hình đối chứng: A (chỉ dùng lược đồ), B (bổ sung few-shot và chuẩn hóa tiếng Việt), C (cấu hình B trên một mô hình khác).

Đánh giá định tính: khảo sát SUS (System Usability Scale) với 3–5 người đóng vai chủ nhà hàng/quản lý, kết hợp phỏng vấn ngắn. Với cỡ mẫu này, kết quả chỉ có giá trị định tính, tham khảo.

Phụ lục 4 — Rủi ro và giải pháp giảm thiểu (trích từ Đề cương khóa luận):

- LLM sinh câu lệnh làm thay đổi dữ liệu: chỉ chấp nhận SELECT đã kiểm tra cú pháp, dùng tài khoản chỉ đọc trên view được chỉ định.
- LLM diễn giải sai lệch kết quả (hallucination): luôn hiển thị kèm bảng số liệu gốc và câu lệnh SQL để người dùng đối chiếu.
- Người dùng truy vấn vượt phân quyền: dùng tập view riêng theo vai trò, ghi nhật ký toàn bộ câu hỏi và SQL đã chạy.
- Dữ liệu bị lộ qua API bên thứ ba: chỉ gửi lược đồ và kết quả tổng hợp, che trường nhạy cảm, dự phòng mô hình nguồn mở tại chỗ.
- Chi phí API vượt dự kiến: đặt hạn mức câu hỏi mỗi ngày, cache kết quả lặp lại, ưu tiên mô hình rẻ cho câu hỏi đơn giản.
- Độ chính xác Text-to-SQL tiếng Việt không đạt ngưỡng: thử nghiệm khả thi sớm (tuần 3–4), dự phòng giới hạn AI Assistant ở tập câu hỏi theo mẫu định sẵn.