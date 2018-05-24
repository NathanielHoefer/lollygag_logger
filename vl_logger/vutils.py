import re

from enum import Enum


class VLogType(Enum):
    """Enums representing the types of log lines."""

    DEBUG = 'DEBUG'
    INFO = 'INFO'
    NOTICE = 'NOTICE'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'
    OTHER = 'OTHER'
    STEP_H = 'STEP'
    TEST_CASE_H = 'TCASE'
    SUITE_H = 'SUITE'

    __order__ = "DEBUG INFO NOTICE WARNING ERROR CRITICAL OTHER STEP_H " \
                "TEST_CASE_H SUITE_H"

    @classmethod
    def get_type(cls, unf_str):
        """Returns the VL log type of the passed string.

        :param str unf_str: Unformatted VL log line
        :rtype: VLogType
        """

        std_pattern = VPatterns.get_std()
        if re.match(std_pattern, unf_str):
            type = re.search(VPatterns.get_std_type(), unf_str).group(0)
            if type == cls.DEBUG.value:
                return VLogType.DEBUG
            elif type == cls.INFO.value:
                return VLogType.INFO
            elif type == cls.NOTICE.value:
                return VLogType.NOTICE
            elif type == cls.WARNING.value:
                return VLogType.WARNING
            elif type == cls.ERROR.value:
                return VLogType.ERROR
            elif type == cls.CRITICAL.value:
                return VLogType.CRITICAL
        return None


class VPatterns(object):
    """Contains methods to return the regex patterns found in vl objects."""

    PATTERN = ".*"

    # Standard Log Patterns
    DATE_RE_PATTERN = "\d{4}-\d{2}-\d{2}"
    TIME_RE_PATTERN = "\d{2}:\d{2}:\d{2}\.\d{6}"
    LOG_TYPES = [VLogType.DEBUG, VLogType.INFO, VLogType.NOTICE,
                 VLogType.WARNING, VLogType.ERROR, VLogType.CRITICAL]
    SOURCE_PATTERN = "\[.*:.*\]"
    THREAD_PATTERN = "\[.*:.*\]"
    DETAIL_PATTERN = ".*"

    @classmethod
    def get_std(cls):
        """Return the regex ``str`` for a standard vlogline."""
        patterns = []
        patterns.append(cls.get_std_datetime())
        patterns.append(cls.get_std_type())
        patterns.append(cls.get_std_source())
        patterns.append(cls.get_std_thread())
        patterns.append(cls.get_std_details())
        return " ".join(patterns)

    @classmethod
    def get_std_datetime(cls):
        """Return the regex ``str`` used for identifying VL datetime field."""
        return " ".join([cls.DATE_RE_PATTERN, cls.TIME_RE_PATTERN])

    @classmethod
    def get_std_type(cls):
        """Return the regex ``str`` used for identifying VL type field."""
        type_str_list = [x.value for x in cls.LOG_TYPES]
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
        """Return the regex ``str`` used for identifying VL thread field."""
        return cls.DETAIL_PATTERN


def create_log_line(unf_str, type):
    """Creates the appropriate VLogLine object based on type.

    :param str unf_str: Unformatted VL log line
    :param VLogType type: Type of VLogLine object to create.
    :rtype: Base | None
    :returns: VLogLine if unf_str matches pattern of type, else None
    """
    fmt_log = None
    return fmt_log