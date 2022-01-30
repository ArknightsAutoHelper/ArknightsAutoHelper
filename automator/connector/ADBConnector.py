from io import BytesIO
import os
import logging.config
from pathlib import Path
from random import randint
import random
import shlex
import warnings
import zlib
import struct
import socket
import time
import contextlib
import importlib
import collections.abc

from util import cvimage as Image
import numpy as np
import cv2

import app
# from config import ADB_ROOT, ADB_HOST, SCREEN_SHOOT_SAVE_PATH, ShellColor, CONFIG_PATH,enable_adb_host_auto_detect, ADB_SERVER
from .ADBClientSession import ADBClientSession
from util.socketutil import recvall, recvexactly
from . import revconn

# from numpy import average, dot, linalg

logger = logging.getLogger(__name__)


def _screencap_to_image(cap, rotate=0):
    w, h, pixels = cap
    if len(pixels) == w * h * 4 + 4:
        # new format for Android P
        colorspace = struct.unpack_from('<I', pixels, 4)[0]
        pixels = pixels[4:]
    elif len(pixels) == w * h * 4:
        colorspace = 0
    else:
        raise ValueError('screencap short read')
    arr = np.frombuffer(pixels, dtype=np.uint8)
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
    if colorspace == 2:
        from PIL import Image as PILImage, ImageCms
        from imgreco.cms import p3_profile, srgb_profile
        pil_im = PILImage.frombuffer('RGBA', (w, h), arr, 'raw', 'RGBA', 0, 1)
        ImageCms.profileToProfile(pil_im, p3_profile, srgb_profile, ImageCms.INTENT_RELATIVE_COLORIMETRIC, inPlace=True)
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
            root = Path(os.environ['LOCALAPPDATA']).joinpath('Android', 'Sdk')
            base = 'adb.exe'
        elif system == 'Linux':
            root = Path(os.environ['HOME']).joinpath('Android', 'Sdk')
        elif system == 'Darwin':
            root = Path(os.environ['HOME']).joinpath('Library', 'Android', 'sdk')

        if 'ANDROID_SDK_ROOT' in os.environ:
            root = Path(os.environ['ANDROID_SDK_ROOT'])

        adbpath = root.joinpath('platform-tools', base)

        if adbpath.exists():
            return adbpath

    except:
        return None


_last_check = 0
def check_adb_alive():
    global _last_check
    if time.monotonic() - _last_check < 0.1:
        return True
    try:
        sess = ADBClientSession(app.ADB_SERVER)
        version = int(sess.service('host:version').read_response().decode(), 16)
        logger.debug('ADB server version %d', version)
        _last_check = time.monotonic()
        return True
    except socket.timeout:
        return False
    except ConnectionRefusedError:
        return False
    except RuntimeError:
        return False


def ensure_adb_alive():
    if check_adb_alive():
        return
    logger.info('尝试启动 adb server')
    import subprocess
    adbbin = app.config.device.adb_binary
    if not adbbin:
        adb_binaries = ['adb']
        try:
            bundled_adb = app.get_vendor_path('platform-tools')
            adb_binaries.append(bundled_adb / 'adb')
        except FileNotFoundError:
            pass
        findadb = find_adb_from_android_sdk()
        if findadb is not None:
            adb_binaries.append(findadb)
    else:
        adb_binaries = [adbbin]
    for adbbin in adb_binaries:
        try:
            logger.debug('trying %r', adbbin)
            if os.name == 'nt' and app.background:
                si = subprocess.STARTUPINFO(dwFlags=subprocess.STARTF_USESHOWWINDOW, wShowWindow=subprocess.SW_HIDE)
                subprocess.run([adbbin, 'start-server'], check=True, startupinfo=si)
            else:
                subprocess.run([adbbin, 'start-server'], check=True)
            # wait for the newly started ADB server to probe emulators
            time.sleep(0.5)
            if check_adb_alive():
                return
        except FileNotFoundError:
            pass
        except subprocess.CalledProcessError:
            pass
    raise OSError("can't start adb server")


