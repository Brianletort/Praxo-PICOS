SHELL := /bin/bash

.PHONY: bootstrap bootstrap-python bootstrap-node lint typecheck test test-python test-web dev-api dev-web

bootstrap: bootstrap-python bootstrap-node

bootstrap-python:
	python3.12 -m venv .venv
	source .venv/bin/activate && python -m pip install --upgrade pip setuptools wheel
	source .venv/bin/activate && pip install -e ".[dev]"

bootstrap-node:
	npm install --workspaces

lint:
	source .venv/bin/activate && ruff check .

typecheck:
	source .venv/bin/activate && mypy services packages tests

test: test-python

test-python:
	source .venv/bin/activate && pytest

dev-api:
	source .venv/bin/activate && uvicorn services.api.src.praxo_picos_api.main:app --reload --port 8865

dev-web:
	cd apps/web && npm run dev
