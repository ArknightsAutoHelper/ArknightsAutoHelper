import logging
import bottle
from gevent import pywsgi
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket.logging import create_logger

def server_factory():
    server_box = []
    class GeventWebSocketServer(bottle.ServerAdapter):
        def run(self, handler):
            server = pywsgi.WSGIServer((self.host, self.port), handler, handler_class=WebSocketHandler, **self.options)
            server_box.append(server)
            if not self.quiet:
                server.logger = create_logger('geventwebsocket.logging')
                server.logger.setLevel(logging.INFO)
                server.logger.addHandler(logging.StreamHandler())
                server.logger.propagate = False

            server.serve_forever()
    return GeventWebSocketServer, server_box

def start():
    app = bottle.Bottle()
    server = pywsgi.WSGIServer(('127.0.0.1', 0), app, handler_class=WebSocketHandler)
    root='/path/to/your/static/files'
    @app.route("/")
    def serve_root():
        return bottle.static_file("index.html", root)

    @app.route("/<filepath:path>")
    def serve_static(filepath):
        return bottle.static_file(filepath, root)
    
    @app.route("/ws", apply=[websocket])
    def rpc_endpoint():
        wsock = bottle.request.environ.get('wsgi.websocket')
        if not wsock:
            bottle.abort(400, 'Expected WebSocket request.')
        while True:
            try:
                msg = wsock.receive()
                if msg is not None:
                    wsock.send(msg)
                else: 
                    break
            except WebSocketError:
                break
        server_box[0].stop()
    
    bottle.run(app, port=None, server=server_class)
