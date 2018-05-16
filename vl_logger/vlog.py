import six
import abc

from vl_logger.lollygag_logger import LogLine
from vl_logger.venums import VLogType


@six.add_metaclass(abc.ABCMeta)
class VLogLine(LogLine):
    """Abstract base class for all other log line elements."""

    PATTERN = ""
    MAX_LINE_LEN = 100

    @classmethod
    def set_max_line_len(cls, max_len):
        """Sets the maximum length of the VLogLine string.

        :param int max_len: Max number of chars in VLogLine string.
        """
        cls.MAX_LINE_LEN = max_len

    @abc.abstractmethod
    def __str__(self):
        """Formatted string representing VLogLine object."""
        return None

    @abc.abstractmethod
    def parse_fields(self, unf_str):
        """Parse the unformatted string into the various fields and create the
        appropriate VL objects.

        Note: This method is abstract.

        :param str unf_str: Unformatted VL log line
        """
        pass

    @classmethod
    @abc.abstractmethod
    def get_pattern(cls):
        """Returns the regex pattern that is used for identifying VL log
        objects.

        Note: This method is abstract.

        :rtype: str
        """
        return cls.PATTERN



class LogUtils(object):
    """Collection of log utility functions."""

    @staticmethod
    def get_type(unf_str):
        """Returns the VL log type of the passed string.

        :param str unf_str: Unformatted VL log line
        :rtype: VLogType
        """
        return None

    @staticmethod
    def create_log_line(unf_str, type):
        """Creates the appropriate VLogLine object based on type.

        :param str unf_str: Unformatted VL log line
        :param VLogType type: Type of VLogLine object to create.
        :rtype: VLogLine | None
        :returns: VLogLine if unf_str matches pattern of type, else None
        """
        fmt_log = None
        return fmt_log