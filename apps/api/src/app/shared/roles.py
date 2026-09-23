"""The three fixed roles of the system (VAI_TRO).

Each role maps to exactly one read-only view exposed to the AI Assistant
(NFR-06, NFR-12); see `app.modules.ai.scope`.
"""

from enum import StrEnum


class Role(StrEnum):
    MANAGER = "MANAGER"
    CASHIER = "CASHIER"
    WAREHOUSE = "WAREHOUSE"
