# Lộ trình triển khai — Hệ thống quản lý nhà hàng tích hợp AI

Ngày: 2026-09-24 · Cập nhật: 2026-09-24

## Mục tiêu dự án

Biến repository từ **khung dự án** thành sản phẩm chạy được: sáu module nghiệp vụ đầy đủ theo
FR-CAT/SALE/INV/REP/SET/AI trong báo cáo, cộng khối trợ lý AI Text-to-SQL tiếng Việt có bộ dữ liệu
đánh giá và thực nghiệm ba cấu hình đối chứng.

**Đích cuối:** `make gate` xanh, sáu module dùng được theo đúng ma trận quyền §3.4.2, bộ 50–100 câu
hỏi – SQL chấm được trên ba cấu hình A/B/C, và số liệu thực nghiệm đủ để đưa vào Chương 4 của báo cáo.

## Hiện trạng

| Hạng mục | Trạng thái |
| --- | --- |
| Tài liệu (báo cáo, Class/Use Case/Sequence diagram) | Đã chốt, đã đồng bộ vào repo |
| Hạ tầng (monorepo, toolchain, CI, Makefile, Docker) | Xong |
| Primitive dùng chung (`core/`, `shared/`) | Xong, có test |
| `guard.py` (kiểm duyệt SQL) | Xong, 20 test |
| Lược đồ CSDL 29 bảng | **Chưa có** |
| View `vw_ai_*` + tài khoản chỉ-đọc | **Chưa có** |
| Sáu module nghiệp vụ | Chỉ có router rỗng |
| Pipeline AI | Chỉ `normalize` xong; 5 bước còn lại là interface |
| Seed dữ liệu, bộ đánh giá | Chưa có |

## Ràng buộc bất biến

Áp dụng cho **mọi** phase, không phase nào được vi phạm:

1. **MySQL 8.4**, `utf8mb4_unicode_ci`. Không cú pháp PostgreSQL.
2. **Định danh CSDL tiếng Việt** theo báo cáo (`NGUYEN_LIEU`, `MaNguyenLieu`, `DaXoa`); tên
   lớp/hàm/biến Python tiếng Anh.
3. **Truy vấn chỉ qua SQLAlchemy**, không nối chuỗi SQL.
4. **Phân quyền ở tầng API**, không chỉ ẩn nút giao diện (NFR-05).
5. **Business Date 06:00 → 06:00** qua `app.shared.business_date`, không tự tính lại.
6. **SQL của AI bắt buộc qua `guard.validate_sql`** — không có đường tắt.
7. **Mỗi vai trò một view + một tài khoản CSDL chỉ-đọc riêng** (NFR-06).
8. **Audit log append-only** cho đúng danh sách thao tác rủi ro ở FR-SET-08.
9. `make gate` xanh trước khi kết thúc mỗi task.

## Sơ đồ phụ thuộc giữa các phase

```
Phase 0 (lược đồ CSDL)  ← chặn tất cả
   │
   ├─▶ Phase 1 (Cài đặt)  ← chặn tất cả: cần tài khoản thật để đăng nhập
   │      │
   │      ├─▶ Phase 2 (Danh mục)  ← cần món/nguyên liệu/công thức
   │      │      │
   │      │      ├─▶ Phase 3 (Kho)   ← cần nguyên liệu; cung cấp trừ/hoàn kho FIFO
   │      │      │      │
   │      │      │      └─▶ Phase 4 (Bán hàng)  ← cần giá/công thức + trừ kho
   │      │      │             │
   │      │      │             └─▶ Phase 5 (Báo cáo)  ← đọc order/hóa đơn/kho
   │      │      │
   │      └─▶ Phase 6 (AI Assistant)  ← cần view + dữ liệu để hỏi
   │
   └─▶ Phase 7 (Seed + Đánh giá)  ← cần lược đồ; chạy được song song từ Phase 1
```

**Đường găng:** 0 → 1 → 2 → 3 → 4 → 5. Phase 6 và 7 tách nhánh, làm song song được.

## Sáu phase triển khai

