# Codex Instructions for Homebase CLI

You are working on a Python command-line tool called **Homebase**.

Homebase is a context-based file and todo manager. Users create named workspaces for classes, projects, career goals, or life areas. Each workspace points to a real local folder. Users can then move files into that workspace, optionally into subfolders, optionally rename them, and create todos connected to files or folders.

The CLI command should be:

```bash
hb
```

The project must be managed with `uv`, installable as a Python package, and should use `typer` and `rich`.

---

## Main Goal

Build a clean, working MVP of Homebase with these features:

```bash
hb add NAME FOLDER
hb list
hb show NAME
hb open NAME
hb open NAME --sub SUBFOLDER

hb file add NAME FILE --into SUBFOLDER --as NEW_NAME --apply
hb file list NAME

hb todo add NAME TEXT --due DATE --attach PATH
hb todo list NAME
hb todo done NAME TODO_ID
hb todo open NAME TODO_ID

hb check
hb undo
```

Optional if time:

```bash
hb link add NAME TITLE URL
hb link list NAME
```

---

## Core Idea

A workspace is a named context.

Example:

```bash
hb add math189 ~/Documents/School/MATH189
hb add islenet ~/Documents/Projects/IsleNet
hb add career ~/Documents/Career
```

This means:

```text
math189 -> ~/Documents/School/MATH189
islenet -> ~/Documents/Projects/IsleNet
career  -> ~/Documents/Career
```

After a workspace exists, the user can add files or todos to it.

Example:

```bash
hb file add math189 ~/Downloads/hw3.pdf --into homework --apply
```

This should move:

```text
~/Downloads/hw3.pdf
-> ~/Documents/School/MATH189/homework/hw3.pdf
```

Example with todo:

```bash
hb file add math189 ~/Downloads/hw3.pdf \
  --into homework \
  --todo "Finish HW3" \
  --due 2026-06-10 \
  --apply
```

This should:

1. Move the file into the workspace.
2. Record the file under the workspace.
3. Create a todo attached to that file.

---

## Design Principles

1. Keep the tool simple.
2. Do not auto-add dates to filenames.
3. By default, keep the original filename.
4. Only rename if the user provides `--as`.
5. Do not try to magically guess where a file belongs.
6. The user explicitly chooses a workspace name.
7. Never overwrite files by default.
8. File move commands should preview by default.
9. Only actually move files when `--apply` is used.
10. Save file move history so `hb undo` can restore the latest move.
11. Store file paths relative to the workspace folder when possible.
12. Add interactive prompts when required arguments are missing.

---

## Project Setup

Use this structure:

```text
homebase-cli/
├── README.md
├── CODEX.md
├── pyproject.toml
└── src/
    └── homebase/
        ├── __init__.py
        ├── cli.py
        ├── storage.py
        ├── utils.py
        └── files.py
```

Use these dependencies:

```bash
uv add typer rich
```

In `pyproject.toml`, add:

```toml
[project.scripts]
hb = "homebase.cli:app"
```

The tool should run with:

```bash
uv run hb --help
```

---

## Storage

Store app data locally in:

```text
~/.homebase/
├── contexts.json
└── history.json
```

### `contexts.json`

This stores workspaces.

Example:

```json
{
  "math189": {
    "folder": "~/Documents/School/MATH189",
    "files": [
      {
        "path": "homework/hw3.pdf",
        "added_at": "2026-05-28"
      }
    ],
    "todos": [
      {
        "id": 1,
        "text": "Finish HW3",
        "due": "2026-06-10",
        "done": false,
        "resources": [
          {
            "type": "file",
            "path": "homework/hw3.pdf"
          }
        ]
      }
    ],
    "links": []
  }
}
```

### `history.json`

This stores file move history for undo.

Example:

```json
[
  {
    "old_path": "~/Downloads/hw3.pdf",
    "new_path": "~/Documents/School/MATH189/homework/hw3.pdf",
    "workspace": "math189",
    "timestamp": "2026-05-28T18:30:00"
  }
]
```

