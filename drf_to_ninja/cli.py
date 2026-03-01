import sys
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from drf_to_ninja.parsers.serializers import parse_serializers
from drf_to_ninja.generators.schemas import generate_schemas
from drf_to_ninja.parsers.views import parse_views
from drf_to_ninja.generators.routers import generate_routers
from drf_to_ninja.parsers.urls import parse_urls
from drf_to_ninja.generators.urls import generate_url_wiring
from drf_to_ninja.parsers.permissions import parse_permissions
from drf_to_ninja.parsers.settings import parse_settings
from drf_to_ninja.generators.auth import generate_auth, generate_settings_report

app = typer.Typer(
    name="drf2ninja",
    help="🤖 DRF to Django Ninja Compiler: Intelligently migrate your legacy APIs with a beautiful, user-friendly DX.",
    add_completion=False,
)
console = Console()


def display_code_panel(title: str, code: str, language: str = "python"):
    """Displays generated code beautifully with syntax highlighting."""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    panel = Panel(
        syntax,
        title=f"[cyan bold]{title}[/cyan bold]",
        border_style="cyan",
        expand=False,
    )
    console.print(panel)


def write_output(filename: str, content: str, output_dir: Path, dry_run: bool):
    """Write generated content to a file, or preview it in dry-run mode."""
    if dry_run:
        console.print(f"[dim]  (dry-run) Would write to [cyan]{output_dir / filename}[/cyan][/dim]")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / filename
    target.write_text(content)
    console.print(f"  [green]✓[/green] Wrote [cyan]{target}[/cyan]")


