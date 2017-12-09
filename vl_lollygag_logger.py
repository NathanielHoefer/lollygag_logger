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

from abc import ABCMeta, abstractmethod
import subprocess
import configparser
import os
import sys
import re
import argparse
from threading import Thread
import Queue
from vl_config_file import *
from lollygag_logger import LogLine, LogFormatter

# Descriptions for arg parse
PROGRAM = "Lollygag Logger"
DESCRIPTION = "This script will print out formatted logs from a log file or format the output of the " \
              "vl run command."
ARG_FILE_DESC = "Path of the log file to print."
ARG_VL_DESC = "The path to the suite as used in the 'vl run' command."

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
    TOKEN_COUNT = len(FIELDS)

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

        # Check to see if there are the expected number of tokens in the line. Currently expecting there
        # to be 5 or 6 tokens. If not, then mark as a non-standard vl format, and return
        split = input_str.split(" ", self.TOKEN_COUNT - 1)
        if not (self.TOKEN_COUNT - 1 <= len(split) <= self.TOKEN_COUNT):
            return

        # Assign token to proper field if format matches correctly
        self.date = split[0] if re.match("^\d{4}\-\d{2}\-\d{2}$", split[0]) else ""
        self.time = split[1] if re.match("^\d{2}:\d{2}:\d{2}\.\d{6}$", split[1]) else ""
        if split[2] in self.LOG_LEVELS:
            self.type = split[2]
        self.source = split[3] if re.match("^\[.*:.*\]$", split[3]) else ""
        self.thread = split[4] if re.match("^\[.*:.*\]$", split[4]) else ""
        self.details = split[5] if len(split) == self.TOKEN_COUNT else ""

        # If any of the fields are empty with the exception of details, change type to OTHER and move all
        # line data to the details field.
        for field in self.FIELDS:
            if field is not "details" and getattr(self, field) is "":
                self._default_vals()
                return
        self.standard_format = True


class ValenceConsoleOutput(LogFormatter):
    """Class containing log line format functions.

    :ivar log_line_cls: the LogLine class used to parse the unformatted log lines
    :ivar format_config: the configparser that contains all of the user options
    """

    # Valid values from ConfigParser that result in True
    VALID_TRUE_INPUT = ("true", "yes", "t", "y", "1")

    log_queue = []

    def __init__(self, log_line_cls, format_config):
        self.log_line_cls = log_line_cls
        self.format_config = format_config
        self.log_line = None

        # Format config sections stored individually as dicts
        self.sect_display_log_types = self.format_config[DISPLAY_LOG_TYPES_SECT]
        self.sect_display_fields = self.format_config[DISPLAY_FIELDS_SECT]
        self.sect_condense_fields = self.format_config[CONDENSE_FIELDS_SECT]
        self.sect_collapse_structs = self.format_config[COLLAPSE_STRUCTS_SECT]
        self.sect_lengths = self.format_config[LENGTHS_SECT]

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
        if not self._str_to_bool(self.sect_display_log_types[log_type]):
            return

        # Remove and condense fields in standard logs per format config file
        if self.log_line.standard_format:
            self._remove_fields()
            self._condense_fields()

        # Grab max line length from format config file or from console width
        formatted_line = str(self.log_line)
        if self._str_to_bool(self.sect_lengths["use_console_len"]) and sys.stdin.isatty():
            _, console_width = os.popen('stty size', 'r').read().split()
            max_len = int(console_width)
        else:
            max_len = int(self.sect_lengths["max_line_len"])

        # Condense entire log line if beyond max length
        print self.condense(formatted_line, max_len)

    def _str_to_bool(self, str_bool_val):
        """Evaluates bool value of string input based on LogFormatter.VALID_TRUE_INPUT"""
        return str_bool_val.lower() in self.VALID_TRUE_INPUT

    def _remove_fields(self):
        """Remove field from line if marked not to display."""
        for field, val in self.sect_display_fields.items():
            if not self._str_to_bool(val):
                setattr(self.log_line, field, "")

    def _condense_fields(self):
        """Condense and collapse individual line fields to the specified length in format config."""
        for field, val in self.sect_condense_fields.items():
            if self._str_to_bool(val):
                self.condense_field(field)

    def condense_field(self, field):
        """Condenses each field of a log line per the format config file to a specific length, and
        collapses lists and dictionaries that exceed a given length. All specified in the format_config
        file and updates the log_line object.

        :param str field: The LogLine field to be condensed.
        """

        collapse_dict = self.sect_collapse_structs["dict"]
        collapse_list = self.sect_collapse_structs["list"]
        condense_len = int(self.sect_lengths["condensed_field_len"])
        current_field_str = getattr(self.log_line, field)

        # Collapse dicts or lists if specified
        if self._str_to_bool(collapse_dict):
            current_field_str = self.collapse_struct(current_field_str, "dict")
        if self._str_to_bool(collapse_list):
            current_field_str = self.collapse_struct(current_field_str, "list")

        # Condense length of element if it exceeds specified length
        current_field_str = self.condense(current_field_str, condense_len)
        setattr(self.log_line, field, current_field_str)
        return current_field_str

    def collapse_struct(self, field_str, data_struct):
        """Shortens the display of the first encountered list or dictionary to a specified length within
        a given string. If the length of the structure (including the '[]' or '{}' is > the
        collapsed_struct_len specified in config file, then the structure will be reduced to that length
        and indicated by an ellipse. Ex: [abcdefghijklmnopqrstuvwxyzab] -> [abcdefghijklmnopqrstuvwxy...]

        Currently only minimizes the out-most structure while ignoring the inner structures. Will look
        to fix this in the future if time allows.

        :param str field_str: The log line element str containing the data structure
        :param str data_struct: "list" or "dict" indicating what data structure to collapse
        :return: String of the element with the specified collapsed structure.
        """
        # Determine struct entered
        if data_struct == "dict":
            start_char = "{"
            end_char = "}"
        elif data_struct == "list":
            start_char = "["
            end_char = "]"
        else:
            return field_str

        # Initialize collapse values - probably can find library to do this more efficiently
        start_index = field_str.find(start_char)
        end_index = field_str.find(end_char)
        collapse_len = int(self.format_config[LENGTHS_SECT]["collapsed_struct_len"])

        # Collapse first data structure found
        if 0 <= start_index < end_index:
            struct = "".join([start_char,
                             self.condense(field_str[start_index + 1: end_index], collapse_len - 2),
                             end_char])
            return "".join([field_str[:start_index], struct, field_str[end_index + 1:]])
        return field_str

    def condense(self, str_line, max_len):
        """Condenses the string if it is greater than the max length, appending ellipses.

        :param str str_line: Line to be condensed
        :param int max_len: The maximum length of the line
        """

        if len(str_line) > max_len:
            return "".join([str_line[:max_len - 3], "..."])
        else:
            return str_line


