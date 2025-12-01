.PHONY: help test test-verbose test-coverage test-fast clean install lint format

help:
	@echo "OxUtils Development Commands"
	@echo ""
	@echo "  make install          Install dependencies"
	@echo "  make test             Run all tests"
	@echo "  make test-verbose     Run tests with verbose output"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo "  make test-fast        Run tests without coverage"
	@echo "  make lint             Run linting checks"
	@echo "  make format           Format code"
	@echo "  make clean            Clean build artifacts"

install:
	uv sync --dev

test:
	pytest

test-verbose:
	pytest -v

test-coverage:
	pytest --cov=oxutils --cov-report=term-missing --cov-report=html

test-fast:
	pytest --no-cov

test-settings:
	pytest tests/test_settings.py -v

test-exceptions:
	pytest tests/test_exceptions.py -v

test-functions:
	pytest tests/test_functions.py -v

test-jwt:
	pytest tests/test_jwt.py -v

test-mixins:
	pytest tests/test_mixins.py -v

test-enums:
	pytest tests/test_enums.py -v

lint:
	ruff check src/

format:
	ruff format src/

clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
