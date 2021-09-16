import base64
import inspect
import json
import os
import sys
import traceback
import six


class ADK(object):
    def __init__(self, apply_func, load_func=None):
        """
        Creates the adk object
        :param apply_func: A required function that can have an arity of 1-2, depending on if loading occurs
        :param load_func: An optional supplier function used if load time events are required, has an arity of 0.
        """
        self.FIFO_PATH = "/tmp/algoout"
        apply_args, _, _, _, _, _, _ = inspect.getfullargspec(apply_func)
        if load_func:
            load_args, _, _, _, _, _, _ = inspect.getfullargspec(load_func)
            if len(load_args) > 0:
                raise Exception("load function must not have parameters")
            self.load_func = load_func
        else:
            self.load_func = None
        if len(apply_args) > 2 or len(apply_args) == 0:
            raise Exception("apply function may have between 1 and 2 parameters, not {}".format(len(apply_args)))
        self.apply_func = apply_func
        self.is_local = not os.path.exists(self.FIFO_PATH)
        self.load_result = None
        self.loading_exception = None

    def load(self):
        try:
            if self.load_func:
                self.load_result = self.load_func()
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
            if self.load_result:
                apply_result = self.apply_func(payload, self.load_result)
            else:
                apply_result = self.apply_func(payload)
            response_obj = self.format_response(apply_result)
            return response_obj
        except Exception as e:
            response_obj = self.create_exception(e)
            return response_obj

    def format_data(self, request):
        if request["content_type"] in ["text", "json"]:
            data = request["data"]
        elif request["content_type"] == "binary":
            data = self.wrap_binary_data(base64.b64decode(request["data"]))
        else:
            raise Exception("Invalid content_type: {}".format(request["content_type"]))
        return data

    def is_binary(self, arg):
        if six.PY3:
            return isinstance(arg, base64.bytes_types)

        return isinstance(arg, bytearray)

    def wrap_binary_data(self, data):
        if six.PY3:
            return bytes(data)
        else:
            return bytearray(data)

    def format_response(self, response):
        if self.is_binary(response):
            content_type = "binary"
            response = str(base64.b64encode(response), "utf-8")
        elif isinstance(response, six.string_types) or isinstance(response, six.text_type):
            content_type = "text"
        else:
            content_type = "json"
        response_string = json.dumps(
            {
                "result": response,
                "metadata": {
                    "content_type": content_type
                }
            }
        )
        return response_string

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

    def create_exception(self, exception, loading_exception=False):
        if hasattr(exception, "error_type"):
            error_type = exception.error_type
        elif loading_exception:
            error_type = "LoadingError"
        else:
            error_type = "AlgorithmError"
        response = json.dumps({
            "error": {
                "message": str(exception),
                "stacktrace": traceback.format_exc(),
                "error_type": error_type,
            }
        })
        return response

    def process_local(self, local_payload, pprint):
        result = self.apply(local_payload)
        self.write_to_pipe(result, pprint=pprint)

    def init(self, local_payload=None, pprint=print):
            self.load()
            if self.is_local and local_payload:
                if self.loading_exception:
                    load_error = self.create_exception(self.loading_exception, loading_exception=True)
                    self.write_to_pipe(load_error, pprint=pprint)
                self.process_local(local_payload, pprint)
            else:
                for line in sys.stdin:
                    request = json.loads(line)
                    formatted_input = self.format_data(request)
                    if self.loading_exception:
                        load_error = self.create_exception(self.loading_exception, loading_exception=True)
                        self.write_to_pipe(load_error, pprint=pprint)
                    else:
                        result = self.apply(formatted_input)
                        self.write_to_pipe(result)