def format_print_file_to_console(filepath):
    """Prints a log file to the console using format information found within a format config file within
    the same directory as the log file. If the format config file isn't found, a new one is created using
    default settings. Refer to Create Config File function for further config details.

    :param str filepath: File path of the log file to be printed.
    """

    # Create new format config file if it doesn't already exist in the same directory as the log file
    config_path = filepath[:filepath.rfind("/") + 1] + FORMAT_CONFIG_FILE_NAME
    if not os.path.isfile(config_path):
        create_config_file(config_path)
    config = configparser.ConfigParser()
    config.read(config_path)

    # Open the log file, format each line, and print to the console.
    with open(filepath, "r") as logfile:
        for line in logfile.readlines():
            formatted_line = LegacyLogFormatter.format_line_for_console(line, config)
            if formatted_line == "\n":
                print ""
            elif formatted_line == "":
                continue
            else:
                print formatted_line


def format_vl_output(vl_run_path):
    """Captures the log lines from the output of a "vl run <vl_run_path>" and formats them as specified
    in a format config file. This function will need to be call in the same location as a typical vl run
    would be called in to ensure that the suite path is correct.

    The format config file is generated in the current working directory and
    can be updated. Refer to Create Config File function for further config details.

    :param str vl_run_path: The path to the suite to be executed
    :return:
    """

    # Create new format config file if it doesn't already exist in the current working directory
    config_path = os.getcwd() + "/" + FORMAT_CONFIG_FILE_NAME
    if not os.path.isfile(config_path):
        create_config_file()
    config = configparser.ConfigParser()
    config.read(config_path)
    initial_config_modify_time = os.path.getmtime(config_path)

    # Begin vl run subprocess
    proc = subprocess.Popen(["vl", "run", vl_run_path], stdout=subprocess.PIPE,
                            bufsize=1, universal_newlines=False)
    try:

        # Capture output from vl run, format it, and print it to the console
        for line in iter(proc.stdout.readline, b''):

            # Check for format config file update
            current_config_modify_time = os.path.getmtime(config_path)
            if current_config_modify_time > initial_config_modify_time:
                config.read(config_path)
                initial_config_modify_time = current_config_modify_time

            # Format and print log line
            formatted_line = LegacyLogFormatter.format_line_for_console(line, config)
            if formatted_line == "\n":
                print ""
            elif formatted_line == "":
                continue
            else:
                print formatted_line
            sys.stdout.flush()

        proc.stdout.close()
        proc.wait()
    except KeyboardInterrupt:
        proc.kill()


if __name__ == '__main__':

    # Argument setup and parsing
    parser = argparse.ArgumentParser(prog=PROGRAM, description=DESCRIPTION)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f", action="store", dest="log_filepath", help=ARG_FILE_DESC)
    group.add_argument("-vl", action="store", dest="vl_suite_path", help=ARG_VL_DESC)
    args = parser.parse_args()

    # Validate that args exist and execute printing the logs
    if args.log_filepath:
        arg_path = args.log_filepath
        if arg_path[0] == "/" or arg_path[0] == "~":
            file_path = arg_path
        else:
            file_path = os.getcwd() + "/" + arg_path
        format_print_file_to_console(file_path)
    elif args.vl_suite_path:
        format_vl_output(args.vl_suite_path)
    else:
        print "Please pass valid arguments"
