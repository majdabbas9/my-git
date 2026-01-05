import os
from git_object import GitObject


def hash_file_to_blob(file_path, write=True):
    """
    Hash a file and optionally store it as a blob object.
    
    Args:
        file_path: Path to the file to hash
        write: Whether to write the blob to .mygit/objects (default: True)
        
    Returns:
        SHA-1 hash of the blob object
    """
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    return GitObject.write_object("blob", file_content, write)


def read_git_object(object_hash):
    """
    Read a Git object by its hash.
    
    Args:
        object_hash: SHA-1 hash of the object
        
    Returns:
        Object content as bytes
    """
    try:
        return GitObject.read_object(object_hash)
    except FileNotFoundError:
        print(f"Error: Object {object_hash} not found")
        exit(1)


# Legacy function names for backward compatibility (to be removed after refactoring)
def write_object(object_type, data, write=True):
    """Legacy function - use GitObject.write_object() instead."""
    return GitObject.write_object(object_type, data, write)


def my_get_hash_object(file_path, write=True):
    """Legacy function - use hash_file_to_blob() instead."""
    return hash_file_to_blob(file_path, write)


def my_get_cat_file(object_hash):
    """Legacy function - use read_git_object() instead."""
    return read_git_object(object_hash)
