#!/usr/bin/env python3

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    import sys
    import Arknights.launcher
    sys.exit(Arknights.launcher.main(sys.argv))
