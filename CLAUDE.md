# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Sensor Toolkit is a Python training project for the ACT271-TI Vibe Coding course. It provides utilities for validating and processing sensor data readings. The project is designed for Python 3.10+ on Linux/macOS/Windows.

## Common Development Commands

### Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or on Windows:
.venv\Scripts\activate

# Install dependencies and dev tools
pip install -e ".[dev]"
```

### Code Quality
```bash
# Format code with black
black src/

# Lint with ruff
ruff check src/

# Run all formatters and linters
ruff format src/
ruff check --fix src/
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=sensor_toolkit --cov-report=html

# Run a single test file
pytest tests/test_validators.py

# Run a specific test
pytest tests/test_validators.py::test_validate_sensor_id

# Run tests matching a pattern
pytest -k "temperature" -v
```

## Project Structure and Architecture

### Directory Layout
- `src/sensor_toolkit/`: Main package containing modules
- `tests/`: Test files mirroring `src/` structure
- `tests/conftest.py`: Shared pytest fixtures and test configuration

### Data Model: Sensor Reading
All sensor readings contain standardized fields with validation ranges:
- `timestamp`: ISO 8601 datetime string
- `sensor_id`: String format "TI-XXXX-YYYY" (X, Y = alphanumeric)
- `temperature`: Float, range [-40, 150] °C
- `pressure`: Float, range [0, 1000] hPa
- `humidity`: Float, range [0, 100] %

### Validation Strategy
Input validation occurs at system boundaries. The `sensor_toolkit.validators` module provides functions to validate individual fields and complete sensor readings. Validators return boolean results and raise exceptions with descriptive messages on failure.

## Coding Standards

### General Rules
- Use Python type hints on all function signatures
- Follow PEP 8 via ruff and black formatters
- Write Google-style docstrings for all public functions
- Maximum function length: 30 lines
- Maximum line length: 100 characters
- Always use `pathlib.Path` instead of `os.path`

### Module Organization
- Each validator function validates a single field or concept
- Use descriptive names that clearly indicate what is validated
- Public functions should have type hints and docstrings
- Internal helper functions may be private (prefixed with `_`)

## Testing Standards
- Use pytest for all tests
- Target minimum test coverage: 80%
- Test structure mirrors source: `src/sensor_toolkit/module.py` → `tests/test_module.py`
- Use fixtures in `tests/conftest.py` for shared test data
- Test files should import fixtures with meaningful names (e.g., `valid_sensor_reading`, `invalid_temperature`)
- Never delete or overwrite existing test files

## Important Constraints
- NEVER generate or reference real TI proprietary systems
- NEVER output API keys, credentials, or secrets
- ALWAYS use sample/synthetic data, not real production data
- When unsure about a change, explain the plan before executing
