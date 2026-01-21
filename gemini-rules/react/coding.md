# React & TypeScript Coding Standards

## Code Style
- **Components:** Functional Components with Hooks ONLY. No Class components.
- **Language:** TypeScript (`.tsx`, `.ts`) is mandatory.
- **Types:**
    - Use `interface` for public API definitions (props, state).
    - Use `type` for unions, intersections, and primitives.

## Architecture & Patterns
- **Error Handling (Resilient):**
    - **Boundaries:** Use React Error Boundaries to catch UI crashes.
    - **Async:** Always use `try/catch` or `.catch()` for API calls; never assume a successful response.
    - **User Feedback:** All errors must trigger a user-facing notification (Toast, Alert) or a fallback state.
    - **Strict Typing:** Define error types/interfaces for API error responses.
- **Boundary Validation (Fail-Fast):**
    - Use Zod or Yup for schema validation on all API responses and form inputs.
    - Ensure TypeScript types match the runtime validation schemas.
- **Configuration First:**
    - **No Magic Values:** Do not hardcode URLs, timeouts, or magic numbers (e.g., `1000` for debounce) in components.
    - **Extraction:** Use `.env` files or a central `config/` or `constants/` directory.
- **Interfaces for Dependencies:**
    - API clients and Services should be defined by `interface` to allow mocking in tests.
    - Example: `useAuth(service: AuthProvider)` where `AuthProvider` is an interface.

## State & Data
- **Local State:** `useState` for simple UI state.
- **Global State:** `useContext` + `useReducer` for moderate complexity. External libraries (Zustand/Redux) only if strictly needed.
- **Side Effects:** encapsulate `useEffect` logic in custom hooks (e.g., `useWindowSize`).

## Performance
- **Memoization:** Use `useMemo` and `useCallback` strategically, not by default.
- **Keys:** Never use array index as keys for lists if the list can change.

## Styling
- **Approach:** CSS Modules, Tailwind CSS, or Styled Components (Project specific, but stick to one).

## Testing & TDD
- **TDD Protocol (Mandatory):**
    - Logic/Hooks: Write unit tests first (Vitest/Jest).
    - Components: Write interaction tests first (Testing Library).
    - E2E: Write "User Journey" tests first (Playwright/Cypress) for critical paths (ATDD).
- **Tooling:** Vitest (Unit), React Testing Library (Component), Playwright (E2E).
- **Rule:** No component is complete without a corresponding test file.
