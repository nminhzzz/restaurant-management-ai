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
