"""Run all test cases found in *_test.py modules located in this directory."""

from os import getcwd
from unittest import defaultTestLoader, TextTestResult, TextTestRunner
from warnings import resetwarnings, simplefilter


resetwarnings()
simplefilter('error')
test_suite = defaultTestLoader.discover(
    '.' if getcwd().endswith('tests') else 'tests')
test_runner = TextTestRunner(resultclass=TextTestResult, verbosity=1)
result = test_runner.run(test_suite)
raise SystemExit(not result.wasSuccessful())
