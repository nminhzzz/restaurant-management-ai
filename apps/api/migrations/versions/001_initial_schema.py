"""initial schema — 29 tables + indexes."""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Created from Base.metadata — order respects FK dependencies
    # Use raw DDL via op.execute(CreateTable(...).compile(dialect=mysql.dialect())) would be dialect-specific.
    # Instead emit op.create_table calls generated from metadata.
    import app.modules.ai.models  # noqa: F401
    import app.modules.catalog.models  # noqa: F401
    import app.modules.inventory.models  # noqa: F401
    import app.modules.sales.models  # noqa: F401
    import app.modules.settings.models  # noqa: F401
    import app.shared.audit  # noqa: F401
    from app.shared.base import Base

    # Create all tables from metadata
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    import app.modules.ai.models  # noqa: F401
    import app.modules.catalog.models  # noqa: F401
    import app.modules.inventory.models  # noqa: F401
    import app.modules.sales.models  # noqa: F401
    import app.modules.settings.models  # noqa: F401
    import app.shared.audit  # noqa: F401
    from app.shared.base import Base

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
