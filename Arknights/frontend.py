import time

class DummyFrontend:
    def attach(self, helper):
        pass
    def alert(self, title, text, level='info', details=None):
        """user-targeted message"""
    def notify(self, name, value):
        """program-targeted message"""
    def delay(self, secs, skippable):
        time.sleep(secs)
