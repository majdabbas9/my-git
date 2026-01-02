import sys
import os
import zlib
import hashlib
def write_object(object_name,data,write = True):
    to_store = (object_name + " " + str(len(data)) + "\0").encode("ascii") + data
    sha1 = hashlib.sha1(to_store).hexdigest()
    if write:
        path = os.path.join(".mygit","objects",sha1[:2],sha1[2:])
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(zlib.compress(to_store))
    return sha1

def my_get_hash_object(file_path,write = True):
    with open(file_path ,"rb") as f:
        data = f.read()
    return write_object("blob",data)

def my_get_cat_file(sha):
    path = os.path.join(".mygit","objects",sha[:2],sha[2:])
    if not os.path.exists(path):
        print("no file like that")
        exit(1)
    with open(path,"rb") as f:
        data = zlib.decompress(f.read())
        data_start = data.find(b"\x00")
        return data[data_start+1:]
