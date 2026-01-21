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
