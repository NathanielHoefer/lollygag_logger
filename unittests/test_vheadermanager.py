import unittest
from datetime import datetime

from vl_logger import vlogline
from vl_logger.vutils import VLogType
from vl_logger.vutils import VLogStdFields
from vl_logger.vmanagers import HeaderManager


class TestHeaderManager(unittest.TestCase):

    def setUp(self):
        vlogline.Base.COLORIZE = False
        vlogline.Base.DISPLAY_FIELDS = [
            VLogStdFields.DATE,
            VLogStdFields.TIME,
            VLogStdFields.TYPE,
            VLogStdFields.SOURCE,
            VLogStdFields.THREAD,
            VLogStdFields.DETAILS
        ]
        vlogline.Base.CONDENSE_LINE = False
        vlogline.Base.SHORTEN_FIELDS = False


    def test_add_headers(self):
        format = " ".join(["%Y-%m-%d", "%H:%M:%S.%f"])
        headman = HeaderManager()
        headman.start_time(datetime.strptime("2018-05-08 13:33:22.984875", format), root=True)
        headman.end_time(datetime.strptime("2018-05-09 22:34:22.984875", format), root=True)

        gen_h1 = vlogline.GeneralHeader("=Preconditions=")
        headman.add_general(gen_h1)
        headman.start_time(datetime.strptime("2018-05-08 14:33:22.984875", format))

        suite_h1 = vlogline.SuiteHeader("=Test Suite: Starting Setup of TsSuite=")
        headman.add_suite(suite_h1)
        headman.start_time(datetime.strptime("2018-05-08 15:33:22.984875", format))

        tc_h1 = vlogline.TestCaseHeader("=Test Case 0: Starting Setup of TcTest=")
        headman.add_testcase(tc_h1)
        headman.start_time(datetime.strptime("2018-05-08 16:33:22.984875", format))

        tc_h2 = vlogline.TestCaseHeader("=Test Case 0: Starting Test of TcTest=")
        headman.add_testcase(tc_h2)
        headman.start_time(datetime.strptime("2018-05-08 17:33:22.984875", format))

        step_h1 = vlogline.StepHeader("-Starting Step 0 for TcTest: Verify Something\n"
                                      "Expect: Something else-")
        headman.add_step(step_h1)
        headman.start_time(datetime.strptime("2018-05-08 18:33:22.984875", format))
        step_h2 = vlogline.StepHeader("-Starting Step 1 for TcTest: Verify Something else\n"
                                      "Expect: Something else-")
        headman.add_step(step_h2)
        headman.start_time(datetime.strptime("2018-05-08 19:33:22.984875", format))

        tc_h3 = vlogline.TestCaseHeader("=Test Case 0: Starting Teardown of TcTest=")
        headman.add_testcase(tc_h3)
        headman.start_time(datetime.strptime("2018-05-08 20:33:22.984875", format))

        gen_h2 = vlogline.GeneralHeader("=Final Report=")
        headman.add_general(gen_h2)
        headman.start_time(datetime.strptime("2018-05-08 21:33:22.984875", format))

        print("\n\n" + headman.generate_summary())






    # def test_std_log_creation_no_type(self):
    #     line = "2017-10-30 19:13:32.208116 DEBUG [res.core:636] " \
    #            "[MainProcess:MainThread] Sending HTTP POST request"
    #     std_log = vlogline.Standard(line)
    #     self.assertEqual(str(std_log), line)
    #
    # def test_std_log_creation_type(self):
    #     line = "2017-10-30 19:13:32.208116 DEBUG [res.core:636] " \
    #            "[MainProcess:MainThread] Sending HTTP POST request"
    #     std_log = vlogline.Standard(line, VLogType.DEBUG)
    #     self.assertEqual(str(std_log), line)
    #
    # def test_std_log_creation_no_details(self):
    #     line = "2017-10-30 19:13:32.208116 INFO [res.core:636] " \
    #            "[MainProcess:MainThread]"
    #     std_log = vlogline.Standard(line, VLogType.INFO)
    #     self.assertEqual(str(std_log), line)
    #
    # def test_traceback_creation(self):
    #     lines = ['Traceback (most recent call last):',
    #              '  File "/home/http_utils.py", line 1078, in _call_cluster_api',
    #              '    check_json_rpc_response(json_response, retry_faults, method)',
    #              '  File "/home/testing/http_utils.py", line 1031, in check_json_rpc_response',
    #              '    response)',
    #              'ApiCallMethodException: DoesNotExist. JSON response: {u\'id\': 63}']
    #     trc_log = vlogline.Traceback(lines)
    #     self.assertEqual(str(trc_log), "\n".join(lines))
    #
    # def test_traceback_creation_leading_chars(self):
    #     lines = ['|! Traceback (most recent call last):',
    #              '|!   File "/home/http_utils.py", line 1078, in _call_cluster_api',
    #              '|!     check_json_rpc_response(json_response, retry_faults, method)',
    #              '|!   File "/home/testing/http_utils.py", line 1031, in check_json_rpc_response',
    #              '|!     response)',
    #              '|! ApiCallMethodException: DoesNotExist. JSON response: {u\'id\': 63}']
    #     trc_log = vlogline.Traceback(lines)
    #     self.assertEqual(str(trc_log), "\n".join(lines))
    #
    # def test_set_max_len(self):
    #     vlogline.Standard.set_max_line_len(50)
    #     self.assertEqual(vlogline.Standard.MAX_LINE_LEN, 50)
    #
    # def test_suite_header_creation(self):
    #     line = "=Test Suite: Starting Setup of TsSuite="
    #     exp_result = "======================================================" \
    #                  "===================================================\n" \
    #                  "Test Suite: Starting Setup of TsSuite\n" \
    #                  "======================================================" \
    #                  "==================================================="
    #     suite_h = vlogline.SuiteHeader(line)
    #     self.assertEqual(str(suite_h), exp_result)
    #     self.assertEqual(suite_h.suite_name, "TsSuite")
    #
    # def test_case_header_creation(self):
    #     line = "=Test Case 0: Starting Test of TcTest="
    #     exp_result = "======================================================" \
    #                  "===================================================\n" \
    #                  "Test Case 0: Starting Test of TcTest\n" \
    #                  "======================================================" \
    #                  "==================================================="
    #     case_h = vlogline.TestCaseHeader(line)
    #     self.assertEqual(str(case_h), exp_result)
    #     self.assertEqual(case_h.test_case_name, "TcTest")
    #     self.assertEqual(case_h.number, 0)
    #
    # def test_step_header_creation(self):
    #     line = "-Starting Step 5 for TcTest: Verify Something\n" \
    #            "Expect: Something else-"
    #     exp_result = "------------------------------------------------------" \
    #                  "---------------------------------------------------\n" \
    #                  "Starting Step 5 for TcTest: Verify Something\n" \
    #                  "Expect: Something else\n" \
    #                  "------------------------------------------------------" \
    #                  "---------------------------------------------------"
    #     step_h = vlogline.StepHeader(line)
    #     self.assertEqual(str(step_h), exp_result)
    #     self.assertEqual(step_h.test_case_name, "TcTest")
    #     self.assertEqual(step_h.number, 5)
    #     self.assertEqual(step_h.action, "Verify Something")
    #     self.assertEqual(step_h.expected_results, "Something else")
    #
    # def test_general_header_creation(self):
    #     line = "=Final Report="
    #     exp_result = "======================================================" \
    #                  "===================================================\n" \
    #                  "Final Report\n" \
    #                  "======================================================" \
    #                  "==================================================="
    #     gen_h = vlogline.GeneralHeader(line)
    #     self.assertEqual(str(gen_h), exp_result)


if __name__ == '__main__':
    unittest.main()