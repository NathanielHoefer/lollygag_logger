import os
import re
import sys

from vl_logger import vlogline
from vl_logger.lollygag_logger import LogFormatter
from vl_logger.vutils import VLogType
from vl_logger.vutils import VPatterns
from vl_logger import vlogfield
from vl_logger.vheadermanager import HeaderManager


class VFormatter(LogFormatter):
    """Handle formatting and displaying of VL Logs as they are passed line by line.

    ``VFormatter`` is to be passed in the ``LollygagLogger`` in order to process each VL log line.
    This is done by passing each log line as a raw string into ``format()``,
    which handles the processing of the string.
    The processed string is then returned and is then passed to ``send()`` via ``LollygagLogger``.
    It is then evaluated and printed.

    Processing a log line within ``format()`` includes:
        - Classification (Info log, Suite Header, Traceback, etc.)
        - Condensing log line to specific length
        - Colorization of defined log elements.
    """

    DISPLAY_LOG_TYPES = [
        VLogType.DEBUG,
        VLogType.INFO,
        VLogType.NOTICE,
        VLogType.WARNING,
        VLogType.ERROR,
        VLogType.CRITICAL,
        VLogType.TRACEBACK,
        VLogType.OTHER,
        VLogType.STEP_H,
        VLogType.TEST_CASE_H,
        VLogType.SUITE_H,
        VLogType.GENERAL_H
    ]
    CONSOLE_WIDTH = False
    DISPLAY_TESTCASE_NAME = ""
    DISPLAY_TESTCASE_NUM = -1
    DISPLAY_STEP_NUM = -1
    SUMMARY = False

    def __init__(self):
        """Initializes ``VFormatter``

        :ivar str border_flag: Character type used for the border in the current header.
        :ivar bool traceback_flag: True if currently processing a traceback, otherwise False.
        :ivar str tb_leading_char: Leading characters of the current traceback.
        :ivar bool last_line_empty: Flag indicating if the last log was empty.
        :ivar [str] stored_logs: Cache of log lines that are waiting to be processed.
            Used for mutli-line logs such as tracebacks.
        :ivar VLogType curr_log_type: Stores the current log type.
        :ivar str curr_tc_name: Name of the current test case.
        :ivar int curr_tc_number: Number of the current test case.
        :ivar int curr_step_number: Number of the current step within a test case.
        """
        self.border_flag = ""
        self.traceback_flag = False
        self.tb_leading_char = ""
        self.last_line_empty = False
        self.stored_logs = []
        self.curr_log_type = None

        self.header_man = HeaderManager(tc_name=self.DISPLAY_TESTCASE_NAME,
                                        tc_num=self.DISPLAY_TESTCASE_NUM,
                                        step=self.DISPLAY_STEP_NUM)
        self.prev_fmt_log = None
        self._curr_time = None

        self._set_log_len()

    def format(self, unf_str):
        """Convert raw log line to formatted log line objects.

        :param str unf_str: Unformatted raw string
        :rtype: list(``LogLine``|str|None)
        :returns: ``LogLine`` object if classified
        :returns: Empty str if raw log contains only space characters
        :returns: Non-empty str if raw log not classified.
        :returns: None if log line is not to be printed.
        """
        fmt_logs = []
        if unf_str.isspace():
            fmt_logs.append("")  # Print a blank line
            return fmt_logs

        # Handle multi-line logs: headers and tracebacks
        unf_str = self._handle_raw_header(unf_str.rstrip("\n"))
        self.curr_log_type = VLogType.get_type(unf_str)
        unf_str = self._handle_raw_traceback(unf_str)

        # Discard logs based on type that are not to be displayed
        if self.curr_log_type and self.curr_log_type not in self.DISPLAY_LOG_TYPES:
            # Store Start time
            self._store_curr_time(unf_str)
            self.prev_fmt_log = None
            fmt_logs.append(None)  # Don't print anything
            return fmt_logs

        # Create LogLine objects
        fmt_log = self._create_log_line(unf_str, self.curr_log_type)
        if fmt_log:
            fmt_logs.append(fmt_log)  # Print classified log
            return fmt_logs
        elif self.header_man.in_specified_testcase():
            fmt_logs.append(unf_str)  # Print unclassified log
            return fmt_logs
        return fmt_logs

    def send(self, fmt_logs):
        """Prints each of the formatted logs passed.

        :param list(``LogLine``|str|None) fmt_logs: The formatted log lines after ``format()``.
        """
        for log in fmt_logs:
            if log:
                self.last_line_empty = False
                print log
            elif log == "":
                if not self.last_line_empty:
                    self.last_line_empty = True
                    print ""

    def complete(self):
        """Prints summary if requested."""

        if self.SUMMARY:
            self.header_man.end_time(self.curr_time, root=True)
            print(self.header_man.generate_summary())

    @property
    def curr_time(self):
        return self._curr_time

    @curr_time.setter
    def curr_time(self, curr_datetime):
        self._curr_time = curr_datetime

    @classmethod
    def display_log_types(cls, types):
        """Print only the ``vutils.VLogType`` specified.

        .. code-block:: python

            from vl_logger.vutils import VLogType
            VFormatter.set_display_log_types([VLogType.DEBUG, VLogType.INFO])

        :param [VLogType] types: The enums specifying which logs types to print.
        """
        cls.DISPLAY_LOG_TYPES = types

    @classmethod
    def use_console_width(cls, set=True):
        """Use the console width as the max line width if available."""
        cls.CONSOLE_WIDTH = set

    @classmethod
    def display_test_case(cls, name="", number=-1):
        if name:
            cls.DISPLAY_TESTCASE_NAME = name
        if number >= 0:
            cls.DISPLAY_TESTCASE_NUM = number

    @classmethod
    def display_step(cls, number=-1):
        if number >= 0:
            cls.DISPLAY_STEP_NUM = number

    @classmethod
    def display_summary(cls, set=True):
        cls.SUMMARY = set

    def _store_log(self, unf_str):
        self.stored_logs.append(unf_str)

    def _pull_logs(self):
        logs = "\n".join(self.stored_logs)
        self.stored_logs = []
        return logs

    def _set_log_len(self):
        console_width = 0
        if self.CONSOLE_WIDTH and sys.stdin.isatty():
            widths_tuple = os.popen('stty size', 'r').read().split()
            if widths_tuple:
                _, console_width = widths_tuple
                console_width = int(console_width)
        if console_width:
            vlogline.Base.set_max_line_len(console_width)

    def _create_log_line(self, unf_str, log_type):
        """Create the appropriate VLogLine object based on type.

        :param str unf_str: Unformatted VL log line
        :param VLogType log_type: Type of VLogLine object to create.
        :rtype: LogLine | None
        :returns: VLogLine if unf_str matches pattern of type and is in specified test case, else None
        """
        if not log_type or not unf_str:
            return unf_str

        output = None
        # Standard Log Line
        if log_type in VPatterns.std_log_types() and self.header_man.in_specified_testcase():
            output = vlogline.Standard(unf_str, log_type)

            # Store Start time
            self._store_curr_time(output)
        # Traceback Log Lines
        elif log_type == VLogType.TRACEBACK and self.header_man.in_specified_testcase():
            output = vlogline.Traceback(unf_str)
        # Step Header
        elif log_type == VLogType.STEP_H:
            fmt_log = vlogline.StepHeader(unf_str)
            output = self.header_man.update_current_log(fmt_log)
        # Test Case Header
        elif log_type == VLogType.TEST_CASE_H:
            fmt_log = vlogline.TestCaseHeader(unf_str)
            output = self.header_man.update_current_log(fmt_log)
        # Suite Header
        elif log_type == VLogType.SUITE_H:
            fmt_log = vlogline.SuiteHeader(unf_str)
            output = self.header_man.update_current_log(fmt_log)
        # General Header
        elif log_type == VLogType.GENERAL_H:
            fmt_log = vlogline.GeneralHeader(unf_str)
            output = self.header_man.update_current_log(fmt_log)
        # Other Log Line
        elif log_type == VLogType.OTHER and self.header_man.in_specified_testcase():
            output = vlogline.Other(unf_str)

        if output:
            self.prev_fmt_log = output

        return output

    def _handle_raw_header(self, unf_str):
        """Handle header operations.

        Since headers are contained in multiple lines, the description must be stored.
        The description is then modified as follows and returned.
        They are identified as follows and can be ``=`` or ``-``::

            ============================* (First border)
            <header description>
            ============================* (Second border)

        Modified Header Description::

            <border char><description><border char>
            Ex: '=General Header='

        :rtype: str | None
        :returns: None if unf_str is a border
        :returns: unf_str if unf_str is not part of a header
        :returns: modified header description if unf_str is a header description
        """
        # Border to test case, suite, or general header.
        if re.match("=+", unf_str):
            # Second border
            if self.border_flag == "=":
                self.border_flag = ""
                return self._pull_logs()
            # First border
            else:
                self.border_flag = "="
                return None
        # Border to test case steps
        elif re.match("-+", unf_str):
            # Second border
            if self.border_flag == "-":
                self.border_flag = ""
                return self._pull_logs()
            # First border
            else:
                self.border_flag = "-"
                return None

        # Header details surrounded by borders
        if self.border_flag:
            unf_str = self.border_flag + unf_str + self.border_flag
            self._store_log(unf_str)
            return None
        else:
            return unf_str

    def _handle_raw_traceback(self, unf_log):
        """Handle traceback operations.

        Since tracebacks are contained in multiple lines, the separate elements must be stored.
        They are identified as follows and can be prepended by the same leading characters::

            Traceback (most recent call last):
              File "<file name>", line <line num>, in <func call>
                <line>
              ...
            <exception>: <description>

        Leading characters can be ``!``, ``|>``, etc.

        :rtype: str | list(str) | None
        :returns: unf_str if not part of a traceback
        :returns: None if unf_log is part of traceback but not exception
        :returns: list of log lines gathered from traceback if unf_log is the last line.
        """
        output = ""
        # First line of traceback ('Traceback (most recent call last):')
        if self.curr_log_type == VLogType.TRACEBACK:
            self.tb_leading_char = re.match(VPatterns.get_traceback(), unf_log).group(1)
            self._store_log(unf_log)
            self.traceback_flag = True
            output = None
        # Non-traceback log line
        elif not self.traceback_flag:
            output = unf_log
        # Last line of traceback ('<exception>: <description')
        elif re.match(VPatterns.get_traceback_exception(), unf_log[len(self.tb_leading_char):]):
            output = self.stored_logs
            output.append(unf_log)
            self.curr_log_type = VLogType.TRACEBACK
            self.stored_logs = []
            self.traceback_flag = False
            self.tb_leading_char = ""
        # Inner traceback element
        elif self.curr_log_type == VLogType.OTHER and unf_log:
            self._store_log(unf_log)
            output = None
        return output

    def _store_curr_time(self, log):
        """Store the datetime object of the time from the current log or None if no time available."""
        if self.SUMMARY:
            set_root = False
            if not self.header_man.is_test_start_time_added():
                set_root = True

            if isinstance(log, str):
                pattern = "^(" + VPatterns.get_std_datetime() + ")"
                m = re.match(pattern, log)
                if m.group(1):
                    self._curr_time = vlogfield.Datetime(m.group(1)).get_datetime()
            else:
                self._curr_time = log.datetime.get_datetime()

            if isinstance(self.prev_fmt_log, vlogline.Header) or set_root:
                self.header_man.start_time(self._curr_time, root=set_root)
