from __future__ import annotations
from typing import Literal, Optional, Union, TYPE_CHECKING

from concurrent import futures
from dataclasses import dataclass
from enum import IntFlag
import io
import ipaddress
import logging
import random
import socket
import struct
import threading
import time
from contextlib import contextmanager

import numpy as np
import lz4.block

from .client import ADBDevice
from ..types import EventAction, EventFlag

from util.socketutil import recvexactly
from util import cvimage


class DisplayFlag(IntFlag):
    SCREEN_CAPTURE = 0x1
    SCREEN_CAPTURE_SECURE = 0x3
    INPUT = 0x4


_logger = logging.getLogger(__name__)

class SocketWithLock:
    def __init__(self, sock: socket.socket):
        self.socket = sock
        self.lock = threading.Lock()
    def close(self):
        self.socket.close()


@dataclass
class ScreenshotImage:
    COLORSPACE_UNKNOWN = 0
    COLORSPACE_SRGB = 1
    COLORSPACE_DISPLAY_P3 = 2

    image: cvimage.Image
    colorspace: int
    capture_latency: float


def _socket_iter_lines(sock: socket.socket):
    linebuf = io.BytesIO()
    buf = bytearray(4096)
    while True:
        chunklen = sock.recv_into(buf, 4096)
        if chunklen == 0:
            break
        chunk = buf[:chunklen]
        while (index := chunk.find(b'\n')) != -1:
            linebuf.write(chunk[:index+1])
            line = linebuf.getvalue()
            linebuf.truncate(0)
            linebuf.seek(0)
            yield line
            chunk = chunk[index + 1:]
        linebuf.write(chunk)

