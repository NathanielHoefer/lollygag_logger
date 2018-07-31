"""Module containing VL Utility classes and functions."""

import re
import time
import sys
import os

from enum import Enum
from colorama import Fore, Back, Style

"""
Different conditions of tracebacks:
1. EOF: Starts with '|!!! Exception Occurred:


"""

class VLogType(Enum):
    """Enums representing the types of log lines."""

    DEBUG = 'DEBUG'
    INFO = 'INFO '
    NOTICE = 'NOTE '
    WARNING = 'WARN '
    ERROR = 'ERROR'
    CRITICAL = 'CRIT '
    TRACEBACK = 'TRACEBACK'
    OTHER = 'OTHER'
    STEP_H = 'STEP'
    TEST_CASE_H = 'TCASE'
    SUITE_H = 'SUITE'
    GENERAL_H = 'GENERAL'

    __order__ = "DEBUG INFO NOTICE WARNING ERROR CRITICAL TRACEBACK OTHER STEP_H " \
                "TEST_CASE_H SUITE_H GENERAL_H"

    @classmethod
    def get_type(cls, unf_str):
        """Return the VL log type of the passed string.

        If there is no match to a current type, then ``None`` is returned.
        The current supported types are::

            DEBUG | INFO | NOTICE | WARNING | ERROR | CRITICAL | TRACEBACK | STEP_H
            | TEST_CASE_H | SUITE_H | GENERAL_H

        :param str unf_str: Unformatted VL log line
        :rtype: VLogType | None
        """
        if not unf_str:
            return None

        if re.match(VPatterns.get_std(), unf_str):
            type = re.search(VPatterns.get_std_type(), unf_str).group(0)
            if type == cls.DEBUG.name:
                return VLogType.DEBUG
            elif type == cls.INFO.name:
                return VLogType.INFO
            elif type == cls.NOTICE.name:
                return VLogType.NOTICE
            elif type == cls.WARNING.name:
                return VLogType.WARNING
            elif type == cls.ERROR.name:
                return VLogType.ERROR
            elif type == cls.CRITICAL.name:
                return VLogType.CRITICAL
        elif re.match(VPatterns.get_traceback(), unf_str):
            return VLogType.TRACEBACK
        elif re.match(VPatterns.get_suite_header(), unf_str):
            return VLogType.SUITE_H
        elif re.match(VPatterns.get_test_case_header(), unf_str):
            return VLogType.TEST_CASE_H
        elif re.match(VPatterns.get_step_header(), unf_str):
            return VLogType.STEP_H
        elif re.match(VPatterns.get_general_header(), unf_str):
            return VLogType.GENERAL_H
        elif re.match(VPatterns.OTHER_PATTERN, unf_str):
            return VLogType.OTHER
        return None


class VLogStdFields(Enum):
    """Enums representing the fields in the standard logs."""

    DATE = 'DATE'
    TIME = 'TIME'
    TYPE = 'TYPE'
    SOURCE = 'SOURCE'
    THREAD = 'THREAD'
    DETAILS = 'DETAILS'


class Colorize:
    """Provides methods to color logs based on their VLogType."""

    TYPE_COLORS = {
        'DEBUG': Fore.MAGENTA,
        'INFO': Fore.BLUE,
        'NOTICE': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Style.BRIGHT + Fore.RED,
        'CRITICAL': Style.BRIGHT + Back.RED + Fore.YELLOW,
        'OTHER': Style.RESET_ALL,
        'STEP_H': Style.BRIGHT + Fore.MAGENTA,
        'TEST_CASE_H': Style.BRIGHT + Fore.CYAN,
        'SUITE_H': Style.BRIGHT + Fore.YELLOW,
        'GENERAL_H': Style.BRIGHT + Fore.GREEN
    }

    COLORS = {
        'traceback-header': Style.BRIGHT + Fore.YELLOW,
        'traceback-exception': Style.BRIGHT + Fore.RED,
        'traceback-description': Style.BRIGHT + Fore.YELLOW,
        'traceback-line-num': Fore.YELLOW,
        'traceback-filename': Fore.RED,
        'traceback-funct': Fore.GREEN,

        'json-post': Style.BRIGHT,
        'api-id': Style.BRIGHT,
        'api-request': Style.BRIGHT + Back.BLUE + Fore.WHITE,
        'api-response': Style.BRIGHT + Back.MAGENTA + Fore.WHITE,

        'passed-status': Fore.GREEN,
        'passed-error-status': Fore.YELLOW,
        'failed-status': Fore.RED
    }


    @classmethod
    def apply(cls, text, color_str):
        """Applies the console coloring to the given text based on the given color.

        Note: Colors correspond to strings found in ``COLORS``.
        """
        color = cls.COLORS[color_str]
        return color + text + Style.RESET_ALL

    @classmethod
    def type_apply(cls, text, type=VLogType.OTHER):
        """Applies the console coloring to the given text based on the given VLogType."""
        color = cls.TYPE_COLORS[type.name]
        return color + text + Style.RESET_ALL

    @classmethod
    def esc_len(cls, log_type):
        """Returns the length of escape characters in a given log line if used ``type_apply``."""
        return len(cls.TYPE_COLORS[log_type.name]) + len(Style.RESET_ALL)


