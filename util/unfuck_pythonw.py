import sys
import os
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'r+')
    sys.stderr = sys.stdout
    sys.stdin = sys.stdout
