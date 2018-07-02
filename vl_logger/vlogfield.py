"""This module defines all of the VL field objects found in standard logs."""

import abc
from datetime import datetime
from vl_logger.vutils import Colorize

import six

from vl_logger.vutils import VLogType


@six.add_metaclass(abc.ABCMeta)
class LogField(object):
    """Abstract base class used for representing fields in log lines."""

    @abc.abstractmethod
    def __str__(self):
        """Abstract method for returning ``str`` of field."""


class Datetime(LogField):
    """Represents both date and time field."""

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
            self.display_date = True
            self.display_time = True
        except ValueError:
            msg = "The datetime token '" + datetime_token + "' is not vaild."
            raise ValueError(msg)

    def __str__(self):
        """Convert date and time fields to ``str`` following vl formatting."""
        if self.display_date and self.display_time:
            str_format = " ".join([self.DATE_FORMAT, self.TIME_FORMAT])
        elif self.display_time:
            str_format = self.TIME_FORMAT
        elif self.display_date:
            str_format = self.DATE_FORMAT
        else:
            return ""
        return self.datetime.strftime(str_format)

    def get_datetime(self):
        """Return the ``datetime`` object of the field."""
        return self.datetime


class Type(LogField):
    """Represents the type field."""

    def __init__(self, type):
        """Initialize datetime field from ``VLogType`` token.

        :param VLogType type: Type of log
        :raise ValueError: On types not in ``VLogType``
        """
        self.colorize = False
        self.display = True
        if type in list(VLogType):
            self.type = type
        else:
            raise ValueError("Invalid type '" + type + "'")

    def __str__(self):
        """Convert type field to ``str``."""
        output = self.type.value
        if not self.display:
            output = ""
        if self.colorize and output:
            output = Colorize.apply(self.type.value, self.type)
        return output

    def get_type(self):
        """Return the ``VLogType`` of the field."""
        return self.type


class Source(LogField):
    """Represents the source field."""

    def __init__(self, source_token):
        """Initialize source field from ``str`` token.

        :param str source_token: Source token from VL log
        :raise ValueError: On value that doesn't follow source format
        """
        try:
            source_token = source_token.strip("[]")
            module, _, line_number = source_token.partition(":")
            if not line_number:
                raise ValueError
        except ValueError:
            msg = "The source token '" + source_token + "' is not valid."
            raise ValueError(msg)
        self.module = module
        self.line_number = int(line_number)
        self.display = True

    def __str__(self):
        """Convert source field to ``str``."""
        output = ""
        if self.display:
            output = "".join(["[", self.module, ":", str(self.line_number), "]"])
        return output

    def get_module(self):
        """Return the ``str`` module of the field."""
        return self.module

    def get_line_number(self):
        """Return the ``int`` line number of the field."""
        return self.line_number


class Thread(LogField):
    """Represents the thread field."""

    def __init__(self, thread_token):
        """Initialize thread field from ``str`` token.

        :param str thread_token: Thread token from VL log
        :raise ValueError: On value that doesn't follow thread format
        """
        try:
            thread_token = thread_token.strip("[]")
            process, _, thread = thread_token.partition(":")
            if not thread:
                raise ValueError
        except ValueError:
            msg = "The thread token '" + thread_token + "' is not valid."
            raise ValueError(msg)
        self.process = process
        self.thread = thread
        self.display = True

    def __str__(self):
        """Convert thread field to ``str``."""
        output = ""
        if self.display:
            output = "".join(["[", self.process, ":", self.thread, "]"])
        return output

    def get_process(self):
        """Return the ``str`` process of the field."""
        return self.process

    def get_thread(self):
        """Return the ``str`` thread of the field."""
        return self.thread


class Details(LogField):
    """Represents the details field."""

    def __init__(self, details_token):
        """Initialize thread field from ``str`` token."""
        self.details = details_token
        self.display = True

    def __str__(self):
        """Convert details field to ``str``."""
        output = ""
        if self.display:
            output = self.details
        return output
