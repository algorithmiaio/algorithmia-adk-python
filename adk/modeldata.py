import os
import json
import hashlib
from adk.classes import FileData


class ModelData(object):
    def __init__(self, client, model_manifest_path):
        self.manifest_freeze_path = model_manifest_path
        self.manifest_data = get_manifest(self.manifest_freeze_path)
        self.client = client
        self.models = {}
        self.user_data = {}
        self.system_data = {}

    def available(self):
        if self.manifest_data:
            return True
        else:
            return False

    def initialize(self):
        if self.client is None:
            raise Exception("Client was not defined, please define a Client when using Model Manifests.")
        for required_file in self.manifest_data['required_files']:
            name = required_file['name']
            if name in self.models:
                raise Exception("Duplicate 'name' detected. \n"
                                + name + " was found to be used by more than one data file, please rename.")
            expected_hash = required_file['md5_checksum']
            with self.client.file(required_file['source_uri']).getFile() as f:
                local_data_path = f.name
            real_hash = md5_for_file(local_data_path)
            if real_hash != expected_hash and required_file['fail_on_tamper']:
                raise Exception("Model File Mismatch for " + name +
                                "\nexpected hash:  " + expected_hash + "\nreal hash: " + real_hash)
            else:
                self.models[name] = FileData(real_hash, local_data_path)

    def get_model(self, model_name):
        if model_name in self.models:
            return self.models[model_name].file_path
        elif len([optional for optional in self.manifest_data['optional_files'] if
                  optional['name'] == model_name]) > 0:
            self.find_optional_model(model_name)
            return self.models[model_name].file_path
        else:
            raise Exception("model name " + model_name + " not found in manifest")

    def find_optional_model(self, file_name):

        found_models = [optional for optional in self.manifest_data['optional_files'] if
                        optional['name'] == file_name]
        if len(found_models) == 0:
            raise Exception("file with name '" + file_name + "' not found in model manifest.")
        model_info = found_models[0]
        self.models[file_name] = {}
        expected_hash = model_info['md5_checksum']
        with self.client.file(model_info['source_uri']).getFile() as f:
            local_data_path = f.name
        real_hash = md5_for_file(local_data_path)
        if real_hash != expected_hash and model_info['fail_on_tamper']:
            raise Exception("Model File Mismatch for " + file_name +
                            "\nexpected hash:  " + expected_hash + "\nreal hash: " + real_hash)
        else:
            self.models[file_name] = FileData(real_hash, local_data_path)


def get_manifest(manifest_path):
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest_data = json.load(f)
        expected_lock_checksum = manifest_data.get('lock_checksum')
        del manifest_data['lock_checksum']
        detected_lock_checksum = md5_for_str(str(manifest_data))
        if expected_lock_checksum != detected_lock_checksum:
            raise Exception("Manifest FreezeFile Tamper Detected; please use the CLI and 'algo freeze' to rebuild your "
                            "algorithm's freeze file.")
        return manifest_data
    else:
        return None


def md5_for_file(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return str(hash_md5.hexdigest())


def md5_for_str(content):
    hash_md5 = hashlib.md5()
    hash_md5.update(content.encode())
    return str(hash_md5.hexdigest())
