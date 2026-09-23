# Phase 6 — Module 6: Trợ lý AI (Text-to-SQL)

> **Cho người thực thi:** dùng skill `executing-plans` để chạy kế hoạch này theo từng task.

**Mục tiêu:** Toàn bộ FR-AI-01…09: hỏi đáp tiếng Việt, sinh SQL, kiểm duyệt, thực thi trên view phân
quyền, diễn giải kết quả kèm bảng số liệu và biểu đồ — mỗi vai trò một trợ lý riêng đúng phạm vi.

**Kiến trúc:** Pipeline sáu bước đã chốt trong `pipeline/__init__.py`:
`normalize → prompt → generate → guard → execute → interpret`. Bước 1 (`normalize`) và bước 4
(`guard`) đã xong và có test. Phase này lấp bốn bước còn lại. **Không bước nào được bỏ qua `guard`.**

**Spec:** báo cáo §2.4.6 (FR-AI-01…09), §3.4.1 (ma trận quyền dữ liệu), §4.1.1, NFR-06, NFR-16,
SD-05, Phụ lục 4 (ba cấu hình đối chứng).

**Phụ thuộc:** Phase 0 (view + tài khoản chỉ-đọc), Phase 2 và Phase 4 (dữ liệu để hỏi).
**Lộ trình:** `docs/plans/2026-09-24-master-roadmap.md` · **Nhánh:** `feat/phase-6-assistant`

**Cổng người duyệt:** G4

## Ràng buộc chung

- Mọi SQL **bắt buộc** qua `guard.validate_sql` trước khi thực thi — không có đường tắt, kể cả trong test.
- Prompt **chỉ** chứa lược đồ của **một** view (view của vai trò đang hỏi), không bao giờ chứa bảng lõi
  (FR-AI-05).
- Thực thi bằng tài khoản chỉ-đọc **của đúng vai trò** (`accounts.readonly_url_for`), tối đa
  `AI_SQL_TIMEOUT_SECONDS` (3s) và `AI_MAX_ROWS` (500) dòng.
- Tối đa `AI_MAX_SQL_ATTEMPTS` (2) lần sinh SQL cho mỗi câu hỏi (NFR-06).
- Câu trả lời **luôn** kèm bảng số liệu gốc và ghi chú phạm vi dữ liệu (FR-AI-07, business rule 16).
- Loại biểu đồ theo quy tắc cố định: biến động theo thời gian → line; so sánh nhóm → bar; cơ cấu →
  doughnut; không phù hợp → chỉ bảng (FR-AI-07).
- Không trả lời được thì thông báo và gợi ý diễn đạt lại, không im lặng (FR-AI-09).
- Toàn bộ chuỗi xử lý (chuẩn hóa → sinh SQL → kiểm duyệt → thực thi → diễn giải) phải xong trong
  `AI_RESPONSE_BUDGET_SECONDS` (8s) — NFR-02. `AI_SQL_TIMEOUT_SECONDS` (3s) là hạn riêng cho phần
  CSDL; phần còn lại là ngân sách cho LLM.
- Câu trả lời, thông báo lỗi và gợi ý làm rõ đều bằng **tiếng Việt** (NFR-14).
- `make gate` xanh trước khi kết thúc mỗi task.

## Cấu trúc file

| File | Trách nhiệm |
| --- | --- |
| `apps/api/src/app/modules/ai/pipeline/prompt.py` | Bước 2 — lược đồ view + few-shot, dựng prompt. |
| `apps/api/src/app/modules/ai/pipeline/generator.py` | Bước 3 — gọi LLM, hạn mức ngày, cache. |
| `apps/api/src/app/modules/ai/pipeline/executor.py` | Bước 5 — chạy SQL trên tài khoản chỉ-đọc của vai trò. |
| `apps/api/src/app/modules/ai/pipeline/interpreter.py` | Bước 6 — câu trả lời tiếng Việt + đặc tả biểu đồ. |
| `apps/api/src/app/modules/ai/charts.py` | Quy tắc chọn loại biểu đồ (FR-AI-07). |
| `apps/api/src/app/modules/ai/llm.py` | Adapter nhà cung cấp LLM (thương mại + Ollama dự phòng). |
| `apps/api/src/app/modules/ai/service.py` | Điều phối sáu bước, ghi `TRUY_VAN_AI`. |
| `apps/web/src/features/assistant/` | Khung chat, bảng số liệu, biểu đồ, mục "Xem chi tiết". |
| `apps/api/tests/modules/test_ai_*.py` | Test theo từng bước. |

