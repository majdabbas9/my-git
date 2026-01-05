import time
from datetime import datetime
from git_object import GitObject
from tree import write_tree_from_directory
from help import (
    update_branch_reference,
    get_branch_commit_id,
    get_tree_from_commit,
    get_current_branch
)


def format_author(name, email, timestamp=None):
    """
    Format author information for a commit.
    
    Args:
        name: Author name
        email: Author email
        timestamp: Unix timestamp (default: current time)
        
    Returns:
        Formatted author string: "name <email> timestamp timezone"
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    dt = datetime.fromtimestamp(timestamp).astimezone()
    timezone_offset = dt.strftime("%z")  # e.g., +0200
    
    return f"{name} <{email}> {timestamp} {timezone_offset}"


def create_commit_object(tree_object_id, message, parent_commit_id=None, 
                        author_name="You", author_email="you@example.com"):
    """
    Create a commit object.
    
    Args:
        tree_object_id: SHA-1 hash of the tree object
        message: Commit message
        parent_commit_id: SHA-1 hash of parent commit (None for initial commit)
        author_name: Name of the author
        author_email: Email of the author
        
    Returns:
        SHA-1 hash of the commit object
    """
    lines = []
    
    # Add tree reference
    lines.append(f"tree {tree_object_id}")
    
    # Add parent reference if this is not the initial commit
    if parent_commit_id is not None:
        lines.append(f"parent {parent_commit_id}")
    
    # Add author and committer information
    author = format_author(author_name, author_email)
    lines.append(f"author {author}")
    lines.append(f"committer {author}")
    
    # Add blank line and message
    lines.append("")
    lines.append(message.rstrip("\n"))
    lines.append("")  # Ensure trailing newline
    
    # Create commit object
    commit_data = "\n".join(lines).encode("utf-8")
    
    return GitObject.write_object("commit", commit_data)


def commit_changes(message, ignore_patterns, author_name="You", author_email="you@example.com"):
    """
    Create a new commit with current changes.
    
    Args:
        message: Commit message
        ignore_patterns: List of file/directory patterns to ignore
        author_name: Name of the author
        author_email: Email of the author
        
    Returns:
        Success or error message string
    """
    current_branch = get_current_branch()
    
    # Handle case where current_branch might be None
    if current_branch is None:
        return "Error: No branch found. Please run 'init' first or checkout a branch."
    
    parent_commit_id = get_branch_commit_id(current_branch)
    
    # Get current tree ID from HEAD commit if it exists
    current_tree_id = None
    if parent_commit_id:
        current_tree_id = get_tree_from_commit(current_branch)
    
    # Create tree from current working directory
    tree_object_id = write_tree_from_directory("", ignore_patterns)
    
    # Check if there are any changes
    if tree_object_id == current_tree_id:
        return "nothing to commit"
    
    # Create the commit
    commit_id = create_commit_object(
        tree_object_id, 
        message, 
        parent_commit_id, 
        author_name, 
        author_email
    )
    
    # Update branch reference to point to new commit
    update_branch_reference(commit_id, current_branch)
    
    return "Commit created."


# Legacy function names for backward compatibility
def write_commit(tree_object_id, message, parent_commit_id=None, 
                author_name="You", author_email="you@example.com"):
    """Legacy function - use create_commit_object() instead."""
    return create_commit_object(tree_object_id, message, parent_commit_id, 
                               author_name, author_email)


def my_get_commit(message, ignore_patterns, author_name="You", author_email="you@example.com"):
    """Legacy function - use commit_changes() instead."""
    return commit_changes(message, ignore_patterns, author_name, author_email)
