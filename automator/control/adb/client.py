from __future__ import annotations
from typing import Optional

import contextlib
from functools import lru_cache
import socket
import struct
import logging
import time

import numpy as np

from util.socketutil import recvexactly, recvall

from .server import ensure_adb_alive

logger = logging.getLogger(__name__)

def _check_okay(sock):
    result = recvexactly(sock, 4)
    if result != b'OKAY':
        raise RuntimeError(_read_hexlen(sock))


def _read_hexlen(sock):
    textlen = int(recvexactly(sock, 4), 16)
    if textlen == 0:
        return b''
    buf = recvexactly(sock, textlen)
    return buf

def _read_binlen_le(sock):
    textlen = struct.unpack('<I', recvexactly(sock, 4))[0]
    if textlen == 0:
        return b''
    buf = recvexactly(sock, textlen)
    return buf

class ADBClientSession:
    def __init__(self, server=None, timeout=None):
        if server is None:
            server = ('127.0.0.1', 5037)
        if server[0] == '127.0.0.1' or server[0] == '::1':
            timeout = 0.5
        sock = socket.create_connection(server, timeout=timeout)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.settimeout(None)
        self.sock: socket.socket = sock

    def close(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def service(self, cmd: str):
        """make a service request to ADB server, consult ADB sources for available services"""
        cmdbytes = cmd.encode()
        data = b'%04X%b' % (len(cmdbytes), cmdbytes)
        self.sock.send(data)
        _check_okay(self.sock)
        return self

    def read_response(self):
        """read a chunk of length indicated by 4 hex digits"""
        return _read_hexlen(self.sock)

    def detach(self):
        sock = self.sock
        self.sock = None
        return sock


class ADBDevice:
    def __init__(self, serial: Optional[str] = None, server: Optional[ADBServer] = None):
        self.serial = serial
        self.server = server or ADBServer.DEFAULT

    def __repr__(self):
        return f'{self.__class__.__name__}({self.server!r}, serial={self.serial!r})'

    def create_session(self):
        if self.serial is not None:
            session = self._create_session_retry()
        else:
            session = self.server.create_session()
            session.service('host:transport-any')
        return session
    
    def _create_session_retry(self, retry_count=0):
        session = self.server.create_session()
        try:
            session.service('host:transport:' + self.serial)
            return session
        except RuntimeError as e:
            session.close()
            if retry_count == 0 and e.args and isinstance(e.args[0], bytes) and b'not found' in e.args[0]:
                if ':' in self.serial and self.serial.split(':')[-1].isdigit():
                    logger.info('adb connect %s', self.serial)
                    self.server.paranoid_connect(self.serial)
                    return self._create_session_retry(retry_count + 1)
            raise

    def service(self, cmd: str):
        """make a service request to adbd, consult ADB sources for available services"""
        session = self.create_session()
        session.service(cmd)
        return session

    def exec_stream(self, cmd=''):
        """run command in device, with stdout/stdin attached to the socket returned"""
        return self.service('exec:' + cmd).detach()

    def exec(self, cmd):
        """run command in device, returns stdout content after the command exits"""
        if len(cmd) == 0:
            raise ValueError('no command specified for blocking exec')
        sock = self.exec_stream(cmd)
        data = recvall(sock)
        sock.close()
        return data

    def shell_stream(self, cmd=''):
        """run command in device, with pty attached to the socket returned"""
        return self.service('shell:' + cmd).detach()

    def shell(self, cmd):
        """run command in device, returns pty output after the command exits"""
        if len(cmd) == 0:
            raise ValueError('no command specified for blocking shell')
        sock = self.shell_stream(cmd)
        data = recvall(sock)
        sock.close()
        return data

    def push(self, target_path: str, buffer: ReadableBuffer, mode=0o100755, mtime: int = None):
        """push data to device"""
        # Python has no type hint for buffer protocol, why?
        sock = self.service('sync:').detach()
        request = b'%s,%d' % (target_path.encode(), mode)
        sock.send(b'SEND' + struct.pack("<I", len(request)) + request)
        sendbuf = np.empty(65536+8, dtype=np.uint8)
        sendbuf[0:4] = np.frombuffer(b'DATA', dtype=np.uint8)
        input_arr = np.frombuffer(buffer, dtype=np.uint8)
        for arr in np.array_split(input_arr, np.arange(65536, input_arr.size, 65536)):
            sendbuf[4:8].view('<I')[0] = len(arr)
            sendbuf[8:8+len(arr)] = arr
            sock.sendall(sendbuf[0:8+len(arr)])
        if mtime is None:
            mtime = int(time.time())
        sock.sendall(b'DONE' + struct.pack("<I", mtime))
        _check_okay(sock)
        _read_binlen_le(sock)
        sock.close()

class ADBAnyDevice(ADBDevice):
    def __init__(self, server: Optional[ADBServer] = None):
        super().__init__(None, server)

class ADBAnyUSBDevice(ADBDevice):
    def __init__(self, server: Optional[ADBServer] = None):
        super().__init__('<any usb>', server)
    
    def create_session(self):
        return self.server.create_session().service('host:transport-usb')

class ADBAnyEmulatorDevice(ADBDevice):
    def __init__(self, server: Optional[ADBServer] = None):
        super().__init__('<any emulator>', server)
    
    def create_session(self):
        return self.server.create_session().service('host:transport-local')

class ADBServer:
    DEFAULT: ADBServer

    def __init__(self, address=('127.0.0.1', 5037)):
        self.address = address

    def __repr__(self):
        address = f'{self.address[0]}:{self.address[1]}'
        return f'{self.__class__.__name__}({address!r})'

    def create_session(self):
        ensure_adb_alive(self)
        return self._create_session_nocheck()

    def _create_session_nocheck(self):
        return ADBClientSession(server=self.address)

    def service(self, cmd: str, timeout: Optional[float] = None):
        """make a service request to ADB server, consult ADB sources for available services"""
        session = self.create_session()
        session.sock.settimeout(timeout)
        session.service(cmd)
        return session

    def devices(self, show_offline=False):
        """returns list of devices that the adb server knows"""
        resp = self.service('host:devices').read_response().decode()
        devices = [tuple(line.rsplit('\t', 2)) for line in resp.splitlines()]
        if not show_offline:
            devices = [x for x in devices if x[1] != 'offline']
        return devices

    def connect(self, device, timeout=None):
        resp = self.service('host:connect:%s' % device, timeout=timeout).read_response().decode(errors='ignore')
        logger.debug('adb connect %s: %s', device, resp)
        if 'unable' in resp or 'cannot' in resp:
            raise RuntimeError(resp)

    def disconnect(self, device):
        resp = self.service('host:disconnect:%s' % device).read_response().decode(errors='ignore')
        logger.debug('adb disconnect %s: %s', device, resp)
        if 'unable' in resp or 'cannot' in resp:
            raise RuntimeError(resp)

    def disconnect_all_offline(self):
        with contextlib.suppress(RuntimeError):
            for x in self.devices():
                if x[1] == 'offline':
                    with contextlib.suppress(RuntimeError):
                        self.disconnect(x[0])

    def paranoid_connect(self, port, timeout=5):
        with contextlib.suppress(RuntimeError):
            self.disconnect(port)
        self.connect(port, timeout=timeout)

    def _check_device(self, device: ADBDevice) -> ADBDevice:
        device.create_session().close()
        return device

    def get_device(self, serial: Optional[str] = None) -> ADBDevice:
        """Connect to a device"""
        return self._check_device(ADBDevice(serial, self))

    def get_usbdevice(self) -> ADBDevice:
        """switch to a USB-connected device"""
        return self._check_device(ADBAnyUSBDevice(self))

    def get_emulator(self) -> ADBDevice:
        """switch to an (SDK) emulator device"""
        return self._check_device(ADBAnyEmulatorDevice(self))

ADBServer.DEFAULT = ADBServer()

@lru_cache(maxsize=2)
def get_adb_server_by_address(server: str) -> ADBServer:
    ip, port = server.split(':', 1)
    port = int(port)
    if ip == '127.0.0.1' and port == 5037:
        return ADBServer.DEFAULT
    return ADBServer((ip, port))

def get_config_adb_server():
    import app
    server: str = app.config.device.adb_server
    return get_adb_server_by_address(server)
