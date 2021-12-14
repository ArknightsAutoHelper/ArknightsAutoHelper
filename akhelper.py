#!/usr/bin/env python3

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    import sys
    import Arknights.configure_launcher
    import automator.launcher
    sys.exit(automator.launcher.main(sys.argv))
