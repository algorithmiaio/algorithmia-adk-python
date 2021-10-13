import sys
import json
import unittest
import os
from tests.AdkTest import ADKTest
import base64
from tests.adk_algorithms import *


class RemoteTest(unittest.TestCase):
    if os.name == "posix":
        fifo_pipe_path = "/tmp/algoout"
    fifo_pipe = None

    def setUp(self):
        try:
            os.mkfifo(self.fifo_pipe_path)
        except Exception:
            pass

    def tearDown(self):
        if os.name == "posix":
            os.remove(self.fifo_pipe_path)

    def read_in(self):
        if os.name == "posix":
            return self.read_from_pipe()
        if os.name == "nt":
            return self.read_from_stdin()

    def read_from_stdin(self):
        return json.loads(sys.stdin)

    def read_from_pipe(self):
        read_obj = os.read(self.fifo_pipe, 10000)
        if isinstance(read_obj, bytes):
            read_obj = read_obj.decode("utf-8")
        actual_output = json.loads(read_obj)
        os.close(self.fifo_pipe)
        return actual_output

    def open_pipe(self):
        if os.name == "posix":
            self.fifo_pipe = os.open(self.fifo_pipe_path, os.O_RDONLY | os.O_NONBLOCK)

    def execute_example(self, input, apply, load=None):
        self.open_pipe()
        algo = ADKTest(apply, load)
        sys.stdin = input
        algo.init()
        output = self.read_in()
        return output

    def execute_without_load(self, input, apply):
        self.open_pipe()
        algo = ADKTest(apply)
        sys.stdin = input
        algo.init()
        output = self.read_in()
        return output

    def execute_manifest_example(self, input, apply, load, manifest_path):
        client = Algorithmia.client()
        self.open_pipe()
        algo = ADKTest(apply, load, manifest_path=manifest_path, client=client)
        sys.stdin = input
        algo.init()
        output = self.read_in()
        return output

    # ----- Tests ----- #

    def test_basic(self):
        input = {'content_type': 'json', 'data': 'Algorithmia'}
        expected_output = {"metadata":
            {
                "content_type": "text"
            },
            "result": "hello Algorithmia"
        }
        input = [str(json.dumps(input))]
        actual_output = self.execute_example(input, apply_input_or_context)
        self.assertEqual(expected_output, actual_output)

    def test_basic_2(self):
        input = {'content_type': 'json', 'data': 'Algorithmia'}
        expected_output = {"metadata":
            {
                "content_type": "text"
            },
            "result": "hello Algorithmia"
        }
        input = [str(json.dumps(input))]
        actual_output = self.execute_without_load(input, apply_basic)
        self.assertEqual(expected_output, actual_output)

    def test_algorithm_loading_basic(self):
        input = {'content_type': 'json', 'data': 'ignore me'}
        expected_output = {'metadata':
            {
                'content_type': 'json'
            },
            'result': {'message': 'This message was loaded prior to runtime'}
        }
        input = [str(json.dumps(input))]
        actual_output = self.execute_example(input, apply_input_or_context, loading_text)
        self.assertEqual(expected_output, actual_output)

    def test_algorithm_loading_algorithmia(self):
        input = {'content_type': 'json', 'data': 'ignore me'}
        expected_output = {'metadata':
            {
                'content_type': 'json'
            },
            'result': {
                'data_url': 'data://demo/collection/somefile.json',
                'data': {'foo': 'bar'}
            }
        }
        input = [str(json.dumps(input))]
        actual_output = self.execute_example(input, apply_input_or_context, loading_file_from_algorithmia)
        self.assertEqual(expected_output, actual_output)

    def test_error_loading(self):
        input = {'content_type': 'json', 'data': 'Algorithmia'}
        expected_output = {'error':
                               {'message': 'This exception was thrown in loading',
                                'error_type': 'LoadingError',
                                'stacktrace': ''
                                }
                           }
        input = [str(json.dumps(input))]
        actual_output = self.execute_example(input, apply_input_or_context, loading_exception)
        # beacuse the stacktrace is local path specific,
        # we're going to assume it's setup correctly and remove it from our equality check
        actual_output["error"]["stacktrace"] = ''
        self.assertEqual(expected_output, actual_output)

    def test_error_binary_data(self):
        input = {"content_type": "binary", "data": "cGF5bG9hZA=="}
        expected_output = {'error':
                               {'message': 'can only concatenate str (not "bytes") to str',
                                'error_type': 'AlgorithmError',
                                'stacktrace': ''
                                }
                           }
        input = [str(json.dumps(input))]
        actual_output = self.execute_without_load(input, apply_basic)
        actual_output["error"]["stacktrace"] = ''
        self.assertEqual(expected_output, actual_output)

    def test_binary_data(self):
        input = {"content_type": "binary", "data": "cGF5bG9hZA=="}
        expected_output = {'metadata':
            {
                'content_type': 'binary'
            },
            'result': "aGVsbG8gcGF5bG9hZA=="
        }
        input = [str(json.dumps(input))]
        actual_output = self.execute_without_load(input, apply_binary)
        self.assertEqual(expected_output, actual_output)

    def test_manifest_file_success(self):
        input = {'content_type': 'json', 'data': 'Algorithmia'}
        expected_output = {'metadata':
            {
                'content_type': 'text'
            },
            'result': "all model files were successfully loaded"
        }
        input = [str(json.dumps(input))]
        actual_output = self.execute_manifest_example(input, apply_successful_manifest_parsing,
                                                      loading_with_manifest,
                                                      manifest_path="tests/manifests/good_model_manifest"
                                                                    ".json.freeze")
        self.assertEqual(expected_output, actual_output)


def run_test():
    unittest.main()
