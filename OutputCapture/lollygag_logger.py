"""
=========================================================================================================
Lollygag Logger
=========================================================================================================

Current Functionality:
 - Read a log file and print out the contents
 - Display options:
    - On/Off Debug and Info lines
    - On/Off Date, Time, Type, Source, Thread, and Details in log line
    - On/Off condense source, thread, and detail elements
    - Take file name input for log file
    - Automatic generation and retrieval of format_config file

TODO list:
 - Clean up current work and add comments/docstrings
 - Create separate file for starting vl run process and capturing output
 - Handle ERROR and WARNING log types

=========================================================================================================
"""

import subprocess
import sys
import time
import tempfile
from enum import Enum
import configparser
import os, sys
import re

FORMAT_CONFIG_NAME = "format_config"

LINE_ELEMENTS = ("date", "time", "type", "source", "thread", "details")
TYPE_DEBUG = "DEBUG"
TYPE_INFO = "INFO"
TYPE_WARNING = "WARNING"
TYPE_ERROR = "ERROR"
TYPE_STEP = "STEP"
TYPE_TITLE = "TITLE"
TYPE_OTHER = "OTHER"
LOG_TYPES = (TYPE_DEBUG, TYPE_INFO, TYPE_WARNING, TYPE_STEP, TYPE_TITLE, TYPE_OTHER)

FORMAT_CONFIG_FILE_NAME = "format_config"


class LogType(Enum):
    DEBUG = 1
    INFO = 2
    STEP = 3
    TITLE = 4
    OTHER = 5

    # TODO - Figure out a better solution to this
    @classmethod
    def type_str_len(cls):
        return 5

    @classmethod
    def find_log_type(cls, log_type_str):
        if log_type_str.upper() == TYPE_DEBUG:
            return LogType.DEBUG
        elif log_type_str.upper() == TYPE_INFO:
            return LogType.INFO
        elif re.match("(\-\-\-)+", log_type_str):
            return LogType.STEP
        elif re.match("(===)+", log_type_str):
            return LogType.TITLE
        else:
            return LogType.OTHER


class LogLine:
    CONDENSE_LEN = 100              # Max number of characters to show of details when condensed
    COND_LIST_DISPLAY_LEN = 10      # Number of characters to show within condensed list or dict

    def __init__(self, line=""):
        self.original_line = line
        self.type_enum = LogType.OTHER

        self.date = ""
        self.time = ""
        self.type = ""
        self.source = ""
        self.thread = ""
        self.details = ""

        self._parse_line(line)

    def __str__(self):
        return self.original_line

    def _parse_line(self, input):
        input.strip()
        is_standard = re.match("[0-9]{4}\-[0-9]{2}\-[0-9]{2}", input)
        if is_standard:
            split = input.split(" ", 5)
            self.date = split[0]
            self.time = split[1]
            self.type = split[2].ljust(5)
            self.source = split[3]
            self.thread = split[4]
            self.details = split[5]
            self.type_enum = LogType.find_log_type(input)
        else:
            self.details = input
            self.type_enum = LogType.find_log_type(input)


