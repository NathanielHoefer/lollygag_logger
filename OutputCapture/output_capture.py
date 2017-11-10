import subprocess
import sys
import time
import tempfile
from enum import Enum
import configparser
import re

LINE_ELEMENTS = ("date", "time", "type", "source", "thread", "details")
TYPE_DEBUG = "DEBUG"
TYPE_INFO = "INFO"
TYPE_WARNING = "WARNING"
TYPE_STEP = "STEP"
TYPE_TITLE = "TITLE"
TYPE_OTHER = "OTHER"
LOG_TYPES = (TYPE_DEBUG, TYPE_INFO, TYPE_WARNING, TYPE_STEP, TYPE_TITLE, TYPE_OTHER)


class LogType(Enum):
    DEBUG = 1
    INFO = 2
    STEP = 3
    TITLE = 4
    OTHER = 5

    # TODO - Figure out a better solution to this
    @classmethod
    def type_str_len(cls):
        return 5

    @classmethod
    def find_log_type(cls, log_type_str):
        if log_type_str.upper() == TYPE_DEBUG:
            return TYPE_DEBUG
        elif log_type_str.upper() == TYPE_INFO:
            return TYPE_INFO
        elif re.match("(\-\-\-)+", log_type_str):
            return TYPE_STEP
        elif re.match("(===)+", log_type_str):
            return TYPE_TITLE
        else:
            return TYPE_OTHER


class LogLine:
    CONDENSE_LEN = 100              # Max number of characters to show of details when condensed
    COND_LIST_DISPLAY_LEN = 10      # Number of characters to show within condensed list or dict

    def __init__(self, line=""):
        self.date = ""
        self.time = ""
        self.type = LogType.OTHER
        self.source = ""
        self.thread = ""
        self.details = ""

        self._parse_line(line)

    def _parse_line(self, input):
        input.strip()
        is_standard = re.match("[0-9]{4}\-[0-9]{2}\-[0-9]{2}", input)
        if is_standard:
            split = input.split(" ", 5)
            self.date = split[0]
            self.time = split[1]
            self.type = split[2]
            self.source = split[3]
            self.thread = split[4]
            self.details = split[5]
        else:
            self.type = LogType.find_log_type(input)
            self.details = input

    def condensed_details(self):
        return self._condense(self.details, collapse_list=True, collapse_dict=True)

    def condensed_source(self):
        return self._condense(self.source, collapse_list=True)

    def condensed_thread(self):
        return self._condense(self.thread, collapse_list=True)

    def _condense(self, str_element, collapse_list=False, collapse_dict=False):
        output = str_element
        if collapse_list and collapse_dict:
            output = self._collapse(output, "[", "]")
            output = self._collapse(output, "{", "}")
        elif collapse_list:
            output = self._collapse(output, "[", "]")
        elif collapse_dict:
            output = self._collapse(output, "{", "}")

        # import pdb; pdb.set_trace()
        if len(output) > self.CONDENSE_LEN:
            output = "".join([output[:self.CONDENSE_LEN], "..."])
        return output.strip()

    def _collapse(self, str_element, start_char, end_char):
        start_index = str_element.find(start_char)
        end_index = str_element.find(end_char)
        if 0 <= start_index <= self.CONDENSE_LEN \
                and start_index < end_index <= self.CONDENSE_LEN \
                and end_index - start_index > self.COND_LIST_DISPLAY_LEN:
            return "".join([str_element[:start_index + self.COND_LIST_DISPLAY_LEN], "...", end_char])
        return str_element

