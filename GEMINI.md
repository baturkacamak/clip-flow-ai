# Gemini Context Configuration

<!-- 
    This is the master file that you would place in your PROJECT ROOT (renaming it to GEMINI.md).
-->

<!-- 1. GLOBAL BASICS (Always Include) -->
# General Development Standards

These rules apply to all projects, regardless of language.

## Git & Version Control
- **Conventional Commits:** ALWAYS use conventional commits.
    - `feat: add user login`
    - `fix: resolve null pointer in dashboard`
    - `docs: update readme`
    - `chore: update dependencies`
- **Branching:** Use `feature/` or `fix/` prefixes (e.g., `feature/dark-mode`).
- **Secrets:** NEVER commit API keys, tokens, or passwords.

## Tone & Style
- **Brevity:** Be concise. Don't explain "what" you did unless asked. Focus on "why".
- **Safety:** Always analyze existing code before changing it. Do not break existing functionality.
- **Independence:** If a requested library is missing, check if it's installed. If not, ask before adding it.

## Reusability Protocol (DRY - Critical)
- **Search First:** Before writing ANY helper, utility, or generic logic, you **MUST** run a `glob` or `search` to find existing implementations in `core/`, `lib/`, `shared/`, `common/` or `utils/`.
- **Strict Ban on Duplication:** Creating a function that already exists in the Core Library is a CRITICAL FAILURE.
- **Extend, Don't Reinvent:** If a core utility is *almost* right, extend it. Do not write a separate version.
- **Convention:** Assume a `Core` or `Shared` namespace exists. Verify it before importing.

## Code Hygiene (Leave No Trace)
- **No Dead Code:** You MUST remove unused imports, commented-out logic, and "zombie" functions before finishing.
- **No Debug Prints:** Remove all `print()`, `console.log()`, or `var_dump()` statements. Use the Logger if persistent output is needed.
- **Cleanup:** If you modify a file, you own its cleanliness. Fix existing lint warnings near your changes.

## Engineering Excellence
- **Refactor over Patch:** Do not add complexity to an already complex function. If a change makes a function too long or hard to read, you MUST refactor it into smaller, cohesive units before or during the implementation.
- **Fail-Fast:** Detect errors at the earliest possible point. Validate inputs at the boundary (API, CLI, UI) before passing them to the core logic.

# Global Infrastructure Standards

These standards apply to **ALL** projects.

## 1. Governance & Documentation
- **Security:** `SECURITY.md` must exist with a vulnerability reporting policy.
- **Conduct:** `CODE_OF_CONDUCT.md` (Contributor Covenant).
- **License:** `LICENSE` file (SPDX compliant).
- **ADR:** Architectural Decision Records in `docs/adr/`.
- **Changelog:** `CHANGELOG.md` following "Keep a Changelog" format.
- **Readme:** Must include badges for Build Status, License, and Version.

## 2. AI Instructions (Code Generation)
- **Mandatory Testing:** When generating code, Gemini **MUST** always generate accompanying unit tests.
    - **Unit Tests:** Required for all logic.
    - **E2E/Integration:** Required for new features or API endpoints.
- **Test-Driven:** Prefer a Test-Driven Development (TDD) approach where possible.

## 3. GitHub Configuration
- **Issue Templates:** `.github/ISSUE_TEMPLATE/` (Bug Report, Feature Request).
- **PR Template:** `.github/pull_request_template.md` with checklist.
- **Labels:** `.github/labeler.yml` for auto-labeling based on changed files.
- **Stale:** Use `actions/stale` to manage inactive issues.
- **Release Drafter:** `.github/release-drafter.yml` to automate changelogs and semantic releases.

## 4. Generic Automation (CI/CD)
- **Workflows:**
    - `release.yml`: Automated GitHub Releases.
        - **Trigger:** On push to tags `v*`.
        - **Action:** `softprops/action-gh-release`.
        - **Artifacts:** Must upload build assets (binaries, dist/ folder) if applicable.
        - **Changelog:** Auto-generated from Release Drafter or Conventional Commits.
    - `docs.yml`: Automated documentation deployment (e.g., GitHub Pages).
    - `pre-commit-autoupdate.yml`: Weekly auto-update of pre-commit hooks.
- **Dependabot:** `.github/dependabot.yml` for weekly updates.
- **Secret Scanning:** `gitleaks` enabled in pre-commit or CI.

