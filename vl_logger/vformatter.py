from vl_logger.lollygag_logger import LogFormatter
from vl_logger import vlogline
from vl_logger.vutils import VLogType
from vl_logger.vutils import VPatterns
import re

class VFormatter(LogFormatter):

    def __init__(self):
        self.border_flag = ""
        self.stored_logs = []

    def format(self, unf_str):

        if unf_str.isspace():
            return ""

        unf_str = self.check_border(unf_str.strip())

        type = VLogType.get_type(unf_str)

        fmt_log = self.create_log_line(unf_str, type)
        if fmt_log:
            return fmt_log
        else:
            return unf_str

    def send(self, fmt_log):

        if fmt_log:
            print fmt_log
        elif fmt_log == "":
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
            if self.border == "=":
                self.border = ""
                return self._pull_logs()
            else:
                self.border = "="
                return None
        elif re.match("-+", unf_str):
            if self.border == "-":
                self.border = ""
                return self._pull_logs()
            else:
                self.border = "-"
                return None

        # Header details
        if self.border:
            unf_str = self.border + unf_str + self.border
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