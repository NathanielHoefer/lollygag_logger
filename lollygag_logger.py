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
import configparser
import os
import sys
import re
import argparse
from threading import Thread
import Queue

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

FORMAT_CONFIG_FILE_NAME = "format_config"


class LollygagLogger:
    """Primary class that reads log lines individually from a file handle and handles formatting those
    lines based on the LogLine class and LogFormatter used.
    """

    def __init__(self, stream_handle, log_line, log_formatter):
        """Stores the components necessary for the run function

        :param stream_handle: an iterable that iterates line by line
        :param log_line: the class extended from LogLine that uses the uses the desired parser for the
            logs to be formatted.
        :param log_formatter: the class extended from LogFormatter that formats the passed LogLine JSON
            information
        """

        self.stream_handle = stream_handle
        self.log_line = log_line
        self.log_formatter = log_formatter
        self.queue = Queue.Queue()

    def run(self):
        """Executes the read and format threads concurrently."""
        # TODO

    def read(self):
        """Continuously reads logs line by line from the stream_handle and stores them as LogLine objects
        in JSON format to the queue."""

        for unformatted_line in self.stream_handle:
            if unformatted_line == "\n":
                self._store("")
                continue
            unformatted_line= unformatted_line.strip("\n\\n")
            if unformatted_line == "":
                continue
            else:
                self._store(unformatted_line)

    def format(self):
        """Continuously looks for logs in JSON format within the queue and then formats them according
        to the log_formatter class
        """

        formatter = self.log_formatter()

        while True:
            unformatted_line = self.queue.get(block=True)
            formatter.format(unformatted_line)

    def _store(self, unformatted_line):
        """Stores the unformatted line as a LogLine object in JSON format"""
        self.queue.put(self.log_line(unformatted_line).to_json())


class LogLine:
    """Stores log line into its various elements per the vl logging."""

    def __init__(self, line=""):
        self.original_line = line

        self.date = ""
        self.time = ""
        self.type = ""
        self.source = ""
        self.thread = ""
        self.details = ""

        self._parse_line(line)

    def __str__(self):
        return self.original_line

    def _parse_line(self, input_str):
        """Determines if the log line is in standard vl logging format based on the format of the
        timestamp (I know, its not very thorough, but it works for now). If the line is not in standard
        format, the line is stored in details as is.

        :param str input: The unformatted log line to be parsed.
        :return:
        """
        input_str.strip()
        is_standard = re.match("[0-9]{4}\-[0-9]{2}\-[0-9]{2}", input_str)
        if is_standard:
            split = input_str.split(" ", 5)
            self.date = split[0]
            self.time = split[1]
            self.type = split[2].ljust(5)
            self.source = split[3]
            self.thread = split[4]
            self.details = split[5]
        else:
            self.details = input_str


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

        # Grab max line length from format config file or from console width
        if LogFormatter.str_to_bool(format_config["LENGTHS"]["use_console_len"]):
            _, console_width = os.popen('stty size', 'r').read().split()
            max_len = int(console_width)
        else:
            max_len = int(format_config["LENGTHS"]["max_line_len"])

        # Condense entire log line if beyond max length
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
            formatting. Refer to Create Config File function for further config details.
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
            formatting. Refer to Create Config File function for further config details.
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
            formatted_line = LogFormatter.format_line_for_console(line, config)
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
            formatted_line = LogFormatter.format_line_for_console(line, config)
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
    group.add_argument("-f",  action="store", dest="log_filepath", help=ARG_FILE_DESC)
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