---

## Task 1: Lược đồ view và dựng prompt (FR-AI-05, 06)

**Files:**
- Modify: `apps/api/src/app/modules/ai/pipeline/prompt.py`
- Test: `apps/api/tests/modules/test_ai_prompt.py`

**Interfaces:**
- Consumes: `scope.views_for`, `accounts.readonly_url_for`, `guard.validate_sql`,
  `information_schema.columns`.
- Produces: `schema_block(session, role) -> str`;
  `build_prompt(question, role, schema, examples) -> str`.

- [ ] **Step 1: Viết test**

```python
async def test_the_schema_block_mentions_only_the_role_view(session, seed_views):
    """FR-AI-05: never the core tables."""
    block = await schema_block(session, Role.WAREHOUSE)

    assert "vw_ai_kho" in block
    for table in ("HOA_DON", "GIAO_DICH_THANH_TOAN", "NGUOI_DUNG"):
        assert table not in block


async def test_the_schema_block_lists_the_columns_of_that_view(session, seed_views):
    block = await schema_block(session, Role.WAREHOUSE)

    assert "TenNguyenLieu" in block
    assert "SoLuongTon" in block


async def test_each_role_gets_a_different_schema_block(session, seed_views):
    blocks = {role: await schema_block(session, role) for role in Role}

    assert len(set(blocks.values())) == len(Role)


async def test_the_prompt_carries_the_instructions_the_schema_and_the_question(session, seed_views):
    prompt = await build_prompt("Doanh thu hôm qua?", Role.CASHIER)

    assert "vw_ai_thungan" in prompt
    assert "Doanh thu hôm qua?" in prompt
    assert "SELECT" in prompt


async def test_the_prompt_forbids_touching_anything_outside_the_view(session, seed_views):
    prompt = await build_prompt("Cho tôi toàn bộ người dùng", Role.CASHIER)

    assert "chỉ" in prompt.lower()
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_ai_prompt.py -v`
Expected: FAIL — `NotImplementedError`

- [ ] **Step 3: Cài đặt**

`schema_block()` đọc `information_schema.columns` **chỉ** cho view của vai trò, kèm mô tả tiếng Việt
cho cột quan trọng (ví dụ `BusinessDate` = "ngày kinh doanh, 06:00 → 06:00"). `build_prompt()` ghép:
hướng dẫn hệ thống (chỉ `SELECT`, chỉ một câu, chỉ view này), lược đồ, few-shot lấy từ
`data/eval/questions.example.jsonl` đã lọc theo vai trò, rồi câu hỏi.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_ai_prompt.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(ai): build the role-scoped prompt from the view schema`

---

## Task 2: Adapter LLM và sinh SQL (FR-AI-01, 09 — NFR-16)

**Files:**
- Create: `apps/api/src/app/modules/ai/llm.py`
- Modify: `apps/api/src/app/modules/ai/pipeline/generator.py`
- Test: `apps/api/tests/modules/test_ai_generator.py`

**Interfaces:**
- Consumes: `prompt.build_prompt`, `guard.validate_sql`, `settings.ai_max_sql_attempts`,
  `settings.ai_daily_question_quota`.
- Produces: `LlmClient` (Protocol: `complete(prompt) -> str`); `CommercialClient`, `OllamaClient`,
  `FakeClient` (test); `get_client() -> LlmClient`;
  `generate_sql(session, question, role) -> str` (đã qua guard, tối đa 2 lần thử).

- [ ] **Step 1: Viết test**

```python
async def test_generation_returns_sql_that_passed_the_guard(session, fake_llm, seed_views):
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan")

    sql = await generate_sql(session, "Hôm nay có bao nhiêu đơn?", Role.CASHIER)

    assert "vw_ai_thungan" in sql
    assert "LIMIT" in sql  # the guard added the ceiling


async def test_a_write_statement_is_never_returned(session, fake_llm, seed_views):
    """FR-AI-05 and NFR-06: the guard is not optional."""
    fake_llm.reply("DELETE FROM vw_ai_thungan")

    with pytest.raises(BusinessRuleError):
        await generate_sql(session, "xóa hết đơn đi", Role.CASHIER)


