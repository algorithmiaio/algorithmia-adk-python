import json
import os
import unittest
from adk import ADK
from tests.adk_algorithms import *


class LocalTest(unittest.TestCase):
    fifo_pipe_path = "/tmp/algoout"

    def setUp(self):
        try:
            os.remove(self.fifo_pipe_path)
        except:
            pass

    def execute_example(self, input, apply, load=lambda: None):
        algo = ADK(apply, load)
        output = []
        algo.init(input, pprint=lambda x: output.append(x))
        return output[0]

    def execute_without_load(self, input, apply):
        algo = ADK(apply)
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
                                'error_type': 'AlgorithmError',
                                'stacktrace': ''
                                }
                           }
        actual_output = json.loads(self.execute_example(input, apply_input_or_context, loading_exception))
        # beacuse the stacktrace is local path specific,
        # we're going to assume it's setup correctly and remove it from our equality check
        actual_output["error"]["stacktrace"] = ''
        self.assertEqual(expected_output, actual_output)


def run_test():
    unittest.main()
