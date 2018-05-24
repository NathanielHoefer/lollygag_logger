from vl_logger.lollygag_logger import LogFormatter
from vl_logger import vlogline
from vl_logger.vutils import VLogType

class VFormatter(LogFormatter):

    def __init__(self):
        pass

    def format(self, unf_str):
        unf_str = unf_str.strip()
        type = VLogType.get_type(unf_str)
        if type:
            return vlogline.Standard(unf_str, type)
        else:
            return unf_str

    def send(self, fmt_log):
        print fmt_log