class LogFormatter:
    """Class containing log line format functions"""

    # Valid values from ConfigParser that result in True
    VALID_TRUE_INPUT = ("true", "yes", "t", "y", "1")

    @staticmethod
    def format_line_for_console(unformatted_line, format_config):
        """With the options within the format_config, the unformatted log line is formatted and returned.

        In order for the line to be fully formatted, the log must contain the following elements and
        order, otherwise the line will be only has the option to be condensed.
        <Date: 9999-99-99> <Time: 99:99:99.999999> <Type> <Source> <Thread> <Details>

        :param str unformatted_line: Any single line of log information
        :param configparser.ConfigParser format_config: ConfigParser containing the options for desired
            formatting. Refer to Create Config File function for further details.
        :return: String of updated log line.
        """

        # Check to see if line is empty, and create log line object to parse the line
        if unformatted_line == "\n":
            return "\n"
        line = unformatted_line.strip("\n\\n")
        if not line:
            return ""
        log_line = LogLine(line)

        # Return original line if unable to read format config file
        if not format_config.sections():
            return str(log_line)

        # Retrieve options
        display_log_types = format_config["DISPLAY LOG TYPES"]
        display_elements = format_config["DISPLAY ELEMENTS"]
        condense_elements = format_config["CONDENSE ELEMENTS"]

        # Don't print line if marked false in config file
        log_type = log_line.type.lower()
        if log_type in format_config["DISPLAY LOG TYPES"] \
                and not LogFormatter.str_to_bool(display_log_types[log_type]):
            return ""

        # Return only the line details if not a standard log line
        standard_logs = (TYPE_DEBUG, TYPE_INFO, TYPE_WARNING, TYPE_ERROR)
        if log_type.upper().strip() not in standard_logs:
            return log_line.details

        # Condense and collapse individual line elements from standard log line
        elements = []
        for elem, val in display_elements.items():
            if LogFormatter.str_to_bool(val):
                if LogFormatter.str_to_bool(condense_elements[elem]):
                    elements.append(LogFormatter._static_condense(log_line, elem, format_config))
                else:
                    elements.append(getattr(log_line, elem))
        output = " ".join(elements)

        # Condense entire log line if necessary

        # TODO - Get console size for max len
        # if LogFormatter.str_to_bool(format_config["LENGTHS"]["use_console_len"]):
        #     _, max_len = os.popen('stty size', 'r').read().split()
        # else:

        max_len = int(format_config["LENGTHS"]["max_line_len"])
        if len(output) > max_len:
            output = output[:max_len - 3] + "..."
        return output

    @staticmethod
    def _static_condense(log_line, element, format_config):
        """Condenses each element of a log line per the format config file to a specific length, and
        collapses lists and dictionaries that exceed a given length. All specified in the format_config
        file. Doesn't change the values of the log_line object.

        :param LogLine log_line: Line to be condensed and collapsed if requested.
        :param str element: Name of element within the LogLine object to be condensed
        :param configparser.ConfigParser format_config: ConfigParser containing the options for desired
            formatting. Refer to Create Config File function for further details.
        :returns: String of the condensed and collapsed log_line
        """

        collapse_dict = format_config["COLLAPSE STRUCTURES"]["dict"]
        collapse_list = format_config["COLLAPSE STRUCTURES"]["list"]
        condense_len = int(format_config["LENGTHS"]["condensed_elem_len"])
        current_str = getattr(log_line, element)

        # Collapse dicts or lists if specified
        if collapse_dict:
            current_str = LogFormatter._collapse(current_str, "dict", format_config)
        if collapse_list:
            current_str = LogFormatter._collapse(current_str, "list", format_config)

        # Condense length of element if it exceeds specified length
        if len(current_str) > condense_len:
            current_str = "".join([current_str[:condense_len - 3], "..."])
        return current_str

    @staticmethod
    def _collapse(str_element, data_struct, format_config):
        """Shortens the display of the first encountered list or dictionarie to a specified length within
        a given string.

        Should update to locate recursively, but not extremely important right now.

        :param str str_element: The log line element str containing the data structure
        :param str data_struct: "list" or "dict" indicating what data structure to collapse
        :param configparser.ConfigParser format_config: ConfigParser containing the options for desired
            formatting. Refer to Create Config File function for further details.
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
            return str_element

        # Initialize collapse values - probably can find library to do this more efficiently
        start_index = str_element.find(start_char)
        end_index = str_element.find(end_char)
        collapse_len = int(format_config["LENGTHS"]["collapsed_struct_len"])

        # Collapse first data structure found - should make this to
        if 0 <= start_index < end_index and end_index - start_index > collapse_len:
            return "".join([str_element[:start_index + collapse_len - 4], "...", end_char])
        return str_element

    @classmethod
    def str_to_bool(cls, input):
        """Evaluates bool value of string input based on LogFormatter.VALID_TRUE_INPUT"""
        return input.lower() in cls.VALID_TRUE_INPUT


def create_config_file(filepath = ""):
    """Creates a config parser file within the current working directory containing the options for
    formatting log lines.

    :param str filepath: File path to store format config file. Default is current working directory.
    """

    config = configparser.ConfigParser()

    # Log lines identified by the following types to be printed or ignored
    config.add_section("DISPLAY LOG TYPES")
    config.set("DISPLAY LOG TYPES", "debug", "False")
    config.set("DISPLAY LOG TYPES", "info", "True")

    # Elements within each log line to be printed or ignored
    config.add_section("DISPLAY ELEMENTS")
    config.set("DISPLAY ELEMENTS", "date", "False")
    config.set("DISPLAY ELEMENTS", "time", "True")
    config.set("DISPLAY ELEMENTS", "type", "True")
    config.set("DISPLAY ELEMENTS", "source", "True")
    config.set("DISPLAY ELEMENTS", "thread", "False")
    config.set("DISPLAY ELEMENTS", "details", "True")

    # Elements within each log line to be condensed to the specified length under the LENGTHS section -
    # condensed_elem_len
    config.add_section("CONDENSE ELEMENTS")
    config.set("CONDENSE ELEMENTS", "date", "False")
    config.set("CONDENSE ELEMENTS", "time", "False")
    config.set("CONDENSE ELEMENTS", "type", "False")
    config.set("CONDENSE ELEMENTS", "source", "True")
    config.set("CONDENSE ELEMENTS", "thread", "True")
    config.set("CONDENSE ELEMENTS", "details", "True")

    # Data structures within elements to be condensed to be collapsed to the specified length under the
    # LENGTHS section - collapsed_struct_len
    config.add_section("COLLAPSE STRUCTURES")
    config.set("COLLAPSE STRUCTURES", "list", "True")
    config.set("COLLAPSE STRUCTURES", "dict", "True")

    # Various length options
    config.add_section("LENGTHS")
    config.set("LENGTHS", "use_console_len", "True")        # Use console width for max log line length
    config.set("LENGTHS", "max_line_len", "200")            # Max length of log line to be printed
    config.set("LENGTHS", "condensed_elem_len", "100")      # This value includes the "..."
    config.set("LENGTHS", "collapsed_struct_len", "30")     # This value includes the "[" and "...]"

    # Write config to file in current working directory
    filepath = filepath if filepath else FORMAT_CONFIG_FILE_NAME
    with open(filepath, "wb") as configfile:
        config.write(configfile)


def format_print_file_to_console(filepath):
    """Prints a log file to the console using format information found within a format config file within
    the same directory as the log file. If the format config file isn't found, a new one is created using
    default settings.

    :param str filepath: File path of the log file to be printed.
    """

    # Create new format config file if it doesn't already exist in the current working directory
    config_path = filepath[:filepath.rfind("/") + 1] + FORMAT_CONFIG_NAME
    if not os.path.isfile(config_path):
        create_config_file(config_path)
    config = configparser.ConfigParser()
    config.read(config_path)

    # Open the log file, format each line, and print to the console.
    with open(filepath, "r") as logfile:
        for line in logfile.readlines():
            formatted_line = LogFormatter.format_line_for_console(line, config)
            if formatted_line == "\n":
                print ""
            elif formatted_line == "":
                continue
            else:
                print formatted_line

def format_vl_output(vl_run_path):

    # Create new format config file if it doesn't already exist in the current working directory
    config_path = os.getcwd() + "/" + FORMAT_CONFIG_FILE_NAME
    if not os.path.isfile(config_path):
        create_config_file()
    config = configparser.ConfigParser()
    config.read(config_path)

    proc = subprocess.Popen(["vl", "run", sys.argv[1]], stdout=subprocess.PIPE,
                            bufsize=1, universal_newlines=False)
    for line in iter(proc.stdout.readline, b''):
        formatted_line = LogFormatter.format_line_for_console(line, config)
        print formatted_line
        sys.stdout.flush()


            # print("Captured Output: {}".format(line.decode("utf-8").rstrip(), flush=True))
    proc.stdout.close()
    proc.wait()


if __name__ == '__main__':

    # Check for entered path
    if len(sys.argv) == 2:
        arg_path = sys.argv[1]
        if arg_path[0] == "/" or arg_path[0] == "~":
            file_path = arg_path
        else:
            file_path = os.getcwd() + "/" + sys.argv[1]
    # else:
    #     print "Please provide the log file to print"
    #     exit(0)
    else:
        file_path = "/home/nathaniel/Repos/lollygag_logger/OutputCapture/test.log"
        # file_path = "/home/hnathani/vl_artifacts/TsCreateDeleteAccountsVolSnap-2017-09-22T14.12.18/test.log"
        # file_path = "/home/hnathani/Documents/OutputCapture/testlogs.log"

    format_print_file_to_console(file_path)



    # print("Starting")
    # proc = subprocess.Popen(['python', r'C:\Users\natha\Downloads\OutputCapture\output_print.py'], stdout=subprocess.PIPE,
    #                         bufsize=1, universal_newlines=False)
    # for line in iter(proc.stdout.readline, b''):
    #     print("Captured Output: {}".format(line.decode("utf-8").rstrip(), flush=True))
    # proc.stdout.close()
    # proc.wait()