| Phase | Nội dung | FR | Phụ thuộc | Chủ trì (§1.5) |
| --- | --- | --- | --- | --- |
| **0** | Lược đồ CSDL 29 bảng, view phân quyền, tài khoản chỉ-đọc | — | — | Hùng |
| **1** | Module 5 — Cài đặt: xác thực, tài khoản, vai trò, cấu hình, audit log | FR-SET-01…09 | 0 | Minh |
| **2** | Module 1 — Danh mục: món, giá/công thức theo Business Date, nguyên liệu, NCC, bàn | FR-CAT-01…28 | 1 | Hùng |
| **3** | Module 3 — Kho: nhập theo lô, trừ FIFO, xuất thủ công, kiểm kê, giá bình quân | FR-INV-01…12 | 2 | Minh |
| **4** | Module 2 — Bán hàng: order, phiếu bếp, thanh toán QR, đối soát, hóa đơn | FR-SALE-01…29 | 3 | Hùng |
| **5** | Module 4 — Báo cáo: doanh thu, xếp hạng món, giá vốn, biên lợi nhuận, khung giờ | FR-REP-01…10 | 4 | Minh |
| **6** | Module 6 — AI Assistant: prompt, sinh SQL, thực thi, diễn giải, biểu đồ | FR-AI-01…09 | 2, 4 | Hùng · Minh |
| **7** | Seed 12 tháng + bộ đánh giá 50–100 câu + harness A/B/C + SUS/UAT | Phụ lục 4 | 0 (chạy song song) | Khánh |

Kế hoạch chi tiết từng phase nằm trong `docs/plans/phases/`.

## Thứ tự thực thi đề xuất

Ba thành viên làm song song được theo bảng trên, nhưng thứ tự **an toàn nhất** cho một người làm
tuần tự là:

1. **Phase 0** — không có lược đồ thì không module nào viết được.
2. **Phase 1** — không có đăng nhập thật thì mọi test API phải giả lập token.
3. **Phase 7 (phần seed)** — có dữ liệu sớm để Phase 2–5 phát triển trên dữ liệu thật thay vì
   fixture tay; phần bộ đánh giá và harness làm sau ở Phase 6.
4. **Phase 2 → 3 → 4 → 5** theo đường găng.
5. **Phase 6** — cần view (Phase 0) và dữ liệu order (Phase 4) mới đánh giá được chất lượng.
6. **Phase 7 (phần đánh giá)** — chốt số liệu thực nghiệm sau cùng.

## Truy vết yêu cầu phi chức năng

Mỗi NFR phải có một chỗ chịu trách nhiệm rõ ràng, nếu không nó sẽ bị bỏ quên cho tới lúc bảo vệ.

