from __future__ import annotations
import util.early_logs
import util.unfuck_https_proxy
import queue
import asyncio
import signal
import threading
import concurrent.futures
import logging

from rpc.aioobservable import Subject
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from automator.helper import BaseAutomator

import app
app.background = True

interrupt_signal = Subject()

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

class AsyncWebHandler(logging.Handler):
    terminator = '\n'

    def __init__(self, outq: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.outq = outq
        self.loop = loop

    def flush(self):
        pass

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            asyncio.run_coroutine_threadsafe(self.outq.put(dict(type="log", message=msg, level=level)), self.loop)
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)

loghandler = PendingHandler()
loghandler.setLevel(logging.INFO)
app.init([loghandler])

class WebFrontend:
    def __init__(self, output: Subject[dict], loop: asyncio.AbstractEventLoop):
        self.output = output
        self.loop = loop
        self.interrupt_event = threading.Event()
        self.skip_event = threading.Event()

    def attach(self, helper):
        pass
    def alert(self, title, text, level='info', details=None):
        """user-targeted message"""
        self.output.next(dict(type="alert", title=title, message=text, level=level, details=details))
    def notify(self, name, value=None):
        """program-targeted message"""
        # logger.info("sending notify %s %r", name, value)
        self.output.next(dict(type="notify", name=name, value=value))
    def request_device_connector(self):
        try:
            return connector.auto_connect()
        except:
            self.notify_availiable_devices()
            self.notify('web:request-device')
            raise RuntimeError('请选择设备后重试')
    def notify_availiable_devices(self):
        devices = connector.enum_devices()
        self.devices = devices
        self.notify("web:availiable-devices", [x[0] for x in devices])

    def interrupt(self):
        self.interrupt_event.set()
        self.skip_event.set()

    def delay(self, secs, allow_skip):
        self.notify("wait", dict(duration=secs, allow_skip=allow_skip))
        try:
            if not allow_skip:
                self.interrupt_event.wait(secs)
            else:
                if self.interrupt_event.is_set():
                    raise KeyboardInterrupt()
                self.skip_event.clear()
                self.skip_event.wait(secs)
            if self.interrupt_event.is_set():
                raise KeyboardInterrupt()
        finally:
            self.notify("wait", dict(duration=0, allow_skip=False))

_export_methods = {}

def export(func):
    _export_methods[func.__name__] = asyncio.iscoroutinefunction(func)
    return func

class ApiServer:
    def __init__(self, helper: BaseAutomator):
        self.main_thread_queue = queue.Queue()
        self.helper = helper
    def interrupt(self):
        signal.raise_signal(signal.SIGINT)
    async def handle_request(self, request):
        func_name = request['func']
        is_async = _export_methods[func_name]
        func = getattr(self, func_name)
        if is_async:
            return await func(**request['args'])
        else:
            return await asyncio.to_thread(func, **request['args'])


    def run_main_thread(self):
        while True:
            try:
                command = self.main_thread_queue.get(block=True, timeout=1)
            except queue.Empty:
                continue
            if command is None:
                break
            elif command == 'sched:start':
                try:
                    self.helper.scheduler.run()
                except KeyboardInterrupt:
                    pass

    # API functions
    @export
    async def app_get_version(self):
        return app.version

    @export
    async def app_get_config(self):
        schema, values = app.schemadef.to_viewmodel(app.config)
        return dict(schema=schema, values=values)

    @export
    async def app_set_config_values(self, values):
        app.schemadef.set_flat_values(app.config, values)

    @export
    async def app_check_updates(self):
        pass

    @export
    async def sched_refresh_task_list(self):
        return self.helper.scheduler.tasks

    @export
    async def sched_add_task(self, defn):
        pass

    @export
    async def sched_update_task(self, task_id, defn):
        pass

    @export
    async def sched_remove_task(self, task_id):
        pass

    @export
    async def sched_reset_task_list(self):
        pass

    @export
    async def sched_quick_run_task(self, defn):
        pass

    @export
    async def sched_start(self):
        self.main_thread_queue.put('sched:start')

    @export
    async def sched_interrupt(self):
        pass

    @export
    async def sched_get_registered_tasks(self):
        pass


def server_thread(loop_future: concurrent.futures.Future, stopper_future: concurrent.futures.Future, notify_sink: Subject):
    loop = asyncio.new_event_loop()
    print("creating loop", loop, id(loop))
    asyncio.set_event_loop(loop)
    loop_future.set_result(loop)
    from . import ws_endpoint
    ws_endpoint.start(stopper_future)


def run():
    # signal.signal(signal.SIGINT, lambda *args: interrupt_signal.next(None))
    from Arknights.helper import ArknightsHelper
    loop_future = concurrent.futures.Future()
    stop_future = concurrent.futures.Future()
    notify_sink = Subject()
    thread = threading.Thread(target=server_thread, args=(loop_future, stop_future, notify_sink))
    thread.start()
    aioloop = loop_future.result()
    stopper = stop_future.result()
    helper = ArknightsHelper(frontend=WebFrontend(output=notify_sink, loop=aioloop))
    main_thread_queue = queue.Queue()

    try:
        while True:
            try:
                print('waiting for next command')
                action = main_thread_queue.get(timeout=1)
            except queue.Empty:
                continue
            if action is None:
                break
            elif action == 'sched:start':
                try:
                    helper.scheduler.run()
                except KeyboardInterrupt:
                    pass
            
            print(action)
    finally:
        print("requesting stop")
        stopper()
        print("waiting for rpc thread")
        thread.join()

if __name__ == '__main__':
    run()
