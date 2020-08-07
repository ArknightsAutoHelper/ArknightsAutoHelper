import os
import logging.config
from random import randint
import zlib
import struct
import socket
import time

from PIL import Image

import config
# from config import ADB_ROOT, ADB_HOST, SCREEN_SHOOT_SAVE_PATH, ShellColor, CONFIG_PATH,enable_adb_host_auto_detect, ADB_SERVER
from .ADBClientSession import ADBClientSession
from util.socketutil import recvall
from . import revconn

# from numpy import average, dot, linalg

logger = logging.getLogger(__name__)


def _screencap_to_image(cap):
    w, h, pixels = cap
    return Image.frombytes('RGBA', (w, h), pixels)


def _ensure_pil_image(imgorfile):
    if isinstance(imgorfile, Image.Image):
        return imgorfile
    return Image.open(imgorfile)


def check_adb_alive():
    try:
        sess = ADBClientSession(config.ADB_SERVER)
        version = int(sess.service('host:version').read_response().decode(), 16)
        logger.debug('ADB server version %d', version)
        return True
    except ConnectionRefusedError:
        return False
    except RuntimeError:
        return False


def ensure_adb_alive():
    if check_adb_alive():
        return
    logger.info('尝试启动 adb server')
    import subprocess
    adbbin = config.get('device/adb_binary', None)
    if adbbin is None:
        adb_binaries = ['adb', os.path.join(config.ADB_ROOT, 'adb')]
    else:
        adb_binaries = [adbbin]
    for adbbin in adb_binaries:
        try:
            logger.debug('trying %r', adbbin)
            subprocess.run([adbbin, 'start-server'], check=True)
            return True
        except FileNotFoundError:
            pass
        except subprocess.CalledProcessError:
            pass
    raise OSError("can't start adb server")


