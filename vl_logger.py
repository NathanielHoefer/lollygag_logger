#!/usr/bin/env python

"""
=========================================================================================================
Valence Lollygag Logger
=========================================================================================================
by Nathaniel Hoefer
Version: 1.0
Last Updated: 12/30/2017

This is a tool specifically designed for formatting Valence logs for better legibility and debugging by
allowing customized formatting. It is completely unobtrusive in the sense that it doesn't directly affect
any of the artifacts or testing that is being produced. This is accomplished by capturing each log line a
s it is being printed to the console or read, and runs it through the formatter - affecting only the
screen output of the logs, leaving all other aspects such as files intact. Because of this line-by-line
formatting, a number of sources can be read from as explained below.

Usage
    To begin a test and format the printed logs, use the `-run` argument followed by the suite path. This
    tool utilizes the `vl run` command, so it must be installed and you must execute it from the same
    directory as if running that command instead. To stop the test, issue a keyboard interupt Ctrl-C just
    as you would normally.

    Ex: python vl_logger.py -run <path.to.suite>

    To format and print logs from a file**, use the `-r` argument followed by the file path.

    Ex: python vl_logger.py -r <file path>

    To format and print logs from a AT2 Task Step Instance, use the `-at2` argument followed by the task
    instance step ID.

    Ex: python vl_logger.py -at2 <step id>

    Other Features
    The following features are available when using the `-r` or `-at2` arguments:
    Write output to file:** Instead of printing the formatted logs to the console, they will be written
    to the specified file including ACSII color additions with the `-w` argument.

    Ex: python vl_logger.py -at2 <step id> -w <file path>

    List specific suite/test case/step: To only print the logs found within a specific test header, us
    the `-l` argument. This includes anything that is found within that header. For example, if you
    wanted to print the logs found within 'Test Case 0: Starting Test...' then all of the associated
    steps will also be printed. Just keep in mind that the header description (the part in between all of
    the '-' or '=') needs to be copied exactly.

    Ex: python vl_logger.py -r <file path> -l "<entire header description>"

    Find logs containing specific string: To specify a string to look for, use the `-f` argument followed
    by the desired string, then only logs containing the specified string will be printed. If the string
    is visible after being formatted, then it will also be highlighted.

    Ex: python vl_logger.py -at2 <step id> -f "<string>"

    Note: Only the logs that are already set to be shown will be evaluated. As an example, if debug logs
    are set to be hidden, they will not be displayed even if they contain the specified search string.
    However, if the the field containing the string is hidden but the rest of the log line is set to
    print, then the log line will be printed - indicating a match.


Format Config File
    The settings are accessed through the `.vl_logger.ini` file which is created on your first run of the
    logger. Currently, the customization is as follows found within the .ini file:
     - hide/view specific log types
     - hide/view
     - specific log fields
     - condense fields
     - condense logs to a specified length or the console width
     - collapse dictionaries and lists
     - color the log type if displayed

    By default, it is stored in your home directory, but you may specify another directory by using the
    `-ini` argument. If using the `-run` option,the .ini file can be updated at any point during the
    current test, and will reflect any changes on future logs. For example, if you decide that you wish
    to see debug logs, simply change the option within the format_config file and save it, and any
    further logs will include the debug logs.
    Note: The options listed are only what is currently offered. It will be expanded in future releases.

Additional Info
    To execute this tool without the initial `python` command from any directory, execute the following
    commands.

    chmod u+x vl_logger.py
    ln -s <explicit path to repo>/lollygag_logger/vl_logger.py ~/bin/vl_logger

    Then you may execute the tool as follows:

    Ex: vl_logger -at2 <step id> -f "<string>"

    Do not use PDB when using this script, it will not output correctly.
    If you find any bugs or have suggestions, feel free to contact me.

=========================================================================================================
"""

import argparse
import subprocess
import requests
from requests import auth
import sys

from bin.lollygag_logger import LollygagLogger
from bin.vl_console_module.vl_config_file import *
from bin.vl_console_module import ValenceConsoleFormatter as Formatter
from bin.vl_console_module import ValenceLogLine as LogLine