class VPatterns(object):
    """Contains methods to return the regex patterns found in vl objects."""

    PATTERN = ".*"

    # Standard Log Patterns
    DATE_RE_PATTERN = "\d{4}-\d{2}-\d{2}"
    TIME_RE_PATTERN = "\d{2}:\d{2}:\d{2}(?:\.\d{6}|,\d{3})"
    AT2_TIME_PATTERN = "\d{2}:\d{2}:\d{2},\d{3}"
    LOG_TYPES = [VLogType.DEBUG, VLogType.INFO, VLogType.NOTICE,
                 VLogType.WARNING, VLogType.ERROR, VLogType.CRITICAL]
    SOURCE_PATTERN = "\[.*:.*\]"
    THREAD_PATTERN = "\[.*:.*\]"
    DETAIL_PATTERN = ".*"
    DETAIL_API_PATTERN = "^JSON-RPC-POST response|(^Sending HTTP POST request).*"
    DETAIL_REQUEST_PATTERN = "^Sending HTTP POST request to server_url: (.*); ({.*}|None).$"
    DETAIL_RESPONSE_PATTERN = "^JSON-RPC-POST response: ({.*})$"


    # Suite Header Patterns
    SUITE_NAME_PATTERN = "(Ts.*)"
    SUITE_HEADER_PATTERN = "^=Test Suite: .*" + SUITE_NAME_PATTERN + "=$"

    # Test Case Patterns
    CASE_NAME_PATTERN = "(Tc.*)"
    CASE_HEADER_PATTERN = "^=Test Case (\d+): .*" + CASE_NAME_PATTERN + "=$"

    # Test Step Patterns
    STEP_HEADER_PATTERN = "^-Starting Step (\d+) for " + CASE_NAME_PATTERN \
                          + ": .*-" + "\n-Expect: .*-$"

    # General Header Patterns
    GENERAL_HEADER_PATTERN = "^=(.*)=$"

    TRACEBACK_PATTERN = "^(.*)Traceback \(most recent call last\):\s*$"
    TRACEBACK_STEP_PATTERN = "^\s*File \"(.+\.py)\", line (\d+), in (\w+)\\n\s+(.+)$"
    TRACEBACK_EXCEPTION_PATTERN = "^(\w+): (.*)$"

    # Pattern describing the following
    # "# History...", "|> ...", "! ..."
    OTHER_PATTERN = "^[# History|\|>|!].+$"

    @classmethod
    def get_std(cls):
        """Return the regex ``str`` for a standard vlogline."""
        patterns = []
        patterns.append(cls.get_std_datetime())
        patterns.append(cls.get_std_type())
        patterns.append("".join([cls.get_std_source(), "(?: ", cls.get_std_thread(), ")?"]))
        patterns.append(cls.get_std_details())
        output = " ".join(patterns)
        output = "".join(["^", output, "$"])
        return output

    @classmethod
    def get_std_datetime(cls):
        """Return the regex ``str`` used for identifying VL datetime field."""
        return " ".join([cls.DATE_RE_PATTERN, cls.TIME_RE_PATTERN])

    @classmethod
    def get_at2_time(cls):
        """Return the regex ``str`` used for identifying VL AT2 time field."""
        return cls.AT2_TIME_PATTERN

    @classmethod
    def get_std_type(cls):
        """Return the regex ``str`` used for identifying VL type field."""
        type_str_list = [x.name for x in cls.LOG_TYPES]
        type_str = "|".join(type_str_list)
        return "".join(["(", type_str, ")"])

    @classmethod
    def get_std_source(cls):
        """Return the regex ``str`` used for identifying VL source field."""
        return cls.SOURCE_PATTERN

    @classmethod
    def get_std_thread(cls):
        """Return the regex ``str`` used for identifying VL thread field."""
        return cls.THREAD_PATTERN

    @classmethod
    def get_std_details(cls):
        """Return the regex ``str`` used for identifying VL details field."""
        return cls.DETAIL_PATTERN

    @classmethod
    def get_std_details_api(cls):
        """Return the regex ``str`` used for identifying api call in the VL details field."""
        return cls.DETAIL_API_PATTERN

    @classmethod
    def get_std_details_request(cls):
        """Return the regex ``str`` used for identifying request api call in the VL details field."""
        return cls.DETAIL_REQUEST_PATTERN

    @classmethod
    def get_std_details_response(cls):
        """Return the regex ``str`` used for identifying response api call in the VL details field."""
        return cls.DETAIL_RESPONSE_PATTERN

    @classmethod
    def get_traceback(cls):
        """Return the regex ``str`` used for identifying VL tracebacks."""
        return cls.TRACEBACK_PATTERN

    @classmethod
    def get_traceback_exception(cls):
        """Return the regex ``str`` used for identifying VL tracebacks."""
        return cls.TRACEBACK_EXCEPTION_PATTERN

    @classmethod
    def get_suite_name(cls):
        """Return the regex ``str`` used for identifying VL suite name."""
        return cls.SUITE_NAME_PATTERN

    @classmethod
    def get_suite_header(cls):
        """Return the regex ``str`` used for identifying VL suite header."""
        return cls.SUITE_HEADER_PATTERN

    @classmethod
    def get_test_case_name(cls):
        """Return the regex ``str`` used for identifying VL test case name."""
        return cls.CASE_NAME_PATTERN

    @classmethod
    def get_test_case_header(cls):
        """Return the regex ``str`` for identifying VL test case header."""
        return cls.CASE_HEADER_PATTERN

    @classmethod
    def get_step_header(cls):
        """Return the regex ``str`` for identifying VL step header."""
        return cls.STEP_HEADER_PATTERN

    @classmethod
    def get_general_header(cls):
        """Return the regex ``str`` for identifying VL general header."""
        return cls.GENERAL_HEADER_PATTERN

    @classmethod
    def std_log_types(cls):
        return cls.LOG_TYPES

    @classmethod
    def get_other(cls):
        """Return the regex ``str`` used for identifying misc. logs."""
        return cls.OTHER_PATTERN