class _ScreenCapImplPNG:
    def __init__(self, device_session_factory, rotate, displayid=None):
        self.device_session_factory = device_session_factory
        self.screenshot_rotate = rotate
        self.displayid = displayid
        if self.displayid is None:
            self.command = 'screencap -p'
        else:
            self.command = 'screencap -p -d {}'.format(self.displayid)

    def check(self):
        return self.screencap().size
    
    def screencap(self):
        from PIL import Image as PILImage, ImageCms
        s = self.device_session_factory().exec_stream(self.command)
        data = recvall(s, 4194304, True)
        img = PILImage.open(BytesIO(data))
        if self.screenshot_rotate != 0:
            img = img.rotate(self.screenshot_rotate)
        if icc := img.info.get('icc_profile', ''):
            iccio = BytesIO(icc)
            src_profile = ImageCms.ImageCmsProfile(iccio)
            from imgreco.cms import srgb_profile
            ImageCms.profileToProfile(img, src_profile, srgb_profile, ImageCms.INTENT_RELATIVE_COLORIMETRIC, inPlace=True)
        from util import pil_zerocopy
        return Image.fromarray(pil_zerocopy.asarray(img), img.mode)

    __call__ = screencap

class _ScreenCapImplDefault:
    def __init__(self, device_session_factory, rotate, compression_level=1, displayid=None):
        self.device_session_factory = device_session_factory
        self.screenshot_rotate = rotate
        self.displayid = displayid
        self.compress = compression_level
        if self.displayid is None:
            self.command = 'screencap'
        else:
            self.command = 'screencap -d {}'.format(self.displayid)
        if self.compress > 0:
            self.compress_suffix = f' | gzip -{self.compress}'
        else:
            self.compress_suffix = ''
    
    def decompress(self, data):
        if self.compress == 0:
            return data
        data = zlib.decompress(data, zlib.MAX_WBITS | 16, 8388608)
        return data

    def check(self):
        A_gz = self.device_session_factory().exec('echo A' + self.compress_suffix)
        if self.decompress(A_gz) != b'A\n':
            raise RuntimeError("gzip -1 in device cannot produce desired output")
        s = self.device_session_factory().exec_stream(self.command)
        data = recvexactly(s, 12)
        s.close()
        w, h, f = struct.unpack_from('III', data, 0)
        assert (f == 1)
        return w, h

    def screencap(self):
        t0 = time.perf_counter()
        if self.compress == 0:
            s = self.device_session_factory().exec_stream(self.command)
            header = recvexactly(s, 12)
            w, h, f = struct.unpack_from('III', header, 0)
            datalen = w * h * 4
            data = recvall(s, datalen+4, True)
            s.close()
            # data = zlib.decompress(data, zlib.MAX_WBITS | 16, 8388608)
            assert (f == 1)
            result = _screencap_to_image((w, h, data[:datalen+4]), self.screenshot_rotate)
        else:
            s = self.device_session_factory().exec_stream(self.command + self.compress_suffix)
            data = recvall(s, 8388608, True)
            data = self.decompress(data)
            w, h, f = struct.unpack_from('III', data, 0)
            datalen = w * h * 4
            s.close()
            # data = zlib.decompress(data, zlib.MAX_WBITS | 16, 8388608)
            assert (f == 1)
            result = _screencap_to_image((w, h, data[12:datalen+12+4]), self.screenshot_rotate)
        t = time.perf_counter() - t0
        logger.debug('screencap: %.3fms', t * 1000)
        return result

    __call__ = screencap