async def test_the_model_gets_a_second_attempt_after_a_bad_query(session, fake_llm, seed_views):
    """NFR-06: at most two generations per question."""
    fake_llm.reply_sequence(["SELECT * FROM hoa_don", "SELECT COUNT(*) FROM vw_ai_thungan"])

    sql = await generate_sql(session, "hỏi", Role.CASHIER)

    assert fake_llm.calls == 2
    assert "vw_ai_thungan" in sql


async def test_a_third_attempt_never_happens(session, fake_llm, seed_views):
    fake_llm.reply_sequence(["SELECT * FROM hoa_don", "SELECT * FROM nguoi_dung", "SELECT 1 FROM vw_ai_thungan"])

    with pytest.raises(BusinessRuleError):
        await generate_sql(session, "hỏi", Role.CASHIER)

    assert fake_llm.calls == 2


async def test_an_out_of_scope_question_asks_for_clarification(session, fake_llm, seed_views):
    """FR-AI-06."""
    fake_llm.reply("CLARIFY: bạn muốn xem doanh thu của ngày nào?")

    with pytest.raises(ClarificationNeeded):
        await generate_sql(session, "doanh thu", Role.CASHIER)


async def test_the_daily_quota_stops_further_calls(session, fake_llm, seed_views, quota_reached):
    """NFR-16."""
    with pytest.raises(QuotaExceeded):
        await generate_sql(session, "hỏi", Role.CASHIER)

    assert fake_llm.calls == 0


async def test_a_repeated_question_is_served_from_cache(session, fake_llm, seed_views):
    """NFR-16."""
    fake_llm.reply("SELECT COUNT(*) FROM vw_ai_thungan")
    await generate_sql(session, "hôm nay bao nhiêu đơn", Role.CASHIER)

    await generate_sql(session, "hôm nay bao nhiêu đơn", Role.CASHIER)

    assert fake_llm.calls == 1


async def test_the_cache_does_not_leak_across_roles(session, fake_llm, seed_views):
    """FR-AI-05: the same words asked by another role must not reuse the answer."""
    fake_llm.reply_sequence(["SELECT COUNT(*) FROM vw_ai_thungan", "SELECT COUNT(*) FROM vw_ai_kho"])

    await generate_sql(session, "có bao nhiêu", Role.CASHIER)
    await generate_sql(session, "có bao nhiêu", Role.WAREHOUSE)

    assert fake_llm.calls == 2
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_ai_generator.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.ai.llm`

- [ ] **Step 3: Cài đặt**

`generate_sql()` lặp tối đa `settings.ai_max_sql_attempts` lần: gọi model, **đưa ngay qua
`guard.validate_sql`**; lỗi guard thì thử lại kèm thông báo lỗi trong prompt; hết lượt thì ném
`BusinessRuleError`. Cache theo khoá `(role, normalized_question)` — **có vai trò trong khoá**, nếu
không thì câu hỏi giống nhau giữa hai vai trò sẽ dùng chung câu trả lời và rò dữ liệu.
`get_client()` chọn nhà cung cấp theo `settings.ai_provider`; Ollama là dự phòng khi nhà cung cấp
chính không khả dụng (§4.1.1).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_ai_generator.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(ai): generate SQL through the guard with quota and caching`

---

## Task 3: Thực thi trên tài khoản chỉ-đọc của vai trò (FR-AI-05 — NFR-06)

**Files:**
- Modify: `apps/api/src/app/modules/ai/pipeline/executor.py`
- Test: `apps/api/tests/modules/test_ai_executor.py`

**Interfaces:**
- Consumes: `accounts.readonly_url_for` (đã có từ trước Phase 0 Task 8),
  `settings.ai_sql_timeout_seconds`.
- Produces: `execute(sql, *, role, timeout_seconds) -> list[dict[str, Any]]`.

- [ ] **Step 1: Viết test**

