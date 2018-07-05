import os
import re
import sys

from vl_logger import vlogline
from vl_logger.lollygag_logger import LogFormatter
from vl_logger.vutils import VLogType
from vl_logger.vutils import VPatterns


class VFormatter(LogFormatter):

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

    def __init__(self):
        self.border_flag = ""
        self.traceback_flag = False
        self.tb_leading_char = ""
        self.last_line_empty = False
        self.stored_logs = []
        self.curr_log_type = None
        self._set_log_len()

    def format(self, unf_str):
        fmt_logs = []
        if unf_str.isspace():
            fmt_logs.append("")  # Print a blank line
            return fmt_logs

        unf_str = self.check_border(unf_str.rstrip("\n"))
        self.curr_log_type = VLogType.get_type(unf_str)
        unf_str = self.check_traceback(unf_str)

        # Discard logs that aren't to be displayed
        if self.curr_log_type and self.curr_log_type not in self.DISPLAY_LOG_TYPES:
            fmt_logs.append(None)  # Don't print anything
            return fmt_logs

        fmt_log = self.create_log_line(unf_str, self.curr_log_type)
        if fmt_log:
            fmt_logs.append(fmt_log)  # Print classified log
            return fmt_logs
        else:
            fmt_logs.append(unf_str)  # Print unclassified log
            return fmt_logs

    def send(self, fmt_logs):
        for log in fmt_logs:
            if isinstance(log, str):  # TODO - Remove when completed with tracebacks
                # print Fore.GREEN + log + Style.RESET_ALL
                print log
            elif log:
                self.last_line_empty = False
                print log
            elif log == "":
                if not self.last_line_empty:
                    self.last_line_empty = True
                    print ""

    def create_log_line(self, unf_str, type):
        """Create the appropriate VLogLine object based on type.

        :param str unf_str: Unformatted VL log line
        :param VLogType type: Type of VLogLine object to create.
        :rtype: Base | None
        :returns: VLogLine if unf_str matches pattern of type, else None
        """
        if not type or not unf_str:
            return unf_str

        fmt_log = None
        if type in VPatterns.std_log_types():
            fmt_log = vlogline.Standard(unf_str, type)
            # if self.is_traceback_log(fmt_log):
            #     self.stored_logs.append(fmt_log)
            #     return None
        elif type == VLogType.TRACEBACK:
            fmt_log = vlogline.Traceback(unf_str)
        elif type == VLogType.SUITE_H:
            fmt_log = vlogline.SuiteHeader(unf_str)
        elif type == VLogType.TEST_CASE_H:
            fmt_log = vlogline.TestCaseHeader(unf_str)
        elif type == VLogType.STEP_H:
            fmt_log = vlogline.StepHeader(unf_str)
        elif type == VLogType.GENERAL_H:
            fmt_log = vlogline.GeneralHeader(unf_str)
        elif type == VLogType.OTHER:
            fmt_log = vlogline.Other(unf_str)
        return fmt_log

    def check_border(self, unf_str):
        """Handle border operations.

        This method will determine what is to be done with borders
        :return: None if initial border or
        """
        if re.match("=+", unf_str):
            if self.border_flag == "=":
                self.border_flag = ""
                return self._pull_logs()
            else:
                self.border_flag = "="
                return None
        elif re.match("-+", unf_str):
            if self.border_flag == "-":
                self.border_flag = ""
                return self._pull_logs()
            else:
                self.border_flag = "-"
                return None

        # Header details
        if self.border_flag:
            unf_str = self.border_flag + unf_str + self.border_flag
            self._store_log(unf_str)
            return None
        else:
            return unf_str

    def check_traceback(self, unf_log):
        """Handle traceback operations."""
        if self.curr_log_type == VLogType.TRACEBACK:
            self.tb_leading_char = re.match(VPatterns.get_traceback(), unf_log).group(1)
            self._store_log(unf_log)
            self.traceback_flag = True
            return None
        elif not self.traceback_flag:
            return unf_log
        elif re.match(VPatterns.get_traceback_exception(), unf_log[len(self.tb_leading_char):]):
            output = self.stored_logs
            output.append(unf_log)
            self.curr_log_type = VLogType.TRACEBACK
            self.stored_logs = []
            self.traceback_flag = False
            self.tb_leading_char = ""
            return output
        elif self.curr_log_type == VLogType.OTHER and unf_log:
            self._store_log(unf_log)
            return None

    @classmethod
    def display_log_types(cls, types):
        """Print only the ``VLogType``s specified.

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
            vlogline.Base.set_max_line_len(console_width)  # TODO - Use interface when created
