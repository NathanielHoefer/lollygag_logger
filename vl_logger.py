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
from bin.vl_console_module import ValenceConsoleFormatter as Formatter
from bin.vl_console_module import ValenceLogLine as LogLine


def args():
    # Descriptions for arg parse
    program = "Valence Lollygag Logger"
    description = "Formats Valence Logs based on custom user preferences to assist in debugging. This " \
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
    find_desc = "Highlight specified string found in the logs."
    list_desc = "List specified test case or step. For test case, match 'Test Case #'. If specifying " \
                "step, list full name out as seen in logs."
    write_desc = "Write log output to specified file."

    # Argument setup and parsing
    parser = argparse.ArgumentParser(prog=program, description=description)
    group = parser.add_mutually_exclusive_group()
    parser.add_argument("vl_source", help=vl_desc)
    group.add_argument("-r", "--read", action="store_true", help=file_desc)
    group.add_argument("-at2", action="store_true", help=at2_desc)
    parser.add_argument("-f", "--find", action="store", dest="find_str", help=find_desc)
    parser.add_argument("-l", "--list", action="store", dest="list_step", help=list_desc)
    parser.add_argument("-w", "--write", action="store", dest="write_path", help=write_desc)
    return parser.parse_args()


if __name__ == '__main__':
    args = args()

    # Validate that args exist and execute printing the logs
    if args.vl_source:
        config = create_config_file()
        vl_console_output = Formatter(LogLine, config, args.find_str, args.list_step, args.write_path)
        if not args.read and not args.at2:
            # Begin vl run subprocess
            proc = subprocess.Popen(["vl", "run", args.vl_source], stdout=subprocess.PIPE,
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
                arg_path = args.vl_source
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
        else:
            print "Please pass valid arguments"
