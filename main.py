#!/usr/bin/env python3
import sys
import os
import argparse
from blob import hash_file_to_blob, read_git_object
from tree import write_tree_from_directory, list_tree_contents
from commit import commit_changes
from help import find_repo_root, get_ignore_patterns, format_commit_log
from branch import create_branch, checkout


def cmd_init(args):
    """Initialize a new MyGit repository."""
    os.makedirs(".mygit/objects", exist_ok=True)
    os.makedirs(".mygit/refs/heads", exist_ok=True)
    with open(".mygit/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized mygit directory")


def cmd_hash_object(args):
    """Hash a file and create a blob object."""
    print(hash_file_to_blob(args.file))


def cmd_cat_file(args):
    """Display the content of a Git object."""
    content = read_git_object(args.object)
    if isinstance(content, bytes):
        sys.stdout.buffer.write(content)
    else:
        print(content)


def cmd_write_tree(args):
    """Create a tree object from the current directory."""
    ignore_patterns = get_ignore_patterns()
    path = args.path if args.path else ""
    print(write_tree_from_directory(path, ignore_patterns))


def cmd_ls_tree(args):
    """List the contents of a tree object."""
    ignore_patterns = []
    if os.path.exists("ignore.txt"):
        with open("ignore.txt", "r") as f:
            ignore_patterns = f.read().splitlines()
    
    path = args.path if args.path else ""
    try:
        full_path = os.path.join(find_repo_root(path), path)
        if not os.path.exists(full_path):
            print(f"fatal: Not a valid object name {path}")
            return
    except FileNotFoundError:
        # If find_repo_root fails, continue anyway
        pass
    
    print(list_tree_contents(path, ignore_patterns, args.name_only, args.oid))


def cmd_commit(args):
    """Create a new commit with the current changes."""
    ignore_patterns = []
    if os.path.exists("ignore.txt"):
        with open("ignore.txt", "r") as f:
            ignore_patterns = f.read().splitlines()
    
    print(commit_changes(
        args.message,
        ignore_patterns,
        author_name=args.author,
        author_email=args.email
    ))


def cmd_branch(args):
    """Create a new branch."""
    print(create_branch(args.name))


def cmd_checkout(args):
    """Switch branches or restore working tree files."""
    result = checkout(args.name, create_branch=args.b)
    if result:
        print(result)


def cmd_log(args):
    """Show commit history."""
    print(format_commit_log())


def main():
    """Main entry point for MyGit CLI."""
    parser = argparse.ArgumentParser(description="MyGit - A simple git implementation")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # init command
    sp_init = subparsers.add_parser("init", help="Initialize a new git repository")
    sp_init.set_defaults(func=cmd_init)
    
    # hash-object command
    sp_hash = subparsers.add_parser(
        "hash-object",
        help="Compute object ID and optionally create a blob from a file"
    )
    sp_hash.add_argument("file", help="File to hash")
    sp_hash.set_defaults(func=cmd_hash_object)
    
    # cat-file command
    sp_cat = subparsers.add_parser(
        "cat-file",
        help="Provide content or type and size information for repository objects"
    )
    sp_cat.add_argument("object", help="The object to display")
    sp_cat.add_argument("-p", action="store_true", help="Pretty-print object content")
    sp_cat.set_defaults(func=cmd_cat_file)
    
    # write-tree command
    sp_write_tree = subparsers.add_parser(
        "write-tree",
        help="Create a tree object from the current index"
    )
    sp_write_tree.add_argument("path", nargs="?", default="", help="Path to write tree from")
    sp_write_tree.set_defaults(func=cmd_write_tree)
    
    # ls-tree command
    sp_ls_tree = subparsers.add_parser("ls-tree", help="List the contents of a tree object")
    sp_ls_tree.add_argument("--name-only", action="store_true", help="List only filenames")
    sp_ls_tree.add_argument("--oid", help="The tree OID to list")
    sp_ls_tree.add_argument("path", nargs="?", default="", help="Tree object to list")
    sp_ls_tree.set_defaults(func=cmd_ls_tree)
    
    # commit command
    sp_commit = subparsers.add_parser("commit", help="Record changes to the repository")
    sp_commit.add_argument("-m", "--message", required=True, help="Commit message")
    sp_commit.add_argument("--author", default="You", help="Author name")
    sp_commit.add_argument("--email", default="you@example.com", help="Author email")
    sp_commit.set_defaults(func=cmd_commit)
    
    # branch command
    sp_branch = subparsers.add_parser("branch", help="List, create, or delete branches")
    sp_branch.add_argument("name", help="The name of the branch to create")
    sp_branch.set_defaults(func=cmd_branch)
    
    # checkout command
    sp_checkout = subparsers.add_parser(
        "checkout",
        help="Switch branches or restore working tree files"
    )
    sp_checkout.add_argument("name", help="The name of the branch or commit to checkout")
    sp_checkout.add_argument("-b", action="store_true", help="Create a new branch and switch to it")
    sp_checkout.set_defaults(func=cmd_checkout)
    
    # log command
    sp_log = subparsers.add_parser("log", help="Show commit history")
    sp_log.set_defaults(func=cmd_log)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()