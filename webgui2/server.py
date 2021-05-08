from util import unfuck_pythonw
import sys
import os
import logging
import bottle
import json
import gevent
import gevent.queue
import gevent.pywsgi
import gevent.threadpool
import multiprocessing
from geventwebsocket import WebSocketError
import geventwebsocket
import geventwebsocket.websocket
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket.logging import create_logger
import contextlib
try:
    import webview
    use_webview = True
except ImportError:
    use_webview = False
import config


def start(port=0):
    multiprocessing.set_start_method('spawn')
    app = bottle.Bottle()
    logger = create_logger('geventwebsocket.logging')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    logger.propagate = False
    if config.bundled:
        root = os.path.join(config.root, 'web')
    else:
        root=os.path.join(os.path.dirname(__file__), 'dist')
    httpsock = gevent.socket.socket(gevent.socket.AF_INET, gevent.socket.SOCK_STREAM)
    httpsock.bind(('127.0.0.1', port))
    httpsock.listen()

    token = '1145141919'

    @app.route("/")
    def serve_root():
        return bottle.static_file("index.html", root)

    @app.route('/itemimg/<name>.png')
    def itemimg(name):
        logger.info('serving file %s', name)
        import imgreco.resources
        import imgreco.item
        items = imgreco.item.all_known_items()
        respath = items.get(name, None)
        if respath:
            bottle.response.content_type = 'image/png'
            return imgreco.resources.open_file(respath)
        else:
            return 404
    
    def readws(ws):
        while True:
            try:
                msg = ws.receive()
            except WebSocketError:
                return None
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
            from .worker_launcher import worker_process
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
                        if obj is None:
                            error = True
                            break
                        wsread = gevent.spawn(readws, wsock)
                        pool.spawn(inq.put, obj)
            logger.info('worker loop stopped')
            with contextlib.suppress(Exception):
                gevent.kill(wsread)
                wsock.close()
                inq.put_nowait(None)
            p.kill()
            
    @app.route("/<filepath:path>")
    def serve_static(filepath):
        return bottle.static_file(filepath, root)

    group = gevent.pool.Pool()
    server = gevent.pywsgi.WSGIServer(httpsock, app, handler_class=WebSocketHandler, log=logger, spawn=group)
    url = f'http://{server.address[0]}:{server.address[1]}/?token={token}'
    print(url)
    server_task = gevent.spawn(server.serve_forever)
    if port != 0:
        server_task.get()
        return
    from .webhost import get_host
    host = get_host()
    host.start(url, 980, 820)

    if host.wait_handle:
        # neither gevent nor pywebview like non-main thread
        webview_task = gevent.get_hub().threadpool.spawn(host.wait_handle)
        webview_task.wait()
    else:
        idlechk_interval = getattr(host, 'poll_interval', 60)
        idlecount = 1
        while True:
            gevent.sleep(idlechk_interval)
            if len(group) == 0:
                idlecount += 1
            else:
                idlecount = 0
            if idlecount >= 3:
                print("stopping idle server")
                break
            # gevent.util.print_run_info()
    server.stop()

if __name__ == '__main__':
    start()