```python
async def test_the_query_runs_on_the_account_of_the_asking_role(monkeypatch, fake_engine_factory):
    """NFR-06: never a shared read-only account."""
    await execute("SELECT 1", role=Role.WAREHOUSE, timeout_seconds=3.0)

    assert fake_engine_factory.urls == [settings.ai_readonly_url_warehouse]


async def test_the_statement_timeout_is_applied(monkeypatch, fake_engine_factory):
    """NFR-06: at most three seconds on the database."""
    await execute("SELECT 1", role=Role.MANAGER, timeout_seconds=3.0)

    assert "MAX_EXECUTION_TIME" in fake_engine_factory.executed[0]
    assert "3000" in fake_engine_factory.executed[0]


async def test_rows_come_back_as_plain_dicts(monkeypatch, fake_engine_factory):
    fake_engine_factory.rows = [(1, "Phở bò")]

    rows = await execute("SELECT * FROM vw_ai_kho", role=Role.WAREHOUSE, timeout_seconds=3.0)

    assert rows == [{"MaNguyenLieu": 1, "TenNguyenLieu": "Phở bò"}]


async def test_the_account_is_never_reused_across_roles(monkeypatch, fake_engine_factory):
    await execute("SELECT 1", role=Role.CASHIER, timeout_seconds=3.0)
    await execute("SELECT 1", role=Role.WAREHOUSE, timeout_seconds=3.0)

    assert len(set(fake_engine_factory.urls)) == 2
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_ai_executor.py -v`
Expected: FAIL — `execute()` chưa nhận `role`

- [ ] **Step 3: Cài đặt**

Mở engine từ `readonly_url_for(role)`, đặt `SET SESSION MAX_EXECUTION_TIME = <ms>` trước khi chạy câu
SQL, dùng `text(sql)` của SQLAlchemy (không nối chuỗi), đóng engine sau khi xong (hoặc cache theo vai
trò — engine pool không dùng chung giữa các vai trò).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_ai_executor.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(ai): execute validated SQL on the role's read-only account`

---

## Task 4: Diễn giải kết quả và chọn biểu đồ (FR-AI-07, 08)

**Files:**
- Create: `apps/api/src/app/modules/ai/charts.py`
- Modify: `apps/api/src/app/modules/ai/pipeline/interpreter.py`
- Test: `apps/api/tests/modules/test_ai_interpreter.py`

**Interfaces:**
- Consumes: `LlmClient`, `views_for`.
- Produces: `choose_chart(columns, rows) -> ChartSpec | None`;
  `interpret(session, question, sql, rows, role) -> str`;
  `scope_note(role) -> str`.

- [ ] **Step 1: Viết test**

```python
def test_a_time_series_becomes_a_line_chart():
    """FR-AI-07: change over time is a line chart."""
    spec = choose_chart(columns=["BusinessDate", "DoanhThu"], rows=time_series_rows)

    assert spec.type == "line"
    assert spec.x == "BusinessDate"
    assert spec.y == ["DoanhThu"]


def test_a_comparison_between_groups_becomes_a_bar_chart():
    spec = choose_chart(columns=["TenMon", "SoLuong"], rows=ranking_rows)

    assert spec.type == "bar"


def test_a_share_of_a_whole_becomes_a_doughnut_chart():
    spec = choose_chart(columns=["TenMon", "TyTrong"], rows=share_rows)

    assert spec.type == "doughnut"


def test_a_single_number_gets_no_chart():
    """FR-AI-07: nothing suitable, so the table stands alone."""
    assert choose_chart(columns=["SoDon"], rows=[{"SoDon": 42}]) is None


def test_two_columns_that_are_not_a_series_get_no_chart():
    assert choose_chart(columns=["TenNguyenLieu", "DonViTinh"], rows=rows) is None


async def test_the_answer_is_vietnamese_and_carries_the_scope_note(session, fake_llm):
    """FR-AI-07 and business rule 16."""
    fake_llm.reply("Hôm qua có 42 đơn hàng.")

    answer = await interpret(session, "hôm qua bao nhiêu đơn?", sql, rows, Role.CASHIER)

    assert "42" in answer
    assert "vw_ai_thungan" in answer


async def test_the_scope_note_differs_per_role(session):
    assert scope_note(Role.WAREHOUSE) != scope_note(Role.MANAGER)
    assert "kho" in scope_note(Role.WAREHOUSE).lower()


async def test_an_empty_result_is_explained_not_left_blank(session, fake_llm):
    """FR-AI-09."""
    answer = await interpret(session, "hôm qua bao nhiêu đơn?", sql, [], Role.CASHIER)

    assert answer != ""
    assert "không có" in answer.lower()
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_ai_interpreter.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.ai.charts`

- [ ] **Step 3: Cài đặt**

