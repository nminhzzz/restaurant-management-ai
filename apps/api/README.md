# apps/api — Backend API

FastAPI service hosting the six business modules and the AI Assistant
(Text-to-SQL) pipeline. See the repository root `AGENTS.md` for conventions and
`docs/BaoCao_HeThongQuanLyNhaHang.md` for the functional specification.

## Layout

| Path | Purpose |
| --- | --- |
| `src/app/core/` | Cross-cutting infrastructure: config, database session, security, dependencies (token revalidation, role checks), error handling. |
| `src/app/shared/` | Reusable primitives shared by every module: declarative base, enums, soft delete, business date, audit log, pagination, roles. |
| `src/app/modules/<name>/` | One package per business module. Each exposes `router.py` (HTTP layer), `schemas.py` and `service.py` (business rules); modules that own tables also have `models.py`. |
| `src/app/modules/ai/` | AI Assistant: SQL guard (`guard.py`, issues `ValidatedSql`), role-scoped views (`scope.py`), per-role read-only accounts (`accounts.py`), and the Text-to-SQL pipeline in `pipeline/` (prompt, generator, executor, interpreter). |
| `migrations/` | Alembic environment and revisions (11 revisions, single head). |
| `tests/` | Pytest suite. `tests/integration/` and the `*_on_mysql` schema tests need a real MySQL (`make gate-integration`). |

## Modules

| Module | Notes |
| --- | --- |
| `catalog` | Groups, dishes, recipes and price versions (`versions.py`), ingredients, suppliers, tables. Scheduled prices/recipes are promoted on their Business Date. |
| `sales` | Item holds (`holds.py`), orders, kitchen tickets, payments (`payments.py`), QR gateways (`gateways/`: `sepay`, `simulator`), webhooks, QR exceptions and refunds (`exceptions.py`), invoices snapshot (`invoices.py`), floor and table release (`floor.py`). |
| `inventory` | Receipts, lots (FIFO, expiry), manual write-offs, stocktake sessions that block stock writers, monthly costing (`costing.py`). |
| `reports` | Read-only aggregates (`queries.py`, `periods.py`): revenue, rankings, margin and cost, hourly, comparison, unsettled and cancelled/closed-unpaid orders. It owns no tables, so it has **no `models.py`** and reads the other modules' models. |
| `settings` | Accounts (create, PATCH, lock/unlock), authentication, system config, audit log, backup export. |
| `ai` | See above. Every generated query must go through `guard.validate_sql`; the executor accepts only `ValidatedSql`. |

## Commands

```bash
uv sync                       # install dependencies
uv run uvicorn app.main:app --reload --app-dir src
uv run alembic upgrade head   # apply migrations
uv run pytest                 # tests
uv run ruff check .           # lint
uv run ruff format .          # format
uv run mypy .                 # type check
```

From the repository root, `make gate` runs format check, lint, type check, tests and the web build;
`make gate-full` adds the MySQL integration tests when the host has the resources.
