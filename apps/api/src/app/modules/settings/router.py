"""HTTP layer for the settings module."""

from fastapi import APIRouter

router = APIRouter(prefix="/settings", tags=["Module 5 — Settings"])
