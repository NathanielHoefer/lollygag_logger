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

    def condense(self, element, format_config):

        collapse_dict = format_config["COLLAPSE STRUCTURES"]["dict"]
        collapse_list = format_config["COLLAPSE STRUCTURES"]["list"]
        condense_len = int(format_config["LENGTHS"]["condensed_elem_len"])
        current_str = getattr(self, element)

        # Collapse dicts or lists if specified
        if collapse_dict:
            current_str = self._collapse(current_str, "{", "}", format_config)
        if collapse_list:
            current_str = self._collapse(current_str, "[", "]", format_config)

        # Condense length of element if it exceeds specified length
        if len(current_str) > condense_len:
            current_str = "".join([current_str[:condense_len - 3], "..."])

        return current_str

    @staticmethod
    def _collapse(str_element, start_char, end_char, format_config):
        start_index = str_element.find(start_char)
        end_index = str_element.find(end_char)
        collapse_len = int(format_config["LENGTHS"]["collapsed_struct_len"])
        if 0 <= start_index < end_index and end_index - start_index > collapse_len:
            return "".join([str_element[:start_index + collapse_len - 4], "...", end_char])
        # import pdb; pdb.set_trace()
        return str_element

class LogFormatter:
    VALID_TRUE_INPUT = ("true", "yes", "t", "y", "1")

    @staticmethod
    def format_line(log_line, format_config):

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
                    elements.append(log_line.condense(elem, format_config))
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

    @classmethod
    def str_to_bool(cls, input):
        return input.lower() in cls.VALID_TRUE_INPUT


def create_config_file():
    config = configparser.ConfigParser()

    config.add_section("DISPLAY LOG TYPES")
    config.set("DISPLAY LOG TYPES", "debug", "False")
    config.set("DISPLAY LOG TYPES", "info", "True")

    config.add_section("DISPLAY ELEMENTS")
    config.set("DISPLAY ELEMENTS", "date", "False")
    config.set("DISPLAY ELEMENTS", "time", "True")
    config.set("DISPLAY ELEMENTS", "type", "True")
    config.set("DISPLAY ELEMENTS", "source", "True")
    config.set("DISPLAY ELEMENTS", "thread", "False")
    config.set("DISPLAY ELEMENTS", "details", "True")

    config.add_section("CONDENSE ELEMENTS")
    config.set("CONDENSE ELEMENTS", "date", "False")
    config.set("CONDENSE ELEMENTS", "time", "False")
    config.set("CONDENSE ELEMENTS", "type", "False")
    config.set("CONDENSE ELEMENTS", "source", "True")
    config.set("CONDENSE ELEMENTS", "thread", "True")
    config.set("CONDENSE ELEMENTS", "details", "True")

    config.add_section("COLLAPSE STRUCTURES")
    config.set("COLLAPSE STRUCTURES", "list", "True")
    config.set("COLLAPSE STRUCTURES", "dict", "True")

    config.add_section("LENGTHS")
    config.set("LENGTHS", "use_console_len", "True")
    config.set("LENGTHS", "max_line_len", "200")
    config.set("LENGTHS", "condensed_elem_len", "100")
    config.set("LENGTHS", "collapsed_struct_len", "30")

    with open("format_config", "wb") as configfile:
        config.write(configfile)



def format_print_file(filepath):

    # Create new format config file if it doesn't already exist in the current working directory
    local_cwd = filepath[:filepath.rfind("/") + 1]
    config_path = local_cwd + FORMAT_CONFIG_NAME
    if not os.path.isfile(config_path):
        create_config_file()

    config = configparser.ConfigParser()
    config.read(config_path)

    # config.read("/home/hnathani/repos/hoefer/lollygag-logger/OutputCapture/format_config")
    with open(filepath, "r") as file:
        for line in file.readlines():
            if line == "\n":
                print ""
            else:
                line = line.strip("\n\\n")
                f = LogFormatter.format_line(LogLine(line), config)
                if not f:
                    continue
                print f


if __name__ == '__main__':

    # Check for entered path
    if len(sys.argv) == 2:
        file_path = os.getcwd() + "/" + sys.argv[1]
    # else:
    #     print "Please provide the log file to print"
    #     exit(0)
    else:
        file_path = "/home/nathaniel/Repos/lollygag_logger/OutputCapture/test.log"
        # file_path = "/home/hnathani/vl_artifacts/TsCreateDeleteAccountsVolSnap-2017-09-22T14.12.18/test.log"
        # file_path = "/home/hnathani/Documents/OutputCapture/testlogs.log"

    format_print_file(file_path)



    # print("Starting")
    # proc = subprocess.Popen(['python', r'C:\Users\natha\Downloads\OutputCapture\output_print.py'], stdout=subprocess.PIPE,
    #                         bufsize=1, universal_newlines=False)
    # for line in iter(proc.stdout.readline, b''):
    #     print("Captured Output: {}".format(line.decode("utf-8").rstrip(), flush=True))
    # proc.stdout.close()
    # proc.wait()