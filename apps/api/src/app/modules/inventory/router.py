"""HTTP layer for the inventory module."""

from fastapi import APIRouter

router = APIRouter(prefix="/inventory", tags=["Module 3 — Inventory"])
