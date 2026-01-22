# Justfile for ClipFlowAI

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

build-ui:
    npm run build

server:
    poetry run python backend/server.py

gui:
    npm run dev

dev:
    npx concurrently "just server" "just gui"

clean:
    rm -rf dist build .pytest_cache .mypy_cache .ruff_cache
    find . -type d -name "__pycache__" -exec rm -rf {} +
