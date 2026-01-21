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