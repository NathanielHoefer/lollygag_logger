"""
=========================================================================================================
Valence Console Formatter Class
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/2/2017

TODO - Update this description

=========================================================================================================
"""

# TODO - Update file description

import sys
import helpers
import re
from bin.lollygag_logger import LogFormatter
from bin.lollygag_logger.lollygag_logger import KILL_SIGNAL
from vl_objects import ValenceHeader as Header
from enums import LogType, ValenceField, ColorType
from vl_config_file import *

WRITE_UPDATE_INCREMENT = 10


class ValenceConsoleFormatter(LogFormatter):
    """Class containing log line format functions.

    :ivar log_line_cls: the LogLine class used to parse the unformatted log lines
    :ivar format_config: the configparser that contains all of the user options
    :ivar find_str: String to highlight if contained in line.
    :ivar list_step: The step or test case to be printed. For test case, match 'Test Case #'. If
        specifying step, list full name out as seen in logs. If empty, all logs will be printed.
    :ivar write_path: File to save the formatted logs to. If empty, logs won't be saved.
    """

    log_queue = []

    def __init__(self, log_line_cls, format_config, ini_filepath="",
                 find_str="", list_step="", write_path=""):
        self.log_line_cls = log_line_cls
        self.format_config = format_config
        self.format_config_filepath = ini_filepath if ini_filepath \
            else DEFAULT_CONFIG_PATH
        self.find_str = find_str
        self.list_step = list_step
        self.write_path = write_path
        self.duplicate_blank_line = False
        self.log_lines_read = 0

        # Format config sections stored individually as dicts
        self._read_vals_from_config_file()
        self.format_config_mod_time = os.path.getmtime(self.format_config_filepath)

        # Variables needed for titles and steps
        self.waiting_for_header = {LogType.TITLE: False, LogType.STEP: False}
        self.last_log_time = None

        # List step variables
        self.listed_step_to_print = False
        self.listed_step_type = None
        self.listed_steps_status = "Searching"  # "Searching" | "Processing" | "Completed"
        self.searching_text_printed = False

    def format(self, unformatted_log_line):
        """Prints the formatted log line to the console based on the format config file options.

        1. Create LogLine object
        2. Store last log time
        3. Update format_config if it has been updated
        4. Construct and print header
        5. Skip line if not marked for print
        6. Remove and condense fields in standard format
        7. Add color to type field
        8. Condense entire line if beyond max and print

        :return: Formatted logline as string | empty string | None if not to print
        """

        # TODO - Fix find bug

        # Strip log line string and use it to create the log_line object
        line = unformatted_log_line.strip("\n\\n")
        log_line = self.log_line_cls(line, self._calc_max_len())

        # Store last log time
        if log_line.standard_format and log_line.time:
            self.last_log_time = log_line.time[0]

        # Update format config values if file has been updated
        self._update_format_config()

        # Handle header if applicable
        formatted_header = self._handle_header(log_line)
        if formatted_header:
            if formatted_header is True:
                return None
            else:
                return formatted_header

        # Don't print if not in the current step
        if self.list_step and not self.listed_step_to_print:
            return None

        # Don't print if searching for string and log doesn't contain it
        if self.find_str and not re.search(self.find_str, log_line.original_line):
            return None

        # Skip line if type is marked to not display
        log_type = log_line.get_log_type().name.lower()
        if not helpers.str_to_bool(self.sect_display_log_types[log_type]):
            return None

        # Remove and condense fields in standard logs per format config file
        if log_line.standard_format:
            log_line = self._remove_fields(log_line)
            log_line = self._condense_fields(log_line)

        # Add color to the type field and convert log line to string
        if helpers.str_to_bool(self.format_config[COLORS]["use_colors"]):
            color = ColorType[log_line.get_log_type().name]
            log_line.color_field(ValenceField.TYPE, color)

        return log_line

    def send(self, formatted_log_line):
        """Either prints formatted line to console or write it to file based on write flag.

        If writing to a file, will print to screen number of lines written. Also, prevents multiple
        blank lines from being printed in a row.

        :param ValenceLogLine formatted_log_line: Formatted log line | None - indicating to not print
        line.
        """

        # Increase lines read count and print update if writing to a file
        self.log_lines_read += 1
        if self.write_path and self.log_lines_read % WRITE_UPDATE_INCREMENT == 0:
            print "Lines Read: {0}\r".format(self.log_lines_read),
            sys.stdout.flush()

        # Print searching message until step has been found
        if self.listed_steps_status == "Searching":

            search_text = ""
            if self.find_str:
                search_text = "Searching for string: \"{0}\"\n".format(self.find_str)
            elif self.list_step:
                search_text = "Searching for Test Case/Step: {0}\n".format(self.list_step)

            if not self.searching_text_printed:
                print search_text
                self.searching_text_printed = True
            else:
                print "---   \r" if self.log_lines_read % 100 < 50 else "   ---\r",

        # Update status when log line is sent through
        if formatted_log_line is None:
            return None
        else:
            self.listed_steps_status = "Processing"

        # Check to see if multiple blank lines are being printed
        if formatted_log_line.original_line == "" and not self.duplicate_blank_line:
            self.duplicate_blank_line = True
        elif formatted_log_line.original_line == "" and self.duplicate_blank_line:
            return None
        elif formatted_log_line is not None:
            self.duplicate_blank_line = False

        self._print_line(formatted_log_line)

        # Kill program when listed steps have been processed.
        if self.listed_steps_status == "Completed":
            return KILL_SIGNAL
        else:
            return None

    def _handle_header(self, log_line):
        """Determines if LogLine is part of header and handles the printing if so.

        Initially attempts to create header object, store it, then print it. If the header is the
        'Final Report', then the headers and their ellapsed time will be reported.

        :return: True if LogLine was part of a header, but not to be printed, False if LogLine is not
        part of header, and a formatted string representing header if header is to be printed.
        """
        log_type = log_line.get_log_type()
        header_line = self._combine_header_logs(log_type, log_line)

        if header_line:

            # Check if header matches step to list
            if header_line.original_line == self.list_step:
                self.listed_step_to_print = True
                self.listed_step_type = header_line.type

            # Return without printing if a specified step to print and this isn't part of it
            if self.list_step and not self.listed_step_to_print:
                return True

            # Uncheck 'selected step' flag once the next step is hit if a step is selected or the next
            # test case step is hit if test case is selected.
            if self.listed_step_type:
                if self.listed_step_type.value >= header_line.type.value \
                        and header_line.original_line != self.list_step \
                        and header_line.original_line != "":
                    self.listed_step_to_print = False
                    self.listed_steps_status = "Completed"
                    return True
            return header_line

        # Don't print header border
        elif log_type == LogType.STEP or log_type == LogType.TITLE or any(
                self.waiting_for_header.values()):
            return True
        else:
            return False

    def _combine_header_logs(self, log_type, log_line):
        """Combines header LogLines into single header objects.

        Since LogLines are not typically stored and are simply printed, a flag must be set to absorb
        header loglines use as the borders and the header details.
        """
        formatted_header = None
        curr_type = None
        for header_type, is_waiting in self.waiting_for_header.items():

            # First border of the header
            if log_type == header_type and not is_waiting:
                self.waiting_for_header[header_type] = True

            # Details of border
            elif log_type == LogType.OTHER and is_waiting:
                color = ColorType[header_type.name]
                formatted_header = Header(log_line.original_line, self._calc_max_len(), color)
                curr_type = header_type
                break

            # Last border of header
            elif log_type == header_type and is_waiting:
                self.waiting_for_header[header_type] = False
            else:
                self.waiting_for_header[header_type] = False
        if formatted_header and helpers.str_to_bool(self.sect_display_log_types[curr_type.name.lower()]):

            # Check if finding string
            if self.find_str and not re.search(self.find_str, formatted_header.original_line):
                return None
            return formatted_header
        else:
            return None

    def _remove_fields(self, log_line):
        """Remove field from line if marked not to display.

        :param ValenceLogLine log_line: Log line with fields to be removed
        """
        for field, val in self.sect_display_fields.items():
            if not helpers.str_to_bool(val):
                field = ValenceField[field.upper()]
                log_line.remove_field(field)
        return log_line

    def _condense_fields(self, log_line):
        """Condense and collapse individual line fields to the specified length in format config.

        :param ValenceLogLine log_line: Log line with fields to be removed
        """
        collapse_dict = helpers.str_to_bool(self.sect_collapse_structs["dict"])
        collapse_list = helpers.str_to_bool(self.sect_collapse_structs["list"])
        collapse_len = int(self.format_config[LENGTHS_SECT]["collapsed_struct_len"])
        condense_len = int(self.sect_lengths["condensed_field_len"])

        for field, val in self.sect_condense_fields.items():
            if helpers.str_to_bool(val):
                field = ValenceField[field.upper()]
                log_line.condense_field(field, condense_len, collapse_dict, collapse_list, collapse_len)
        return log_line

    def _update_format_config(self):
        """Updates the format config member dicts if the format config has been updated."""
        current_config_mod_time = os.path.getmtime(self.format_config_filepath)
        if current_config_mod_time > self.format_config_mod_time:
            self._read_vals_from_config_file()
            self.format_config_mod_time = current_config_mod_time

    def _read_vals_from_config_file(self):
        """Reads all of the values from the format .ini file and stores them to the member dicts"""
        self.format_config.read(self.format_config_filepath)
        self.sect_display_log_types = self.format_config[DISPLAY_LOG_TYPES_SECT]
        self.sect_display_fields = self.format_config[DISPLAY_FIELDS_SECT]
        self.sect_condense_fields = self.format_config[CONDENSE_FIELDS_SECT]
        self.sect_collapse_structs = self.format_config[COLLAPSE_STRUCTS_SECT]
        self.sect_lengths = self.format_config[LENGTHS_SECT]

    def _calc_max_len(self):
        """Returns max length of the logline to be printed based on the format config file."""
        if helpers.str_to_bool(self.sect_lengths["use_console_len"]) and sys.stdin.isatty():
            widths_tuple = os.popen('stty size', 'r').read().split()
            if widths_tuple:
                _, console_width = widths_tuple
                return int(console_width)

        return int(self.sect_lengths["max_line_len"])

    def _print_line(self, log_line):
        """Prints str if no write_path specified, otherwise save line to file specific by write_path."""

        log_str = str(log_line)

        if self.write_path:
            with open(self.write_path, "a") as write_file:
                write_file.write(log_str + "\n")
        else:
            print log_str
