"""
=========================================================================================================
Enum Classes
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/30/2017
"""

from enum import Enum


class ColorType(Enum):
    """Enums representing colors for each log line type."""

    DEBUG = '\033[35m'      # Purple
    INFO = '\033[34m'       # Blue
    NOTICE = '\033[32m'     # Green
    WARNING = '\033[33m'    # Yellow
    ERROR = '\033[31m'      # Red
    STEP = '\033[92m'       # Bright Green
    TITLE = '\033[93m'      # Bright Yellow
    OTHER = '\033[0m'       # None
    HIGHLIGHT = '\033[101m'  # Bright Red Background
    END = '\033[0m'

    __order__ = "DEBUG INFO WARNING ERROR STEP TITLE OTHER HIGHLIGHT END"


class LogType(Enum):
    """Enums representing the types of log lines."""

    DEBUG = 'DEBUG'
    INFO = 'INFO'
    NOTICE = 'NOTE'
    WARNING = 'WARN'
    ERROR = 'ERROR'
    STEP = 'STEP'
    TITLE = 'TITLE'
    OTHER = 'OTHER'

    __order__ = "DEBUG INFO WARNING ERROR STEP TITLE OTHER"

    def __str__(self):
        return self.value.ljust(5, " ")


class HeaderType(Enum):
    """Enums representing the types of headers."""

    VALENCE = 1
    SUITE = 2
    TEST_CASE = 3
    STEP = 4
    OTHER = 5

    __order__ = "VALENCE SUITE TEST_CASE STEP OTHER"


class ValenceField(Enum):
    """Enums representing the different fields in Valence logs."""

    DATE = 'date'
    TIME = 'time'
    TYPE = 'type'
    SOURCE = 'source'
    THREAD = 'thread'
    DETAILS = 'details'

    __order__ = 'DATE TIME TYPE SOURCE THREAD DETAILS'


class ListingStatus(Enum):
    """Enums representing the various listing statuses."""

    SEARCHING = 1
    PROCESSING = 2
    COMPLETED = 3
