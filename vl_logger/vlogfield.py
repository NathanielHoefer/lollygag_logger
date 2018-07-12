"""This module defines all of the VL field objects found in standard logs."""

import abc
import json
import os
import pprint
import re
from datetime import datetime

import six

from vl_logger.vutils import Colorize
from vl_logger.vutils import VLogType
from vl_logger.vutils import VPatterns


@six.add_metaclass(abc.ABCMeta)
class LogField(object):
    """Abstract base class used for representing fields in log lines."""

    def __init__(self):
        """Initialize base class."""
        self._display = True
        self._colorize = False

    @abc.abstractmethod
    def __str__(self):
        """Abstract method for returning ``str`` of field."""

    @property
    def display(self):
        return self._display

    @display.setter
    def display(self, value=True):
        if isinstance(value, bool):
            self._display = value

    @property
    def colorize(self):
        return self._colorize

    @colorize.setter
    def colorize(self, value=True):
        if isinstance(value, bool):
            self._colorize = value


class Datetime(LogField):
    """Represents both date and time field."""

    _DATE_FORMAT = "%Y-%m-%d"
    _TIME_FORMAT = "%H:%M:%S.%f"

    def __init__(self, datetime_token):
        """Initialize datetime field from ``str`` token.

        :param str datetime_token: Date and time token from VL log field
        :raise ValueError: On value that doesn't follow date and time format
        """
        super(Datetime, self).__init__()
        try:
            format = " ".join([self._DATE_FORMAT, self._TIME_FORMAT])
            self._datetime = datetime.strptime(datetime_token, format)
            self._display_date = True
            self._display_time = True
        except ValueError:
            msg = "The datetime token '" + datetime_token + "' is not vaild."
            raise ValueError(msg)

    def __str__(self):
        """Convert date and time fields to ``str`` following vl formatting."""
        if self._display:
            if self._display_date and self._display_time:
                str_format = " ".join([self._DATE_FORMAT, self._TIME_FORMAT])
            elif self._display_time:
                str_format = self._TIME_FORMAT
            elif self._display_date:
                str_format = self._DATE_FORMAT
            else:
                return ""
            return self._datetime.strftime(str_format)
        else:
            return ""

    @property
    def datetime(self):
        """Return the ``datetime`` object of the field."""
        return self._datetime

    @property
    def display_date(self):
        return self._display_date

    @display_date.setter
    def display_date(self, value=True):
        if isinstance(value, bool):
            self._display_date = value

    @property
    def display_time(self):
        return self._display_time

    @display_time.setter
    def display_time(self, value=True):
        if isinstance(value, bool):
            self._display_time = value


class Type(LogField):
    """Represents the type field."""

    def __init__(self, type):
        """Initialize datetime field from ``VLogType`` token.

        :param VLogType type: Type of log
        :raise ValueError: On types not in ``VLogType``
        """
        super(Type, self).__init__()
        self._shorten_type = False
        if type in list(VLogType):
            self._type = type
        else:
            raise ValueError("Invalid type '" + type + "'")

    def __str__(self):
        """Convert type field to ``str``."""
        if self._shorten_type:
            output = self._type.value
        else:
            output = self._type.name
        if not self._display:
            output = ""
        if self._colorize and output:
            output = Colorize.type_apply(output, self._type)
        return output

    @property
    def logtype(self):
        return self._type

    @property
    def shorten_type(self):
        return self._shorten_type

    @shorten_type.setter
    def shorten_type(self, value=True):
        if isinstance(value, bool):
            self._shorten_type = value


class Source(LogField):
    """Represents the source field."""

    def __init__(self, source_token):
        """Initialize source field from ``str`` token.

        :param str source_token: Source token from VL log
        :raise ValueError: On value that doesn't follow source format
        """
        super(Source, self).__init__()
        try:
            source_token = source_token.strip("[]")
            module, _, line_number = source_token.partition(":")
            if not line_number:
                raise ValueError
        except ValueError:
            msg = "The source token '" + source_token + "' is not valid."
            raise ValueError(msg)
        self._module = module
        self._line_number = int(line_number)
        self._shorten_amount = 0

    def __str__(self):
        """Convert source field to ``str``."""
        output = ""
        if self._display:
            output = "".join([self._module, ":", str(self._line_number)])
            if self._shorten_amount and len(output) > self._shorten_amount - 2:
                output = "".join([output[:self._shorten_amount - 3], "..."])
            output = "".join(["[", output, "]"])
        return output

    @property
    def module(self):
        return self._module

    @property
    def line_number(self):
        return self._line_number

    @property
    def shorten_amount(self):
        return self._shorten_amount

    @shorten_amount.setter
    def shorten_amount(self, value=0):
        if isinstance(value, int):
            self._shorten_amount = value


class Thread(LogField):
    """Represents the thread field."""

    def __init__(self, thread_token):
        """Initialize thread field from ``str`` token.

        :param str thread_token: Thread token from VL log
        :raise ValueError: On value that doesn't follow thread format
        """
        super(Thread, self).__init__()
        try:
            thread_token = thread_token.strip("[]")
            process, _, thread = thread_token.partition(":")
            if not thread:
                raise ValueError
        except ValueError:
            msg = "The thread token '" + thread_token + "' is not valid."
            raise ValueError(msg)
        self._process = process
        self._thread = thread
        self._shorten_amount = 0

    def __str__(self):
        """Convert thread field to ``str``."""
        output = ""
        if self._display:
            output = "".join([self._process, ":", self._thread])
            if self._shorten_amount and len(output) > self._shorten_amount - 2:
                output = "".join([output[:self._shorten_amount - 3], "..."])
            output = "".join(["[", output, "]"])
        return output

    @property
    def process(self):
        return self._process

    @property
    def thread(self):
        return self._thread

    @property
    def shorten_amount(self):
        return self._shorten_amount

    @shorten_amount.setter
    def shorten_amount(self, value=0):
        if isinstance(value, int):
            self._shorten_amount = value


