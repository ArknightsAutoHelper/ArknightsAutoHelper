
from dataclasses import dataclass
import socket
import sys
import struct
import threading
import time
from collections import deque

import numpy as np
import lz4.block


from automator.connector.ADBConnector import ADBConnector
from util.socketutil import recvexactly

def main():
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.user32.SetThreadDpiAwarenessContext(ctypes.c_ssize_t(-4))
    from automator.connector import auto_connect
    from automator.connector.ADBConnector import ADBConnector
    # device = ADBConnector('172.20.7.215:5555', 1)
    device = auto_connect()
    import cv2
    

    cv2.namedWindow('test')
    img: ScreenshotImage = None
    imgchanged = False
    stop = False
    fps_deque = deque(maxlen=10)
    def thread():
        client = ScreenshotClient(device, 1)
        def thr2():
            while True:
                message = client.stdio_stream.recv(1024)
                if len(message) == 0:
                    break
                print(message.decode('utf-8', errors='ignore'))
        threading.Thread(target=thr2).start()
        nonlocal img, imgchanged, stop
        try:
            while not stop:
                newimg = client.screenshot()
                fps_deque.append(time.perf_counter())
                if newimg is not None:
                    img = newimg
                    imgchanged = True
        finally:
            client.close()
    threading.Thread(target=thread).start()

    try:
        while not stop:
            if imgchanged:
                imgchanged = False
                bgrim = cv2.cvtColor(img.array, cv2.COLOR_RGBA2BGR)
                latency = (time.perf_counter() - img.perf_counter_timestamp) * 1000
                fps = -1
                width = img.array.shape[1]
                height = img.array.shape[0]
                if len(fps_deque) == 10:
                    fps = 10 / (fps_deque[-1] - fps_deque[0])
                cv2.setWindowTitle('test', f'screenshot {width}x{height}')
                cv2.putText(bgrim, f'{latency=:.2f}ms {fps=:.2f}', (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 128, 255), 2)
                cv2.imshow('test', bgrim)
            key = cv2.waitKey(4)
            try:
                if key == 27 or cv2.getWindowProperty('test', cv2.WND_PROP_VISIBLE) != 1:
                    break
            except:
                break
    except:
        import traceback
        traceback.print_exc()
    finally:
        stop = True

    cv2.destroyAllWindows()

@dataclass
class ScreenshotImage:
    COLORSPACE_UNKNOWN = 0
    COLORSPACE_SRGB = 1
    COLORSPACE_DISPLAY_P3 = 2

    array: np.ndarray
    colorspace: int
    perf_counter_timestamp: float


class ScreenshotClient:
    def __init__(self, device: ADBConnector, compress_level=0):
        self.compress_request = struct.pack('>i', compress_level)
        self.device = device
        server_buf = open('app-release-unsigned.apk', 'rb').read()
        self.device.push("/data/local/tmp/app-release-unsigned.apk", server_buf)
        cmdline = 'CLASSPATH=/data/local/tmp/app-release-unsigned.apk app_process /data/local/tmp xyz.cirno.scrsrv.Main'
        self.stdio_stream: socket.socket = self.device.device_session_factory().shell_stream(cmdline)
        response = self.stdio_stream.recv(50)
        if b'listening on AF_UNIX' not in response:
            raise ConnectionError("Failed to start scrsrv: " + response.decode("utf-8", "ignore"))
        self.data_stream = device.device_session_factory().service('localabstract:scrsrv').sock
        self.syncoffset = self.sync() - time.perf_counter_ns()
        self.send_command(b'DISP', struct.pack('>ii', device.displayid or 0, 0))

    def send_command(self, cmd, payload=b''):
        self.data_stream.sendall(cmd + struct.pack('>i', len(payload)) + payload)
        response = recvexactly(self.data_stream, 8)
        assert response[:4] == b'OKAY'
        return struct.unpack('>i', response[4:])[0]

    def sync(self):
        resplen = self.send_command(b'SYNC')
        assert resplen == 8
        nanosecs = struct.unpack('>q', recvexactly(self.data_stream, 8))[0]
        return nanosecs

    def screenshot(self):
        resplen = self.send_command(b'SCAP', self.compress_request)
        assert resplen >= 32
        header = recvexactly(self.data_stream, 32)
        width, height, px, row, color, ts, decompress_len = struct.unpack('>iiiiiqi', header)
        rawsize = resplen - 32
        if rawsize == 0:
            return None
        buf = recvexactly(self.data_stream, rawsize, return_buffer=True)
        if decompress_len != 0:
            decompressed = lz4.block.decompress(buf, uncompressed_size=decompress_len, return_bytearray=True)
            buf = np.frombuffer(decompressed, dtype=np.uint8)
        arr = np.lib.stride_tricks.as_strided(buf, (height, width, 4), (row, px, 1))
        arr = np.ascontiguousarray(arr)

        # offset = nanoTime - perf_counter_ns
        local_render_time = (ts - self.syncoffset) / 1e9
        return ScreenshotImage(arr, color, local_render_time)

    def close(self):
        self.stdio_stream.close()
        self.data_stream.close()
if __name__ == '__main__':
    main()
