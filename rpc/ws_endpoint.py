import asyncio
import starlette
import starlette.applications
import starlette.websockets
import starlette.responses
import uvicorn
from .context import session_var

def start(session):
    app = starlette.applications.Starlette(debug=True)
    @app.websocket_route('/rpc')
    async def ws_conn(websocket: starlette.websockets.WebSocket):
        token = websocket.query_params.get('token', None)
        print(f'ws_conn: token={token}')
        if token != '1145141919':
            await websocket.close(1002)
            return
        await websocket.accept()
        session_var.set(session)
        while True:
            msg = await websocket.receive()
            if msg['type'] == 'websocket.disconnect':
                break
            await websocket.send_text(msg.get('text', 'Hello World!'))
    @app.route('/')
    async def hello(request):
        return starlette.responses.PlainTextResponse(f'Running loop: {asyncio.get_event_loop()}')
    
    uvicorn.run(app, port=3001)


if __name__ == '__main__':
    start()
