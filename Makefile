.PHONY: install lint format test run migrate

install:
	pip install -e ".[dev]"

lint:
	ruff check .
	black --check .
	isort --check-only .
	mypy app

format:
	ruff check . --fix
	black .
	isort .

test:
	pytest

run:
	uvicorn app.main:app --reload

migrate:
	alembic upgrade head
