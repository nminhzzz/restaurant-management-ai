"""The three fixed roles of the system (VAI_TRO).

Each role maps to exactly one read-only view exposed to the AI Assistant
(NFR-06, NFR-12); see `app.modules.ai.scope`.
"""

from enum import StrEnum


class Role(StrEnum):
    MANAGER = "MANAGER"
    CASHIER = "CASHIER"
    WAREHOUSE = "WAREHOUSE"


class OperationStatus(StrEnum):
    """Lifecycle of a single order line (FR-SALE-10)."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SERVED = "SERVED"
    CANCELLED = "CANCELLED"


class DishStatus(StrEnum):
    """Operational state of a dish (FR-CAT-06, FR-CAT-11, FR-CAT-26)."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
