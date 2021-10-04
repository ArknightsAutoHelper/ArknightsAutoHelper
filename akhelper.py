#!/usr/bin/env python3

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    import sys
    import Arknights.shell_next
    sys.exit(Arknights.shell_next.main(sys.argv))
