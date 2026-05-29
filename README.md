# Homebase

Homebase is a Python command-line workspace manager that helps users organize files and todos by context. Users can create named workspaces for classes, projects, career goals, or life areas. Each workspace has a folder, files, todos, resources, and links, so users can move downloaded files into the right place and keep tasks connected to the materials needed to complete them.

## Usage

Create a workspace:

```bash
hb add math189 ~/Documents/School/MATH189
```

List and inspect workspaces:

```bash
hb list
hb show math189
```

Open a workspace folder:

```bash
hb open math189
hb open math189 --sub homework
```

Preview a file move:

```bash
hb file add math189 ~/Downloads/hw3.pdf --into homework
```

Move a downloaded file into a workspace:

```bash
hb file add math189 ~/Downloads/hw3.pdf --into homework --apply
```

Move a file and create a todo:

```bash
hb file add math189 ~/Downloads/hw3.pdf --into homework --todo "Finish HW3" --due 2026-06-10 --apply
```

Add a todo with attached resources:

```bash
hb todo add math189 "Submit HW3" --attach homework/hw3.pdf --attach homework
```

List and complete todos:

```bash
hb todo list math189
hb todo done math189 1
```

Open a todo resource:

```bash
hb todo open math189 1
```

Check all unfinished todos:

```bash
hb check
```

Undo the latest file move:

```bash
hb undo
```

## Installation

```bash
uv add "git+https://github.com/<your-username>/homebase-cli.git"
```

Run locally during development:

```bash
uv run hb --help
```
