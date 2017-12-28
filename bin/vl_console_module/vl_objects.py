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

    STEP and TITLE types are unique in that the line is stored in the details

    :cvar list LOG_LEVELS: The unique log levels specified by Valence
    :cvar list FIELDS: The unique sections found within a Valence log in standard format
    :cvar int TOKEN_COUNT: The number of fields
    """

    LOG_LEVELS = ["debug", "info", "warning", "error"]  # Temp until enum working
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
        """Returns the log line string with the log type surrounded by an ANSI escape color sequence."""
        if self.standard_format:
            fields = self._list_fields_as_str()
            fields[2] = helpers.color_by_type(self.type, fields[2])
            fields = [x for x in fields if x != ""]
        else:
            fields = [helpers.color_by_type(self.type, self.original_line)]
        return " ".join(fields)

    def _default_vals(self):
        """Set all field to default values."""
        self.date = ""
        self.time = ""
        self.type = LogType.OTHER
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
            self.type = LogType.TITLE
            return
        if re.match("^-{30,}$", input_str):
            self.type = LogType.STEP
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

        # Assign token to proper field if format matches correctly
        self.date = split[0] if re.match("^\d{4}-\d{2}-\d{2}$", split[0]) else ""
        self._str_to_date()

        # Check to see if logs are in valence format or AT2 format based on time
        if re.match("^\d{2}:\d{2}:\d{2}\.\d{6}$", split[1]) \
                or re.match("^\d{2}:\d{2}:\d{2},\d{3}$", split[1]):
            self.time = split[1]
            self._str_to_time()
        else:
            self.time = ""

        str_type = split[2]
        if str_type in [x.name for x in LogType]:
            self.type = LogType[str_type]

        self.source = split[3] if re.match("^\[.*:.*\]$", split[3]) else ""

        if self.at2_log:  # Special case to check if logs are being read from AT2 based on time stamp
            self.details = split[4] if len(split) == self.AT2_TOKEN_COUNT else ""
        else:
            self.thread = split[4] if re.match("^\[.*:.*\]$", split[4]) else ""
            self.details = split[5] if len(split) == self.VALENCE_TOKEN_COUNT else ""

        # If any of the fields are empty with the exception of details, change type to OTHER and move all
        # line data to the details field.
        for field in ValenceFields:
            if self.at2_log:
                if (field is not ValenceFields.DETAILS and field is not ValenceFields.THREAD)\
                        and getattr(self, field.value) is "":
                    self._default_vals()
                    return
            else:
                if field is not ValenceFields.DETAILS and getattr(self, field.value) is "":
                    self._default_vals()
                    return
        self.standard_format = True

    def _list_fields_as_str(self):
        str_fields_list = [getattr(self, field.value) for field in ValenceFields]
        str_fields_list[0] = self._date_to_str()
        str_fields_list[1] = self._time_to_str()
        str_fields_list[2] = str(str_fields_list[2])
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

    def __init__(self, original_line="", max_len=105):
        super(ValenceHeader, self).__init__(original_line)
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
        self.type = HeaderType.VALENCE
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