`choose_chart()` **thuần quy tắc**, không gọi LLM: cột ngày/tháng + cột số → `line`; cột phân loại +
cột số, nhiều dòng → `bar`; cột phân loại + cột số mà tổng xấp xỉ 100 (hoặc tên gợi tỷ trọng) →
`doughnut`; còn lại → `None`. `interpret()` gọi LLM để viết câu trả lời nhưng **luôn** ghép thêm
`scope_note(role)` bằng code, không để model tự sinh (business rule 16).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_ai_interpreter.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(ai): interpret results and pick the chart by rule`

---

## Task 5: Điều phối pipeline và ghi nhật ký truy vấn (FR-AI-01, 02, 03, 04, 05, 06, 09)

**Files:**
- Modify: `apps/api/src/app/modules/ai/service.py`
- Modify: `apps/api/src/app/modules/ai/schemas.py`
- Modify: `apps/api/src/app/modules/ai/router.py`
- Test: `apps/api/tests/modules/test_ai_service.py`

**Interfaces:**
- Consumes: Task 1–4, `ChatSession`, `AssistantQuery`.
- Produces: `answer(session, question, role, user_id) -> ChatResponse`;
  `POST /assistant/chat` (bỏ 501).

- [ ] **Step 1: Viết test**

```python
async def test_one_turn_records_the_question_sql_timing_and_status(client, cashier_token, seed_views, fake_llm):
    """SD-05 and the TRUY_VAN_AI contract."""
    fake_llm.reply("SELECT COUNT(*) AS SoDon FROM vw_ai_thungan")

    response = await chat(client, cashier_token, "hôm nay có bao nhiêu đơn?")

    assert response.status_code == 200
    row = await latest_query(db_session)
    assert row.question == "hôm nay có bao nhiêu đơn?"
    assert row.status == "Thành công"
    assert row.response_ms >= 0
    assert row.data_scope == "vw_ai_thungan"


async def test_the_scope_recorded_is_the_view_actually_used(client, cashier_token, seed_views, fake_llm):
    """FR-AI-05: the audit trail must show what the assistant was allowed to read."""
    await chat(client, cashier_token, "hỏi")

    assert (await latest_query(db_session)).data_scope == "vw_ai_thungan"


async def test_the_response_carries_the_answer_rows_chart_and_detail(client, cashier_token, seed_views, fake_llm):
    """FR-AI-07 and FR-AI-08."""
    fake_llm.reply("SELECT TenNguyenLieu, SoLuongTon FROM vw_ai_kho")

    body = (await chat(client, warehouse_token, "tồn kho?")).json()

    assert body["answer"]
    assert body["data"]
    assert body["detail"]["sql"]
    assert body["detail"]["row_count"] == len(body["data"])
    assert body["detail"]["elapsed_ms"] >= 0


async def test_a_refusal_is_recorded_and_explained(client, cashier_token, seed_views, fake_llm):
    """FR-AI-09."""
    fake_llm.reply_sequence(["SELECT * FROM hoa_don", "SELECT * FROM nguoi_dung"])

    body = (await chat(client, cashier_token, "cho tôi lợi nhuận")).json()

    assert body["answer"]
    assert (await latest_query(db_session)).status == "Từ chối"


async def test_a_vague_question_asks_for_clarification(client, cashier_token, seed_views, fake_llm):
    """FR-AI-06."""
    fake_llm.reply("CLARIFY: bạn muốn xem doanh thu của ngày nào?")

    body = (await chat(client, cashier_token, "doanh thu")).json()

    assert "ngày nào" in body["answer"]
    assert (await latest_query(db_session)).status == "Yêu cầu làm rõ"


async def test_a_cross_role_question_gets_no_data(client, cashier_token, seed_views, fake_llm):
    """FR-AI-05: asking outside your scope must not return another role's data."""
    fake_llm.reply_sequence(["SELECT * FROM vw_ai_quanly", "SELECT * FROM vw_ai_quanly"])

    body = (await chat(client, cashier_token, "tổng lợi nhuận tháng này")).json()

    assert body["data"] == []


async def test_the_session_is_created_on_the_first_turn_and_reused_after(
    client, cashier_token, seed_views, fake_llm
):
    first = (await chat(client, cashier_token, "câu 1")).json()
    second = (await chat(client, cashier_token, "câu 2", session_id=first["session_id"])).json()

    assert second["session_id"] == first["session_id"]
    assert await session_count() == 1


