# React Infrastructure

## 1. Project Management
- **Manager:** `npm`, `yarn`, or `pnpm` (ensure lockfile is committed).
- **Manifest:** `package.json`.
- **Task Runner:** `Justfile`
    ```makefile
    test:
        npm run test
    lint:
        npm run lint
    build:
        npm run build
    ```

## 2. Versioning
- **Strategy:** Use `npm version` (patch|minor|major) to bump `package.json` and create Git tags simultaneously.
- **Automation:** Use `release-it` or `standard-version` for advanced changelog generation and file syncing.

## 3. Quality & Linting
- **Linter:** `eslint` with React and Accessibility (a11y) plugins.
- **Formatter:** `prettier`.
- **Pre-commit:** `lint-staged` to run linters on changed files only.
    ```yaml
    repos:
      - repo: local
        hooks:
          - id: test
            name: test
            entry: npm run test
            language: system
            pass_filenames: false
            always_run: true
    ```

## 3. CI/CD Implementation
- **Setup:**
    ```yaml
    - uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
    ```
- **Build:** `npm run build` (Must pass without errors).
- **Test:** `npm run test` (Vitest or Jest).

## 4. Containerization (Frontend)
- **Build Stage:** Node image to build static assets.
- **Serve Stage:** Nginx alpine image to serve the `dist/` or `build/` folder.
