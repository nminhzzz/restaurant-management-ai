"""Document-level contracts that must stay aligned with system behavior."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def test_business_date_guidance_uses_configured_effective_boundary():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    report = (ROOT / "docs" / "BaoCao_HeThongQuanLyNhaHang.md").read_text(encoding="utf-8")

    assert "app.shared.business_date" in agents
    assert "effective_business_day_start" in agents
    assert "Business Date kế tiếp" in agents
    assert "06:00 → 06:00 hôm sau" not in agents

    assert "GioBatDauBusinessDateMoi" in report
    assert "NgayHieuLucGioMoi" in report
