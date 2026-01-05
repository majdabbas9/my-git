import os
from git_object import GitObject
from blob import hash_file_to_blob, read_git_object
from help import find_repo_root


def create_tree_object(directory_path, ignore_patterns):
    """
    Create a tree object from a directory.
    
    Args:
        directory_path: Path to the directory
        ignore_patterns: List of file/directory names to ignore
        
    Returns:
        SHA-1 hash of the tree object
    """
    with os.scandir(directory_path) as entries:
        tree_entries = []
        
        for child in entries:
            if child.name in ignore_patterns:
                continue
            
            if child.is_file():
                mode = b"100644"
                object_id = hash_file_to_blob(child)
            elif child.is_dir():
                mode = b"40000"
                object_id = create_tree_object(
                    os.path.join(directory_path, child), 
                    ignore_patterns
                )
            
            # Format: mode + space + name + null byte + hash bytes
            entry_data = mode + b" " + child.name.encode("utf-8") + b"\x00" + bytes.fromhex(object_id)
            tree_entries.append([child.name, entry_data])
        
        # Sort entries by name
        tree_entries.sort(key=lambda entry: entry[0])
        
        # Concatenate all entry data
        tree_data = b"".join(entry[1] for entry in tree_entries)
        
        return GitObject.write_object("tree", tree_data)


def parse_tree_object(tree_hash):
    """
    Parse a tree object and return its entries.
    
    Args:
        tree_hash: SHA-1 hash of the tree object
        
    Returns:
        List of [mode, name, hash] for each entry
    """
    entries = []
    tree_data = read_git_object(tree_hash)
    
    index = 0
    while index < len(tree_data):
        # Find space after mode
        space_index = tree_data.find(b" ", index)
        # Find null byte after name
        null_index = tree_data.find(b"\x00", space_index + 1)
        
        mode = tree_data[index:space_index].decode("ascii")
        name = tree_data[space_index + 1:null_index].decode("ascii")
        object_hash = tree_data[null_index + 1:null_index + 21].hex()
        
        entries.append([mode, name, object_hash])
        index = null_index + 21
    
    return entries


def write_tree_from_directory(path="", ignore_patterns=None):
    """
    Create a tree object from a directory in the repository.
    
    Args:
        path: Relative path from repository root (default: "")
        ignore_patterns: List of patterns to ignore (default: None)
        
    Returns:
        SHA-1 hash of the tree object
    """
    directory_path = os.path.join(find_repo_root(path), path)
    return create_tree_object(directory_path, ignore_patterns)


def list_tree_contents(path="", ignore_patterns=None, names_only=False, object_id=None):
    """
    List the contents of a tree object.
    
    Args:
        path: Relative path from repository root (default: "")
        ignore_patterns: List of patterns to ignore (default: None)
        names_only: If True, only return names, not full info (default: False)
        object_id: Specific tree hash to list (default: None, will compute from path)
        
    Returns:
        String with tree contents, one entry per line
    """
    if object_id:
        tree_hash = object_id
    else:
        directory_path = os.path.join(find_repo_root(path), path)
        tree_hash = create_tree_object(directory_path, ignore_patterns)
    
    entries = parse_tree_object(tree_hash)
    
    result = []
    for entry in entries:
        if names_only:
            result.append(entry[1])  # Just the name
        else:
            result.append(" ".join(entry))  # mode name hash
    
    return "\n".join(result)


# Legacy function names for backward compatibility
def write_tree(directory_path, ignore_patterns):
    """Legacy function - use create_tree_object() instead."""
    return create_tree_object(directory_path, ignore_patterns)


def parse_tree(tree_hash):
    """Legacy function - use parse_tree_object() instead."""
    return parse_tree_object(tree_hash)


def my_get_write_tree(path="", ignore_patterns=None):
    """Legacy function - use write_tree_from_directory() instead."""
    return write_tree_from_directory(path, ignore_patterns)


def my_get_ls_tree(path="", ignore_patterns=None, names_only=False, object_id=None):
    """Legacy function - use list_tree_contents() instead."""
    return list_tree_contents(path, ignore_patterns, names_only, object_id)
