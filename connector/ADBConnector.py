from io import BytesIO
import os
import logging.config
from random import randint
from sys import exc_info
import zlib
import struct
import socket
import time
import contextlib
import importlib
import collections.abc

from PIL import Image
import numpy as np
import cv2

import config
# from config import ADB_ROOT, ADB_HOST, SCREEN_SHOOT_SAVE_PATH, ShellColor, CONFIG_PATH,enable_adb_host_auto_detect, ADB_SERVER
from .ADBClientSession import ADBClientSession
from util.socketutil import recvall, recvexactly
from . import revconn

# from numpy import average, dot, linalg

logger = logging.getLogger(__name__)


def _screencap_to_image(cap, rotate=0):
    w, h, pixels = cap
    mem = memoryview(pixels)
    arr = np.frombuffer(mem, dtype=np.uint8)
    arr = arr.reshape((h, w, 4))
    if rotate == 0:
        pass
    elif rotate == 90:
        arr = cv2.rotate(arr, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif rotate == 180:
        arr = cv2.rotate(arr, cv2.ROTATE_180)
    elif rotate == 270:
        arr = cv2.rotate(arr, cv2.ROTATE_90_CLOCKWISE)
    else:
        raise ValueError('invalid rotate')
    return Image.fromarray(arr, 'RGBA')


def _ensure_pil_image(imgorfile):
    if isinstance(imgorfile, Image.Image):
        return imgorfile
    return Image.open(imgorfile)


def find_adb_from_android_sdk():
    import platform
    system = platform.system()
    root = ''
    base = 'adb'

    try:
        if system == 'Windows':
            root = os.path.join(os.environ['LOCALAPPDATA'], 'Android', 'Sdk')
            base = 'adb.exe'
        elif system == 'Linux':
            root = os.path.join(os.environ['HOME'], 'Android', 'Sdk')
        elif system == 'Darwin':
            root = os.path.join(os.environ['HOME'], 'Library', 'Android', 'sdk')

        if 'ANDROID_SDK_ROOT' in os.environ:
            root = os.environ['ANDROID_SDK_ROOT']

        adbpath = os.path.join(root, 'platform-tools', base)

        if os.path.exists(adbpath):
            return adbpath

    except:
        return None



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
        findadb = find_adb_from_android_sdk()
        if findadb is not None:
            adb_binaries.append(findadb)
    else:
        adb_binaries = [adbbin]
    for adbbin in adb_binaries:
        try:
            logger.debug('trying %r', adbbin)
            subprocess.run([adbbin, 'start-server'], check=True)
            # wait for the newly started ADB server to probe emulators
            time.sleep(0.5)
            return True
        except FileNotFoundError:
            pass
        except subprocess.CalledProcessError:
            pass
    raise OSError("can't start adb server")


class _ScreenCapImplPNG:
    def __init__(self, device_session_factory, rotate):
        self.device_session_factory = device_session_factory
        self.screenshot_rotate = rotate

    def check(self):
        return self.screencap().size
    
    def screencap(self):
        s = self.device_session_factory().exec_stream('screencap -p')
        data = recvall(s, 4194304, True)
        img = Image.open(BytesIO(data))
        if self.screenshot_rotate != 0:
            img = img.rotate(self.screenshot_rotate)
        return img
    
    __call__ = screencap

class _ScreenCapImplDefault:
    def __init__(self, device_session_factory, rotate):
        self.device_session_factory = device_session_factory
        self.screenshot_rotate = rotate

    def check(self):
        A_gz = self.device_session_factory().exec('echo A | gzip -1')
        if zlib.decompress(A_gz, zlib.MAX_WBITS | 16, 32) != b'A\n':
            raise RuntimeError("gzip -1 in device cannot produce desired output")
        s = self.device_session_factory().exec_stream('screencap')
        data = recvexactly(s, 12)
        s.close()
        w, h, f = struct.unpack_from('III', data, 0)
        assert (f == 1)
        return w, h

    def screencap(self):
        s = self.device_session_factory().exec_stream('screencap|gzip -1')
        data = recvall(s, 4194304)
        s.close()
        data = zlib.decompress(data, zlib.MAX_WBITS | 16, 8388608)
        w, h, f = struct.unpack_from('III', data, 0)
        assert (f == 1)
        return _screencap_to_image((w, h, data[12:]), self.screenshot_rotate)

    __call__ = screencap

class _ScreenCapImplReverseLoopback:
    def __init__(self, device_session_factory, rotate, rch, loopback):
        self.device_session_factory = device_session_factory
        self.screenshot_rotate = rotate
        self.loopback = loopback
        self.rch = rch

    def check(self):
        future = self.rch.register_cookie()
        with future:
            control_sock = self.device_session_factory().exec_stream('(echo -n %s; screencap) | nc %s %d' % (future.cookie.decode(), self.loopback, self.rch.port))
            with control_sock, future.get() as conn:
                data = recvexactly(conn, 12)
        w, h, f = struct.unpack_from('III', data, 0)
        assert (f == 1)
        return w, h

    def screencap(self):
        future = self.rch.register_cookie()
        with future:
            control_sock = self.device_session_factory().exec_stream('(echo -n %s; screencap) | nc %s %d' % (future.cookie.decode(), self.loopback, self.rch.port))
            with control_sock, future.get() as conn:
                data = recvall(conn, 8388608, True)
        w, h, f = struct.unpack_from('III', data, 0)
        assert (f == 1)
        return _screencap_to_image((w, h, data[12:]), self.screenshot_rotate)

    __call__ = screencap

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
        self.screencap_impl = None
        self.screen_size = (0, 0)
        self.device_identifier = self.get_device_identifier()
        self.config_key = 'adb-%s' % self.device_identifier
        self.screenshot_rotate = 0
        logger.debug('device identifier: %s', self.device_identifier)
        self.load_device_config()

    def __del__(self):
        if self.rch and self.rch.is_alive():
            self.rch.stop()

    def get_device_identifier(self):
        hostname = self.device_session_factory().exec('getprop net.hostname').decode().strip()
        if hostname:
            return hostname
        android_id = self.device_session_factory().exec('settings get secure android_id').decode().strip()
        if android_id:
            return android_id

    def disconnect_offline(self):
        with contextlib.suppress(RuntimeError):
            for x in self.host_session_factory().devices():
                if x[1] == 'offline':
                    with contextlib.suppress(RuntimeError):
                        self.host_session_factory().disconnect(x[0])

    def panaroid_connect(self, port, timeout=0):
        with contextlib.suppress(RuntimeError):
            self.host_session_factory().disconnect(port)
        host_session = self.host_session_factory()
        if timeout != 0:
            host_session.sock.settimeout(timeout)
        host_session.connect(port)

    def __adb_device_name_detector(self):
        devices = [x for x in self.host_session_factory().devices() if x[1] != 'offline']

        if len(devices) == 0:
            fixups = config.get('device/adb_no_device_fixups', [])

            # old config migration
            if autoconn := config.get('device/adb_auto_connect', None):
                fixups.append(dict(run='adb_connect', target=autoconn))

            if fixups:
                logger.info('无设备连接，尝试自动修复')
                self.disconnect_offline()
                for fixup in fixups:
                    if isinstance(fixup, collections.abc.Mapping):
                        name = fixup['run']
                        if not name.isidentifier():
                            logger.error('无效修复模块名称 %r', name)
                            continue
                        try:
                            logger.info('运行修复模块 %s', name)
                            module = importlib.import_module('..fixups.' + name, __name__)
                            if module.run(self, fixup):
                                logger.info('自动修复成功')
                                break
                        except ModuleNotFoundError:
                            logger.error('无效修复模块名称 %s', name)
                        except Exception:
                            logger.error('自动修复模块 %s 发生错误', name)
                            logger.debug('', exc_info=True)
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
            for i, (serial, status) in enumerate(devices):
                print("%2d. %s" % (i, serial))
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
        if not (self.adb_serial.startswith('emulator-') or self.adb_serial.startswith('127.0.0.1:')):
            return []
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

    def _init_reverse_connection(self):
        if self.rch is not None:
            return
        self.rch = revconn.ReverseConnectionHost()
        self.rch.start()

    def screenshot(self, cached=True):
        t0 = time.monotonic()
        if cached and self.cache_screenshot:
            if self.last_screenshot is not None and t0 - self.last_screenshot_timestamp < self.last_screenshot_duration:
                return self.last_screenshot
        exc = None
        for attempt in range(10):
            try:
                img = self.screencap_impl()
            except Exception as e:
                exc = e
                continue
            break
        else:  # not break
            raise exc
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

    def load_device_config(self):
        import config.device_database
        
        device_record = config.device_database.get_device(self.config_key)
        if device_record.is_new_record():
            self._probe_device_config(device_record)
            return

        logger.debug('using device-specific config in database')

        if 'screenshot_rotate' in device_record:
            self.screenshot_rotate = int(device_record['screenshot_rotate'])
            if self.screenshot_rotate % 90 != 0:
                raise ValueError("invalid screenshot_rotate value")

        screenshot_impl = device_record.get('screenshot_type', 'default')
        if screenshot_impl == 'safe':
            self.screencap_impl = _ScreenCapImplPNG(self.device_session_factory, self.screenshot_rotate)
        elif screenshot_impl == 'loopback' and 'loopback_address' in device_record:
            self._init_reverse_connection()
            self.loopback = device_record['loopback_address']
            self.screencap_impl = _ScreenCapImplReverseLoopback(self.device_session_factory, self.screenshot_rotate, self.rch, self.loopback)
        elif screenshot_impl == 'default':
            self.screencap_impl = _ScreenCapImplDefault(self.device_session_factory, self.screenshot_rotate)
        else:
            raise KeyError("unknown screenshot_type: %s" % screenshot_impl)

        try:
            width, height = self.screencap_impl.check()
        except:
            logger.error("device sanity check with information in database failed", exc_info=True)
            self._probe_device_config(device_record)
        else:
            if width != device_record.get('screen_width', 0) or height != device_record.get('screen_height', 0):
                logger.debug('screen size changed, reprobing device %s', self.device_identifier)
                self._probe_device_config(device_record)
            else:
                self.screen_size = (width, height)



    def _probe_device_config(self, device_record):
        time_gzipped_raw = 999
        time_reverse_loopback = 999
        screenshot = None
        workaround_slow_emulator_adb = config.get('device/workaround_slow_emulator_adb', 'auto')

        if 'screenshot_rotate' not in device_record:
            device_record['screenshot_rotate'] = 0

        try:
            default_impl = _ScreenCapImplDefault(self.device_session_factory, device_record['screenshot_rotate'])
            device_record['screenshot_type'] = 'default'
            self.screencap_impl = default_impl
            t0 = time.monotonic()
            screenshot = default_impl.screencap()
            t1 = time.monotonic()
            time_gzipped_raw = t1 - t0
            logger.debug('gzipped raw screencap: %dx%d image in %.02f secs ', screenshot.width, screenshot.height, time_gzipped_raw)
        except:
            logger.debug('gzipped raw screencap failed, using fail-safe PNG screencap')
            png_impl = _ScreenCapImplPNG(self.device_session_factory, device_record['screenshot_rotate'])
            screenshot = png_impl.screencap()
            logger.debug('PNG screencap: %dx%d image in %.03f secs', screenshot.width, screenshot.height, time_gzipped_raw)
            self.screencap_impl = png_impl
            device_record['screenshot_type'] = 'safe'
            workaround_slow_emulator_adb = 'never'
        
        if workaround_slow_emulator_adb == 'auto' or workaround_slow_emulator_adb == 'always':
            loopbacks = self._detect_loopbacks()
            if len(loopbacks):
                logger.debug('possible loopback addresses: %s', repr(loopbacks))
                self._init_reverse_connection()
                if self._test_reverse_connection(loopbacks):
                    loopback_impl = _ScreenCapImplReverseLoopback(self.device_session_factory, device_record['screenshot_rotate'], self.rch, self.loopback)
                    t0 = time.monotonic()
                    screenshot = loopback_impl.screencap()
                    t1 = time.monotonic()
                    time_reverse_loopback = t1 - t0
                    logger.debug('reverse connection raw screencap: %dx%d image in %.03f secs', screenshot.width, screenshot.height, time_gzipped_raw)
                    if workaround_slow_emulator_adb == 'always' or time_reverse_loopback < time_gzipped_raw:
                        device_record['screenshot_type'] = 'loopback'
                        device_record['loopback_address'] = self.loopback
                        self.screencap_impl = loopback_impl
                else:
                    self.rch.stop()

        device_record['screen_width'] = screenshot.width
        device_record['screen_height'] = screenshot.height
        device_record.save()

        self.screen_size = (screenshot.width, screenshot.height)

    def ensure_alive(self):
        self.device_session_factory().exec(':')
