"""Module containing all Log Line Objects."""

import abc
import re

import six
from vl_logger import vlogfield
from vl_logger.lollygag_logger import LogLine
from vl_logger.vutils import VLogType
from vl_logger.vutils import VLogStdFields
from vl_logger.vutils import VPatterns
from vl_logger.vutils import Colorize


@six.add_metaclass(abc.ABCMeta)
class Base(LogLine):
    """Abstract base class for all other log line elements."""

    # Configuration Settings
    MAX_LINE_LEN = 105
    COLORIZE = False
    CONDENSE_LINE = False
    SHORTEN_TYPE = False
    FORMAT_API = False
    DISPLAY_FIELDS = [
        VLogStdFields.DATE,
        VLogStdFields.TIME,
        VLogStdFields.TYPE,
        VLogStdFields.SOURCE,
        VLogStdFields.THREAD,
        VLogStdFields.DETAILS
    ]

    # Other Settings
    UNF_LINE_SPLIT_COUNT = 5
    FIELDS = [vlogfield.Datetime,
              vlogfield.Type,
              vlogfield.Source,
              vlogfield.Thread,
              vlogfield.Details]

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

    @classmethod
    def set_max_line_len(cls, max_len):
        """Set the maximum length of the standard log line strings when printed.

        This doesn't include header descriptions, tracebacks, or logs not classified.

        :param int max_len: Max number of chars to print for each string.
        """
        cls.MAX_LINE_LEN = max_len

    @classmethod
    def get_max_line_len(cls):
        """Return the maximum length of the VLogLine string."""
        return cls.MAX_LINE_LEN

    @classmethod
    def colorize(cls, set=True):
        """Use the colored option if available in a ``LogLine`` object."""
        cls.COLORIZE = set

    @classmethod
    def format_api(cls, set=True):
        """Format the API requests and responses."""
        cls.FORMAT_API = set

    @classmethod
    def condense_line(cls, set=True):
        """Condense the ``str`` output of standard logs to the specified max line length."""
        cls.CONDENSE_LINE = set

    @classmethod
    def shorten_type(cls, set=True):
        """Printed log types are shortened to 5 characters to ensure consistency between lines."""
        cls.SHORTEN_TYPE = set

    @classmethod
    def display_fields(cls, fields):
        """Print only the ``VLogStdFields`` specified.

        .. code-block:: python

            from vl_logger.vutils import VLogStdFields
            Base.display_fields([VLogStdFields.TIME, VLogStdFields.TYPE])

        :param [VLogStdFields] fields: The enums specifying which logs to print.
        """
        cls.DISPLAY_FIELDS = fields


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
        self.additional_logs = []
        self._set_config()

    def __str__(self):
        """Formatted string representing Standard VLogLine."""
        fields = []
        fields.append(str(self.datetime))
        fields.append(str(self.type))
        fields.append(str(self.source))
        fields.append(str(self.thread))
        fields.append(str(self.details))
        output = " ".join(x for x in fields if x)

        if self.CONDENSE_LINE and not self.details.is_api_call():
            line_len = self.MAX_LINE_LEN
            if self.COLORIZE:
                line_len += Colorize.esc_len(self.type.get_type())
            output = output[:line_len]

        if self.additional_logs:
            output = "\n".join([output].extend(self.additional_logs))
        return output

    def _parse_fields(self, unf_str, type=None):
        """Parse the string into the various fields.

        :return a list of the vlogfield objects in the order that they appeared
        :rtype list
        """
        tokens = unf_str.split(" ", self.UNF_LINE_SPLIT_COUNT)
        if not type:
            type = VLogType.get_type(unf_str)
        fields = []
        fields.append(vlogfield.Datetime(" ".join([tokens[0], tokens[1]])))
        fields.append(vlogfield.Type(type))
        fields.append(vlogfield.Source(tokens[3]))
        fields.append(vlogfield.Thread(tokens[4]))
        fields.append(vlogfield.Details(tokens[5] if len(tokens) >= 6 else ""))
        return fields

    def _set_config(self):
        """Sets the individual field options such as color and display."""
        if self.COLORIZE:
            self.type.colorize = True
            self.details.colorize = True

        if self.SHORTEN_TYPE:
            self.type.shorten_type = True

        if self.FORMAT_API:
            self.details.format_api_calls()

        # Fields to display
        self.datetime.display_date = True if VLogStdFields.DATE in self.DISPLAY_FIELDS else False
        self.datetime.display_time = True if VLogStdFields.TIME in self.DISPLAY_FIELDS else False
        self.type.display = True if VLogStdFields.TYPE in self.DISPLAY_FIELDS else False
        self.source.display = True if VLogStdFields.SOURCE in self.DISPLAY_FIELDS else False
        self.thread.display = True if VLogStdFields.THREAD in self.DISPLAY_FIELDS else False
        self.details.display = True if VLogStdFields.DETAILS in self.DISPLAY_FIELDS else False


