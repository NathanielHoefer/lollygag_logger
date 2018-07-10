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
        self.shorten_type = False
        if type in list(VLogType):
            self.type = type
        else:
            raise ValueError("Invalid type '" + type + "'")

    def __str__(self):
        """Convert type field to ``str``."""
        if self.shorten_type:
            output = self.type.value
        else:
            output = self.type.name
        if not self.display:
            output = ""
        if self.colorize and output:
            output = Colorize.type_apply(output, self.type)
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
        self.colorize = False

        # Only used when format_api_calls() is called.
        self.request_method = None
        self.request_url = None
        self.request_id = None
        self.response_id = None
        self.response_result = None
        self.response_type = None

    def __str__(self):
        """Convert details field to ``str``."""
        output = ""
        if self.display:
            if self.is_api_request():
                output = self._api_request_str()
            elif self.is_api_response():
                output = self._api_response_str()
            else:
                output = self.details
        return output

    def format_api_calls(self):
        """When converted to string, the API requests and responses will be formatted."""
        m = re.match(VPatterns.get_std_details_api(), self.details)
        if m:
            if not m.group(1):
                request = re.match(VPatterns.get_std_details_request(), self.details)
                self.request_method = request.group(1)
                self.request_url = request.group(2)
                self.request_id = int(request.group(3))
            else:
                response = re.match(VPatterns.get_std_details_response(), self.details)
                string = response.group(1)
                json_response = json.loads(string)
                self.response_id = json_response['id']
                # self.response_result = json_response
                if 'result' in json_response:
                    self.response_result = json_response['result']
                    self.response_type = 'Result'
                elif 'error' in json_response:
                    self.response_result = json_response['error']
                    self.response_type = 'Error'

    def is_api_request(self):
        """Return ``True`` if detail contains an API request."""
        return bool(self.request_id)

    def is_api_response(self):
        """Return ``True`` if detail contains an API response."""
        return bool(self.response_id)

    def is_api_call(self):
        """Return ``True`` if detail contains an API call."""
        return self.is_api_request() or self.is_api_response()

    def _api_request_str(self):
        json_post = "JSON-RPC-POST "
        req = "request"
        id = "id: {}".format(self.request_id)
        if self.colorize:
            json_post = Colorize.apply(json_post, 'json-post')
            req = Colorize.apply(req, 'api-request')
            id = Colorize.apply(id, 'api-id')

        output = ["\n  {}{} ({})".format(json_post, req, id)]
        output.append("    Method: {}".format(self.request_method))
        output.append("    URL: {}".format(self.request_url))
        return "\n".join(output)

    def _api_response_str(self):
        json_post = "JSON-RPC-POST "
        res = "response"
        id = "id: {}".format(self.response_id)
        if self.colorize:
            json_post = Colorize.apply(json_post, 'json-post')
            res = Colorize.apply(res, 'api-response')
            id = Colorize.apply(id, 'api-id')

        output = ["\n  {}{} ({}): {}".format(json_post, res, id, self.response_type)]
        result = pprint.pformat(self.response_result) if self.response_result else None
        output.append("""    {}""".format(result))
        return "\n".join(output)


class TracebackStep(LogField):
    """Represents the traceback step field."""

    def __init__(self, step_token, leading_chars=""):
        """Initialize step fields from ``str`` token."""
        self.colorize = False
        m = re.match(VPatterns.TRACEBACK_STEP_PATTERN, step_token)
        self.leading_chars = leading_chars
        if m:
            self.file = m.group(1)
            self.line_num = int(m.group(2))
            self.function = m.group(3)
            self.line = m.group(4)
        else:
            self.file = ""
            self.line_num = 0
            self.function = ""
            self.line = ""

    def __str__(self):
        """Convert traceback step field to ``str``."""
        line_num = self.line_num
        path, filename = os.path.split(self.file)
        funct = self.function
        if self.colorize:
            line_num = Colorize.apply(str(line_num), 'traceback-line-num')
            funct = Colorize.apply(funct, 'traceback-funct')
            filename = Colorize.apply(filename, 'traceback-filename')
        tb_file = os.path.join(path, filename)
        output = "{0}  File \"{1}\", line {2}, in {3}\n{0}    {4}".format(self.leading_chars,
                                                                          tb_file, line_num,
                                                                          funct, self.line)
        return output

    def get_file(self):
        return self.file

    def get_line_num(self):
        return self.line_num

    def get_function(self):
        return self.function

    def get_line(self):
        return self.line

    def set_colorize(self, set=True):
        self.colorize = set


class TracebackException(LogField):
    """Represents the traceback exception field."""

    def __init__(self, exception_token, leading_chars=""):
        """Initialize exception field from ``str`` token."""
        self.colorize = False
        m = re.match(VPatterns.TRACEBACK_EXCEPTION_PATTERN, exception_token)
        self.leading_chars = leading_chars
        if m:
            self.exception = m.group(1)
            self.desc = m.group(2)
        else:
            self.exception = ""
            self.desc = ""

    def __str__(self):
        """Convert traceback exception field to ``str``."""
        exception = self.exception
        desc = self.desc
        if self.colorize:
            exception = Colorize.apply(exception, 'traceback-exception')
            desc = Colorize.apply(desc, 'traceback-description')
        output = "{0}{1}: {2}".format(self.leading_chars, exception, desc)
        return output

    def get_exception(self):
        return self.exception

    def get_desc(self):
        return self.desc