async def test_the_endpoint_no_longer_returns_501(client, cashier_token, seed_views, fake_llm):
    assert (await chat(client, cashier_token, "hỏi")).status_code == 200


async def test_a_slow_turn_is_cut_off_at_the_response_budget(client, cashier_token, seed_views, slow_llm):
    """NFR-02: the whole chain must fit in eight seconds, not just the database part."""
    with pytest.raises(TimeoutError):
        await answer(session, "hỏi", Role.CASHIER, user_id=1)

    assert (await latest_query(db_session)).status == "Lỗi"


async def test_every_message_shown_to_the_user_is_vietnamese(client, cashier_token, seed_views, fake_llm):
    """NFR-14."""
    fake_llm.reply_sequence(["SELECT * FROM hoa_don", "SELECT * FROM hoa_don"])

    body = (await chat(client, cashier_token, "cho tôi lợi nhuận")).json()

    assert "Không thể" in body["answer"] or "không thể" in body["answer"]
```


async def test_the_manager_can_ask_about_all_three_domains(client, manager_token, seed_views, fake_llm):
    """FR-AI-02: the manager inherits every scope (FR-SET-03)."""
    fake_llm.reply("SELECT COUNT(*) AS n FROM vw_ai_quanly")

    for question in ("doanh thu tháng này?", "tồn kho còn bao nhiêu?", "món nào bán chạy nhất?"):
        assert (await chat(client, manager_token, question)).status_code == 200


async def test_the_cashier_can_ask_about_sales_but_not_cost(
    client, cashier_token, seed_views, fake_llm
):
    """FR-AI-03: revenue and invoices yes, purchase prices and margin no."""
    fake_llm.reply("SELECT COUNT(*) AS n FROM vw_ai_thungan")

    allowed = await chat(client, cashier_token, "hôm nay bán được bao nhiêu đơn?")
    assert allowed.status_code == 200

    fake_llm.reply_sequence(["SELECT * FROM vw_ai_quanly", "SELECT * FROM vw_ai_quanly"])
    refused = await chat(client, cashier_token, "giá nhập hàng tháng này là bao nhiêu?")
    assert refused.json()["data"] == []


async def test_the_warehouse_can_ask_about_stock_but_not_revenue(
    client, warehouse_token, seed_views, fake_llm
):
    """FR-AI-04."""
    fake_llm.reply("SELECT TenNguyenLieu FROM vw_ai_kho")

    allowed = await chat(client, warehouse_token, "nguyên liệu nào sắp hết?")
    assert allowed.status_code == 200

    fake_llm.reply_sequence(["SELECT * FROM vw_ai_quanly", "SELECT * FROM vw_ai_quanly"])
    refused = await chat(client, warehouse_token, "doanh thu hôm qua là bao nhiêu?")
    assert refused.json()["data"] == []


async def test_each_role_talks_to_its_own_view(client, seed_views, fake_llm):
    """FR-AI-01: one assistant per role, scoped to that role's view."""
    fake_llm.reply("SELECT 1 AS n FROM vw_ai_thungan")
    await chat(client, cashier_token, "hỏi")

    assert (await latest_query(db_session)).data_scope == "vw_ai_thungan"
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_ai_service.py -v`
Expected: FAIL — endpoint trả 501

- [ ] **Step 3: Cài đặt**

`answer()` chạy đúng sáu bước theo thứ tự trong `pipeline/__init__.py`, bọc `try/except` để **mọi**
nhánh đều ghi `TRUY_VAN_AI` với `TrangThai` phù hợp (`Thành công` / `Yêu cầu làm rõ` / `Từ chối` /
`Lỗi`) và `ThoiGianPhanHoi`. Xóa nhánh trả 501 ở router.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/modules/test_ai_service.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(ai): wire the six-step pipeline and log every turn`

---

## Task 6: Giao diện chat, biểu đồ và "Xem chi tiết" (FR-AI-01, 07, 08)

**Files:**
- Create: `apps/web/src/features/assistant/chart-view.tsx`
- Create: `apps/web/src/features/assistant/chart-view.test.tsx`
- Modify: `apps/web/src/features/assistant/chat-panel.tsx`
- Modify: `apps/web/src/types/api.ts`

**Interfaces:**
- Consumes: `ChatResponse`, endpoint Task 5.
- Produces: `ChartView`; `ChatPanel` hiển thị thêm biểu đồ và ghi chú phạm vi.

- [ ] **Step 1: Viết test**

```tsx
it("renders a line chart for a time series", async () => {
  render(<ChartView spec={{ type: "line", x: "BusinessDate", y: ["DoanhThu"] }} rows={timeSeries} />);

  expect(screen.getByRole("img", { name: /biểu đồ đường/i })).toBeInTheDocument();
});

