import sys
import os
import argparse
from commit import get_parent_commit_id,get_branch_commit_id

def find_commot_ancestor(branch1,branch2):
    commit_id1 = get_branch_commit_id(branch1)
    commit_id2 = get_branch_commit_id(branch2)
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
        for c in curr:
            if c in all_commit_id_seen:
                return c


print(find_commot_ancestor("main","test"))

