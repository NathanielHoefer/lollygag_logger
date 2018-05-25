"""Module containing all Log Line Objects."""

import abc
import re

import six
from vl_logger import vlogfield
from vl_logger.lollygag_logger import LogLine
from vl_logger.vutils import VLogType
from vl_logger.vutils import VPatterns


@six.add_metaclass(abc.ABCMeta)
class Base(LogLine):
    """Abstract base class for all other log line elements."""

    PATTERN = ""
    MAX_LINE_LEN = 105
    UNF_LINE_SPLIT_COUNT = 5
    FIELDS = [vlogfield.Datetime,
              vlogfield.Type,
              vlogfield.Source,
              vlogfield.Thread,
              vlogfield.Details]

    @classmethod
    def set_max_line_len(cls, max_len):
        """Set the maximum length of the VLogLine string.

        :param int max_len: Max number of chars in VLogLine string.
        """
        cls.MAX_LINE_LEN = max_len

    @classmethod
    def get_max_line_len(cls):
        """Return the maximum length of the VLogLine string."""
        return cls.MAX_LINE_LEN

    @abc.abstractmethod
    def __str__(self):
        """Formatted string representing VLogLine object."""
        return None

    @abc.abstractmethod
    def _parse_fields(self, unf_str):
        """Parse the string into the various fields.

        :param str unf_str: Unformatted VL log line
        """
        pass


class Standard(Base):
    """Standard VL Log Line.

    A standard VL log line is identified by the following format

    .. code-block:: none

        <date> <time> <type> <source> <thread> <details>

        Ex:
        2017-10-30 19:13:32.208116 DEBUG [res.core:636] [MainProcess:MainThread] Sending HTTP POST request  # nopep8
    """

    def __init__(self, unf_str, type=None):
        """Initialize the standard VL log line.

        If the log type has already been determined prior to initializing, then
        the type can be passed in, otherwise it will be determined.

        :param str unf_str: Unformatted VL log line
        :param `vutils.VLogType`_ type: The type of VL log line
        """
        self.datetime, self.type, self.source, self.thread, \
            self.details = self._parse_fields(unf_str, type)

    def __str__(self):
        """Formatted string representing Standard VLogLine."""
        return " ".join([
            str(self.datetime),
            str(self.type),
            str(self.source),
            str(self.thread),
            str(self.details)
        ])

    def _parse_fields(self, unf_str, type=None):
        """Parse the string into the various fields.

        :return a list of the vlogfield objects in the order that they appeared
        :rtype list
        """
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


@six.add_metaclass(abc.ABCMeta)
class Header(Base):
    """Abstract base class for all other header log line elements."""

    BORDER_CHAR = "="

    @abc.abstractmethod
    def _add_border(self, header_str):
        """Return string with border before and after header string."""
        return None

    @classmethod
    def get_border_char(cls):
        """Return the character used for the border."""
        return cls.BORDER_CHAR


class SuiteHeader(Header):
    """Suite Header VL Log Line.

    A Suite Header VL log line is identified by the following format:

    .. code-block:: none

        ============================* (len of 105)
        Test Suite: <Description ending in suite name (Ts.*)>
        ============================* (len of 105)

        Ex:
        ============================* (len of 105)
        Test Suite: Starting Setup of TsSuite
        ============================* (len of 105)

    .. note::

        Don't include the borders in the unf_str.
        Only the information between the borders.
    """

    BORDER_CHAR = "="

    def __init__(self, unf_str):
        """Initialize the suite header VL log line.

        :param str unf_str: Unformatted VL log line
        """
        self.suite_name, self.desc = self._parse_fields(unf_str)

    def __str__(self):
        """Formatted string representing suite header VLogLine.

        This does include the borders surrounding the header string.
        """
        header_str = " ".join([
            "Test Suite:",
            self.desc
        ])
        return self._add_border(header_str)

    def _parse_fields(self, unf_str):
        """Parse the string into the suite header fields.

        Fields::

            Suite Name, Description

        :return a list of the suite header fields
        :rtype list(str)
        """
        _, desc_token = unf_str.split(": ")
        fields = []
        suite_name = re.search(VPatterns.get_suite_name(), desc_token).group(0)
        fields.append(suite_name)
        fields.append(desc_token)
        return fields

    def _add_border(self, header_str):
        """Return the header string with borders.

        The length of the border is determined by the Max Line Length.
        """
        border = self.BORDER_CHAR * self.get_max_line_len()
        return "\n".join([border, header_str, border])


class TestCaseHeader(Header):
    """Test Case Header VL Log Line.

    A Test Case Header VL log line is identified by the following format:

    .. code-block:: none

        ============================* (len of 105)
        Test Case #: <Description ending in test case name (Tc.*)>
        ============================* (len of 105)

        Ex:
        ============================* (len of 105)
        Test Case 0: Starting Test of TcTest
        ============================* (len of 105)

    .. note::

        Don't include the borders in the unf_str.
        Only the information between the borders.
    """

    BORDER_CHAR = "="

    def __init__(self, unf_str):
        """Initialize the test case header VL log line.

        :param str unf_str: Unformatted VL log line
        """
        self.test_case_name, self.number, \
            self.desc = self._parse_fields(unf_str)

    def __str__(self):
        """Formatted string representing test case header VLogLine.

        This does include the borders surrounding the header string.
        """
        header_str = "".join([
            "Test Case ", str(self.number), ": ", self.desc
        ])
        return self._add_border(header_str)

    def _parse_fields(self, unf_str):
        """Parse the string into the test case header fields.

        Fields::

            Test Case Name, Number, Description

        :return a list of the test case header fields
        :rtype list(str)
        """
        unf_str = unf_str.lstrip("Test Case ")
        number, desc_token = unf_str.split(": ")
        case_name = re.search(VPatterns.get_test_case_name(),
                              desc_token).group(0)
        fields = []
        fields.append(case_name)
        fields.append(int(number))
        fields.append(desc_token)
        return fields

    def _add_border(self, header_str):
        """Return the header string with borders.

        The length of the border is determined by the Max Line Length.
        """
        border = self.BORDER_CHAR * self.get_max_line_len()
        return "\n".join([border, header_str, border])
