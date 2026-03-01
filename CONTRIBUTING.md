# Contributing to DRF to Django Ninja Compiler

Thanks for your interest! Here's how to contribute.

## Setup

```bash
git clone https://github.com/lektronik/drf-to-ninja-compiler.git
cd drf-to-ninja-compiler
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Development Workflow

1. Create a branch for your feature: `git checkout -b feature/your-feature`
2. Write your code and add tests in `tests/test_compiler.py`
3. Run the test suite: `pytest tests/ -v`
4. Format your code: `black .`
5. Run security scan: `bandit -r drf_to_ninja/`
6. Submit a pull request

## Project Structure

```
drf_to_ninja/
├── cli.py                  # Typer CLI entrypoint
├── parsers/
│   ├── serializers.py      # DRF Serializer → AST parser
│   ├── views.py            # DRF View/ViewSet → AST parser
│   ├── urls.py             # DRF urls.py → AST parser
│   ├── permissions.py      # DRF permissions/auth → AST parser
│   └── settings.py         # REST_FRAMEWORK settings → parser
├── generators/
│   ├── schemas.py           # Pydantic Schema generator
│   ├── routers.py           # Ninja Router/@api generator
│   ├── urls.py              # NinjaAPI wiring generator
│   └── auth.py              # Auth mapping + settings report
```

## Adding a New Parser

1. Create a new file in `drf_to_ninja/parsers/`
2. Use Python's `ast` module to walk the AST tree
3. Return a list of dictionaries with the parsed data
4. Add corresponding generator in `drf_to_ninja/generators/`
5. Wire it into `cli.py`
6. Add tests in `tests/test_compiler.py`

## Code Quality

- **Formatting:** We use `black` — run `black .` before committing
- **Security:** We use `bandit` — no high-severity issues allowed
- **Tests:** All PRs must pass the existing test suite plus add tests for new features

## Reporting Issues

Open an issue on GitHub with:
- What you tried to compile (the DRF code)
- What the compiler generated
- What you expected instead
