import Queue
import abc
from threading import Thread

import six

COMPLETED_SIGNAL = "Log Read Complete. Stop Formatting"
KILL_SIGNAL = "Stop command issued. Reading and Formatting Logs Interrupted " \
              "and Stopped."


class LollygagLogger:
    """Primary class that reads log lines individually from a stream handle
    and handles formatting those lines based on the LogLine class and
    LogFormatter used.
    """

    def __init__(self, stream_handle, log_formatter):
        """Stores the components necessary for the run function.

        :ivar stream_handle: an iterable that iterates line by line
        :ivar LogFormatter log_formatter: an instance extended from
            LogFormatter that formats the passed LogLine.
        :ivar Queue queue: The queue that allows for communication between the
            read and format threads
        :ivar bool read_complete: Identifies whether the read thread is
            completed reading.
        :ivar bool kill_logging: Identifies whether a kill signal needs to be
            sent.
        """

        self.stream_handle = stream_handle
        self.log_formatter = log_formatter
        self.queue = Queue.Queue()
        self.read_complete = False
        self.kill_logging = False

    def run(self):
        """Executes the read and format threads concurrently."""
        threads = [Thread(target=self.read), Thread(target=self.format)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.log_formatter.complete()

    def read(self):
        """Continuously reads logs line by line from the stream_handle and
        stores them as LogLine objects to the queue."""
        for unformatted_log_line in self.stream_handle:
            self.queue.put(unformatted_log_line, block=True)
            if self.kill_logging:
                exit(0)
        else:
            # Send signal through the queue indicating stream completion
            self.queue.put(COMPLETED_SIGNAL)

    def format(self):
        """Continuously looks for LogLine objects within the queue and then
        formats them according to the log_formatter class
        """
        while True:
            # Check to see if stream is complete
            unformatted_log_line = self.queue.get(block=True)
            if unformatted_log_line == COMPLETED_SIGNAL or self.kill_logging:
                exit(0)

            formatted_log_line_buffer = self.log_formatter.format(
                unformatted_log_line)
            signal = self.log_formatter.send(formatted_log_line_buffer)
            if signal == KILL_SIGNAL:
                self.kill()

            self.queue.task_done()

    def kill(self):
        """Send signal to stop reading and formatting."""
        self.kill_logging = True


@six.add_metaclass(abc.ABCMeta)
class LogFormatter:
    """Abstract base class\used in the LollygagLogger to format incoming
    LogLine objects.
    """

    @abc.abstractmethod
    def format(self, log_line):
        """Subclasses must handle an unformatted log line string and return a
        LogLine object.
        """
        pass

    @abc.abstractmethod
    def send(self, log_line):
        """Subclasses must handle a formatted log line object."""
        pass

    @abc.abstractmethod
    def complete(self):
        """Subclasses must include a completion step for any finalization steps."""
        pass


@six.add_metaclass(abc.ABCMeta)
class LogLine:
    """Abstract base class used in the LollygagLogger to tokenize a single
    log.
    """
