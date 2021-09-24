import os
import json
import hashlib


def process_manifest(self):
    if os.path.exists(self.manifest_path):
        with open(self.manifest_path) as f:
            manifest_data = json.load(f)
        manifest = manifest_data


def check_hash(model_path, expected_hash):
    real_hash = md5(model_path)
    if real_hash == expected_hash:
        return True
    else:
        return False


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
