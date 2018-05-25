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

    def test_suite_header_creation(self):
        line = "Test Suite: Starting Setup of TsSuite"
        exp_result = "======================================================" \
                     "===================================================\n" \
                     "Test Suite: Starting Setup of TsSuite\n" \
                     "======================================================" \
                     "==================================================="
        suite_h = vlogline.SuiteHeader(line)
        self.assertEqual(str(suite_h), exp_result)
        self.assertEqual(suite_h.suite_name, "TsSuite")

    def test_case_header_creation(self):
        line = "Test Case 0: Starting Test of TcTest"
        exp_result = "======================================================" \
                     "===================================================\n" \
                     "Test Case 0: Starting Test of TcTest\n" \
                     "======================================================" \
                     "==================================================="
        case_h = vlogline.TestCaseHeader(line)
        self.assertEqual(str(case_h), exp_result)
        self.assertEqual(case_h.test_case_name, "TcTest")
        self.assertEqual(case_h.number, 0)

    def test_step_header_creation(self):
        line = "Starting Step 5 for TcTest: Verify Something\n" \
               "Expect: Something else"
        exp_result = "------------------------------------------------------" \
                     "---------------------------------------------------\n" \
                     "Starting Step 5 for TcTest: Verify Something\n" \
                     "Expect: Something else\n" \
                     "------------------------------------------------------" \
                     "---------------------------------------------------"
        step_h = vlogline.StepHeader(line)
        self.assertEqual(str(step_h), exp_result)
        self.assertEqual(step_h.test_case_name, "TcTest")
        self.assertEqual(step_h.number, 5)
        self.assertEqual(step_h.action, "Verify Something")
        self.assertEqual(step_h.expected_results, "Something else")

    # def test_general_header_creation(self):
    #     line = "Final Report"
    #     exp_result = "======================================================" \
    #                  "===================================================\n" \
    #                  "Final Report\n" \
    #                  "======================================================" \
    #                  "==================================================="
    #     gen_h = vlogline.GeneralHeader(line)
    #     self.assertEqual(str(gen_h), exp_result)



if __name__ == '__main__':
    unittest.main()