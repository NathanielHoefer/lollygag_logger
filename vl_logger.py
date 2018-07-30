#!/usr/bin/env python

"""
Formats the logs to be output to the screen.
"""

import argparse
import re
import requests
import os
import subprocess

from vl_logger.vformatter import VFormatter
from vl_logger.vconfiginterface import VConfigInterface
from vl_logger.lollygag_logger import LollygagLogger

FILE_PATTERN = "^(?:\w|-)+\.log$"
AT2_PATTERN = "^\d+$"
SUITE_PATTERN = "^Ts(?:\w|-)+$"


def args():
    """Args for vl_logger.

    :rtype: ArgumentParser
    """

    # Descriptions for arg parse
    program = "Valence Lollygag Logger"
    description = "A non-obtrusive tool that captures Valence Logs being printed to the screen and " \
                  "formats them based on custom user preferences to assist in debugging. This " \
                  "tool can format logs from the 'vl run' command, stored log file, or an at2 task " \
                  "step instance. When formatting logs from the 'vl run' command, the tool will " \
                  "execute the command directly and the output will be in real time."
    read_desc = "Read from log file specified."
    at2_desc = ""  # TODO
    log_source = ""  # TODO
    testcase_desc = ""  # TODO
    format_api_desc = ""  # TODO
    summary_desc = ""  # TODO

    # Argument setup and parsing
    parser = argparse.ArgumentParser(prog=program, description=description)
    group = parser.add_mutually_exclusive_group()
    parser.add_argument("log_source", nargs=1, help=log_source)
    # group.add_argument("-r", "--read", action="store", dest="read_path", help=read_desc)
    # group.add_argument("-at2", action="store", dest="at2_inst", help=at2_desc)
    parser.add_argument("-t", "--testcase", action="store", dest="testcase", help=testcase_desc)
    parser.add_argument("-a", "--api", action="store_true", dest="format_api", help=format_api_desc)
    parser.add_argument("-s", "--summary", action="store_true", dest="summary", help=summary_desc)
    return parser.parse_args()


if __name__ == '__main__':
    args = args()

    logger = None

    COMMAND_LINE = True

    if COMMAND_LINE:

        log_source = args.log_source[0]

        savedfile = re.match(FILE_PATTERN, log_source)
        at2_instance = re.match(AT2_PATTERN, log_source)
        suite = re.match(SUITE_PATTERN, log_source)

        logfile = ""
        is_at2 = False

        if savedfile:
            logfile = log_source

        elif at2_instance:
            tmp_config = VConfigInterface()
            AT2_USER, AT2_PASS, FETCH_PATH = tmp_config.get_at2_info()


            output_file = "%s.log" % log_source
            logfile = os.path.join(os.getcwd(), output_file)
            print "AT2 option selected. TaskID: {0}.".format(log_source)
            if not os.path.exists(logfile):
                print "Downloading from AT2..."
                command = []
                command.extend(["python", "%s" % FETCH_PATH, "%s" % log_source])
                command.extend(["-o", "%s" % logfile])
                command.extend(["-u", "%s" % AT2_USER])
                command.extend(["-p", "%s" % AT2_PASS])
                subprocess.call(command)
            is_at2 = True

        elif suite:
            pass
        else:
            print "Invalid log source."
            exit(0)

        # Display specific test cases and steps
        if (savedfile or at2_instance) and args.testcase:
            tmp_config = VConfigInterface()
            tmp_config.use_unformatted()
            tmp_formatter = VFormatter(tmp_config)
            m = re.match("^(\d+|Tc\w*)(:(\d+))*$", args.testcase)
            # Test case specified
            if m.group(1):
                if m.group(1).isdigit():
                    logfile = tmp_formatter.parse_test_case(logfile, tc_num=int(m.group(1)))
                else:
                    logfile = tmp_formatter.parse_test_case(logfile, tc_name=m.group(1))
            # Step specified
            if m.group(3) and m.group(3).isdigit():
                logfile = tmp_formatter.parse_step(logfile, step_num=int(m.group(3)))

        config = VConfigInterface()

        if is_at2:
            config.at2_format()

        if args.format_api:
            config.format_api()

        if args.summary:
            config.display_summary()

        vl_console_output = VFormatter(config)
        try:
            with open(logfile, "r") as logfile:
                logger = LollygagLogger(logfile, vl_console_output)
                logger.run()
        except KeyboardInterrupt:
            logger.kill()
            print "Keyboard Interrupt: Exiting Logger"
            exit(0)

    else:
        # path = "/home/nathaniel/vl_artifacts/TsDriveEncryptionPersistenceAndAccessibility-2018-02-07T16.14.18/test.log"
        path = "/home/hnathani/vl_artifacts/TsNetworking_7285930_test.log"


        config = VConfigInterface()
        config.at2_format()

        # config.display_test_case(number=1)
        # config.display_step(number=1)
        config.display_summary(False)

        # config.use_unformatted()

        vl_console_output = VFormatter(config)
        # vl_console_output.parse_test_case(path, tc_num=0)
        try:
            with open(path, "r") as logfile:
                logger = LollygagLogger(logfile, vl_console_output)
                logger.run()
        except KeyboardInterrupt:
            logger.kill()
            print "Keyboard Interrupt: Exiting Logger"
            exit(0)
