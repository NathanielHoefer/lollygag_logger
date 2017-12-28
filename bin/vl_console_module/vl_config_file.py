"""
=========================================================================================================
Valence Config File Methods and Constants
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/2/2017
"""

# TODO - Update file description

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
CONDENSE_FIELDS_SECT = "CONDENSE FIELDS"
COLLAPSE_STRUCTS_SECT = "COLLAPSE STRUCTURES"
LENGTHS_SECT = "LENGTHS"
COLORS = "COLORS"


def create_config_file(file_directory=""):
    """Creates a config parser file within the current working directory containing the options for
    formatting log lines.

    :param str file_directory: File directory to store format config file. If not specified, then will
        store in the user's home directory.
    """

    config_fields = OrderedDict()

    # Username and password for grabbing AT2 logs from a task instance ID.
    config_fields[AT2_TASKINSTANCE_CREDENTIALS] = [
        ("username", ""),
        ("password", "")]

    # Log lines identified by the following types to be printed or ignored
    config_fields[DISPLAY_LOG_TYPES_SECT] = [
        ("debug",   "False"),
        ("info",    "True"),
        ("step",    "True"),
        ("title",   "True"),
        ("warning", "True"),
        ("error",   "True"),
        ("other",   "True")]

    # Elements within each log line to be printed or ignored
    config_fields[DISPLAY_FIELDS_SECT] = [
        ("date",    "False"),
        ("time",    "True"),
        ("type",    "True"),
        ("source",  "True"),
        ("thread",  "False"),
        ("details", "True")]

    # Elements within each log line to be condensed to the specified length under the LENGTHS
    # section - condensed_elem_len
    config_fields[CONDENSE_FIELDS_SECT] = [
        ("date",    "False"),
        ("time",    "False"),
        ("type",    "False"),
        ("source",  "True"),
        ("thread",  "True"),
        ("details", "True")]

    # Data structures within elements to be condensed to be collapsed to the specified length under
    # the LENGTHS section - collapsed_struct_len
    config_fields[COLLAPSE_STRUCTS_SECT] = [
        ("list", "True"),
        ("dict", "True")]

    # Various length options
    config_fields[LENGTHS_SECT] = [
        ("use_console_len",     "True"),    # Use console width for max log line length
        ("max_line_len",        "200"),     # Max length of log line to be printed
        ("condensed_field_len", "300"),     # This value includes the "..."
        ("collapsed_struct_len", "30")]     # This value includes the "[" and "...]"

    config_fields[COLORS] = [
        ("use_colors", "True")
    ]

    # Create and add sections and options to configparser object
    format_config = configparser.ConfigParser()
    if file_directory:
        config_path = file_directory + "/" + FORMAT_CONFIG_FILE_NAME
    else:
        config_path = DEFAULT_CONFIG_DIR + "/" + FORMAT_CONFIG_FILE_NAME

    # If format config file doesn't already exist, create and write, otherwise read from existing file.
    if not os.path.isfile(config_path):
        for section, options in config_fields.items():
            format_config.add_section(section)
            for option in options:
                format_config.set(section, option[0], option[1])
        with open(config_path, "wb") as configfile:
            format_config.write(configfile)
    else:
        format_config.read(config_path)

    return format_config
