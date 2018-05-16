from enum import Enum


class VLogType(Enum):
    """Enums representing the types of log lines."""

    DEBUG = 'DEBUG'
    INFO = 'INFO'
    NOTICE = 'NOTE'
    WARNING = 'WARN'
    ERROR = 'ERROR'
    CRITICAL = 'CRIT'
    OTHER = 'OTHER'
    STEP_H = 'STEP'
    TEST_CASE_H = 'TCASE'
    SUITE_H = 'SUITE'

    __order__ = "DEBUG INFO NOTICE WARNING ERROR CRITICAL OTHER STEP_H " \
                "TEST_CASE_H SUITE_H"