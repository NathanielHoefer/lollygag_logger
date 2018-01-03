"""
=========================================================================================================
Helper Functions
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/30/2017
"""

import copy
import re
from enums import ColorType, LogType

# Valid values from ConfigParser that result in True
VALID_TRUE_INPUT = ("true", "yes", "t", "y", "1")


def str_to_bool(str_bool_val):
    """Evaluates bool value of string input based on VALID_TRUE_INPUT.

    :param str str_bool_val: bool value as string
    :rtype: bool
    """
    return str_bool_val.lower() in VALID_TRUE_INPUT


def collapse_struct(field_str, data_struct, collapse_len=30):
    """Shortens the display of the first encountered list or dictionary to a specified length.

    If the length of the structure (including the '[]' or '{}' is > the
    collapsed_struct_len specified in config file, then the structure will be reduced to that length
    and indicated by an ellipse. Ex: [abcdefghijklmnopqrstuvwxyzab] -> [abcdefghijklmnopqrstuvwxy...]

    Currently only minimizes the out-most structure while ignoring the inner structures. Will look
    to fix this in the future if time allows. Note: There may be a bug with collapsing the wrong dicts.
    :param str field_str: The log line element str containing the data structure
    :param str data_struct: "list" or "dict" indicating what data structure to collapse
    :param int collapse_len: The max length of the structures
    :return: String of the element with the specified collapsed structure.
    :rtype: str
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
    """Condenses each field of a log line to the condense length, and collapses lists and dict.

    :param str field_str: The LogLine field str to be condensed.
    :param int condense_len: The max length of the field
    :param bool collapse_dict: If true, collapse dict to the specified collapse_len
    :param bool collapse_list: If true, collapse list to the specified collapse_len
    :param int collapse_len: The max length of the structures
    :rtype: str
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

    Does not count \033 escape sequences towards line length.
    :param str str_line: Line to be condensed
    :param int max_len: The maximum length of the line
    :rtype: str
    """

    # Determine the number of extra characters found in the escape sequences and add them to the
    # max_len since they won't add additional characters when printed to the console.
    esc_seq_list = re.findall('\\033\[\d+m', str_line[:max_len + 1])
    esc_seq_num = 0
    for esc_seq in esc_seq_list:
        esc_seq_num += len(esc_seq)
    max_len += esc_seq_num

    cont_str = "..."

    if len(str_line) > max_len:
        return "".join([str_line[:max_len - 3], cont_str])
    else:
        return str_line


def color_by_type(log_type, log_str):
    """Returns the type field with ANSI coloring format.

    :param LogType log_type: Enum of the log type which identifies the color
    :param str log_str: The string to be colored.
    :return: String colored using color value based on type.
    :rtype: str
    """

    return ColorType[log_type.name].value + log_str + ColorType.END.value


def print_variable_list(lst_input, funct):
    """Recursively print list from beginning to end executing the given function on each element.

    Does not affect original list.
    Note: funct must be a function that accepts an object for the first argument, and an indent depth as
        the second. Indent starts at 0. Ex: indent_print(object, 4)

    :param list lst_input: list to be printed
    :param function funct: Used to print each element in the list
    """

    lst = copy.deepcopy(lst_input)
    _print_list_rec(lst, funct, 0)


def _print_list_rec(lst_input, funct, depth):
    """Recursive function to print_variable_list."""
    if not lst_input:
        return 0

    el = lst_input.pop(0)
    if not isinstance(el, list):
        funct(el, depth)
    else:
        _print_list_rec(el, funct, depth + 1)
    _print_list_rec(lst_input, funct, depth)
