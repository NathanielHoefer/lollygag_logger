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

import subprocess
import sys
import re
import argparse
from vl_config_file import *
from lollygag_logger import LogLine, LogFormatter, LollygagLogger
import helpers
import requests
from requests import auth

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

# Types of logs found during vl execution
TYPE_DEBUG = "DEBUG"
TYPE_INFO = "INFO"
TYPE_WARNING = "WARNING"
TYPE_ERROR = "ERROR"
TYPE_STEP = "STEP"
TYPE_TITLE = "TITLE"
TYPE_OTHER = "OTHER"




class ValenceLogLine(LogLine):
    """Stores log line into its various fields per the vl logging.

    Lines with all fields matching with the exception of the details token missing will still be
    considered in standard format. If any other field doesn't match, all of the fields are returned
    to normal, and the type is considered OTHER with the original line being retained.

    STEP and TITLE types are unique in that the line is stored in the details

    :cvar list LOG_LEVELS: The unique log levels specified by Valence
    :cvar list FIELDS: The unique sections found within a Valence log in standard format
    :cvar int TOKEN_COUNT: The number of fields
    """

    LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]
    FIELDS = ["date", "time", "type", "source", "thread", "details"]
    VALENCE_TOKEN_COUNT = len(FIELDS)
    AT2_TOKEN_COUNT = VALENCE_TOKEN_COUNT - 1

    def __init__(self, original_line=""):
        super(ValenceLogLine, self).__init__(original_line)
        self._default_vals()
        self._tokenize_line(original_line)

    def __str__(self):
        if self.standard_format:
            return " ".join([getattr(self, field)
                             for field in self.FIELDS if getattr(self, field) != ""])
        else:
            return self.original_line

    def _default_vals(self):
        """Set all field to default values."""
        self.date = ""
        self.time = ""
        self.type = "OTHER"
        self.source = ""
        self.thread = ""
        self.details = ""
        self.standard_format = False
        self.at2_log = False

    def _tokenize_line(self, input_str):
        """Determines if the log line is in standard vl logging format based on regular expressions.

        :param str input_str: The unformatted log line to be parsed.
        :return:
        """

        # Check to see if line is a STEP identified by a row of '-' or a TITLE identified by a row of '='
        input_str = input_str.strip()
        if re.match("^={5,}$", input_str):
            self.type = "TITLE"
            return
        if re.match("^-{5,}$", input_str):
            self.type = "STEP"
            return

        # Identifies if the log is int AT2 standard format based on the format of the time stamp. AT2
        # logs don't include the thread field, so determine token count if in AT2 format.
        current_token_count = 0
        if re.search("\d{2}:\d{2}:\d{2}\,\d{3}", input_str):
            self.at2_log = True
            current_token_count = self.AT2_TOKEN_COUNT
        else:
            current_token_count = self.VALENCE_TOKEN_COUNT

        # Check to see if there are the expected number of tokens in the line. If not, then mark as a
        # non-standard vl format, and return.
        split = input_str.split(" ", current_token_count - 1)
        if not (current_token_count - 1 <= len(split) <= current_token_count):
            return


        # Assign token to proper field if format matches correctly
        self.date = split[0] if re.match("^\d{4}\-\d{2}\-\d{2}$", split[0]) else ""

        # Check to see if logs are in valence format or AT2 format based on time
        if re.match("^\d{2}:\d{2}:\d{2}\.\d{6}$", split[1]):
            self.time = split[1]
        elif re.match("^\d{2}:\d{2}:\d{2}\,\d{3}$", split[1]):
            self.time = split[1]
        else:
            self.time = ""
        if split[2] in self.LOG_LEVELS:
            self.type = split[2]
        self.source = split[3] if re.match("^\[.*:.*\]$", split[3]) else ""
        if self.at2_log:  # Special case to check if logs are being read from AT2 based on time stamp
            self.details = split[4] if len(split) == self.AT2_TOKEN_COUNT else ""
        else:
            self.thread = split[4] if re.match("^\[.*:.*\]$", split[4]) else ""
            self.details = split[5] if len(split) == self.VALENCE_TOKEN_COUNT else ""

        # If any of the fields are empty with the exception of details, change type to OTHER and move all
        # line data to the details field.
        for field in self.FIELDS:
            if self.at2_log:
                if (field is not "details" and field is not "thread")\
                        and getattr(self, field) is "":
                    self._default_vals()
                    return
            else:
                if field is not "details" and getattr(self, field) is "":
                    self._default_vals()
                    return
        self.standard_format = True


