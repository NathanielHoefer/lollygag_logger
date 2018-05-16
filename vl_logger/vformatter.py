from vl_logger.lollygag_logger import LogFormatter

class VFormatter(LogFormatter):

    def __init__(self):
        pass

    def format(self, unf_str):
        return unf_str

    def send(self, fmt_log):
        print fmt_log