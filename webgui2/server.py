import sys
import logging
import traceback
import bottle
import json
import gevent
import gevent.queue
import gevent.threadpool
import multiprocessing
from geventwebsocket import WebSocketError
import geventwebsocket
import geventwebsocket.websocket
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket.logging import create_logger
from util import socketutil
import numpy as np
import pickle
# import pywebview


def worker_process(inq, outq):
    from . import worker
    worker.worker_process(inq, outq)
    pass


def start():
    import os
    app = bottle.Bottle()
    logger = create_logger('geventwebsocket.logging')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    logger.propagate = False
    root=os.path.join(os.path.dirname(__file__), 'dist')
    httpsock = gevent.socket.socket(gevent.socket.AF_INET, gevent.socket.SOCK_STREAM)
    httpsock.bind(('127.0.0.1', 8081))
    httpsock.listen()


    workersock = gevent.socket.socket(gevent.socket.AF_INET, gevent.socket.SOCK_STREAM)
    workersock.bind(('127.0.0.1', 0))
    workersock.listen()


    server = gevent.pywsgi.WSGIServer(httpsock, app, handler_class=WebSocketHandler, log=logger)
    token = '1145141919'
    use_webview = False

    @app.route("/")
    def serve_root():
        return bottle.static_file("index.html", root)

    @app.route("/<filepath:path>")
    def serve_static(filepath):
        return bottle.static_file(filepath, root)
    
    def readws(ws):
        while True:
            msg = ws.receive()
            if msg is not None:
                if not isinstance(msg, str):
                    continue
                try:
                    obj = json.loads(msg)
                except:
                    logger.error("invalid JSON")
                    continue
                logger.debug("received request %r", obj)
                return obj
            else:
                return None

    @app.route("/ws")
    def rpc_endpoint():
        wsock : geventwebsocket.websocket.WebSocket = bottle.request.environ.get('wsgi.websocket')
        if not wsock:
            bottle.abort(400, 'Expected WebSocket request.')
        authorized = False
        if use_webview:
            authorized = False
        else:
            wsock.send('{"type":"need-authorize"}')
        while True:
            try:
                obj = readws(wsock)
                if obj is None:
                    break
                request_type = obj.get('type', None)
                if request_type == 'web:authorize':
                    client_token = obj.get('token', None)
                    if client_token == token:
                        authorized = True
                        break
            except WebSocketError:
                break
        if authorized:
            logger.info('client authorized')
            inq = multiprocessing.Queue()
            outq = multiprocessing.Queue()
            p = multiprocessing.Process(target=worker_process, args=(inq, outq), daemon=True)
            logger.info('spawning worker process')
            p.start()
            pool : gevent.threadpool.ThreadPool = gevent.get_hub().threadpool
            error = False
            logger.info('starting worker loop')
            outqread = pool.spawn(outq.get)
            wsread = gevent.spawn(readws, wsock)
            while not error:
                for task in gevent.wait((outqread, wsread), count=1):
                    if task is outqread:
                        try:
                            outval = outqread.get()
                        except:
                            logger.error('read worker output failed with exception', exc_info=True)
                            error = True
                            break
                        gevent.spawn(wsock.send, json.dumps(outval))
                        outqread = pool.spawn(outq.get)
                    elif task is wsread:
                        try:
                            obj = wsread.get()
                        except:
                            logger.error('read message from websocket failed with exception', exc_info=True)
                            error = True
                            break
                        wsread = gevent.spawn(readws, wsock)
                        pool.spawn(inq.put, obj)
            logger.info('worker loop stopped')
            wsock.close()
            inq.put_nowait(None)
            p.kill()
                

        # server.stop()
    print(server.address)
    server.serve_forever()

    # bottle.run(app, port=None, server=server_class)

if __name__ == '__main__':
    start()
