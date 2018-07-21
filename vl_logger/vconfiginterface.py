from vl_logger import vlogline
from vl_logger import vformatter
from vl_logger.vutils import VLogStdFields
from vl_logger.vutils import VLogType

from collections import OrderedDict
import configparser
import os

DEFAULT_CONFIG_DIR = os.path.expanduser("~")
FORMAT_CONFIG_FILE_NAME = ".vl_logger.ini"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR + "/" + FORMAT_CONFIG_FILE_NAME

# Section names
AT2_TASKINSTANCE_CREDENTIALS = "AT2 LOG CREDENTIALS"
DISPLAY_LOG_TYPES_SECT = "DISPLAY LOG TYPES"
DISPLAY_FIELDS_SECT = "DISPLAY FIELDS"
GENERAL = "GENERAL"


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
        config = VConfigInterface(use_default=True)

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

    def __init__(self, use_default=False, use_unformatted=False):
        """Initialize the Config Interface."""
        if use_default and not use_unformatted:
            self.use_default()
        elif not use_default and use_unformatted:
            self.use_unformatted()
        self._format_config = None

    def create_config_file(self, file_directory=""):
        """Creates a config parser file within the current working directory containing the options for
        formatting log lines.

        :param str file_directory: File directory to store format config file. If not specified, then will
            store in the user's home directory.
        """

        config_fields = OrderedDict()

        # Username and password for grabbing AT2 logs from a task instance ID.
        config_fields[AT2_TASKINSTANCE_CREDENTIALS] = [
            ("username", ""),
            ("password", ""),
            ("at2_url", "https://")]

        # Log lines identified by the following types to be printed or ignored
        config_fields[DISPLAY_LOG_TYPES_SECT] = [
            ("debug", "False"),
            ("info", "True"),
            ("notice", "True"),
            ("step", "True"),
            ("title", "True"),
            ("warning", "True"),
            ("error", "True"),
            ("other", "True")]

        # Elements within each log line to be printed or ignored
        config_fields[DISPLAY_FIELDS_SECT] = [
            ("date", "False"),
            ("time", "True"),
            ("type", "True"),
            ("source", "True"),
            ("thread", "False"),
            ("details", "True")]

        config_fields[GENERAL] = [
            ("use_colors", "True"),
            ("format api", "False"),
            ("condense line", "True"),
            ("shorten fields", "True"),
            ("display summary", "True"),
            ("use_console_len", "True"),  # Use console width for max log line length
            ("max_line_len", "200")]  # Max length to be printed if console width is not selected

        # Create and add sections and options to configparser object
        self._format_config = configparser.ConfigParser()
        if file_directory:
            config_path = file_directory + "/" + FORMAT_CONFIG_FILE_NAME
        else:
            config_path = DEFAULT_CONFIG_DIR + "/" + FORMAT_CONFIG_FILE_NAME

        # If format config file doesn't already exist, create and write, otherwise read from existing file.
        if not os.path.isfile(config_path):
            for section, options in config_fields.items():
                self._format_config.add_section(section)
                for option in options:
                    self._format_config.set(section, option[0], option[1])
            with open(config_path, "wb") as configfile:
                self._format_config.write(configfile)
        else:
            self._format_config.read(config_path)

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
        self.shorten_fields()
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
        self.shorten_fields(0)
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

    def format_api(self, set=True):
        """Format the API requests and responses."""
        vlogline.Base.format_api(set)
        if VLogType.DEBUG not in vformatter.VFormatter.DISPLAY_LOG_TYPES:
            vformatter.VFormatter.DISPLAY_LOG_TYPES.append(VLogType.DEBUG)

    def condense_line(self, set=True):
        """Condense the ``str`` output of standard logs to the specified max line length."""
        vlogline.Base.condense_line(set)

    def shorten_fields(self, value=30):
        """Printed log types are shortened to 5 characters to ensure consistency between lines."""
        vlogline.Base.shorten_fields(value)

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

    def display_test_case(self, name="", number=-1):
        vformatter.VFormatter.display_test_case(name, number)

    def display_step(self, number=-1):
        vformatter.VFormatter.display_step(number)

    def display_summary(self, set=True):
        vformatter.VFormatter.display_summary(set)
