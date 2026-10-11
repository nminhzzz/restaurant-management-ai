# Document Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Đồng bộ hướng dẫn repo với báo cáo mới và sửa link hình hỏng trên filesystem phân biệt chữ hoa/thường.

**Architecture:** Chỉ cập nhật AGENTS.md và đường dẫn Markdown trong báo cáo. Quy tắc Business Date mô tả giờ cấu hình có hiệu lực nhưng vẫn yêu cầu mọi phép tính qua helper; đường dẫn ảnh dùng Images/ đúng với tên thư mục thực tế. Không sửa apps/web/AGENTS.md do Next.js sinh.

**Tech Stack:** Markdown, Git, Linux case-sensitive filesystem.

**Spec:** ../specs/2026-10-11-align-code-with-report-design.md, nguyên tắc nguồn yêu cầu và mục 1.

## Global Constraints

- Tài liệu/ngôn ngữ học thuật bằng tiếng Việt.
- MySQL 8.4 và định danh CSDL tiếng Việt tiếp tục là chuẩn.
- Không sửa apps/web/AGENTS.md.
- Ảnh nằm trong docs/Images; report ở docs/ nên dùng đường dẫn tương đối `Images/image_N.png`.

---

### Task 1: Đồng bộ Business Date rule

**Files:**
- Modify: AGENTS.md
- Create: apps/api/tests/schema/test_document_contract.py
- Reference: docs/BaoCao_HeThongQuanLyNhaHang.md, FR-SET-04 và bảng 17
- Reference: root AGENTS.md, which currently says the 06:00 start is fixed.

- [ ] Step 1: Thêm test hợp đồng tài liệu kiểm tra AGENTS yêu cầu tính Business Date qua app.shared.business_date, lấy mốc hiệu lực từ cấu hình và report có các cột giờ mới/ngày hiệu lực; xác nhận toàn bộ link ảnh Markdown trong report tồn tại theo filesystem.
- [ ] Step 2: Chạy cd apps/api && uv run pytest tests/schema/test_document_contract.py -q; Expected: FAIL vì hướng dẫn hiện nói cố định 06:00.
- [ ] Step 3: Sửa AGENTS.md: mốc giờ lấy từ cấu hình có hiệu lực, giờ mới áp dụng từ Business Date kế tiếp, mọi phép tính qua helper dùng chung.
- [ ] Step 4: Chạy lại test hợp đồng; Expected: PASS.

### Task 2: Sửa 22 đường dẫn ảnh

**Files:**
- Modify: docs/BaoCao_HeThongQuanLyNhaHang.md
- Test: apps/api/tests/schema/test_document_contract.py

- [ ] Step 1: Thêm validator đọc các Markdown image link và xác nhận file tồn tại tương đối với docs/.
- [ ] Step 2: Chạy cd apps/api && uv run pytest tests/schema/test_document_contract.py -q; Expected: FAIL trên prefix images/ hiện tại.
- [ ] Step 3: Đổi prefix trong 22 tham chiếu từ images/ sang Images/; không đổi tên file ảnh.
- [ ] Step 4: Chạy `cd apps/api && uv run pytest tests/schema/test_document_contract.py -q` và `git diff --check`; Expected: PASS, mọi link trỏ tới `docs/Images/image_1.png` … `docs/Images/image_22.png`.
