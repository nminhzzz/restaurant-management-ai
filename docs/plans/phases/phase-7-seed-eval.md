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

**Phụ thuộc:** Phase 0 (lược đồ) cho Task 1; **Phase 2, 3, 4 (service)** cho Task 2 — script seed gọi
`create_dish`/`assign_recipe`, `create_receipt`/`create_issue`/`create_stocktake`/`close_month` và
`submit_order`/`pay_cash`/`start_qr`; **Phase 6** cho Task 4 (harness). Không có đường tắt: ràng buộc
"sinh dữ liệu qua tầng service" ở dưới chính là thứ khiến phase này không thể bắt đầu sớm.

**Lộ trình:** `docs/plans/2026-09-24-master-roadmap.md` · **Nhánh:** `feat/phase-7-seed-eval`

## Ràng buộc chung

- Dữ liệu sinh ra phải **tôn trọng bất biến nghiệp vụ**: không tồn kho âm, FIFO đúng, Business Date
  06:00 → 06:00, trạng thái dòng món hợp lệ.
- **Gọi `seed_reference_data()` (Phase 1 Task 1 Step 0) trước mọi thứ khác.** Ba vai trò và dòng cấu
  hình singleton chưa bao giờ được seed ở phase nào khác; thiếu chúng thì FK `MaVaiTro` fail ngay
  dòng đầu tiên.
- Sinh dữ liệu **deterministic** theo seed: cùng seed cho cùng bộ dữ liệu (điều kiện để thực nghiệm
  lặp lại được).
- **Đồng hồ cắm được**: seed nhận `now` từ `SeedConfig`, không gọi `datetime.now()`. Test của phase
  này chạy trên `FIXED_NOW` của Phase 0 Task 0 (fixture `freeze_clock` autouse cắm seam
  `business_date.now`). Lý do phải cắm cả seam lẫn `SeedConfig`: nếu script gọi `datetime.now()` thì
  bộ dữ liệu sinh ra sẽ lệch ngày so với mọi test khác.
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
| `apps/api/tests/seed/conftest.py` | Fixture `seeded_reference`, `seeded_year` (chỉ thấy trong `tests/seed/`). |
| `apps/api/tests/eval/conftest.py` | Fixture `questions`, `one_question`, `refusal_question` (chỉ thấy trong `tests/eval/`). |

---

## Task 1: Khung sinh dữ liệu và danh mục nền

**Files:**
- Create: `scripts/seed/config.py`
- Create: `scripts/seed/catalog.py`
- Create: `scripts/seed/generate.py`
- Modify: `scripts/seed/README.md`
- Test: `apps/api/tests/seed/test_generator.py`

**Interfaces:**
- Consumes: Phase 1 service (`seed_reference_data`, `create_user`); Phase 2 service (`create_ingredient`,
  `create_dish`, `assign_recipe`, `create_table`).
- Produces: `SeedConfig` (dataclass: `seed`, `months`, `orders_target`, `now: datetime`);
  `build_catalogue(config) -> CataloguePlan` (**hàm thuần**, không chạm CSDL — đây là chỗ tính
  deterministic được kiểm chứng);
  `seed_catalog(session, config) -> CatalogIds` (persist `CataloguePlan` qua tầng service);
  `python scripts/seed/generate.py --seed 42 --months 12`.

**Vì sao tách `build_catalogue` khỏi `seed_catalog`:** muốn chứng minh "cùng seed cho cùng danh mục"
thì phải chạy hàm sinh **hai lần**. Chạy `seed_catalog` hai lần trên cùng một CSDL sẽ vướng unique
constraint (`TenMon`, `TenNhomMon`) ở lần thứ hai — test sẽ đỏ vì lý do không liên quan tới tính
deterministic, và dựng hai CSDL tạm chỉ để so tên là quá đắt. Hàm thuần vừa kiểm được điều cần kiểm,
vừa nhanh hơn nhiều lần.

- [ ] **Step 1: Viết test cho tính deterministic và quy mô**

