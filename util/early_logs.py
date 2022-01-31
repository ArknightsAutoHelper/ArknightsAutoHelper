import logging

class EarlyLogsHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []
        self.enabled = True

    def fetch(self):
        result = self.records[:]
        self.records.clear()
        return result

    def emit(self, record: logging.LogRecord):
        if self.enabled:
            self.records.append(record)

_handler = EarlyLogsHandler()
logging.root.addHandler(_handler)
logging.root.setLevel(logging.NOTSET)

def fetch_and_stop():
    _handler.enabled = False
    return _handler.fetch()
