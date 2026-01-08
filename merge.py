import sys
import os
import argparse
from commit import get_parent_commit_id,get_branch_commit_id,update_branch_reference,write_commit_2_parents
from help import get_curr_branch
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

my_git_merge("main")