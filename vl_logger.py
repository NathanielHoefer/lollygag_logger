#!/usr/bin/env python

"""
=========================================================================================================
Valence Lollygag Logger
=========================================================================================================
by Nathaniel Hoefer
Version: 1.0
Last Updated: 12/30/2017

This is a tool specifically designed for formatting Valence logs in a way that makes them more legible
and allows for customized viewing. It is completely unobtrusive in the sense that it doesn't directly
affect any of the artifacts or testing that is being produced. This is accomplished by capturing each
log line as it is being printed to the console or read, and runs it through the formatter. Because of
this line-by-line formatting, a number of sources can be read from as explained below. When reading
from a file or an AT2 Task Step Instance, you may also write the output to a file, list a specific
test case step, as well as print and highlight logs with a specified string.

Read from the 'vl run' command
    This can be accomplished by running this tool in place of the 'vl run' command - listing the suite
    path to begin executing the suite. To stop the test, simply use the keyboard interrupt Ctrl-C as you
    would normally.

    Ex: python vl_logger path.to.suite

    Note: the write, find, and list features are not currently available when running a test.

Read from a log file
    If you would like to format any artifact log files, simply enter the log path and mark the '-r'
    flag to print the file to the screen.

    Ex: python vl_logger ~/test.log -r

Pull from an AT2 Task Step Instance
    You may also format an AT2 Task Step Instance by its ID then mark the '-at2' flag. The username
    and password will need to be manually entered into the .ini file. While not yet able to continuously
    update the logs if the test is currently running, it can still format the current state of the test.

    Ex: python vl_logger 652271542 -at2

The settings are accessed through the .vl_logger.ini file which is created on your first run of the
logger. By default, it is stored in your home directory, but you may specify another directory by
using the '-ini' argument. Currently, the customization is as follows found within the .ini file:
 - hide/view specific log types
 - hide/view
 - specific log fields
 - condense fields
 - condense logs to a specified length or the console width
 - collapse dictionaries and lists
 - color the log type if displayed

Other Features
 - Write:
    Instead of printing the formatted logs to the console, they will be written to the specified
    file including ACSII color additions.

    Ex: python vl_logger ~/test.log -r -w ~/test_formatted.log

 - List:
    Only prints the logs found within a specific test header. This includes anything that is found within
    that header. For example, if you wanted to print the logs found within 'Test Case 0: Starting Test
    ...' then all of the associated steps will also be printed. Just keep in mind that the header
    description (the part in between all of the '-' or '=') needs to be copied exactly.

    Ex: python vl_logger ~/test.log -r -l 'Test Case 0: Starting Test of Test1'
    Ex: python vl_logger ~/test.log -r -l 'Starting Step 0 for Test1: Doing Stuff'
    Ex: python vl_logger ~/test.log -r -l 'Test Suite: Starting Setup of Suite1'

 - Find:
    By specifying a string to look for, only logs containing the specified string will be printed. If
    the string is visible after being formatted, then it will also be highlighted. One thing to note
    is that only the logs that are already set to be shown will be evaluated. As an example,
    if debug logs are set to be hidden, they will not be displayed even if they contain the specified
    search string. However, if the the field containing the string is hidden but the rest of the log line
    is set to print, then the log line will be printed - indicating a match.

    Ex: python vl_logger ~/test.log -r -f '2017-10-30'

=========================================================================================================
"""

import argparse
import subprocess
import requests
from requests import auth

from bin.lollygag_logger import LollygagLogger
from bin.vl_console_module.vl_config_file import *
from bin.vl_console_module import ValenceConsoleFormatter as Formatter
from bin.vl_console_module import ValenceLogLine as LogLine


