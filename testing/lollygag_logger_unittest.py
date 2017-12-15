"""
=========================================================================================================
LollygagLogger Unittest
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/14/2017
"""

from lollygag_logger import LollygagLogger, LogFormatter
import unittest
import os
import sys
from cStringIO import StringIO
import subprocess

class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout


class TestFormatter(LogFormatter):

    def format(self, log_line):
        print log_line.strip()


class Streaming(unittest.TestCase):

    def test_file_stream(self):
        logger_output = []
        expected_output = []

        # Run Lollygag Logger and capture output
        with Capturing(logger_output) as logger_output:
            with open("stream_test.log", "r") as logfile:
                logger = LollygagLogger(logfile, TestFormatter())
                logger.run()

        with open("stream_test.log", "r") as logfile:
            expected_output = logfile.read().splitlines()

        self.assertEqual(logger_output, expected_output)

    def test_stdout_stream(self):
        logger_output = []
        expected_output = ["0", "1", "2"]
        proc = subprocess.Popen(["python", "test_program_stream.py"], stdout=subprocess.PIPE,
                                bufsize=1, universal_newlines=False)
        with Capturing(logger_output) as logger_output:
            logger = LollygagLogger(iter(proc.stdout.readline, b''), TestFormatter())
            logger.run()

        self.assertEqual(logger_output, expected_output)


if __name__ == "__main__":
    unittest.main()