| NFR | Nội dung | Xử lý ở đâu |
| --- | --- | --- |
| NFR-01 | Thao tác nghiệp vụ < 2s với 20 phiên đồng thời | Phase 5 Task 5 (kiểm `EXPLAIN` trên index §3.2.3) + Phase 3 Task 1 (khóa dòng không để nghẽn toàn bảng) |
| NFR-02 | Trợ lý AI phản hồi < 8s | Phase 6 Task 2 (`AI_RESPONSE_BUDGET_SECONDS`) + Phase 7 Task 4 (đo trong harness) |
| NFR-03 | Chịu tải ≥ 20.000 order/năm | Phase 0 (index §3.2.3) + Phase 7 Task 2 (sinh đúng quy mô) |
| NFR-04 | Mật khẩu băm, không plaintext | Phase 1 Task 1 (argon2 có sẵn ở `core/security.py`) |
| NFR-05 | Phân quyền ở tầng backend | Phase 1 Task 2 (`require_any_role`) + mọi phase sau đều có test 403 |
| NFR-06 | Giới hạn quyền của AI | Phase 0 Task 7 (view + tài khoản riêng) + Phase 6 Task 2, 3, 5 |
| NFR-07 | Nhật ký không sửa/xóa được | Phase 1 Task 4 (chỉ đăng ký `GET`) |
| NFR-08 | Nhất quán khi tranh chấp tồn kho | Phase 3 Task 1 (`SELECT ... FOR UPDATE` + một transaction ba tầng) |
| NFR-09 | RPO ≤ 24h với sao lưu thủ công | Phase 1 Task 2 (FR-SET-06 xuất bản sao) + `docker-compose.yml` volume; lịch sao lưu vận hành ghi ở README |
| NFR-10 | Toàn vẹn giao dịch (atomic) | Xuyên suốt: mọi thao tác ghi nằm trong một transaction, kể cả ghi audit (Phase 1 Task 2 chốt quy ước) |
| NFR-11 | Mở rộng vai trò/module không phải thiết kế lại | Kiến trúc đã có: mỗi module một gói, registry `modules.ts`, `Role` là enum; ghi chú ở Phase 2 Task 6 khi thêm màn hình |
| NFR-12 | Tách biệt tập view AI khỏi bảng lõi | Phase 0 Task 7 + Phase 6 Task 1, 5 |
| NFR-13 | Tối ưu thao tác trên tablet | Phase 4 Task 7 (vùng chạm lớn, bàn phím số cho trường số lượng) |
| NFR-14 | Hiển thị tiếng Việt | Xuyên suốt: `core/errors.py` đã trả thông báo tiếng Việt; mọi chuỗi hiển thị mới phải là tiếng Việt (quy ước trong `AGENTS.md`) |
| NFR-15 | Ghi log lỗi backend đủ chi tiết | Phase 1 Task 1 (không lộ chi tiết ra ngoài nhưng log lại) + Phase 4 Task 4 (log webhook sai chữ ký) |
| NFR-16 | Kiểm soát chi phí gọi LLM | Phase 6 Task 2 (hạn mức ngày + cache theo vai trò) |
| NFR-17 | Tương thích Chrome/Edge/Safari, máy tính và tablet | Phase 4 Task 7 và Phase 5 Task 5 (kiểm thử thủ công trên ba trình duyệt trước khi kết thúc phase) |

## Cổng kiểm soát của con người

Bốn mốc bắt buộc dừng lại xin ý kiến, không tự vượt:

| Mốc | Sau khi | Câu hỏi cần chốt |
| --- | --- | --- |
| G1 | Phase 0 | Lược đồ 29 bảng đã đúng ý chưa? Ba quyết định ở phase-0 §"Quyết định cần chốt"? |
| G2 | Phase 1 | Luồng xác thực và ma trận quyền đã khớp §3.4.2 chưa? |
| G3 | Phase 4 | Nghiệp vụ bán hàng (đường đi của tiền) đã đúng thực tế nhà hàng chưa? |
| G4 | Phase 6 | Số liệu thực nghiệm ba cấu hình đã đủ để viết Chương 4 chưa? |

## Điểm chưa chốt cần bạn quyết

Các điểm dưới đây ảnh hưởng tới thiết kế, không tự quyết được:

