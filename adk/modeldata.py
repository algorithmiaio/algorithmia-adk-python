import os
import json
import hashlib
from adk.classes import FileData


class ModelData(object):
    def __init__(self, client, model_manifest_path):
        self.manifest_reg_path = model_manifest_path
        self.manifest_frozen_path = "{}.freeze".format(self.manifest_reg_path)
        self.manifest_data = self.get_manifest()
        self.client = client
        self.models = {}
        self.usr_key = "__user__"
        self.using_frozen = True

    def __getitem__(self, key):
        return getattr(self, self.usr_key + key)

    def __setitem__(self, key, value):
        setattr(self, self.usr_key + key, value)

    def data(self):
        __dict = self.__dict__
        output = {}
        for key in __dict.keys():
            if self.usr_key in key:
                without_usr_key = key.split(self.usr_key)[1]
                output[without_usr_key] = __dict[key]
        return output

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
            source_uri = required_file['source_uri']
            fail_on_tamper = required_file.get('fail_on_tamper', False)
            expected_hash = required_file.get('md5_checksum', None)
            if name in self.models:
                raise Exception("Duplicate 'name' detected. \n"
                                + name + " was found to be used by more than one data file, please rename.")
            with self.client.file(source_uri).getFile() as f:
                local_data_path = f.name
            real_hash = md5_for_file(local_data_path)
            if real_hash != expected_hash and fail_on_tamper:
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
        source_uri = model_info['source_uri']
        fail_on_tamper = model_info.get("fail_on_tamper", False)
        expected_hash = model_info.get('md5_checksum', None)
        with self.client.file(source_uri).getFile() as f:
            local_data_path = f.name
        real_hash = md5_for_file(local_data_path)
        if self.using_frozen:
            if real_hash != expected_hash and fail_on_tamper:
                raise Exception("Model File Mismatch for " + file_name +
                                "\nexpected hash:  " + expected_hash + "\nreal hash: " + real_hash)
            else:
                self.models[file_name] = FileData(real_hash, local_data_path)
        else:
            self.models[file_name] = FileData(real_hash, local_data_path)


    def get_manifest(self):
        if os.path.exists(self.manifest_frozen_path):
            with open(self.manifest_frozen_path) as f:
                manifest_data = json.load(f)
            if check_lock(manifest_data):
                return manifest_data
            else:
                raise Exception("Manifest FreezeFile Tamper Detected; please use the CLI and 'algo freeze' to rebuild your "
                                "algorithm's freeze file.")
        elif os.path.exists(self.manifest_reg_path):
            with open(self.manifest_reg_path) as f:
                manifest_data = json.load(f)
            self.using_frozen = False
            return manifest_data
        else:
            return None


def check_lock(manifest_data):
    expected_lock_checksum = manifest_data.get('lock_checksum')
    del manifest_data['lock_checksum']
    detected_lock_checksum = md5_for_str(str(manifest_data))
    if expected_lock_checksum != detected_lock_checksum:
        return False
    else:
        return True


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
