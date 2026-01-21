# Python Infrastructure

## 1. Project Management
- **Tool:** Use `poetry`, `hatch`, or `uv` via `pyproject.toml`.
- **Lockfile:** `poetry.lock` (or equivalent) must be committed.
- **Task Runner:** `Justfile`
    ```makefile
    test:
        poetry run pytest
    lint:
        poetry run ruff check . --fix
    ```

## 2. Versioning (No Drift)
- **Plugin:** `poetry-dynamic-versioning`.
    - **Why:** Keeps `pyproject.toml` and `__version__` in sync with Git tags automatically.
    - **Config:**
    ```toml
    [tool.poetry-dynamic-versioning]
    enable = true
    vcs = "git"
    style = "pep440"
    ```

## 3. Quality & Linting
- **Ruff:** Use `ruff` for both linting and formatting.
    - Config in `pyproject.toml`:
    ```toml
    [tool.ruff]
    select = ["E", "F", "I", "B"] # Pyflakes, pycodestyle, isort, bugbear
    ignore = []
    ```
- **Type Checking:** `mypy` strict mode.
- **Pre-commit:**
    ```yaml
    repos:
      - repo: local
        hooks:
          - id: pytest
            name: pytest
            entry: poetry run pytest
            language: system
            pass_filenames: false
            always_run: true
    ```

## 3. CI/CD Implementation (GitHub Actions)
- **Setup:**
    ```yaml
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
    ```
- **Test Command:** `pytest --cov=./ --cov-report=xml`
- **Coverage:** Upload to Codecov (`codecov/codecov-action`).

## 4. Containerization
- **Base Image:** `FROM python:3.11-slim-bookworm` (or newer).
- **Optimization:** Use multi-stage builds if compiling C-extensions.
- **User:** Run as non-root user.
