from tests.test_adk_remote import RemoteTest
from tests.test_adk_local import LocalTest
import unittest
import os
if __name__ == "__main__":
    if os.getenv('ALGORITHMIA_API_KEY', None) == None:
        raise Exception("api key not provided, please export your ALGORITHMIA_API_KEY environment variable.")
    unittest.main()