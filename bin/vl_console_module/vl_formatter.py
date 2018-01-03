"""
=========================================================================================================
Valence Console Formatter Class
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/30/2017
"""

import sys
import helpers
import re
from bin.lollygag_logger import LogFormatter
from bin.lollygag_logger.lollygag_logger import KILL_SIGNAL
from vl_objects import ValenceHeader as Header
from enums import LogType, ValenceField, ColorType, ListingStatus
from vl_config_file import *

WRITE_UPDATE_INCREMENT = 10


class ValenceConsoleFormatter(LogFormatter):
    """Class containing log line format functions to be passed into the LollygagLogger.

    This class uses a LogLine object to format it and then print it to the console or write it to a
    file. Settings are specified via a .ini file which include the following:
     - which log types to display
     - which log fields to display
     - which log fields to condense
     - whether to collapse lists or dicts
     - whether to use console length for max log line size, or a specified size
     - the condensed field length and collapsed struct length
     - whether to use colors

    :ivar log_line_cls: the LogLine class used to parse the unformatted log lines
    :ivar format_config: the configparser that contains all of the user options
    :ivar ini_filepath: the directory of where to look for the .ini config file.
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

        if self.find_str or self.list_step:
            self.listed_steps_status = ListingStatus.SEARCHING
            self.searching_text_printed = False
        else:
            self.listed_steps_status = ListingStatus.PROCESSING
            self.searching_text_printed = True

    def format(self, unformatted_log_line):
        """Creates and formats the LogLine object, handling any formatting options.

        Current order of formatting:
        1. Create LogLine object
        2. Check to see if finding string
        3. Store last log time
        4. Update format_config if it has been updated
        5. Construct header object
        6. Skip line if not marked for print
        7. Remove and condense fields in standard format
        8. Add color to type field

        :return: Formatted ValenceLogLine | Formatted ValenceHeader | None if not to print
        """

        # TODO - Handle KeyError for incorrect config file

        # Strip log line string and use it to create the log_line object
        line = unformatted_log_line.strip("\n\\n")
        log_line = self.log_line_cls(line, self._calc_max_len())

        # Only print the logs with the desired substrings and highlight the substring.
        # Note: If substring is within condensed portion or removed field, the log will still print,
        # but without the highlighting.
        if self.find_str:
            if re.search(re.escape(self.find_str), log_line.original_line):
                self._highlight_line(log_line)
            else:
                return None

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
                log_line = formatted_header

        # Skip line if type is marked to not display
        log_type = log_line.get_log_type().name.lower()
        if not helpers.str_to_bool(self.sect_display_log_types[log_type]):
            return None

        # Don't print if not in the current step
        if self.list_step and not self.listed_step_to_print:
            return None

        # Remove and condense fields in standard logs per format config file
        if type(log_line) == self.log_line_cls and log_line.standard_format:
            log_line = self._remove_fields(log_line)
            log_line = self._condense_fields(log_line)

        # Add color to the type field and convert log line to string
        if helpers.str_to_bool(self.format_config[COLORS]["use_colors"]):
            color = ColorType[log_line.get_log_type().name]
            if type(log_line) == self.log_line_cls:
                log_line.color_field(ValenceField.TYPE, color)
            elif type(log_line) == Header:
                log_line.color_header(color)

        return log_line

    def send(self, formatted_log_line):
        """Either prints formatted line to console or write it to file based on write flag.

        If writing to a file, will print to screen number of lines written. Also, prevents multiple
        blank lines from being printed in a row. Also condenses LogLine string if specified in .ini file.

        :param ValenceLogLine | ValenceHeader formatted_log_line: Formatted log line | None - indicating
            to not print line.
        :return: ValenceLogLine if formatted | KILL_SIGNAL if LollygagLogger is to be killed before
        completion | None
        """

        # Increase lines read count and print update if writing to a file
        self.log_lines_read += 1
        if self.write_path and self.log_lines_read % WRITE_UPDATE_INCREMENT == 0:
            print "Lines Read: {0}\r".format(self.log_lines_read),
            sys.stdout.flush()

        # Print searching message until step has been found
        if self.listed_steps_status == ListingStatus.SEARCHING:

            search_text = ""
            if self.find_str:
                search_text = "Searching for string: \"{0}\"\n".format(self.find_str)
            elif self.list_step:
                search_text = "Searching for Test Case/Step: {0}\n".format(self.list_step)

            if not self.searching_text_printed:
                print search_text
                self.searching_text_printed = True
            else:
                print ("---   \r" if self.log_lines_read % 100 < 50 else "   ---\r"),

        # Update status when log line is sent through
        if formatted_log_line is None:
            return None
        else:
            self.listed_steps_status = ListingStatus.PROCESSING

        # Check to see if multiple blank lines are being printed
        if formatted_log_line.original_line == "" and not self.duplicate_blank_line:
            self.duplicate_blank_line = True
        elif formatted_log_line.original_line == "" and self.duplicate_blank_line:
            return None
        elif formatted_log_line is not None:
            self.duplicate_blank_line = False

        self._print_line(formatted_log_line)

        # Kill program when listed steps have been processed.
        if self.listed_steps_status == ListingStatus.COMPLETED:
            return KILL_SIGNAL
        else:
            return None

    def _highlight_line(self, log_line):
        """Highlights the find_str within the log_line."""
        replace_str = ColorType.HIGHLIGHT.value + self.find_str + ColorType.END.value

        if log_line.standard_format:
            for field in ValenceField:
                field_str = log_line.get_field_str(field)
                if field_str is not None:
                    field_str = field_str.replace(self.find_str, replace_str)
                    log_line.set_field_str(field, field_str)
        else:
            log_line.original_line = log_line.original_line.replace(self.find_str, replace_str)
        return log_line

    def _handle_header(self, log_line):
        """Determines if LogLine is part of header and handles combining and formatting the header.

        :param ValenceLogLine log_line: Log line that is checked for header status
        :return: True if LogLine was part of a header, but not to be printed | False if LogLine is not
        part of header | ValenceHeader if LogLine is to be printed and part of header
        """
        log_type = log_line.get_log_type()
        header_line = self._combine_header_logs(log_type, log_line)

        if header_line:

            # Check if header matches step to list
            if header_line.original_line == self.list_step:
                self.listed_step_to_print = True
                self.listed_step_type = header_line.header_type

            # Return without printing if a specified step to print and this isn't part of it
            if self.list_step and not self.listed_step_to_print:
                return True

            # Uncheck 'selected step' flag once the next step is hit if a step is selected or the next
            # test case step is hit if test case is selected.
            if self.listed_step_type:
                if self.listed_step_type.value >= header_line.header_type.value \
                        and header_line.original_line != self.list_step \
                        and header_line.original_line != "":
                    self.listed_step_to_print = False
                    self.listed_steps_status = ListingStatus.COMPLETED
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

        :param LogType log_type: The current type of the LogLine
        :param ValenceLogLine log_line: The log line to determine if header
        :return: ValenceHeader if the log line is the description line of the header | None
        """
        formatted_header = None
        for header_type, is_waiting in self.waiting_for_header.items():

            # First border of the header
            if log_type == header_type and not is_waiting:
                self.waiting_for_header[header_type] = True

            # Details of border
            elif log_type == LogType.OTHER and is_waiting:
                formatted_header = Header(log_line.original_line, self._calc_max_len())
                break

            # Last border of header
            elif log_type == header_type and is_waiting:
                self.waiting_for_header[header_type] = False
            else:
                self.waiting_for_header[header_type] = False

        return formatted_header if formatted_header else None

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

        :param ValenceLogLine log_line: Log line with fields to be condensed
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
        if helpers.str_to_bool(self.format_config[COLORS]["use_colors"]):
            log_str = str(log_line) + ColorType.END.value
        else:
            log_str = str(log_line)

        if self.write_path:
            with open(self.write_path, "a") as write_file:
                write_file.write(log_str + "\n")
        else:
            print log_str
