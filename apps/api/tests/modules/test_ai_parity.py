"""Report parity: topic isolation and accountable provider usage."""

import httpx
import pytest

from app.core.errors import BusinessRuleError
from app.modules.ai.guard import validate_sql
from app.modules.ai.scope import views_for
from app.shared.roles import Role


def test_roles_expose_topic_sets_and_never_the_old_union_views():
    for role, prefix in [
        (Role.MANAGER, "quanly"),
        (Role.CASHIER, "thungan"),
        (Role.WAREHOUSE, "kho"),
    ]:
        views = views_for(role)
        assert len(views) > 1
        assert f"vw_ai_{prefix}" not in views
        assert all(view.startswith(f"vw_ai_{prefix}_") for view in views)
    assert "vw_ai_kho_suat" in views_for(Role.WAREHOUSE)


def test_guard_accepts_same_role_topic_join_but_rejects_cross_role():
    sql = (
        "SELECT a.MaOrder FROM vw_ai_thungan_order a "
        "JOIN vw_ai_thungan_hoadon b ON a.MaOrder=b.MaOrder"
    )
    assert "LIMIT 500" in validate_sql(sql, allowed_views=views_for(Role.CASHIER), max_rows=500)
    with pytest.raises(BusinessRuleError):
        validate_sql(
            "SELECT * FROM vw_ai_quanly_giavon", allowed_views=views_for(Role.CASHIER), max_rows=500
        )


@pytest.mark.anyio
async def test_provider_usage_records_actual_versions_tokens_cost_and_failed_fallback_attempts():
    from app.modules.ai import llm
    from app.modules.ai.usage import collect_usage

    def handler(request):
        import json

        model = json.loads(request.content)["model"]
        if model == "primary":
            return httpx.Response(503, json={"error": "down"})
        return httpx.Response(
            200,
            json={
                "model": "fallback-20261009",
                "usage": {"prompt_tokens": 1000, "completion_tokens": 200},
                "choices": [{"message": {"content": "SELECT 1"}}],
            },
        )

    client = llm.CommercialClient(
        api_key="test",
        model="primary",
        base_url="https://example.test",
        fallback_model="fallback",
        transport=httpx.MockTransport(handler),
    )
    with collect_usage(input_price=0.3, output_price=1.2) as usage:
        assert await llm.complete_async(client, "question") == "SELECT 1"
    assert usage.call_count == 2
    assert usage.input_tokens == 1000
    assert usage.output_tokens == 200
    assert usage.cost_usd == pytest.approx(0.00054)
    assert usage.models == ["primary", "fallback-20261009"]


def test_query_log_restricts_parent_deletion_and_has_required_usage_columns():
    from app.modules.ai.models import AssistantQuery

    table = AssistantQuery.__table__
    assert next(iter(table.c.MaPhien.foreign_keys)).ondelete == "RESTRICT"
    assert {"ModelPhienBan", "TokenDauVao", "TokenDauRa", "ChiPhiUSD", "SoLanGoi"} <= set(
        table.c.keys()
    )


@pytest.mark.anyio
async def test_execution_errors_share_the_two_generation_attempt_budget(
    session, seed_views, fake_llm
):
    from app.modules.ai.pipeline.generator import generate_sql

    fake_llm.reply_sequence(
        ["SELECT Missing FROM vw_ai_thungan_order", "SELECT MaOrder FROM vw_ai_thungan_order"]
    )
    executed = []

    async def execute(sql):
        executed.append(sql)
        if "Missing" in sql:
            raise RuntimeError("Unknown column")

    sql = await generate_sql(session, "đơn hôm nay", Role.CASHIER, validate_execution=execute)
    assert "MaOrder" in sql
    assert len(executed) == 2


@pytest.mark.anyio
async def test_execution_failure_on_both_attempts_is_refused(session, seed_views, fake_llm):
    from app.modules.ai.pipeline.generator import generate_sql

    fake_llm.reply("SELECT Missing FROM vw_ai_thungan_order")
    executed = []

    async def execute(sql):
        executed.append(sql)
        raise RuntimeError("Unknown column")

    with pytest.raises(BusinessRuleError):
        await generate_sql(session, "đơn hôm nay", Role.CASHIER, validate_execution=execute)
    assert len(executed) == 2


@pytest.mark.anyio
async def test_explicit_examples_cannot_inject_another_roles_schema(session, seed_views):
    from app.modules.ai.pipeline.prompt import build_prompt

    prompt = await build_prompt(
        session,
        "tồn kho",
        Role.WAREHOUSE,
        examples=[{"question": "doanh thu", "sql": "SELECT TongTien FROM vw_ai_quanly_hoadon"}],
    )
    assert "vw_ai_quanly_hoadon" not in prompt


