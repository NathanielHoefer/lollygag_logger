"""This module defines all of the VL field objects found in standard logs."""

import six
import abc
import re
from datetime import datetime
from vl_logger.venums import VLogType


@six.add_metaclass(abc.ABCMeta)
class LogField(object):
    """Abstract base class used for representing fields in log lines."""

    PATTERN = ""

    @abc.abstractmethod
    def __str__(self):
        """Abstract method for returning ``str`` of field."""
        pass

    @classmethod
    def get_pattern(cls):
        """Return the regex pattern that is used for identifying VL log field.

        :rtype: str
        """
        return cls.PATTERN


class Datetime(LogField):
    """Represents both date and time field."""

    DATE_RE_PATTERN = "\d{4}-\d{2}-\d{2}"
    TIME_RE_PATTERN = "\d{2}:\d{2}:\d{2}\.\d{6}"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S.%f"

    def __init__(self, datetime_token):
        """Initialize datetime field from ``str`` token.

        :param str datetime_token: Date and time token from VL log field
        :raise ValueError: On value that doesn't follow date and time format
        """
        try:
            format = " ".join([self.DATE_FORMAT, self.TIME_FORMAT])
            self.datetime = datetime.strptime(datetime_token, format)
        except ValueError:
            msg = "The datetime token '" + datetime_token + "' is not vaild."
            raise ValueError(msg)

    def __str__(self):
        """Convert date and time fields to ``str`` following vl formatting."""
        format = " ".join([self.DATE_FORMAT, self.TIME_FORMAT])
        return self.datetime.strftime(format)

    def get_datetime(self):
        """Return the ``datetime`` object of the field."""
        return self.datetime

    @classmethod
    def get_pattern(cls):
        """Return the regex ``str`` used for identifying VL datetime field."""
        return "^" + cls.DATE_RE_PATTERN + " " + cls.TIME_RE_PATTERN + "$"


class Type(LogField):
    """Represents the type field."""

    def __init__(self, type):
        """Initialize datetime field from ``VLogType`` token.

        :param VLogType type: Type of log
        :raise ValueError: On types not in ``VLogType``
        """
        if type in list(VLogType):
            self.type = type
        else:
            raise ValueError("Invalid type '" + type + "'")

    def __str__(self):
        """Convert type field to ``str``."""
        return self.type.value

    def get_type(self):
        """Return the ``VLogType`` of the field."""
        return self.type


class Source(LogField):
    """Represents the source field.

    :ivar str source_token: Source token from VL log
    """

    def __init__(self, source_token):
        pass

    def __str__(self):
        pass


class Thread(LogField):
    """Represents the thread field.

    :ivar str thread_token: Thread token from VL log
    """

    def __init__(self, thread_token):
        pass

    def __str__(self):
        pass


class Details(LogField):
    """Represents the details field.

    :ivar str details_token: Details token from VL log
    """

    def __init__(self, details_token):
        pass

    def __str__(self):
        pass
