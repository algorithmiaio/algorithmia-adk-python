import json
import os
import unittest
from tests.AdkTest import ADKTest
from tests.adk_algorithms import *


class LocalTest(unittest.TestCase):
    fifo_pipe_path = "/tmp/algoout"

    def setUp(self):
        try:
            os.remove(self.fifo_pipe_path)
        except:
            pass

    def execute_example(self, input, apply, load=None):
        if load:
            algo = ADKTest(apply, load)
        else:
            algo = ADKTest(apply)
        output = []
        algo.init(input, pprint=lambda x: output.append(x))
        return output[0]

    def execute_manifest_example(self, input, apply, load, manifest_path):
        client = Algorithmia.client()
        algo = ADKTest(apply, load, manifest_path=manifest_path, client=client)
        output = []
        algo.init(input, pprint=lambda x: output.append(x))
        return output[0]

    def execute_without_load(self, input, apply):
        algo = ADKTest(apply)
        output = []
        algo.init(input, pprint=lambda x: output.append(x))
        return output[0]

    def test_basic(self):
        input = 'Algorithmia'
        expected_output = {"metadata":
            {
                "content_type": "text"
            },
            "result": "hello Algorithmia"
        }
        actual_output = json.loads(self.execute_example(input, apply_input_or_context))
        self.assertEqual(expected_output, actual_output)

    def test_basic_2(self):
        input = 'Algorithmia'
        expected_output = {"metadata":
            {
                "content_type": "text"
            },
            "result": "hello Algorithmia"
        }
        actual_output = json.loads(self.execute_without_load(input, apply_basic))
        self.assertEqual(expected_output, actual_output)

    def test_algorithm_loading_basic(self):
        input = "ignore me"
        expected_output = {'metadata':
            {
                'content_type': 'json'
            },
            'result': {'message': 'This message was loaded prior to runtime'}
        }
        actual_output = json.loads(self.execute_example(input, apply_input_or_context, loading_text))
        self.assertEqual(expected_output, actual_output)

    def test_algorithm_loading_algorithmia(self):
        input = "ignore me"
        expected_output = {'metadata':
            {
                'content_type': 'json'
            },
            'result': {
                'data_url': 'data://demo/collection/somefile.json',
                'data': {'foo': 'bar'}
            }
        }
        actual_output = json.loads(self.execute_example(input, apply_input_or_context, loading_file_from_algorithmia))
        self.assertEqual(expected_output, actual_output)

    def test_error_loading(self):
        input = "Algorithmia"
        expected_output = {'error':
                               {'message': 'This exception was thrown in loading',
                                'error_type': 'LoadingError',
                                'stacktrace': ''
                                }
                           }
        actual_output = json.loads(self.execute_example(input, apply_input_or_context, loading_exception))
        # beacuse the stacktrace is local path specific,
        # we're going to assume it's setup correctly and remove it from our equality check
        actual_output["error"]["stacktrace"] = ''
        self.assertEqual(expected_output, actual_output)

    def test_error_binary_data(self):
        input = b"payload"
        expected_output = {'error':
                               {'message': 'can only concatenate str (not "bytes") to str',
                                'error_type': 'AlgorithmError',
                                'stacktrace': ''
                                }
                           }
        actual_output = json.loads(self.execute_without_load(input, apply_basic))
        actual_output["error"]["stacktrace"] = ''
        self.assertEqual(expected_output, actual_output)

    def test_binary_data(self):
        input = b"payload"
        expected_output = {'metadata':
            {
                'content_type': 'binary'
            },
            'result': "aGVsbG8gcGF5bG9hZA=="
        }
        actual_output = json.loads(self.execute_without_load(input, apply_binary))
        self.assertEqual(expected_output, actual_output)

    def test_manifest_file_success(self):
        input = "Algorithmia"
        expected_output = {'metadata':
            {
                'content_type': 'text'
            },
            'result': "all model files were successfully loaded"
        }
        actual_output = json.loads(self.execute_manifest_example(input, apply_successful_manifest_parsing,
                                                                 loading_with_manifest,
                                                                 manifest_path="tests/manifests/good_model_manifest"
                                                                               ".json"))
        self.assertEqual(expected_output, actual_output)

    def test_manifest_file_tampered(self):
        input = "Algorithmia"
        expected_output = {"error": {"error_type": "LoadingError",
                                     "message": "Model File Mismatch for squeezenet\n"
                                                "expected hash:  f20b50b44fdef367a225d41f747a0963\n"
                                                "real hash: 46a44d32d2c5c07f7f66324bef4c7266",
                                     "stacktrace": "NoneType: None\n"}}

        actual_output = json.loads(self.execute_manifest_example(input, apply_successful_manifest_parsing,
                                                                 loading_with_manifest,
                                                                 manifest_path="tests/manifests/bad_model_manifest"
                                                                               ".json"))
        self.assertEqual(expected_output, actual_output)


def run_test():
    unittest.main()