class LogFormatter:
    VALID_TRUE_INPUT = ("true", "yes", "t", "y", "1")

    @staticmethod
    def format_line(log_line):
        config = configparser.ConfigParser()
        config.read("/home/hnathani/repos/hoefer/lollygag-logger/OutputCapture/format_config")

        if not config.sections():
            return log_line

        display_log_types = config["DISPLAY LOG TYPES"]
        display_elements = config["DISPLAY ELEMENTS"]
        condense_elements = config["CONDENSE ELEMENTS"]
        # import pdb; pdb.set_trace()
        output = []

        log_type = log_line.type.upper()
        if log_type in config["DISPLAY LOG TYPES"] and not LogFormatter._str_to_bool(display_log_types[log_type]):
            return ""


        if log_type == TYPE_TITLE or log_type == TYPE_STEP or log_type == TYPE_OTHER:
            return log_line.details
        if LogFormatter._str_to_bool(display_elements["DisplayDate"]):
            output.append(log_line.date)
        if LogFormatter._str_to_bool(display_elements["DisplayTime"]):
            output.append(log_line.time)
        if LogFormatter._str_to_bool(display_elements["DisplayType"]):
            output.append(log_line.type.ljust(LogType.type_str_len()))
        if LogFormatter._str_to_bool(display_elements["DisplaySource"]):
            if LogFormatter._str_to_bool(condense_elements["CondSource"]):
                output.append(log_line.condensed_source())
            else:
                output.append(log_line.source)
        if LogFormatter._str_to_bool(display_elements["DisplayThread"]):
            if LogFormatter._str_to_bool(condense_elements["CondThread"]):
                output.append(log_line.condensed_thread())
            else:
                output.append(log_line.thread)
        if LogFormatter._str_to_bool(display_elements["DisplayDetails"]):
            if LogFormatter._str_to_bool(condense_elements["CondDetails"]):
                output.append(log_line.condensed_details())
            else:
                output.append(log_line.details)
        return " ".join(output)

    @classmethod
    def _str_to_bool(cls, input):
        return input.lower() in cls.VALID_TRUE_INPUT


def format_print_file(filepath):
    # TODO - Edit to associate steps and titles not as type other
    with open(filepath, "r") as file:
        for line in file.readlines():
            if line == "\n":
                print ""
            else:
                line = line.strip("\n\\n")
                f = LogFormatter.format_line(LogLine(line))
                if not f:
                    continue
                print f


if __name__ == '__main__':


    # line = "2017-10-30 19:13:23.871372 DEBUG [sf_platform.core.retry_handlers.retry_wrapper:624] [MainProcess:MainThread] CallContext 63: UUID=63-6589ff16-bda6-11e7-89b9-6c0b84e27010, function=call_readonly_cluster_api, call_stack=[/home/hnathani/repos/suites_refresh/nathaniel/nathaniel-sr-autoplatform/sf_platform/cluster_api.py:get_constants:3722, from /home/hnathani/repos/suites_refresh/nathaniel/nathaniel-sr-autoplatform/sf_platform/api/ApiVolume.py:purge_deleted_volumes:1207, from /home/hnathani/repos/suites_refresh/nathaniel/nathaniel-sr-autotest-content/steps/AutotestVolume.py:delete_volumes:1984, from /home/hnathani/repos/suites_refresh/nathaniel/nathaniel-sr-autotest-content/tests/bulk_volume/cases/bulk_volume_operations.py:_teardown:692, from /home/hnathani/repos/suites_refresh/nathaniel/nathaniel-sr-autoplatform/valence_repo/valence/camelot/case.py:_internal_teardown:339]"
    # log_line = LogLine(line)
    # print(log_line.type)
    # print(log_line.date)
    # print LogFormatter.format_line(log_line, condense_details=True)
    # print(LogFormatter.format_line(log_line, condense_details=True, source=False, thread=False))

    # path = "/home/nathaniel/Repos/lollygag_logger/OutputCapture/test.log"
    path = "/home/hnathani/vl_artifacts/TsCreateDeleteAccountsVolSnap-2017-09-22T14.12.18/test.log"
    # path = "/home/hnathani/Documents/OutputCapture/testlogs.log"

    format_print_file(path)

    log_format = {
        "date":True,
        "time":True,
        "type":True,
        "details":True
    }
    #print log_line.format_line(**log_format)

    # line = "2017-10-30 19:13:22.383767 INFO [sf_platform.api.ApiVolume.delete_volumes:1185] [MainProcess:MainThread] Deleting volumes: [203, 204]."
    # log_line = LogLine(line)
    # print(log_line.type)
    # print(log_line.date)
    #
    # line = "=========================================================================================================\n"
    # print LogFormatter.format_line(LogLine(line))
    # print(log_line.type)
    # print(log_line.date)


    # print("Starting")
    # proc = subprocess.Popen(['python', r'C:\Users\natha\Downloads\OutputCapture\output_print.py'], stdout=subprocess.PIPE,
    #                         bufsize=1, universal_newlines=False)
    # for line in iter(proc.stdout.readline, b''):
    #     print("Captured Output: {}".format(line.decode("utf-8").rstrip(), flush=True))
    # proc.stdout.close()
    # proc.wait()