class Traceback(Base):
    """VL Traceback Log.

    Each line is to be its separated as its own element within a list.
    The lines may be prepended by the same leading characters.
    Leading characters can be ``!``, ``|>``, etc.


    .. code-block:: none

        Traceback (most recent call last):
          File "<file name>", line <line num>, in <func call>
            <line>
          ...
        <exception>: <description>
    """

    def __init__(self, unf_str_list):
        """Initialize the traceback.

        :param str unf_str_list: Unformatted VL log line
        """
        self.leading_chars = ""
        self.type = VLogType.TRACEBACK
        self.steps, self.exception = self._parse_fields(unf_str_list)
        self._set_config()

    def __str__(self):
        """Formatted string representing VLogLine Traceback log."""
        header = "Traceback (most recent call last):"
        if self.COLORIZE:
            header = Colorize.apply(header, 'traceback-header')
        header = "{}{}".format(self.leading_chars, header)
        steps = "\n".join([str(step) for step in self.steps])
        output = "\n".join([header, steps, str(self.exception)])
        return output

    def _parse_fields(self, unf_str_list):
        """Parse the list of strings into the header, steps, and exception fields.

        :param list(str) unf_str_list: Unformatted VL log line
        """
        unf_header = unf_str_list[0]
        unf_steps = unf_str_list[1:-1]
        unf_exception = unf_str_list[-1]

        self.leading_chars = re.match(VPatterns.get_traceback(), unf_header).group(1)
        fmt_steps = []
        for line1, line2 in zip(unf_steps[0::2], unf_steps[1::2]):
            line1 = self._remove_leading_chars(line1)
            line2 = self._remove_leading_chars(line2)
            step = "\n".join([line1, line2])
            fmt_steps.append(vlogfield.TracebackStep(step, self.leading_chars))
        unf_exception = self._remove_leading_chars(unf_exception)
        fmt_exception = vlogfield.TracebackException(unf_exception, self.leading_chars)
        return fmt_steps, fmt_exception

    def _remove_leading_chars(self, line):
        """Removes the leading characters from given string."""
        return line[len(self.leading_chars):]

    def _set_config(self):
        """Sets the individual field options such as color and display."""
        if self.COLORIZE:
            for step in self.steps:
                step.set_colorize(True)
            self.exception.colorize = True

@six.add_metaclass(abc.ABCMeta)
class Header(Base):
    """Abstract base class for all other header log line elements."""

    BORDER_CHAR = "="

    def _add_border(self, header_str):
        """Return the header string with borders.

        The length of the border is determined by the Max Line Length.
        """
        border = self.BORDER_CHAR * self.get_max_line_len()
        border = Colorize.type_apply(border, self.type)
        return "\n".join([border, header_str, border])

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

    .. testcode::

        from vl_logger import vlogline

        # Note how '=' must be added before and after the header string
        # to indicate that it is a header.
        unf_str = "=Test Suite: Starting Setup of TsSuite="
        suite_header = vlogline.SuiteHeader(unf_str)

    .. note::

        Don't include the borders in the unf_str.
        Only the information between the borders.
    """

    BORDER_CHAR = "="

    def __init__(self, unf_str):
        """Initialize the suite header VL log line.

        :param str unf_str: Unformatted VL log line
        """
        self.type = VLogType.SUITE_H
        self.suite_name, self.desc = self._parse_fields(unf_str)

    def __str__(self):
        """Formatted string representing suite header VLogLine.

        This does include the borders surrounding the header string.
        """
        header_str = " ".join([
            "Test Suite:",
            self.desc
        ])
        if self.COLORIZE:
            header_str = Colorize.apply(header_str, 'header-desc')
        header_str = self._add_border(header_str)
        return header_str

    def _parse_fields(self, unf_str):
        """Parse the string into the suite header fields.

        Fields::

            Suite Name, Description

        :return a list of the suite header fields
        :rtype list(str)
        """
        unf_str = unf_str.strip(self.BORDER_CHAR)
        _, desc_token = unf_str.split(": ")
        fields = []
        suite_name = re.search(VPatterns.get_suite_name(), desc_token).group(0)
        fields.append(suite_name)
        fields.append(desc_token)
        return fields


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

    .. testcode::

        from vl_logger import vlogline

        # Note how '=' must be added before and after the header string
        # to indicate that it is a header.
        unf_str = "=Test Case 0: Starting Test of TcTest="
        test_case_header = vlogline.TestCaseHeader(unf_str)

    .. note::

        Don't include the borders in the unf_str.
        Only the information between the borders.
    """

    BORDER_CHAR = "="

    def __init__(self, unf_str):
        """Initialize the test case header VL log line.

        :param str unf_str: Unformatted VL log line
        """
        self.type = VLogType.TEST_CASE_H
        self.test_case_name, self.number, \
            self.desc = self._parse_fields(unf_str)

    def __str__(self):
        """Formatted string representing test case header VLogLine.

        This does include the borders surrounding the header string.
        """
        header_str = "".join([
            "Test Case ", str(self.number), ": ", self.desc
        ])
        if self.COLORIZE:
            header_str = Colorize.apply(header_str, 'header-desc')
        header_str = self._add_border(header_str)
        return header_str

    def _parse_fields(self, unf_str):
        """Parse the string into the test case header fields.

        Fields::

            Test Case Name, Number, Description

        :return a list of the test case header fields
        :rtype list(str)
        """
        unf_str = unf_str.strip(self.BORDER_CHAR)
        unf_str = unf_str.lstrip("Test Case ")
        number, desc_token = unf_str.split(": ")
        case_name = re.search(VPatterns.get_test_case_name(),
                              desc_token).group(0)
        fields = []
        fields.append(case_name)
        fields.append(int(number))
        fields.append(desc_token)
        return fields


