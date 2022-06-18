from __future__ import annotations
import logging
import os
from pathlib import Path
import socket
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import ADBServer

logger = logging.getLogger(__name__)


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
def check_adb_alive(server: ADBServer):
    global _last_check
    if time.monotonic() - _last_check < 0.1:
        return True
    try:
        sess = server._create_session_nocheck()
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


def ensure_adb_alive(server: ADBServer):
    if check_adb_alive(server):
        return
    if server.address[0] != '127.0.0.1' and server.address[0] != 'localhost':
        raise RuntimeError('ADB server is not running on localhost, please start it manually')
    start_adb_server()

def start_adb_server():
    logger.info('尝试启动 adb server')
    import subprocess
    import app
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
    from .client import ADBServer
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
            if check_adb_alive(ADBServer()):
                logger.info('已启动 adb server')
                return
        except FileNotFoundError:
            pass
        except subprocess.CalledProcessError:
            pass
    raise OSError("can't start adb server")
