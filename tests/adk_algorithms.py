import Algorithmia
import base64
import os


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


def apply_successful_manifest_parsing(input, result):
    if result:
        return "all model files were successfully loaded"
    else:
        return "model files were not loaded correctly"


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


def loading_with_manifest(manifest):
    squeezenet_path = manifest.get_model("squeezenet")
    labels_path = manifest.get_model("labels")
    # optional model
    mobilenet_path = manifest.get_model("mobilenet")
    if os.path.exists(squeezenet_path) and os.path.exists(labels_path) and os.path.exists(mobilenet_path):
        return True
    else:
        return False
