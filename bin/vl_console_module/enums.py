"""
=========================================================================================================
Enum Classes
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/226/2017
"""

from enum import Enum


class ColorType(Enum):
    """Enums representing colors for each log line type."""

    DEBUG = '\033[35m'
    INFO = '\033[34m'
    WARNING = '\033[33m'
    ERROR = '\033[31m'
    STEP = '\033[92m'
    TITLE = '\033[93m'
    OTHER = '\033[0m'
    END = '\033[0m'


class LogType(Enum):
    """Enums representing the types of log lines."""
    # TODO - pip install enum34

    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    STEP = 'step'
    TITLE = 'title'
    OTHER = 'other'

