#!/usr/bin/env python

"""Formats the logs to be output to the screen."""

import argparse
import os
import re

from bin.lollygag_logger import LollygagLogger
from bin.vconfiginterface import VConfigInterface
from bin.vformatter import VFormatter

FILE_PATTERN = "^(?:\w|-|/|\.)+\.log$"
AT2_PATTERN = "^\d+$"
SUITE_PATTERN = "^(?:\w|-|/|\.)*Ts(?:\w|-)+$"


def args():
    """Args for vlogger."""

    # Descriptions for arg parse
    program = "Valence Lollygag Logger"
    description = "A non-obtrusive tool that captures Valence Logs being printed to the screen and " \
                  "formats them based on custom user preferences to assist in debugging. This " \
                  "tool can format logs from the 'vl run' command, stored log file, or an at2 task " \
                  "step instance. When formatting logs from the 'vl run' command, the tool will " \
                  "execute the command directly and the output will be in real time."
    log_source = "Log File (*.log) | AT2 Task Inst. Step ID | Suite Path (path.to.suite.Ts*)"
    testcase_desc = "(tc_name|tc_number)[:step number] - List specified test case and optionally step"
    format_api_desc = "Display API calls"
    save_desc = "Store formatted logs to a file at a default location. " \
                "The storage location can be specified in the .ini file, but " \
                "defaults to ~/vl_artifacts."
    epilog = "The configuration file (.ini) is located at ~/.vlogger.ini. " \
             "When executing a suite, only options specified in the .ini file are considered."

    # Argument setup and parsing
    parser = argparse.ArgumentParser(prog=program, description=description, epilog=epilog)
    parser.add_argument("log_source", nargs=1, help=log_source)
    parser.add_argument("-t", "--testcase", action="store", dest="testcase", help=testcase_desc)
    parser.add_argument("-a", "--api", action="store_true", dest="format_api", help=format_api_desc)
    parser.add_argument("-s", "--save", action="store_true", dest="save", help=save_desc)
    return parser.parse_args()


if __name__ == '__main__':

    # Variable Init ***********************************************************

    args = args()

    logger = None
    log_source = args.log_source[0]
    logfile = ""

    savedfile = re.match(FILE_PATTERN, log_source)
    at2_instance = re.match(AT2_PATTERN, log_source)
    suite = re.match(SUITE_PATTERN, log_source)

    # Log source **************************************************************
    # - Handle any log source specific operations

    if savedfile:
        logfile = log_source

    elif at2_instance:
        from plugins import at2_task
        logfile = at2_task.logs_from_at2(log_source)

    elif suite:
        from plugins import vl_run
        logfile = vl_run.execute_local_run(log_source)

    else:
        print "Invalid log source."
        exit(1)

    # Test Cases **************************************************************

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

    # Additional Configuration ************************************************

    config = VConfigInterface()

    if savedfile or at2_instance:
        is_at2 = config.is_at2_formatting(logfile)
        if is_at2:
            config.at2_format()

        if args.save:
            save_filename = "fmt_%s" % os.path.basename(logfile)
            save_filepath = os.path.join(os.path.dirname(logfile), save_filename)
            print "Saving formatted logs to %s..." % save_filepath
            open(save_filepath, 'w').close()
            word_count = sum(1 for line in open(logfile))
            config.save_file(save_filepath, word_count)

        if args.format_api:
            config.format_api()

    # Execute vlogger *********************************************************

    vl_console_output = VFormatter(config)
    try:
        if suite:
            logger = LollygagLogger(iter(logfile.stdout.readline, b''), vl_console_output)
            logger.run()
        else:
            with open(logfile, "r") as logfile:
                logger = LollygagLogger(logfile, vl_console_output)
                logger.run()
    except KeyboardInterrupt:
        logger.kill()
        print "Keyboard Interrupt: Exiting Logger"
        exit(0)
