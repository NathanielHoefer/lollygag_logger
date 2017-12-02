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
from collections import OrderedDict
from threading import Thread
import Queue
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

FORMAT_CONFIG_FILE_NAME = "format_config.ini"


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
            return " ".join([field for field in self.FIELDS if field != ""])
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
        display_log_types = self.format_config["DISPLAY LOG TYPES"]
        log_type = self.log_line.type.strip().lower()
        if not self._str_to_bool(display_log_types[log_type]):
            return

        # Remove and condense fields in standard logs per format config file
        if self.log_line.standard_format:
            self._remove_fields()
            self._condense_fields()

        # Grab max line length from format config file or from console width
        formatted_line = str(self.log_line)
        if self._str_to_bool(self.format_config["LENGTHS"]["use_console_len"]):
            _, console_width = os.popen('stty size', 'r').read().split()
            max_len = int(console_width)
        else:
            max_len = int(self.format_config["LENGTHS"]["max_line_len"])

        # Condense entire log line if beyond max length
        if len(formatted_line) > max_len:
            formatted_line = formatted_line[:max_len - 3] + "..."
        print formatted_line

    def _str_to_bool(self, str_bool_val):
        """Evaluates bool value of string input based on LogFormatter.VALID_TRUE_INPUT"""
        return str_bool_val.lower() in self.VALID_TRUE_INPUT

    def _remove_fields(self):
        """Remove field from line if marked not to display."""
        display_fields = self.format_config["DISPLAY FIELDS"]
        for field, val in display_fields.items():
            if not self._str_to_bool(val):
                setattr(self.log_line, field, "")

    def _condense_fields(self):
        """Condense and collapse individual line fields to the specified length in format config."""
        condense_fields = self.format_config["CONDENSE FIELDS"]
        for field, val in condense_fields.items():
            if self._str_to_bool(val):
                self._condense_field(field)

    def _condense_field(self, field):
        """Condenses each field of a log line per the format config file to a specific length, and
        collapses lists and dictionaries that exceed a given length. All specified in the format_config
        file and updates the log_line object.

        :param str field: The LogLine field to be condensed.
        """

        collapse_dict = self.format_config["COLLAPSE STRUCTURES"]["dict"]
        collapse_list = self.format_config["COLLAPSE STRUCTURES"]["list"]
        condense_len = int(self.format_config["LENGTHS"]["condensed_field_len"])
        current_field_str = getattr(self.log_line, field)

        # Collapse dicts or lists if specified
        if collapse_dict:
            current_field_str = self._collapse_struct(current_field_str, "dict")
        if collapse_list:
            current_field_str = self._collapse_struct(current_field_str, "list")

        # Condense length of element if it exceeds specified length
        if len(current_field_str) > condense_len:
            current_field_str = "".join([current_field_str[:condense_len - 3], "..."])
        setattr(self.log_line, field, current_field_str)

    def _collapse_struct(self, field_str, data_struct):
        """Shortens the display of the first encountered list or dictionary to a specified length within
        a given string.

        Should update to locate recursively, but not extremely important right now.

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
        collapse_len = int(self.format_config["LENGTHS"]["collapsed_struct_len"])

        # Collapse first data structure found - should make this to
        if 0 <= start_index < end_index and end_index - start_index > collapse_len:
            return "".join([field_str[:start_index + collapse_len - 4], "...", end_char])
        return field_str


def create_config_file(filepath=""):
    """Creates a config parser file within the current working directory containing the options for
    formatting log lines.

    :param str filepath: File path to store format config file. Default is current working directory.
    """

    config_fields = OrderedDict()

    # Log lines identified by the following types to be printed or ignored
    config_fields["DISPLAY LOG TYPES"] = [
        ("debug",   "False"),
        ("info",    "True"),
        ("step",    "True"),
        ("title",   "True"),
        ("warning", "True"),
        ("error",   "True"),
        ("other",   "True")]

    # Elements within each log line to be printed or ignored
    config_fields["DISPLAY FIELDS"] = [
        ("date",    "False"),
        ("time",    "True"),
        ("type",    "True"),
        ("source",  "True"),
        ("thread",  "False"),
        ("details", "True")]

    # Elements within each log line to be condensed to the specified length under the LENGTHS
    # section - condensed_elem_len
    config_fields["CONDENSE FIELDS"] = [
        ("date",    "False"),
        ("time",    "False"),
        ("type",    "False"),
        ("source",  "True"),
        ("thread",  "True"),
        ("details", "True")]

    # Data structures within elements to be condensed to be collapsed to the specified length under
    # the LENGTHS section - collapsed_struct_len
    config_fields["COLLAPSE STRUCTURES"] = [
        ("list", "True"),
        ("dict", "True")]

    # Various length options
    config_fields["LENGTHS"] = [
        ("use_console_len",     "True"),    # Use console width for max log line length
        ("max_line_len",        "200"),     # Max length of log line to be printed
        ("condensed_field_len", "100"),     # This value includes the "..."
        ("collapsed_struct_len", "30")]     # This value includes the "[" and "...]"

    # Create and add sections and options to configparser object
    format_config = configparser.ConfigParser()
    for section, options in config_fields.items():
        format_config.add_section(section)
        for option in options:
            format_config.set(section, option[0], option[1])

    # Write config to file in current working directory
    filepath = filepath + FORMAT_CONFIG_FILE_NAME if filepath else FORMAT_CONFIG_FILE_NAME
    with open(filepath, "wb") as configfile:
        format_config.write(configfile)

    return format_config


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
