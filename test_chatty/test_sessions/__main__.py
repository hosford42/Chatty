import os
import unittest

loader = unittest.TestLoader()
suite = loader.discover(os.path.dirname(__file__))
runner = unittest.TextTestRunner()
runner.run(suite)
