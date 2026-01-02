import sys
import os
import zlib
import hashlib
from blob import my_get_hash_object,my_get_cat_file,write_object
from help import find_repo_root
def write_tree(dir_path,to_ignore):
    with os.scandir(dir_path) as entries:
        all_raw_data = []
        # Each entry: (file/dict name, data)
        for child in entries:
            if child.name in to_ignore:
                continue
            if child.is_file():
                mode = b"100644"
                oid = my_get_hash_object(child)
            elif child.is_dir():
                mode = b"40000"
                oid = write_tree(os.path.join(dir_path,child),to_ignore)
            raw_data = mode + b" " + child.name.encode("utf-8")  + b"\0" + bytes.fromhex(oid)
            all_raw_data.append([child.name,raw_data])
        all_raw_data.sort(key= lambda t : t[0])
        data = b"".join(e[1] for e in all_raw_data)
        return write_object("tree",data)


def parse_tree(sha):
    out = []
    data = my_get_cat_file(sha)
    i = 0
    while i < len(data):
        sp = data.find(b" ",i)
        nl = data.find(b"\0",sp+1)
        mode = data[i:sp].decode("ascii")
        name = data[sp+1:nl].decode("ascii")
        sha = data[nl+1:nl+21].hex()
        out.append([mode,name,sha])
        i = nl + 21
    return out


def my_get_write_tree(path = "",to_ignore = None):
    dir_path = os.path.join(find_repo_root(path),path)
    return write_tree(dir_path,to_ignore)


def my_get_ls_tree(path = "",to_ignore = None,names_only = False):
    dir_path = os.path.join(find_repo_root(path),path)
    out = parse_tree(write_tree(dir_path,to_ignore))
    res = []
    for o in out:
        res.append(o[1] if names_only else " ".join(o))
    return "\n".join(res)
