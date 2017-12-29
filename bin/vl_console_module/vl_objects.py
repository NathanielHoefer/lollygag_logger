"""
=========================================================================================================
Valence Config File Methods and Constants
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/2/2017
"""
import datetime
import re
from bin.lollygag_logger import LogLine
from enums import *
import helpers


class ValenceLogLine(LogLine):
    """Stores log line into its various fields per the vl logging.

    Lines with all fields matching with the exception of the details token missing will still be
    considered in standard format. If any other field doesn't match, all of the fields are returned
    to normal, and the type is considered OTHER with the original line being retained.

    # Since date, time, and type are represented objects, the field contains a list where

    STEP and TITLE types are unique in that the line is stored in the details

    :cvar list LOG_LEVELS: The unique log levels specified by Valence
    :cvar list FIELDS: The unique sections found within a Valence log in standard format
    :cvar int TOKEN_COUNT: The number of fields
    """

    VALENCE_TOKEN_COUNT = len(ValenceField)
    AT2_TOKEN_COUNT = VALENCE_TOKEN_COUNT - 1

    def __init__(self, original_line="", max_len=300):
        super(ValenceLogLine, self).__init__(original_line)
        self.max_len = max_len
        self._default_vals()
        self._tokenize_line(original_line)

    def __str__(self):
        """Returns fields as strings if they have not been removed and the log line is in standard
        format, otherwise the original line is returned."""
        if self.standard_format:
            field_strings = self._list_all_field_strings()
            str_output = " ".join([field for field in field_strings if field is not None])
        else:
            str_output = self.original_line
        return helpers.condense(str_output, self.max_len)

    def set_field_str(self, field, value):
        """Sets the string value of a field

        Note: Currently does not change the datetime objects or ValenceField enum. They need to be set
        individually using self.time[0] = ...

        :param ValenceField field: The field to be set
        :param str value: The string that the field will be set to. Can also be None.
        """

        # Change str value in field list
        if field == ValenceField.DATE or field == ValenceField.TIME or field == ValenceField.TYPE:
            field_list = getattr(self, field.value)
            field_list[1] = value
            setattr(self, field.value, field_list)
        else:
            setattr(self, field.value, value)

    def get_field_str(self, field):
        """Returns the string of any of the Valence fields.

        :param ValenceField field: The field to retrieve string
        :return: The string value in that field or None if that is the current value assigned.
        """
        field_value = getattr(self, field.value)
        if field_value is None:
            return None

        if field == ValenceField.DATE or field == ValenceField.TIME or field == ValenceField.TYPE:
            field_list = field_value
            return field_list[1]
        else:
            return field_value

    def get_log_type(self):
        """Returns the LogType."""
        return self.type[0] if self.type else None

    def color_field(self, field, color):
        """Colors the field str using the specified ANSI escape color sequence."""

        field_value = self.get_field_str(field)
        if field_value is not None:
            field_value = color.value + field_value + ColorType.END.value
            self.set_field_str(field, field_value)

    def remove_field(self, field):
        """Set the specified field to None.

        :param ValenceField field: Field to be set to None
        """
        setattr(self, field.value, None)

    def condense_field(self, field, condense_len=50, collapse_dict=False, collapse_list=False,
                       collapse_len=30):
        """Condenses the field to the condense length, and collapses lists and dictionaries that
        exceed a given length.

        :param ValenceField field: The LogLine field str to be condensed.
        :param int condense_len: The max length of the field
        :param bool collapse_dict: If true, collapse dict to the specified collapse_len
        :param bool collapse_list: If true, collapse list to the specified collapse_len
        :param int collapse_len: The max length of the structures
        """
        current_field_str = getattr(self, field.value)
        if current_field_str is None:
            return

        # Collapse dicts or lists if specified
        if collapse_dict:
            current_field_str = helpers.collapse_struct(current_field_str, "dict", collapse_len)
        if collapse_list:
            current_field_str = helpers.collapse_struct(current_field_str, "list", collapse_len)

        # Condense length of element if it exceeds specified length
        setattr(self, field.value, helpers.condense(current_field_str, condense_len))

    def _default_vals(self):
        """Set all field to default values."""
        self.date = None
        self.time = None
        self.type = [LogType.OTHER, LogType.OTHER.value]
        self.source = None
        self.thread = None
        self.details = None
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
            self.type[0] = LogType.TITLE
            self.type[1] = LogType.TITLE.value
            return
        if re.match("^-{30,}$", input_str):
            self.type[0] = LogType.STEP
            self.type[1] = LogType.STEP.value
            return

        # Identifies if the log is int AT2 standard format based on the format of the time stamp. AT2
        # logs don't include the thread field, so determine token count if in AT2 format.
        if re.search("\d{2}:\d{2}:\d{2},\d{3}", input_str):
            self.at2_log = True
            current_token_count = self.AT2_TOKEN_COUNT
        else:
            current_token_count = self.VALENCE_TOKEN_COUNT

        # Check to see if there are the expected number of tokens in the line. If not, then mark as a
        # non-standard vl format, and return.
        split = input_str.split(" ", current_token_count - 1)
        if not (current_token_count - 1 <= len(split) <= current_token_count):
            return

        # Parse Date
        # Create datetime object for date and assign str to 2nd index
        date = self._str_to_date(split[0]) if re.match("^\d{4}-\d{2}-\d{2}$", split[0]) else None
        if date is None:
            self.date = None
        else:
            date_values = [date, split[0]]
            self.date = date_values

        # Parse Time
        # Check to see if logs are in valence format or AT2 format based on time then create datetime
        # object for time and assign str to 2nd index
        if re.match("^\d{2}:\d{2}:\d{2}\.\d{6}$", split[1]) \
                or re.match("^\d{2}:\d{2}:\d{2},\d{3}$", split[1]):
            time_values = [self._str_to_time(split[1]), split[1]]
            self.time = time_values
        else:
            self.time = None

        # Parse Type
        # Assign LogType enum to first index and the str representation to the 2nd index.
        if split[2] in [x.name for x in LogType]:
            self.type[0] = LogType[split[2]]
            self.type[1] = str(self.type[0])

        # Parse Source
        self.source = split[3] if re.match("^\[.*:.*\]$", split[3]) else None

        # Parse Thread and Detail
        if self.at2_log:  # Special case to check if logs are being read from AT2 based on time stamp
            self.details = split[4] if len(split) == self.AT2_TOKEN_COUNT else None
        else:
            self.thread = split[4] if re.match("^\[.*:.*\]$", split[4]) else None
            self.details = split[5] if len(split) == self.VALENCE_TOKEN_COUNT else None

        # If any of the fields are empty with the exception of details, change type to OTHER and move all
        # line data to the details field.
        for field in ValenceField:
            if self.at2_log:
                if (field is not ValenceField.DETAILS and field is not ValenceField.THREAD)\
                        and getattr(self, field.value) is None:
                    self._default_vals()
                    return
            else:
                if field is not ValenceField.DETAILS and getattr(self, field.value) is None:
                    self._default_vals()
                    return
        self.standard_format = True

    def _list_all_field_strings(self):
        """Returns list of all field values as strings. If a value is None, then it has been removed."""
        return [self.get_field_str(field) for field in ValenceField]

    def _str_to_date(self, date_str):
        """Converts date str to a datetime object if in the following format: YYYY-MM-DD

        :param str date_str: String representind the date
        :return: datetime object if str formatted correctly, else None
        """
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return date if date else None

    def _str_to_time(self, time_str):
        """Converts time str to a datetime object if in the following format:
            HH:MM:SS.FFFFFF or HH:MM:SS,FFF if reading from AT2 log

        :param str time_str: String representing the time
        :return: datetime object if str formatted correctly, else None
        """
        if self.at2_log:
            time = datetime.datetime.strptime(time_str, "%H:%M:%S,%f")
        else:
            time = datetime.datetime.strptime(time_str, "%H:%M:%S.%f")
        return time if time else None


