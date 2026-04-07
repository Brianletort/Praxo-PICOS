SHELL := /bin/bash

.PHONY: bootstrap bootstrap-python bootstrap-node lint typecheck \
        test test-python test-web test-e2e test-regression test-performance \
        regression regression-fast check-regression-monotonicity \
        dev-api dev-web

bootstrap: bootstrap-python bootstrap-node

bootstrap-python:
	python3 -m venv .venv
	source .venv/bin/activate && python -m pip install --upgrade pip setuptools wheel
	source .venv/bin/activate && pip install -e ".[dev]"

bootstrap-node:
	npm install --workspaces

lint:
	source .venv/bin/activate && ruff check .
	cd apps/web && npm run lint

typecheck:
	source .venv/bin/activate && mypy services packages tests
	cd apps/web && npm run typecheck

test: test-python test-web

test-python:
	source .venv/bin/activate && pytest -m "unit or contract or smoke" --timeout=60

test-web:
	cd apps/web && npm run test:run

test-e2e:
	cd apps/web && npm run e2e

test-regression:
	source .venv/bin/activate && pytest -m "regression" --timeout=120

test-performance:
	source .venv/bin/activate && pytest -m "performance" --timeout=300

regression: test-python test-web test-regression test-performance
	@echo "Full regression suite complete."

regression-fast: test-python test-web
	source .venv/bin/activate && pytest -m "regression" -x --timeout=60
	@echo "Fast regression subset complete."

check-regression-monotonicity:
	bash scripts/check-regression-monotonicity.sh

dev-api:
	source .venv/bin/activate && uvicorn services.api.src.praxo_picos_api.main:app --reload --port 8865

dev-web:
	cd apps/web && npm run dev
