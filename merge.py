import sys
import os
import argparse
from commit import (
    get_parent_commit_id,
    get_branch_commit_id,
    update_branch_reference,
    write_commit_2_parents,
    get_commit_info,
    create_commit_object
)
from help import get_curr_branch,find_repo_root

def find_commot_ancestor(commit_id1,commit_id2):
    all_commit_id_seen = set()
    if commit_id1 == commit_id2:
        return commit_id1
    queue = [commit_id1]
    all_commit_id_seen.add(commit_id1)
    while queue:
        curr = get_parent_commit_id(queue.pop(0))
        if curr:
            queue.extend(curr)
            for c in curr:
                all_commit_id_seen.add(c)
    queue = [commit_id2]
    while queue:
        curr = get_parent_commit_id(queue.pop(0))
        if commit_id1 in curr:
            return commit_id1
        for c in curr:
            if c in all_commit_id_seen:
                return c
        queue.extend(curr)

def my_git_merge(branch):
    curr_branch = get_curr_branch()
    if curr_branch == branch:
        return "cant merge the same branch"
    commit_id_1 = get_branch_commit_id(curr_branch)
    commit_id_2 = get_branch_commit_id(branch)
    common_commit_id = find_commot_ancestor(commit_id_1,commit_id_2)
    if commit_id_1 == common_commit_id:
        update_branch_reference(commit_id_2)
        return "merged"
    if commit_id_2 == common_commit_id:
        return "cant merge to an old version"
    return write_commit_2_parents(merge_branch1=curr_branch,merge_branch2=branch,parent_commit_id1=commit_id_1,parent_commit_id2=commit_id_2)

def my_git_rebase(branch):
    curr_branch = get_curr_branch()
    if curr_branch is None:
        return "No active branch"
    if curr_branch == branch:
        return "Cannot rebase branch onto itself"
        
    current_commit_id = get_branch_commit_id(curr_branch)
    target_commit_id = get_branch_commit_id(branch)
    
    if not current_commit_id or not target_commit_id:
        return "One or both branches have no commits"
        
    common_ancestor = find_commot_ancestor(current_commit_id, target_commit_id)
    
    if common_ancestor == current_commit_id:
        # Fast-forward: current is ancestor of target.
        update_branch_reference(target_commit_id, curr_branch)
        return f"Fast-forwarded {curr_branch} to {branch}"
        
    # Collect commits to rebase
    commits_to_rebase = []
    pointer = current_commit_id
    while pointer != common_ancestor and pointer is not None:
        commits_to_rebase.append(pointer)
        parents = get_parent_commit_id(pointer)
        if parents:
            pointer = parents[0]
        else:
            break
            
    commits_to_rebase.reverse()
    
    # Replay commits
    new_parent = target_commit_id
    
    for commit_id in commits_to_rebase:
        info = get_commit_info(commit_id)
        if info:
            new_commit_id = create_commit_object(
                info['tree_id'],
                info['message'],
                [new_parent],
                info['author_name'],
                info['author_email']
            )
            new_parent = new_commit_id
            path = os.path.join(find_repo_root(),".mygit","objects")
            os.remove(os.path.join(path,commit_id[:2],commit_id[2:]))
    # Update branch ref
    update_branch_reference(new_parent, curr_branch)
    return f"Successfully rebased {curr_branch} onto {branch}"
