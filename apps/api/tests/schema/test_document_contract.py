"""Document-level contracts that must stay aligned with system behavior."""

import re
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


def test_report_image_links_resolve_with_exact_path_casing():
    docs_dir = ROOT / "docs"
    report = (docs_dir / "BaoCao_HeThongQuanLyNhaHang.md").read_text(encoding="utf-8")
    image_targets = re.findall(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)", report)
    expected_targets = {f"Images/image_{number}.png" for number in range(1, 23)}
    actual_paths = {
        path.relative_to(docs_dir).as_posix() for path in docs_dir.rglob("*") if path.is_file()
    }

    assert len(image_targets) == 22
    assert set(image_targets) == expected_targets
    for target in image_targets:
        assert target in actual_paths, (
            f"Markdown image target has missing or incorrect casing: {target}"
        )
        assert (docs_dir / target).is_file(), f"Markdown image target does not exist: {target}"
