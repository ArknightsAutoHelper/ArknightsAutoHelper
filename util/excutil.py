import logging
import traceback

class guard:
    def __init__(self, logger=None):
        self.logger = logger
    def __enter__(self):
        pass
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.logger is not None:
                self.logger.error('recovered from exception', exc_info=1)
        return True

def format_exception(etype, evalue, tb):
    message = traceback.format_exception_only(etype, evalue)
    trace = ''.join(traceback.format_tb(tb))
    return dict(message=message, trace=trace)
