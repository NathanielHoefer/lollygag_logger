import unittest
from datetime import datetime

from vl_logger import vlogline
from vl_logger.vutils import VLogType


class TestLogLineCreation(unittest.TestCase):

    def test_std_log_creation_no_type(self):
        line = "2017-10-30 19:13:32.208116 DEBUG [res.core:636] " \
               "[MainProcess:MainThread] Sending HTTP POST request"
        std_log = vlogline.Standard(line)
        self.assertEqual(str(std_log), line)

    def test_std_log_creation_type(self):
        line = "2017-10-30 19:13:32.208116 DEBUG [res.core:636] " \
               "[MainProcess:MainThread] Sending HTTP POST request"
        std_log = vlogline.Standard(line, VLogType.DEBUG)
        self.assertEqual(str(std_log), line)

    def test_set_max_len(self):
        vlogline.Standard.set_max_line_len(50)
        self.assertEqual(vlogline.Standard.MAX_LINE_LEN, 50)



if __name__ == '__main__':
    unittest.main()