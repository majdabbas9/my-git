# Removed circular import
import sys
import os
import zlib
import hashlib
from help import find_repo_root,get_to_ignore,get_curr_branch,find_curr_branch_commit,change_ref,change_head
from blob import my_get_cat_file
from tree import parse_tree

repo_root = find_repo_root()
def my_git_branch(branch_name):
    path = os.path.join(repo_root,".mygit","refs","heads",branch_name)
    ref_commit_id_of_head = os.path.join(repo_root,".mygit","HEAD")
    with open(ref_commit_id_of_head,"r") as r:
        ref = r.read()
    commit_id_ref = os.path.join(repo_root,".mygit",ref.split(" ")[1].split("\n")[0])
    with open(commit_id_ref, "r") as f:
        commit_hash = f.read().strip()
        
    if os.path.exists(path):
        return f"fatal: A branch named '{branch_name}' already exists."
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(commit_hash + "\n")
        return f"Created branch '{branch_name}'"

def delete_workdir_from_tree(tree_sha, current_dir, to_ignore):
    entries = parse_tree(tree_sha)
    for mode, name, sha in entries:
        if name in to_ignore:
            continue
            
        path = os.path.join(current_dir, name)
        if mode == "100644":
            if os.path.exists(path):
                os.remove(path)
        elif mode == "40000":
            if os.path.exists(path):
                delete_workdir_from_tree(sha, path, to_ignore)
                try:
                    os.rmdir(path)
                except OSError:
                    pass # Directory might not be empty due to ignored files

def update_workdir_from_tree(tree_sha, current_dir, to_ignore):
    entries = parse_tree(tree_sha)
    for mode, name, sha in entries:
        if name in to_ignore:
            continue
            
        path = os.path.join(current_dir, name)
        if mode == "100644":
            content = my_get_cat_file(sha)
            with open(path, "wb") as f:
                f.write(content)
        elif mode == "40000":
            os.makedirs(path, exist_ok=True)
            update_workdir_from_tree(sha, path, to_ignore)

def change_the_content_of_current_dict(commit_id, to_ignore=None):
    if to_ignore is None:
        to_ignore = get_to_ignore() 
    # 1. Delete contents of the previous commit tree
    curr_branch = get_curr_branch()
    prev_commit_id = find_curr_branch_commit(curr_branch)
    if prev_commit_id:
        try:
            prev_commit_content = my_get_cat_file(prev_commit_id).decode("utf-8")
            prev_tree_sha = None
            for line in prev_commit_content.split("\n"):
                if line.startswith("tree "):
                    prev_tree_sha = line.split(" ")[1]
                    break
            if prev_tree_sha:
                delete_workdir_from_tree(prev_tree_sha, repo_root, to_ignore)
        except Exception:
            pass # Old commit might not exist or be invalid

    # 2. Extract new tree SHA from commit content
    commit_content = my_get_cat_file(commit_id).decode("utf-8")
    lines = commit_content.split("\n")
    tree_sha = None
    for line in lines:
        if line.startswith("tree "):
            tree_sha = line.split(" ")[1]
            break
            
    if tree_sha:
        update_workdir_from_tree(tree_sha, repo_root, to_ignore)
    else:
        raise ValueError(f"Could not find tree in commit {commit_id}")

def my_git_check_out(commit_id_or_branch_name,create_branch = False):
    if len(commit_id_or_branch_name) == 40 and os.path.exists(os.path.join(repo_root,".mygit","objects",commit_id_or_branch_name[:2],commit_id_or_branch_name[2:])):
        change_the_content_of_current_dict(commit_id_or_branch_name)
        change_ref(commit_id_or_branch_name)
    else :
        ref_path = os.path.join(repo_root,".mygit","refs","heads",commit_id_or_branch_name) 
        branch_exists = os.path.exists(ref_path)
        if create_branch and not branch_exists:
            print(my_git_branch(commit_id_or_branch_name)) 
        if branch_exists or create_branch:
            change_head(f"ref: refs/heads/{commit_id_or_branch_name}\n")
            return f"switched to branch {commit_id_or_branch_name}" if create_branch 
        else:
            return "this branch dont exist"
