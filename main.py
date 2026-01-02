#!/usr/bin/env python3
import sys
import os
import argparse
from blob import my_get_hash_object, my_get_cat_file
from tree import my_get_write_tree, my_get_ls_tree
from help import find_repo_root

def cmd_init(args):
    os.makedirs(".mygit/objects", exist_ok=True)
    os.makedirs(".mygit/refs/heads", exist_ok=True)
    with open(".mygit/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized mygit directory")

def cmd_hash_object(args):
    print(my_get_hash_object(args.file))

def cmd_cat_file(args):
    # Depending on how my_get_cat_file returns data (bytes or str), handle printing
    content = my_get_cat_file(args.object)
    if isinstance(content, bytes):
        sys.stdout.buffer.write(content)
    else:
        print(content)

def cmd_write_tree(args):
    to_ignore = []
    if os.path.exists("ignore.txt"):
        with open("ignore.txt", "r") as f:
            to_ignore = f.read().splitlines()
    
    path = args.path if args.path else ""
    print(my_get_write_tree(path, to_ignore))

def cmd_ls_tree(args):
    to_ignore = []
    if os.path.exists("ignore.txt"):
        with open("ignore.txt", "r") as f:
            to_ignore = f.read().splitlines()

    path = args.path if args.path else ""
    try:
        full_path = os.path.join(find_repo_root(path), path)
        if not os.path.exists(full_path):
             print(f"fatal: Not a valid object name {path}")
             return
    except FileNotFoundError:
        # If find_repo_root fails (no .mygit), maybe handle or just let it crash/print error
        pass
        
    print(my_get_ls_tree(path, to_ignore, args.name_only))

def main():
    parser = argparse.ArgumentParser(description="MyGit - A simple git implementation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    sp_init = subparsers.add_parser("init", help="Initialize a new git repository")
    sp_init.set_defaults(func=cmd_init)

    # hash-object
    sp_hash = subparsers.add_parser("hash-object", help="Compute object ID and optionally create a blob from a file")
    sp_hash.add_argument("file", help="File to hash")
    sp_hash.set_defaults(func=cmd_hash_object)

    # cat-file
    sp_cat = subparsers.add_parser("cat-file", help="Provide content or type and size information for repository objects")
    sp_cat.add_argument("object", help="The object to display")
    # You might want to add flags like -p, -t, -s later
    sp_cat.add_argument("-p", action="store_true", help="Pretty-print object content") 
    sp_cat.set_defaults(func=cmd_cat_file)

    # write-tree
    sp_write_tree = subparsers.add_parser("write-tree", help="Create a tree object from the current index")
    sp_write_tree.add_argument("path", nargs="?", default="", help="Path to write tree from")
    sp_write_tree.set_defaults(func=cmd_write_tree)

    # ls-tree
    sp_ls_tree = subparsers.add_parser("ls-tree", help="List the contents of a tree object")
    sp_ls_tree.add_argument("--name-only", action="store_true", help="List only filenames")
    sp_ls_tree.add_argument("path", nargs="?", default="", help="Tree object to list")
    sp_ls_tree.set_defaults(func=cmd_ls_tree)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()