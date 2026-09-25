# Lộ trình triển khai — Hệ thống quản lý nhà hàng tích hợp AI

Ngày: 2026-09-24 · Cập nhật: 2026-09-25

## Mục tiêu dự án

Biến repository từ **khung dự án** thành sản phẩm chạy được: sáu module nghiệp vụ đầy đủ theo
FR-CAT/SALE/INV/REP/SET/AI trong báo cáo, cộng khối trợ lý AI Text-to-SQL tiếng Việt có bộ dữ liệu
đánh giá và thực nghiệm ba cấu hình đối chứng.

**Đích cuối:** `make gate` xanh, sáu module dùng được theo đúng ma trận quyền §3.4.2, bộ 50–100 câu
hỏi – SQL chấm được trên ba cấu hình A/B/C, và số liệu thực nghiệm đủ để đưa vào Chương 4 của báo cáo.

## Hiện trạng

Cập nhật 2026-09-25: **Phase 0 → 7 đã xong** trên `main` (`make gate` xanh), trừ **Task 5 của Phase 7**
(lần chạy thực nghiệm A/B/C để lấy số liệu Chương 4) đang chờ nhà cung cấp LLM — Q5 và Q6 bên dưới.

| Hạng mục | Trạng thái |
| --- | --- |
| Tài liệu (báo cáo, Class/Use Case/Sequence diagram) | Đã chốt, đã đồng bộ vào repo |
| Hạ tầng (monorepo, toolchain, CI, Makefile, Docker) | Xong |
| Primitive dùng chung (`core/`, `shared/`) | Xong, có test |
| `guard.py` (kiểm duyệt SQL) | Xong, 20 test |
| Lược đồ CSDL 29 bảng theo báo cáo + `DEM_ORDER` | **Xong** (Phase 0; migration `890db4fbb8b6` + `0f1501bac9b8`) |
| View `vw_ai_*` + tài khoản chỉ-đọc | **Xong** (Phase 0, cập nhật ở Phase 7 theo đặc tả `db/views/README.md`) |
| Sáu module nghiệp vụ | Phase 1–6 xong (Cài đặt · Danh mục · Kho · Bán hàng · Báo cáo · Trợ lý AI) |
| Pipeline AI | **Xong** (Phase 6): prompt theo view, sinh SQL qua guard, thực thi trên tài khoản vai trò, diễn giải + biểu đồ |
| Seed dữ liệu, bộ đánh giá | **Xong** (Phase 7): `make seed` (12 tháng qua tầng service), 75 câu hỏi – SQL chuẩn, harness A/B/C. **Số liệu thực nghiệm chưa có** — cần Q5/Q6 |

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
   │      │      │             ├─▶ Phase 5 (Báo cáo)  ← đọc order/hóa đơn/kho
   │      │      │             │
   │      │      │             └─▶ Phase 6 (AI Assistant)  ← cần dữ liệu order thật
   │      │      │
   │      └─▶ Phase 7 (Seed)  ← cần service của Phase 2, 3, 4
   │
   └─▶ Phase 7 (Đánh giá)  ← cần pipeline Phase 6
