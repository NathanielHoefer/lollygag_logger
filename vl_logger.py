#!/usr/bin/env python

"""
Formats the logs to be output to the screen.
"""

import argparse
import re

from vl_logger.vformatter import VFormatter
from vl_logger.vconfiginterface import VConfigInterface
from vl_logger.lollygag_logger import LollygagLogger


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
    testcase_desc = ""  # TODO
    format_api_desc = ""  # TODO
    summary_desc = ""  # TODO

    # Argument setup and parsing
    parser = argparse.ArgumentParser(prog=program, description=description)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-r", "--read", action="store", dest="read_path", help=read_desc)
    parser.add_argument("-t", "--testcase", action="store", dest="testcase", help=testcase_desc)
    parser.add_argument("-a", "--api", action="store_true", dest="format_api", help=format_api_desc)
    parser.add_argument("-s", "--summary", action="store_true", dest="summary", help=summary_desc)
    return parser.parse_args()


if __name__ == '__main__':
    args = args()

    logger = None

    COMMAND_LINE = True

    if COMMAND_LINE:
        config = VConfigInterface(use_default=True, use_unformatted=False)

        # Display specific test cases and steps
        if args.testcase:
            m = re.match("^(\d+|Tc\w*)(:(\d+))*$", args.testcase)
            if m.group(1):
                if m.group(1).isdigit():
                    config.display_test_case(number=int(m.group(1)))
                else:
                    config.display_test_case(name=m.group(1))
            if m.group(3) and m.group(3).isdigit():
                config.display_step(number=int(m.group(3)))

        if args.format_api:
            config.format_api()

        if args.summary:
            config.display_summary()

        vl_console_output = VFormatter()
        try:
            with open(args.read_path, "r") as logfile:
                logger = LollygagLogger(logfile, vl_console_output)
                logger.run()
        except KeyboardInterrupt:
            logger.kill()
            print "Keyboard Interrupt: Exiting Logger"
            exit(0)

    else:
        path = "/home/nathaniel/vl_artifacts/testing/general_only.log"

        config = VConfigInterface(use_default=True, use_unformatted=False)
        # config.display_test_case(number=0)
        # config.display_step(number=1)
        # config.format_api()

        DISPLAY_SUMMARY = True

        if DISPLAY_SUMMARY:
            config.display_summary()
        vl_console_output = VFormatter()
        try:
            with open(path, "r") as logfile:
                logger = LollygagLogger(logfile, vl_console_output)
                logger.run()
        except KeyboardInterrupt:
            logger.kill()
            print "Keyboard Interrupt: Exiting Logger"
            exit(0)
