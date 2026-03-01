# Changelog

All notable changes to this project will be documented in this file.

## [0.1.2] - 2026-03-01

### Added
- URL parser (`parsers/urls.py`) — parses DRF `urls.py` patterns.
- URL wiring generator — produces `NinjaAPI` setup and `add_router()` calls.
- Permissions/auth parser — detects `permission_classes` and `authentication_classes`.
- Auth mapping generator — maps DRF permissions/auth to Ninja equivalents.
- Settings parser — extracts `REST_FRAMEWORK` config (pagination, throttling, filters).
- Settings migration report generator — actionable migration guide for each setting.
- `--urls` flag to compile DRF URL patterns.
- `--settings` flag to parse Django settings.
- `--style` flag (`router` or `api`) to choose between `@router.get()` and `@api.get()` syntax.
- `--dry-run` flag to preview output without writing files.
- `--output` flag to write generated files to a directory.
- `CONTRIBUTING.md` for open-source contributors.
- 22 comprehensive tests (up from 8).

## [0.1.1] - 2026-03-01

### Changed
- Renamed "HUMAN INTERVENTION REQUIRED" to "USER REVIEW REQUIRED" throughout generated output.
- Tightened CLI demo screenshot with no blank space.
- Fixed null-safety bug in router generator when `serializer_class` is not defined.

## [0.1.0] - 2026-03-01

### Added
- AST-based parsing of DRF `ModelSerializer`, `Serializer`, `APIView`, `ModelViewSet`, and `ViewSet`.
- Pydantic `ModelSchema` and `Schema` generation from parsed serializers.
- Django Ninja `@router` endpoint generation from parsed views.
- Automatic detection of custom fields, methods, and overrides with inline `TODO` comments.
- Beautiful CLI powered by `Typer` and `Rich` with syntax-highlighted output.
- Pre-commit hooks for `black` formatting and `bandit` security analysis.
- GitHub Actions CI pipeline across Python 3.10, 3.11, and 3.12.
