#!/usr/bin/env python

"""
=========================================================================================================
Lollygag Logger
=========================================================================================================
by Nathaniel Hoefer
Contact: nathaniel.hoefer@netapp.com
Version: 0.5
Last Updated: 11/14/2017

This is the first iteration of a script to present a more legible output from the vl suite execution.

Currently, this is capable of reading from a log file by using the -f argument to specify a log file to
read from. This method will also generate a format config file during the initial run in the same
location as the log file. This format config file allows you - the user - to specify how you would like
the output to be formatted.

Another option is to run this script using the -vl argument, passing in the suite path just as though
you are running the "vl run suite.path.etc" command. You will still have to execute this from within the
same directory as if you were executing the command by itself. The big difference is this too generates
a format config file, that you can change at any point during your test to see future logs in the new
format. This format config file will be generated in your current working directory.

Script execution examples:
python lollygag_logger.py -f test.log
python lollygag_logger.py -vl suite.path.etc

If you experience any issues with this script (which there stands a good possibility) or you would like
suggest an improvement, you can reach me at my email listed above.


Improvements to implement:
 - Split reading from a file handle and formatting into two separate processes in a producer-consumer
 model.
 - Treat reading from file and executing vl process as both file handles to be passed into a single funct

=========================================================================================================
"""

# TODO - Update file description

import argparse
import subprocess

import requests
from requests import auth

from bin.lollygag_logger import LollygagLogger
from bin.vl_console_module.vl_config_file import *
from bin.vl_console_module import ValenceConsoleFormatter
from bin.vl_console_module import ValenceLogLine

# Descriptions for arg parse
PROGRAM = "Lollygag Logger"
DESCRIPTION = "This script will print out formatted logs from a log file or format the output of the " \
              "vl run command."
ARG_VL_DESC = "By default, the path to suite as in the vl_run command. Also used by -read and -at2 flags"
ARG_FILE_DESC = "Read from log file in vl_path."
ARG_AT2_DESC = "Fetch AT2 Task Instance logs from taskID in vl_path"
ARG_FIND_DESC = "Highlight specified string found in the logs."
ARG_LIST_DESC = "List specified test case or step. For test case, match 'Test Case #'. If" \
                "specifying step, list full name out as seen in logs."
ARG_SAVE_DESC = "Save log output to specified file."


if __name__ == '__main__':

    # Argument setup and parsing
    parser = argparse.ArgumentParser(prog=PROGRAM, description=DESCRIPTION)
    group = parser.add_mutually_exclusive_group()
    parser.add_argument("vl_path", help=ARG_VL_DESC)
    group.add_argument("-r", "--read", action="store_true", help=ARG_FILE_DESC)
    group.add_argument("-at2", action="store_true", help=ARG_AT2_DESC)
    parser.add_argument("-f", "--find", action="store", dest="find_str", help=ARG_FIND_DESC)
    parser.add_argument("-l", "--list", action="store", dest="list_step", help=ARG_LIST_DESC)
    parser.add_argument("-s", "--save", action="store", dest="save_path", help=ARG_SAVE_DESC)
    args = parser.parse_args()

    # Validate that args exist and execute printing the logs
    if args.vl_path:
        config = create_config_file()
        vl_console_output = ValenceConsoleFormatter(ValenceLogLine, config,
                                                    args.find_str, args.list_step, args.save_path)
        if not args.read and not args.at2:
            # Begin vl run subprocess
            proc = subprocess.Popen(["vl", "run", args.vl_path], stdout=subprocess.PIPE,
                                    bufsize=1, universal_newlines=False)
            try:
                logger = LollygagLogger(iter(proc.stdout.readline, b''), vl_console_output)
                logger.run()
                proc.stdout.close()
                proc.wait()
            except KeyboardInterrupt:
                proc.kill()
        elif args.read:
            try:
                arg_path = args.vl_path
                if arg_path[0] == "/" or arg_path[0] == "~":
                    file_path = arg_path
                else:
                    file_path = os.getcwd() + "/" + arg_path
                with open(file_path, "r") as logfile:
                    logger = LollygagLogger(logfile, vl_console_output)
                    logger.run()
            except KeyboardInterrupt:
                print "Keyboard Interrupt: Exiting"
                exit(0)
        elif args.at2:

            AT2_USER = config[AT2_TASKINSTANCE_CREDENTIALS]["username"]
            AT2_PASS = config[AT2_TASKINSTANCE_CREDENTIALS]["password"]

            if not AT2_USER or not AT2_PASS:
                print "Please enter username and password in " \
                      "the {0} file.".format(FORMAT_CONFIG_FILE_NAME)
                exit(0)

            STEP_ID = args.vl_path
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
            print "AT2 option selected. TaskID: {0}.".format(args.vl_path)
        else:
            print "Please pass valid arguments"
