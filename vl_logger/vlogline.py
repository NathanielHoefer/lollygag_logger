import six
import abc

from vl_logger.lollygag_logger import LogLine
from vl_logger import vlogfield
from vl_logger.vutils import VLogType


@six.add_metaclass(abc.ABCMeta)
class Base(LogLine):
    """Abstract base class for all other log line elements."""

    PATTERN = ""
    MAX_LINE_LEN = 100
    UNF_LINE_SPLIT_COUNT = 5
    FIELDS = [vlogfield.Datetime,
              vlogfield.Type,
              vlogfield.Source,
              vlogfield.Thread,
              vlogfield.Details]

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


class Standard(Base):

    def __init__(self, unf_str, type=None):
        self.datetime, self.type, self.source, self.thread, \
        self.details = self.parse_fields(unf_str, type)

    def __str__(self):
        return " ".join([
            str(self.datetime),
            str(self.type),
            str(self.source),
            str(self.thread),
            str(self.details)
        ])

    def parse_fields(self, unf_str, type=None):
        tokens = unf_str.split(" ", self.UNF_LINE_SPLIT_COUNT)
        fields = []
        fields.append(vlogfield.Datetime(" ".join([tokens[0], tokens[1]])))
        if type:
            fields.append(vlogfield.Type(type))
        else:
            fields.append(vlogfield.Type(VLogType.get_type(unf_str)))
        fields.append(vlogfield.Source(tokens[3]))
        fields.append(vlogfield.Thread(tokens[4]))
        fields.append(vlogfield.Details(tokens[5]))
        return fields
