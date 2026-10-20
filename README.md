# Picture-Sort
This minimal algorithm takes a md-file and a directory of files and copies the listed items from the md-file to a child-folder.

- select directories via arrow-keys
- autocompletes filenames
- creates subdirectory for every markdown- heading
- verifies integrity


## Use-case
Writing markdown instead of manually deleting files and let the Algorithm securely copy your most important files.

## Markdown-example
```md
1056/15/45/89
2556/68/72/73/74/98

# Subfolder 1
7645/46/52/57/67/68/78/86/91/
7742/58/62/65/
7810/16/22/29/34/45/49/

# Subfolder 2
9279/84/87/
9301/04/
```
The algorithm creates a list of all selected files and detects leading numbers.
Adjust paths and file-naming if necessary.

## Requirements
- uv

## Installation
install uv ontop of python not with python!

Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Run
```bash
uv run main.py
```
