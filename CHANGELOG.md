# Changelog

## [0.3.0] — 2026-03-01

### Added
- **Nested serializer detection** — detects nested `Serializer()` fields (with `many=True`) and `Meta.depth`
- **`@action` decorator support** — parses custom ViewSet actions and generates dedicated routes
- **GenericAPIView variants** — supports `ListAPIView`, `CreateAPIView`, `RetrieveUpdateDestroyAPIView`, and 6 more
- **`--project` batch mode** — scans an entire Django app directory, auto-detecting all DRF files
- **PATCH route generation** — `partial_update` now generates `@router.patch()` endpoints
- **Integration tests** — 9 end-to-end tests using `typer.testing.CliRunner`
- **47 total tests** (up from 22)

## [0.1.2] — 2026-03-01

### Added
- URL parser — parse `urls.py` patterns and generate NinjaAPI wiring
- Permissions/auth parser — detect `permission_classes` and map to Ninja equivalents
- Settings parser — extract `REST_FRAMEWORK` config and generate migration reports
- `--style api` — choose between `@router.get()` and `@api.get()` syntax
- `--dry-run` — preview output without writing files
- `--output` — write generated files to a directory
- `--settings` — parse Django settings.py
- CONTRIBUTING.md for open-source contributors
- Step-by-step migration guide in README

## [0.1.0] — 2026-02-28

### Added
- Initial release
- Serializer parser (AST-based) with custom field detection
- View parser for `APIView` and `ModelViewSet`
- Schema generator (`ModelSchema`, `Schema`)
- Router generator (`@router` syntax)
- Rich-powered CLI with `Typer`
- CI/CD with GitHub Actions
- Pre-commit hooks (`black`, `bandit`)
