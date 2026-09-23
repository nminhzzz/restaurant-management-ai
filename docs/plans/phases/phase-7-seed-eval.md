# Phase 7 — Dữ liệu mô phỏng và đánh giá thực nghiệm

> **Cho người thực thi:** dùng skill `executing-plans` để chạy kế hoạch này theo từng task.

**Mục tiêu:** Script sinh dữ liệu 12 tháng (≥ 20.000 order), bộ 50–100 câu hỏi tiếng Việt – SQL chuẩn
phân tầng ba mức khó, và harness chạy ba cấu hình đối chứng A/B/C để lấy số liệu cho Chương 4.

**Kiến trúc:** `scripts/seed/` sinh dữ liệu **qua tầng service** của các module, không chèn thẳng
bằng SQL — nhờ vậy dữ liệu tôn trọng mọi bất biến nghiệp vụ (FIFO, Business Date, trạng thái món,
`GIAO_DICH_KHO` khớp ba tầng tồn kho). `data/eval/` giữ bộ câu hỏi; harness chạy qua đúng pipeline
của Phase 6.

**Spec:** báo cáo Phụ lục 4 (dữ liệu thử nghiệm và phương pháp đánh giá), §1.5 (phân công), §4.2
(chỉ số và mục tiêu), NFR-03, NFR-16.

**Phụ thuộc:** Phase 0 (lược đồ) để bắt đầu; phần đánh giá cần Phase 6.
**Lộ trình:** `docs/plans/2026-09-24-master-roadmap.md` · **Nhánh:** `feat/phase-7-seed-eval`

## Ràng buộc chung

- Dữ liệu sinh ra phải **tôn trọng bất biến nghiệp vụ**: không tồn kho âm, FIFO đúng, Business Date
  06:00 → 06:00, trạng thái dòng món hợp lệ.
- Sinh dữ liệu **deterministic** theo seed: cùng seed cho cùng bộ dữ liệu (điều kiện để thực nghiệm
  lặp lại được).
- Người soạn SQL chuẩn **không** đồng thời thiết kế prompt (Phụ lục 4).
- Bộ đánh giá phải có cả **ca hỏi vượt quyền** và kỳ vọng bị từ chối (FR-AI-05).
- Mỗi câu hỏi ghi rõ `view` mà SQL chuẩn phải tham chiếu.
- `make gate` xanh trước khi kết thúc mỗi task.

## Cấu trúc file

| File | Trách nhiệm |
| --- | --- |
| `scripts/seed/generate.py` | Entrypoint `make seed` gọi. |
| `scripts/seed/config.py` | Tham số phân phối: hai đỉnh trong ngày, mùa vụ, luật lũy thừa. |
| `scripts/seed/catalog.py` | Sinh danh mục: nhóm món, món, công thức, nguyên liệu, NCC, bàn. |
| `scripts/seed/operations.py` | Sinh order, thanh toán, nhập/xuất kho, kiểm kê. |
| `data/eval/questions.jsonl` | Bộ câu hỏi chính thức. |
| `data/eval/harness.py` | Chạy ba cấu hình A/B/C, xuất bảng chỉ số. |
| `data/eval/README.md` | Đặc tả định dạng (đã có) — bổ sung cách chạy. |
| `apps/api/tests/seed/test_generator.py` | Test bất biến của dữ liệu sinh ra. |

---

## Task 1: Khung sinh dữ liệu và danh mục nền

**Files:**
- Create: `scripts/seed/config.py`
- Create: `scripts/seed/catalog.py`
- Create: `scripts/seed/generate.py`
- Modify: `scripts/seed/README.md`
- Test: `apps/api/tests/seed/test_generator.py`

**Interfaces:**
- Consumes: Phase 2 service (`create_ingredient`, `create_dish`, `assign_recipe`, `create_table`);
  Phase 1 service (`create_user`) để tạo ba tài khoản.
- Produces: `SeedConfig` (dataclass: seed, months, orders_target);
  `seed_catalog(session, config) -> CatalogIds`;
  `python scripts/seed/generate.py --seed 42 --months 12`.

- [ ] **Step 1: Viết test cho tính deterministic và quy mô**