class Details(LogField):
    """Represents the details field."""

    def __init__(self, details_token):
        """Initialize thread field from ``str`` token."""
        super(Details, self).__init__()

        self._details = details_token

        # Only used when format_api_calls() is called.
        self._request_method = None
        self._request_url = None
        self._request_id = None
        self._request_params = None
        self._response_id = None
        self._response_result = None
        self._response_type = None

    def __str__(self):
        """Convert details field to ``str``."""
        output = ""
        if self._display:
            if self._is_api_request():
                output = self._api_request_str()
            elif self._is_api_response():
                output = self._api_response_str()
            else:
                output = self._details
        return output

    def format_api_calls(self):
        """When converted to string, the API requests and responses will be formatted."""
        m = re.match(VPatterns.get_std_details_api(), self._details)
        if m:
            if m.group(1):
                request = re.match(VPatterns.get_std_details_request(), self._details)
                if request.group(2) != 'None':
                    request_json = json.loads(request.group(2))
                    self._request_url = request.group(1)
                    self._request_id = int(request_json['id'])
                    self._request_method = request_json['method']
                    self._request_params = request_json['params']
            else:
                response = re.match(VPatterns.get_std_details_response(), self._details)
                string = response.group(1)
                json_response = json.loads(string)
                self._response_id = json_response['id']
                if 'result' in json_response:
                    self._response_result = json_response['result']
                    self._response_type = 'Result'
                elif 'error' in json_response:
                    self._response_result = json_response['error']
                    self._response_type = 'Error'

    def _is_api_request(self):
        """Return ``True`` if detail contains an API request."""
        return bool(self._request_id)

    def _is_api_response(self):
        """Return ``True`` if detail contains an API response."""
        return bool(self._response_id)

    def _is_api_call(self):
        """Return ``True`` if detail contains an API call."""
        return self._is_api_request() or self._is_api_response()

    def _api_request_str(self):
        """Return API request in as a formatted string."""
        json_post = "JSON-RPC-POST "
        req = "request"
        id = "id: {}".format(self._request_id)
        if self._colorize:
            json_post = Colorize.apply(json_post, 'json-post')
            req = Colorize.apply(req, 'api-request')
            id = Colorize.apply(id, 'api-id')

        output = ["\n  {}{} ({})".format(json_post, req, id)]
        output.append("    Method: {}".format(self._request_method))
        output.append("    URL: {}".format(self._request_url))
        params = pprint.pformat(self._request_params) if self._request_params else None
        output.append("""    Params: {}""".format(params))
        return "\n".join(output)

    def _api_response_str(self):
        """Return API response in as a formatted string."""
        json_post = "JSON-RPC-POST "
        res = "response"
        id = "id: {}".format(self._response_id)
        if self._colorize:
            json_post = Colorize.apply(json_post, 'json-post')
            res = Colorize.apply(res, 'api-response')
            id = Colorize.apply(id, 'api-id')

        output = ["\n  {}{} ({}): {}".format(json_post, res, id, self._response_type)]
        result = pprint.pformat(self._response_result) if self._response_result else None
        output.append("""    {}""".format(result))
        return "\n".join(output)


class TracebackStep(LogField):
    """Represents the traceback step field."""

    def __init__(self, step_token, leading_chars=""):
        """Initialize step fields from ``str`` token."""
        super(TracebackStep, self).__init__()
        m = re.match(VPatterns.TRACEBACK_STEP_PATTERN, step_token)
        self._leading_chars = leading_chars
        if m:
            self._file = m.group(1)
            self._line_num = int(m.group(2))
            self._function = m.group(3)
            self._line = m.group(4)
        else:
            self._file = ""
            self._line_num = 0
            self._function = ""
            self._line = ""

    def __str__(self):
        """Convert traceback step field to ``str``."""
        line_num = self._line_num
        path, filename = os.path.split(self._file)
        funct = self._function
        if self._colorize:
            line_num = Colorize.apply(str(line_num), 'traceback-line-num')
            funct = Colorize.apply(funct, 'traceback-funct')
            filename = Colorize.apply(filename, 'traceback-filename')
        tb_file = os.path.join(path, filename)
        output = "{0}  File \"{1}\", line {2}, in {3}\n{0}    {4}".format(self._leading_chars,
                                                                          tb_file, line_num,
                                                                          funct, self._line)
        return output

    @property
    def file(self):
        return self._file

    @property
    def line_num(self):
        return self._line_num

    @property
    def function(self):
        return self._function

    @property
    def line(self):
        return self._line


class TracebackException(LogField):
    """Represents the traceback exception field."""

    def __init__(self, exception_token, leading_chars=""):
        """Initialize exception field from ``str`` token."""
        super(TracebackException, self).__init__()
        self._colorize = False
        m = re.match(VPatterns.TRACEBACK_EXCEPTION_PATTERN, exception_token)
        self._leading_chars = leading_chars
        if m:
            self._exception = m.group(1)
            self._desc = m.group(2)
        else:
            self._exception = ""
            self._desc = ""

    def __str__(self):
        """Convert traceback exception field to ``str``."""
        exception = self._exception
        desc = self._desc
        if self._colorize:
            exception = Colorize.apply(exception, 'traceback-exception')
            desc = Colorize.apply(desc, 'traceback-description')
        output = "{0}{1}: {2}".format(self._leading_chars, exception, desc)
        return output

    @property
    def exception(self):
        return self._exception

    @property
    def desc(self):
        return self._desc

