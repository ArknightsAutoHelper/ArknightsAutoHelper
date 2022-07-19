import logging
import asyncio
import concurrent.futures
import json
import traceback
import starlette
import starlette.applications
import starlette.websockets
import starlette.responses
import uvicorn

from rpc.server import ApiServer

class FireAndForgetHelper:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.tasks = {}
        self.seq = 0
    def add_task(self, task):
        seq = self.seq
        self.seq += 1
        self.tasks[seq] = task
        task.add_done_callback(lambda task: self.tasks.pop(seq))


def start(stopper_future: concurrent.futures.Future, api_server: ApiServer):
    logging.getLogger('uvicorn').propagate = False

    app = starlette.applications.Starlette(debug=True)
    loop = asyncio.get_event_loop()

    async def handle_jsonrpc(websocket: starlette.websockets.WebSocket, jdoc):
        try:
            request = json.loads(jdoc)
            response = await api_server.handle_jsonrpc(request)
        except:
            traceback.print_exc()
            response = dict(jsonrpc='2.0', error=dict(code=-32700, message=f'Parse error'))
        if response is not None:
            await websocket.send_text(json.dumps(response, separators=(',', ':')))

    fire_and_forget = FireAndForgetHelper(loop)

    @app.websocket_route('/rpc')
    async def ws_conn(websocket: starlette.websockets.WebSocket):
        token = websocket.query_params.get('token', None)
        print(f'ws_conn: token={token}')
        if token != '1145141919':
            await websocket.close(1002)
            return
        await websocket.accept()
        notify_sink = api_server.notify_sink
        aioq = asyncio.Queue()
        async def subscriber(x):
            await aioq.put(x)
        with notify_sink.subscribe_async(subscriber, loop=asyncio.get_event_loop()):
            queue_get = asyncio.create_task(aioq.get())
            ws_receive = asyncio.create_task(websocket.receive())
            while True:
                done, pending = await asyncio.wait([queue_get, ws_receive], return_when=asyncio.FIRST_COMPLETED)
                if queue_get in done:
                    content = queue_get.result()
                    notify = dict(jsonrpc='2.0', method="notify", params=[content])
                    # TODO: send notify
                    await websocket.send_text(json.dumps(notify, separators=(',', ':')))
                    queue_get = asyncio.create_task(aioq.get())
                if ws_receive in done:
                    msg = ws_receive.result()
                    if msg['type'] == 'websocket.disconnect':
                        break
                    if jdoc := msg.get('text', None):
                        fire_and_forget.add_task(asyncio.create_task(handle_jsonrpc(websocket, jdoc)))
                    # await websocket.send_text(msg.get('text', 'Hello World!'))
                    ws_receive = asyncio.create_task(websocket.receive())
            for t in pending:
                t.cancel()
    @app.route('/')
    async def hello(request):
        return starlette.responses.PlainTextResponse(f'Running loop: {asyncio.get_event_loop()}')
    
    # uvicorn.run(app, port=3001)
    server = uvicorn.Server(uvicorn.Config(app, port=3001))
    def stop():
        server.force_exit = True
        server.should_exit = True
        # loop.call_soon_threadsafe(server.shutdown)
    stopper_future.set_result(stop)
    server.run()


if __name__ == '__main__':
    start()
