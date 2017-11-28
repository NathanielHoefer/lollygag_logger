#!/usr/bin/env python

"""
=========================================================================================================
Lollygag Logger
=========================================================================================================
by Nathaniel Hoefer
Contact: nathaniel.hoefer@netapp.com
Version: 0.5
Last Updated: 11/14/2017

This is the first iteration of a script to present a more legible output from the vl suite execution.

Currently, this is capable of reading from a log file by using the -f argument to specify a log file to
read from. This method will also generate a format config file during the initial run in the same
location as the log file. This format config file allows you - the user - to specify how you would like
the output to be formatted.

Another option is to run this script using the -vl argument, passing in the suite path just as though
you are running the "vl run suite.path.etc" command. You will still have to execute this from within the
same directory as if you were executing the command by itself. The big difference is this too generates
a format config file, that you can change at any point during your test to see future logs in the new
format. This format config file will be generated in your current working directory.

Script execution examples:
python lollygag_logger.py -f test.log
python lollygag_logger.py -vl suite.path.etc

If you experience any issues with this script (which there stands a good possibility) or you would like
suggest an improvement, you can reach me at my email listed above.


Improvements to implement:
 - Split reading from a file handle and formatting into two separate processes in a producer-consumer
 model.
 - Treat reading from file and executing vl process as both file handles to be passed into a single funct

=========================================================================================================
"""

from abc import ABCMeta, abstractmethod
from threading import Thread
import Queue


class LollygagLogger:
    """Primary class that reads log lines individually from a file handle and handles formatting those
    lines based on the LogLine class and LogFormatter used.
    """

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
        threads = [Thread(self.read), Thread(self.format)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def read(self):
        """Continuously reads logs line by line from the stream_handle and stores them as LogLine objects
        to the queue."""
        for unformatted_log_line in self.stream_handle:
            self.queue.put(unformatted_log_line)
        self.read_complete = True

    def format(self):
        """Continuously looks for LogLine objects within the queue and then formats them according to the
        log_formatter class
        """
        while not self.read_complete:
            unformatted_log_line = self.queue.get(block=True)
            self.log_formatter.format(unformatted_log_line)


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