.PHONY: help install dev-install run api test lint format clean docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make run           - Run procurement workflow via CLI"
	@echo "  make api           - Start FastAPI REST API server"
	@echo "  make test          - Run pytest test suite"
	@echo "  make lint          - Lint code using ruff"
	@echo "  make format        - Format code using ruff & black"
	@echo "  make clean         - Clean bytecode and cached outputs"
	@echo "  make docker-build  - Build Docker container"
	@echo "  make docker-up     - Start containerized services"
	@echo "  make docker-down   - Stop containerized services"

install:
	pip install -r requirements.txt

dev-install:
	pip install -e ".[dev]"

run:
	python -m src.main

api:
	uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest -v tests/

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info

docker-build:
	docker build -t procurement-crew:latest .

docker-up:
	docker compose up -d

docker-down:
	docker compose down