it("renders a doughnut chart for shares", () => {
  render(<ChartView spec={{ type: "doughnut", x: "TenMon", y: ["TyTrong"] }} rows={shares} />);

  expect(screen.getByRole("img", { name: /biểu đồ tròn/i })).toBeInTheDocument();
});

it("renders no chart when the server sends none", () => {
  const { container } = render(<ChartView spec={null} rows={rows} />);

  expect(container).toBeEmptyDOMElement();
});

it("keeps the SQL detail collapsed by default", async () => {
  """FR-AI-08."""
  stubFetch(chatResponseWithSql);

  render(<ChatPanel />);
  fireEvent.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));

  const detail = await screen.findByText("Câu SQL đã chạy");
  expect(detail.closest("details")).not.toHaveAttribute("open");
});

it("always shows the scope note next to the answer", async () => {
  """FR-AI-07 and business rule 16."""
  stubFetch(chatResponseWithScope);

  render(<ChatPanel />);
  fireEvent.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));

  expect(await screen.findByText(/vw_ai_thungan/)).toBeInTheDocument();
});
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/web && pnpm test`
Expected: FAIL — `Cannot find module '@/features/assistant/chart-view'`

- [ ] **Step 3: Cài đặt**

Biểu đồ vẽ bằng SVG thuần, không thêm thư viện. Mục "Xem chi tiết" **thu gọn mặc định** (FR-AI-08).
Ghi chú phạm vi dữ liệu luôn hiển thị cạnh câu trả lời (business rule 16). Giao diện chat riêng theo
vai trò (FR-AI-01).

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/web && pnpm test`
Expected: PASS

- [ ] **Step 5: Chạy cổng kiểm tra đầy đủ**

Run: `UV_CACHE_DIR=/tmp/uv-cache make gate`
Expected: xanh. Commit: `feat(web): chart the assistant answers and keep the scope note visible`

---

## Kiểm chứng

| Cổng | Lệnh | Kỳ vọng |
| --- | --- | --- |
| Prompt theo vai trò | `pytest tests/modules/test_ai_prompt.py` | xanh |
| Sinh SQL + hạn mức + cache | `pytest tests/modules/test_ai_generator.py` | xanh |
| Thực thi trên tài khoản vai trò | `pytest tests/modules/test_ai_executor.py` | xanh |
| Diễn giải + biểu đồ | `pytest tests/modules/test_ai_interpreter.py` | xanh |
| Pipeline + nhật ký | `pytest tests/modules/test_ai_service.py` | xanh |
| Giao diện | `cd apps/web && pnpm test` | xanh |
| Toàn bộ | `make gate` | xanh |

## Rủi ro

- **Rò dữ liệu chéo vai trò** là rủi ro nghiêm trọng nhất. Ba lớp bảo vệ: prompt chỉ có một view,
  `guard` chặn mọi quan hệ ngoài view, và tài khoản CSDL chỉ có `GRANT SELECT` trên view đó. Cache
  **phải** có vai trò trong khoá.
- **Chất lượng SQL phụ thuộc model**: bộ few-shot lấy từ `data/eval` (Phase 7) — nếu bộ đó chưa xong
  thì dùng `questions.example.jsonl`, nhưng phải thay trước khi chạy thực nghiệm.
- **Chi phí LLM** (NFR-16): hạn mức ngày và cache là bắt buộc, không phải tối ưu hoá tuỳ chọn.
- **Nhà cung cấp LLM chưa cấu hình (Q6)**: API của nhà cung cấp chưa nằm trong allowlist mạng của
  sandbox. Cần bạn thêm domain, hoặc dùng provider sẵn có. Test dùng `FakeClient` nên không bị chặn.
- **Timeout 3 giây** (NFR-06) có thể chặt với truy vấn tổng hợp nặng trên 20.000 order. Nếu thấy hỏng
  nhiều, xem lại index của Phase 0 trước khi nới timeout — nới timeout là đổi yêu cầu, cần bạn đồng ý.
