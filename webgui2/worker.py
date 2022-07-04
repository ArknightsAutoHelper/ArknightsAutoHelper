import util.early_logs
import util.unfuck_https_proxy

import logging
import sys
import threading
import multiprocessing
import queue as threading_Queue

import Arknights.helper
import app
from automator.control.ADBController import ADBController
from util.excutil import format_exception
from typing import Mapping

app.background = True
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
logger.propagate = False

class PendingHandler(logging.Handler):
    terminator = '\n'

    def __init__(self):
        super().__init__()
        self.records = []
        self.output = None

    def attach(self, output: logging.Handler):
        self.output = output
        for record in self.records:
            self.output.emit(record)
        self.records.clear()

    def flush(self):
        if self.output is not None:
            self.output.flush()

    def emit(self, record: logging.LogRecord):
        if self.output is None:
            self.records.append(record)
        else:
            self.output.emit(record)

loghandler = PendingHandler()
loghandler.setLevel(logging.INFO)
app.init([loghandler])

class WebHandler(logging.Handler):
    terminator = '\n'

    def __init__(self, outq):
        super().__init__()
        self.outq = outq

    def flush(self):
        pass

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            self.outq.put(dict(type="log", message=msg, level=level))
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)


class WorkerThread(threading.Thread):
    def __init__(self, inq: threading_Queue.Queue, outq : multiprocessing.Queue, skip_event : threading.Event, interrupt_event : threading.Event):
        super().__init__()
        self.input = inq
        self.output = outq
        self.device = None
        self.blocking = False
        self.skip_wait_event = skip_event
        self.interrupt_event = interrupt_event
        self.helper = None
        self.allowed_calls = {
            "web:connect": self.web_connect,
            "worker:set_refill_with_item": lambda x: self.helper.addon('CombatAddon').configure_refill(with_item=bool(x)) and None,
            "worker:set_refill_with_originium": lambda x: self.helper.addon('CombatAddon').configure_refill(with_originium=bool(x)) and None,
            "worker:set_max_refill_count": self.set_max_refill_count,
            "worker:module_battle": lambda stage, count: self.helper.addon('StageNavigator').navigate_and_combat(stage, int(count)) and None,
            "worker:module_battle_slim": lambda count: self.helper.addon('CombatAddon').combat_on_current_stage(int(count)) and None,
            "worker:clear_task": lambda: self.helper.addon('QuestAddon').clear_task() and None,
            "worker:recruit": lambda: self.helper.addon('RecruitAddon').recruit(),
        }

    def notify_availiable_devices(self):
        from automator.control.targets import enum_targets
        devices = enum_targets()
        self.devices = devices
        self.notify("web:availiable-devices", [str(x) for x in devices])

    # threading.Thread
    def run(self):
        print("starting worker thread")
        realhandler = WebHandler(self.output)
        loghandler.attach(realhandler)
        version = app.version
        if app.get_instance_id() != 0:
            version += f" (instance {app.get_instance_id()})"
        self.notify("web:version", version)
        self.notify_availiable_devices()
        self.helper = Arknights.helper.ArknightsHelper(frontend=self)
        while True:
            self.notify("worker:idle")
            command : dict = self.input.get(block=True)
            if command.get('type', None) == "call":
                self.interrupt_event.clear()
                self.notify('worker:busy')
                tag = command.get('tag', None)
                action = command.get('action', None)
                return_value = None
                exc = None
                try:
                    func = self.allowed_calls[action]
                    args = command.get('args', [])
                    return_value = func(*args)
                except:
                    exc = sys.exc_info()
                if exc is None:
                    result = dict(type='call-result', status='resolved', tag=tag, return_value=return_value)
                else:
                    result = dict(type='call-result', status='exception', tag=tag, exception=format_exception(*exc))
                if tag is not None:
                    self.output.put_nowait(result)

    # frontend, called by helper
    def attach(self, helper):
        pass
    def alert(self, title, text, level='info', details=None):
        """user-targeted message"""
        logger.info("sending alert %s %s %s %s", level, title, text, details)
        self.output.put(dict(type="alert", title=title, message=text, level=level, details=details))
    def notify(self, name, value=None):
        """program-targeted message"""
        logger.info("sending notify %s %r", name, value)
        self.output.put(dict(type="notify", name=name, value=value))
    def request_device_connector(self):
        from automator.control.targets import auto_connect
        try:
            return auto_connect(preference=app.config.device.adb_always_use_device)
        except:
            self.notify_availiable_devices()
            self.notify('web:show-devices')
            raise RuntimeError('请选择设备后重试')
    def delay(self, secs, allow_skip):
        self.notify("wait", dict(duration=secs, allow_skip=allow_skip))
        try:
            if not allow_skip:
                self.interrupt_event.wait(secs)
            else:
                if self.interrupt_event.is_set():
                    raise KeyboardInterrupt()
                self.skip_wait_event.clear()
                self.skip_wait_event.wait(secs)
            if self.interrupt_event.is_set():
                raise KeyboardInterrupt()
        finally:
            self.notify("wait", dict(duration=0, allow_skip=False))

    
    # called by user
    def web_connect(self, dev:str):
        print(dev.split(':', 1))
        connector_type, cookie = dev.split(':', 1)
        if connector_type == 'list':
            record = self.devices[int(cookie)]
            new_connector = record.create_controller()
        elif connector_type == 'adb':
            from automator.control.adb.targets import get_target_from_adb_serial
            new_connector = get_target_from_adb_serial(cookie).create_controller()
        else:
            raise KeyError("unknown connector type " + connector_type)
        connector_str = str(new_connector)
        old_controller = self.helper.connect_device(new_connector)
        if old_controller is not None:
            old_controller.close()


    def set_max_refill_count(self, count):
        self.helper.addon('CombatAddon').refill_count = 0
        self.helper.addon('CombatAddon').max_refill_count = count



def worker_process(inq : multiprocessing.Queue, outq : multiprocessing.Queue):
    print("starting worker process")
    threadq = threading_Queue.Queue()
    skip_evt = threading.Event()
    intr_evt = threading.Event()
    thr = WorkerThread(threadq, outq, skip_evt, intr_evt)
    thr.setDaemon(True)
    thr.start()
    print("starting worker process loop")

    while True:
        request = inq.get()
        if request is None:
            break
        if not isinstance(request, Mapping):
            outq.put(dict(type="alert", title="RPC Error", text="invalid request object", level="error"))
            break
        req_type = request.get("type", None)
        if req_type == "web:skip":
            skip_evt.set()
        elif req_type == "web:interrupt":
            intr_evt.set()
            skip_evt.set()
        elif req_type == "web:kill":
            import os
            os.kill(os.getpid())
        else:
            threadq.put(request)
    outq.close()
        