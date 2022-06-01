import socket
import selectors
import threading
import secrets
import queue
from concurrent.futures import Future
from typing import Any
from weakref import WeakValueDictionary


class ReverseConnectionFuture(Future[socket.socket]):
    cookie: Any

class ReverseConnectionHost(threading.Thread):
    def __init__(self, port=0):
        super().__init__()
        self.daemon = True
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_sock.bind(('127.0.0.1', port))
        self.port = self.listen_sock.getsockname()[1]
        self.registered = WeakValueDictionary[str, ReverseConnectionFuture]()
        self.registered_lock = threading.RLock()
    
    def __del__(self):
        self.stop()

    def register_cookie(self, cookie=None) -> ReverseConnectionFuture:
        future = None
        with self.registered_lock:
            if cookie is None:
                while True:
                    cookie = b'%08X' % secrets.randbits(32)
                    if cookie not in self.registered:
                        break
            else:
                assert len(cookie) == 8
            if cookie not in self.registered:
                future = ReverseConnectionFuture()
                future.cookie = cookie
                self.registered[cookie] = future
        return future


    def _fulfilled(self, cookie, sock):
        with self.registered_lock:
            future = self.registered.pop(cookie, None)
        if future is not None:
            future.set_result(sock)


    def run(self):
        self.listen_sock.listen()
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.listen_sock, selectors.EVENT_READ, (self._accept_conn, None))

        while True:
            # print('selecting ', list(self.sel.get_map().keys()))
            if len(self.sel.get_map()) == 0:
                break
            events = self.sel.select(1)
            for key, event in events:
                callback, cookie = key.data
                callback(key.fileobj, event, cookie)

    def stop(self):
        self.sel.unregister(self.listen_sock)
        self.listen_sock.close()
        for _, future in self.registered.items():
            future.cancel()

    def _accept_conn(self, sock, event, _):
        conn, peer = sock.accept()
        self.sel.register(conn, selectors.EVENT_READ, (self._conn_data, [b'']))
    
    def _conn_data(self, sock, event, box):
        data = sock.recv(8 - len(box[0]))
        if data:
            box[0] += data
            if len(box[0]) == 8:
                self.sel.unregister(sock)
                cookie = box[0]
                if cookie in self.registered:
                    self._fulfilled(cookie, sock)
                else:
                    sock.close()
        else:
            self.sel.unregister(sock)
            sock.close()
        
def main():
    worker = ReverseConnectionHost(11451)
    worker.start()
    try:
        while True:
            worker.register_cookie(b'0000000\n')
            sock = worker.wait_registered_socket(b'0000000\n')
            while True:
                buf = sock.recv(4096)
                if not buf:
                    break
                sock.send(buf)
            sock.close()
    finally:
        worker.stop()
    
if __name__ == "__main__":
    main()