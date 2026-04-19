import hashlib


def hash_pair(a, b):
    """Hash two strings together."""
    return hashlib.sha256((a + b).encode()).hexdigest()

def build_merkle_tree(leaves):
    """Build a Merkle tree from a list of leaf hashes."""
    if not leaves:
        raise IndexError("Cannot build Merkle tree with no leaves")
    
    if len(leaves) == 1:
        return leaves[0]
        
    next_level = []
    for i in range(0, len(leaves), 2):
        if i + 1 < len(leaves):
            next_level.append(hash_pair(leaves[i], leaves[i+1]))
        else:
            # Duplicate last element if odd number
            next_level.append(hash_pair(leaves[i], leaves[i]))
            
    return build_merkle_tree(next_level)