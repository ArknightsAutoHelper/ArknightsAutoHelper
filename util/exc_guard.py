import logging


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