---

## Commands

### `hb add NAME FOLDER`

Create a workspace.

Example:

```bash
hb add math189 ~/Documents/School/MATH189
```

Expected behavior:

* Create the folder if it does not exist.
* Add the workspace to `contexts.json`.
* Initialize `files`, `todos`, and `links` as empty lists.
* If the workspace already exists, show an error.

---

### `hb list`

List all workspaces using `rich.Table`.

Columns:

```text
Name
Folder
Todos
Files
```

---

### `hb show NAME`

Show a workspace dashboard.

Display:

```text
Workspace name
Folder
Files
Todos
Links
```

Example output:

```text
MATH189
Folder: ~/Documents/School/MATH189

Files:
- homework/hw3.pdf

Todos:
[ ] 1. Finish HW3 (due 2026-06-10)
    resources:
    - file: homework/hw3.pdf

Links:
No links yet.
```

---

### `hb open NAME`

Open the workspace folder.

Example:

```bash
hb open math189
```

On macOS, use:

```python
subprocess.run(["open", str(path)])
```

Also support Linux with `xdg-open` if easy.

---

### `hb open NAME --sub SUBFOLDER`

Open a subfolder inside the workspace.

Example:

```bash
hb open math189 --sub homework
```

Target:

```text
~/Documents/School/MATH189/homework
```

If the subfolder does not exist, ask:

```text
Folder does not exist. Create it? [y/N]
```

If yes, create and open it. If no, cancel.

---

## File Commands

Use a Typer sub-app:

```bash
hb file ...
```

---

### `hb file add NAME [FILE]`

Move a file or folder into a workspace.

Example:

```bash
hb file add math189 ~/Downloads/hw3.pdf --into homework --apply
```

Expected move:

```text
~/Downloads/hw3.pdf
-> ~/Documents/School/MATH189/homework/hw3.pdf
```

Options:

```text
--into SUBFOLDER
--as NEW_NAME
--todo TEXT
--due DATE
--apply
```

Behavior:

* If `--apply` is missing, only preview the move.
* If `--apply` is present, actually move the file.
* If `--into` is provided, place the file inside that subfolder.
* If the subfolder does not exist, create it.
* If `--as` is provided, rename the file to that name.
* If `--as` is not provided, keep the original filename.
* If `--todo` is provided, create a todo attached to the moved file.
* Do not overwrite existing files.
* Record the move in `history.json`.
* Record the file path in the workspace's `files` list.

Example dry run:

```bash
hb file add math189 ~/Downloads/hw3.pdf --into homework
```

Output:

```text
Preview:

From:
~/Downloads/hw3.pdf

To:
~/Documents/School/MATH189/homework/hw3.pdf

Dry run only. Add --apply to move the file.
```

Example with rename:

```bash
hb file add math189 ~/Downloads/final_final.pdf --into homework --as hw3.pdf --apply
```

Expected:

```text
~/Downloads/final_final.pdf
-> ~/Documents/School/MATH189/homework/hw3.pdf
```

Example with todo:

```bash
hb file add math189 ~/Downloads/hw3.pdf \
  --into homework \
  --todo "Finish HW3" \
  --due 2026-06-10 \
  --apply
```

Expected todo:

```json
{
  "id": 1,
  "text": "Finish HW3",
  "due": "2026-06-10",
  "done": false,
  "resources": [
    {
      "type": "file",
      "path": "homework/hw3.pdf"
    }
  ]
}
```

---

### Interactive `hb file add`

If user runs:

```bash
hb file add math189
```

Prompt:

```text
File or folder to add:
Subfolder inside math189? leave blank for root:
Rename file? leave blank to keep original:
Create a todo for this file? [y/N]:
Todo title:
Due date? optional:

Preview:
FROM -> TO

Apply? [y/N]:
```

If user confirms, move the file.

---