## 5. Versioning Strategy (Single Source of Truth)
- **Source:** The **Git Tag** (e.g., `v1.2.0`) is the SINGLE source of truth.
- **Automation:** Files (`pyproject.toml`, `package.json`, `README.md`, `__init__.py`) MUST be updated automatically by CI or local scripts.
- **Tools:**
    - **Python:** `poetry-dynamic-versioning` (preferred) or `bump-my-version`.
    - **Node:** `npm version` or `release-it`.
    - **General:** `bump-my-version` for syncing `README.md` and docs.

## 6. Development Environment
- **Task Runner:** `Justfile` required to standardize commands (test, lint, build).
- **Dev Containers:** `.devcontainer/devcontainer.json` for consistent, reproducible environments.
- **AI Context:** `.geminiignore` must exist to exclude `dist/`, `node_modules/`, `build/`, and lockfiles from AI context.

## 6. Editor & Formatting
- **EditorConfig:** `.editorconfig` file required for cross-editor consistency.
    - Indent style: Space
    - End of line: LF
    - Insert final newline: True
    - Trim trailing whitespace: True

## 7. Pre-commit (Universal Hooks)
- **Config:** `.pre-commit-config.yaml`
- **Requirement:** MUST run unit tests before allowing a commit.
- **Hooks:**
    - `trailing-whitespace`
    - `end-of-file-fixer`
    - `check-yaml`
    - `check-json`
    - `conventional-pre-commit` (Enforce `feat:`, `fix:` commit messages).

<!-- 2. LANGUAGE SPECIFIC (Python) -->

# Python Coding Standards

## Code Style
- **Type Hints:** ALWAYS use type hints for function arguments and return values.
    - `def calculate_total(price: float, tax: float) -> float:`
- **Docstrings:** Use Google-style docstrings.
- **Formatting:** Adhere to PEP 8 (enforced by Ruff).
- **Naming:**
    - Variables/Functions: `snake_case`
    - Classes: `PascalCase`
    - Constants: `UPPER_CASE`

## Architecture
- **Boundary Validation (Fail-Fast):**
    - Use `pydantic` or `dataclasses` with type-checking for all incoming data.
    - Validate all API/CLI inputs immediately; do not pass raw dicts into the core logic.
- **Configuration First:**
    - **No Magic Values:** Do not hardcode numbers, timeouts, or paths deep in logic.
    - **Extraction:** Move them to `config.py`, `settings.py`, or class-level `CONSTANTS`.
- **Interfaces First:**
    - **Boundaries:** All external dependencies (DB, APIs, storage) MUST be typed as `Protocol` or `ABC` (Abstract Base Class).
    - **Usage:** Logic should depend on `RepositoryInterface`, never `SqlAlchemyRepository`.
- **No Global State:**
    - **Forbidden:** Singletons and mutable global variables.
    - **Avoid:** Static methods (`@staticmethod`) for logic that requires dependencies. Use instance methods or pure functions.
- **Dependency Injection:** Prefer passing dependencies explicitly over global state or side-channel imports.
- **Composition:** Prefer composition over deep inheritance hierarchies.
- **Error Handling (No Silent Failures):**
    - **Custom Exceptions:** Use domain-specific exceptions (e.g., `OrderProcessingError`) instead of generic `Exception`.
    - **No Swallowing:** Never use bare `except:` or `except Exception: pass`. Every catch MUST be handled (logged, retried, or re-raised).
    - **Context:** Exceptions must be raised with relevant state (e.g., `raise UserError("Invalid age", user_id=123)`).
    - **Traceability:** Always use `raise NewException(...) from original_err` to preserve stack traces.

## Testing Patterns
- **TDD Protocol (Mandatory):**
    1.  **Red:** Write the failing unit/integration test FIRST.
    2.  **Green:** Write the minimal code to pass the test.
    3.  **Refactor:** Improve code structure while keeping tests green.
- **Coverage:** No code is accepted without a passing test.
- **Framework:** `pytest` is the standard.
- **Mocks:** Use `unittest.mock` or `pytest-mock` to isolate units.
- **Fixtures:** Use `pytest` fixtures for setup/teardown logic.

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


# Project Specific Context
<!-- Add specific instructions for THIS project below -->
