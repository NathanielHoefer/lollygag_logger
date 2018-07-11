from anytree import Node, RenderTree
from vl_logger.vutils import VLogType
from vl_logger import vlogline
from datetime import datetime

class HeaderManager:

    def __init__(self, tc_name=None, tc_num=None, step=None):
        """Intialize the HeaderManager.

        :param str tc_name: Name of test case to only be stored.
        :param int tc_num: Int of test case to only be stored.
        :param int step: Int of step to only be stored.
        """
        self._curr_general = None
        self._curr_suite = None
        self._curr_testcase = None
        self._curr_step = None

        self.root = Node(vlogline.GeneralHeader("=Test Summary="))
        self._header_tree = [self.root]

        self._store_tc_name = tc_name
        self._store_tc_num = tc_num
        self._store_step = step

    def generate_summary(self):
        """Return a string containing a summary of all the headers."""
        str_format = "%H:%M:%S.%f"

        self.calc_end_time()

        output = []
        for pre, fill, node in RenderTree(self.root):
            # if node.is_root:
            #     output.append(node.name.get_id())
            # else:
            output.append("%s%s" % (pre, node.name.get_id()))
            # output.append("%s%s" % (fill, "  Start Time: %s" % (node.name.start_time.strftime(str_format))))
            # output.append("%s%s" % (fill, "  End Time: %s" % (node.name.end_time.strftime(str_format))))
            runtime = node.name.end_time - node.name.start_time
            output.append("%s%s" % (fill, "  Runtime: %s" % runtime))
        return "\n".join(output).encode('utf-8')

    def add_general(self, header):
        self._curr_general = self._add_node(header, self.root)
        self._curr_suite = None
        self._curr_testcase = None
        self._curr_step = None

    def add_suite(self, header):
        self._curr_suite = self._add_node(header, self._header_tree[self._curr_general])
        self._curr_testcase = None
        self._curr_step = None

    def add_testcase(self, header):
        self._curr_testcase = self._add_node(header, self._header_tree[self._curr_suite])
        self._curr_step = None

    def add_step(self, header):
        self._curr_step = self._add_node(header, self._header_tree[self._curr_testcase])

    def start_time(self, start_time, root=False):
        """Set the start time of the current ``VHeader`` object."""
        if root:
            root_header = self.root.name
            root_header.start_time = start_time
        else:
            header = self.current_header()
            header.start_time = start_time

    def is_test_start_time_added(self):
        """Return False if the initial test start time hasn't been specified."""
        return bool(self.root.name.start_time)

    def end_time(self, end_time, root=False):
        """Set the end time of the current ``VHeader`` object."""
        if root:
            root_header = self.root.name
            root_header.end_time = end_time
        else:
            header = self.current_header()
            header.end_time = end_time

    def current_header(self):
        """Return the current ``VHeader`` object."""
        return self._header_tree[-1].name

    def previous_header(self):
        """Return the previous ``VHeader`` object."""
        return self._header_tree[-2].name

    def calc_end_time(self):
        """Calulates the end time for each header."""
        self._recursive_calc_end_time(self.root)

    def _add_node(self, header, parent):
        """Add header node to tree and return index."""
        node = Node(header, parent=parent)
        self._header_tree.append(node)
        return len(self._header_tree) - 1

    def _get_header(self, index):
        """Return the ``VHeader`` object at the specified index."""
        return self._header_tree[index].name

    def in_specified_testcase(self):
        """Determines what logs are to be displayed based on test case and step specified.

        If logs from a specific test case or step is specified
        (via the ``DISPLAY_TESTCASE_NAME``, ``DISPLAY_TESTCASE_NUM``, and ``DISPLAY_STEP_NUM``),
        the current test case and step will be matched against the expected values.
        If the names or numbers don't match, then ``None`` will be returned.

        :return: True if log is in specified test case or step, otherwise False.
        """
        display_tc_name = self._store_tc_name
        display_tc_num = self._store_tc_num
        display_step = self._store_step

        # No Test Case name or number specified
        if not display_tc_name and display_tc_num < 0:
            return True

        display_log = False
        # Test Case number specified
        if display_tc_num >= 0 and self._curr_testcase:
            if self._get_header(self._curr_testcase).number == display_tc_num:
                display_log = True

        # Test Case name specified
        if display_tc_name and self._curr_testcase:
            if self._get_header(self._curr_testcase).test_case_name == display_tc_name:
                display_log = True

        # Test Case Step specified
        if display_step >= 0 and display_log:
            if self._curr_step and self._get_header(self._curr_step).number != display_step:
                display_log = False
            elif not self._curr_step:
                display_log = False

        return display_log

    def update_current_log(self, fmt_log):
        """Update the values stored in current member variables and check if log is to display.

        :return: Original formatted log if specified to print, otherwise None.
        """
        log_type = fmt_log.type
        if log_type == VLogType.GENERAL_H:
            self.add_general(fmt_log)
        elif log_type == VLogType.SUITE_H:
            self.add_suite(fmt_log)
        elif log_type == VLogType.TEST_CASE_H:
            self.add_testcase(fmt_log)
        elif log_type == VLogType.STEP_H:
            self.add_step(fmt_log)

        output = fmt_log if self.in_specified_testcase() else None
        return output

    # Endtime Functions
    #####################################################################################################

    def _recursive_calc_end_time(self, node):
        # Node is root
        if node.is_root:
            for child in node.children[::-1]:
                self._recursive_calc_end_time(child)
            return

        # Node is last sibling
        if self._is_last_sibling(node):
            node.name.end_time = self._get_last_sibling_starttime(node)

        # Node is not last sibling
        else:
            node.name.end_time = self._get_next_sibling_starttime(node)

        # Base case
        if node.is_leaf:
            return
        else:
            for child in node.children[::-1]:
                self._recursive_calc_end_time(child)

    def _is_last_sibling(self, node):
        children = node.parent.children
        return True if node == children[-1] else False

    def _get_next_sibling_starttime(self, node):
        children = node.parent.children
        index = children.index(node)
        start_time = children[index + 1].name.start_time
        return start_time

    def _get_last_sibling_starttime(self, node):
        # Parent is root
        parent = node.parent
        if parent.is_root:
            return parent.name.end_time

        # Parent is last sibling
        if self._is_last_sibling(parent):
            return self._get_last_sibling_starttime(parent)

        # Parent is not last sibling
        else:
            return self._get_next_sibling_starttime(parent)
