import typer
from rich.console import Console
from rich.table import Table

from homebase.files import build_target_path, move_into_workspace, record_file
from homebase.storage import ensure_storage, read_contexts, write_contexts
from homebase.utils import expand_path, open_path


app = typer.Typer(help="Organize workspace files and todos by context.")
file_app = typer.Typer(help="Manage files in workspaces.")
app.add_typer(file_app, name="file")
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


@app.command()
def open(name: str, sub: str | None = typer.Option(None, "--sub")) -> None:
    """Open a workspace folder or subfolder."""
    ensure_storage()
    contexts = read_contexts()
    context = contexts.get(name)
    if context is None:
        console.print(f"[red]Workspace does not exist:[/red] {name}")
        raise typer.Exit(1)

    target = expand_path(context["folder"])
    if sub:
        target = target / sub
        if not target.exists():
            create = typer.confirm("Folder does not exist. Create it?", default=False)
            if not create:
                console.print("Canceled.")
                raise typer.Exit()
            target.mkdir(parents=True, exist_ok=True)

    try:
        open_path(target)
    except (FileNotFoundError, RuntimeError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@file_app.command("add")
def file_add(
    name: str,
    file: str | None = typer.Argument(None),
    into: str | None = typer.Option(None, "--into"),
    new_name: str | None = typer.Option(None, "--as"),
    apply: bool = typer.Option(False, "--apply"),
) -> None:
    """Preview or move a file into a workspace."""
    ensure_storage()
    contexts = read_contexts()
    context = contexts.get(name)
    if context is None:
        console.print(f"[red]Workspace does not exist:[/red] {name}")
        raise typer.Exit(1)

    interactive = file is None
    if interactive:
        file = typer.prompt("File or folder to add")
        into = typer.prompt(f"Subfolder inside {name}? leave blank for root", default="")
        into = into or None
        new_name = typer.prompt("Rename file? leave blank to keep original", default="")
        new_name = new_name or None

    source_path, target_path, relative_path = build_target_path(context, file, into, new_name)

    console.print("[bold]Preview:[/bold]")
    console.print()
    console.print("[bold]From:[/bold]")
    console.print(str(source_path))
    console.print()
    console.print("[bold]To:[/bold]")
    console.print(str(target_path))
    console.print()

    if not apply:
        if interactive and typer.confirm("Apply?", default=False):
            apply = True
        else:
            console.print("Dry run only. Add --apply to move the file.")
            raise typer.Exit()

    try:
        move_into_workspace(source_path, target_path)
    except (FileNotFoundError, FileExistsError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    record_file(context, relative_path)
    contexts[name] = context
    write_contexts(contexts)
    console.print(f"Moved: {source_path} -> {target_path}")


@file_app.command("list")
def file_list(name: str) -> None:
    """List recorded files in a workspace."""
    ensure_storage()
    contexts = read_contexts()
    context = contexts.get(name)
    if context is None:
        console.print(f"[red]Workspace does not exist:[/red] {name}")
        raise typer.Exit(1)

    console.print(f"[bold]Files in {name}:[/bold]")
    console.print()
    files = context.get("files", [])
    if not files:
        console.print("No files yet.")
        return
    for file_record in files:
        console.print(f"- {file_record.get('path', '')}")
