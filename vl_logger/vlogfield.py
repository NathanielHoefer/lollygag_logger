import six
import abc
import re
from datetime import datetime

@six.add_metaclass(abc.ABCMeta)
class LogField(object):
    """Abstract base class used for representing fields in log lines."""

    PATTERN = ""

    @abc.abstractmethod
    def __str__(self):
        pass

    @classmethod
    def get_pattern(cls):
        """Returns the regex pattern that is used for identifying VL log field.

        :rtype: str
        """
        return cls.PATTERN


class DatetimeField(LogField):
    """Represents both date and time field.

    :ivar str datetime_token: Date and time token from VL log field
    """
    DATE_RE_PATTERN = "\d{4}-\d{2}-\d{2}"
    TIME_RE_PATTERN = "\d{2}:\d{2}:\d{2}\.\d{6}"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S.%f"

    def __init__(self, datetime_token):
        try:
            format = " ".join([self.DATE_FORMAT, self.TIME_FORMAT])
            self.datetime = datetime.strptime(datetime_token, format)
        except ValueError:
            msg = "The datetime token '" + datetime_token + "' is not vaild."
            raise ValueError(msg)

    def __str__(self):
        format = " ".join([self.DATE_FORMAT, self.TIME_FORMAT])
        return self.datetime.strftime(format)

    @classmethod
    def get_pattern(cls):
        """Returns the regex pattern that is used for identifying VL datetime
        field.

        :rtype: str
        """
        return "^" + cls.DATE_RE_PATTERN + " " + cls.TIME_RE_PATTERN + "$"


class TypeField(LogField):
    """Represents the type field.

    :ivar str type_token: Type token from VL log
    """

    def __init__(self, type_token):
        pass

    def __str__(self):
        pass


class SourceField(LogField):
    """Represents the source field.

    :ivar str source_token: Source token from VL log
    """

    def __init__(self, source_token):
        pass

    def __str__(self):
        pass


class ThreadField(LogField):
    """Represents the thread field.

    :ivar str thread_token: Thread token from VL log
    """

    def __init__(self, thread_token):
        pass

    def __str__(self):
        pass


class DetailsField(LogField):
    """Represents the details field.

    :ivar str details_token: Details token from VL log
    """

    def __init__(self, details_token):
        pass

    def __str__(self):
        pass
