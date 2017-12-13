"""
=========================================================================================================
Valence Config File Methods and Constants
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/2/2017
"""

from collections import OrderedDict
import configparser

FORMAT_CONFIG_FILE_NAME = "format_config.ini"

# Section names
DISPLAY_LOG_TYPES_SECT = "DISPLAY LOG TYPES"
DISPLAY_FIELDS_SECT = "DISPLAY FIELDS"
CONDENSE_FIELDS_SECT = "CONDENSE FIELDS"
COLLAPSE_STRUCTS_SECT = "COLLAPSE STRUCTURES"
LENGTHS_SECT = "LENGTHS"


def create_config_file(filepath=""):
    """Creates a config parser file within the current working directory containing the options for
    formatting log lines.

    :param str filepath: File path to store format config file. Default is current working directory.
    """

    config_fields = OrderedDict()

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
        ("condensed_field_len", "100"),     # This value includes the "..."
        ("collapsed_struct_len", "30")]     # This value includes the "[" and "...]"

    # Create and add sections and options to configparser object
    format_config = configparser.ConfigParser()
    for section, options in config_fields.items():
        format_config.add_section(section)
        for option in options:
            format_config.set(section, option[0], option[1])

    # Write config to file in current working directory
    filepath = filepath if filepath else FORMAT_CONFIG_FILE_NAME
    with open(filepath, "wb") as configfile:
        format_config.write(configfile)

    return format_config
