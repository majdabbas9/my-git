import sys
import os
import zlib
import hashlib
import time
from datetime import datetime, timezone
from blob import write_object
from tree import my_get_write_tree
from help import change_ref,find_parent_commit,extract_tree_oid_from_commit_head,get_curr_branch
def format_author(name: str, email: str, timestamp: int | None = None) -> str:
    if timestamp is None:
        timestamp = int(time.time())

    dt = datetime.fromtimestamp(timestamp).astimezone()
    offset = dt.strftime("%z")  # e.g. +0200

    return f"{name} <{email}> {timestamp} {offset}"


def write_commit(tree_oid,message,parent_oid = None,author_name = "You",author_email = "you@example.com"):
    """
    Create a commit object.
    Returns commit oid.
    """
    lines = []

    lines.append(f"tree {tree_oid}")

    if parent_oid is not None:
        lines.append(f"parent {parent_oid}")

    author = format_author(author_name, author_email)
    lines.append(f"author {author}")
    lines.append(f"committer {author}")

    # blank line between headers and message
    lines.append("")
    lines.append(message.rstrip("\n"))
    lines.append("")  # ensure trailing newline

    payload = "\n".join(lines).encode("utf-8")

    return write_object("commit", payload)
def my_get_commit(message,to_ignore,author_name = "You",author_email = "you@example.com"):
    curr_branch = get_curr_branch()
    parent_oid = find_parent_commit(curr_branch)
    curr_tree_oid = extract_tree_oid_from_commit_head(curr_branch)
    tree_oid = my_get_write_tree("", to_ignore)
    if tree_oid == curr_tree_oid:
        return "nothing to commit"
    else :
        oid = write_commit(tree_oid,message,parent_oid,author_name,author_email)
        change_ref(oid,curr_branch)
        return "Commit created."