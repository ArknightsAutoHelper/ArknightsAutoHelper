import time

class DummyFrontend:
    def attach(self, helper):
        pass
    def notify(self, name, value):
        pass
    def delay(self, secs, skippable):
        time.sleep(secs)
