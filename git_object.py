import os
import zlib
import hashlib


class GitObject:
    """
    Base class for all Git objects (blob, tree, commit).
    Provides common functionality for storing, retrieving, and hashing objects.
    """

    @staticmethod
    def write_object(object_type, data, write=True):
        """
        Write a Git object to the .mygit/objects directory.
        
        Args:
            object_type: Type of object ('blob', 'tree', or 'commit')
            data: Raw object data as bytes
            write: Whether to actually write to disk (default: True)
            
        Returns:
            SHA-1 hash of the object
        """
        # Create header: "type size\0"
        header = f"{object_type} {len(data)}\0".encode("ascii")
        object_data = header + data
        
        # Calculate SHA-1 hash
        object_hash = hashlib.sha1(object_data).hexdigest()
        
        if write:
            # Store in .mygit/objects/[first 2 chars]/[remaining chars]
            object_path = os.path.join(".mygit", "objects", object_hash[:2], object_hash[2:])
            
            # Only write if object doesn't already exist
            if not os.path.exists(object_path):
                os.makedirs(os.path.dirname(object_path), exist_ok=True)
                with open(object_path, "wb") as f:
                    f.write(zlib.compress(object_data))
        
        return object_hash

    @staticmethod
    def read_object(object_hash):
        """
        Read and decompress a Git object from storage.
        
        Args:
            object_hash: SHA-1 hash of the object
            
        Returns:
            Raw object content (without header) as bytes
        """
        object_path = os.path.join(".mygit", "objects", object_hash[:2], object_hash[2:])
        
        if not os.path.exists(object_path):
            raise FileNotFoundError(f"Object {object_hash} not found")
        
        with open(object_path, "rb") as f:
            compressed_data = f.read()
            decompressed_data = zlib.decompress(compressed_data)
            
            # Find the null byte separating header from content
            null_byte_index = decompressed_data.find(b"\x00")
            
            # Return content without header
            return decompressed_data[null_byte_index + 1:]
