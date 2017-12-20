"""
=========================================================================================================
Enum Classes
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/20/2017
"""

import helpers


class ColorType:

    DEBUG = '\033[35m'
    INFO = '\033[34m'
    WARNING = '\033[33m'
    ERROR = '\033[31m'
    STEP = '\033[92m'
    TITLE = '\033[93m'
    OTHER = '\033[0m'
    END = '\033[0m'

    @classmethod
    def color_by_type(cls, type, type_field):
        """Returns the type field with ANSI coloring format"""

        if type == "debug":
            return helpers.color_str(type_field, cls.DEBUG)
        elif type == "info":
            return helpers.color_str(type_field, cls.INFO)
        elif type == "warning":
            return helpers.color_str(type_field, cls.WARNING)
        elif type == "error":
            return helpers.color_str(type_field, cls.ERROR)
        elif type == "step":
            return helpers.color_str(type_field, cls.STEP)
        elif type == "title":
            return helpers.color_str(type_field, cls.TITLE)
        elif type == "other":
            return helpers.color_str(type_field, cls.OTHER)
        else:
            return type_field
