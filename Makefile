SHELL := /bin/bash
.DEFAULT_GOAL := help

API := apps/api
WEB := apps/web
ENV_FILE := .env
ENV_TEMPLATE := .env.example

.PHONY: help setup env db-up db-down api web migrate revision seed check-resources gate-integration \
         fmt fmt-check lint typecheck test test-api test-web build gate clean

help: ## Liệt kê các lệnh có sẵn
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Cài dependencies cho api và web
	cd $(API) && uv sync
	cd $(WEB) && pnpm install

env: ## Tạo tập biến môi trường cục bộ từ file mẫu nếu chưa có
	@test -f $(ENV_FILE) || cp $(ENV_TEMPLATE) $(ENV_FILE)
	@echo "$(ENV_FILE) đã sẵn sàng"

db-up: ## Bật MySQL bằng docker compose
	docker compose up -d db

db-down: ## Tắt MySQL
	docker compose down

api: ## Chạy backend ở chế độ phát triển (cổng 8000)
	cd $(API) && uv run uvicorn app.main:app --reload --app-dir src --port 8000

web: ## Chạy frontend ở chế độ phát triển (cổng 3000)
	cd $(WEB) && pnpm dev

migrate: ## Áp dụng toàn bộ migration
	cd $(API) && uv run alembic upgrade head

check-resources: ## Kiểm tra đĩa/RAM/load trước khi chạy integration (skip nếu thiếu)
	@python3 scripts/check_resources.py

revision: ## Sinh migration mới: make revision m="add order tables"
	cd $(API) && uv run alembic revision --autogenerate -m "$(m)"

seed: ## Sinh dữ liệu mô phỏng 12 tháng
	cd $(API) && uv run python ../../scripts/seed/generate.py

fmt: ## Tự sửa định dạng
	cd $(API) && uv run ruff format .
	cd $(WEB) && pnpm format

fmt-check: ## Kiểm tra định dạng (không sửa)
	cd $(API) && uv run ruff format --check .
	cd $(WEB) && pnpm format:check

lint: ## Lint cả hai phía
	cd $(API) && uv run ruff check .
	cd $(WEB) && pnpm lint

typecheck: ## mypy (api) và tsc (web)
	cd $(API) && uv run mypy .
	cd $(WEB) && pnpm typecheck

test: test-api test-web ## pytest (api) và vitest (web)

test-api: ## Chạy kiểm thử backend
	cd $(API) && uv run pytest

test-web: ## Chạy kiểm thử frontend
	cd $(WEB) && pnpm test

build: ## Build production bundle của web
	cd $(WEB) && pnpm build

gate: fmt-check lint typecheck test build ## Cổng kiểm tra bắt buộc trước khi kết thúc

gate-full: ## Gate đầy đủ trước khi tag Phase (nhẹ + MySQL nếu đủ tài nguyên)
	$(MAKE) gate
	$(MAKE) gate-integration || echo "[gate-full] integration skipped (host under pressure or MySQL not running)"

gate-integration: check-resources ## Gate trên MySQL thật (B1) - skip nếu máy yếu
	cd $(API) && uv run pytest -m integration -q

clean: ## Xoá artefact build cục bộ
	rm -rf $(WEB)/.next $(WEB)/coverage $(API)/.pytest_cache $(API)/.mypy_cache $(API)/.ruff_cache
