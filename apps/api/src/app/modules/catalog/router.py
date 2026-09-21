"""HTTP layer for the catalogue module.

Routes are added per feature; keep business rules in a `service.py` next to this
file rather than in the handlers.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/catalog", tags=["Module 1 — Catalogue"])
