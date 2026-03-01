# 🤖 DRF to Django Ninja Compiler

[![CI](https://github.com/lektronik/drf-to-ninja-compiler/actions/workflows/ci.yml/badge.svg)](https://github.com/lektronik/drf-to-ninja-compiler/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

An intelligent, user-friendly compiler tool designed to automatically parse Django Rest Framework (DRF) code (`serializers.py`, `views.py`, `urls.py`, `settings.py`) and convert it into modern, fast Django Ninja equivalents (`schemas.py`, `api.py`).

Tired of manually migrating hundreds of legacy DRF endpoints? This tool automates the heavy lifting by leveraging Abstract Syntax Tree (AST) parsing to reverse-engineer your code.

<p align="center">
  <img src="https://raw.githubusercontent.com/lektronik/drf-to-ninja-compiler/main/docs/cli_demo.svg" alt="CLI Demo" width="800">
</p>

## ✨ Features
- **Pydantic Schemas:** Parses DRF `ModelSerializer` and generates standard Ninja `ModelSchema`.
- **Nested Serializer Detection:** Detects nested `Serializer()` fields (with `many=True`) and `Meta.depth`.
- **Intelligent Routing:** Parses `APIView`, `ModelViewSet`, and all `GenericAPIView` variants (`ListCreateAPIView`, `RetrieveUpdateDestroyAPIView`, etc.).
- **`@action` Support:** Detects custom ViewSet `@action` decorators and generates dedicated routes.
- **URL Wiring:** Parses `urls.py` and generates `NinjaAPI` setup with router registration.
- **Auth & Permissions:** Detects `permission_classes` and `authentication_classes` and maps them to Ninja equivalents.
- **Settings Migration:** Parses `REST_FRAMEWORK` settings dict and generates a migration report (pagination, throttling, filters).
- **User Review:** Automatically flags custom overrides (like `SerializerMethodField` or custom View methods) and injects helpful `TODO` comments so you know exactly what needs manual review.
- **Batch Mode:** `--project` flag scans an entire Django app directory and auto-detects all DRF files.
- **Beautiful DX:** Powered by `Typer` and `Rich` for a stunning terminal experience.
- **47 Tests:** Comprehensive test suite with `CliRunner` integration tests.

## � Before & After

**Your legacy DRF code:**
```python
# serializers.py
class OrderSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'status', 'total']

    def get_total(self, obj):
        return sum(item.price for item in obj.items.all())
```

**What the compiler generates:**
```python
# schemas.py (auto-generated)
class OrderSchema(ModelSchema):
    # ⚠️ USER REVIEW REQUIRED:
    # The compiler detected custom fields or methods in the DRF Serializer:
    #  - total
    #  - method:get_total
    # You will need to manually map these to Pydantic types or Resolve() blocks.
    class Meta:
        model = Order
        fields = ['id', 'status', 'total']
```

**Your legacy DRF ViewSet:**
```python
# views.py
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def list(self, request): ...
    def create(self, request): ...
```

**What the compiler generates:**
```python
# api.py (auto-generated)
@router.get('/order/', response=list[OrderSchema])
def list_order(request):
    """Automatically generated list view for OrderViewSet."""
    return Order.objects.all()

@router.post('/order/', response=OrderSchema)
def create_order(request, payload: OrderInSchema):
    """Automatically generated create view for OrderViewSet."""
    # TODO: Implement creation logic using payload.dict()
    pass
```

## 🚀 Installation

```bash
# Install from PyPI (recommended)
pip install drf-to-ninja

# Or install from source for development
git clone https://github.com/lektronik/drf-to-ninja-compiler.git
cd drf-to-ninja-compiler
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## 🛠 Usage

Simply point the compiler at your existing DRF files:

```bash
# Full migration — serializers, views, urls, and settings
drf2ninja -s myapp/serializers.py -v myapp/views.py -u myapp/urls.py --settings myapp/settings.py

# Use @api.get() syntax instead of @router.get()
drf2ninja -s myapp/serializers.py -v myapp/views.py --style api

# Preview without writing files
drf2ninja -s myapp/serializers.py --dry-run

# Write generated files to a directory
drf2ninja -s myapp/serializers.py -v myapp/views.py -o ./ninja_output/

# Scan entire Django app directory (auto-detects serializers, views, urls, settings)
drf2ninja --project myapp/
```

| Flag | Description |
|---|---|
| `-s, --serializers` | Path to DRF `serializers.py` |
| `-v, --views` | Path to DRF `views.py` |
| `-u, --urls` | Path to DRF `urls.py` |
| `--settings` | Path to Django `settings.py` |
| `--style` | Output style: `router` (default) or `api` |
| `--dry-run` | Preview output without writing files |
| `-o, --output` | Directory to write generated files |
| `-p, --project` | Scan a Django app directory (auto-detect all files) |

## 📖 Step-by-Step Migration Guide

This is the recommended workflow to migrate a DRF app to Django Ninja:

### Step 1: Run the Compiler

```bash
drf2ninja -s myapp/serializers.py -v myapp/views.py -u myapp/urls.py --settings myapp/settings.py -o ./ninja_output/
```

This generates four files in `./ninja_output/`:
- `schemas.py` — Pydantic schemas (replaces serializers)
- `api.py` — Ninja route handlers (replaces views)
- `urls.py` — NinjaAPI wiring (replaces DRF router config)
- `migration_report.py` — Settings migration guide

### Step 2: Handle Flagged Code

The compiler flags anything it can't fully auto-translate with a `⚠️ USER REVIEW REQUIRED` comment. Here's what to do for each case:

| Flagged Pattern | What It Means | What To Do |
|---|---|---|
| `SerializerMethodField` | A computed field using `get_*()` | Use a [Resolver](https://django-ninja.dev/guides/response/resolvers/) in your Schema |
| Custom `validate_*()` | DRF field validator | Use Pydantic's `@field_validator` decorator |
| `perform_create()` / `perform_update()` | Custom save logic in ViewSet | Move the logic into your Ninja route function body |
| Custom `@action` methods | Extra ViewSet endpoints | Create a separate `@router.get()` / `@router.post()` for each |
| `permission_classes` | DRF permission check | Use Ninja's `auth=` parameter or custom auth callables |
| `authentication_classes` | DRF auth backend | Use `HttpBearer`, `django_auth`, or `HttpBasicAuth` from `ninja.security` |
| `DEFAULT_THROTTLE_CLASSES` | DRF throttling | Use `django-ninja-extra` or custom middleware (Ninja has no built-in throttle) |
| `DEFAULT_FILTER_BACKENDS` | DRF filter backends | Use `FilterSchema` or manual query parameters in Ninja |

### Step 3: Wire the API

In your main `urls.py`, add the Ninja API:

```python
# urls.py
from ninja_output.api import router  # or api, depending on --style

from ninja import NinjaAPI

api = NinjaAPI()
api.add_router("/", router)

urlpatterns = [
    path("api/", api.urls),
]
```

### Step 4: Install Django Ninja

```bash
pip install django-ninja
```

Add `"ninja"` to `INSTALLED_APPS` in `settings.py` and run your project:

```bash
python manage.py runserver
```

Your new API documentation is automatically available at `/api/docs`.

### Step 5: Verify and Clean Up

- Visit `/api/docs` to confirm all endpoints are live
- Run your existing test suite to catch regressions
- Remove old DRF code once everything works
- Uninstall DRF: `pip uninstall djangorestframework`

## 🔒 Security & Code Quality
This project uses `pre-commit` hooks to ensure code quality and security.
- **Formatting:** `black`
- **Security Analysis:** `bandit`

To set up the hooks locally:
```bash
pip install pre-commit
pre-commit install
```

## 🤝 Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

```bash
pytest tests/  # Run the test suite (22 tests)
```