```python
def test_the_same_seed_produces_the_same_catalogue():
    """Repeatable experiments need repeatable data."""
    first = build_catalogue(SeedConfig(seed=42, months=12))
    second = build_catalogue(SeedConfig(seed=42, months=12))

    assert first.dish_names == second.dish_names
    assert first.recipes == second.recipes


def test_a_different_seed_produces_a_different_catalogue():
    first = build_catalogue(SeedConfig(seed=42, months=12))
    second = build_catalogue(SeedConfig(seed=7, months=12))

    assert first.dish_names != second.dish_names


def test_the_catalogue_lands_in_the_ranges_the_report_describes():
    """Appendix 4: 60 to 80 dishes."""
    plan = build_catalogue(SeedConfig(seed=42, months=12))

    assert 60 <= len(plan.dish_names) <= 80
    assert len(plan.ingredient_names) >= 30
    assert len(plan.tables) >= 12


async def test_seeding_persists_exactly_what_was_planned(session, seeded_reference):
    """The pure plan and the database must not drift apart."""
    plan = build_catalogue(SeedConfig(seed=42, months=12))

    ids = await seed_catalog(session, SeedConfig(seed=42, months=12))

    assert sorted(ids.dish_names) == sorted(plan.dish_names)
    assert len(ids.dish_ids) == len(plan.dish_names)


async def test_every_dish_has_an_active_recipe_so_it_can_be_ordered(session, seeded_reference):
    ids = await seed_catalog(session, SeedConfig(seed=42, months=12))

    for dish_id in ids.dish_ids:
        assert await active_recipe(session, dish_id, today()) is not None


async def test_three_accounts_cover_the_three_roles(session, seeded_reference):
    ids = await seed_catalog(session, SeedConfig(seed=42, months=12))

    assert {user.role for user in ids.users} == {"MANAGER", "CASHIER", "WAREHOUSE"}
```

`seeded_reference` là fixture của `tests/seed/conftest.py`: gọi `seed_reference_data()` (Phase 1 Task 1
Step 0) trên session đang mở. Không có nó thì FK `MaVaiTro` fail trước khi test chạy được dòng nào.

- [ ] **Step 2: Chạy test cho đỏ**

Run: `cd apps/api && ./.venv/bin/pytest tests/seed/test_generator.py -v`
Expected: FAIL — `ModuleNotFoundError: scripts.seed.config`

- [ ] **Step 3: Cài đặt**

`generate.py` là entrypoint mỏng: đọc tham số dòng lệnh, mở session, gọi `seed_reference_data()` rồi
`seed_catalog` và `seed_operations`, in tiến độ. `config.py` giữ các hằng số phân phối ở **một** chỗ để
thực nghiệm điều chỉnh được. Mọi ngẫu nhiên đi qua `random.Random(config.seed)` — **không** dùng
`random` toàn cục.

`build_catalogue(config)` là hàm thuần: chỉ đọc `config` và một `random.Random(config.seed)`, không
mở session, không gọi service. `seed_catalog(session, config)` lấy `CataloguePlan` từ nó rồi gọi
`create_ingredient`/`create_dish`/`assign_recipe`/`create_table` để persist. Nhờ vậy tính deterministic
kiểm được mà không cần CSDL, còn ràng buộc "dữ liệu tôn trọng bất biến" vẫn được giữ vì mọi thao tác
ghi đều đi qua service.

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
  `daily_order_count(config, day) -> int`; `hour_weight(hour) -> float`;
  `dish_order_counts(config, days) -> dict[str, int]`;
  `ingredient_total`/`lot_total`/`ledger_total`/`negative_stock_count`/`lot_cache_mismatch_count`/
  `ledger_mismatch_count`/`order_status_counts`/`order_count_between` (helper đọc của Phase 0 Task 0).
  Fixture `seeded_year` (dựng 12 tháng) nằm ở `tests/seed/conftest.py`; `tests/seed/test_orders.py`
  khai báo `pytestmark = pytest.mark.slow` ở đầu file để cả nhóm không chạy trong `make gate`.

- [ ] **Step 1: Viết test cho các đặc trưng phân phối**

Bốn test đầu là **hàm thuần** (chỉ đọc `config`, không chạm CSDL) nên chạy nhanh; bốn test sau cần
`seeded_year`. Đặt `pytestmark = pytest.mark.slow` ở đầu file để cả nhóm bị loại khỏi `make gate`, và
chạy riêng bằng `./.venv/bin/pytest tests/seed/test_orders.py -m slow`.