```python
async def test_the_same_seed_produces_the_same_catalogue(session_factory):
    """Repeatable experiments need repeatable data."""
    first = await seed_catalog(session_factory(), SeedConfig(seed=42, months=12))
    second = await seed_catalog(session_factory(), SeedConfig(seed=42, months=12))

    assert first.dish_names == second.dish_names


async def test_a_different_seed_produces_a_different_catalogue(session_factory):
    first = await seed_catalog(session_factory(), SeedConfig(seed=42, months=12))
    second = await seed_catalog(session_factory(), SeedConfig(seed=7, months=12))

    assert first.dish_names != second.dish_names


async def test_the_catalogue_lands_in_the_ranges_the_report_describes(session_factory):
    """Appendix 4: 60 to 80 dishes."""
    ids = await seed_catalog(session_factory(), SeedConfig(seed=42, months=12))

    assert 60 <= len(ids.dish_names) <= 80
    assert len(ids.ingredient_names) >= 30
    assert len(ids.table_ids) >= 12


async def test_every_dish_has_an_active_recipe_so_it_can_be_ordered(session_factory):
    ids = await seed_catalog(session_factory(), SeedConfig(seed=42, months=12))

    for dish_id in ids.dish_ids:
        assert await active_recipe(session, dish_id, today()) is not None


async def test_three_accounts_cover_the_three_roles(session_factory):
    ids = await seed_catalog(session_factory(), SeedConfig(seed=42, months=12))

    assert {user.role for user in ids.users} == {"MANAGER", "CASHIER", "WAREHOUSE"}
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/seed/test_generator.py -v`
Expected: FAIL — `ModuleNotFoundError: scripts.seed.config`

- [ ] **Step 3: Cài đặt**

`generate.py` là entrypoint mỏng: đọc tham số dòng lệnh, mở session, gọi `seed_catalog` rồi
`seed_operations`, in tiến độ. `config.py` giữ các hằng số phân phối ở **một** chỗ để thực nghiệm
điều chỉnh được. Mọi ngẫu nhiên đi qua `random.Random(config.seed)` — **không** dùng `random` toàn cục.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/seed/test_generator.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(seed): generate the catalogue deterministically`

---

## Task 2: Sinh order 12 tháng theo đặc trưng ngành (NFR-03)

**Files:**
- Create: `scripts/seed/operations.py`
- Modify: `scripts/seed/generate.py`
- Modify: `scripts/seed/README.md`
- Test: `apps/api/tests/seed/test_orders.py`

**Interfaces:**
- Consumes: Task 1; Phase 4 service (`submit_order`, `pay_cash`, `start_qr`, `expire_stale_qr`);
  Phase 3 service (`create_receipt`, `create_issue`, `create_stocktake`, `close_month`).
- Produces: `seed_operations(session, config, ids) -> SeedSummary`;
  `daily_order_count(config, day) -> int`; `hour_for(config, day, rng) -> int`.

- [ ] **Step 1: Viết test cho các đặc trưng phân phối**

```python
def test_the_day_has_two_peaks():
    """Appendix 4: lunch and dinner peaks."""
    lunch = sum(hour_weight(12) + hour_weight(13) for _ in [0])
    afternoon = sum(hour_weight(15) + hour_weight(16) for _ in [0])

    assert lunch > afternoon


def test_weekends_are_busier_than_weekdays():
    saturday = daily_order_count(config, date(2026, 9, 26))  # Saturday
    tuesday = daily_order_count(config, date(2026, 9, 22))  # Tuesday

    assert saturday > tuesday


def test_the_monthly_volume_reaches_the_nfr_03_floor():
    """NFR-03: at least 20.000 orders a year."""
    total = sum(
        daily_order_count(config, date(2026, 1, 1) + timedelta(days=offset))
        for offset in range(365)
    )

    assert total >= 20_000


def test_a_few_dishes_take_most_of_the_orders():
    """Appendix 4: a power-law distribution, not a flat one."""
    counts = dish_order_counts(config, days=30)

    top_ten = sum(sorted(counts.values(), reverse=True)[:10])
    assert top_ten > sum(counts.values()) * 0.5


async def test_generated_orders_respect_business_invariants(session, seeded_year):
    """The generator must not invent states the services would refuse."""
    assert await negative_stock_count(session) == 0
    assert await lot_cache_mismatch_count(session) == 0
    assert await ledger_mismatch_count(session) == 0


async def test_the_three_tiers_agree_after_a_full_year(session, seeded_year):
    for ingredient_id in await ingredient_ids(session):
        total = await ingredient_total(session, ingredient_id)
        lots = await lot_total(session, ingredient_id)
        ledger = await ledger_total(session, ingredient_id)
        assert total == lots == ledger


