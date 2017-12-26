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
from bin.lollygag_logger import LogFormatter
from vl_objects import ValenceHeader as Header
from enums import ColorType
from vl_config_file import *

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


class ValenceConsoleFormatter(LogFormatter):
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
                formatted_header = Header(self.log_line.original_line, header_type,
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
                self.executed_suites[self.current_suite_index][self.current_test_case_index]\
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
