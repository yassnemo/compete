# compete — developer task runner.
# Windows users without `make` can run the underlying commands directly
# (see each target) or use `uv run python scripts/demo.py`.

.PHONY: help install install-web demo demo-data run-all api web test lint fmt typecheck dbt-build dbt-docs screenshots clean

help:
	@echo "compete targets:"
	@echo "  install      Install Python deps (uv) + Playwright Chromium"
	@echo "  install-web  Install web deps (npm)"
	@echo "  demo         Seed demo data, build marts, start API + web"
	@echo "  demo-data    Seed demo data and build the dbt marts only"
	@echo "  run-all      Real pipeline: sync -> collect -> extract -> dbt -> report"
	@echo "  api          Start the FastAPI server"
	@echo "  web          Start the Next.js dev server"
	@echo "  test         Run the Python test suite"
	@echo "  lint / fmt   Ruff lint / Ruff+Black format"
	@echo "  dbt-build    Build + test the dbt marts"
	@echo "  screenshots  Capture dashboard screenshots (needs web+api running)"

install:
	uv sync --extra dev --extra dbt --extra api --extra report
	uv run playwright install chromium

install-web:
	cd web && npm install

demo-data:
	uv run python scripts/seed_demo.py --build

demo:
	uv run python scripts/demo.py

run-all:
	uv run compete run-all

api:
	uv run compete-api

web:
	cd web && npm run dev

test:
	uv run pytest

lint:
	uv run ruff check pipeline tests api scripts

fmt:
	uv run ruff check --fix pipeline tests api scripts
	uv run black pipeline tests api scripts

typecheck:
	uv run mypy pipeline

dbt-build:
	cd warehouse/dbt && COMPETE_DUCKDB_PATH=$(PWD)/data/compete.duckdb uv run --project $(PWD) dbt build --profiles-dir .

screenshots:
	uv run python scripts/screenshots.py

clean:
	rm -rf data/*.duckdb data/raw warehouse/dbt/target
