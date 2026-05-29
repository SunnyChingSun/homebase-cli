import typer
from rich.console import Console
from rich.table import Table

from homebase.storage import ensure_storage, read_contexts, write_contexts
from homebase.utils import expand_path


app = typer.Typer(help="Organize workspace files and todos by context.")
console = Console()


@app.callback()
def main() -> None:
    """Homebase command-line workspace manager."""


@app.command()
def add(name: str, folder: str) -> None:
    """Create a workspace."""
    ensure_storage()
    contexts = read_contexts()
    if name in contexts:
        console.print(f"[red]Workspace already exists:[/red] {name}")
        raise typer.Exit(1)

    workspace_folder = expand_path(folder)
    workspace_folder.mkdir(parents=True, exist_ok=True)
    contexts[name] = {
        "folder": str(workspace_folder),
        "files": [],
        "todos": [],
        "links": [],
    }
    write_contexts(contexts)
    console.print(f"Added workspace [bold]{name}[/bold]: {workspace_folder}")


@app.command("list")
def list_workspaces() -> None:
    """List all workspaces."""
    ensure_storage()
    contexts = read_contexts()
    table = Table(title="Homebase Workspaces")
    table.add_column("Name")
    table.add_column("Folder")
    table.add_column("Todos", justify="right")
    table.add_column("Files", justify="right")

    for name, context in sorted(contexts.items()):
        table.add_row(
            name,
            str(context.get("folder", "")),
            str(len(context.get("todos", []))),
            str(len(context.get("files", []))),
        )

    console.print(table)


@app.command()
def show(name: str) -> None:
    """Show a workspace dashboard."""
    ensure_storage()
    contexts = read_contexts()
    context = contexts.get(name)
    if context is None:
        console.print(f"[red]Workspace does not exist:[/red] {name}")
        raise typer.Exit(1)

    console.print(f"[bold]{name.upper()}[/bold]")
    console.print(f"Folder: {context.get('folder', '')}")
    console.print()

    console.print("[bold]Files:[/bold]")
    files = context.get("files", [])
    if files:
        for file_record in files:
            console.print(f"- {file_record.get('path', '')}")
    else:
        console.print("No files yet.")
    console.print()

    console.print("[bold]Todos:[/bold]")
    todos = context.get("todos", [])
    if todos:
        for todo in todos:
            status = "x" if todo.get("done") else " "
            due = todo.get("due") or "no due date"
            console.print(f"[{status}] {todo.get('id')}. {todo.get('text')} (due {due})")
            resources = todo.get("resources", [])
            if resources:
                console.print("    resources:")
                for resource in resources:
                    console.print(f"    - {resource.get('type')}: {resource.get('path')}")
    else:
        console.print("No todos yet.")
    console.print()

    console.print("[bold]Links:[/bold]")
    links = context.get("links", [])
    if links:
        for link in links:
            console.print(f"- {link.get('title')}: {link.get('url')}")
    else:
        console.print("No links yet.")