| # | Vấn đề | Ảnh hưởng | Đề xuất |
| --- | --- | --- | --- |
| Q1 | **Cổng thanh toán QR chưa chọn** (Phụ lục 2, Vấn đề #3). Không có nhà cung cấp thì không có webhook thật để tích hợp. | Phase 4 | Dựng **adapter** với một cổng giả lập (`mock`) làm mặc định, cài đặt theo interface; cắm cổng thật sau chỉ đổi adapter. Webhook vẫn xác thực chữ ký + đối chiếu số tiền + idempotent đầy đủ. |
| Q2 | **Máy in nhiệt** (§1.4.3 loại chi tiết driver/khổ giấy khỏi phạm vi). | Phase 4 | Backend sinh **nội dung phiếu** (text + cấu trúc) và ghi `PHIEU_BEP`; tầng in thật để ngoài hệ thống. Giao diện có nút in gọi `window.print()`. |
| Q3 | **Sao lưu/phục hồi** (FR-SET-06/07, FR-SET-07 ghi rõ "(Mở rộng)"). | Phase 1 | Làm FR-SET-06 (xuất bản sao thủ công) trong MVP; FR-SET-07 để lại sau, ghi rõ trong plan là mở rộng. |
| Q4 | **Tên biến môi trường LLM**: báo cáo §1.4.2 và §4.1.1 ghi `LLM_MODEL`, repo hiện dùng `AI_MODEL`. | Phase 6 | Đổi sang `LLM_MODEL` cho khớp báo cáo, giữ `AI_PROVIDER` để chọn nhà cung cấp. Xác nhận giúp. |
| Q5 | **Phạm vi thực nghiệm A/B/C**: cấu hình C là "cấu hình B trên một mô hình khác" — cần model nào? Ollama chưa cài trên máy này (`ollama not found`). | Phase 7 | Cần bạn chốt model cho cấu hình C, hoặc cho phép dùng model thương mại thứ hai (ví dụ Gemini Flash) thay vì Ollama. |
| Q6 | **Mô hình LLM chính**: `AI_MODEL=gpt-4o-mini` trong `.env.example`, nhưng sandbox chỉ cho phép các domain trong `~/.codex/config.toml` — API của OpenAI chưa nằm trong allowlist. | Phase 6 | Cần bạn thêm domain API của nhà cung cấp vào allowlist, hoặc dùng provider đã có sẵn (`bedrock.viber.vn`). |

## Rủi ro toàn dự án

| Rủi ro | Mức | Giảm thiểu |
| --- | --- | --- |
| Lược đồ 29 bảng phức tạp (lô FIFO, ba tầng tồn kho, `GIAO_DICH_KHO` bốn FK rời rạc) dễ sai | Cao | Phase 0 có test ràng buộc + chạy migration thật trên MySQL, không chỉ test metadata |
| Tranh chấp tồn kho đồng thời (NFR-08) | Cao | `SELECT ... FOR UPDATE` trên `NGUYEN_LIEU` theo §3.2.2, một transaction bao trọn ba tầng |
| Báo cáo giá vốn phụ thuộc job backfill giá bình quân | Trung bình | Job backfill là thành phần bắt buộc của Phase 3; báo cáo phải đánh dấu rõ dòng "tạm tính" |
| Không có cổng thanh toán thật | Trung bình | Adapter + mock (Q1); luồng webhook vẫn kiểm thử được đầy đủ |
| Chi phí gọi LLM khi chạy thực nghiệm A/B/C | Trung bình | NFR-16: hạn mức câu hỏi/ngày + cache câu hỏi lặp; chạy harness trên bộ 50–100 câu |
| Ba thành viên sửa cùng file (`modules.ts`, `main.py`) | Thấp | Mỗi module một gói riêng; registry `modules.ts` chỉ sửa khi thêm module |
| Prompt AI phụ thuộc lược đồ | Trung bình | Chỉ triển khai `prompt.py` sau khi Phase 0 xong |

## Định nghĩa "xong" của dự án

- [ ] `make gate` xanh trên nhánh `main` (format · lint · mypy/tsc · test · build).
- [ ] 29 bảng + 3 view + 3 tài khoản chỉ-đọc chạy được trên MySQL 8.4 sạch.
- [ ] Sáu module có API + giao diện dùng được, đúng ma trận quyền §3.4.2 (có test cho từng vai trò).
- [ ] Mọi thao tác rủi ro ở FR-SET-08 đều sinh bản ghi `NHAT_KY_HE_THONG`.
- [ ] Trợ lý AI trả lời được câu hỏi tiếng Việt trong đúng phạm vi vai trò, từ chối khi vượt quyền.
- [ ] Bộ 50–100 câu hỏi – SQL chuẩn hoàn chỉnh, phân tầng ba mức khó.
- [ ] Harness chạy được ba cấu hình A/B/C và xuất bảng chỉ số (độ chính xác thực thi, tỷ lệ SQL lỗi,
      tỷ lệ từ chối, thời gian phản hồi).
- [ ] Seed 12 tháng ≥ 20.000 order, tôn trọng Business Date và FIFO.