```

**Đường găng:** 0 → 1 → 2 → 3 → 4 → 5. Phase 6 cần lược đồ (Phase 0) và công thức (Phase 2) để dựng
prompt, nhưng cần **dữ liệu order thật** (Phase 4) mới đánh giá được chất lượng — nên trên thực tế
nó bắt đầu sau Phase 4.

**Phase 7 không nằm ngoài đường găng nhưng cũng không song song được sớm:** script seed gọi
`create_dish`/`assign_recipe` (Phase 2), `create_receipt`/`create_issue`/`create_stocktake`/`close_month`
(Phase 3) và `submit_order`/`pay_cash`/`start_qr` (Phase 4) — **sinh dữ liệu qua tầng service là ràng
buộc của chính phase đó** (§"Kiến trúc" của phase-7), nên phần seed chỉ bắt đầu được sau Phase 4.
Phần bộ câu hỏi và harness đợi Phase 6. Chỉ có khung `SeedConfig` + danh mục nền là làm được sớm.

## Tám phase triển khai

| Phase | Nội dung | FR | Phụ thuộc | Chủ trì (§1.5) |
| --- | --- | --- | --- | --- |
| **0** | Lược đồ CSDL 29 bảng theo báo cáo + `DEM_ORDER`, view phân quyền, tài khoản chỉ-đọc | — | — | Hùng |
| **1** | Module 5 — Cài đặt: xác thực, tài khoản, vai trò, cấu hình, audit log | FR-SET-01…09 | 0 | Minh |
| **2** | Module 1 — Danh mục: món, giá/công thức theo Business Date, nguyên liệu, NCC, bàn | FR-CAT-01…28 | 1 | Hùng |
| **3** | Module 3 — Kho: nhập theo lô, trừ FIFO, xuất thủ công, kiểm kê, giá bình quân | FR-INV-01…12 | 2 | Minh |
| **4** | Module 2 — Bán hàng: order, phiếu bếp, thanh toán QR, đối soát, hóa đơn | FR-SALE-01…29 | 3 | Hùng |
| **5** | Module 4 — Báo cáo: doanh thu, xếp hạng món, giá vốn, biên lợi nhuận, khung giờ | FR-REP-01…10 | 4 | Minh |
| **6** | Module 6 — AI Assistant: prompt, sinh SQL, thực thi, diễn giải, biểu đồ | FR-AI-01…09 | 2, 4 | Hùng · Minh |
| **7** | Seed 12 tháng + bộ đánh giá 50–100 câu + harness A/B/C + SUS/UAT | Phụ lục 4 | 2, 3, 4 (seed) · 6 (đánh giá) | Khánh |

Kế hoạch chi tiết từng phase nằm trong `docs/plans/phases/`.

## Thứ tự thực thi đề xuất

Ba thành viên làm song song được theo bảng trên, nhưng thứ tự **an toàn nhất** cho một người làm
tuần tự là:

1. **Phase 0** — không có lược đồ thì không module nào viết được.
2. **Phase 1** — không có đăng nhập thật thì mọi test API phải giả lập token.
3. **Phase 2 → 3 → 4 → 5** theo đường găng.
4. **Phase 6** — cần view (Phase 0) và dữ liệu order (Phase 4) mới đánh giá được chất lượng.
5. **Phase 7 (seed)** — chỉ chạy được sau Phase 4 vì script gọi service của Phase 2/3/4; đây là
   bước **sau** đường găng, không phải bước chèn giữa.
6. **Phase 7 (bộ câu hỏi + harness + số liệu)** — chốt số liệu thực nghiệm sau cùng, cần Phase 6.

Nếu cần dữ liệu sớm cho Phase 2–5, dùng fixture của tầng test (Phase 0 Task 0) chứ **không** hạ
Phase 7 xuống trước — thứ tự đó không chạy được.

## Truy vết yêu cầu phi chức năng

Mỗi NFR phải có một chỗ chịu trách nhiệm rõ ràng, nếu không nó sẽ bị bỏ quên cho tới lúc bảo vệ.

| NFR | Nội dung | Xử lý ở đâu |
| --- | --- | --- |
| NFR-01 | Thao tác nghiệp vụ < 2s với 20 phiên đồng thời | Phase 5 Task 5 (`bench_reports.py`, ngưỡng 2s/endpoint) + Phase 3 Task 1 (khóa dòng không để nghẽn toàn bảng) |
| NFR-02 | Trợ lý AI phản hồi < 8s | Phase 6 Task 2 (`AI_RESPONSE_BUDGET_SECONDS`) + Phase 7 Task 4 (đo trong harness) |
| NFR-03 | Chịu tải ≥ 20.000 order/năm | Phase 0 (index §3.2.3) + Phase 7 Task 2 (sinh đúng quy mô) + Phase 5 Task 5 (`bench_reports.py` đo trên dữ liệu 12 tháng) |
| NFR-04 | Mật khẩu băm, không plaintext | Phase 1 Task 1 (argon2 có sẵn ở `core/security.py`) |
| NFR-05 | Phân quyền ở tầng backend | Phase 1 Task 2 (`require_any_role`) + mọi phase sau đều có test 403 |
| NFR-06 | Giới hạn quyền của AI | Phase 0 Task 7 (view + tài khoản riêng) + Phase 6 Task 2, 3, 5 |
| NFR-07 | Nhật ký không sửa/xóa được | Phase 1 Task 4 (chỉ đăng ký `GET`) |
| NFR-08 | Nhất quán khi tranh chấp tồn kho | Phase 3 Task 1 (`SELECT ... FOR UPDATE` + một transaction ba tầng) |
| NFR-09 | RPO ≤ 24h với sao lưu thủ công | Phase 1 Task 2 (FR-SET-06 xuất bản sao) + `docker-compose.yml` volume; lịch sao lưu vận hành ghi ở README |
| NFR-10 | Toàn vẹn giao dịch (atomic) | Xuyên suốt: mọi thao tác ghi nằm trong một transaction, kể cả ghi audit (Phase 1 Task 2 chốt quy ước) |
| NFR-11 | Mở rộng vai trò/module không phải thiết kế lại | Kiến trúc đã có: mỗi module một gói, registry `modules.ts`, `Role` là enum; ghi chú ở Phase 2 Task 6 khi thêm màn hình |
| NFR-12 | Tách biệt tập view AI khỏi bảng lõi | Phase 0 Task 7 (view chỉ đọc từ bảng lõi, `test_ai_views.py`) + Phase 0 Task 8 (`test_ai_isolation.py`: GRANT chặn bảng lõi) + Phase 6 Task 1 (prompt chỉ chứa đúng một view — `test_the_prompt_names_the_forbidden_tables_explicitly`) + Phase 6 Task 5 (`TRUY_VAN_AI.PhamViDuLieu` ghi lại view thật đã dùng) |
| NFR-13 | Tối ưu thao tác trên tablet | Phase 4 Task 7 (vùng chạm lớn, bàn phím số cho trường số lượng) |
| NFR-14 | Hiển thị tiếng Việt | Xuyên suốt: `core/errors.py` đã trả thông báo tiếng Việt; mọi chuỗi hiển thị mới phải là tiếng Việt (quy ước trong `AGENTS.md`) |
| NFR-15 | Ghi log lỗi backend đủ chi tiết | Phase 1 Task 1 (không lộ chi tiết ra ngoài nhưng log lại) + Phase 4 Task 4 (log webhook sai chữ ký) |
| NFR-16 | Kiểm soát chi phí gọi LLM | Phase 6 Task 2 (hạn mức ngày + cache theo vai trò) |
| NFR-17 | Tương thích Chrome/Edge/Safari, máy tính và tablet | Phase 4 Task 7 Step 6 (màn hình order/thanh toán) + Phase 5 Task 5 Step 7 (màn hình báo cáo); cả hai ghi kết quả từng trình duyệt vào PR |

## Cổng kiểm soát của con người

Bốn mốc bắt buộc dừng lại xin ý kiến, không tự vượt:

| Mốc | Sau khi | Câu hỏi cần chốt |
| --- | --- | --- |
| G1 | Phase 0 | Lược đồ 29 bảng theo báo cáo (cộng `DEM_ORDER` phát sinh ở Phase 4) đã đúng ý chưa? Ba quyết định ở phase-0 §"Quyết định cần chốt"? |
| G2 | Phase 1 | Luồng xác thực và ma trận quyền đã khớp §3.4.2 chưa? |
| G3 | Phase 4 | Nghiệp vụ bán hàng (đường đi của tiền) đã đúng thực tế nhà hàng chưa? |
| G4 | Phase 6 | Số liệu thực nghiệm ba cấu hình đã đủ để viết Chương 4 chưa? |

## Điểm chưa chốt cần bạn quyết

Các điểm dưới đây ảnh hưởng tới thiết kế, không tự quyết được. Cột **Trạng thái** cho biết plan đã
tự chốt được chưa, hay vẫn đang chờ bạn trả lời — plan viết theo hướng đề xuất để không bị chặn, và
đổi hướng rẻ hơn nhiều so với đổi kiến trúc.

| # | Vấn đề | Ảnh hưởng | Đề xuất | Trạng thái |
| --- | --- | --- | --- | --- |
| Q1 | **Cổng thanh toán QR chưa chọn** (Phụ lục 2, Vấn đề #3). Không có nhà cung cấp thì không có webhook thật để tích hợp. | Phase 4 | Dựng **adapter** với một cổng giả lập (`mock`) làm mặc định, cài đặt theo interface; cắm cổng thật sau chỉ đổi adapter. Webhook vẫn xác thực chữ ký + đối chiếu số tiền + idempotent đầy đủ. | Plan đi theo đề xuất; đổi nhà cung cấp chỉ cần viết thêm một adapter. |
| Q2 | **Máy in nhiệt** (§1.4.3 loại chi tiết driver/khổ giấy khỏi phạm vi). | Phase 4 | Backend sinh **nội dung phiếu** (text + cấu trúc) và ghi `PHIEU_BEP`; tầng in thật để ngoài hệ thống. Giao diện có nút in gọi `window.print()`. | Plan đi theo đề xuất; §1.4.3 đã loại driver khỏi phạm vi nên không cần chốt. |
| Q3 | **Sao lưu/phục hồi** (FR-SET-06/07, FR-SET-07 ghi rõ "(Mở rộng)"). | Phase 1 | Làm FR-SET-06 (xuất bản sao thủ công) trong MVP; FR-SET-07 để lại sau, ghi rõ trong plan là mở rộng. | **Đã chốt trong plan** (Phase 1 Task 2 + mục Rủi ro). Phục hồi là thao tác phá huỷ — bàn riêng trước khi làm. |
| Q4 | **Tên biến môi trường LLM**: báo cáo §1.4.2 và §4.1.1 ghi `LLM_MODEL`, repo hiện dùng `AI_MODEL`. | Phase 6 | Đổi sang `LLM_MODEL` cho khớp báo cáo, giữ `AI_PROVIDER` để chọn nhà cung cấp. Xác nhận giúp. | **Đã xong ở Phase 6 Task 2** — `core/config.py`, `.env.example` và `llm.py` nay dùng `LLM_MODEL`. |
| Q5 | **Phạm vi thực nghiệm A/B/C**: cấu hình C là "cấu hình B trên một mô hình khác" — cần model nào? Ollama chưa cài trên máy này (`ollama not found`). | Phase 7 | Cần bạn chốt model cho cấu hình C, hoặc cho phép dùng model thương mại thứ hai (ví dụ Gemini Flash) thay vì Ollama. | **Chờ bạn chốt** (Phase 7 Task 4 + mục Rủi ro ghi rõ hai đường). Không chặn Phase 0–6. |
| Q6 | **Mô hình LLM chính**: `AI_MODEL=gpt-4o-mini` trong `.env.example`, nhưng sandbox chỉ cho phép các domain trong `~/.codex/config.toml` — API của OpenAI chưa nằm trong allowlist. | Phase 6 | Cần bạn thêm domain API của nhà cung cấp vào allowlist, hoặc dùng provider đã có sẵn (`bedrock.viber.vn`). | **Chờ bạn chốt.** Ảnh hưởng duy nhất là lúc chạy thật; test Phase 6 dùng `fake_llm` nên không bị chặn. |

## Rủi ro toàn dự án

| Rủi ro | Mức | Giảm thiểu |
| --- | --- | --- |
| Lược đồ 29 bảng phức tạp (lô FIFO, ba tầng tồn kho, `GIAO_DICH_KHO` bốn FK rời rạc) dễ sai | Cao | Phase 0 có test ràng buộc + chạy migration thật trên MySQL, không chỉ test metadata |
| Tầng fixture dùng chung bị bỏ sót khiến vòng red→green vô nghĩa ở mọi phase | Cao | Phase 0 **Task 0** dựng `conftest.py`/`factories.py` trước mọi task khác; test của Task 0 khẳng định fixture chạy được |
| Tài liệu kế hoạch lệch nhau giữa các phase (chữ ký hàm, tên trường, phụ thuộc) | Trung bình | Mỗi phase có mục "Hợp đồng với các phase khác"; sửa chữ ký ở phase sở hữu hàm, phase khác chỉ nhắc lại |
| Tranh chấp tồn kho đồng thời (NFR-08) | Cao | `SELECT ... FOR UPDATE` trên `NGUYEN_LIEU` theo §3.2.2, một transaction bao trọn ba tầng |
| Báo cáo giá vốn phụ thuộc job backfill giá bình quân | Trung bình | Job backfill là thành phần bắt buộc của Phase 3; báo cáo phải đánh dấu rõ dòng "tạm tính" |
| Không có cổng thanh toán thật | Trung bình | Adapter + mock (Q1); luồng webhook vẫn kiểm thử được đầy đủ |
| Chi phí gọi LLM khi chạy thực nghiệm A/B/C | Trung bình | NFR-16: hạn mức câu hỏi/ngày + cache câu hỏi lặp; chạy harness trên bộ 50–100 câu |
| Ba thành viên sửa cùng file (`modules.ts`, `main.py`) | Thấp | Mỗi module một gói riêng; registry `modules.ts` chỉ sửa khi thêm module |
| Prompt AI phụ thuộc lược đồ | Trung bình | Chỉ triển khai `prompt.py` sau khi Phase 0 xong |

## Nợ kỹ thuật đã biết, phải trả trong lúc làm

Không phải rủi ro (chưa xảy ra) mà là **việc đã biết chắc là phải làm**, ghi ở đây để không ai quên:

| Việc | Ai trả | Ở đâu |
| --- | --- | --- |
| `VAI_TRO` + `CAU_HINH_HE_THONG` chưa từng được seed; mọi FK `MaVaiTro` fail trên CSDL sạch | Phase 1 | Task 1 Step 0 (`seed_reference_data`) |
| `aiosqlite`, `asgi-lifespan`, `httpx` (runtime) chưa có trong `pyproject.toml`; marker pytest chưa đăng ký | Phase 0 | Task 0 Step 1 (và Phase 6 Task 2 cho `httpx`) |
| `NAMING_CONVENTION` thiếu khoá `ck` → mọi `CHECK` vô danh, test lọc `ck_` pass rỗng | Phase 0 | Quy ước #8 + Task 1 |
| `MON_AN.TrangThai` GENERATED không biểu diễn được `Nháp` — báo cáo tự mâu thuẫn | Phase 2 | Mục "Trạng thái hiển thị của món" + quyết định #1 của Phase 0 |
| `ThuTuHienThi` (sắp xếp nhóm món, FR-CAT-01) chưa có endpoint lẫn test | Phase 2 | Task 1 (`reorder_groups`) |
| Bộ đếm số order không tồn tại; `SELECT MAX(...) FOR UPDATE` không khoá được dải rỗng | Phase 4 | Task 1 (`DEM_ORDER`, bảng thứ 30) |
| `scripts/bench_reports.py` chưa có → cổng NFR-01/NFR-03 thành "unfinished" im lặng | Phase 5 | Task 5 Step 5 |
| `data/eval/harness.py` không import được từ `apps/api/tests` nếu thiếu `pythonpath` | Phase 7 | Task 4 Step 2 |
| `grants.sql` chứa mật khẩu plaintext — không được commit | Phase 0 | Task 7 (`grants.sql.template` + `scripts/apply_grants.sh`) |
| Đồng hồ: service gọi `datetime.now()` trực tiếp thì test không cắm được | Phase 0 | Task 0 Step 4 (`business_date.now()` + fixture `freeze_clock` autouse) |
| `ThuTuHienThi` không đặt `UNIQUE` — reorder tạm trùng số giữa chừng | Phase 0 | Task 2 (chốt không unique) + Phase 2 Task 1 |

## Định nghĩa "xong" của dự án

- [ ] `make gate` xanh trên nhánh `main` (format · lint · mypy/tsc · test · build).
- [ ] 29 bảng theo báo cáo + `DEM_ORDER` + 3 view + 3 tài khoản chỉ-đọc chạy được trên MySQL 8.4 sạch.
- [ ] Sáu module có API + giao diện dùng được, đúng ma trận quyền §3.4.2 (có test cho từng vai trò).
- [ ] Mọi thao tác rủi ro ở FR-SET-08 đều sinh bản ghi `NHAT_KY_HE_THONG`.
- [ ] Trợ lý AI trả lời được câu hỏi tiếng Việt trong đúng phạm vi vai trò, từ chối khi vượt quyền.
- [ ] Bộ 50–100 câu hỏi – SQL chuẩn hoàn chỉnh, phân tầng ba mức khó.
- [ ] Harness chạy được ba cấu hình A/B/C và xuất bảng chỉ số (độ chính xác thực thi, tỷ lệ SQL lỗi,
      tỷ lệ từ chối, thời gian phản hồi).
- [ ] Seed 12 tháng ≥ 20.000 order, tôn trọng Business Date và FIFO.
