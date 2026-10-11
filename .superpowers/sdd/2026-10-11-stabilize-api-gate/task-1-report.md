# Task 1 Report: Hermetic payment tests

## Implementation

- Added an autouse pytest fixture in `apps/api/tests/conftest.py` that sets `PAYMENT_GATEWAY=simulator` and clears `SEPAY_BANK_ACCOUNT`, `SEPAY_BANK_CODE`, and `SEPAY_WEBHOOK_API_KEY` with `monkeypatch.setenv`.
- Explicit SePay fixtures continue to override the defaults. The existing `get_settings.cache_clear()` setup and teardown fixture remains unchanged.
- Made `test_selecting_sepay_without_credentials_fails_at_startup` explicitly set the gateway to SePay and the three required credentials to empty strings before asserting the `RuntimeError`.

## TDD and baseline

Ran the brief's exact focused pytest command before implementation. It passed all 34 tests, so the reported six failures were not reproducible in this worktree/environment. No `.env` values were read into logs or reported. Because the baseline was green, I could not demonstrate those failures turning red before the fix; the targeted startup test already passed here.

The focused command passed again after implementation (34 passed). It also passed with dummy ambient process settings `PAYMENT_GATEWAY=sepay` and nonempty SePay credentials, demonstrating that the autouse fixture isolates simulator tests while per-test SePay configuration remains effective.

## Self-review

- The fixture is limited to the test suite and uses `monkeypatch`, so environment changes are restored after each test.
- The startup validation test no longer depends on host credentials being absent.
- `git diff --check` passed.

## Concerns

The six failures described in the brief were not observed before the change. The external environment that produced them may differ from this worktree's environment; the hostile-environment verification confirms the new default is insulated from process-level SePay settings.

## Fix round 1: collection before fixtures

- Confirmed that `app.main` calls `get_settings()` during import, before pytest autouse fixtures run. Collection therefore needs a temporary simulator environment around that import.
- Wrapped the `app.main` import in `patch.dict("os.environ", ...)`, which restores the original environment even if the import raises. Added a subprocess regression check for both present and absent host variables. The existing subprocess check covers `pytest --collect-only` with SePay selected and all required credentials empty. Neither check prints environment values.
- Verified under `PAYMENT_GATEWAY=sepay` with empty SePay credentials: collection regression and focused payment suite passed (50 passed). Per-test `sepay_env` cases remain green. Ruff check, Ruff format check, and `git diff --check` passed.
- `make gate` passed format, lint, and type checks, then stopped in API pytest: 440 passed and one inventory costing test failed (`test_closing_a_month_prices_its_write_offs_and_is_audited`, expected estimated cost 3000, received 0). That test also fails in isolation. The gate did not reach web tests or build.

### Self-review

- The import override affects only four payment variables and exists only while `app.main` imports; `patch.dict` handles restoration on normal and exceptional exits.
- The per-test autouse fixture still defaults to simulator and clears SePay credentials, while explicit SePay fixtures override it.
- The new subprocess assertions use fixed dummy values and generic failure messages, so host credentials are not exposed in test output.
