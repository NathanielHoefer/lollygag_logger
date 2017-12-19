#!/usr/bin/env python

"""
=========================================================================================================
Test Program Stream
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/14/2017

Used solely for tests LollygagLogger by printing values a second apart.
"""

from time import sleep

if __name__ == "__main__":
    for i in range(3):
        print i
        sleep(1)
