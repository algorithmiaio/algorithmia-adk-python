import Algorithmia
import base64
import traceback
import json


# -- Apply functions --- #
def apply_basic(input):
    return "hello " + input


def apply_binary(input):
    if isinstance(input, bytes):
        input = input.decode('utf8')
    return bytes("hello " + input, encoding='utf8')


def apply_input_or_context(input, globals=None):
    if isinstance(globals, dict):
        return globals
    else:
        return "hello " + input


# -- Loading functions --- #
def loading_text():
    context = dict()
    context['message'] = 'This message was loaded prior to runtime'
    return context


def loading_exception():
    raise Exception("This exception was thrown in loading")


def loading_file_from_algorithmia():
    context = dict()
    client = Algorithmia.client()
    context['data_url'] = 'data://demo/collection/somefile.json'
    context['data'] = client.file(context['data_url']).getJson()
    return context


# -- exception handling Algorithms -- #

def exception_write_to_file(exc):
    response = {
        "error": {
            "message": str(exc),
            "stacktrace": traceback.format_exc(),
        }
    }
    with open("/tmp/exception.txt", 'w') as f:
        json.dump(response, f)
