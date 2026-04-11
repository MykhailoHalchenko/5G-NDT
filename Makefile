.PHONY: install dev-install run test lint format type-check clean docker-up docker-down

# ── Environment ──────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

dev-install:
	pip install -e ".[dev]"
	pip install black flake8 mypy

# ── Application ───────────────────────────────────────────────────────────────
run:
	python -m src.api.main --seed

run-empty:
	python -m src.api.main

run-api:
	python -m src.api.app

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=xml

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# ── Code quality ──────────────────────────────────────────────────────────────
lint:
	flake8 src/ tests/ --max-line-length=120

format:
	black src/ tests/ --line-length=120

format-check:
	black src/ tests/ --line-length=120 --check

type-check:
	mypy src/ --ignore-missing-imports

# ── Docker ────────────────────────────────────────────────────────────────────
docker-up:
	docker-compose -f infra/docker/docker-compose.yml up -d

docker-down:
	docker-compose -f infra/docker/docker-compose.yml down

docker-build:
	docker build -f infra/docker/Dockerfile -t 5g-ndt:latest .

# ── Database ──────────────────────────────────────────────────────────────────
setup-db:
	python scripts/setup_db.py

seed:
	python scripts/seed_topology.py

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name ".coverage" -delete
	find . -name "coverage.xml" -delete
	rm -rf .pytest_cache dist build *.egg-info