```python
def test_the_day_has_two_peaks():
    """Appendix 4: lunch and dinner peaks."""
    lunch = hour_weight(12) + hour_weight(13)
    afternoon = hour_weight(15) + hour_weight(16)

    assert lunch > afternoon
    assert hour_weight(19) > afternoon


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
  Fixture `questions` (đọc `data/eval/questions.jsonl`) khai báo ở **`tests/eval/conftest.py`** —
  không phải `tests/seed/conftest.py`, vì pytest chỉ nạp `conftest.py` của thư mục cha của file test.
  Nếu file chưa tồn tại, fixture **fail** với thông báo trỏ về Step 3 — không trả danh sách rỗng, vì
  danh sách rỗng sẽ khiến `test_the_set_has_between_fifty_and_one_hundred_questions` đỏ vì lý do sai.

- [ ] **Step 1: Viết test kiểm tra bộ dữ liệu**

```python
def test_the_set_has_between_fifty_and_one_hundred_questions(questions):
    assert 50 <= len(questions) <= 100


def test_every_difficulty_tier_is_represented(questions):
    """Appendix 4: three tiers."""
    tiers = Counter(question["difficulty"] for question in questions)

    assert set(tiers) == {"easy", "medium", "hard"}
    assert all(count >= 10 for count in tiers.values())


def test_every_role_has_questions(questions):
    roles = Counter(question["role"] for question in questions)

    assert set(roles) == {"MANAGER", "CASHIER", "WAREHOUSE"}


def test_each_question_names_the_view_its_sql_must_use(questions):
    for question in questions:
        assert question["view"] == ROLE_VIEWS[Role(question["role"])]


def test_every_reference_sql_passes_the_guard(questions):
    """If the reference SQL cannot run, it is not a valid reference."""
    for question in questions:
        guard.validate_sql(
            question["sql"],
            allowed_views=views_for(Role(question["role"])),
            max_rows=500,
        )


def test_no_reference_sql_touches_a_core_table(questions):
    """String matching would be fooled by a column named after a table; parse instead."""
    for question in questions:
        tables = {table.name for table in sqlglot.parse_one(question["sql"]).find_all(sqlglot.exp.Table)}

        assert tables <= set(ROLE_VIEWS.values())


def test_the_set_includes_cross_role_cases_expected_to_be_refused(questions):
    """FR-AI-05: the set also proves the assistant stays in its lane."""
    refused = [q for q in questions if q["notes"] and "vượt quyền" in q["notes"]]

    assert len(refused) >= 5


def test_questions_are_unique_and_numbered(questions):
    ids = [question["id"] for question in questions]

    assert len(set(ids)) == len(ids)
    assert ids == [f"Q{index:03d}" for index in range(1, len(ids) + 1)]


def test_vietnamese_diacritics_are_kept_intact(questions):
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
- Create: `data/__init__.py`, `data/eval/__init__.py` (rỗng — để `data.eval.harness` import được)
- Modify: `apps/api/pyproject.toml` (`pythonpath` để test import được `data.eval.harness`)
- Modify: `data/eval/README.md`
- Test: `apps/api/tests/eval/test_harness.py`

**Interfaces:**
- Consumes: Phase 6 pipeline (`pipeline.normalize.normalize_question`, `pipeline.prompt.build_prompt`,
  `pipeline.generator.generate_sql`), `questions.jsonl`.
- Produces: `Config` (A: chỉ lược đồ; B: thêm few-shot + chuẩn hóa; C: cấu hình B trên model khác);
  `run_configuration(config, questions) -> ConfigResult` (dataclass: `config`, `execution_accuracy`,
  `error_rate`, `refusal_rate`, `mean_latency_ms`, `failures: list[Failure]`);
  `compare(results) -> ComparisonTable` (`.rows` là một dòng mỗi cấu hình);
  `run_harness(config, questions, out) -> None`;
  `python data/eval/harness.py --configs A,B,C --out results.json`.

`Config` là một `enum` **có mang dữ liệu**, không phải ba hằng số rời: mỗi giá trị phải trả lời được
`model_for(config)`, `uses_examples(config)`, `normalises(config)`. Test ở Step 1 gọi cả ba hàm này,
nên chúng thuộc phần "Produces" chứ không phải chi tiết nội bộ.

`fake_llm` là fixture của Phase 0 Task 0; nó ghi lại `last_prompt`, `last_model` và đếm `calls` —
harness phải đi qua `get_client()` của Phase 6 để `monkeypatch` bắt được nó.

