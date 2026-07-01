.PHONY: help install run test clean docker build lint format

help:
	@echo "AI Assistant - Makefile commands"
	@echo "=================================="
	@echo ""
	@echo "Installation:"
	@echo "  make install       - Install dependencies"
	@echo "  make install-dev   - Install with dev dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make run           - Run CLI mode"
	@echo "  make run-voice     - Run voice mode"
	@echo "  make run-server    - Run server mode"
	@echo "  make run-daemon    - Run daemon mode"
	@echo ""
	@echo "Development:"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make mypy          - Type checking"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make docker-logs   - View container logs"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         - Clean cache and temp files"
	@echo "  make freeze        - Freeze requirements"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,docker,integrations]"

run:
	python main.py --mode cli

run-voice:
	python main.py --mode voice

run-server:
	python main.py --mode server --port 8000

run-daemon:
	python main.py --mode daemon

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=. --cov-report=html

lint:
	ruff check .
	flake8 .

format:
	black .
	ruff check --fix .

mypy:
	mypy . --ignore-missing-imports

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "✅ Контейнеры запущены"
	@echo "   Ollama: http://localhost:11434"
	@echo "   ChromaDB: http://localhost:8000"
	@echo "   Assistant: http://localhost:8001"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/

freeze:
	pip freeze > requirements-frozen.txt

.DEFAULT_GOAL := help