def test_grant_template_matches_allowlists_exactly():
    import re
    from pathlib import Path

    template = (Path(__file__).parents[4] / "db/views/grants.sql.template").read_text()
    for role, account in [
        (Role.MANAGER, "manager"),
        (Role.CASHIER, "cashier"),
        (Role.WAREHOUSE, "warehouse"),
    ]:
        granted = set(
            re.findall(r"GRANT SELECT ON restaurant\.(\w+) TO 'ai_" + account + "'@'%'", template)
        )
        assert granted == views_for(role)


@pytest.mark.anyio
async def test_provider_failure_still_persists_attempt_without_claiming_exact_cost(
    session, seed_views, ai_engine, ai_runtime_store
):
    from sqlalchemy import select

    from app.modules.ai import llm
    from app.modules.ai.models import AssistantQuery
    from app.modules.ai.service import answer

    def handler(request):
        return httpx.Response(401, json={"error": "no"})

    llm.set_client(
        llm.CommercialClient(
            api_key="fixture",
            model="version-actual",
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        )
    )
    try:
        with pytest.raises(httpx.HTTPStatusError):
            await answer(session, "đơn?", Role.CASHIER, user_id=1)
        record = (await session.scalars(select(AssistantQuery))).one()
        assert record.call_count == 1
        assert record.model_version == "version-actual"
        assert record.cost_usd is None
        assert record.usage_detail["cost_complete"] is False
    finally:
        llm.set_client(None)


@pytest.mark.anyio
async def test_servings_are_fresh_aggregate_of_current_recipe_holds_and_eligible_lots(
    session, seed_views
):
    await assert_servings_fresh(session)


async def assert_servings_fresh(session):
    from datetime import date, datetime, timedelta

    from sqlalchemy import column, select, table

    from app.modules.catalog.models import Dish, Ingredient, Recipe, RecipeItem
    from app.modules.inventory.models import IngredientLot
    from app.modules.sales.models import Reservation, ReservationDetail
    from app.modules.settings.models import User
    from app.modules.settings.service import seed_reference_data

    await seed_reference_data(session)
    user = User(
        username="ai-warehouse",
        password_hash="unused",
        full_name="Bếp",
        role_id="WAREHOUSE",
        status="Hoạt động",
    )
    ingredient = Ingredient(name="NL-AI", unit="kg", stock_qty=100, min_stock=1)
    dish = Dish(name="Món AI", missing_recipe=False, manual_paused=False)
    session.add_all([user, ingredient, dish])
    await session.flush()
    recipe = Recipe(dish_id=dish.id, business_date=date(2000, 1, 1), status="Đang áp dụng")
    session.add(recipe)
    await session.flush()
    session.add(RecipeItem(recipe_id=recipe.id, ingredient_id=ingredient.id, quantity=2))
    lot = IngredientLot(ingredient_id=ingredient.id, quantity_remaining=10, status="Còn hạn")
    expired = IngredientLot(ingredient_id=ingredient.id, quantity_remaining=90, status="Hết hạn")
    session.add_all([lot, expired])
    await session.flush()
    now = datetime.now()
    hold = Reservation(
        selection_code="ai-fresh",
        user_id=user.id,
        dish_id=dish.id,
        recipe_id=recipe.id,
        quantity=1,
        expires_at=now + timedelta(days=1),
        status="Đang giữ",
    )
    session.add(hold)
    await session.flush()
    session.add(ReservationDetail(reservation_id=hold.id, lot_id=lot.id, quantity=2))
    await session.flush()
    view = table(
        "vw_ai_kho_suat",
        column("MaMon"),
        column("TenMon"),
        column("SoSuatKhaDung"),
        column("ThoiDiemTinh"),
    )

    async def servings():
        return await session.scalar(select(view.c.SoSuatKhaDung).where(view.c.MaMon == dish.id))

    assert await servings() == 4
    hold.expires_at = now - timedelta(days=1)
    await session.flush()
    assert await servings() == 5
    lot.quantity_remaining = 4
    await session.flush()
    assert await servings() == 2
    dish.manual_paused = True
    await session.flush()
    assert await servings() is None


@pytest.mark.anyio
async def test_timeout_attempt_is_counted_before_dispatch_and_fallback(monkeypatch):
    import threading

    from app.modules.ai import llm
    from app.modules.ai.usage import collect_usage

    monkeypatch.setenv("AI_LLM_TIMEOUT_SECONDS", "0.01")
    from app.core.config import get_settings

    get_settings.cache_clear()
    release = threading.Event()
    client = llm.CommercialClient(
        api_key="fixture",
        model="stalled",
        base_url="https://example.test",
        fallback_client=llm.FakeClient("SELECT 1"),
    )

    def stalled(model, prompt):
        release.wait(1)
        return "late"

    monkeypatch.setattr(client, "_post", stalled)
    try:
        with collect_usage(input_price=0.3, output_price=1.2) as usage:
            await llm.complete_async(client, "q")
            assert usage.call_count == 2
            assert usage.models[0] == "stalled"
            assert not usage.cost_complete
    finally:
        release.set()