def args():
    # Descriptions for arg parse
    program = "Valence Lollygag Logger"
    description = "A non-obtrusive tool that captures Valence Logs being printed to the screen and " \
                  "formats them based on custom user preferences to assist in debugging. This " \
                  "tool can format logs from the 'vl run' command, stored log file, or an at2 task " \
                  "step instance. When formatting logs from the 'vl run' command, the tool will " \
                  "execute the command directly and the output will be in real time."
    vl_desc = "Source of the logs. Without -r or -at2 flags, this tool will attempt to execute the " \
              "'vl run' command using the vl_source parameter as the suite path. To cancel the " \
              "'vl run' execution, pass a keyboard interrupt and the test will be cancelled. Refer " \
              "to -r or -at2 descriptions for additional info."
    file_desc = "Flag indicating to read from log file specified in the vl_source parameter."
    at2_desc = "Flag indicating to fetch AT2 Task Instance logs from the specified AT2 Task Step " \
               "Instance ID specified in the vl_source parameter."
    find_desc = "Highlight specified string found in the logs. Not functional when running the 'vl " \
                "run' command."
    list_desc = "List specified test case or step. Be sure to copy the entire test case or step " \
                "description --excluding the borders and 'Expect: Pass'. Also remember to use " \
                "quotation marks. Not functional when running the 'vl run' command."
    write_desc = "Write log output to specified file. Not functional when running the 'vl run' command."
    ini_desc = "Directory to look for format .ini file."

    # Argument setup and parsing
    parser = argparse.ArgumentParser(prog=program, description=description)
    group = parser.add_mutually_exclusive_group()
    parser.add_argument("vl_source", help=vl_desc)
    group.add_argument("-r", "--read", action="store_true", help=file_desc)
    group.add_argument("-at2", action="store_true", help=at2_desc)
    parser.add_argument("-w", "--write", action="store", dest="write_path", help=write_desc)
    parser.add_argument("-f", "--find", action="store", dest="find_str", help=find_desc)
    parser.add_argument("-l", "--list", action="store", dest="list_step", help=list_desc)
    parser.add_argument("-ini", action="store", dest="ini_path", help=ini_desc)
    return parser.parse_args()


if __name__ == '__main__':
    args = args()

    # Validate that args exist and execute printing the logs
    if args.vl_source:
        config = create_config_file(args.ini_path)
        if args.write_path:
            with open(args.write_path, "w") as write_file:
                write_file.write("")

        logger = None

        # 'vl run' Case
        if not args.read and not args.at2:
            # Currently not implementing find_str, list_step, or write_path
            vl_console_output = Formatter(log_line_cls=LogLine,
                                          format_config=config,
                                          ini_filepath=args.ini_path)
            proc = subprocess.Popen(["python", "vl", "run", args.vl_source], stdout=subprocess.PIPE,
                                    bufsize=1, universal_newlines=False)
            try:
                logger = LollygagLogger(iter(proc.stdout.readline, b''), vl_console_output)
                logger.run()
                proc.stdout.close()
                proc.wait()
            except KeyboardInterrupt:
                proc.kill()
                logger.kill()
                print "Keyboard Interrupt: Exiting Logger"
                exit(0)

        # Reading from a file
        elif args.read:
            vl_console_output = Formatter(log_line_cls=LogLine,
                                          format_config=config,
                                          ini_filepath=args.ini_path,
                                          find_str=args.find_str,
                                          list_step=args.list_step,
                                          write_path=args.write_path)
            try:
                arg_path = args.vl_source
                with open(arg_path, "r") as logfile:
                    logger = LollygagLogger(logfile, vl_console_output)
                    logger.run()
            except KeyboardInterrupt:
                logger.kill()
                print "Keyboard Interrupt: Exiting Logger"
                exit(0)

        # Pulling from AT2 Task Step Instance
        elif args.at2:
            vl_console_output = Formatter(log_line_cls=LogLine,
                                          format_config=config,
                                          ini_filepath=args.ini_path,
                                          find_str=args.find_str,
                                          list_step=args.list_step,
                                          write_path=args.write_path)
            AT2_USER = config[AT2_TASKINSTANCE_CREDENTIALS]["username"]
            AT2_PASS = config[AT2_TASKINSTANCE_CREDENTIALS]["password"]

            if not AT2_USER or not AT2_PASS:
                print "Please enter username and password in " \
                      "the {0} file.".format(FORMAT_CONFIG_FILE_NAME)
                exit(0)

            STEP_ID = args.vl_source
            AT2_STREAM_URL = 'https://autotest2.solidfire.net/stream/stdout/{}/'.format(STEP_ID)
            AUTH = auth.HTTPBasicAuth(AT2_USER, AT2_PASS)
            session = requests.Session()
            session.auth = AUTH

            resp = requests.Response()  # dummy for now

            try:
                resp = session.get(AT2_STREAM_URL, stream=True)
                logger = LollygagLogger(resp.iter_lines(), vl_console_output)
                logger.run()
            except BaseException:  # pylint: disable=broad-except
                raise
            finally:
                resp.close()
            print "AT2 option selected. TaskID: {0}.".format(args.vl_source)

        # Invalid arguments
        else:
            print "Please pass valid arguments"
            exit(0)

        if args.write_path:
            print "Write to {0} Complete".format(args.write_path)
