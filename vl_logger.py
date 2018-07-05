#!/usr/bin/env python

"""
Formats the logs to be output to the screen.
"""

import argparse

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

    # Argument setup and parsing
    parser = argparse.ArgumentParser(prog=program, description=description)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-r", "--read", action="store", dest="read_path", help=read_desc)
    return parser.parse_args()


if __name__ == '__main__':
    args = args()

    logger = None

    config = VConfigInterface(use_unformatted=True)
    vl_console_output = VFormatter()
    try:
        with open(args.read_path, "r") as logfile:
            logger = LollygagLogger(logfile, vl_console_output)
            logger.run()
    except KeyboardInterrupt:
        logger.kill()
        print "Keyboard Interrupt: Exiting Logger"
        exit(0)

    # logger = None
    # path = "/home/nathaniel/vl_artifacts/TsDriveEncryptionPersistenceAndAccessibility-2018-02-07T16.14.18/test.log"
    #
    # vl_console_output = VFormatter()
    # try:
    #     with open(path, "r") as logfile:
    #         logger = LollygagLogger(logfile, vl_console_output)
    #         logger.run()
    # except KeyboardInterrupt:
    #     logger.kill()
    #     print "Keyboard Interrupt: Exiting Logger"
    #     exit(0)
