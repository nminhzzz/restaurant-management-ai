"""Audit and AI query logs are append-only at the MySQL layer (NFR-08)."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_audit_and_ai_triggers_exist(mysql_engine_factory, mysql_seed_views) -> None:
    engine = mysql_engine_factory()
    try:
        async with engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(
                        "SELECT TRIGGER_NAME FROM information_schema.TRIGGERS "
                        "WHERE TRIGGER_SCHEMA = DATABASE() "
                        "AND EVENT_OBJECT_TABLE IN ('NHAT_KY_HE_THONG', 'TRUY_VAN_AI')"
                    )
                )
            ).scalars()
            names = set(rows.all())
    finally:
        await engine.dispose()

    assert names == {
        "trg_NHAT_KY_HE_THONG_no_update",
        "trg_NHAT_KY_HE_THONG_no_delete",
        "trg_TRUY_VAN_AI_no_update",
        "trg_TRUY_VAN_AI_no_delete",
    }


@pytest.mark.asyncio
async def test_an_audit_row_cannot_be_updated(mysql_engine_factory) -> None:
    engine = mysql_engine_factory()
    try:
        with pytest.raises(OperationalError):
            async with engine.begin() as conn:
                await conn.execute(
                    text(
                        "INSERT INTO NHAT_KY_HE_THONG "
                        "(LoaiThaoTac, DoiTuong, MaDoiTuong) "
                        "VALUES ('TEST', 'ORDER', '1')"
                    )
                )
                await conn.execute(
                    text(
                        "UPDATE NHAT_KY_HE_THONG SET LoaiThaoTac = 'CHANGED' "
                        "WHERE LoaiThaoTac = 'TEST'"
                    )
                )
    finally:
        await engine.dispose()
