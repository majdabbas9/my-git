import os

def find_repo_root(path="."):
    """
    Given a path, traverse up until a .mygit directory is found.
    Returns the absolute path to the root of the repo.
    Raises FileNotFoundError if not found.
    """
    path = os.path.abspath(path)
    current = path \
        if os.path.isdir(path) \
        else os.path.dirname(path)

    while True:
        if os.path.isdir(os.path.join(current, ".mygit")):
            return current
        
        parent = os.path.dirname(current)
        if parent == current:
            # We reached the filesystem root and didn't find it
            raise FileNotFoundError("Could not find .mygit directory")
        current = parent

def change_head(commit_oid,curr_branch = "main"):
    repo_path = find_repo_root()
    full_path_to_head = os.path.join(repo_path,".mygit","refs","heads",curr_branch)
    with open(full_path_to_head,"w") as f:
        f.write(commit_oid)

change_head("123")