async def test_every_order_has_a_plausible_final_state(session, seeded_year):
    statuses = await order_status_counts(session)

    assert set(statuses) <= {
        "Đã thanh toán", "Chờ đối soát", "Tranh chấp", "Đã hủy", "Tự động đóng",
    }


async def test_orders_land_on_both_sides_of_the_0600_boundary(session, seeded_year):
    """A generator that only emits daytime orders would hide timezone bugs."""
    early = await order_count_between(session, time(0, 0), time(5, 59))
    late = await order_count_between(session, time(18, 0), time(23, 59))

    assert early > 0
    assert late > 0
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/seed/test_orders.py -v`
Expected: FAIL — `ModuleNotFoundError: scripts.seed.operations`

- [ ] **Step 3: Cài đặt**

Trọng số giờ: hai đỉnh quanh 11–13h và 18–20h, đáy 15–16h. Trọng số ngày: cuối tuần ×1,6. Mùa vụ
theo tháng (thấp sau Tết, cao dịp lễ cuối năm). Phân bố món: `weight ∝ 1/rank^1,2`. Mỗi order đi
**qua `submit_order()`** để trừ kho đúng FIFO, rồi thanh toán (`pay_cash` ~70%, QR ~30%), và một tỉ lệ
nhỏ để `Chờ đối soát` / `Tranh chấp` / `Đã hủy` để Phase 5 có dữ liệu cho FR-REP-02 và FR-REP-10.
Nhập kho định kỳ 2–3 lần/tuần để tồn không cạn; xuất thủ công và kiểm kê rải rác.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/seed/test_orders.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(seed): generate twelve months of orders with realistic patterns`

---

## Task 3: Soạn bộ câu hỏi – SQL chuẩn (đóng góp khoa học)

**Files:**
- Create: `data/eval/questions.jsonl`
- Create: `apps/api/tests/eval/test_questions.py`
- Modify: `data/eval/README.md`

**Interfaces:**
- Consumes: `guard.validate_sql`, `scope.views_for`.
- Produces: bộ 50–100 bản ghi theo định dạng đã đặc tả ở `data/eval/README.md`.

- [ ] **Step 1: Viết test kiểm tra bộ dữ liệu**

```python
def test_the_set_has_between_fifty_and_one_hundred_questions():
    assert 50 <= len(questions) <= 100


def test_every_difficulty_tier_is_represented():
    """Appendix 4: three tiers."""
    tiers = Counter(question["difficulty"] for question in questions)

    assert set(tiers) == {"easy", "medium", "hard"}
    assert all(count >= 10 for count in tiers.values())


def test_every_role_has_questions():
    roles = Counter(question["role"] for question in questions)

    assert set(roles) == {"MANAGER", "CASHIER", "WAREHOUSE"}


def test_each_question_names_the_view_its_sql_must_use():
    for question in questions:
        assert question["view"] == ROLE_VIEWS[Role(question["role"])]


def test_every_reference_sql_passes_the_guard():
    """If the reference SQL cannot run, it is not a valid reference."""
    for question in questions:
        guard.validate_sql(
            question["sql"],
            allowed_views=views_for(Role(question["role"])),
            max_rows=500,
        )


def test_no_reference_sql_touches_a_core_table():
    for question in questions:
        assert not any(
            table in question["sql"]
            for table in ("HOA_DON ", "NGUOI_DUNG", "NGUYEN_LIEU ", "ORDER ")
        )


def test_the_set_includes_cross_role_cases_expected_to_be_refused():
    """FR-AI-05: the set also proves the assistant stays in its lane."""
    refused = [q for q in questions if q["notes"] and "vượt quyền" in q["notes"]]

    assert len(refused) >= 5


def test_questions_are_unique_and_numbered():
    ids = [question["id"] for question in questions]

    assert len(set(ids)) == len(ids)
    assert ids == [f"Q{index:03d}" for index in range(1, len(ids) + 1)]


def test_vietnamese_diacritics_are_kept_intact():
    """A normaliser that strips diacritics would lose meaning on food names."""
    for question in questions:
        assert question["question"] == unicodedata.normalize("NFC", question["question"])
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/eval/test_questions.py -v`
Expected: FAIL — `data/eval/questions.jsonl` chưa tồn tại

- [ ] **Step 3: Soạn bộ câu hỏi**

Phân bổ đề xuất (tổng 75):