### `hb file list NAME`

List recorded files in a workspace.

Example:

```bash
hb file list math189
```

Output:

```text
Files in math189:

- homework/hw3.pdf
- lecture/lec10-notes.pdf
```

---

## Todo Commands

Use a Typer sub-app:

```bash
hb todo ...
```

---

### `hb todo add NAME [TEXT]`

Add a todo to a workspace.

Example:

```bash
hb todo add math189 "Finish HW3" --due 2026-06-10
```

Options:

```text
--due DATE
--attach PATH
```

`--attach` should be allowed multiple times.

Example:

```bash
hb todo add math189 "Submit HW3" \
  --attach homework/hw3/hw3.pdf \
  --attach homework/hw3/solution.ipynb \
  --attach homework/hw3/writeup.pdf
```

A todo's attachments should be stored as `resources`.

Each resource:

```json
{
  "type": "file",
  "path": "homework/hw3.pdf"
}
```

or:

```json
{
  "type": "folder",
  "path": "homework/hw3"
}
```

Resource type detection:

* If the path exists and is a directory, use `folder`.
* Otherwise use `file`.

Paths should be relative to the workspace folder.

---

### Interactive `hb todo add`

If user runs:

```bash
hb todo add math189
```

Prompt:

```text
Todo title:
Due date? optional:
Attach resources? [y/N]:
Resource path inside workspace:
Add another resource? [y/N]:
Create? [y/N]:
```

---

### `hb todo list NAME`

List todos in a workspace.

Output example:

```text
MATH189 Todos

[ ] 1. Finish HW3 (due 2026-06-10)
    resources:
    - folder: homework/hw3

[✓] 2. Review notes (no due date)
```

---

### `hb todo done NAME TODO_ID`

Mark todo as done.

Example:

```bash
hb todo done math189 1
```

Output:

```text
Done: Finish HW3
```

---

### `hb todo open NAME TODO_ID`

Open the resources attached to a todo.

Behavior:

* If no resources, print: `This todo has no resources.`
* If one resource, open it directly.
* If multiple resources, ask user which one to open.

Example prompt:

```text
This todo has multiple resources:

[1] folder: homework/hw3
[2] file: homework/hw3/hw3.pdf
[3] file: homework/hw3/solution.ipynb

Open which one?
```

Use the workspace folder as the base path.

---

## Check Command

### `hb check`

Show unfinished todos across all workspaces.

Example output:

```text
Todo Check

Workspace   ID   Todo               Due          Resources
math189     1    Finish HW3          2026-06-10   homework/hw3.pdf
dsc190      2    Submit final repo   2026-06-10   final-project/
career      1    Update resume       none         resume.pdf
```

Only show unfinished todos.

Sort:

1. Todos with due dates first.
2. Earlier due dates first.
3. Todos without due dates after that.

---

## Undo Command

### `hb undo`

Undo the latest file move.

Behavior:

* Read latest entry from `history.json`.
* Move `new_path` back to `old_path`.
* Remove the latest entry from history.
* Also remove the matching file record from the workspace's `files` list if possible.
* Do not overwrite anything.

Safety:

* If history is empty, print: `No history to undo.`
* If `new_path` does not exist, show an error.
* If `old_path` already exists, show an error.

Output example:

```text
Undo complete:
~/Documents/School/MATH189/homework/hw3.pdf
-> ~/Downloads/hw3.pdf
```

---

## Optional Link Commands

Use a Typer sub-app:

```bash
hb link ...
```

### `hb link add NAME TITLE URL`

Example:

```bash
hb link add math189 "Gradescope" "https://www.gradescope.com"
```

Add link to workspace.

### `hb link list NAME`

Output:

```text
Links for math189:

- Gradescope: https://www.gradescope.com
```

---

## Helper Functions

Implement these helpers.

### `expand_path`

```python
def expand_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()
```

### `open_path`

