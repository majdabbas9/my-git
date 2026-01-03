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

def get_to_ignore():
    to_ignore = []
    path = os.path.join(find_repo_root(),"ignore.txt")
    if os.path.exists(path):
        with open(path, "r") as f:
            to_ignore = f.read().splitlines()
    return to_ignore


def change_ref(commit_oid,curr_branch = "main"):
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

def get_all_commits(start_node=None):
    repo_root = find_repo_root()
    if start_node is None:
        head_path = os.path.join(repo_root, ".mygit", "HEAD")
        if not os.path.exists(head_path):
            return []
        with open(head_path, "r") as f:
            content = f.read().strip()
        if content.startswith("ref: "):
            ref_path = os.path.join(repo_root, ".mygit", content[5:])
            if not os.path.exists(ref_path):
                return []
            with open(ref_path, "r") as f:
                current_sha = f.read().strip()
        else:
            current_sha = content
    else:
        branch_path = os.path.join(repo_root, ".mygit", "refs", "heads", start_node)
        if os.path.exists(branch_path):
            with open(branch_path, "r") as f:
                current_sha = f.read().strip()
        else:
            current_sha = start_node

    commits = []
    queue = [current_sha]
    visited = set()

    while queue:
        sha = queue.pop(0)
        if not sha or sha in visited:
            continue
        visited.add(sha)
        
        try:
            raw_content = my_get_cat_file(sha)
            content = raw_content.decode("utf-8")
            commits.append(sha)
            
            for line in content.split("\n"):
                if line.startswith("parent "):
                    parts = line.split(" ")
                    if len(parts) > 1:
                        queue.append(parts[1])
        except Exception:
            # Skip if object not found or not a commit
            continue
            
    return commits

def get_curr_branch():
    repo_path = find_repo_root()
    path = os.path.join(repo_path, ".mygit", "HEAD")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        content = f.read().strip()
    if content.startswith("ref: "):
        # Git refs always use forward slashes internally
        return content.split("/")[-1]
    return None
