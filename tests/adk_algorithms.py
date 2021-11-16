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


def apply_input_or_context(input, model_data=None):
    if model_data:
        return model_data.data()
    else:
        return "hello " + input


def apply_successful_manifest_parsing(input, model_data):
    if model_data:
        return "all model files were successfully loaded"
    else:
        return "model files were not loaded correctly"


# -- Loading functions --- #
def loading_text(modelData):
    modelData['message'] = 'This message was loaded prior to runtime'
    return modelData


def loading_exception(modelData):
    raise Exception("This exception was thrown in loading")


def loading_file_from_algorithmia(modelData):
    modelData['data_url'] = 'data://demo/collection/somefile.json'
    modelData['data'] = modelData.client.file(modelData['data_url']).getJson()
    return modelData


def loading_with_manifest(modelData):
    modelData["squeezenet"] = modelData.get_model("squeezenet")
    modelData['labels'] = modelData.get_model("labels")
    # optional model
    modelData['mobilenet'] = modelData.get_model("mobilenet")
    return modelData