Fixture `one_question` (một bản ghi `questions.jsonl`) và `refusal_question` (một câu `vượt quyền`)
khai báo ở `tests/eval/conftest.py`.

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

`data/` nằm ngoài `apps/api`, nên `from data.eval.harness import run_configuration` chỉ chạy được khi
gốc repo có trên `sys.path`. Thêm hai file `__init__.py` rỗng (`data/`, `data/eval/`) và một dòng vào
`apps/api/pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["../.."]  # so `import data.eval.harness` resolves from tests/
```

Khi chạy tay thì `sys.path[0]` là `data/eval/`, nên `import data...` không resolve — chạy bằng đường
dẫn file, không dùng `-m`:

`cd apps/api && ./.venv/bin/python ../../data/eval/harness.py --configs A,B,C --out ../../docs/eval-results.json`

(`app.*` vẫn import được vì `uv sync` cài package `app` ở chế độ editable.)

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

Run: `./scripts/apply_grants.sh`
Expected: ba tài khoản chỉ-đọc sẵn sàng. Script lấy mật khẩu từ biến môi trường; mật khẩu không nằm
trong repo (Phase 0 Task 7).

- [ ] **Step 3: Chạy ba cấu hình**

Run: `cd apps/api && ./.venv/bin/python ../../data/eval/harness.py --configs A,B,C --out ../../docs/eval-results.json`
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
| Order 12 tháng | `pytest tests/seed/test_orders.py -m slow` | xanh (đã loại khỏi `make gate`) |
| Bộ câu hỏi hợp lệ | `pytest tests/eval/test_questions.py` | xanh |
| Harness A/B/C | `pytest tests/eval/test_harness.py` | xanh |
| Dữ liệu thật | `make seed` rồi kiểm tra tồn kho âm | 0 dòng âm |
| Thực nghiệm | `cd apps/api && ./.venv/bin/python ../../data/eval/harness.py` | có bảng chỉ số |
| Toàn bộ | `make gate` | xanh |

## Rủi ro

- **Sinh dữ liệu qua service sẽ chậm** (20.000 order, mỗi order vài truy vấn). Chấp nhận được vì chạy
  một lần; nếu quá lâu thì gộp theo lô và tắt audit log trong lúc seed — nhưng **không** bỏ qua tầng
  service, vì như vậy dữ liệu sẽ vi phạm bất biến và làm hỏng chính thực nghiệm. Test `seeded_year`
  nằm trong nhóm `slow` (Task 2 Step 1) để `make gate` không kéo dài thêm mỗi lần commit.
- **Thứ tự phụ thuộc bị đảo**: phase này gọi service của Phase 2/3/4, nên **không** bắt đầu được ngay
  sau Phase 0 như bảng phụ thuộc cũ ghi. Nếu ai đó cố chạy Task 2 sớm, `ImportError` ở
  `create_receipt` là dấu hiệu đúng, không phải lỗi cần workaround.
- **Quên `seed_reference_data()`** thì lỗi đầu tiên là FK `MaVaiTro`, không phải thông báo dễ hiểu.
  Fixture `seeded_reference` tồn tại để chuyện đó không xảy ra trong test.
- **Thời gian chạy thực nghiệm A/B/C** tốn tiền gọi LLM. Chạy trên bộ 75 câu × 3 cấu hình = 225 lượt;
  dùng cache của NFR-16 và chạy ngoài giờ cao điểm.
- **Cấu hình C cần chốt model (Q5)**: Ollama chưa cài trên máy này. Nếu không cài được, dùng một model
  thương mại thứ hai làm cấu hình C — nhưng phải ghi rõ trong báo cáo để không hiểu sai là "mô hình
  nguồn mở tại chỗ".
- **Bộ câu hỏi do chính nhóm soạn** có thể thiên vị theo cách nhóm hiểu dữ liệu. Phụ lục 4 đã yêu cầu
  tách người soạn SQL khỏi người thiết kế prompt và đo tỷ lệ đồng thuận — làm đúng quy trình đó.
- **Số liệu thực nghiệm có thể không đạt mục tiêu 80%/55%.** Đó là kết quả, không phải lỗi — báo cáo
  phải ghi đúng số đo được kèm phân tích nguyên nhân, không chỉnh số.
