import traceback
import six
import base64
import json


def format_data(request):
    if request["content_type"] in ["text", "json"]:
        data = request["data"]
    elif request["content_type"] == "binary":
        data = wrap_binary_data(base64.b64decode(request["data"]))
    else:
        raise Exception("Invalid content_type: {}".format(request["content_type"]))
    return data


def is_binary(arg):
    if six.PY3:
        return isinstance(arg, base64.bytes_types)

    return isinstance(arg, bytearray)


def wrap_binary_data(data):
    if six.PY3:
        return bytes(data)
    else:
        return bytearray(data)


def format_response(response):
    if is_binary(response):
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


def create_exception(exception, loading_exception=False):
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
