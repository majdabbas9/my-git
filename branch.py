import os
from help import (
    find_repo_root,
    get_ignore_patterns,
    get_current_branch,
    get_branch_commit_id,
    update_branch_reference,
    update_head_reference
)
from blob import read_git_object
from tree import parse_tree_object


def create_branch(branch_name):
    """
    Create a new branch pointing to the current commit.
    
    Args:
        branch_name: Name of the new branch
        
    Returns:
        Success or error message string
    """
    repo_root = find_repo_root()
    branch_path = os.path.join(repo_root, ".mygit", "refs", "heads", branch_name)
    
    # Get current commit hash from HEAD
    head_ref_path = os.path.join(repo_root, ".mygit", "HEAD")
    with open(head_ref_path, "r") as f:
        head_ref = f.read()
    
    # Extract the actual branch reference path
    commit_ref_path = os.path.join(repo_root, ".mygit", head_ref.split(" ")[1].split("\n")[0])
    
    with open(commit_ref_path, "r") as f:
        commit_hash = f.read().strip()
    
    # Check if branch already exists
    if os.path.exists(branch_path):
        return f"fatal: A branch named '{branch_name}' already exists."
    
    # Create the new branch
    os.makedirs(os.path.dirname(branch_path), exist_ok=True)
    with open(branch_path, "w") as f:
        f.write(commit_hash + "\n")
    
    return f"Created branch '{branch_name}'"


def delete_working_directory_files(tree_id, current_directory, ignore_patterns):
    """
    Recursively delete files from working directory based on a tree object.
    
    Args:
        tree_id: SHA-1 hash of the tree object
        current_directory: Current directory path
        ignore_patterns: List of patterns to ignore
    """
    entries = parse_tree_object(tree_id)
    
    for mode, name, object_hash in entries:
        if name in ignore_patterns:
            continue
        
        file_path = os.path.join(current_directory, name)
        
        if mode == "100644":
            # Regular file
            if os.path.exists(file_path):
                os.remove(file_path)
        elif mode == "40000":
            # Directory
            if os.path.exists(file_path):
                delete_working_directory_files(object_hash, file_path, ignore_patterns)
                try:
                    os.rmdir(file_path)
                except OSError:
                    # Directory might not be empty due to ignored files
                    pass


def restore_working_directory_files(tree_id, current_directory, ignore_patterns):
    """
    Recursively restore files to working directory from a tree object.
    
    Args:
        tree_id: SHA-1 hash of the tree object
        current_directory: Current directory path
        ignore_patterns: List of patterns to ignore
    """
    entries = parse_tree_object(tree_id)
    
    for mode, name, object_hash in entries:
        if name in ignore_patterns:
            continue
        
        file_path = os.path.join(current_directory, name)
        
        if mode == "100644":
            # Regular file - restore content
            file_content = read_git_object(object_hash)
            with open(file_path, "wb") as f:
                f.write(file_content)
        elif mode == "40000":
            # Directory - create and recurse
            os.makedirs(file_path, exist_ok=True)
            restore_working_directory_files(object_hash, file_path, ignore_patterns)


def switch_to_commit(commit_id, ignore_patterns=None):
    """
    Switch the working directory to match a specific commit.
    
    Args:
        commit_id: SHA-1 hash of the commit to switch to
        ignore_patterns: List of patterns to ignore (default: from ignore.txt)
    """
    repo_root = find_repo_root()
    
    if ignore_patterns is None:
        ignore_patterns = get_ignore_patterns()
    
    # Delete contents of the previous commit tree
    current_branch = get_current_branch()
    previous_commit_id = get_branch_commit_id(current_branch)
    
    if previous_commit_id:
        try:
            previous_commit_content = read_git_object(previous_commit_id).decode("utf-8")
            previous_tree_id = None
            
            for line in previous_commit_content.split("\n"):
                if line.startswith("tree "):
                    previous_tree_id = line.split(" ")[1]
                    break
            
            if previous_tree_id:
                delete_working_directory_files(previous_tree_id, repo_root, ignore_patterns)
        except Exception:
            # Previous commit might not exist or be invalid
            pass
    
    # Extract tree from new commit and restore files
    commit_content = read_git_object(commit_id).decode("utf-8")
    tree_id = None
    
    for line in commit_content.split("\n"):
        if line.startswith("tree "):
            tree_id = line.split(" ")[1]
            break
    
    if tree_id:
        restore_working_directory_files(tree_id, repo_root, ignore_patterns)
    else:
        raise ValueError(f"Could not find tree in commit {commit_id}")


def checkout(target_ref, create_branch=False):
    """
    Switch to a branch or commit.
    
    Args:
        target_ref: Branch name or commit hash to checkout
        create_branch: If True, create the branch if it doesn't exist
        
    Returns:
        Success or error message string, or None if successful
    """
    repo_root = find_repo_root()
    
    # Check if target_ref is a commit hash (40-character hex string)
    is_commit_hash = (
        len(target_ref) == 40 and
        os.path.exists(os.path.join(repo_root, ".mygit", "objects", target_ref[:2], target_ref[2:]))
    )
    
    if is_commit_hash:
        # Checkout a specific commit (detached HEAD)
        switch_to_commit(target_ref)
        update_branch_reference(target_ref)
    else:
        # Checkout a branch
        branch_ref_path = os.path.join(repo_root, ".mygit", "refs", "heads", target_ref)
        branch_exists = os.path.exists(branch_ref_path)
        
        if create_branch and not branch_exists:
            print(create_branch(target_ref))
        
        if branch_exists or create_branch:
            update_head_reference(f"ref: refs/heads/{target_ref}\n")
            return f"switched to branch {target_ref}" if create_branch else None
        else:
            return "this branch dont exist"


# Legacy function names for backward compatibility
def my_git_branch(branch_name):
    """Legacy function - use create_branch() instead."""
    return create_branch(branch_name)


def delete_workdir_from_tree(tree_id, current_directory, ignore_patterns):
    """Legacy function - use delete_working_directory_files() instead."""
    return delete_working_directory_files(tree_id, current_directory, ignore_patterns)


def update_workdir_from_tree(tree_id, current_directory, ignore_patterns):
    """Legacy function - use restore_working_directory_files() instead."""
    return restore_working_directory_files(tree_id, current_directory, ignore_patterns)


def change_the_content_of_current_dict(commit_id, ignore_patterns=None):
    """Legacy function - use switch_to_commit() instead."""
    return switch_to_commit(commit_id, ignore_patterns)


def my_git_check_out(target_ref, create_branch=False):
    """Legacy function - use checkout() instead."""
    return checkout(target_ref, create_branch)
