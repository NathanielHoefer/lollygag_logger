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
import datetime
from vl_config_file import *
from lollygag_logger import LogLine, LogFormatter, LollygagLogger
import helpers
from enums import ColorType
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
            return " ".join([field for field in self._list_fields_as_str() if field != ""])
        else:
            return self.original_line

    def color_type(self):
        """Returns the log line with the log type surrounded by an ANSI escape color sequence."""
        if self.standard_format:
            fields = self._list_fields_as_str()
            fields[2] = ColorType.color_by_type(fields[2].lower(), fields[2])
            fields = [x for x in fields if x != ""]
        else:
            fields = [ColorType.color_by_type(self.type.lower(), self.original_line)]
        return " ".join(fields)

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
        # each with a minimum of 30 chars
        input_str = input_str.strip()
        if re.match("^={30,}$", input_str):
            self.type = "TITLE"
            return
        if re.match("^-{30,}$", input_str):
            self.type = "STEP"
            return

        # Identifies if the log is int AT2 standard format based on the format of the time stamp. AT2
        # logs don't include the thread field, so determine token count if in AT2 format.
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
        self._str_to_date()

        # Check to see if logs are in valence format or AT2 format based on time
        if re.match("^\d{2}:\d{2}:\d{2}\.\d{6}$", split[1]) \
                or re.match("^\d{2}:\d{2}:\d{2}\,\d{3}$", split[1]):
            self.time = split[1]
            self._str_to_time()
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

    def _list_fields_as_str(self):
        str_fields_list = [getattr(self, field) for field in self.FIELDS]
        str_fields_list[0] = self._date_to_str()
        str_fields_list[1] = self._time_to_str()
        return str_fields_list

    def _date_to_str(self):
        if self.date:
            return self.date.strftime("%Y-%m-%d")
        else:
            return ""

    def _time_to_str(self):
        if not self.time:
            return ""

        if self.at2_log:
            time = self.time.strftime("%H:%M:%S,%f")[:-3]
        else:
            time = self.time.strftime("%H:%M:%S.%f")
        return time

    def _str_to_date(self):
        if not self.date:
            return
        date = re.split("-", self.date)
        self.date = datetime.date(int(date[0]), int(date[1]), int(date[2]))

    def _str_to_time(self):
        if not self.time:
            return
        if self.at2_log:
            self.time = datetime.datetime.strptime(self.time, "%H:%M:%S,%f")
        else:
            self.time = datetime.datetime.strptime(self.time, "%H:%M:%S.%f")

        # time = re.split(":|;|\.|\,", self.time)
        # self.time = datetime.time(int(time[0]), int(time[1]), int(time[2]), int(time[3].ljust(6, "0")))


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
        if self.original_line == "Expect: Pass":
            return ""
        else:
            return "\n".join([border, self.original_line, border, ""])

    def _default_vals(self):
        """Set all field to default values."""
        self.suite = False
        self.test_name = ""
        self.test_info = ""
        self.test_instruction = ""
        self.test_number = 0
        self.start_time = None
        self.end_time = None

    def _tokenize_line(self, input_str):
        """Splits the input into the various tokens based on whether the header is a title or a step.

        :param str input_str: Log line found in a valence header to be tokenized.
        """

        # Don't try to parse if header not in test case or suite
        split = input_str.split(":", 1)
        if len(split) <= 1 or input_str == "Expect: Pass":
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

    def __init__(self, log_line_cls, format_config, format_config_filepath="",
                 find_str="", list_step="", save_file=""):
        self.log_line_cls = log_line_cls
        self.format_config = format_config
        self.format_config_filepath = format_config_filepath if format_config_filepath \
            else DEFAULT_CONFIG_PATH
        self.log_line = None
        self.find_str = find_str
        self.list_step = list_step
        self.save_file = save_file
        self.duplicate_blank_line = False

        # Format config sections stored individually as dicts
        self._read_vals_from_config_file()
        self.format_config_mod_time = os.path.getmtime(self.format_config_filepath)

        # Variables needed for titles and steps
        self.waiting_for_header = {"title": False, "step": False}
        self.previous_header = None
        self.finish_times = {}
        self.executed_suites = []
        self.current_suite_name = ""
        self.current_suite_index = -1
        self.current_test_case = ""
        self.current_test_case_index = -1
        self.prev_header_was_step = False
        self.current_step_index = -1
        self.last_log_time = None

    def format(self, unformatted_log_line):
        """Prints the formatted log line to the console based on the format config file options."""

        # Check to see if line is empty, and create log line object to parse the line
        if unformatted_log_line == "\n":
            if not self.duplicate_blank_line:
                self.duplicate_blank_line = True
                print ""
            return
        line = unformatted_log_line.strip("\n\\n")
        if not line:
            return
        self.log_line = self.log_line_cls(line)

        # Store last log time
        if self.log_line.standard_format and self.log_line.time:
            self.last_log_time = self.log_line.time

        # Update format config values if file has been updated
        current_config_mod_time = os.path.getmtime(self.format_config_filepath)
        if current_config_mod_time > self.format_config_mod_time:
            self._read_vals_from_config_file()
            self.format_config_mod_time = current_config_mod_time

        print_in_color = helpers.str_to_bool(self.format_config[COLORS]["use_colors"])

        # Construct header object and print
        log_type = self.log_line.type.strip().lower()
        formatted_line = self._combine_header_logs(log_type)
        if formatted_line:
            self._store_header(formatted_line)
            log_output = str(formatted_line)
            if log_output:
                print ColorType.color_by_type(formatted_line.type, log_output) \
                    if print_in_color else log_output

            if formatted_line.original_line == "Final Report":
                # TODO - Fix ellapsed time issues 12/23
                helpers.print_variable_list(self.executed_suites, self._print_header_report)
            return

        # Don't print header border
        elif log_type == "step" or log_type == "title" or any(self.waiting_for_header.values()):
            return

        # Skip line if type is marked to not display
        if not helpers.str_to_bool(self.sect_display_log_types[log_type]):
            return

        # Remove and condense fields in standard logs per format config file
        if self.log_line.standard_format:
            self._remove_fields()
            self._condense_fields()

        # Add color to the type field
        if helpers.str_to_bool(self.format_config[COLORS]["use_colors"]):
            formatted_line = self.log_line.color_type()
        else:
            formatted_line = str(self.log_line)

        # Condense entire log line if beyond max length
        log_output = helpers.condense(formatted_line, self._calc_max_len())
        # TODO - Resolve color condensing issue 12/22
        if log_output.strip("\n\\n"):
            print log_output
        elif not self.duplicate_blank_line:
            self.duplicate_blank_line = True
            print log_output
        self.duplicate_blank_line = False

    def _combine_header_logs(self, log_type):
        formatted_header = None
        for header_type, is_waiting in self.waiting_for_header.items():
            if log_type == header_type and not is_waiting:
                self.waiting_for_header[header_type] = True
            elif log_type == "other" and is_waiting:
                formatted_header = ValenceHeader(self.log_line.original_line, header_type,
                                                 self._calc_max_len())
                break
            elif log_type == header_type and is_waiting:
                self.waiting_for_header[header_type] = False
            else:
                self.waiting_for_header[header_type] = False
        if formatted_header and helpers.str_to_bool(self.sect_display_log_types[formatted_header.type]):
            return formatted_header
        else:
            return None

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

    def _store_header(self, header):
        """Stores all headers into a data structure with the following format

        TODO - Change tree model where each header object contains its own children rather than using
        indices.

        [
        Test Preconditions
        Suite 1
            [
            Suite 1 Setup
                [
                Test 1 Setup
                Test 1 Starting
                    [
                    Step 1
                    Step 2
                    ]
                Test 1 Teardown
                Test 2 Setup
                Test 2 Starting
                    [
                    Step 1
                    ]
                Test 2 Teardown
                ]
            Suite 1 Teardown
            ]
        Suite 2
            [
            Suite 2 Setup
            Suite 2 Teardown
            ]
        Final Report
        """

        # Record the starting time for the current header and the ending time for the previous header
        if self.last_log_time:
            header.start_time = self.last_log_time

        if self.previous_header:
            self.finish_times[self.previous_header.original_line] = self.last_log_time
            self.previous_header = header
        else:
            self.previous_header = header

        # Non-suite related titles such as 'Final Report'
        if header.type == "title" and not header.test_name:
            self.executed_suites.extend([header])
            self.current_suite_index += 1
            self.current_test_case_index = -1
            self.current_step_index = -1

        # Suite titles starting with 'Test Suite' that is first starting
        elif header.type == "title" and header.suite and header.test_name != self.current_suite_name:
            self.current_suite_name = header.test_name

            # Reset test case and step indices
            self.current_test_case_index = -1
            self.current_step_index = -1

            self.executed_suites.append([header])
            self.current_suite_index += 1
            self.current_test_case_index += 1

        # Suite titles starting with 'Test Suite' that has already started
        elif header.type == "title" and header.suite and header.test_name == self.current_suite_name:
            self.executed_suites[self.current_suite_index].extend([header])
            self.current_test_case_index += 1

        # Test case titles starting with 'Test Case' that is first starting
        elif header.type == "title" and not header.suite and header.test_name != self.current_test_case:
            self.current_test_case = header.test_name
            self.current_step_index = 0
            self.executed_suites[self.current_suite_index].append([header])
            self.current_test_case_index += 1

        # Test case titles starting with 'Test Case' that has already started
        elif header.type == "title" and not header.suite and header.test_name == self.current_test_case:
            self.executed_suites[self.current_suite_index][self.current_test_case_index].extend([header])
            self.current_step_index += 1

        # Step
        elif header.type == "step":
            if not self.prev_header_was_step:
                self.executed_suites[self.current_suite_index][self.current_test_case_index].append(
                    [header])
                self.current_step_index += 1
            else:
                self.executed_suites[self.current_suite_index][self.current_test_case_index] \
                    [self.current_step_index].extend(
                    [header])
            self.prev_header_was_step = True

        if header.type != "step":
            self.prev_header_was_step = False

    def _print_header_report(self, header, depth):
        """Prints the header report at the end of the test."""
        if header.suite:
            output = "{0}: {1}".format(header.test_name, header.test_instruction)
        elif header.type == "title" and header.test_name:
            output = header.original_line
        elif header.type == "step":
            # TODO - Resolve Step listing issue 12/23
            output = "Step {0}: {1}".format(header.test_number, header.test_instruction)
        else:
            return

        start_time = header.start_time
        end_time = self.finish_times[header.original_line]
        timedelta = end_time - start_time
        # timedelta = timedelta + datetime.Timedelta(days=1) if timedelta < 0 else timedelta

        print "   " * depth + output
        print "   " * (depth + 1) + "Approximate Time Ellapsed: {0}".format(timedelta)

    def _read_vals_from_config_file(self):
        """Reads all of the values from the format .ini file"""
        self.format_config.read(self.format_config_filepath)
        self.sect_display_log_types = self.format_config[DISPLAY_LOG_TYPES_SECT]
        self.sect_display_fields = self.format_config[DISPLAY_FIELDS_SECT]
        self.sect_condense_fields = self.format_config[CONDENSE_FIELDS_SECT]
        self.sect_collapse_structs = self.format_config[COLLAPSE_STRUCTS_SECT]
        self.sect_lengths = self.format_config[LENGTHS_SECT]

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
