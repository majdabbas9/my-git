import os
from blob import my_get_cat_file
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

def find_parent_commit(curr_branch = "main"):
    repo_path = find_repo_root()
    full_path_to_head = os.path.join(repo_path,".mygit","refs","heads",curr_branch)
    if not os.path.exists(full_path_to_head):
        return None
    with open(full_path_to_head,"r") as f:
        data = f.read().strip()
        return data if data else None

def extract_tree_oid_from_commit_head(curr_branch = "main"):
    parent_oid = find_parent_commit(curr_branch)
    data = my_get_cat_file(parent_oid)
    np = data.find(b" ")
    return data[np+1:np+41].decode("ascii")

