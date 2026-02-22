.PHONY: help install dev test lint format type security cov build check-dist clean clean-win zip all pre-commit run dev-api dev-web build-web start-web build-release

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

clean-win: ## Clean build artifacts and caches (Windows)
	@if exist dist rmdir /s /q dist
	@if exist build rmdir /s /q build
	@if exist htmlcov rmdir /s /q htmlcov
	@if exist .coverage rmdir /s /q .coverage
	@if exist .pytest_cache rmdir /s /q .pytest_cache
	@if exist .mypy_cache rmdir /s /q .mypy_cache
	@if exist .ruff_cache rmdir /s /q .ruff_cache
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@for /d /r . %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"
	@del /s /q *.pyc >nul 2>&1 || exit /b 0

zip: ## Create a source archive respecting .gitignore
	@git archive -o SVG2DrawIOLib-source.zip HEAD
	@echo "Created SVG2DrawIOLib-source.zip"

run: ## Run the CLI (use ARGS="..." to pass arguments)
	SVG2DrawIOLib $(ARGS)

dev-api: ## Start FastAPI API server (from repo root)
	uv pip install -e ".[web]"
	uv run uvicorn SVG2DrawIOLib.api.main:app --reload --port 8000

dev-web: ## Start Next.js UI dev server
	cd web-ui && npm run dev

dev-all: ## Start FastAPI API and Next.js UI (Unix only)
	uv run uvicorn SVG2DrawIOLib.api.main:app --reload --port 8000 &
	cd web-ui && npm run dev

build-web: ## Build Next.js static export into web-ui/out/ (required before svg2drawio web)
	cd web-ui && npm run build

build-release: build-web ## Build Next.js UI and copy into the Python package for distribution
	uv run python -c "import shutil,pathlib; w=pathlib.Path('src/SVG2DrawIOLib/web'); shutil.rmtree(w,ignore_errors=True); shutil.copytree('web-ui/out',w); [(p.rename(p.parent.parent/(p.parent.name+'.__PAGE__.txt')),p.parent.rmdir()) for p in list(w.rglob('__PAGE__.txt')) if p.parent.name.startswith('__next.')]"

start-web: build-web ## Build then launch the web UI via the CLI (opens browser)
	svg2drawio web
