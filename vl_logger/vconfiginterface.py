from vl_logger import vlogline
from vl_logger import vformatter
from vl_logger.vutils import VLogStdFields
from vl_logger.vutils import VLogType


class VConfigInterface:
    """An interface for specifying VFormatter configuration options.

    Settings modify how the logs are printed to the console.
    For the settings offered, see methods listed below.

    There are three options when specifying the settings:
        - Default: Use the default settings
        - Manual: Define each setting manually via methods
        - Unformatted: No formatting done

    To implemenent, simply instantiate it before running ``LollygagLogger``

    .. code-block:: python
        :caption: Implementation

        # Default option
        config = VConfigInterface()

        # Manual option
        from vl_logger.vutils import VLogType
        config = VConfigInterface()
        config.display_fields([
            VLogType.WARNING,
            VLogType.ERROR,
            VLogType.CRITICAL,
            VLogType.TRACEBACK
        ])

        # Unformatted option
        config = VConfigInterface(use_unformatted=True)
    """

    def __init__(self, use_unformatted=False):
        """Initialize the Config Interface."""
        if use_unformatted:
            self.use_unformatted()
        else:
            self.use_default()

    def use_default(self):
        """Use the default settings as described below.

        - Colorize: True
        - Condense Lines: True
        - Shorten Log Type: True
        - Use console width (if available): True
        - Standard log fields to display:
            - Time
            - Type
            - Source
            - Details
        - Log Types to display:
            - Info
            - Notice
            - Warning
            - Error
            - Critical
            - Traceback
            - Other
            - Step header
            - Test Case Header
            - Suite Header
            - General Header
        """
        self.colorize()
        self.condense_line()
        self.shorten_type()
        self.use_console_width()
        self.display_fields([
            VLogStdFields.TIME,
            VLogStdFields.TYPE,
            VLogStdFields.SOURCE,
            VLogStdFields.DETAILS
        ])
        self.display_log_types([
            VLogType.INFO,
            VLogType.NOTICE,
            VLogType.WARNING,
            VLogType.ERROR,
            VLogType.CRITICAL,
            VLogType.TRACEBACK,
            VLogType.OTHER,
            VLogType.STEP_H,
            VLogType.TEST_CASE_H,
            VLogType.SUITE_H,
            VLogType.GENERAL_H
        ])

    def use_unformatted(self):
        """Don't use any formatting at all."""
        self.max_line_len(105)
        self.colorize(False)
        self.condense_line(False)
        self.shorten_type(False)
        self.use_console_width(False)
        self.display_fields([
            VLogStdFields.DATE,
            VLogStdFields.TIME,
            VLogStdFields.TYPE,
            VLogStdFields.SOURCE,
            VLogStdFields.THREAD,
            VLogStdFields.DETAILS
        ])
        self.display_log_types([
            VLogType.DEBUG,
            VLogType.INFO,
            VLogType.NOTICE,
            VLogType.WARNING,
            VLogType.ERROR,
            VLogType.CRITICAL,
            VLogType.TRACEBACK,
            VLogType.OTHER,
            VLogType.STEP_H,
            VLogType.TEST_CASE_H,
            VLogType.SUITE_H,
            VLogType.GENERAL_H
        ])

    def max_line_len(self, length=105):
        """Set the maximum length of the standard log line strings when printed.

        This doesn't include header descriptions, tracebacks, or logs not classified.

        :param int max_len: Max number of chars to print for each string.
        """
        vlogline.Base.set_max_line_len(length)

    def colorize(self, set=True):
        """Use the colored option if available in a ``LogLine`` object."""
        vlogline.Base.colorize(set)

    def condense_line(self, set=True):
        """Condense the ``str`` output of standard logs to the specified max line length."""
        vlogline.Base.shorten_type(set)

    def shorten_type(self, set=True):
        """Printed log types are shortened to 5 characters to ensure consistency between lines."""
        vlogline.Base.shorten_type(set)

    def use_console_width(self, set=True):
        """Use the console width as the max line width if available."""
        vformatter.VFormatter.use_console_width(set)

    def display_fields(self, fields):
        """Print only the ``VLogStdFields`` specified.

        :param [VLogStdFields] fields: The enums specifying which logs to print.

        .. code-block:: python

            from vl_logger.vutils import VLogStdFields
            Base.display_fields([VLogStdFields.TIME, VLogStdFields.TYPE])
        """
        vlogline.Base.display_fields(fields)

    def display_log_types(self, types):
        """Print only the ``VLogType``s specified.

        :param [VLogType] types: The enums specifying which logs types to print.

        .. code-block:: python

            from vl_logger.vutils import VLogType
            VFormatter.set_display_log_types([VLogType.DEBUG, VLogType.INFO])
        """
        vformatter.VFormatter.display_log_types(types)
