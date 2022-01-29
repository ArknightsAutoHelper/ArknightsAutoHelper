from __future__ import annotations
import os
import socket
import struct
import threading
from time import sleep
import time
from typing import Any, Callable, Optional, Tuple, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from ..ADBConnector import ADBConnector

# import av
import numpy as np
# from adbutils import AdbDevice, AdbError, Network, _AdbStreamConnection, adb

from .const import EVENT_FRAME, EVENT_INIT, LOCK_SCREEN_ORIENTATION_UNLOCKED
from .control import ControlSender


class Client:
    def __init__(
        self,
        device: Optional[Union[ADBConnector, str]] = None,
        max_width: int = 0,
        bitrate: int = 8000000,
        max_fps: int = 0,
        flip: bool = False,
        block_frame: bool = False,
        stay_awake: bool = False,
        lock_screen_orientation: int = LOCK_SCREEN_ORIENTATION_UNLOCKED,
        displayid: Optional[int] = None,
        connection_timeout: int = 3000,
    ):
        """
        Create a scrcpy client, this client won't be started until you call the start function
        Args:
            device: Android device, select first one if none, from serial if str
            max_width: frame width that will be broadcast from android server
            bitrate: bitrate
            max_fps: maximum fps, 0 means not limited (supported after android 10)
            flip: flip the video
            block_frame: only return nonempty frames, may block cv2 render thread
            stay_awake: keep Android device awake
            lock_screen_orientation: lock screen orientation, LOCK_SCREEN_ORIENTATION_*
            connection_timeout: timeout for connection, unit is ms
        """

        if device is None:
            device = ADBConnector.auto_connect()
        elif isinstance(device, str):
            device = ADBConnector(adb_serial=device)

        self.device = device

        # User accessible
        self.last_frame: Optional[np.ndarray] = None
        self.resolution: Optional[Tuple[int, int]] = None
        self.device_name: Optional[str] = None
        self.control = ControlSender(self)

        # Params
        self.flip = flip
        self.max_width = max_width
        self.bitrate = bitrate
        self.max_fps = max_fps
        self.block_frame = block_frame
        self.stay_awake = stay_awake
        self.lock_screen_orientation = lock_screen_orientation
        self.connection_timeout = connection_timeout
        self.displayid = displayid

        # Need to destroy
        self.alive = False
        self.__server_stream: Optional[socket.socket] = None
        self.__video_socket: Optional[socket.socket] = None
        self.control_socket: Optional[socket.socket] = None
        self.control_socket_lock = threading.Lock()

        self.loop_thread = None

    def __init_server_connection(self) -> None:
        """
        Connect to android server, there will be two sockets, video and control socket.
        This method will set: video_socket, control_socket, resolution variables
        """
        for _ in range(self.connection_timeout // 100):
            try:
                self.__video_socket = self.device.device_session_factory().service('localabstract:scrcpy').sock
                break
            except:
                sleep(0.1)
                pass
        else:
            raise ConnectionError("Failed to connect scrcpy-server after 3 seconds")

        dummy_byte = self.__video_socket.recv(1)
        if not len(dummy_byte) or dummy_byte != b"\x00":
            raise ConnectionError("Did not receive Dummy Byte!")

        self.control_socket = self.device.device_session_factory().service('localabstract:scrcpy').sock
        self.device_name = self.__video_socket.recv(64).decode("utf-8").rstrip("\x00")
        if not len(self.device_name):
            raise ConnectionError("Did not receive Device Name!")

        res = self.__video_socket.recv(4)
        self.resolution = struct.unpack(">HH", res)
        # self.__video_socket.setblocking(False)

    def __deploy_server(self) -> None:
        """
        Deploy server to android device
        """
        # server_root = os.path.abspath(os.path.dirname(__file__))
        # server_file_path = server_root + "/scrcpy-server.jar"
        import config
        server_file_path = os.path.join(config.get_vendor_path('scrcpy-server-novideo'), 'scrcpy-server-novideo.jar')
        server_buf = open(server_file_path, 'rb').read()
        self.device.push("/data/local/tmp/scrcpy-server-novideo.jar", server_buf)
        cmdline = 'CLASSPATH=/data/local/tmp/scrcpy-server-novideo.jar app_process /data/local/tmp com.genymobile.scrcpy.Server 1.21 log_level=verbose control=true tunnel_forward=true'
        if self.displayid is not None:
            cmdline += f' display_id={self.displayid}'
        self.__server_stream: socket.socket = self.device.device_session_factory().shell_stream(cmdline)
        # Wait for server to start
        response = self.__server_stream.recv(50)
        if b'[server]' not in response:
            raise ConnectionError("Failed to start scrcpy-server: " + response.decode("utf-8", "ignore"))

    def start(self) -> None:
        """
        Start listening video stream
        """
        assert self.alive is False

        self.__deploy_server()
        self.__init_server_connection()
        self.loop_thread = threading.Thread(target=self.__stream_loop)
        self.loop_thread.start()

    def stop(self) -> None:
        """
        Stop listening (both threaded and blocked)
        """
        self.alive = False
        if self.__server_stream is not None:
            self.__server_stream.close()
            self.__server_stream = None
        if self.control_socket is not None:
            self.control_socket.close()
            self.control_socket = None
        if self.__video_socket is not None:
            self.__video_socket.close()
            self.__video_socket = None

    def _handle_control(self, buf):
        pass

    def __stream_loop(self) -> None:
        """
        Core loop for video parsing
        """
        import selectors
        select = selectors.DefaultSelector()
        select.register(self.__server_stream, selectors.EVENT_READ, data='log')
        select.register(self.__video_socket, selectors.EVENT_READ, data='video')
        select.register(self.control_socket, selectors.EVENT_READ, data='control')
        buffer = np.empty(262144, dtype=np.uint8)
        while self.alive:
            events = select.select(timeout=1)
            for key, mask in events:
                tag = key.data
                if tag == 'control':
                    rcvlen = self.control_socket.recv_into(buffer, 262144)
                    if rcvlen == 0:
                        break
                    self._handle_control(buffer[:rcvlen])
                elif tag == 'video':
                    rcvlen = self.__video_socket.recv_into(buffer, 262144)
                    if rcvlen == 0:
                        break
                elif tag == 'log':
                    rcvlen = self.__server_stream.recv_into(buffer, 262144)
                    if rcvlen == 0:
                        break
        if self.alive:
            self.stop()