class ControlAgentClient:
    def __init__(self, device: ADBDevice, display_id: Optional[int] = None):
        self.device = device
        self.display_id = display_id or 0

        self.ready_future = futures.Future()
        self.stdio_closed_future = futures.Future()

        self.closed = False
        self.stdio_stream = None
        self.control_stream = None
        self.data_stream = None

        self.log_tag = f'aah-agent on {device}'

        try:
            control_socket_name = 'aah-agent-' + random.randbytes(4).hex()

            _logger.debug(f'{self.log_tag} deploying')
            import app
            agent_path = app.get_vendor_path('aah-agent') / 'app-release-unsigned.apk'
            server_buf = np.fromfile(agent_path, dtype=np.uint8)
            self.device.push("/data/local/tmp/app-release-unsigned.apk", server_buf)

            _logger.debug(f'{self.log_tag} starting')
            cmdline = 'CLASSPATH=/data/local/tmp/app-release-unsigned.apk app_process /data/local/tmp --nice-name=aah-agent xyz.cirno.aah.agent.Main ' + control_socket_name
            self.stdio_stream: socket.socket = self.device.shell_stream(cmdline)

            stdio_thread = threading.Thread(target=self._stdio_worker)
            stdio_thread.daemon = True
            stdio_thread.start()
            
            futures.wait([self.ready_future, self.stdio_closed_future], timeout=10, return_when=futures.FIRST_COMPLETED)
            if not self.ready_future.done():
                self.stdio_stream.close()
                raise ConnectionError("Failed to start scrsrv" )

            self.control_stream = SocketWithLock(self.device.service(f'localabstract:{control_socket_name}').detach())
            self._send_command(self.control_stream, b'OPEN', struct.pack('>ii', 0, 0))
            self._send_command(self.control_stream, b'DISP', struct.pack('>ii', self.display_id, DisplayFlag.INPUT))
        except Exception as e:
            self.close()
            raise

    def __del__(self):
        self.close()

    def open_screenshot(self, mode: Literal['adb', 'listen', 'connect'] = 'adb', address: Optional[tuple[str, int]] = None, connect_payload: Optional[bytes] = None, connection_future: Optional[futures.Future[socket.socket]] = None):
        if mode == 'adb':
            data_socket_name = 'aah-agent-' + random.randbytes(4).hex()
            data_socket_name_bytes = data_socket_name.encode('utf-8')
            self._send_command(self.control_stream, b'OPEN', struct.pack('>iih', 2, 2, len(data_socket_name_bytes)) + data_socket_name_bytes)
            self.data_stream = SocketWithLock(self.device.service(f'localabstract:{data_socket_name}').detach())
        elif mode == 'connect':
            addr = ipaddress.ip_address(address[0])
            port = address[1]
            if addr.version == 4:
                family = 0
            elif addr.version == 6:
                family = 1
            else:
                raise ValueError(f'Unsupported address: {addr}')
            if connect_payload is None:
                connect_payload = b''
            self._send_command(self.control_stream, b'OPEN', struct.pack('>ii', 1, family) + addr.packed + struct.pack('>H', port) + connect_payload)
            sock = connection_future.result()
            self.data_stream = SocketWithLock(sock)
        elif mode == 'listen':
            resp = self._send_command(self.control_stream, b'OPEN', struct.pack('>ii', 2, 0) + b'\x00\x00\x00\x00\x00\x00')  # bind 0.0.0.0:0
            ip = address[0]
            port = struct.unpack('>iH', resp)[1]
            sock = socket.create_connection((ip, port), timeout=10)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.data_stream = SocketWithLock(sock)
        else:
            raise NotImplementedError

        self._send_command(self.data_stream, b'DISP', struct.pack('>ii', self.display_id, DisplayFlag.SCREEN_CAPTURE))

    def _stdio_worker(self):
        try:
            for line in _socket_iter_lines(self.stdio_stream):
                strline = line.rstrip(b'\r\n').decode('utf-8', errors='replace')
                _logger.debug(f'{self.log_tag} stdio: {strline}')
                if 'bootstrap connection: listening' in strline:
                    self.ready_future.set_result(True)
        except OSError:
            _logger.debug(f'{self.log_tag} stdio closed')
        except:
            _logger.debug(f'{self.log_tag} error:', exc_info=True)
        self.stdio_closed_future.set_result(None)

    def _send_command_with_metrics(self, conn: SocketWithLock, cmd, payload=b''):
        tinit = time.perf_counter()
        sock = conn.socket
        with conn.lock:
            sock.sendall(cmd + struct.pack('>i', len(payload)) + payload)
            tsend = time.perf_counter()
            response = recvexactly(sock, 8)
            tresp = time.perf_counter()
            token = response[:4]
            payload_len = struct.unpack('>i', response[4:])[0]
            if token == b'OKAY':
                payload = recvexactly(sock, payload_len)
                tfullresp = time.perf_counter()
                return payload, tinit, tsend, tresp, tfullresp
            elif token == b'FAIL':
                raise RuntimeError(recvexactly(sock, payload_len).decode('utf-8', 'ignore'))
            else:
                raise RuntimeError(f'Unknown response: {token}')

    def _send_command(self, conn: SocketWithLock, cmd, payload=b''):
        payload, tinit, tsend, tresp, tfullresp = self._send_command_with_metrics(conn, cmd, payload)
        return payload

    def _set_display_id(self, display_id: int):
        self._send_command(self.data_stream, b'DISP', struct.pack('>ii', display_id, DisplayFlag.SCREEN_CAPTURE))

    def _sync(self):
        resp = self._send_command(self.control_stream, b'SYNC')
        assert len(resp) == 8
        nanosecs = struct.unpack('>q', resp)[0]
        return nanosecs

    def screenshot(self, compress: bool = False, srgb: bool = False):
        """
        Fetch last rendered frame from device.

        :param compress: whether to compress the image, may speed up transfer
        :param srgb:     whether to convert the image to sRGB

        :return: screenshot image, or `None` if no frame is available
        """
        if compress:
            resp, tinit, tsend, tresp, tfullresp = self._send_command_with_metrics(self.data_stream, b'SCAP', b'\x01\x00\x00\x00')
        else:
            resp, tinit, tsend, tresp, tfullresp = self._send_command_with_metrics(self.data_stream, b'SCAP', b'\x00\x00\x00\x00')
        resplen = len(resp)
        assert resplen >= 40
        width, height, px, row, color, ts, java_capture_latency, decompress_len = struct.unpack_from('>iiiiiqqi', resp, 0)
        # print('colorspace:', color)
        rawsize = resplen - 40
        if rawsize == 0:
            return None
        buf = np.frombuffer(resp[40:], dtype=np.uint8)
        if decompress_len != 0:
            decompressed = lz4.block.decompress(buf, uncompressed_size=decompress_len, return_bytearray=True)
            buf = np.frombuffer(decompressed, dtype=np.uint8)
        arr = np.lib.stride_tricks.as_strided(buf, (height, width, 4), (row, px, 1))
        arr = np.ascontiguousarray(arr)

        # offset = nanoTime - perf_counter_ns
        img = cvimage.fromarray(arr, 'RGBA')
        if srgb and color == ScreenshotImage.COLORSPACE_DISPLAY_P3:
            from imgreco.cms import p3_to_srgb_inplace
            img = p3_to_srgb_inplace(img)
            color = ScreenshotImage.COLORSPACE_SRGB
        xfer_time = time.perf_counter() - tresp
        img.timestamp = ts / 1e9
        return ScreenshotImage(img, color, java_capture_latency / 1e9 + xfer_time)

    def touch_event(self, action: EventAction, x: Union[int, float], y: Union[int, float], pointer_id: int = 0, pressure: float = 1.0, flags: EventFlag = 0):
        """
        Send a touch event to device

        :param action:     action to perform, see :class:`EventAction`
        :param x:          x coordinate of touch event
        :param y:          y coordinate of touch event
        :param pointer_id: pointer id of touch event, use different pointer id for multitouch
        :param pressure:   pressure of touch event
        :param flags:      flags of touch event, see :class:`EventFlag`
        """
        self._send_command(self.control_stream, b'TOUC', struct.pack('>iifffi', action, pointer_id, x, y, pressure, flags))

    def key_event(self, action: EventAction, keycode: int, metastate: int = 0, flags: EventFlag = 0):
        """
        Send a key event (UP or DOWN) to device.

        :param action:    EventAction.UP or EventAction.DOWN
        :param keycode:   see :mod:`keycode`
        :param metastate: state of meta keys
        :param flags:     use EventFlag.ASYNC for asynchronous injected event
        """
        self._send_command(self.control_stream, b'KEY ', struct.pack('>iiii', action, keycode, metastate, flags))

    def send_key(self, keycode: int, metastate: int = 0):
        """
        Send a key press (DOWN then UP) to device.

        :param keycode:   see :mod:`keycode`
        :param metastate: state of meta keys
        """
        self._send_command(self.control_stream, b'KPRS', struct.pack('>ii', keycode, metastate))

    def send_text(self, text: str):
        """
        Send text to device.

        :param text: text to send
        """
        self._send_command(self.control_stream, b'TEXT', text.encode('utf-8'))

    def begin_batch_event(self):
        """
        Begin a batch of event.

        All events in the batch will use the timestamp of begin request
        and not being injected until end_batch_event is called.
        """
        self._send_command(self.control_stream, b'BEGB')
    
    def end_batch_event(self):
        """
        End a batch of event.

        All events sent after begin_batch_event call will be dispatched sequentially with their original mode (async or not)
        """
        self._send_command(self.control_stream, b'ENDB')

    @contextmanager
    def batch_event(self):
        """
        Run a batch of event from a context manager.

        All events in the batch will use the timestamp of begin (__enter__) request.
        """
        try:
            self.begin_batch_event()
            yield
        finally:
            self.end_batch_event()

    def close(self):
        """
        Close all agent connections.

        Agent on device will exit if no active connection.
        """
        if not self.closed:
            _logger.debug(f'closing {self.log_tag}')
            if self.stdio_stream:
                self.stdio_stream.close()
            if self.control_stream:
                self.control_stream.close()
            if self.data_stream:
                self.data_stream.close()
            self.closed = True

