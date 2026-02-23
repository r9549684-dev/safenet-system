import hashlib

def stable_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()