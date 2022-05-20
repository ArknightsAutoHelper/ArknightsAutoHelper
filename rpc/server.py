from __future__ import annotations
import sys
import traceback
import util.early_logs
import util.unfuck_https_proxy
import queue
import asyncio
import signal
import threading
import concurrent.futures
import logging
from util.excutil import format_exception
from collections.abc import Sequence
from rpc.aioobservable import Subject
from typing import TYPE_CHECKING, ClassVar, Mapping, Optional, Union
if TYPE_CHECKING:
    from automator.helper import BaseAutomator
    JSONObject = Mapping[str, 'JSONSerializable']
    JSONArray = Sequence['JSONSerializable']
    JSONSerializable = Union[str, int, float, bool, None, JSONArray, JSONObject]

logger = logging.getLogger(__name__)

class JSONRPCError(RuntimeError):
    code: int
    message: str
class InvalidRequestError(JSONRPCError):
    code = -32600
    message = 'Invalid Request'
class ParseError(JSONRPCError):
    code = -32700
    message = 'Parse Error'
class MethodNotFoundError(JSONRPCError):
    code = -32601
    message = 'Method not found'
class InvalidParamsError(JSONRPCError):
    code = -32602
    message = 'Invalid params'
class InternalError(JSONRPCError):
    code = -32603
    message = 'Internal error'



import app
app.background = True

interrupt_signal = Subject()
notify_sink = Subject()

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
        logger.info("sending notify %s %r", name, value)
        self.output.next((dict(type="notify", name=name, value=value)))
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

_known_methods = {}

def export(func):
    _known_methods[func.__name__] = asyncio.iscoroutinefunction(func)
    return func

class ApiServer:
    def __init__(self, helper: BaseAutomator, notify_sink: Subject):
        self.main_thread_queue = queue.Queue()
        self.helper = helper
        self.notify_sink = notify_sink
    def interrupt(self):
        signal.raise_signal(signal.SIGINT)
    async def handle_request(self, request):
        func_name = request['func']
        is_async = _known_methods[func_name]
        func = getattr(self, func_name)
        if is_async:
            return await func(**request['args'])
        else:
            return await asyncio.to_thread(func, **request['args'])


    async def _handle_single_request(self, request: JSONObject) -> Optional[JSONObject]:
        print("_handle_single_request", request)

        request_id = None
        try:
            if not isinstance(request, Mapping):
                raise InvalidRequestError
            if request.get('jsonrpc') != '2.0':
                raise InvalidRequestError
            request_id = request.get('id', None)
            method = request.get('method', None)
            if not isinstance(method, str):
                raise InvalidRequestError
            if method not in _known_methods:
                raise MethodNotFoundError
            json_params = request.get('params', [])
            if isinstance(json_params, Sequence):
                args = json_params
                kwargs = {}
            elif isinstance(json_params, Mapping):
                args = []
                kwargs = json_params
            is_async = _known_methods[method]
            func = getattr(self, method)
            if is_async:
                result = await func(*args, **kwargs)
            else:
                result = await asyncio.to_thread(func, *args, **kwargs)
            if request_id is None:
                return None
            return dict(jsonrpc='2.0', id=request_id, result=result)
        except JSONRPCError as e:
            response = dict(jsonrpc='2.0', id=request.get('id', None), error=dict(code=e.code, message=e.message))
        except Exception as e:
            traceback.print_exc()
            code = -32000
            rpc_message = "RPC server error"
            if isinstance(e, TypeError):
                message = str(e)
                if 'positional argument but' in message or 'got an unexpected keyword argument' in message:
                    code = InvalidParamsError.code
                    rpc_message = InvalidParamsError.message
            exc = sys.exc_info()
            response = dict(jsonrpc='2.0', id=request.get('id', None), error=dict(code=code, message=rpc_message, data=format_exception(*exc)))
        if request_id is not None:
            return response
        else:
            return None

    async def handle_jsonrpc(self, request: Union[JSONObject, JSONArray]):
        if isinstance(request, Sequence):
            if len(request) == 0:
                return dict(jsonrpc='2.0', id=None, error=dict(code=-32600, message='Invalid Request'))
            return [x for x in await asyncio.gather(*(self._handle_one_request(req) for req in request)) if x is not None]
        elif isinstance(request, Mapping):
            return await self._handle_one_request(request)

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
        if self.helper.scheduler.running:
            return
        self.main_thread_queue.put('sched:start')

    @export
    async def sched_interrupt(self):
        pass

    @export
    async def sched_get_registered_tasks(self):
        pass


    @export
    def test_notify(self, value=None):
        self.helper.frontend.notify('test', dict(value=value))


def server_thread(loop_future: concurrent.futures.Future, stopper_future: concurrent.futures.Future, api_server_future: concurrent.futures.Future):
    loop = asyncio.new_event_loop()
    print("creating loop", loop, id(loop))
    asyncio.set_event_loop(loop)
    loop_future.set_result(loop)
    api_server = api_server_future.result()
    from . import ws_endpoint
    ws_endpoint.start(stopper_future, api_server)


def run():
    # signal.signal(signal.SIGINT, lambda *args: interrupt_signal.next(None))
    from Arknights.helper import ArknightsHelper
    loop_future = concurrent.futures.Future()
    stop_future = concurrent.futures.Future()
    notify_sink = Subject()
    api_server_future = concurrent.futures.Future()
    thread = threading.Thread(target=server_thread, args=(loop_future, stop_future, api_server_future))
    thread.start()
    aioloop = loop_future.result()
    helper = ArknightsHelper(frontend=WebFrontend(output=notify_sink, loop=aioloop))
    api_server = ApiServer(helper, notify_sink)
    api_server_future.set_result(api_server)
    stopper = stop_future.result()

    try:
        while True:
            try:
                # print('waiting for next command')
                action = api_server.main_thread_queue.get(timeout=1)
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