| Mức | Số câu | Dạng |
| --- | --- | --- |
| `easy` | 25 | một bảng, một điều kiện, `COUNT`/`SUM`/`WHERE` đơn giản |
| `medium` | 30 | `GROUP BY`, `ORDER BY` + `LIMIT`, lọc theo khoảng Business Date, join trong cùng view |
| `hard` | 20 | nhiều tầng tổng hợp, so sánh hai kỳ, xếp hạng, tính tỉ trọng |

Theo vai trò: `MANAGER` 35, `CASHIER` 20, `WAREHOUSE` 20. Trong đó **≥ 5 câu cố tình hỏi vượt quyền**
(ghi rõ ở `notes`) để kiểm chứng FR-AI-05.

Quy trình (Phụ lục 4): người soạn SQL **không** đồng thời thiết kế prompt. Trên 15–20 câu ngẫu nhiên,
cả ba thành viên độc lập soạn SQL rồi đối chiếu, ghi lại tỷ lệ đồng thuận.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/eval/test_questions.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(eval): add the Vietnamese Text-to-SQL benchmark set`

---

## Task 4: Harness ba cấu hình đối chứng A/B/C

**Files:**
- Create: `data/eval/harness.py`
- Modify: `data/eval/README.md`
- Test: `apps/api/tests/eval/test_harness.py`

**Interfaces:**
- Consumes: Phase 6 pipeline, `questions.jsonl`.
- Produces: `Config` (A: chỉ lược đồ; B: thêm few-shot + chuẩn hóa; C: cấu hình B trên model khác);
  `run_configuration(config, questions) -> ConfigResult`;
  `compare(results) -> ComparisonTable`;
  `python data/eval/harness.py --configs A,B,C --out results.json`.

- [ ] **Step 1: Viết test**

```python
async def test_configuration_a_sends_no_examples(fake_llm, one_question):
    """A is the schema-only baseline."""
    await run_configuration(Config.A, [one_question])

    assert "Ví dụ" not in fake_llm.last_prompt


async def test_configuration_b_sends_examples_and_normalises(fake_llm, one_question):
    """B adds few-shot examples and Vietnamese normalisation."""
    await run_configuration(Config.B, [one_question])

    assert "Ví dụ" in fake_llm.last_prompt
    assert normalize_question(one_question.question) in fake_llm.last_prompt


async def test_configuration_c_uses_a_different_model(fake_llm, one_question):
    await run_configuration(Config.C, [one_question])

    assert fake_llm.last_model != await model_for(Config.B)


async def test_execution_accuracy_counts_rows_not_sql_text(fake_llm, one_question):
    """Two different queries returning the same table are both correct."""
    fake_llm.reply("SELECT COUNT(*) AS n FROM vw_ai_kho")

    result = await run_configuration(Config.A, [one_question])

    assert result.execution_accuracy == 1.0


async def test_the_four_metrics_of_appendix_4_are_reported(fake_llm, questions):
    result = await run_configuration(Config.A, questions)

    assert result.execution_accuracy >= 0
    assert result.error_rate >= 0
    assert result.refusal_rate >= 0
    assert result.mean_latency_ms >= 0


async def test_cross_role_questions_count_as_correct_refusals(fake_llm, refusal_question):
    """FR-AI-05: refusing is the right answer here."""
    fake_llm.reply_sequence(["SELECT * FROM hoa_don", "SELECT * FROM hoa_don"])

    result = await run_configuration(Config.A, [refusal_question])

    assert result.refusal_rate == 1.0


async def test_the_comparison_table_has_one_row_per_configuration(fake_llm, questions):
    results = [await run_configuration(config, questions) for config in Config]

    assert len(compare(results).rows) == 3


async def test_the_harness_writes_a_result_file(fake_llm, questions, tmp_path):
    await run_harness(Config.A, questions, out=tmp_path / "results.json")

    assert json.loads((tmp_path / "results.json").read_text())["config"] == "A"
```

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/eval/test_harness.py -v`
Expected: FAIL — `ModuleNotFoundError: data.eval.harness`

- [ ] **Step 3: Cài đặt**

Bốn chỉ số theo Phụ lục 4: **độ chính xác thực thi** (so kết quả trả về với SQL chuẩn, không so chuỗi
SQL), **tỷ lệ SQL lỗi**, **tỷ lệ từ chối**, **thời gian phản hồi trung bình**. Harness chạy qua
**đúng pipeline Phase 6**, dùng `FakeClient` trong test và client thật khi chạy thực nghiệm.

Mục tiêu ở §4.2: độ chính xác ≥ 80% (dễ/trung bình) và ≥ 55% (khó); phản hồi < 8 giây/câu.

