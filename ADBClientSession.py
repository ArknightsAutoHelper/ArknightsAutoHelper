import socket
import struct
import gzip

def _recvexactly(sock, n):
    buf = sock.recv(n)
    assert(len(buf) != 0)
    remain = n - len(buf)
    while remain > 0:
        buf2 = sock.recv(remain)
        buf += buf2
        remain -= len(buf2)
    return buf


def _recvall(sock):
    buf = b''
    while True:
        data = sock.recv(4096)
        if not data:
            break
        buf += data
    return buf


def _check_okay(sock):
    result = _recvexactly(sock, 4)
    if result != b'OKAY':
        raise RuntimeError(_read_hexlen(sock))


def _read_hexlen(sock):
    textlen = int(_recvexactly(sock, 4), 16)
    if textlen == 0:
        return b''
    buf = _recvexactly(sock, textlen)
    return buf


class ADBClientSession:
    def __init__(self, server=None):
        if server is None:
            server = ('127.0.0.1', 5037)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server)
        self.sock = sock

    def close(self):
        self.sock.close()

    def service(self, cmd):
        """make a service request to ADB server, consult ADB sources for available services"""
        cmdbytes = cmd.encode()
        data = b'%04X%b' % (len(cmdbytes), cmdbytes)
        self.sock.send(data)
        _check_okay(self.sock)
        return self

    def read_response(self):
        """read a chunk of length indicated by 4 hex digits"""
        return _read_hexlen(self.sock)

    def devices(self):
        """returns list of devices that the adb server knows"""
        resp = self.service('host:devices').read_response().decode()
        devices = [tuple(line.split('\t')) for line in resp.splitlines()]
        return devices

    def connect(self, device):
        resp = self.service('host:connect:%s' % device).read_response()
        if b'unable' in resp:
            raise RuntimeError(resp)

    def device(self, devid=None):
        """switch to a device"""
        if devid is None:
            return self.service('host:transport-any')
        return self.service('host:transport:'+devid)

    def usbdevice(self):
        """switch to a USB-connected device"""
        return self.service('host:transport-usb')

    def emulator(self):
        """switch to an (SDK) emulator device"""
        return self.service('host:transport-local')

    def exec_stream(self, cmd=''):
        """run command in device, with stdout/stdin attached to the socket returned"""
        self.service('exec:'+cmd)
        return self.sock

    def exec(self, cmd):
        """run command in device, returns stdout content after the command exits"""
        if len(cmd) == 0:
            raise ValueError('no command specified for blocking exec')
        sock = self.exec_stream(cmd)
        data = _recvall(sock)
        sock.close()
        return data

    def shell_stream(self, cmd=''):
        """run command in device, with pty attached to the socket returned"""
        self.service('shell:'+cmd)
        return self.sock

    def shell(self, cmd):
        """run command in device, returns pty output after the command exits"""
        if len(cmd) == 0:
            raise ValueError('no command specified for blocking shell')
        sock = self.shell_stream(cmd)
        data = _recvall(sock)
        sock.close()
        return data

    def screencap_png(self):
        """returns PNG bytes"""
        data = self.exec('screencap -p')
        return data
        # w, h, f = struct.unpack_from('III', data, 0)
        # assert(f == 1)
        # return (w, h, data[12:])
    
    def screencap(self):
        """returns (width, height, pixels)
        pixels in RGBA/RGBX format"""
        data = self.exec('screencap|gzip')
        data = gzip.decompress(data)
        w, h, f = struct.unpack_from('III', data, 0)
        assert(f == 1)
        return (w, h, data[12:])
