import time
import sys

if __name__ == '__main__':
    for i in range(1000):
        print("Output: {}".format(i), flush=True)
        time.sleep(0.01)
