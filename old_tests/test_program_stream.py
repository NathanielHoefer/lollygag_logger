#!/usr/bin/env python

"""
=========================================================================================================
Test Program Stream
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/14/2017

Used solely for old_tests LollygagLogger by printing values a second apart.
"""

from time import sleep
import sys


if __name__ == "__main__":

    for line in range(3):
        print line
        sys.stdout.flush()
        sleep(1)