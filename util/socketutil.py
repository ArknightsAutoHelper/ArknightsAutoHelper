import socket

def recvexactly(sock, n):
    buf = bytearray(n)
    mem = memoryview(buf)
    pos = 0
    while pos < n:
        rcvlen = sock.recv_into(mem[pos:])
        pos += rcvlen
        if rcvlen == 0:
            break
    if pos != n:
        raise RuntimeError("recvexactly %d bytes failed" % n)
    return bytes(buf)


def recvall(sock, reflen=65536, return_mem=False):
    buflen = reflen
    buf = bytearray(buflen)
    mem = memoryview(buf)
    pos = 0
    while True:
        if pos >= buflen:
            # do realloc
            mem.release()
            buf += bytearray(reflen)
            buflen += reflen
            mem = memoryview(buf)
        rcvlen = sock.recv_into(mem[pos:])
        pos += rcvlen
        if rcvlen == 0:
            break
    if return_mem:
        return mem[:pos]
    return buf[:pos]
