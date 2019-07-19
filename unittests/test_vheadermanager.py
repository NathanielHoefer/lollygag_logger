import unittest

from datetime import datetime
from bin.vutils import VLogStdFields

from bin.vmanagers import HeaderManager
from bin import vlogline


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

        print("".join(["\n\n", headman.generate_summary()]))

if __name__ == '__main__':
    unittest.main()
