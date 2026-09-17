.PHONY: test fmt all up

up:
	docker compose up -d --build

test:
	cd backend && pytest --cov=app --cov-report=term-missing --cov-fail-under=80

fmt:
	black backend/
	ruff check --fix backend/
	cd backend && mypy app
	
all:
	black --check backend/
	ruff check backend/
	cd backend && mypy app
	cd backend && pytest --cov=app --cov-report=term-missing --cov-fail-under=80