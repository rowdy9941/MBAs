.PHONY: setup install dev down logs check backend-test worker-test frontend-test compose-check
COMPOSE_DEV = docker compose -f compose.yaml -f compose.dev.yaml

setup:
	cp -n .env.example .env || true

install:
	python3.12 -m venv services/api/.venv
	services/api/.venv/bin/python -m pip install -e 'services/api[dev]'
	services/api/.venv/bin/python -m pip install -r services/worker/requirements.txt
	cd apps/dashboard && npm ci

dev: setup
	$(COMPOSE_DEV) up --build
down:
	$(COMPOSE_DEV) down
logs:
	$(COMPOSE_DEV) logs -f --tail=100
backend-test:
	cd services/api && .venv/bin/python -m pytest
worker-test:
	PYTHONPATH=services/worker services/api/.venv/bin/python -m unittest discover -s services/worker/tests
frontend-test:
	cd apps/dashboard && npm test && npm run typecheck
compose-check:
	$(COMPOSE_DEV) config --quiet
check: backend-test worker-test frontend-test compose-check
