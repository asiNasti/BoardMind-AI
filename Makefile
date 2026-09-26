.PHONY: test fmt all up b-fmt f-fmt

up:
	docker compose up -d --build
	cd frontend && npm run dev

test:
	cd backend && pytest --cov=app --cov-report=term-missing --cov-fail-under=80

b-fmt:
	black backend/
	ruff check --fix backend/
	cd backend && mypy app

f-fmt:
	cd frontend && npx prettier --write "src/**/*.{js,jsx,css}"
	cd frontend && npx eslint "src/**/*.{js,jsx}" --fix

fmt: f-fmt b-fmt

all:
	black --check backend/
	ruff check backend/
	cd backend && mypy app
	cd frontend && npx eslint "src/**/*.{js,jsx}" --max-warnings 0
	cd backend && pytest --cov=app --cov-report=term-missing --cov-fail-under=80
	