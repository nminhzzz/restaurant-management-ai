"""TRUY_VAN_AI.PhamViDuLieu stores the list of views a query read (document 04 F.29).

The column held a single family label (VARCHAR(50), e.g. "vw_ai_thungan"). It becomes JSON, an
array of the topic views the generated SQL actually referenced. Existing labels are kept as a
one-element array. The table is append-only, so its UPDATE trigger is dropped only while the
values are converted and is recreated afterwards, even if the conversion fails.

Downgrade keeps the first view of each array (empty arrays become NULL).
"""

from alembic import op

revision = "d01112600007"
down_revision = "d01112600006"
branch_labels = None
depends_on = None

TRIGGER = "trg_TRUY_VAN_AI_no_update"
CREATE_TRIGGER = (
    f"CREATE TRIGGER {TRIGGER} BEFORE UPDATE ON TRUY_VAN_AI FOR EACH ROW "
    "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'TRUY_VAN_AI is append-only'"
)


def _convert(statements: list[str]) -> None:
    op.execute(f"DROP TRIGGER IF EXISTS {TRIGGER}")
    try:
        for statement in statements:
            op.execute(statement)
    finally:
        op.execute(CREATE_TRIGGER)


def upgrade() -> None:
    _convert(
        [
            "ALTER TABLE TRUY_VAN_AI ADD COLUMN PhamViDuLieu_moi JSON NULL",
            "UPDATE TRUY_VAN_AI SET PhamViDuLieu_moi = JSON_ARRAY(PhamViDuLieu) "
            "WHERE PhamViDuLieu IS NOT NULL",
            "ALTER TABLE TRUY_VAN_AI DROP COLUMN PhamViDuLieu",
            "ALTER TABLE TRUY_VAN_AI RENAME COLUMN PhamViDuLieu_moi TO PhamViDuLieu",
        ]
    )


def downgrade() -> None:
    _convert(
        [
            "ALTER TABLE TRUY_VAN_AI ADD COLUMN PhamViDuLieu_cu VARCHAR(50) NULL",
            "UPDATE TRUY_VAN_AI SET PhamViDuLieu_cu = "
            "JSON_UNQUOTE(JSON_EXTRACT(PhamViDuLieu, '$[0]')) WHERE PhamViDuLieu IS NOT NULL",
            "ALTER TABLE TRUY_VAN_AI DROP COLUMN PhamViDuLieu",
            "ALTER TABLE TRUY_VAN_AI RENAME COLUMN PhamViDuLieu_cu TO PhamViDuLieu",
        ]
    )