from valence.driver import main

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
    vl_desc = "This argument will attempt to execute the 'vl run' command so you should be in the " \
              "correct directory before executing. To cancel the 'vl run' execution, pass a keyboard " \
              "interrupt and the test will be cancelled."
    file_desc = "Read from log file specified."
    at2_desc = "Fetch AT2 Task Instance logs from the specified AT2 Task Step Instance ID."
    find_desc = "Highlight specified string found in the logs. Not functional when running the '-run' " \
                "command."
    list_desc = "List specified test case or step. Be sure to copy the entire test case or step " \
                "description --excluding the borders and 'Expect: Pass'. Not functional when running " \
                "the '-run' command."
    write_desc = "Write log output to specified file. Not functional when running the '-run' command."
    ini_desc = "Directory to look for 'vl_logger.ini' file."

    # Argument setup and parsing
    parser = argparse.ArgumentParser(prog=program, description=description)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-run", action="store", dest="suite_path", help=vl_desc)
    group.add_argument("-r", "--read", action="store", dest="read_path", help=file_desc)
    group.add_argument("-at2", action="store", dest="at2_id", help=at2_desc)
    parser.add_argument("-w", "--write", action="store", dest="write_path", help=write_desc)
    parser.add_argument("-f", "--find", action="store", dest="find_str", help=find_desc)
    parser.add_argument("-l", "--list", action="store", dest="list_step", help=list_desc)
    parser.add_argument("-ini", action="store", dest="ini_path", help=ini_desc)
    return parser.parse_args()


if __name__ == '__main__':
    args = args()

    # Validate that args exist and execute printing the logs
    config = create_config_file(args.ini_path)
    if args.write_path:
        with open(args.write_path, "w") as write_file:
            write_file.write("")

    logger = None

    # import os
    # if not os.isatty(0):
    #     config = create_config_file()
    #     vl_console_output = Formatter(log_line_cls=LogLine,
    #                                   format_config=config)
    #     try:
    #         logger = LollygagLogger(sys.stdin, vl_console_output)
    #         logger.run()
    #     except KeyboardInterrupt:
    #         logger.kill()
    #         print "Keyboard Interrupt: Exiting Logger"
    #         exit(0)
    #     exit(0)

    # 'vl run' Case
    if args.suite_path:

        # Currently not implementing find_str, list_step, or write_path
        vl_console_output = Formatter(log_line_cls=LogLine,
                                      format_config=config,
                                      ini_filepath=args.ini_path,
                                      find_str=args.find_str,
                                      list_step=args.list_step,
                                      write_path=args.write_path)

        proc = subprocess.Popen(["vl", "run", args.suite_path], stdout=subprocess.PIPE,
                                universal_newlines=False)

        # rpipe, wpipe = os.pipe()
        # pid = os.fork()
        #
        # if pid == 0:
        #     try:
        #         os.close(wpipe)
        #         rpipe.

        try:
            # main.run(args.suite_path)

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
    elif args.read_path:
        vl_console_output = Formatter(log_line_cls=LogLine,
                                      format_config=config,
                                      ini_filepath=args.ini_path,
                                      find_str=args.find_str,
                                      list_step=args.list_step,
                                      write_path=args.write_path)
        try:
            with open(args.read_path, "r") as logfile:
                logger = LollygagLogger(logfile, vl_console_output)
                logger.run()
        except KeyboardInterrupt:
            logger.kill()
            print "Keyboard Interrupt: Exiting Logger"
            exit(0)

    # Pulling from AT2 Task Step Instance
    elif args.at2_id:
        vl_console_output = Formatter(log_line_cls=LogLine,
                                      format_config=config,
                                      ini_filepath=args.ini_path,
                                      find_str=args.find_str,
                                      list_step=args.list_step,
                                      write_path=args.write_path)
        AT2_USER = config[AT2_TASKINSTANCE_CREDENTIALS]["username"]
        AT2_PASS = config[AT2_TASKINSTANCE_CREDENTIALS]["password"]
        AT2_URL = config[AT2_TASKINSTANCE_CREDENTIALS]["at2_url"]

        if not AT2_USER or not AT2_PASS or AT2_URL == "https://":
            print "Please enter username, password and at2 url in " \
                  "the {0} file.".format(FORMAT_CONFIG_FILE_NAME)
            exit(0)

        STEP_ID = args.at2_id
        AT2_STREAM_URL = '{0}/stream/stdout/{1}/'.format(AT2_URL, STEP_ID)
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
        print "AT2 option selected. TaskID: {0}.".format(args.at2_id)

    # Invalid arguments
    else:
        print "Please pass valid arguments"
        exit(0)

    if args.write_path:
        print "Write to {0} Complete".format(args.write_path)
