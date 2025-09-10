# Capacitance Monitor - Makefile for Unix-like systems

.PHONY: help setup run run-mock run-dev test clean

help: ## Show this help message
	@echo "Capacitance Monitor for Keithley 2110 DMM"
	@echo "=========================================="
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

setup: ## Set up the development environment
	@echo "Setting up development environment..."
	uv venv
	.venv/bin/activate && uv pip install -e ".[dev]"
	@echo "Setup complete! Run 'make run-mock' to test."

run: ## Run the application (instrument selection via GUI)
	@echo "Running application..."
	.venv/bin/activate && python app.py

run-mock: ## Run with mock instrument
	@echo "Running with mock instrument..."
	.venv/bin/activate && python app.py --mock

run-dev: ## Run in development mode with debug
	@echo "Running in development mode..."
	.venv/bin/activate && python app.py --mock --debug

test: ## Run tests
	@echo "Running tests..."
	.venv/bin/activate && python -m pytest tests/ -v

clean: ## Clean up virtual environment
	@echo "Cleaning up..."
	rm -rf .venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

install: ## Install dependencies only
	.venv/bin/activate && uv pip install -e .

install-dev: ## Install dependencies with dev tools
	.venv/bin/activate && uv pip install -e ".[dev]"
