# PHP Coding Standards

## Code Style
- **Standard:** Strictly follow PSR-12.
- **Strict Typing:** ALWAYS add `declare(strict_types=1);` at the top of every PHP file.
- **Type Declarations:** Use explicit types for all properties, arguments, and return values.
    - `public function getTotal(float $price): float`

## Architecture (Laravel/General)
- **Error Handling (Robust):**
    - **Custom Exceptions:** Create specific exception classes for domain failures.
    - **No Swallowing:** Never use empty `catch` blocks.
    - **Report/Render:** Use Laravel's `report()` helper for logging and custom `render()` methods for API error responses.
    - **Context:** Pass context to exceptions using properties or constructor arguments.
- **Boundary Validation (Fail-Fast):**
    - Use Form Requests or DTOs to validate all incoming request data.
    - Logic classes should only receive validated, typed objects, never raw arrays.
- **Configuration First:**
    - **No Magic Values:** Hardcoded strings/ints are forbidden in logic.
    - **Solution:** Use Laravel's `config()` files or class `const`.
- **Interfaces First:**
    - **Rule:** Type-hint Interfaces, NOT concrete classes.
    - **Example:** `function __construct(UserRepositoryInterface $users)` NOT `(UserRepository $users)`.
    - **Boundaries:** Services, Repositories, and External integrations MUST have a corresponding Interface.
- **No Static Cling:**
    - **Forbidden:** Singletons and static method calls for business logic (`Class::method()`).
    - **Preferred:** Constructor Injection for all dependencies.
    - **Facades:** Avoid Facades in domain logic; use the underlying Contract/Interface instead.
- **SOLID:** Adhere strictly to SOLID principles.
- **Thin Controllers:** Move business logic to Services, Actions, or Jobs. Controllers should only handle request/response.
- **Eloquent:** Use Relationships, Scopes, and Accessors. Avoid raw SQL.
- **DTOs:** Use Data Transfer Objects for passing complex data between layers.

## Testing Patterns
- **TDD Protocol (Mandatory):**
    1.  **Red:** Write the failing PEST/PHPUnit test FIRST.
    2.  **Green:** Write the minimal code to pass the test.
    3.  **Refactor:** Clean up.
- **Framework:** `Pest PHP` (preferred) or `PHPUnit`.
- **Strategy:** Write feature tests for endpoints and unit tests for complex logic/services.
- **Coverage:** Zero-Code without tests policy.
