import os
import re
import sys

from vl_logger import vlogline
from vl_logger.lollygag_logger import LogFormatter
from vl_logger.vutils import VLogType
from vl_logger.vutils import VPatterns
from vl_logger import vlogfield
from vl_logger.vmanagers import HeaderManager, LogManager


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

    def __init__(self, config_interface):
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
        self.last_line_empty = False

        # Traceback and Header member variables
        self.stored_logs = []  # Temp location for header and traceback lines
        self.border_flag = ""
        self.traceback_flag = False
        self.tb_leading_char = ""

        self._hm = HeaderManager(tc_name=self.DISPLAY_TESTCASE_NAME,
                                 tc_num=self.DISPLAY_TESTCASE_NUM,
                                 step=self.DISPLAY_STEP_NUM)
        self._lm = LogManager(display_log_types=self.DISPLAY_LOG_TYPES)
        self._config_interface = config_interface

        self._prev_fmt_log = None
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
        if unf_str.isspace():
            self._lm.enqueue_log("")  # Print a blank line
            return self._lm.flush_logs()

        # Handle multi-line logs: headers and tracebacks
        unf_str = self._handle_raw_header(unf_str.rstrip("\n"))
        self._lm.calc_log_type(unf_str)
        unf_str = self._handle_raw_traceback(unf_str)

        # Discard logs based on type that are not to be displayed
        if not self._display_log(unf_str):
            return []  # Don't print anything

        # Create LogLine objects
        fmt_log = self._create_log_line(unf_str, self._lm.curr_log_type)
        if fmt_log:
            self._lm.enqueue_log(fmt_log)  # Print classified log
        elif self._hm.std_log_in_specified_testcase():
            self._lm.enqueue_log(unf_str)  # Print unclassified log
        return self._lm.dequeue_logs()

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

        # Print any remaining logs
        self.send(self._lm.flush_logs())

        if self.SUMMARY:
            try:
                self._hm.end_time(self.curr_time, root=True)
                summary = self._hm.generate_summary()
                print
                print summary
            # except AttributeError:
            except:
                print "Error generating summary. Log may be incomplete."

    @property
    def curr_time(self):
        return self._curr_time

    @property
    def config_interface(self):
        return self._config_interface

    @config_interface.setter
    def config_interface(self, config):
        self._config_interface = config

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
    def use_console_width(cls, value=True):
        """Use the console width as the max line width if available."""
        cls.CONSOLE_WIDTH = value

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
    def display_summary(cls, value=True):
        cls.SUMMARY = value

    def _store_log(self, unf_str):
        self.stored_logs.append(unf_str)

    def _pull_logs(self):
        logs = "\n".join(self.stored_logs)
        self.stored_logs = []
        return logs

    def _display_log(self, unf_str):
        """Return True if the log is specified to be displayed, else False."""
        if not self._lm.display_current_log():
            self._store_curr_time(unf_str)
            self._prev_fmt_log = None
            return False
        else:
            return True

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
        if log_type in VPatterns.std_log_types() and self._hm.std_log_in_specified_testcase():
            output = vlogline.Standard(unf_str, log_type)

            # Store Start time
            self._store_curr_time(output)

            # Associate Error with Header
            if self.SUMMARY and output and output.logtype == VLogType.ERROR:
                self._hm.add_error(output)
        # Traceback Log Lines
        elif log_type == VLogType.TRACEBACK and self._hm.std_log_in_specified_testcase():
            output = vlogline.Traceback(unf_str)
        # Step Header
        elif log_type == VLogType.STEP_H:
            fmt_log = vlogline.StepHeader(unf_str)
            output = self._hm.update_current_log(fmt_log)
        # Test Case Header
        elif log_type == VLogType.TEST_CASE_H:
            fmt_log = vlogline.TestCaseHeader(unf_str)
            output = self._hm.update_current_log(fmt_log)
        # Suite Header
        elif log_type == VLogType.SUITE_H:
            fmt_log = vlogline.SuiteHeader(unf_str)
            output = self._hm.update_current_log(fmt_log)
        # General Header
        elif log_type == VLogType.GENERAL_H:
            fmt_log = vlogline.GeneralHeader(unf_str)
            output = self._hm.update_current_log(fmt_log)
        # Other Log Line
        elif log_type == VLogType.OTHER and self._hm.std_log_in_specified_testcase():
            output = vlogline.Other(unf_str)

        if output:
            self._prev_fmt_log = output

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
        if re.match("={105}", unf_str):
            # Second border
            if self.border_flag == "=":
                self.border_flag = ""
                return self._pull_logs()
            # First border
            else:
                self.border_flag = "="
                return None
        # Border to test case steps
        elif re.match("-{105}", unf_str):
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
        if self._lm.curr_log_type == VLogType.TRACEBACK:
            self._lm.hold = True
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
            self._lm.curr_log_type = VLogType.TRACEBACK
            self.stored_logs = []
            self.traceback_flag = False
            self.tb_leading_char = ""
            self._lm.hold = False
        # Inner traceback element
        elif self._lm.curr_log_type == VLogType.OTHER and unf_log:
            self._store_log(unf_log)
            output = None
        # Traceback doesn't meet vl specifications
        elif self._lm.curr_log_type:
            self._lm.enqueue_log(self._pull_logs())
            self._lm.hold = False
            output = unf_log
        return output

    def _store_curr_time(self, log):
        """Store the datetime object of the time from the current log or None if no time available."""
        if self.SUMMARY:
            set_root = False
            if not self._hm.is_test_start_time_added():
                set_root = True

            if isinstance(log, str):
                pattern = "^(" + VPatterns.get_std_datetime() + ")"
                m = re.match(pattern, log)
                if m and m.group(1):
                    self._curr_time = vlogfield.Datetime(m.group(1)).datetime
            else:
                self._curr_time = log.datetime

            if isinstance(self._prev_fmt_log, vlogline.Header) or set_root:
                self._hm.start_time(self._curr_time, root=set_root)

    def parse_test_case(self, log_file, tc_name=None, tc_num=None):
        """Parses test case logs from a log file.

        The specified test case logs are placed into a file labelled with the tc info,
        and the file will be located in a directory labelled tc_logs in the same directory as the
        log file.
        If the file already exists, the method will return.

        Example::

            parse_test_case("~/logs/test.log", tc_name="TcExample")

            # File location
            ~/logs/tc_logs/TcExample.log

        :param str log_file: Filepath of log file to be parsed.
        :param str tc_name: Name of test case to be parsed, will supercede tc_num if specified
        :param int tc_num: Number of test case to be parsed.
        :returns: String filepath to parsed log file.
        """

        dir = os.path.dirname(log_file)
        tc_dir = os.path.join(dir, "tc_logs")
        if not os.path.exists(tc_dir):
            os.mkdir(tc_dir)
        tc_filename = "%s.log" % (tc_name) if tc_name else ("Tc-%d.log" % (tc_num))
        tc_file = os.path.join(tc_dir, tc_filename)
        if os.path.exists(tc_file):
            return tc_file
        else:
            open(tc_file, "w").close()

        step_regex = VPatterns.get_step_header()
        tc_regex = VPatterns.get_test_case_header()
        suite_regex = VPatterns.get_suite_header()
        general_regex = VPatterns.get_general_header()
        in_specified_tc = False
        completed_specified_tc = False

        with open(log_file) as original_file:
            for line in original_file:
                line = self._handle_raw_header(line.rstrip("\n"))
                if line is None:
                    continue

                tc_match = re.match(tc_regex, line)
                step_match = re.match(step_regex, line)
                header_match = re.match("".join([suite_regex, "|", general_regex]), line)

                # Line is test case
                if tc_match:
                    tc = vlogline.TestCaseHeader(line)

                    # TC name matches current line
                    if tc_name and tc_name == tc.test_case_name:
                        in_specified_tc = True
                    # TC number matches current line
                    elif tc_num >= 0 and tc_num == tc.number:
                        in_specified_tc = True
                    # New TC is reached
                    elif in_specified_tc:
                        completed_specified_tc = True
                        in_specified_tc = False

                    if in_specified_tc:
                        with open(tc_file, "a") as f:
                            f.write(str(tc) + "\n")

                # Line is a step header
                elif step_match and in_specified_tc:
                    step = vlogline.StepHeader(line)
                    with open(tc_file, "a") as f:
                        f.write(str(step) + "\n")

                # New General or Suite header found to signal end of specified test case
                elif header_match and in_specified_tc:
                    completed_specified_tc = True

                # Logs in specified test case
                elif in_specified_tc:
                    with open(tc_file, "a") as f:
                        f.write(str(line) + "\n")

                if completed_specified_tc:
                    return tc_file
        return tc_file

    def parse_step(self, tc_log_file, step_num):
        """Parses step logs from a test case log file.

        The specified step logs are placed into a file labelled with the step info,
        and the file will be located in a directory labelled tc_logs in the same directory as the
        log file.
        If the file already exists, the method will return.

        Example::

            parse_step("~/logs/tc_logs/TcExample.log", step=0)

            # File location
            ~/logs/tc_logs/TcExample_Step-0.log

        :param str tc_log_file: Filepath of log file to be parsed.
        :param int step_num: Number of step to be parsed.
        """

        tc_dir = os.path.dirname(tc_log_file)
        tc_filename = re.search("(Tc-?\w+).log", tc_log_file)
        step_filename = "%s_Step-%d.log" % (tc_filename.group(1), step_num)
        step_file = os.path.join(tc_dir, step_filename)
        if os.path.exists(step_file):
            return step_file
        else:
            open(step_file, "w").close()

        step_regex = VPatterns.get_step_header()
        in_specified_step = False
        completed_specified_step = False

        with open(tc_log_file) as original_file:
            for line in original_file:
                line = self._handle_raw_header(line.rstrip("\n"))
                if line is None:
                    continue

                step_match = re.match(step_regex, line)

                # Line is test case
                if step_match:
                    step = vlogline.StepHeader(line)

                    # TC name matches current line
                    if step_num == step.number:
                        in_specified_step = True
                    # New TC is reached
                    elif in_specified_step:
                        completed_specified_step = True
                        in_specified_step = False

                    if in_specified_step:
                        with open(step_file, "a") as f:
                            f.write(str(step) + "\n")

                # Logs in specified test case
                elif in_specified_step:
                    with open(step_file, "a") as f:
                        f.write(str(line) + "\n")

                if completed_specified_step:
                    return step_file
        return step_file
