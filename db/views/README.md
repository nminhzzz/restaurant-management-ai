# View phân quyền cho trợ lý AI

NFR-06 và NFR-12: trợ lý AI không bao giờ đọc trực tiếp bảng nghiệp vụ lõi. Mỗi vai trò có đúng
một view chỉ-đọc **và một tài khoản CSDL chỉ-đọc riêng**, tài khoản đó chỉ được `GRANT SELECT`
trên đúng view của vai trò mình — không dùng chung một tài khoản chỉ-đọc cho cả ba vai trò.

| Vai trò | View | Được đọc | Bị loại |
| --- | --- | --- | --- |
| Chủ nhà hàng/Quản lý | `vw_ai_quanly` | toàn bộ nhóm bảng nghiệp vụ | — |
| Thu ngân/NV order | `vw_ai_thungan` | `ORDER`, `CHI_TIET_ORDER`, `HOA_DON`, `GIAO_DICH_THANH_TOAN`, `MON_AN`, `BAN` | toàn bộ nhóm bảng kho, giá vốn, lợi nhuận |
| Nhân viên kho | `vw_ai_kho` | `NGUYEN_LIEU`, `LO_NGUYEN_LIEU`, `PHIEU_NHAP_KHO`, `PHIEU_XUAT_KHO`, `PHIEU_KIEM_KE`, `GIAO_DICH_KHO` | `HOA_DON`, `GIAO_DICH_THANH_TOAN`, `GIA_BINH_QUAN_THANG`, cột `GiaVonUocTinh` |

Tên view viết **chữ thường** (`vw_ai_*`) ở tầng CSDL và trong mã nguồn; ký hiệu `VW_AI_*` trong
báo cáo là cùng đối tượng được viết hoa theo quy ước tài liệu. MySQL trên Linux phân biệt
hoa/thường tên bảng/view (`lower_case_table_names=0`), nên DDL phải tạo đúng chữ thường để khớp
`apps/api/src/app/modules/ai/scope.py` và bộ dữ liệu đánh giá.

## Trạng thái

Thư mục này hiện chỉ ghi lại **hợp đồng** của ba view. Câu lệnh `CREATE VIEW` sẽ được thêm cùng
lúc với DDL bảng nghiệp vụ, vì view không thể tạo trước khi bảng nguồn tồn tại.

Ánh xạ vai trò → view ở tầng ứng dụng nằm tại `apps/api/src/app/modules/ai/scope.py`; mọi câu SQL
sinh ra đều bị chặn nếu tham chiếu bất kỳ quan hệ nào ngoài view tương ứng
(`apps/api/src/app/modules/ai/guard.py`).

## Việc cần làm khi có DDL

1. Tạo ba view theo bảng trên, giữ nguyên tên cột tiếng Việt của bảng gốc.
2. Tạo ba tài khoản CSDL chỉ-đọc (một cho mỗi vai trò) và `GRANT SELECT` trên đúng view tương ứng.
   Ánh xạ vai trò → tài khoản nằm tại `apps/api/src/app/modules/ai/accounts.py`.
3. Thêm test khẳng định mỗi view chỉ chứa các bảng thuộc phạm vi vai trò của nó.