def _demo():
    import sys
    import traceback
    from collections import deque
    logging.basicConfig(force=True, level=logging.NOTSET)

    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.user32.SetThreadDpiAwarenessContext(ctypes.c_ssize_t(-4))
        ctypes.windll.winmm.timeBeginPeriod(1)
    from automator.control.targets import get_auto_connect_candidates
    # device = ADBConnector('172.20.7.215:5555', 1)
    device = get_auto_connect_candidates()[0].get_device()
    import cv2
    
    client = ControlAgentClient(device)
    client.open_screenshot()

    mousedown = False
    lastpos = None
    def mouse_event_handler(event, x, y, flags, param):
        nonlocal mousedown
        nonlocal lastpos
        if event == cv2.EVENT_LBUTTONDOWN:
            client.touch_event(EventAction.DOWN, x, y, flags=EventFlag.ASYNC)
            # device.input.scrcpy.control.touch(x, y, const.ACTION_DOWN)
            lastpos = (x, y)
            mousedown = True
        elif event == cv2.EVENT_LBUTTONUP:
            if mousedown:
                client.touch_event(EventAction.UP, x, y, flags=EventFlag.ASYNC)
                # device.input.scrcpy.control.touch(x, y, const.ACTION_UP)
                mousedown = False
        elif event == cv2.EVENT_MOUSEMOVE:
            if mousedown and lastpos != (x, y):
                client.touch_event(EventAction.MOVE, x, y, flags=EventFlag.ASYNC)
                # device.input.scrcpy.control.touch(x, y, const.ACTION_MOVE)
                lastpos = (x, y)

    cv2.namedWindow('test', cv2.WINDOW_NORMAL)
    cv2.setMouseCallback('test', mouse_event_handler)
    img: ScreenshotImage = None
    imgchanged = False
    stop = False
    fps_deque = deque(maxlen=10)
    target_fps = 30
    target_frame_time = 1 / target_fps
    def thread():
        nonlocal img, imgchanged, stop
        last_frame_time = 0
        current_frame_time = 0
        overhead = 0
        try:
            while not stop:
                newimg = client.screenshot(compress=True)
                current_frame_time = time.perf_counter()
                fps_deque.append(current_frame_time)
                if newimg is not None:
                    img = newimg
                    imgchanged = True
                t0 = time.perf_counter()
                time_to_sleep = max(0, target_frame_time - (t0 - last_frame_time) - overhead)
                time.sleep(time_to_sleep)
                last_frame_time = time.perf_counter()
                # print('overhead=', overhead)
                overhead = time.perf_counter() - t0 - time_to_sleep
                
        finally:
            client.close()
    threading.Thread(target=thread).start()

    try:
        while not stop:
            if imgchanged:
                imgchanged = False
                bgrim = img.image.convert('native')
                timestamp = img.image.timestamp
                fps = -1
                if len(fps_deque) == 10:
                    fps = 9 / (fps_deque[-1] - fps_deque[0])
                cv2.setWindowTitle('test', f'screenshot {img.image}')
                cv2.putText(bgrim.array, f'{timestamp=:.3f}ms {fps=:.2f}', (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 128, 255), 2)
                cv2.imshow('test', bgrim.array)
            key = cv2.waitKey(4)
            try:
                if key == 27 or cv2.getWindowProperty('test', cv2.WND_PROP_VISIBLE) != 1:
                    break
            except:
                break
    except:
        traceback.print_exc()
    finally:
        stop = True

    cv2.destroyAllWindows()


if __name__ == '__main__':
    _demo()
