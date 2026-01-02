# MyGit

A lightweight, clean implementation of Git written in Python.

## Features

- **Init**: Initialize a new repository (`.mygit`).
- **Objets**: Hash files and create blobs.
- **Cat-File**: Read object contents (blobs, trees).
- **Write-Tree**: Create tree objects from the directory state.
- **Ls-Tree**: List contents of tree objects.
- **Commit**: Create commit objects (inprogress).

## Usage

```bash
# Initialize
python3 main.py init

# Add a file object
python3 main.py hash-object <filename>

# Write current directory as a tree
python3 main.py write-tree

# Inspect an object
python3 main.py cat-file <sha1>
```

## Structure

- `main.py`: Entry point and CLI command handler.
- `blob.py`: Blob object handling.
- `tree.py`: Tree object handling.
- `commit.py`: Commit object implementation.
- `help.py`: Helper functions.
