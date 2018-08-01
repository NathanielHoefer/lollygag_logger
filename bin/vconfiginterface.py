import os
import re
from collections import OrderedDict

import configparser
from bin.vutils import VLogStdFields
from bin.vutils import VLogType
from bin.vutils import VPatterns

from bin import vlogline
from bin import vformatter
from bin import vlogfield

DEFAULT_CONFIG_DIR = os.path.expanduser("~")
FORMAT_CONFIG_FILE_NAME = ".vlogger.ini"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR + "/" + FORMAT_CONFIG_FILE_NAME
# Valid values from ConfigParser that result in True
VALID_TRUE_INPUT = ("true", "yes", "t", "y", "1")

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

    def __init__(self, file_directory=""):
        """Initialize the Config Interface."""
        self._format_config = None
        self._config_ini_mod_time = None
        self._file_directory = file_directory
        self.create_config_file(self._file_directory)
        self.load_config_file(self._file_directory)

        use_defaults = self._str_to_bool(self._format_config[GENERAL]["use_defaults"])
        use_unformatted = self._str_to_bool(self._format_config[GENERAL]["use_unformatted"])

        if use_defaults and not use_unformatted:
            self.use_default()
        elif not use_defaults and use_unformatted:
            self.use_unformatted()


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
            ("fetch-task-instance-script-path", "fetch-task-instance-step-log.py")]

        # Log lines identified by the following types to be printed or ignored
        config_fields[DISPLAY_LOG_TYPES_SECT] = [
            ("debug", "False"),
            ("info", "True"),
            ("notice", "True"),
            ("warning", "True"),
            ("error", "True"),
            ("critical", "True"),
            ("traceback", "True"),
            ("other", "True"),
            ("step_headers", "True"),
            ("test_case_headers", "True"),
            ("suite_headers", "True"),
            ("general_headers", "True")]

        # Elements within each log line to be printed or ignored
        config_fields[DISPLAY_FIELDS_SECT] = [
            ("date", "False"),
            ("time", "True"),
            ("type", "True"),
            ("source", "True"),
            ("thread", "False"),
            ("details", "True")]

        config_fields[GENERAL] = [
            ("use_defaults", "False"),
            ("use_unformatted", "False"),
            ("use_colors", "True"),
            ("format_api", "False"),
            ("condense_line", "True"),
            ("shorten_fields", "True"),
            ("display_summary", "True"),
            ("use_console_len", "True"),  # Use console width for max log line length
            ("max_line_len", "200")]  # Max length to be printed if console width is not selected

        # Create and add sections and options to configparser object
        self._format_config = configparser.ConfigParser()
        if file_directory:
            self._config_path = file_directory + "/" + FORMAT_CONFIG_FILE_NAME
        else:
            self._config_path = DEFAULT_CONFIG_DIR + "/" + FORMAT_CONFIG_FILE_NAME

        # If format config file doesn't already exist, create and write, otherwise read from existing file.
        if not os.path.isfile(self._config_path):
            for section, options in config_fields.items():
                self._format_config.add_section(section)
                for option in options:
                    self._format_config.set(section, option[0], option[1])
            with open(self._config_path, "wb") as configfile:
                self._format_config.write(configfile)

    def load_config_file(self, file_directory=""):
        if file_directory:
            config_path = os.path.join(file_directory, FORMAT_CONFIG_FILE_NAME)
        else:
            config_path = os.path.join(DEFAULT_CONFIG_DIR, FORMAT_CONFIG_FILE_NAME)
        self._format_config.read(config_path)
        self._config_ini_mod_time = os.path.getmtime(config_path)
        self._load_config_file_log_types()
        self._load_config_file_fields()
        self._load_config_file_general()

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
        self.display_summary()
        self.colorize()
        self.format_api(False)
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
        self.display_summary(False)
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

    def get_at2_info(self):
        """Return AT2 username, password, and fetch-instance-script-path from .ini file.

        :return: Tuple (username, password, fetch-instance-script-path)
        """
        info = []
        info.append(self._format_config[AT2_TASKINSTANCE_CREDENTIALS].get("username"))
        info.append(self._format_config[AT2_TASKINSTANCE_CREDENTIALS].get("password"))
        info.append(self._format_config[AT2_TASKINSTANCE_CREDENTIALS].get("fetch-task-instance-script-path"))
        return tuple(info)

    def set_at2_info(self, at2_user, at2_pass, fetch_script):
        """Return AT2 username, password, and fetch-instance-script-path from .ini file."""
        self._format_config.set(AT2_TASKINSTANCE_CREDENTIALS, "username", at2_user)
        self._format_config.set(AT2_TASKINSTANCE_CREDENTIALS, "password", at2_pass)
        self._format_config.set(AT2_TASKINSTANCE_CREDENTIALS, "etch-task-instance-script-path", fetch_script)

    def is_at2_formatting(self, filepath):
        """Determines if the logs are using the AT2 format."""
        with open(filepath, 'r') as f:
            for line in f:
                if re.match(VPatterns.get_std(), line):
                   if re.search(VPatterns.get_at2_time(), line):
                       return True
                   else:
                       return False


    def output_file(self, filepath, log_file_wc):
        """Save formatted STDOUT to a file with progress bar."""
        vformatter.VFormatter.output_file(filepath, log_file_wc)

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
        if set and VLogType.DEBUG not in vformatter.VFormatter.DISPLAY_LOG_TYPES:
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

    def at2_format(self, set=True):
        vlogline.Base.at2_format(set)
        vlogfield.Datetime.at2_format(set)

    def _str_to_bool(self, str_bool_val):
        """Evaluates bool value of string input based on VALID_TRUE_INPUT.

        :param str str_bool_val: bool value as string
        :rtype: bool
        """
        return str_bool_val.lower() in VALID_TRUE_INPUT

    def _load_config_file_log_types(self):
        """Updates the display log types from the loaded config file."""
        types_dict = {}
        for key, val in self._format_config[DISPLAY_LOG_TYPES_SECT].items():
            types_dict[key] = self._str_to_bool(val)

        log_types = []
        if types_dict["debug"]:
            log_types.append(VLogType.DEBUG)
        if types_dict["info"]:
            log_types.append(VLogType.INFO)
        if types_dict["notice"]:
            log_types.append(VLogType.NOTICE)
        if types_dict["warning"]:
            log_types.append(VLogType.WARNING)
        if types_dict["error"]:
            log_types.append(VLogType.ERROR)
        if types_dict["critical"]:
            log_types.append(VLogType.CRITICAL)
        if types_dict["traceback"]:
            log_types.append(VLogType.TRACEBACK)
        if types_dict["other"]:
            log_types.append(VLogType.OTHER)
        if types_dict["step_headers"]:
            log_types.append(VLogType.STEP_H)
        if types_dict["test_case_headers"]:
            log_types.append(VLogType.TEST_CASE_H)
        if types_dict["suite_headers"]:
            log_types.append(VLogType.SUITE_H)
        if types_dict["general_headers"]:
            log_types.append(VLogType.GENERAL_H)
        self.display_log_types(log_types)

    def _load_config_file_fields(self):
        fields_dict = {}
        for key, val in self._format_config[DISPLAY_FIELDS_SECT].items():
            fields_dict[key] = self._str_to_bool(val)

        fields = []
        if fields_dict["date"]:
            fields.append(VLogStdFields.DATE)
        if fields_dict["time"]:
            fields.append(VLogStdFields.TIME)
        if fields_dict["type"]:
            fields.append(VLogStdFields.TYPE)
        if fields_dict["source"]:
            fields.append(VLogStdFields.SOURCE)
        if fields_dict["thread"]:
            fields.append(VLogStdFields.THREAD)
        if fields_dict["details"]:
            fields.append(VLogStdFields.DETAILS)
        self.display_fields(fields)

    def _load_config_file_general(self):
        general_dict = {}
        for key, val in self._format_config[GENERAL].items():
            general_dict[key] = self._str_to_bool(val)

        self.colorize(general_dict["use_colors"])
        self.format_api(general_dict["format_api"])
        self.condense_line(general_dict["condense_line"])
        self.shorten_fields(general_dict["shorten_fields"])
        self.display_summary(general_dict["display_summary"])
        self.use_console_width(general_dict["use_console_len"])
        self.max_line_len(int(self._format_config[GENERAL]["max_line_len"]))