class ValenceHeader(LogLine):
    """Stores the Valence header and its individual tokens.

    A header is either a title, identified by '=', or a step, identified by '-'. Looks for a
    colon-separated header for parsing the line, otherwise the empty values will be used for all but the
    original line member variable.

    :ivar str original_line: The line as it was entered
    :ivar str type: Either 'title' or 'step'
    :ivar bool suite: True if header is a title and describes a suite specifically, otherwise False
    :ivar str test_name: Name of the test case or suite following the 'Ts' or 'Tc' format.
    :ivar str test_info: Information prior to the colon
    :ivar str test_instruction: Information after the colon
    :ivar int test_number: Step or test case number if there is one.
    """

    def __init__(self, original_line="", type="", max_len=105):
        super(ValenceHeader, self).__init__(original_line)
        self.type = type
        self.max_len = max_len
        self._default_vals()
        self._tokenize_line(original_line)

    def __str__(self):
        border = "="*self.max_len if self.type == "title" else "-"*self.max_len
        return "\n".join([border, self.original_line, border])

    def _default_vals(self):
        """Set all field to default values."""
        self.suite = False
        self.test_name = ""
        self.test_info = ""
        self.test_instruction = ""
        self.test_number = 0

    def _tokenize_line(self, input_str):
        """Splits the input into the various tokens based on whether the header is a title or a step.

        :param str input_str: Log line found in a valence header to be tokenized.
        """

        # Don't try to parse if header not in test case or suite
        split = input_str.split(":")
        if len(split) <= 1:
            return

        self.test_info = split[0].strip() if len(split) == 2 else ""
        self.test_instruction = split[1].strip() if len(split) == 2 else ""

        if self.type == "title":
            self.suite = True if self.test_info == "Test Suite" else False
            if self.suite:
                self.test_name = re.search("Ts\w*", self.original_line).group()
            else:
                self.test_name = re.search("Tc\w*", self.original_line).group()
                self.test_number = int(re.search("\d+", self.test_info).group())
        elif self.type == "step":
            self.test_name = re.search("Tc\w*", self.original_line).group()
            self.test_number = int(re.search("\d+", self.test_info).group())
        else:
            self._default_vals()
            return


class ValenceConsoleOutput(LogFormatter):
    """Class containing log line format functions.

    :ivar log_line_cls: the LogLine class used to parse the unformatted log lines
    :ivar format_config: the configparser that contains all of the user options
    :ivar find_str: String to highlight if contained in line.
    :ivar list_step: The step or test case to be printed. For test case, match 'Test Case #'. If
        specifying step, list full name out as seen in logs. If empty, all logs will be printed.
    :ivar save_file: File to save the formatted logs to. If empty, logs won't be saved.
    """

    log_queue = []

    def __init__(self, log_line_cls, format_config, find_str="", list_step="", save_file=""):
        self.log_line_cls = log_line_cls
        self.format_config = format_config
        self.log_line = None
        self.find_str = find_str
        self.list_step = list_step
        self.save_file = save_file

        # Format config sections stored individually as dicts
        self.sect_display_log_types = self.format_config[DISPLAY_LOG_TYPES_SECT]
        self.sect_display_fields = self.format_config[DISPLAY_FIELDS_SECT]
        self.sect_condense_fields = self.format_config[CONDENSE_FIELDS_SECT]
        self.sect_collapse_structs = self.format_config[COLLAPSE_STRUCTS_SECT]
        self.sect_lengths = self.format_config[LENGTHS_SECT]

        # Variables needed for titles and steps
        self.waiting_for_title = False
        self.waiting_for_step = False

    def format(self, unformatted_log_line):
        """Prints the formatted log line to the console based on the format config file options."""

        # Check to see if line is empty, and create log line object to parse the line
        if unformatted_log_line == "\n":
            print ""
            return
        line = unformatted_log_line.strip("\n\\n")
        if not line:
            return
        self.log_line = self.log_line_cls(line)

        # Skip line if type is marked to not display
        log_type = self.log_line.type.strip().lower()
        if not helpers.str_to_bool(self.sect_display_log_types[log_type]):
            return

        # Remove and condense fields in standard logs per format config file
        if self.log_line.standard_format:
            self._remove_fields()
            self._condense_fields()

        # Grab max line length from format config file or from console width
        formatted_line = str(self.log_line)

        # Condense entire log line if beyond max length
        print helpers.condense(formatted_line, self._calc_max_len())

    def _remove_fields(self):
        """Remove field from line if marked not to display."""
        for field, val in self.sect_display_fields.items():
            if not helpers.str_to_bool(val):
                setattr(self.log_line, field, "")

    def _condense_fields(self):
        """Condense and collapse individual line fields to the specified length in format config."""
        collapse_dict = helpers.str_to_bool(self.sect_collapse_structs["dict"])
        collapse_list = helpers.str_to_bool(self.sect_collapse_structs["list"])
        collapse_len = int(self.format_config[LENGTHS_SECT]["collapsed_struct_len"])
        condense_len = int(self.sect_lengths["condensed_field_len"])

        for field, val in self.sect_condense_fields.items():
            if helpers.str_to_bool(val):
                current_field_str = getattr(self.log_line, field)
                current_field_str = helpers.condense_field(current_field_str, condense_len,
                                                           collapse_dict, collapse_list, collapse_len)
                setattr(self.log_line, field, current_field_str)

    def _calc_max_len(self):
        """Returns max length of the logline to be printed based on the format config file."""
        if helpers.str_to_bool(self.sect_lengths["use_console_len"]) and sys.stdin.isatty():
            _, console_width = os.popen('stty size', 'r').read().split()
            return int(console_width)
        else:
            return int(self.sect_lengths["max_line_len"])


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
        vl_console_output = ValenceConsoleOutput(ValenceLogLine, config,
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
            arg_path = args.vl_path
            if arg_path[0] == "/" or arg_path[0] == "~":
                file_path = arg_path
            else:
                file_path = os.getcwd() + "/" + arg_path
            with open(file_path, "r") as logfile:
                logger = LollygagLogger(logfile, vl_console_output)
                logger.run()
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
