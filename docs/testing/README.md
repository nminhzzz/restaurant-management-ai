# Kiểm thử và đánh giá hệ thống

Thư mục này hiện thực MT6 (mục 1.3.2 của `docs/BaoCao_HeThongQuanLyNhaHang.md`): đánh giá chất lượng
hệ thống qua ba phương pháp bổ sung cho nhau. Không phương pháp nào thay thế được phương pháp còn lại —
test case chứng minh từng chức năng hoạt động đúng đặc tả (FR/NFR), SUS đo cảm nhận về khả năng sử dụng,
UAT xác nhận toàn bộ luồng nghiệp vụ đầu-cuối vận hành được trong tay người có kinh nghiệm thật.

## Ba phương pháp và cách chúng khớp nhau

| Phương pháp | Trả lời câu hỏi gì | Ai thực hiện | Tài liệu |
| --- | --- | --- | --- |
| Test case chức năng (bao gồm phân quyền/bảo mật dữ liệu) | Từng FR/NFR có được cài đúng không, kể cả đường lỗi và giới hạn quyền theo vai trò? | Nhóm phát triển (tự động qua CI + thủ công cho phần chưa có test) | `test-cases.md` |
| Khảo sát SUS | Người dùng chưa quen hệ thống cảm thấy dễ dùng đến mức nào? | 3–5 người đóng vai Chủ/Quản lý, sau khi hoàn thành một chuỗi thao tác chuẩn | `sus.md` |
| UAT | Người có kinh nghiệm vận hành nhà hàng thật có chấp nhận hệ thống thay thế quy trình hiện tại không? | Người tham gia phỏng vấn ở Phụ lục 3 (hoặc tương đương), theo kịch bản ca làm việc thật | `uat.md` |

Thứ tự khuyến nghị: chạy xanh toàn bộ test case tự động → hoàn tất test case thủ công còn lại (đặc biệt
nhóm phân quyền và AI data-scope) → mới mời người tham gia SUS/UAT, để không tốn thời gian người ngoài
nhóm vào lỗi mà test tự động lẽ ra đã bắt được.

Checklist tương thích thiết bị/trình duyệt (NFR-13, NFR-17) là điều kiện tiên quyết trước khi mời người
tham gia UAT trên tablet thật — xem `compatibility-checklist.md`.

## Chạy bộ kiểm thử tự động

```bash
make gate       # bắt buộc xanh trước khi kết thúc công việc: fmt-check, lint, typecheck, test, build
make test       # chỉ chạy test (test-api + test-web)
make test-api   # cd apps/api && uv run pytest
make test-web   # cd apps/web && pnpm test
```

Chạy một file/case cụ thể (đối chiếu với cột "Loại" trong `test-cases.md`):

```bash
cd apps/api && uv run pytest tests/modules/test_ai_guard.py -k test_sql_of_another_role_is_rejected
cd apps/web && pnpm test -- payment-panel.test.tsx
```

Dữ liệu mô phỏng phục vụ test thủ công, SUS và UAT được sinh bằng `make seed` (12 tháng, ≥ 20.000 order,
theo NFR-03). Không dùng dữ liệu sản xuất thật cho bất kỳ hoạt động kiểm thử nào.

## Ghi nhận kết quả

- **Test case tự động**: kết quả là output của `make gate`/`make test`; không cần tick tay, chỉ dán số
  lượng pass/fail và ngày chạy vào cột "Kết quả" khi lập báo cáo tổng hợp cho hội đồng.
- **Test case thủ công**: người thực hiện tick trực tiếp vào ô ☐ Đạt / ☐ Không đạt trong `test-cases.md`
  (sao chép bảng ra bản làm việc riêng nếu cần giữ nguyên bản gốc), ghi rõ người thực hiện và ngày.
- **SUS**: mỗi người tham gia điền phiếu riêng theo mẫu ở `sus.md`; kết quả tổng hợp vào bảng điểm, không
  chỉnh sửa câu trả lời gốc sau khi thu.
- **UAT**: dùng bảng sign-off và issue log ở cuối `uat.md`; mọi vấn đề phát sinh trong buổi UAT được ghi
  vào issue log kể cả khi đã được vá ngay tại chỗ.

Toàn bộ kết quả kiểm thử (số liệu pass/fail, phiếu SUS đã điền, issue log UAT) được tổng hợp lại làm căn
cứ cho phần "Kết quả cụ thể" ở cuối báo cáo (mục ghi chú tại dòng liên quan tới MT6 trong
`docs/BaoCao_HeThongQuanLyNhaHang.md`).
