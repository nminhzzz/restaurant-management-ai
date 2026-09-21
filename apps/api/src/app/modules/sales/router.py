"""HTTP layer for the sales module."""

from fastapi import APIRouter

router = APIRouter(prefix="/sales", tags=["Module 2 — Sales"])