class _ScreenCapImplReverseLoopback:
    def __init__(self, device_session_factory, rotate, rch, loopback, displayid=None):
        self.device_session_factory = device_session_factory
        self.screenshot_rotate = rotate
        self.loopback = loopback
        self.rch = rch
        self.displayid = displayid
        if self.displayid is None:
            self.command = 'screencap'
        else:
            self.command = 'screencap -d {}'.format(self.displayid)
    def check(self):
        future = self.rch.register_cookie()
        with future:
            command = f'(echo -n {future.cookie.decode()}'
            control_sock = self.device_session_factory().exec_stream('(echo -n %s; %s) | nc %s %d' % (future.cookie.decode(), self.command, self.loopback, self.rch.port))
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


def _host_session_factory(timeout=None):
    ensure_adb_alive()
    return ADBClientSession(app.ADB_SERVER, timeout)

def enum(devices):
    for serial in ADBConnector.available_devices():
        devices.append((f'ADB: {serial[0]}', ADBConnector, [serial[0]], 'strong'))


from .scrcpy.core import Client as ScrcpyClient
from .scrcpy import const as scrcpy_const
class ScrcpyInput:
    def __init__(self, device, displayid):
        self.scrcpy = ScrcpyClient(device, displayid=displayid)
        self.scrcpy.start()

    def tap(self, x, y, hold_time=0.07):
        self.scrcpy.control.tap(int(x), int(y), hold_time)

    def swipe(self, x0, y0, x1, y1, move_duraion=1, hold_before_release=0, interpolation='linear'):
        if interpolation == 'linear':
            interpolate = lambda x: x
        elif interpolation == 'spline':
            import scipy.interpolate
            xs = [0, random.uniform(0.7, 0.8), 1, 2]
            ys = [0, random.uniform(0.9, 0.95), 1, 1]
            tck = scipy.interpolate.splrep(xs, ys, s=0)
            interpolate = lambda x: scipy.interpolate.splev(x, tck, der=0)
        frame_time = 1/100

        start_time = time.perf_counter()
        end_time = start_time + move_duraion
        self.scrcpy.control.touch(x0, y0, scrcpy_const.ACTION_DOWN)
        t1 = time.perf_counter()
        step_time = t1 - start_time
        if step_time < frame_time:
            time.sleep(frame_time - step_time)
        while True:
            t0 = time.perf_counter()
            if t0 > end_time:
                break
            time_progress = (t0 - start_time) / move_duraion
            path_progress = interpolate(time_progress)
            self.scrcpy.control.touch(int(x0 + (x1 - x0) * path_progress), int(y0 + (y1 - y0) * path_progress), scrcpy_const.ACTION_MOVE)
            t1 = time.perf_counter()
            step_time = t1 - t0
            if step_time < frame_time:
                time.sleep(frame_time - step_time)
        self.scrcpy.control.touch(x1, y1, scrcpy_const.ACTION_MOVE)
        if hold_before_release > 0:
            time.sleep(hold_before_release)
        self.scrcpy.control.touch(x1, y1, scrcpy_const.ACTION_UP)

    def text(self, text):
        self.scrcpy.control.text(text)

class ShellInput:
    def __init__(self, device: 'ADBConnector', displayid):
        self.device = device
        if displayid is not None:
            self.input_command = f'input -d {displayid}'
        else:
            self.input_command = 'input'

    def tap(self, x, y, hold_time=0.07):
        self.device.run_device_cmd(f'{self.input_command} swipe {x} {y} {x} {y} {hold_time*1000:.0f}')

    def swipe(self, x0, y0, x1, y1, move_duraion=1, hold_before_release=0, interpolation='linear'):
        if hold_before_release > 0:
            warnings.warn('hold_before_release is not supported in shell mode, you may experience unexpected inertia scrolling')
        if interpolation != 'linear':
            warnings.warn('interpolation mode other than linear is not supported in shell mode')
        self.device.run_device_cmd(f'{self.input_command} swipe {x0} {y0} {x1} {y1} {move_duraion*1000:.0f}')

    def text(self, text):
        escaped_text = shlex.quote(text)
        self.device.run_device_cmd(f'{self.input_command} text {escaped_text}')

