import subprocess
import sys
import time
import tempfile
from enum import Enum
import re

LINE_ELEMENTS = ("date", "time", "type", "source", "thread", "details")

class LogType(Enum):
    DEBUG = 1
    INFO = 2
    STEP = 3
    TITLE = 4
    OTHER = 5

    @classmethod
    def find_log_type(cls, log_type_str):
        if log_type_str == "DEBUG":
            return cls.DEBUG
        elif log_type_str == "INFO":
            return cls.INFO
        elif re.match("(\-\-\-)+", log_type_str):
            return cls.STEP
        elif re.match("(===)+", log_type_str):
            return cls.TITLE
        else:
            return cls.OTHER


class LogLine:
    CONDENSE_LEN = 300              # Max number of characters to show of details when condensed
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
        is_standard = re.match("[0-9]{4}\-[0-9]{2}\-[0-9]{2}", input)
        if is_standard:
            split = input.split(" ", 5)
            self.date = split[0]
            self.time = split[1]
            self.type = LogType.find_log_type(split[2])
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
        list_index = -1
        dict_index = -1
        if collapse_list and collapse_dict:
            list_index = str_element.find("[", 0, self.CONDENSE_LEN)
            dict_index = str_element.find("{", 0, self.CONDENSE_LEN)
        elif collapse_list:
            list_index = str_element.find("[", 0, self.CONDENSE_LEN)
        elif collapse_dict:
            dict_index = str_element.find("{", 0, self.CONDENSE_LEN)

        if list_index < 0 and dict_index < 0:
            return "".join([str_element[:self.CONDENSE_LEN], "..."])
        elif list_index >= 0:
            index = list_index + self.COND_LIST_DISPLAY_LEN
            return "".join([str_element[:index], "...]"])
        else:
            index = dict_index + self.COND_LIST_DISPLAY_LEN
            return "".join([str_element[:index], "...}"])

class LogFormatter:

    @staticmethod
    def format_line(log_line, condense_details=False, date=True, time=True, type=True, source=True,
                    thread=True, details=True):
        output = []
        if date:
            output.append(log_line.date)
        if time:
            output.append(log_line.time)
        if type:
            output.append(log_line.type.name)
        if source:
            output.append(log_line.condensed_source())
        if thread:
            output.append(log_line.condensed_thread())
        if details:
            if condense_details:
                output.append(log_line.condensed_details())
            else:
                output.append(log_line.details)
        return " ".join(output)


def format_file(filepath, **kwargs):
    with open(filepath, "r") as file:
        for line in file:
            log = LogLine(line)


if __name__ == '__main__':


    line = "2017-10-30 19:13:23.871372 DEBUG [sf_platform.core.retry_handlers.retry_wrapper:624] [MainProcess:MainThread] CallContext 63: UUID=63-6589ff16-bda6-11e7-89b9-6c0b84e27010, function=call_readonly_cluster_api, call_stack=[/home/hnathani/repos/suites_refresh/nathaniel/nathaniel-sr-autoplatform/sf_platform/cluster_api.py:get_constants:3722, from /home/hnathani/repos/suites_refresh/nathaniel/nathaniel-sr-autoplatform/sf_platform/api/ApiVolume.py:purge_deleted_volumes:1207, from /home/hnathani/repos/suites_refresh/nathaniel/nathaniel-sr-autotest-content/steps/AutotestVolume.py:delete_volumes:1984, from /home/hnathani/repos/suites_refresh/nathaniel/nathaniel-sr-autotest-content/tests/bulk_volume/cases/bulk_volume_operations.py:_teardown:692, from /home/hnathani/repos/suites_refresh/nathaniel/nathaniel-sr-autoplatform/valence_repo/valence/camelot/case.py:_internal_teardown:339]"
    log_line = LogLine(line)
    print(log_line.type)
    print(log_line.date)
    print LogFormatter.format_line(log_line, condense_details=True)
    print(LogFormatter.format_line(log_line, condense_details=True, source=False, thread=False))

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
    # line = "========================================================================================================="
    # log_line = LogLine(line)
    # print(log_line.type)
    # print(log_line.date)


    # print("Starting")
    # proc = subprocess.Popen(['python', r'C:\Users\natha\Downloads\OutputCapture\output_print.py'], stdout=subprocess.PIPE,
    #                         bufsize=1, universal_newlines=False)
    # for line in iter(proc.stdout.readline, b''):
    #     print("Captured Output: {}".format(line.decode("utf-8").rstrip(), flush=True))
    # proc.stdout.close()
    # proc.wait()