class ValenceHeader(LogLine):
    """Stores the Valence header and its individual tokens and identifies its type.

    A header is either identified by '=', or '-'. Looks for a colon-separated header for parsing the
    line, otherwise the empty values will be used for all but the original line member variable.

    :ivar str original_line: The line as it was entered
    :ivar HeaderType type: Type of header
    :ivar str test_name: Name of the test case or suite following the 'Ts' or 'Tc' format.
    :ivar str test_info: Information prior to the colon
    :ivar str test_instruction: Information after the colon
    :ivar int test_number: Step or test case number if there is one.
    """

    def __init__(self, original_line="", max_len=105, color=None):
        super(ValenceHeader, self).__init__(original_line)
        self.max_len = max_len
        self.color = color
        self._default_vals()
        self._tokenize_line(original_line)

    def __str__(self):
        border = "="*self.max_len if self.type.value <= 3 else "-"*self.max_len
        if not self.original_line:
            str_output = ""
        else:
            str_output = "\n".join([border, self.original_line, border])

        if self.color:
            str_output = self.color.value + str_output + ColorType.END.value
        return str_output

    def _default_vals(self):
        """Set all field to default values."""
        self.type = HeaderType.VALENCE
        self.test_name = None
        self.test_info = None
        self.test_instruction = None
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
            self.original_line = ""
            return

        self.test_info = split[0].strip() if len(split) == 2 else None
        self.test_instruction = split[1].strip() if len(split) == 2 else None

        if self.test_info == "Test Suite":
            self.type = HeaderType.SUITE
            self.test_name = re.search("Ts\w*", self.original_line).group()
        elif re.match("^Test Case \d+$", self.test_info):
            self.type = HeaderType.TEST_CASE
            self.test_name = re.search("Tc\w*", self.original_line).group()
            self.test_number = int(re.search("\d+", self.test_info).group())
        elif re.search("Step \d+", self.test_info):
            self.type = HeaderType.STEP
            self.test_name = re.search("Tc\w*", self.original_line).group()
            self.test_number = int(re.search("\d+", self.test_info).group())
        else:
            self._default_vals()
            return