class ADBConnector:
    def __init__(self, adb_serial, displayid=None):
        ensure_adb_alive()
        # os.chdir(ADB_ROOT)
        self.device_serial = adb_serial
        self.host_session_factory = _host_session_factory
        self.rch = None
        self.device_session_factory = lambda: self.host_session_factory().device(self.device_serial)
        self.cache_screenshot = app.config.device.cache_screenshot
        self.last_screenshot_timestamp = 0
        self.last_screenshot_duration = 0
        self.last_screenshot = None
        self.screencap_impl = None
        self.screen_size = (0, 0)
        self.displayid = displayid
        try:
            session = self.device_session_factory()
        except RuntimeError as e:
            if e.args and isinstance(e.args[0], bytes) and b'not found' in e.args[0]:
                if ':' in adb_serial and adb_serial.split(':')[-1].isdigit():
                    logger.info('adb connect %s', adb_serial)
                    ADBConnector.paranoid_connect(adb_serial)
                else:
                    raise
        self.device_identifier = self.get_device_identifier()
        self.config_key = 'adb-%s' % self.device_identifier
        self.screenshot_rotate = 0
        logger.debug('device identifier: %s', self.device_identifier)
        self.load_device_config()

    def __del__(self):
        if self.rch and self.rch.is_alive():
            self.rch.stop()

    def __str__(self):
        return 'adb:'+self.device_serial

    def get_device_identifier(self):
        hostname = self.device_session_factory().exec('getprop net.hostname').decode().strip()
        if hostname:
            return hostname
        android_id = self.device_session_factory().exec('settings get secure android_id').decode().strip()
        if android_id:
            return android_id

    @classmethod
    def disconnect_offline(cls):
        with contextlib.suppress(RuntimeError):
            for x in _host_session_factory().devices():
                if x[1] == 'offline':
                    with contextlib.suppress(RuntimeError):
                        _host_session_factory().disconnect(x[0])

    @classmethod
    def paranoid_connect(cls, port, timeout=0):
        with contextlib.suppress(RuntimeError):
            _host_session_factory().disconnect(port)
        host_session = _host_session_factory()
        if timeout != 0:
            host_session.sock.settimeout(timeout)
        host_session.connect(port)

    @classmethod
    def available_devices(cls):
        return [x for x in _host_session_factory().devices() if x[1] != 'offline']


    def run_device_cmd(self, cmd, DEBUG_LEVEL=2):
        output = self.device_session_factory().exec(cmd)
        logger.debug("command: %s", cmd)
        logger.debug("output: %s", repr(output))
        return output


    def _detect_loopbacks(self):
        if not (self.device_serial.startswith('emulator-') or self.device_serial.startswith('127.0.0.1:')):
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

    def screenshot(self, cached=True) -> Image.Image:
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
        if duration is None:
            duration = 1
        self.input.swipe(x1, y1, x2, y2, duration)

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
        self.input.tap(final_X, final_Y)

    def load_device_config(self):
        import app.device_database
        
        device_record = app.device_database.get_device(self.config_key)
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
            self.screencap_impl = _ScreenCapImplPNG(self.device_session_factory, self.screenshot_rotate, displayid=self.displayid)
        elif screenshot_impl == 'loopback' and 'loopback_address' in device_record:
            self._init_reverse_connection()
            self.loopback = device_record['loopback_address']
            self.screencap_impl = _ScreenCapImplReverseLoopback(self.device_session_factory, self.screenshot_rotate, self.rch, self.loopback, displayid=self.displayid)
        elif screenshot_impl == 'default':
            self.screencap_impl = _ScreenCapImplDefault(self.device_session_factory, self.screenshot_rotate, displayid=self.displayid)
        elif screenshot_impl == 'default_uncompressed':
            self.screencap_impl = _ScreenCapImplDefault(self.device_session_factory, self.screenshot_rotate, compression_level=0, displayid=self.displayid)
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

        input_provider = device_record.get('input', 'scrcpy')
        try:
            if input_provider == 'scrcpy':
                self.input = ScrcpyInput(self, self.displayid)
        except:
            logger.debug("scrcpy-server failed, using fallback shell provider", exc_info=True)
            input_provider = 'shell'
        if input_provider == 'shell':
            self.input = ShellInput(self, self.displayid)

    def _probe_device_config(self, device_record):
        time_gzipped_raw = 999
        time_reverse_loopback = 999
        screenshot = None
        workaround_slow_emulator_adb = app.config.device.workaround_slow_emulator_adb

        if 'screenshot_rotate' not in device_record:
            device_record['screenshot_rotate'] = 0

        try:
            gzip_impl = _ScreenCapImplDefault(self.device_session_factory, device_record['screenshot_rotate'], displayid=self.displayid)
            device_record['screenshot_type'] = 'default'
            t0 = time.perf_counter()
            screenshot = gzip_impl.screencap()
            t1 = time.perf_counter()
            time_gzipped_raw = t1 - t0
            logger.debug('gzipped raw screencap: %dx%d image in %.03f ms ', screenshot.width, screenshot.height, time_gzipped_raw*1000)

            uncompressed_impl = _ScreenCapImplDefault(self.device_session_factory, device_record['screenshot_rotate'], compression_level=0, displayid=self.displayid)
            device_record['screenshot_type'] = 'default_uncompressed'
            t0 = time.perf_counter()
            screenshot = uncompressed_impl.screencap()
            t1 = time.perf_counter()
            time_uncompressed_raw = t1 - t0
            logger.debug('uncompressed raw screencap: %dx%d image in %.03f ms ', screenshot.width, screenshot.height, time_uncompressed_raw*1000)

            if time_gzipped_raw < time_uncompressed_raw:
                logger.debug('gzipped raw screencap is faster, using it')
                self.screencap_impl = gzip_impl
                device_record['screenshot_type'] = 'default'
            else:
                logger.debug('uncompressed raw screencap is faster, using it')
                self.screencap_impl = uncompressed_impl
                device_record['screenshot_type'] = 'default_uncompressed'

        except:
            logger.debug('gzipped raw screencap failed, using fail-safe PNG screencap', exc_info=True)
            png_impl = _ScreenCapImplPNG(self.device_session_factory, device_record['screenshot_rotate'], displayid=self.displayid)
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
                    loopback_impl = _ScreenCapImplReverseLoopback(self.device_session_factory, device_record['screenshot_rotate'], self.rch, self.loopback, displayid=self.displayid)
                    t0 = time.perf_counter()
                    screenshot = loopback_impl.screencap()
                    t1 = time.perf_counter()
                    time_reverse_loopback = t1 - t0
                    logger.debug('reverse connection raw screencap: %dx%d image in %.03f ms', screenshot.width, screenshot.height, time_reverse_loopback*1000)
                    if workaround_slow_emulator_adb == 'always' or time_reverse_loopback < time_gzipped_raw:
                        device_record['screenshot_type'] = 'loopback'
                        device_record['loopback_address'] = self.loopback
                        self.screencap_impl = loopback_impl
                else:
                    self.rch.stop()

        try:
            self.input = ScrcpyInput(self, self.displayid)
            input_provider = 'scrcpy'
        except:
            logger.debug("scrcpy-server failed, using fallback shell provider", exc_info=True)
            self.input = ShellInput(self, self.displayid)
            input_provider = 'shell'
        device_record['input'] = input_provider

        device_record['screen_width'] = screenshot.width
        device_record['screen_height'] = screenshot.height
        device_record.save()

        self.screen_size = (screenshot.width, screenshot.height)

    def ensure_alive(self):
        self.device_session_factory().exec(':')

    def push(self, target_path, buf):
        sock = self.device_session_factory().push(target_path, buf)
