import socket
import logging
import time

import numpy as np

logger = logging.getLogger(__name__)

def recvexactly(sock, n):
    buf = np.empty(n, dtype=np.uint8)
    pos = 0
    while pos < n:
        rcvlen = sock.recv_into(buf[pos:])
        pos += rcvlen
        if rcvlen == 0:
            break
    if pos != n:
        raise EOFError("recvexactly %d bytes failed" % n)
    return buf.tobytes()


def recvall(sock, chunklen=65536, return_buffer=False):
    buffers = []
    current_buf = np.empty(chunklen, dtype=np.uint8)
    pos = 0
    while True:
        if pos >= chunklen:
            buffers.append(current_buf)
            current_buf = np.empty(chunklen, dtype=np.uint8)
            pos = 0
        rcvlen = sock.recv_into(current_buf[pos:])
        pos += rcvlen
        if rcvlen == 0:
            break
    buffers.append(current_buf[:pos])
    result = np.concatenate(buffers)
    if return_buffer:
        return result.data
    else:
        return result.tobytes()
