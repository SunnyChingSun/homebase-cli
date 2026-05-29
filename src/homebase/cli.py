import shutil
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table

from homebase.files import (
    build_target_path,
    move_into_workspace,
    record_file,
    relative_to_workspace,
    remove_file_record,
)
from homebase.storage import (
    ensure_storage,
    read_contexts,
    read_history,
    write_contexts,
    write_history,
)
from homebase.todos import add_todo, find_todo, resource_for_path
from homebase.utils import expand_path, open_path


app = typer.Typer(help="Organize workspace files and todos by context.")
file_app = typer.Typer(help="Manage files in workspaces.")
todo_app = typer.Typer(help="Manage workspace todos.")
app.add_typer(file_app, name="file")
app.add_typer(todo_app, name="todo")
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
            console.print(
                f"[{status}] {todo.get('id')}. {todo.get('text')} (due {due})",
                markup=False,
            )
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
    todo_text: str | None = typer.Option(None, "--todo"),
    due: str | None = typer.Option(None, "--due"),
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
        if typer.confirm("Create a todo for this file?", default=False):
            todo_text = typer.prompt("Todo title")
            due = typer.prompt("Due date? optional", default="")
            due = due or None

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
    if todo_text:
        add_todo(
            context,
            todo_text,
            due=due,
            resources=[{"type": "folder" if target_path.is_dir() else "file", "path": relative_path}],
        )
    contexts[name] = context
    write_contexts(contexts)

    history = read_history()
    history.append(
        {
            "old_path": str(source_path),
            "new_path": str(target_path),
            "workspace": name,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    write_history(history)
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


@todo_app.command("add")
def todo_add(
    name: str,
    text: str | None = typer.Argument(None),
    due: str | None = typer.Option(None, "--due"),
    attach: list[str] | None = typer.Option(None, "--attach"),
) -> None:
    """Add a todo to a workspace."""
    ensure_storage()
    contexts = read_contexts()
    context = contexts.get(name)
    if context is None:
        console.print(f"[red]Workspace does not exist:[/red] {name}")
        raise typer.Exit(1)

    if text is None:
        text = typer.prompt("Todo title")
        due = typer.prompt("Due date? optional", default="")
        due = due or None
        attachments: list[str] = []
        if typer.confirm("Attach resources?", default=False):
            while True:
                attachments.append(typer.prompt("Resource path inside workspace"))
                if not typer.confirm("Add another resource?", default=False):
                    break
        attach = attachments
        if not typer.confirm("Create?", default=True):
            console.print("Canceled.")
            raise typer.Exit()

    resources = [resource_for_path(context, item) for item in (attach or [])]
    todo = add_todo(context, text, due=due, resources=resources)
    contexts[name] = context
    write_contexts(contexts)
    console.print(f"Added todo {todo['id']}: {todo['text']}")


@todo_app.command("list")
def todo_list(name: str) -> None:
    """List todos in a workspace."""
    ensure_storage()
    contexts = read_contexts()
    context = contexts.get(name)
    if context is None:
        console.print(f"[red]Workspace does not exist:[/red] {name}")
        raise typer.Exit(1)

    console.print(f"[bold]{name.upper()} Todos[/bold]")
    console.print()
    todos = context.get("todos", [])
    if not todos:
        console.print("No todos yet.")
        return
    for todo in todos:
        status = "x" if todo.get("done") else " "
        due_text = f"due {todo.get('due')}" if todo.get("due") else "no due date"
        console.print(
            f"[{status}] {todo.get('id')}. {todo.get('text')} ({due_text})",
            markup=False,
        )
        resources = todo.get("resources", [])
        if resources:
            console.print("    resources:")
            for resource in resources:
                console.print(f"    - {resource.get('type')}: {resource.get('path')}")


@todo_app.command("done")
def todo_done(name: str, todo_id: int) -> None:
    """Mark a todo done."""
    ensure_storage()
    contexts = read_contexts()
    context = contexts.get(name)
    if context is None:
        console.print(f"[red]Workspace does not exist:[/red] {name}")
        raise typer.Exit(1)

    todo = find_todo(context, todo_id)
    if todo is None:
        console.print(f"[red]Todo ID does not exist:[/red] {todo_id}")
        raise typer.Exit(1)

    todo["done"] = True
    contexts[name] = context
    write_contexts(contexts)
    console.print(f"Done: {todo.get('text')}")


@todo_app.command("open")
def todo_open(name: str, todo_id: int) -> None:
    """Open a resource attached to a todo."""
    ensure_storage()
    contexts = read_contexts()
    context = contexts.get(name)
    if context is None:
        console.print(f"[red]Workspace does not exist:[/red] {name}")
        raise typer.Exit(1)

    todo = find_todo(context, todo_id)
    if todo is None:
        console.print(f"[red]Todo ID does not exist:[/red] {todo_id}")
        raise typer.Exit(1)

    resources = todo.get("resources", [])
    if not resources:
        console.print("This todo has no resources.")
        return

    resource = resources[0]
    if len(resources) > 1:
        console.print("This todo has multiple resources:")
        console.print()
        for index, item in enumerate(resources, start=1):
            console.print(f"[{index}] {item.get('type')}: {item.get('path')}")
        choice = int(typer.prompt("Open which one?"))
        if choice < 1 or choice > len(resources):
            console.print("[red]Invalid choice.[/red]")
            raise typer.Exit(1)
        resource = resources[choice - 1]

    target = expand_path(context["folder"]) / resource["path"]
    try:
        open_path(target)
    except (FileNotFoundError, RuntimeError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command()
def check() -> None:
    """Show unfinished todos across all workspaces."""
    ensure_storage()
    contexts = read_contexts()
    rows = []
    for workspace, context in contexts.items():
        for todo in context.get("todos", []):
            if todo.get("done"):
                continue
            resources = ", ".join(resource.get("path", "") for resource in todo.get("resources", []))
            rows.append(
                {
                    "workspace": workspace,
                    "id": str(todo.get("id")),
                    "text": str(todo.get("text")),
                    "due": todo.get("due") or "none",
                    "resources": resources,
                    "sort_due": todo.get("due") or "9999-99-99",
                    "has_due": 0 if todo.get("due") else 1,
                }
            )

    rows.sort(key=lambda row: (row["has_due"], row["sort_due"], row["workspace"], row["id"]))

    table = Table(title="Todo Check")
    table.add_column("Workspace")
    table.add_column("ID", justify="right")
    table.add_column("Todo")
    table.add_column("Due")
    table.add_column("Resources")
    for row in rows:
        table.add_row(row["workspace"], row["id"], row["text"], row["due"], row["resources"])
    console.print(table)


@app.command()
def undo() -> None:
    """Undo the latest file move."""
    ensure_storage()
    history = read_history()
    if not history:
        console.print("No history to undo.")
        return

    latest = history[-1]
    old_path = expand_path(latest["old_path"])
    new_path = expand_path(latest["new_path"])

    if not new_path.exists():
        console.print(f"[red]Undo target no longer exists:[/red] {new_path}")
        raise typer.Exit(1)
    if old_path.exists():
        console.print(f"[red]Original path already exists:[/red] {old_path}")
        raise typer.Exit(1)

    old_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(new_path), str(old_path))

    contexts = read_contexts()
    workspace = latest.get("workspace")
    context = contexts.get(workspace)
    if context is not None:
        workspace_folder = expand_path(context["folder"])
        relative_path = relative_to_workspace(new_path, workspace_folder)
        remove_file_record(context, relative_path)
        contexts[workspace] = context
        write_contexts(contexts)

    write_history(history[:-1])
    console.print("Undo complete:")
    console.print(str(new_path))
    console.print(f"-> {old_path}")