```python
def open_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", str(path)], check=False)
    elif sys.platform.startswith("win"):
        os.startfile(path)
    else:
        raise RuntimeError("Unsupported operating system")
```

### Relative path logic

When recording a moved file:

```python
relative_path = target_path.relative_to(workspace_folder)
```

When opening a resource:

```python
absolute_path = workspace_folder / resource["path"]
```

---

## Edge Cases to Handle

Please handle these cleanly:

1. Workspace already exists.
2. Workspace does not exist.
3. Source file does not exist.
4. Target file already exists.
5. User runs file command without `--apply`.
6. User cancels interactive prompt.
7. Todo ID does not exist.
8. Todo has no resources.
9. Todo has multiple resources.
10. Subfolder does not exist.
11. Undo history is empty.
12. Undo target no longer exists.
13. Undo original path already exists.

---

## README Requirements

Create a clear `README.md` with this format:

````markdown
# Homebase

Homebase is a Python command-line workspace manager that helps users organize files and todos by context. Users can create named workspaces for classes, projects, career goals, or life areas. Each workspace has a folder, files, todos, resources, and links, so users can move downloaded files into the right place and keep tasks connected to the materials needed to complete them.

## Usage

Create a workspace:

```bash
hb add math189 ~/Documents/School/MATH189
````

Open a workspace folder:

```bash
hb open math189
```

Move a downloaded file into a workspace:

```bash
hb file add math189 ~/Downloads/hw3.pdf --into homework --apply
```

Move a file and create a todo:

```bash
hb file add math189 ~/Downloads/hw3.pdf --into homework --todo "Finish HW3" --due 2026-06-10 --apply
```

Add a todo with an attached folder:

```bash
hb todo add math189 "Finish HW3" --attach homework/hw3
```

Check all unfinished todos:

```bash
hb check
```

Show a workspace:

```bash
hb show math189
```

## Installation

```bash
uv add "git+https://github.com/<your-username>/homebase-cli.git"
```

````

Also include how to run locally during development:

```bash
uv run hb --help
````

---

## Implementation Order

Please implement in small steps.

1. Create project structure.
2. Add `typer` app with `hb --help`.
3. Add JSON storage helpers.
4. Implement `hb add`, `hb list`, `hb show`.
5. Implement `hb open`.
6. Implement `hb file add` with dry-run and `--apply`.
7. Implement `hb file list`.
8. Implement history and `hb undo`.
9. Implement `hb todo add`, `hb todo list`, `hb todo done`.
10. Implement todo resources and `hb todo open`.
11. Implement `hb check`.
12. Add optional link commands.
13. Polish README.

Make sure the app works after each step.

---

## Manual Test Commands

After implementation, these should work:

```bash
uv run hb add math189 ~/Documents/School/MATH189
uv run hb list
uv run hb show math189
uv run hb open math189
uv run hb open math189 --sub homework
```

Create a temporary file:

```bash
mkdir -p ~/Downloads
echo "test" > ~/Downloads/hw3.pdf
```

Move it:

```bash
uv run hb file add math189 ~/Downloads/hw3.pdf --into homework
uv run hb file add math189 ~/Downloads/hw3.pdf --into homework --apply
uv run hb file list math189
```

Add todo:

```bash
uv run hb todo add math189 "Finish HW3" --due 2026-06-10 --attach homework/hw3.pdf
uv run hb todo list math189
uv run hb check
uv run hb todo open math189 1
```

Undo:

```bash
uv run hb undo
```

---

## Final Success Criteria

The MVP is successful if this flow works:

```bash
hb add math189 ~/Documents/School/MATH189
hb file add math189 ~/Downloads/hw3.pdf --into homework --todo "Finish HW3" --due 2026-06-10 --apply
hb check
hb todo open math189 1
hb show math189
```

This should support the intended workflow:

```text
Create workspace
-> move downloaded files into it
-> attach todos to files or folders
-> check tasks across workspaces
-> open the right folder or resource quickly
```

