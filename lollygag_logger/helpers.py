"""
=========================================================================================================
Helper Functions
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/18/2017
"""

# Valid values from ConfigParser that result in True
VALID_TRUE_INPUT = ("true", "yes", "t", "y", "1")


def str_to_bool(str_bool_val):
    """Evaluates bool value of string input based on LogFormatter.VALID_TRUE_INPUT"""
    return str_bool_val.lower() in VALID_TRUE_INPUT


def collapse_struct(field_str, data_struct, collapse_len=30):
    """Shortens the display of the first encountered list or dictionary to a specified length within
    a given string. If the length of the structure (including the '[]' or '{}' is > the
    collapsed_struct_len specified in config file, then the structure will be reduced to that length
    and indicated by an ellipse. Ex: [abcdefghijklmnopqrstuvwxyzab] -> [abcdefghijklmnopqrstuvwxy...]

    Currently only minimizes the out-most structure while ignoring the inner structures. Will look
    to fix this in the future if time allows.

    :param str field_str: The log line element str containing the data structure
    :param str data_struct: "list" or "dict" indicating what data structure to collapse
    :param int collapse_len: The max length of the structures
    :return: String of the element with the specified collapsed structure.
    """
    # Determine struct entered
    if data_struct == "dict":
        start_char = "{"
        end_char = "}"
    elif data_struct == "list":
        start_char = "["
        end_char = "]"
    else:
        return field_str

    # Initialize collapse values - probably can find library to do this more efficiently
    start_index = field_str.find(start_char)
    end_index = field_str.find(end_char)

    # Collapse first data structure found
    if 0 <= start_index < end_index:
        struct = "".join([start_char,
                          condense(field_str[start_index + 1: end_index], collapse_len - 2), end_char])
        val = "".join([field_str[:start_index], struct, field_str[end_index + 1:]])
        return val

    return field_str


def condense_field(field_str, condense_len=50,
                   collapse_dict=False, collapse_list=False, collapse_len=30):
    """Condenses each field of a log line to the condense length, and collapses lists and dictionaries
    that exceed a given length.

    :param str field_str: The LogLine field str to be condensed.
    :param int condense_len: The max length of the field
    :param bool collapse_dict: If true, collapse dict to the specified collapse_len
    :param bool collapse_list: If true, collapse list to the specified collapse_len
    :param int collapse_len: The max length of the structures
    """

    # Collapse dicts or lists if specified
    current_field_str = field_str
    if collapse_dict:
        current_field_str = collapse_struct(current_field_str, "dict", collapse_len)
    if collapse_list:
        current_field_str = collapse_struct(current_field_str, "list", collapse_len)

    # Condense length of element if it exceeds specified length
    return condense(current_field_str, condense_len)


def condense(str_line, max_len):
    """Condenses the string if it is greater than the max length, appending ellipses.

    :param str str_line: Line to be condensed
    :param int max_len: The maximum length of the line
    """
    if len(str_line) > max_len:
        return "".join([str_line[:max_len - 3], "..."])
    else:
        return str_line