@app.command()
def compile(
    serializers: str = typer.Option(
        None,
        "--serializers",
        "-s",
        help="Path to the DRF serializers.py file to compile to Ninja Schemas.",
    ),
    views: str = typer.Option(
        None,
        "--views",
        "-v",
        help="Path to the DRF views.py file to compile to Ninja Routers.",
    ),
    urls: str = typer.Option(
        None,
        "--urls",
        "-u",
        help="Path to the DRF urls.py file to generate Ninja API wiring.",
    ),
    style: str = typer.Option(
        "router",
        "--style",
        help="Output style: 'router' for @router.get() or 'api' for @api.get().",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the generated output without writing any files.",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Directory to write generated files to. If not set, output is printed to the console.",
    ),
    settings: str = typer.Option(
        None,
        "--settings",
        help="Path to Django settings.py to parse REST_FRAMEWORK config.",
    ),
    project: str = typer.Option(
        None,
        "--project",
        "-p",
        help="Path to a Django app directory. Auto-detects serializers.py, views.py, urls.py, and settings.py.",
    ),
):
    """
    Parses complex Django Rest Framework code and seamlessly outputs modern, fast Django Ninja code.
    """
    if project:
        project_path = Path(project)
        if not project_path.is_dir():
            console.print(f"[bold red]Not a directory:[/bold red] {project_path}")
            raise typer.Exit(code=1)
        for fname, flag in [
            ("serializers.py", "serializers"),
            ("views.py", "views"),
            ("urls.py", "urls"),
            ("settings.py", "settings"),
        ]:
            candidate = project_path / fname
            if candidate.exists() and not locals().get(flag):
                if fname == "serializers.py":
                    serializers = str(candidate)
                elif fname == "views.py":
                    views = str(candidate)
                elif fname == "urls.py":
                    urls = str(candidate)
                elif fname == "settings.py":
                    settings = str(candidate)
        console.print(f"[dim]  Scanning project directory: [cyan]{project_path}[/cyan][/dim]")

    if not serializers and not views and not urls and not settings:
        console.print(
            Panel(
                "[bold red]Oops![/bold red] You need to provide something to compile.\n"
                "Try passing [cyan]--serializers path/to/serializers.py[/cyan] or [cyan]--views path/to/views.py[/cyan].",
                title="Authentication Error... wait, no just a user error",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    if style not in ("router", "api"):
        console.print("[bold red]Invalid style.[/bold red] Use 'router' or 'api'.")
        raise typer.Exit(code=1)

    console.print()
    console.print(Text("DRF to Ninja Compiler 🚀", style="bold green justify center"))
    console.print()

    if dry_run:
        console.print("[dim italic]  Running in dry-run mode — no files will be written.[/dim italic]")
        console.print()

    output_dir = Path(output) if output else None

    # --- Compile Serializers ---
    if serializers:
        serializer_path = Path(serializers)
        if not serializer_path.exists():
            console.print(f"[bold red]File not found:[/bold red] {serializer_path}")
            raise typer.Exit(code=1)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(
                description=f"Ingesting Serializers from [magenta]{serializer_path.name}[/magenta]...",
                total=None,
            )

            try:
                serializers_data = parse_serializers(str(serializer_path))
                schema_code = generate_schemas(serializers_data)
            except Exception as e:
                console.print(f"[bold red]Fatal parsing error:[/bold red] {str(e)}")
                raise typer.Exit(code=1)

        display_code_panel("✨ Generated Pydantic Schemas", schema_code)
        if output_dir:
            write_output("schemas.py", schema_code, output_dir, dry_run)

    # --- Compile Views ---
    if views:
        view_path = Path(views)
        if not view_path.exists():
            console.print(f"[bold red]File not found:[/bold red] {view_path}")
            raise typer.Exit(code=1)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(
                description=f"Reverse Engineering ViewSets from [magenta]{view_path.name}[/magenta]...",
                total=None,
            )

            try:
                views_data = parse_views(str(view_path))
                router_code = generate_routers(views_data, style=style)
            except Exception as e:
                console.print(f"[bold red]Fatal parsing error:[/bold red] {str(e)}")
                raise typer.Exit(code=1)

        display_code_panel("⚡ Generated Ninja Routers", router_code)
        if output_dir:
            write_output("api.py", router_code, output_dir, dry_run)

    # --- Compile URLs ---
    if urls:
        url_path = Path(urls)
        if not url_path.exists():
            console.print(f"[bold red]File not found:[/bold red] {url_path}")
            raise typer.Exit(code=1)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(
                description=f"Extracting URL patterns from [magenta]{url_path.name}[/magenta]...",
                total=None,
            )

            try:
                url_patterns = parse_urls(str(url_path))
                url_code = generate_url_wiring(url_patterns)
            except Exception as e:
                console.print(f"[bold red]Fatal parsing error:[/bold red] {str(e)}")
                raise typer.Exit(code=1)

        display_code_panel("🔗 Generated Ninja URL Wiring", url_code)
        if output_dir:
            write_output("urls.py", url_code, output_dir, dry_run)

    # --- Parse Settings ---
    if settings:
        settings_path = Path(settings)
        if not settings_path.exists():
            console.print(f"[bold red]File not found:[/bold red] {settings_path}")
            raise typer.Exit(code=1)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(
                description=f"Parsing REST_FRAMEWORK config from [magenta]{settings_path.name}[/magenta]...",
                total=None,
            )

            try:
                settings_data = parse_settings(str(settings_path))
                settings_report = generate_settings_report(settings_data)
            except Exception as e:
                console.print(f"[bold red]Fatal parsing error:[/bold red] {str(e)}")
                raise typer.Exit(code=1)

        display_code_panel("📋 DRF Settings Migration Report", settings_report)
        if output_dir:
            write_output("migration_report.py", settings_report, output_dir, dry_run)

    # --- Extract permissions from views (runs automatically if views are provided) ---
    if views:
        try:
            perms_data = parse_permissions(str(view_path))
            if perms_data:
                auth_code = generate_auth(perms_data)
                display_code_panel("🔐 Auth & Permission Mapping", auth_code)
                if output_dir:
                    write_output("auth.py", auth_code, output_dir, dry_run)
        except (FileNotFoundError, SyntaxError, ValueError):
            pass


def main():
    app()


if __name__ == "__main__":
    main()
