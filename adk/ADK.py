import inspect
import json
import os
import sys
import Algorithmia
from adk.io import create_exception, format_data, format_response
from adk.manifest.modeldata import ModelData


class ADK(object):
    def __init__(self, apply_func, load_func=None, client=None):
        """
        Creates the adk object
        :param apply_func: A required function that can have an arity of 1-2, depending on if loading occurs
        :param load_func: An optional supplier function used if load time events are required, if a model manifest is provided;
        the function may have a single `manifest` parameter to interact with the model manifest, otherwise must have no parameters.
        :param client: A Algorithmia Client instance that might be user defined,
         and is used for interacting with a model manifest file; if defined.
        """
        self.FIFO_PATH = "/tmp/algoout"

        if client:
            self.client = client
        else:
            self.client = Algorithmia.client()

        apply_args, _, _, _, _, _, _ = inspect.getfullargspec(apply_func)
        self.apply_arity = len(apply_args)
        if load_func:
            load_args, _, _, _, _, _, _ = inspect.getfullargspec(load_func)
            self.load_arity = len(load_args)
            if self.load_arity != 1:
                raise Exception("load function expects 1 parameter to be used to store algorithm state")
            self.load_func = load_func
        else:
            self.load_func = None
        self.apply_func = apply_func
        self.is_local = not os.path.exists(self.FIFO_PATH)
        self.load_result = None
        self.loading_exception = None
        self.manifest_path = "model_manifest.json.freeze"
        self.model_data = self.init_manifest(self.manifest_path)

    def init_manifest(self, path):
        return ModelData(self.client, path)

    def load(self):
        try:
            if self.model_data.available():
                self.model_data.initialize()
            if self.load_func:
                self.load_result = self.load_func(self.model_data)
        except Exception as e:
            self.loading_exception = e
        finally:
            if self.is_local:
                print("loading complete")
            else:
                print("PIPE_INIT_COMPLETE")
                sys.stdout.flush()

    def apply(self, payload):
        try:
            if self.load_result and self.apply_arity == 2:
                apply_result = self.apply_func(payload, self.load_result)
            else:
                apply_result = self.apply_func(payload)
            response_obj = format_response(apply_result)
            return response_obj
        except Exception as e:
            response_obj = create_exception(e)
            return response_obj

    def write_to_pipe(self, payload, pprint=print):
        if self.is_local:
            if isinstance(payload, dict):
                raise Exception(payload)
            else:
                pprint(payload)
        else:
            if os.name == "posix":
                with open(self.FIFO_PATH, "w") as f:
                    f.write(payload)
                    f.write("\n")
                sys.stdout.flush()
            if os.name == "nt":
                sys.stdin = payload

    def process_local(self, local_payload, pprint):
        result = self.apply(local_payload)
        self.write_to_pipe(result, pprint=pprint)

    def init(self, local_payload=None, pprint=print):
        self.load()
        if self.is_local and local_payload:
            if self.loading_exception:
                load_error = create_exception(self.loading_exception, loading_exception=True)
                self.write_to_pipe(load_error, pprint=pprint)
            self.process_local(local_payload, pprint)
        else:
            for line in sys.stdin:
                request = json.loads(line)
                formatted_input = format_data(request)
                if self.loading_exception:
                    load_error = create_exception(self.loading_exception, loading_exception=True)
                    self.write_to_pipe(load_error, pprint=pprint)
                else:
                    result = self.apply(formatted_input)
                    self.write_to_pipe(result)
