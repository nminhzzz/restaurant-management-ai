"""Collection-time configuration must be independent of host payment settings."""

import os
import subprocess
import sys
from pathlib import Path


def test_pytest_collection_succeeds_with_sepay_selected_and_missing_credentials():
    api_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.update(
        {
            "PAYMENT_GATEWAY": "sepay",
            "SEPAY_BANK_ACCOUNT": "",
            "SEPAY_BANK_CODE": "",
            "SEPAY_WEBHOOK_API_KEY": "",
        }
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "tests/modules/test_sales_sepay_adapter.py",
        ],
        cwd=api_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, "pytest collection failed under isolated hostile settings"


def test_collection_import_restores_host_payment_environment():
    api_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.update(
        {
            "PAYMENT_GATEWAY": "sepay",
            "SEPAY_BANK_ACCOUNT": "host-account",
            "SEPAY_WEBHOOK_API_KEY": "host-api-key",
        }
    )
    env.pop("SEPAY_BANK_CODE", None)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os; before = dict(os.environ); "
            "from tests import conftest; "
            "assert dict(os.environ) == before",
        ],
        cwd=api_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, "collection import changed the host payment environment"
