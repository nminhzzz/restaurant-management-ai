"""HTTP layer for the reporting module."""

from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["Module 4 — Reports"])
