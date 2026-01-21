# Justfile for AutoReelAI

default: list

list:
    @just --list

test:
    pytest

lint:
    ruff check .
    mypy src

format:
    ruff format .
    ruff check . --fix

clean:
    rm -rf dist build .pytest_cache .mypy_cache .ruff_cache
    find . -type d -name "__pycache__" -exec rm -rf {} +