class StepHeader(Header):
    """Step Header VL Log Line.

    A Step Header VL log line is identified by the following format:

    .. code-block:: none

        ----------------------------* (len of 105)
        Starting Step # for Test case name (Tc.*): <Action>
        Expect: <Expected results>
        ----------------------------* (len of 105)

        Ex:
        ----------------------------* (len of 105)
        Starting Step 5 for TcTest: Verify Something
        Expect: Something Verified Successfully
        ----------------------------* (len of 105)

    .. note::

        Don't include the borders in the unf_str.
        Only the information between the borders as a single string with
        a newline character separating the two lines.
    """

    BORDER_CHAR = "-"

    def __init__(self, unf_str):
        """Initialize the step header VL log line.

        :param str unf_str: Unformatted VL log line
        """
        self.type = VLogType.STEP_H
        self.test_case_name, self.number, self.action, \
            self.expected_results = self._parse_fields(unf_str)

    def __str__(self):
        """Formatted string representing step header VLogLine.

        This does include the borders surrounding the header string.
        """
        step_str = "".join([
            "Starting Step ", str(self.number), " for ", self.test_case_name,
            ": ", self.action
        ])
        expected_results_str = "".join([
            "Expect: ", self.expected_results
        ])
        header_str = "\n".join([step_str, expected_results_str])
        if self.COLORIZE:
            header_str = Colorize.apply(header_str, 'header-desc')
        header_str = self._add_border(header_str)
        return header_str

    def _parse_fields(self, unf_str):
        """Parse the string into the step header fields.

        Fields::

            Test Case Name, Number, Action, Expected Results

        :return a list of the step header fields
        :rtype list(str)
        """
        line1, line2 = unf_str.split("\n")
        line1 = line1.strip(self.BORDER_CHAR)
        line2 = line2.strip(self.BORDER_CHAR)
        id, action = line1.split(": ")
        case_name = re.search(VPatterns.get_test_case_name(),
                              id).group(0)
        number = re.search("\d+", id).group(0)
        _, expected_result = line2.split(": ")
        fields = []
        fields.append(case_name)
        fields.append(int(number))
        fields.append(action)
        fields.append(expected_result)
        return fields


class GeneralHeader(Header):
    """General Header VL Log Line.

    A General Header VL log line is identified by the following format:

    .. code-block:: none

        ============================* (len of 105)
        <Any description>
        ============================* (len of 105)

        Ex:
        ============================* (len of 105)
        Final Report
        ============================* (len of 105)

    .. testcode::

        from vl_logger import vlogline

        # Note how '=' must be added before and after the header string
        # to indicate that it is a header.
        unf_str = "=Final Report="
        general_header = vlogline.GeneralHeader(unf_str)

    .. note::

        Don't include the borders in the unf_str.
        Only the information between the borders.
    """

    BORDER_CHAR = "="

    def __init__(self, unf_str):
        """Initialize the general header VL log line.

        :param str unf_str: Unformatted VL log line
        """
        self.type = VLogType.GENERAL_H
        self.desc = self._parse_fields(unf_str)

    def __str__(self):
        """Formatted string representing general header VLogLine.

        This does include the borders surrounding the header string.
        """
        header_str = self.desc
        if self.COLORIZE:
            header_str = Colorize.apply(header_str, 'header-desc')
        header_str = self._add_border(header_str)
        return header_str

    def _parse_fields(self, unf_str):
        """Remove the border char from string."""
        unf_str = unf_str.strip(self.BORDER_CHAR)
        return unf_str


class Other(Base):

    def __init__(self, unf_str):
        self.desc = unf_str

    def __str__(self):
        return self.desc

    def _parse_fields(self, unf_str):
        pass
