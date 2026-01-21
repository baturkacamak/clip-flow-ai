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
