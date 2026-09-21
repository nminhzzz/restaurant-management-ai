# apps/api — Backend API

FastAPI service hosting the six business modules and the AI Assistant
(Text-to-SQL) pipeline. See the repository root `AGENTS.md` for conventions and
`docs/BaoCao_HeThongQuanLyNhaHang.md` for the functional specification.

## Layout

| Path | Purpose |
| --- | --- |
| `src/app/core/` | Cross-cutting infrastructure: config, database session, security, dependencies, error handling. |
| `src/app/shared/` | Reusable primitives shared by every module: declarative base, soft delete, business date, audit log, pagination. |
| `src/app/modules/<name>/` | One package per business module. Each exposes `router.py` (HTTP layer) and `models.py` (ORM tables). |
| `src/app/modules/ai/` | AI Assistant: SQL guard, role-scoped views, and the Text-to-SQL pipeline steps. |
| `migrations/` | Alembic environment and revisions. |
| `tests/` | Pytest suite. |

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
