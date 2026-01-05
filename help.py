import os
from blob import read_git_object


def find_repo_root(path="."):
    """
    Find the root directory of the repository.
    
    Traverses up from the given path until a .mygit directory is found.
    
    Args:
        path: Starting path (default: current directory)
        
    Returns:
        Absolute path to the repository root
        
    Raises:
        FileNotFoundError: If .mygit directory is not found
    """
    path = os.path.abspath(path)
    current = path if os.path.isdir(path) else os.path.dirname(path)
    
    while True:
        if os.path.isdir(os.path.join(current, ".mygit")):
            return current
        
        parent = os.path.dirname(current)
        if parent == current:
            # Reached filesystem root without finding .mygit
            raise FileNotFoundError("Could not find .mygit directory")
        current = parent


def get_ignore_patterns():
    """
    Get list of file/directory patterns to ignore from ignore.txt.
    
    Returns:
        List of pattern strings to ignore
    """
    ignore_patterns = []
    ignore_file_path = os.path.join(find_repo_root(), "ignore.txt")
    
    if os.path.exists(ignore_file_path):
        with open(ignore_file_path, "r") as f:
            ignore_patterns = f.read().splitlines()
    
    return ignore_patterns


def update_branch_reference(commit_id, branch_name="main"):
    """
    Update a branch reference to point to a specific commit.
    
    Args:
        commit_id: SHA-1 hash of the commit
        branch_name: Name of the branch (default: "main")
    """
    repo_path = find_repo_root()
    branch_ref_path = os.path.join(repo_path, ".mygit", "refs", "heads", branch_name)
    
    with open(branch_ref_path, "w") as f:
        f.write(commit_id)


def get_branch_commit_id(branch_name="main"):
    """
    Get the commit ID that a branch points to.
    
    Args:
        branch_name: Name of the branch (default: "main")
        
    Returns:
        SHA-1 hash of the commit, or None if branch doesn't exist or is empty
    """
    repo_path = find_repo_root()
    branch_ref_path = os.path.join(repo_path, ".mygit", "refs", "heads", branch_name)
    
    if not os.path.exists(branch_ref_path):
        return None
    
    with open(branch_ref_path, "r") as f:
        commit_data = f.read().strip()
        return commit_data if commit_data else None


def get_tree_from_commit(branch_name="main"):
    """
    Extract the tree object ID from a commit.
    
    Args:
        branch_name: Name of the branch (default: "main")
        
    Returns:
        SHA-1 hash of the tree object
    """
    parent_commit_id = get_branch_commit_id(branch_name)
    commit_data = read_git_object(parent_commit_id)
    
    # Find the tree line: "tree <hash>"
    space_index = commit_data.find(b" ")
    tree_id = commit_data[space_index + 1:space_index + 41].decode("ascii")
    
    return tree_id


def get_all_commits(start_node=None):
    """
    Get all commits reachable from a starting point.
    
    Args:
        start_node: Branch name or commit hash to start from (default: current HEAD)
        
    Returns:
        List of commit hashes in traversal order
    """
    repo_root = find_repo_root()
    
    if start_node is None:
        # Start from current HEAD
        head_path = os.path.join(repo_root, ".mygit", "HEAD")
        if not os.path.exists(head_path):
            return []
        
        with open(head_path, "r") as f:
            head_content = f.read().strip()
        
        if head_content.startswith("ref: "):
            # HEAD points to a branch
            ref_path = os.path.join(repo_root, ".mygit", head_content[5:])
            if not os.path.exists(ref_path):
                return []
            with open(ref_path, "r") as f:
                current_commit_hash = f.read().strip()
        else:
            # HEAD points directly to a commit (detached HEAD)
            current_commit_hash = head_content
    else:
        # Check if start_node is a branch name
        branch_path = os.path.join(repo_root, ".mygit", "refs", "heads", start_node)
        if os.path.exists(branch_path):
            with open(branch_path, "r") as f:
                current_commit_hash = f.read().strip()
        else:
            # Assume it's a commit hash
            current_commit_hash = start_node
    
    commits = []
    queue = [current_commit_hash]
    visited = set()
    
    while queue:
        commit_hash = queue.pop(0)
        if not commit_hash or commit_hash in visited:
            continue
        visited.add(commit_hash)
        
        try:
            raw_content = read_git_object(commit_hash)
            content = raw_content.decode("utf-8")
            commits.append(commit_hash)
            
            # Find parent commits
            for line in content.split("\n"):
                if line.startswith("parent "):
                    parts = line.split(" ")
                    if len(parts) > 1:
                        queue.append(parts[1])
        except Exception:
            # Skip if object not found or not a commit
            continue
    
    return commits