def file_parse(file):

    tc_regex = "^Test Case (\d+): .*(Tc\w+).*$"
    header_regex = "^=*$"
    header = False

    with open(file) as original_file:

        for line in original_file:

            header_match = re.match(header_regex, line)
            # Initial header border
            if header_match and not header:
                header = True
                continue

            # Last header border
            if header and header_match:
                header = False
                continue

            if header:
                tc_match = re.match(tc_regex, line)
                tc_name = ""
                tc_num = ""
                if tc_match:
                    tc_num = tc_match.group(1)
                    tc_name = tc_match.group(2)
                else:
                    pass

_, term_width = os.popen('stty size', 'r').read().split()
term_width = int(term_width)

TOTAL_BAR_LENGTH = 65.
last_time = time.time()
begin_time = last_time
def progress_bar(current, total, msg=None):
    global last_time, begin_time
    if current == 0:
        begin_time = time.time()  # Reset for new bar.

    cur_len = int(TOTAL_BAR_LENGTH*current/total)
    rest_len = int(TOTAL_BAR_LENGTH - cur_len) - 1

    sys.stdout.write(' [')
    for i in range(cur_len):
        sys.stdout.write('=')
    sys.stdout.write('>')
    for i in range(rest_len):
        sys.stdout.write('.')
    sys.stdout.write(']')

    cur_time = time.time()
    step_time = cur_time - last_time
    last_time = cur_time
    tot_time = cur_time - begin_time

    L = []
    L.append('  Step: %s' % format_time(step_time))
    L.append(' | Tot: %s' % format_time(tot_time))
    if msg:
        L.append(' | ' + msg)

    msg = ''.join(L)
    sys.stdout.write(msg)
    for i in range(term_width-int(TOTAL_BAR_LENGTH)-len(msg)-3):
        sys.stdout.write(' ')

    # Go back to the center of the bar.
    for i in range(term_width-int(TOTAL_BAR_LENGTH/2)+2):
        sys.stdout.write('\b')
    sys.stdout.write(' %d/%d ' % (current+1, total))

    if current < total-1:
        sys.stdout.write('\r')
    else:
        sys.stdout.write('\n')
    sys.stdout.flush()

def format_time(seconds):
    days = int(seconds / 3600/24)
    seconds = seconds - days*3600*24
    hours = int(seconds / 3600)
    seconds = seconds - hours*3600
    minutes = int(seconds / 60)
    seconds = seconds - minutes*60
    secondsf = int(seconds)
    seconds = seconds - secondsf
    millis = int(seconds*1000)

    f = ''
    i = 1
    if days > 0:
        f += str(days) + 'D'
        i += 1
    if hours > 0 and i <= 2:
        f += str(hours) + 'h'
        i += 1
    if minutes > 0 and i <= 2:
        f += str(minutes) + 'm'
        i += 1
    if secondsf > 0 and i <= 2:
        f += str(secondsf) + 's'
        i += 1
    if millis > 0 and i <= 2:
        f += str(millis) + 'ms'
        i += 1
    if f == '':
        f = '0ms'
    return f