class ADBConnector:
    def __init__(self, adb_serial=None):
        # os.chdir(ADB_ROOT)
        self.ADB_ROOT = config.ADB_ROOT
        self.adb_serial = adb_serial
        self.host_session_factory = lambda: ADBClientSession(config.ADB_SERVER)
        self.rch = None
        if self.adb_serial is None:
            self.adb_serial = self.__adb_device_name_detector()
        self.device_session_factory = lambda: self.host_session_factory().device(self.adb_serial)
        self.cache_screenshot = config.get('device/cache_screenshot', True)
        self.last_screenshot_timestamp = 0
        self.last_screenshot_duration = 0
        self.last_screenshot = None

        if config.get('device/try_emulator_enhanced_mode', True):
            loopbacks = self._detect_loopbacks()
            if len(loopbacks):
                logger.debug('possible loopback addresses: %s', repr(loopbacks))
                self.rch = revconn.ReverseConnectionHost()
                self.rch.start()
                if self._test_reverse_connection(loopbacks):
                    logger.info('正在使用模拟器优化模式')
                    self.screencap = self._reverse_connection_screencap
                else:
                    self.rch.stop()
        else:
            self.loopback = None

    def __del__(self):
        if self.rch and self.rch.is_alive():
            self.rch.stop()

    def __adb_device_name_detector(self):
        devices = [x for x in self.host_session_factory().devices() if x[1] != 'offline']

        if len(devices) == 0:
            auto_connect = config.get('device/adb_auto_connect', None)
            if auto_connect is not None:
                logger.info('没有已连接设备，尝试连接 %s', auto_connect)
                try:
                    self.host_session_factory().disconnect(auto_connect)
                except:
                    pass
                self.host_session_factory().connect(auto_connect)
            else:
                raise RuntimeError('找不到可用设备')

        devices = [x for x in self.host_session_factory().devices() if x[1] != 'offline']

        always_use_device = config.get('device/adb_always_use_device', None)
        if always_use_device is not None:
            if always_use_device not in (x[0] for x in devices):
                raise RuntimeError('设备 %s 未连接' % always_use_device)
            return always_use_device

        if len(devices) == 1:
            device_name = devices[0][0]
        elif len(devices) > 1:
            logger.info("检测到多台设备")
            num = 0
            while True:
                try:
                    num = int(input("请输入序号选择设备: "))
                    if not 0 <= num < len(devices):
                        raise ValueError()
                    break
                except ValueError:
                    logger.error("输入不合法，请重新输入")
            device_name = devices[num][0]
        else:
            raise RuntimeError('找不到可用设备')
        logger.info("确认设备名称：" + device_name)
        return device_name

    def run_device_cmd(self, cmd, DEBUG_LEVEL=2):
        output = self.device_session_factory().exec(cmd)
        logger.debug("command: %s", cmd)
        logger.debug("output: %s", repr(output))
        return output

    def get_sub_screen(self, image, screen_range):
        return image.crop(
            (
                screen_range[0][0],
                screen_range[0][1],
                screen_range[0][0] + screen_range[1][0],
                screen_range[0][1] + screen_range[1][1]
            )
        )


    def _detect_loopbacks(self):
        board = self.device_session_factory().exec('getprop ro.product.board')
        if b'goldfish' in board:
            return ['10.0.2.2']
        modules = self.device_session_factory().exec('grep -o vboxguest /proc/modules')
        if b'vboxguest' in modules:
            arp = self.device_session_factory().exec('cat /proc/net/arp')
            return [x[:x.find(b' ')].decode() for x in arp.splitlines()[1:]]
        return []

    def _test_reverse_connection(self, loopbacks):
        for addr in loopbacks:
            logger.debug('testing loopback address %s', addr)
            future = self.rch.register_cookie()
            with future:
                cmd = 'echo -n %sOKAY | nc -w 1 %s %d' % (future.cookie.decode(), addr, self.rch.port)
                logger.debug(cmd)
                control_sock = self.device_session_factory().exec_stream(cmd)
                with control_sock:
                    conn = future.get(2)
                    if conn is not None:
                        data = recvall(conn)
                        conn.close()
                        if data == b'OKAY':
                            self.loopback = addr
                            logger.debug('found loopback address %s', addr)
                            return True
        return False

    def screencap_png(self):
        """returns PNG bytes"""
        s = self.device_session_factory().exec_stream('screencap -p')
        data = recvall(s, 4194304)
        return data

    def screencap(self):
        """returns (width, height, pixels)
        pixels in RGBA/RGBX format"""
        s = self.device_session_factory().exec_stream('screencap|gzip -1')
        data = recvall(s, 4194304)
        s.close()
        data = zlib.decompress(data, zlib.MAX_WBITS | 16, 8388608)
        w, h, f = struct.unpack_from('III', data, 0)
        assert (f == 1)
        return (w, h, data[12:])

    def _reverse_connection_screencap(self):
        """returns (width, height, pixels)
        pixels in RGBA/RGBX format"""
        future = self.rch.register_cookie()
        with future:
            control_sock = self.device_session_factory().exec_stream('(echo -n %s; screencap) | nc %s %d' % (future.cookie.decode(), self.loopback, self.rch.port))
            with control_sock:
                with future.get() as conn:
                    data = recvall(conn, 8388608, True)
        w, h, f = struct.unpack_from('III', data, 0)
        assert (f == 1)
        return (w, h, data[12:].tobytes())

    def screenshot(self, cached=True):
        t0 = time.monotonic()
        if cached and self.cache_screenshot:
            if self.last_screenshot is not None and t0 - self.last_screenshot_timestamp < self.last_screenshot_duration:
                return self.last_screenshot
        rawcap = self.screencap()
        img = _screencap_to_image(rawcap)
        t1 = time.monotonic()
        self.last_screenshot_timestamp = t1
        self.last_screenshot_duration = t1 - t0
        self.last_screenshot = img
        return img

    def touch_swipe2(self, origin, movement, duration=None):
        # sleep(1)
        x1, y1, x2, y2 = origin[0], origin[1], origin[0] + movement[0], origin[1] + movement[1]

        logger.debug("滑动初始坐标:({},{}); 移动距离dX:{}, dy:{}".format(*origin, *movement))
        command = "input swipe {} {} {} {} ".format(x1, y1, x2, y2)
        if duration is not None:
            command += str(int(duration))
        self.run_device_cmd(command)

    def touch_tap(self, XY=None, offsets=None):
        # sleep(10)
        # sleep(0.5)
        if offsets is not None:
            final_X = XY[0] + randint(-offsets[0], offsets[0])
            final_Y = XY[1] + randint(-offsets[1], offsets[1])
        else:
            final_X = XY[0] + randint(-1, 1)
            final_Y = XY[1] + randint(-1, 1)
        # 如果你遇到了问题，可以把这百年输出并把日志分享到群里。
        logger.debug("点击坐标:({},{})".format(final_X, final_Y))
        command = "input tap {} {}".format(final_X,
                                           final_Y)
        self.run_device_cmd(command)
