from vl_logger.lollygag_logger import LogFormatter
from vl_logger import vlogline
from vl_logger.vutils import VLogType
from vl_logger.vutils import VPatterns
import re
import sys
import os
from colorama import Fore, Back, Style


class VFormatter(LogFormatter):

    DISPLAY_LOG_TYPES = [
        # VLogType.DEBUG,
        VLogType.INFO,
        VLogType.NOTICE,
        VLogType.WARNING,
        VLogType.ERROR,
        VLogType.CRITICAL,
        VLogType.OTHER,
        VLogType.STEP_H,
        VLogType.TEST_CASE_H,
        VLogType.SUITE_H,
        VLogType.GENERAL_H
    ]

    def __init__(self):
        self.border_flag = ""
        self.last_line_empty = False
        self.stored_logs = []
        self._set_log_len()

    def format(self, unf_str):
        fmt_logs = []
        if unf_str.isspace():
            fmt_logs.append("")
            return fmt_logs

        unf_str = self.check_border(unf_str.rstrip("\n"))
        type = VLogType.get_type(unf_str)

        # Discard logs that aren't to be displayed
        if type and type not in self.DISPLAY_LOG_TYPES:
            fmt_logs.append(None)
            return fmt_logs

        fmt_log = self.create_log_line(unf_str, type)
        if fmt_log:
            fmt_logs.append(fmt_log)
            return fmt_logs
        else:
            fmt_logs.append(unf_str)
            return fmt_logs

    def send(self, fmt_logs):
        for log in fmt_logs:
            if isinstance(log, str):  # TODO - Remove when completed with tracebacks
                print Fore.GREEN + log + Style.RESET_ALL
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
        elif type == VLogType.SUITE_H:
            fmt_log = vlogline.SuiteHeader(unf_str)
        elif type == VLogType.TEST_CASE_H:
            fmt_log = vlogline.TestCaseHeader(unf_str)
        elif type == VLogType.STEP_H:
            fmt_log = vlogline.StepHeader(unf_str)
        elif type == VLogType.GENERAL_H:
            fmt_log = vlogline.GeneralHeader(unf_str)
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

    def _store_log(self, unf_str):
        self.stored_logs.append(unf_str)

    def _pull_logs(self):
        logs = "\n".join(self.stored_logs)
        self.stored_logs = []
        return logs

    def _set_log_len(self):
        console_width = 0
        if sys.stdin.isatty():
            widths_tuple = os.popen('stty size', 'r').read().split()
            if widths_tuple:
                _, console_width = widths_tuple
                console_width = int(console_width)
        if console_width:
            vlogline.Base.set_max_line_len(console_width)  # TODO - Use interface when created
