.PHONY: help install dev test lint format type security cov build check-dist clean all pre-commit run

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install package in production mode
	uv pip install -e .

dev: ## Install package with development dependencies
	uv pip install -e ".[dev]"
	pre-commit install

test: ## Run tests
	uv run pytest tests/ -v

cov: ## Run tests with coverage report
	uv run pytest --cov-report=term-missing --cov-report=html --cov=src/SVG2DrawIOLib tests/

lint: ## Run linting checks
	uv run ruff check src tests

format: ## Format code with ruff
	uv run ruff format src tests
	uv run ruff check --fix src tests

type: ## Run type checking with mypy
	uv run mypy src

security: ## Run security checks with bandit
	uv run bandit -r src -ll

build: ## Build package distribution
	uv build

check-dist: build ## Build and check distribution
	python -m twine check dist/*

all: format lint type security test ## Run all checks and tests

pre-commit: ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

clean: ## Clean build artifacts and caches
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run: ## Run the CLI (use ARGS="..." to pass arguments)
	SVG2DrawIOLib $(ARGS)