def get_current_branch():
    """
    Get the name of the current branch.
    
    Returns:
        Branch name, or None if in detached HEAD state or no branch exists
    """
    repo_path = find_repo_root()
    head_path = os.path.join(repo_path, ".mygit", "HEAD")
    
    if not os.path.exists(head_path):
        return None
    
    with open(head_path, "r") as f:
        head_content = f.read().strip()
    
    if head_content.startswith("ref: "):
        # Extract branch name from ref path (e.g., refs/heads/main -> main)
        return head_content.split("/")[-1]
    
    return None


def update_head_reference(new_ref):
    """
    Update the HEAD reference.
    
    Args:
        new_ref: New reference (e.g., "ref: refs/heads/main" or a commit hash)
    """
    repo_path = find_repo_root()
    head_path = os.path.join(repo_path, ".mygit", "HEAD")
    
    with open(head_path, "w") as f:
        f.write(new_ref + "\n")


# Legacy function names for backward compatibility
def get_to_ignore():
    """Legacy function - use get_ignore_patterns() instead."""
    return get_ignore_patterns()


def change_ref(commit_id, branch_name="main"):
    """Legacy function - use update_branch_reference() instead."""
    return update_branch_reference(commit_id, branch_name)


def find_curr_branch_commit(branch_name="main"):
    """Legacy function - use get_branch_commit_id() instead."""
    return get_branch_commit_id(branch_name)


def extract_tree_oid_from_commit_head(branch_name="main"):
    """Legacy function - use get_tree_from_commit() instead."""
    return get_tree_from_commit(branch_name)


def get_curr_branch():
    """Legacy function - use get_current_branch() instead."""
    return get_current_branch()


def change_head(new_ref):
    """Legacy function - use update_head_reference() instead."""
    return update_head_reference(new_ref)


def format_commit_log(start_node=None):
    """
    Format commit history as a readable log.
    
    Args:
        start_node: Branch name or commit hash to start from (default: current HEAD)
        
    Returns:
        Formatted string with commit history
    """
    from datetime import datetime
    
    commits = get_all_commits(start_node)
    
    if not commits:
        return "No commits found."
    
    log_lines = []
    
    for commit_hash in commits:
        try:
            raw_content = read_git_object(commit_hash)
            content = raw_content.decode("utf-8")
            
            # Parse commit data
            lines = content.split("\n")
            tree_id = None
            parent_id = None
            author_line = None
            message_lines = []
            in_message = False
            
            for line in lines:
                if line.startswith("tree "):
                    tree_id = line.split(" ", 1)[1]
                elif line.startswith("parent "):
                    parent_id = line.split(" ", 1)[1]
                elif line.startswith("author "):
                    author_line = line[7:]  # Remove "author " prefix
                elif line == "" and not in_message:
                    in_message = True
                elif in_message:
                    message_lines.append(line)
            
            # Format output
            log_lines.append(f"commit {commit_hash}")
            
            if author_line:
                # Parse author line: "Name <email> timestamp timezone"
                parts = author_line.rsplit(" ", 2)
                if len(parts) == 3:
                    author_info = parts[0]
                    timestamp = int(parts[1])
                    timezone = parts[2]
                    
                    # Convert timestamp to readable date
                    dt = datetime.fromtimestamp(timestamp)
                    date_str = dt.strftime("%a %b %d %H:%M:%S %Y") + f" {timezone}"
                    
                    log_lines.append(f"Author: {author_info}")
                    log_lines.append(f"Date:   {date_str}")
            
            log_lines.append("")
            
            # Add commit message (indented)
            for msg_line in message_lines:
                if msg_line.strip():  # Skip empty lines at the end
                    log_lines.append(f"    {msg_line}")
            
            log_lines.append("")
            
        except Exception:
            continue
    
    return "\n".join(log_lines)
