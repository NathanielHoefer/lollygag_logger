"""
=========================================================================================================
Lollygag Logger
=========================================================================================================
by Nathaniel Hoefer
Contact: nathaniel.hoefer@netapp.com
Version: 0.5
Last Updated: 11/14/2017

TODO - Update this description

=========================================================================================================
"""

# TODO - Update file description

from abc import ABCMeta, abstractmethod
from threading import Thread
import Queue


class LollygagLogger:
    """Primary class that reads log lines individually from a file handle and handles formatting those
    lines based on the LogLine class and LogFormatter used.
    """

    COMPLETED_SIGNAL = "Log Read Complete. Stop Formatting"

    def __init__(self, stream_handle, log_formatter):
        """Stores the components necessary for the run function

        :ivar stream_handle: an iterable that iterates line by line
        :ivar LogFormatter log_formatter: an instance extended from LogFormatter that formats the
            passed LogLine.
        :ivar Queue queue: The queue that allows for communication between the read and format threads
        :ivar bool read_complete: Identifies whether the read thread is completed reading.
        """

        self.stream_handle = stream_handle
        self.log_formatter = log_formatter
        self.queue = Queue.Queue()
        self.read_complete = False

    def run(self):
        """Executes the read and format threads concurrently."""
        threads = [Thread(target=self.read), Thread(target=self.format)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def read(self):
        """Continuously reads logs line by line from the stream_handle and stores them as LogLine objects
        to the queue."""
        for unformatted_log_line in self.stream_handle:
            self.queue.put(unformatted_log_line, block=True)
        else:
            # Send signal through the queue indicating stream completion
            self.queue.put(self.COMPLETED_SIGNAL)

    def format(self):
        """Continuously looks for LogLine objects within the queue and then formats them according to the
        log_formatter class
        """
        while True:
            unformatted_log_line = self.queue.get(block=True)

            # Check to see if stream is complete
            if unformatted_log_line == self.COMPLETED_SIGNAL:
                break
            self.log_formatter.format(unformatted_log_line)
            self.queue.task_done()


class LogFormatter:
    """Abstract base class\used in the LollygagLogger to format incoming LogLine objects."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def format(self, log_line):
        """Subclasses must handle a LogLine object."""
        pass


class LogLine:
    """Abstract base class used in the LollygagLogger to tokenize a single log."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, original_line):
        self.original_line = original_line
