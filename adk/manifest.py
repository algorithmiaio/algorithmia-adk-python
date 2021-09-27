import os
import json
import hashlib


class ManifestData(object):
    def __init__(self, client, model_manifest_path):
        self.manifest_lock_path = model_manifest_path
        self.manifest_data = get_manifest(self.manifest_lock_path)
        self.client = client
        self.models = {}

    def available(self):
        if self.manifest_data:
            return True
        else:
            return False

    def initialize(self):
        if self.client is None:
            raise Exception("Client was not defined, please define a Client when using Model Manifests.")
        for required_file in self.manifest_data['required_models']:
            name = required_file['name']
            if name in self.models:
                raise Exception("Duplicate 'name' detected. \n"
                                + name + " was found to be used by more than one data file, please rename.")
            self.models[name] = {}
            expected_hash = required_file['md5_checksum']
            with self.client.file(required_file['data_api_path']).getFile() as f:
                local_data_path = f.name
            real_hash = md5(local_data_path)
            if real_hash != expected_hash and required_file['fail_on_tamper']:
                raise Exception("Model File Mismatch for " + name +
                                "\nexpected hash:  " + expected_hash + "\nreal hash: " + real_hash)
            else:
                self.models[name]["md5_checksum"] = real_hash
                self.models[name]['model_path'] = local_data_path

    def get_model(self, model_name):
        if model_name in self.models:
            return self.models[model_name]['model_path']
        elif len([optional for optional in self.manifest_data['optional_models'] if
                  optional['name'] == model_name]) > 0:
            self.find_optional_model(model_name)
            return self.models[model_name]['model_path']
        else:
            raise Exception("model name " + model_name + " not found in manifest")

    def find_optional_model(self, model_name):

        found_models = [optional for optional in self.manifest_data['optional_models'] if
                        optional['name'] == model_name]
        if len(found_models) == 0:
            raise Exception("model with name '" + model_name + "' not found in model manifest.")
        model_info = found_models[0]
        self.models[model_name] = {}
        expected_hash = model_info['md5_checksum']
        with self.client.file(model_info['data_api_path']).getFile() as f:
            local_data_path = f.name
        real_hash = md5(local_data_path)
        if real_hash != expected_hash and model_info['fail_on_tamper']:
            raise Exception("Model File Mismatch for " + model_name +
                            "\nexpected hash:  " + expected_hash + "\nreal hash: " + real_hash)
        else:
            self.models[model_name]["md5_checksum"] = real_hash
            self.models[model_name]['model_path'] = local_data_path


def get_manifest(manifest_path):
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest_data = json.load(f)
        return manifest_data
    else:
        return None


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return str(hash_md5.hexdigest())