- [ ] **Step 4: Chạy test cho xanh**

Run: `cd apps/api && ./.venv/bin/pytest tests/eval/test_harness.py -v`
Expected: PASS

- [ ] **Step 5: Kiểm tra kiểu, lint, commit**

Run: `cd apps/api && ./.venv/bin/ruff format . && ./.venv/bin/ruff check . && ./.venv/bin/mypy .`
Expected: xanh. Commit: `feat(eval): run the three benchmark configurations`

---

## Task 5: Chạy thực nghiệm và tổng hợp số liệu

**Files:**
- Create: `docs/eval-results.md`
- Modify: `data/eval/README.md`

**Interfaces:**
- Consumes: Task 2 (dữ liệu), Task 3 (bộ câu hỏi), Task 4 (harness).
- Produces: bảng số liệu ba cấu hình để đưa vào §4.2 của báo cáo.

- [ ] **Step 1: Nạp dữ liệu mô phỏng**

Run: `make db-up && make migrate && make seed`
Expected: ≥ 20.000 order trong 12 tháng, không lỗi bất biến.

- [ ] **Step 2: Áp view và tài khoản chỉ-đọc**

Run: `docker compose exec -T db mysql -uroot -p*** restaurant < db/views/grants.sql`
Expected: ba tài khoản chỉ-đọc sẵn sàng.

- [ ] **Step 3: Chạy ba cấu hình**

Run: `python data/eval/harness.py --configs A,B,C --out docs/eval-results.json`
Expected: một dòng kết quả cho mỗi cấu hình.

- [ ] **Step 4: Ghi kết quả vào tài liệu**

Tạo `docs/eval-results.md` với: bảng bốn chỉ số × ba cấu hình, phân tích theo mức độ khó, danh sách
câu hỏi thất bại kèm nguyên nhân, và phần đối chiếu với mục tiêu ở §4.2. Ghi rõ **ngày chạy, model,
seed** để lần sau lặp lại được.

- [ ] **Step 5: Chạy cổng kiểm tra đầy đủ và commit**

Run: `UV_CACHE_DIR=/tmp/uv-cache make gate`
Expected: xanh. Commit: `docs(eval): record the benchmark results of the three configurations`

---

## Kiểm chứng

| Cổng | Lệnh | Kỳ vọng |
| --- | --- | --- |
| Danh mục sinh ra | `pytest tests/seed/test_generator.py` | xanh |
| Order 12 tháng | `pytest tests/seed/test_orders.py` | xanh |
| Bộ câu hỏi hợp lệ | `pytest tests/eval/test_questions.py` | xanh |
| Harness A/B/C | `pytest tests/eval/test_harness.py` | xanh |
| Dữ liệu thật | `make seed` rồi kiểm tra tồn kho âm | 0 dòng âm |
| Thực nghiệm | `python data/eval/harness.py` | có bảng chỉ số |
| Toàn bộ | `make gate` | xanh |

## Rủi ro

- **Sinh dữ liệu qua service sẽ chậm** (20.000 order, mỗi order vài truy vấn). Chấp nhận được vì chạy
  một lần; nếu quá lâu thì gộp theo lô và tắt audit log trong lúc seed — nhưng **không** bỏ qua tầng
  service, vì như vậy dữ liệu sẽ vi phạm bất biến và làm hỏng chính thực nghiệm.
- **Thời gian chạy thực nghiệm A/B/C** tốn tiền gọi LLM. Chạy trên bộ 75 câu × 3 cấu hình = 225 lượt;
  dùng cache của NFR-16 và chạy ngoài giờ cao điểm.
- **Cấu hình C cần chốt model (Q5)**: Ollama chưa cài trên máy này. Nếu không cài được, dùng một model
  thương mại thứ hai làm cấu hình C — nhưng phải ghi rõ trong báo cáo để không hiểu sai là "mô hình
  nguồn mở tại chỗ".
- **Bộ câu hỏi do chính nhóm soạn** có thể thiên vị theo cách nhóm hiểu dữ liệu. Phụ lục 4 đã yêu cầu
  tách người soạn SQL khỏi người thiết kế prompt và đo tỷ lệ đồng thuận — làm đúng quy trình đó.
- **Số liệu thực nghiệm có thể không đạt mục tiêu 80%/55%.** Đó là kết quả, không phải lỗi — báo cáo
  phải ghi đúng số đo được kèm phân tích nguyên nhân, không chỉnh số.
