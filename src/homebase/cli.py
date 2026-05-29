import typer
from rich.console import Console


app = typer.Typer(help="Organize workspace files and todos by context.")
console = Console()


@app.callback()
def main() -> None:
    """Homebase command-line workspace manager."""

