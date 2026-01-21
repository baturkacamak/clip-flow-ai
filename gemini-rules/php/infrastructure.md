# PHP Infrastructure

## 1. Project Management
- **Manager:** `composer`.
- **Config:** `composer.json` and `composer.lock` must be committed.
- **Task Runner:** `Justfile`
    ```makefile
    test:
        ./vendor/bin/pest
    lint:
        ./vendor/bin/pint
    ```

## 2. Versioning
- **Source:** Composer relies on Git Tags. Do not hardcode versions in `composer.json`.
- **Syncing:** Use `bump-my-version` if you need to sync `README.md` or strict PHP constant files with the git tag.

## 3. Quality & Linting
- **Linter:** `laravel/pint` (for Laravel) or `friendsofphp/php-cs-fixer`.
- **Static Analysis:** `phpstan/phpstan` (Level 5+) or `larastan`.
- **Pre-commit:**
    ```yaml
    repos:
      - repo: local
        hooks:
          - id: pest
            name: pest
            entry: ./vendor/bin/pest
            language: system
            pass_filenames: false
            always_run: true
    ```

## 3. CI/CD Implementation
- **Setup:**
    ```yaml
    - uses: shivammathur/setup-php@v2
      with:
        php-version: '8.2'
    ```
- **Dependencies:** `composer install --no-ansi --no-interaction --no-progress --prefer-dist`
- **Test Command:** `php artisan test` or `./vendor/bin/pest`.

## 4. Containerization
- **Base Image:** `FROM php:8.2-fpm` (or appropriate version).
- **Extensions:** Use `mlocati/docker-php-extension-installer` for easy extension management.
